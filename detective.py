import random
import ollama
import json
import os

SCORE_FILE = "score.json"

# --- Contexts (FR/EN) ---
contexts = {
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

# --- Roles (FR/EN) ---
roles = {
    "fr": {
        "detective": (
            "Tu es un détective enquêtant sur un crime. "
            "Pose des questions logiques en fonction des réponses précédentes du suspect. "
            "À partir de la 3ème question tu peux accuser. "
            "À la 10ème question tu dois accuser."
        ),
        "suspect_innocent": "Tu es un suspect innocent. Réponds toujours honnêtement.",
        "suspect_criminal": "Tu es le suspect criminel. Tu dois mentir pour éviter d’être découvert."
    },
    "en": {
        "detective": (
            "You are a detective investigating a crime. "
            "Ask logical questions based on the suspect's previous answers. "
            "From the 3rd question you can accuse. "
            "At the 10th question you must accuse."
        ),
        "suspect_innocent": "You are an innocent suspect. Always answer truthfully.",
        "suspect_criminal": "You are the criminal suspect. You must lie to avoid being discovered."
    }
}

def ask_agent(lang, role, message):
    """Call Ollama with a given role and message."""
    prompt = f"{roles[lang][role]}\n\nConversation so far:\n{message}\n\nReply in { 'French' if lang == 'fr' else 'English' }:"
    res = ollama.generate(model="gemma3:latest", prompt=prompt)
    return res["response"].strip()

# --- Score management ---
def load_score():
    if os.path.exists(SCORE_FILE):
        with open(SCORE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"player": 0, "ai": 0}

def save_score(scores):
    with open(SCORE_FILE, "w", encoding="utf-8") as f:
        json.dump(scores, f, indent=2, ensure_ascii=False)

# --- Game start ---
print("🌍 Choose your language / Choisis ta langue: (fr/en)")
lang = input("👉 ").strip().lower()
if lang not in ["fr", "en"]:
    lang = "en"

print("🎮", "Bienvenue dans le jeu du détective IA !" if lang == "fr" else "Welcome to the AI Detective Game!")
print("------------------------------------------------------")
context = random.choice(contexts[lang])
print("📖", context)
print("------------------------------------------------------")

scores = load_score()
print("📊", "Score actuel:" if lang == "fr" else "Current score:", scores)

player_role = input("👉 " + ("Choisis ton rôle (detective/suspect): " if lang == "fr" else "Choose your role (detective/suspect): ")).strip().lower()

# --- Player as Suspect ---
if player_role == "suspect":
    sub_role = input("👉 " + ("Veux-tu être innocent ou coupable ? " if lang == "fr" else "Do you want to be innocent or guilty? ")).strip().lower()
    if sub_role in ["innocent", "innocent(e)"]:
        role_player = "suspect_innocent"
        is_criminal = False
    else:
        role_player = "suspect_criminal"
        is_criminal = True

    print("\n👤 " + ("Tu es suspect." if lang == "fr" else "You are a suspect."))
    print("👉 " + ("Ton rôle est: " if lang == "fr" else "Your role is: "), sub_role.capitalize())

    history = context
    asked = 0
    found = False

    while asked < 10 and not found:
        q = ask_agent(lang, "detective", history + ("\nPose une question au suspect." if lang == "fr" else "\nAsk the suspect a question."))
        asked += 1
        print("\n🕵️ Detective:", q)

        ans_player = input("👉 " + ("Ta réponse: " if lang == "fr" else "Your answer: "))
        history += f"\nSuspect (Player): {ans_player}"

        if asked >= 3 and asked < 10:
            decision = ask_agent(lang, "detective", history + ("\nDois-tu accuser maintenant ou continuer ?" if lang == "fr" else "\nShould you accuse now or continue?"))
            print("⚖️ Detective decision:", decision)

            if "accuser" in decision.lower() or "accuse" in decision.lower():
                verdict = ask_agent(lang, "detective", history + ("\nLe suspect est-il coupable ou innocent ?" if lang == "fr" else "\nIs the suspect guilty or innocent?"))
                print("\n⚖️ Verdict:", verdict)
                if (("coupable" in verdict.lower() or "guilty" in verdict.lower()) and is_criminal) or \
                   (("innocent" in verdict.lower()) and not is_criminal):
                    print("✅ " + ("Le détective a trouvé la vérité." if lang == "fr" else "The detective found the truth."))
                    scores["ai"] += 10
                else:
                    print("🎉 " + ("Tu as trompé le détective !" if lang == "fr" else "You fooled the detective!"))
                    scores["player"] += 5
                found = True

        if asked == 10 and not found:
            print("\n⚖️ " + ("10ème question : le détective doit accuser !" if lang == "fr" else "10th question: the detective must accuse!"))
            verdict = ask_agent(lang, "detective", history + ("\nLe suspect est-il coupable ou innocent ?" if lang == "fr" else "\nIs the suspect guilty or innocent?"))
            print("\n⚖️ Verdict:", verdict)
            if (("coupable" in verdict.lower() or "guilty" in verdict.lower()) and is_criminal) or \
               (("innocent" in verdict.lower()) and not is_criminal):
                print("✅ " + ("Le détective a trouvé la vérité." if lang == "fr" else "The detective found the truth."))
                scores["ai"] += 10
            else:
                print("🎉 " + ("Tu as trompé le détective !" if lang == "fr" else "You fooled the detective!"))
                scores["player"] += 5
            found = True

# --- Player as Detective ---
elif player_role == "detective":
    print("\n🕵️ " + ("Tu es le détective. Interroge les deux suspects !" if lang == "fr" else "You are the detective. Interrogate the two suspects!"))
    criminal = random.choice(["suspect1", "suspect2"])
    role1 = "suspect_criminal" if criminal == "suspect1" else "suspect_innocent"
    role2 = "suspect_criminal" if criminal == "suspect2" else "suspect_innocent"

    asked = 0
    found = False
    while asked < 10 and not found:
        q = input("\n🕵️ " + ("Pose ta question: " if lang == "fr" else "Your question: "))
        asked += 1

        ans1 = ask_agent(lang, role1, q)
        ans2 = ask_agent(lang, role2, q)
        print("👤 Suspect 1:", ans1)
        print("👤 Suspect 2:", ans2)

        if asked >= 3:
            choice = input("\n👉 " + ("Veux-tu accuser ? (oui/non): " if lang == "fr" else "Do you want to accuse? (yes/no): ")).strip().lower()
            if choice in ["oui", "yes"]:
                guess = input("🕵️ " + ("Qui est coupable ? (suspect1/suspect2): " if lang == "fr" else "Who is the criminal? (suspect1/suspect2): "))
                if guess == criminal:
                    print("✅ " + ("Bravo ! Tu as trouvé le coupable !" if lang == "fr" else "Correct! You found the criminal!"))
                    scores["player"] += 10
                else:
                    print("❌ " + ("Mauvais choix... C’était " if lang == "fr" else "Wrong choice... It was "), criminal)
                    scores["player"] -= 5
                found = True

    if not found:
        print("\n⚖️ " + ("10 questions atteintes. Tu dois accuser !" if lang == "fr" else "10 questions reached. You must accuse!"))
        guess = input("🕵️ " + ("Qui est le coupable ? " if lang == "fr" else "Who is the criminal? "))
        if guess == criminal:
            print("✅ " + ("Bravo ! Tu as trouvé le coupable !" if lang == "fr" else "Correct! You found the criminal!"))
            scores["player"] += 10
        else:
            print("❌ " + ("Mauvais choix... C’était " if lang == "fr" else "Wrong choice... It was "), criminal)
            scores["player"] -= 5

# --- Save score ---
save_score(scores)
print("\n📊", "Nouveau score:" if lang == "fr" else "Updated score:", scores)
