def use_card_prompt(lang, card, base_question, case):
    ev = case["evidence"]
    if lang == "fr":
        if card == "pression":
            return base_question + " (Réponds précisément, sans détour.)"
        if card == "piege":
            return f"Où étais-tu exactement à {ev['murder_time']} ?"
        if card == "preuve":
            return f"On a retrouvé {ev['found_item']}. Explique pourquoi cet indice pourrait te concerner."
    else:
        if card == "pression":
            return base_question + " (Answer precisely, no dodging.)"
        if card == "piege":
            return f"Where exactly were you at {ev['murder_time']}?"
        if card == "preuve":
            return f"We found {ev['found_item']}. Explain why this clue might relate to you."
    return base_question
