import random
from datetime import datetime

# --- Imports des modules internes ---
from .case_manager import generate_case, build_suspect_prompt
from .ai_agent import ask_agent, ask_agent_json, detective_analysis_prompt
from .difficulty_manager import gen_opts_for_difficulty
from .cards_manager import use_card_prompt
from .logs_manager import save_game_log



class GameManager:
    def __init__(self):
        self.lang = "fr"
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

    # ------------------------------------------------------------
    def run(self):
        """Lance le jeu complet."""
        print("🌍 Choose your language / Choisis ta langue: (fr/en)")
        self.lang = input("👉 ").strip().lower()
        if self.lang not in ["fr", "en"]:
            self.lang = "en"

        print("🎚️ " + ("Choisis une difficulté (easy/normal/hard): " if self.lang == "fr" else "Choose difficulty (easy/normal/hard): "))
        self.difficulty = input("👉 ").strip().lower()
        if self.difficulty not in ["easy", "normal", "hard"]:
            self.difficulty = "normal"

        context = random.choice(self.contexts[self.lang])
        print("------------------------------------------------------")
        print("🎮 ", "Bienvenue dans le jeu du détective IA !" if self.lang == "fr" else "Welcome to the AI Detective Game!")
        print("📖", context)
        print("------------------------------------------------------")

        player_role = input("👉 " + ("Choisis ton rôle (detective/suspect): " if self.lang == "fr" else "Choose your role (detective/suspect): ")).strip().lower()
        case = generate_case(self.lang)

        if player_role == "detective":
            self.play_detective(context, case)
        elif player_role == "suspect":
            self.play_suspect(context, case)
        else:
            print("⚠️ " + ("Rôle inconnu." if self.lang == "fr" else "Unknown role."))

    # ------------------------------------------------------------
    def play_detective(self, context, case):
        """Mode joueur = détective humain."""
        print("\n🕵️ " + ("Tu es le détective. Interroge les deux suspects !" if self.lang == "fr" else "You are the detective. Interrogate the two suspects!"))
        criminal = case["culprit"]
        role1 = "suspect_criminal" if criminal == "suspect1" else "suspect_innocent"
        role2 = "suspect_criminal" if criminal == "suspect2" else "suspect_innocent"

        asked = 0
        found = False
        history = ""
        opts = gen_opts_for_difficulty(self.difficulty)
        cards = {"pression": 1, "piege": 1, "preuve": 1}

        while asked < 10 and not found:
            # Gestion des cartes
            if any(v > 0 for v in cards.values()):
                print("🎴 " + ("Cartes dispos : pression / piege / preuve / aucune" if self.lang == "fr" else "Available cards: pressure / trap / evidence / none"))
                card = input("👉 ").strip().lower()
            else:
                card = "aucune"

            q = input("\n🕵️ " + ("Pose ta question: " if self.lang == "fr" else "Your question: "))
            if card in ["pression", "piege", "preuve"] and cards[card] > 0:
                q = use_card_prompt(self.lang, card, q, case)
                cards[card] = 0

            asked += 1
            prompt_s1 = build_suspect_prompt(self.lang, role1, case, history, q, "suspect1")
            prompt_s2 = build_suspect_prompt(self.lang, role2, case, history, q, "suspect2")

            ans1 = ask_agent("gemma3:latest", prompt_s1, opts)
            ans2 = ask_agent("gemma3:latest", prompt_s2, opts)

            print(f"👤 Suspect 1: {ans1}")
            print(f"👤 Suspect 2: {ans2}")

            history += f"\nQ: {q}\nS1: {ans1}\nS2: {ans2}"

            # Analyse JSON à partir de la 3e question
            if asked >= 3:
                analysis_prompt = detective_analysis_prompt(self.lang, history)
                analysis = ask_agent_json("gemma3:latest", analysis_prompt)
                if analysis:
                    print("📊 Analyse IA:", analysis)
                    s1, s2 = analysis["suspect1"]["score"], analysis["suspect2"]["score"]
                    suggestion = "suspect1" if s1 >= s2 else "suspect2"
                    print("👉 Suggestion d'accusation:", suggestion)

                choice = input("\n👉 " + ("Veux-tu accuser ? (oui/non): " if self.lang == "fr" else "Do you want to accuse? (yes/no): ")).strip().lower()
                if choice in ["oui", "yes"]:
                    guess = input("🕵️ " + ("Qui est le coupable ? (suspect1/suspect2): " if self.lang == "fr" else "Who is guilty? (suspect1/suspect2): "))
                    if guess == criminal:
                        print("✅ " + ("Bravo ! Tu as trouvé le coupable !" if self.lang == "fr" else "Correct! You found the criminal!"))
                    else:
                        print("❌ " + ("Mauvais choix... C’était " if self.lang == "fr" else "Wrong choice... It was "), criminal)
                    found = True

        if not found:
            print("\n⚖️ " + ("10 questions atteintes. Tu dois accuser !" if self.lang == "fr" else "10 questions reached. You must accuse!"))
            guess = input("🕵️ " + ("Qui est le coupable ? " if self.lang == "fr" else "Who is the criminal? "))
            if guess == criminal:
                print("✅ " + ("Bravo ! Tu as trouvé le coupable !" if self.lang == "fr" else "Correct! You found the criminal!"))
            else:
                print("❌ " + ("Mauvais choix... C’était " if self.lang == "fr" else "Wrong choice... It was "), criminal)

        # Log de partie
        payload = {
            "mode": "detective",
            "lang": self.lang,
            "difficulty": self.difficulty,
            "context": context,
            "case": case,
            "questions": asked,
            "history": history,
            "found": found,
            "culprit": criminal
        }
        path = save_game_log(payload)
        print("🗂️ Log sauvegardé :", path)

    # ------------------------------------------------------------
    def play_suspect(self, context, case):
        """Mode joueur = suspect humain."""
        print("\n👤 " + ("Tu es un suspect. Essaie de tromper le détective IA !" if self.lang == "fr" else "You are a suspect. Try to fool the AI detective!"))
        sub_role = input("👉 " + ("Veux-tu être innocent ou coupable ? " if self.lang == "fr" else "Do you want to be innocent or guilty? ")).strip().lower()
        role_player = "suspect_innocent" if "innoc" in sub_role else "suspect_criminal"
        is_criminal = (role_player == "suspect_criminal")

        asked = 0
        found = False
        history = context
        opts = gen_opts_for_difficulty(self.difficulty)

        while asked < 10 and not found:
            q_prompt = "Pose une question au suspect." if self.lang == "fr" else "Ask a question to the suspect."
            q = ask_agent("gemma3:latest", f"{context}\nDetective: {q_prompt}", opts)
            asked += 1
            print("\n🕵️ Detective:", q)

            ans_player = input("👉 " + ("Ta réponse: " if self.lang == "fr" else "Your answer: "))
            history += f"\nQ: {q}\nSuspect: {ans_player}"

            if asked >= 3:
                decision_prompt = detective_analysis_prompt(self.lang, history)
                analysis = ask_agent_json("gemma3:latest", decision_prompt)
                if analysis:
                    s = analysis["suspect1"]["score"] if "suspect1" in analysis else 50
                    if s > 60 or asked == 10:
                        verdict = "guilty"
                    else:
                        verdict = "innocent"
                    print("⚖️ Verdict IA:", verdict)
                    if (verdict == "guilty" and is_criminal) or (verdict == "innocent" and not is_criminal):
                        print("✅ " + ("Le détective a trouvé la vérité." if self.lang == "fr" else "The detective found the truth."))
                    else:
                        print("🎉 " + ("Tu as trompé le détective !" if self.lang == "fr" else "You fooled the detective!"))
                    found = True

        # Log de partie
        payload = {
            "mode": "suspect",
            "lang": self.lang,
            "difficulty": self.difficulty,
            "context": context,
            "case": case,
            "answers": asked,
            "history": history,
            "is_criminal": is_criminal
        }
        path = save_game_log(payload)
        print("🗂️ Log sauvegardé :", path)
