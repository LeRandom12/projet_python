import random

def generate_case(lang="fr"):
    suspects = ["suspect1", "suspect2"]
    culprit = random.choice(suspects)

    alibis_en = {
        "suspect1": "At home watching TV from 20:00 to 23:00",
        "suspect2": "At the library from 20:30 to 22:00"
    }
    alibis_fr = {
        "suspect1": "Chez moi à regarder la TV de 20h00 à 23h00",
        "suspect2": "À la bibliothèque de 20h30 à 22h00"
    }

    evidence_en = {
        "murder_time": "21:15",
        "location": "Old library",
        "found_item": "A glove with traces of ink"
    }
    evidence_fr = {
        "murder_time": "21:15",
        "location": "vieille bibliothèque",
        "found_item": "Un gant avec des traces d’encre"
    }

    return {
        "culprit": culprit,
        "alibis": alibis_fr if lang == "fr" else alibis_en,
        "evidence": evidence_fr if lang == "fr" else evidence_en
    }


def build_suspect_prompt(lang, suspect_role, case, history, detective_question, who_tag):
    tr = case["alibis"][who_tag]
    ev = case["evidence"]

    if lang == "fr":
        innocent_hdr = (
            f"Tu es {who_tag}, suspect INNOCENT. Dis toujours la vérité.\n"
            f"Ton alibi réel: {tr}. Crime vers {ev['murder_time']} à la {ev['location']}.\n"
            f"Indice matériel: {ev['found_item']}."
        )
        criminal_hdr = (
            f"Tu es {who_tag}, suspect COUPABLE. Mens pour éviter d'être découvert.\n"
            f"Tu connais les faits réels (ne les dis pas tels quels): "
            f"crime {ev['murder_time']} à la {ev['location']}, indice: {ev['found_item']}.\n"
            f"N'écris rien d'invraisemblable, évite les contradictions."
        )
        lang_tail = "Réponds en français, de façon naturelle et concise."
    else:
        innocent_hdr = (
            f"You are {who_tag}, an INNOCENT suspect. Always tell the truth.\n"
            f"Your real alibi: {tr}. Crime around {ev['murder_time']} in the {ev['location']}.\n"
            f"Material clue: {ev['found_item']}."
        )
        criminal_hdr = (
            f"You are {who_tag}, the GUILTY suspect. Lie to avoid being discovered.\n"
            f"You know the real facts (do not reveal them literally): "
            f"crime {ev['murder_time']} at the {ev['location']}, clue: {ev['found_item']}.\n"
            f"Stay plausible and avoid contradictions."
        )
        lang_tail = "Reply in concise English."

    header = criminal_hdr if (suspect_role == "suspect_criminal") else innocent_hdr
    return f"{header}\n\nConversation:\n{history}\n\nDetective: {detective_question}\n{lang_tail}"
