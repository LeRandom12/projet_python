import random
import ollama

# --- Définition des rôles IA ---
roles = {
    "detective": (
        "You are a detective investigating a crime. "
        "Your goal is to find who is guilty by asking questions and analyzing answers. "
        "Be logical and concise in your deductions."
    ),
    "suspect_innocent": (
        "You are an innocent suspect. "
        "Always tell the truth about the crime and your alibi."
    ),
    "suspect_criminal": (
        "You are the criminal suspect. "
        "You must lie to avoid being discovered. "
        "Be careful not to contradict yourself."
    )
}

def ask_agent(role, message):
    """Appelle Ollama avec un rôle donné et un message."""
    prompt = f"{roles[role]}\n\nConversation so far:\n{message}\n\nYour reply:"
    res = ollama.generate(model="gemma3:latest", prompt=prompt)
    return res["response"].strip()

# --- Choix du rôle par le joueur ---
print("🎮 Bienvenue dans le jeu du détective IA !")
player_role = input("👉 Choisis ton rôle (detective/suspect): ").strip().lower()

# --- Attribution des rôles ---
if player_role == "detective":
    print("🕵️ Tu es le détective. Trouve qui est coupable !")
    criminal = random.choice(["suspect1", "suspect2"])
    role1 = "suspect_criminal" if criminal == "suspect1" else "suspect_innocent"
    role2 = "suspect_criminal" if criminal == "suspect2" else "suspect_innocent"

    # Interrogatoire
    for _ in range(3):
        q = input("\n🕵️ Pose ta question aux suspects: ")

        ans1 = ask_agent(role1, q)
        ans2 = ask_agent(role2, q)

        print("👤 Suspect 1:", ans1)
        print("👤 Suspect 2:", ans2)

    # Verdict
    guess = input("\n🕵️ Qui est le coupable ? (suspect1/suspect2): ").strip().lower()
    if guess == criminal:
        print("✅ Bravo détective, tu as trouvé le vrai coupable !")
    else:
        print("❌ Mauvais choix... Le coupable était", criminal)

# --- Mode joueur = suspect ---
elif player_role == "suspect":
    print("👤 Tu es un suspect. Essaie de tromper le détective IA !")
    is_criminal = random.choice([True, False])  # le joueur peut être innocent ou coupable
    role_player = "suspect_criminal" if is_criminal else "suspect_innocent"
    other_role = "suspect_innocent" if role_player == "suspect_criminal" else "suspect_criminal"

    # Tour d’interrogatoire
    for _ in range(3):
        q = ask_agent("detective", "Ask a question to the suspects.")
        print("\n🕵️ Detective asks:", q)

        ans_player = input("👉 Ta réponse: ")
        ans_ai = ask_agent(other_role, q)

        print("👤 Suspect IA:", ans_ai)

        # Le détective analyse
        analysis = ask_agent("detective", f"Suspect (Player): {ans_player}\nSuspect (AI): {ans_ai}\nWho seems guilty?")
        print("🕵️ Detective:", analysis)

    # Verdict final
    verdict = ask_agent("detective", "Based on the interrogation, who is the criminal? Choose: player or AI.")
    print("\n⚖️ Verdict final du détective:", verdict)

    if ("player" in verdict.lower() and is_criminal) or ("ai" in verdict.lower() and not is_criminal):
        print("✅ Le détective a trouvé la vérité.")
    else:
        print("🎉 Bravo ! Tu as trompé le détective.")

else:
    print("⚠️ Rôle inconnu. Relance le jeu et choisis 'detective' ou 'suspect'.")
