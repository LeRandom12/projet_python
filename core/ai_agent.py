import json
import ollama

def ask_agent(model, prompt, options=None):
    res = ollama.generate(model=model, prompt=prompt, options=options or {})
    return res["response"].strip()

def ask_agent_json(model, prompt, retries=2):
    for _ in range(retries + 1):
        resp = ollama.generate(model=model, prompt=prompt)["response"].strip()
        try:
            return json.loads(resp)
        except Exception:
            start, end = resp.find("{"), resp.rfind("}")
            if start != -1 and end != -1:
                try:
                    return json.loads(resp[start:end+1])
                except Exception:
                    pass
    return None

def detective_analysis_prompt(lang, history):
    if lang == "fr":
        return (
            "Tu es un détective. Analyse le dialogue ci-dessous et renvoie un JSON compact :\n"
            '{"suspect1":{"score":int,"motifs":["..."]},"suspect2":{"score":int,"motifs":["..."]},"incoherences":["..."]}\n'
            "score: 0=innocent, 100=très suspect.\n"
            f"Dialogue:\n{history}\nRéponds UNIQUEMENT en JSON."
        )
    else:
        return (
            "You are a detective. Analyze dialogue below and return compact JSON:\n"
            '{"suspect1":{"score":int,"motives":["..."]},"suspect2":{"score":int,"motives":["..."]},"inconsistencies":["..."]}\n'
            "score: 0=innocent, 100=highly suspicious.\n"
            f"Dialogue:\n{history}\nReply ONLY in JSON."
        )
