import requests
from bs4 import BeautifulSoup
import ollama 

url = "https://tldr.tech/webdev/2025-09-29"
res = requests.get(url)

soup = BeautifulSoup(res.text, "html.parser")

for desc in soup.find_all("div", "newsletter-html"):
    text = desc.get_text(strip=True)
    print(text)

    res = ollama.generate(
        model="gemma3:latest",
        prompt=f"Write me a ten-word summary of the following text:\n\n{text}"
    )

    print("Synthèse par IA:", res["response"])
    break
