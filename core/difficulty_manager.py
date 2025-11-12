# core/difficulty_manager.py
def gen_opts_for_difficulty(level):
    if level == "easy":
        return {"temperature": 0.9, "num_predict": 200}
    if level == "hard":
        return {"temperature": 0.4, "num_predict": 160}
    return {"temperature": 0.7, "num_predict": 180}
