# core/game_manager.py
import random
from datetime import datetime

from .case_manager import generate_case, build_suspect_prompt
from .ai_agent import ask_agent, ask_agent_json, detective_analysis_prompt
from .difficulty_manager import gen_opts_for_difficulty
from .cards_manager import use_card_prompt
from .logs_manager import save_game_log


class GameManager:
    """
    Version GUI-friendly : fournit start_game() et process_turn(input_text)
    et gère un petit automate d'états pour dérouler le jeu en interface.
    """

    def __init__(self):
        # Réglages courants
        self.lang = "en"
        self.difficulty = "normal"
        self.contexts = {
            "fr": [
                "Un meurtre a eu lieu dans une vieille bibliothèque. Le détective doit découvrir qui ment.",
                "Un cambriolage a eu lieu dans un musée. Deux suspects sont interrogés.",
                "Un empoisonnement a eu lieu lors d’un dîner mondain. Qui est le coupable ?",
                "Un vol de bijoux a été signalé dans un hôtel de luxe. Deux suspects sont entendus.",
                "Un incendie criminel a détruit une maison. Le détective enquête sur les deux survivants suspects."
            ],
            "en": [
                "A murder has taken place in an old library. The detective must find out who is lying.",
                "A burglary was committed in a museum. Two suspects are being questioned.",
                "A poisoning occurred during a dinner party. Who is guilty?",
                "A jewel theft has been reported in a luxury hotel. Two suspects are under interrogation.",
                "An arson destroyed a house. The detective investigates the two surviving suspects."
            ]
        }

        # État de jeu
        self.state = "ask_lang"  # ask_lang → ask_difficulty → ask_role → (detective|suspect)
        self.context = ""
        self.case = None
        self.opts = gen_opts_for_difficulty("normal")

        # Variables mode détective
        self.detective_asked = 0
        self.detective_history = ""
        self.detective_cards = {"pression": 1, "piege": 1, "preuve": 1}
        self.criminal = None
        self.role1 = None
        self.role2 = None

        # Variables mode suspect
        self.suspect_is_criminal = False
        self.suspect_history = ""
        self.suspect_asked = 0  # nombre de questions déjà posées par l'IA détective

    # ------------------------------------------------------------------
    # API GUI
    def start_game(self, _user_input_ignored=None):
        """Retourne le premier message d’invite pour la GUI."""
        self.state = "ask_lang"
        return "🌍 Choose your language / Choisis ta langue: (fr/en)"

    def process_turn(self, user_input: str) -> str:
        """Traite la saisie utilisateur selon l’état courant, et retourne la réponse IA / prochaine consigne."""
        try:
            if self.state == "ask_lang":
                return self._handle_lang(user_input)
            if self.state == "ask_difficulty":
                return self._handle_difficulty(user_input)
            if self.state == "ask_role":
                return self._handle_role(user_input)
            if self.state == "detective_wait_question":
                return self._handle_detective_question(user_input)
            if self.state == "detective_force_accuse":
                return self._handle_detective_force_accuse(user_input)
            if self.state == "suspect_choose_alignment":
                return self._handle_suspect_choose_alignment(user_input)
            if self.state == "suspect_wait_player_answer":
                return self._handle_suspect_player_answer(user_input)

            return "⚠️ Internal state error. Restart the game."

        except Exception as e:
            return f"⚠️ Error: {e}"

    # ------------------------------------------------------------------
    # Handlers des états

    def _handle_lang(self, txt: str) -> str:
        t = (txt or "").strip().lower()
        self.lang = "fr" if t == "fr" else "en"
        self.state = "ask_difficulty"
        return "🎚️ " + (
            "Choisis une difficulté (easy/normal/hard): "
            if self.lang == "fr"
            else "Choose difficulty (easy/normal/hard): "
        )

    def _handle_difficulty(self, txt: str) -> str:
        t = (txt or "").strip().lower()
        self.difficulty = t if t in ["easy", "normal", "hard"] else "normal"
        self.opts = gen_opts_for_difficulty(self.difficulty)
        self.context = random.choice(self.contexts[self.lang])
        self.case = generate_case(self.lang)

        self.state = "ask_role"
        head = (
            "🎮 Bienvenue dans le jeu du détective IA !"
            if self.lang == "fr"
            else "🎮 Welcome to the AI Detective Game!"
        )
        return (
            f"{head}\n"
            f"📖 {self.context}\n"
            + (
                "👉 Choisis ton rôle (detective/suspect): "
                if self.lang == "fr"
                else "👉 Choose your role (detective/suspect): "
            )
        )

    def _handle_role(self, txt: str) -> str:
        t = (txt or "").strip().lower()
        if t not in ["detective", "suspect"]:
            return (
                "❓ Rôle invalide. Tape 'detective' ou 'suspect'."
                if self.lang == "fr"
                else "❓ Invalid role. Type 'detective' or 'suspect'."
            )

        if t == "detective":
            self.criminal = self.case["culprit"]
            self.role1 = (
                "suspect_criminal" if self.criminal == "suspect1" else "suspect_innocent"
            )
            self.role2 = (
                "suspect_criminal" if self.criminal == "suspect2" else "suspect_innocent"
            )
            self.detective_asked = 0
            self.detective_history = ""
            self.detective_cards = {"pression": 1, "piege": 1, "preuve": 1}
            self.state = "detective_wait_question"

            return (
                "🕵️ Tu es le détective. Interroge les deux suspects !\n"
                "🎴 Cartes (1 chacune) : pression / piege / preuve. Utilise-les en préfixant ta question, ex: 'preuve: Où étiez-vous ?'\n"
                "👉 Pose ta première question :"
                if self.lang == "fr"
                else "🕵️ You are the detective. Interrogate both suspects!\n"
                "🎴 Cards (1 each): pressure / trap / evidence. Use them by prefixing your question, e.g.: 'evidence: Where were you?'\n"
                "👉 Ask your first question:"
            )

        self.suspect_history = self.context
        self.suspect_asked = 0
        self.state = "suspect_choose_alignment"
        return (
            "🎭 Veux-tu être innocent ou coupable ?"
            if self.lang == "fr"
            else "🎭 Do you want to be innocent or guilty?"
        )

    # ---------- Mode Détective ----------
    def _handle_detective_question(self, txt: str) -> str:
        question = (txt or "").strip()
        if not question:
            return "❓ " + (
                "Écris une question." if self.lang == "fr" else "Please type a question."
            )

        lower = question.lower()
        if lower.startswith("pression:") or lower.startswith("pressure:"):
            if self.detective_cards["pression"] > 0:
                question = question.split(":", 1)[1].strip()
                question = use_card_prompt(self.lang, "pression", question, self.case)
                self.detective_cards["pression"] = 0
            else:
                return "♻️ " + (
                    "Carte 'pression' déjà utilisée."
                    if self.lang == "fr"
                    else "'pressure' card already used."
                )
        elif lower.startswith("piege:") or lower.startswith("trap:"):
            if self.detective_cards["piege"] > 0:
                question = question.split(":", 1)[1].strip()
                question = use_card_prompt(self.lang, "piege", question, self.case)
                self.detective_cards["piege"] = 0
            else:
                return "♻️ " + (
                    "Carte 'piege' déjà utilisée."
                    if self.lang == "fr"
                    else "'trap' card already used."
                )
        elif lower.startswith("preuve:") or lower.startswith("evidence:"):
            if self.detective_cards["preuve"] > 0:
                question = question.split(":", 1)[1].strip()
                question = use_card_prompt(self.lang, "preuve", question, self.case)
                self.detective_cards["preuve"] = 0
            else:
                return "♻️ " + (
                    "Carte 'preuve' déjà utilisée."
                    if self.lang == "fr"
                    else "'evidence' card already used."
                )

        self.detective_asked += 1

        p1 = build_suspect_prompt(
            self.lang, self.role1, self.case, self.detective_history, question, "suspect1"
        )
        p2 = build_suspect_prompt(
            self.lang, self.role2, self.case, self.detective_history, question, "suspect2"
        )
        a1 = ask_agent("gemma3:latest", p1, self.opts)
        a2 = ask_agent("gemma3:latest", p2, self.opts)

        self.detective_history += f"\nQ: {question}\nS1: {a1}\nS2: {a2}"

        base = f"👤 Suspect 1: {a1}\n👤 Suspect 2: {a2}\n"
        suffix = ""

        if self.detective_asked >= 3:
            ap = detective_analysis_prompt(self.lang, self.detective_history)
            analysis = ask_agent_json("gemma3:latest", ap)

            if analysis:
                try:
                    s1 = analysis["suspect1"]["score"]
                    s2 = analysis["suspect2"]["score"]
                    suggestion = "suspect1" if s1 >= s2 else "suspect2"
                    if self.lang == "fr":
                        suffix += f"\n📊 Analyse IA → S1:{s1} / S2:{s2} | Suggestion: {suggestion}\n"
                        suffix += "👉 Pour accuser, écris: accuse suspect1 ou accuse suspect2. Sinon pose une autre question."
                    else:
                        suffix += f"\n📊 AI analysis → S1:{s1} / S2:{s2} | Suggestion: {suggestion}\n"
                        suffix += "👉 To accuse, type: accuse suspect1 or accuse suspect2. Otherwise, ask another question."
                except Exception:
                    suffix += "\n👉 " + (
                        "Tu peux accuser ou poser une autre question."
                        if self.lang == "fr"
                        else "You can accuse or ask another question."
                    )
            else:
                suffix += "\n👉 " + (
                    "Tu peux accuser: 'accuse suspect1' ou 'accuse suspect2'."
                    if self.lang == "fr"
                    else "You can accuse: 'accuse suspect1' or 'accuse suspect2'."
                )
        else:
            suffix += "\n👉 " + (
                "Pose une autre question." if self.lang == "fr" else "Ask another question."
            )

        if self.detective_asked >= 10:
            self.state = "detective_force_accuse"
            suffix = "\n⚖️ " + (
                "10 questions atteintes. Tu dois accuser maintenant !"
                if self.lang == "fr"
                else "10 questions reached. You must accuse now!"
            )

        cmd = lower.strip()
        if cmd.startswith("accuse"):
            parts = cmd.split()
            if len(parts) == 2 and parts[1] in ["suspect1", "suspect2"]:
                return self._finalize_detective_verdict(parts[1])
        return base + suffix

    def _handle_detective_force_accuse(self, txt: str) -> str:
        cmd = (txt or "").strip().lower()
        if cmd.startswith("accuse"):
            parts = cmd.split()
            if len(parts) == 2 and parts[1] in ["suspect1", "suspect2"]:
                return self._finalize_detective_verdict(parts[1])
        return (
            "❓ Écris: 'accuse suspect1' ou 'accuse suspect2'."
            if self.lang == "fr"
            else "❓ Type: 'accuse suspect1' or 'accuse suspect2'."
        )

    def _finalize_detective_verdict(self, guess: str) -> str:
        good = guess == self.criminal
        msg = (
            "✅ Bravo ! Tu as trouvé le coupable !"
            if good
            else f"❌ Mauvais choix… C’était {self.criminal}"
        ) if self.lang == "fr" else (
            "✅ Correct! You found the criminal!"
            if good
            else f"❌ Wrong choice… It was {self.criminal}"
        )

        payload = {
            "mode": "detective",
            "timestamp": datetime.now().isoformat(),
            "lang": self.lang,
            "difficulty": self.difficulty,
            "context": self.context,
            "case": self.case,
            "questions": self.detective_asked,
            "history": self.detective_history,
            "culprit": self.criminal,
            "player_guess": guess,
            "success": good,
        }
        save_game_log(payload)

        self.state = "ask_lang"
        tail = "\n\n" + (
            "🔁 Tape 'fr' ou 'en' pour relancer."
            if self.lang == "fr"
            else "🔁 Type 'fr' or 'en' to play again."
        )
        return msg + tail

    # ---------- Mode Suspect ----------
    def _handle_suspect_choose_alignment(self, txt: str) -> str:
        t = (txt or "").strip().lower()
        self.suspect_is_criminal = ("coup" in t) or ("guilt" in t)
        self.suspect_history = self.context
        self.suspect_asked = 0

        q_prompt = (
            "Pose une question au suspect."
            if self.lang == "fr"
            else "Ask a question to the suspect."
        )
        q = ask_agent("gemma3:latest", f"{self.context}\nDetective: {q_prompt}", self.opts)
        self.suspect_asked += 1
        self.suspect_history += f"\nQ: {q}"

        self.state = "suspect_wait_player_answer"
        return (
            f"🕵️ Détective: {q}\n👉 Ta réponse :"
            if self.lang == "fr"
            else f"🕵️ Detective: {q}\n👉 Your answer:"
        )

    def _handle_suspect_player_answer(self, txt: str) -> str:
        answer = (txt or "").strip()
        if not answer:
            return (
                "✍️ Écris ta réponse."
                if self.lang == "fr"
                else "✍️ Type your answer."
            )
        self.suspect_history += f"\nSuspect: {answer}"

        if self.suspect_asked >= 3 or self.suspect_asked >= 10:
            dp = detective_analysis_prompt(self.lang, self.suspect_history)
            analysis = ask_agent_json("gemma3:latest", dp)
            verdict = "guilty"
            if analysis:
                try:
                    score = analysis.get("suspect1", {}).get("score", 50)
                    verdict = "guilty" if (score > 60 or self.suspect_asked >= 10) else "innocent"
                except Exception:
                    verdict = "guilty" if self.suspect_asked >= 10 else "innocent"

            good = (verdict == "guilty") == self.suspect_is_criminal
            if self.lang == "fr":
                head = f"⚖️ Verdict du détective: {'coupable' if verdict == 'guilty' else 'innocent'}"
                tail = "\n✅ Le détective a trouvé la vérité." if good else "\n🎉 Tu as trompé le détective !"
                restart = "\n\n🔁 Tape 'fr' ou 'en' pour relancer."
            else:
                head = f"⚖️ Detective verdict: {verdict}"
                tail = "\n✅ The detective found the truth." if good else "\n🎉 You fooled the detective!"
                restart = "\n\n🔁 Type 'fr' or 'en' to play again."

            payload = {
                "mode": "suspect",
                "timestamp": datetime.now().isoformat(),
                "lang": self.lang,
                "difficulty": self.difficulty,
                "context": self.context,
                "case": self.case,
                "history": self.suspect_history,
                "is_criminal": self.suspect_is_criminal,
                "suspect_questions": self.suspect_asked,
                "ai_verdict": verdict,
                "ai_correct": good,
            }
            save_game_log(payload)

            self.state = "ask_lang"
            return head + tail + restart

        q_prompt = (
            "Pose une autre question au suspect."
            if self.lang == "fr"
            else "Ask another question to the suspect."
        )
        q = ask_agent(
            "gemma3:latest",
            f"{self.context}\nDialogue:\n{self.suspect_history}\nDetective: {q_prompt}",
            self.opts,
        )
        self.suspect_asked += 1
        self.suspect_history += f"\nQ: {q}"
        return (
            f"🕵️ Détective: {q}\n👉 Ta réponse :"
            if self.lang == "fr"
            else f"🕵️ Detective: {q}\n👉 Your answer:"
        )
