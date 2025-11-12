# gui/main_gui.py
import tkinter as tk
from tkinter import ttk, scrolledtext
import threading

from core.game_manager import GameManager


class DetectiveGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🕵️ AI Detective Game")
        self.root.geometry("800x560")
        self.root.configure(bg="#1e1e1e")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TLabel", background="#1e1e1e", foreground="white", font=("Segoe UI", 11))
        style.configure("TButton", font=("Segoe UI", 11, "bold"), padding=6)
        style.configure("TEntry", padding=6)

        self.text_area = scrolledtext.ScrolledText(
            self.root, wrap=tk.WORD, bg="#252526", fg="white",
            insertbackground="white", font=("Consolas", 11)
        )
        self.text_area.pack(padx=10, pady=(10, 6), fill=tk.BOTH, expand=True)

        bottom = ttk.Frame(self.root)
        bottom.pack(padx=10, pady=(0, 10), fill=tk.X)

        self.entry = ttk.Entry(bottom)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.entry.bind("<Return>", self.send_message)

        self.send_btn = ttk.Button(bottom, text="Envoyer", command=self.send_message)
        self.send_btn.pack(side=tk.RIGHT)

        self.game = GameManager()
        # bootstrap: afficher la première invite (choix langue)
        first = self.game.start_game()
        self.display_ai(first)

    # ----------------------
    def display_user(self, text: str):
        self.text_area.insert(tk.END, f"🧑 {text}\n")
        self.text_area.see(tk.END)

    def display_ai(self, text: str):
        self.text_area.insert(tk.END, f"🤖 {text}\n")
        self.text_area.see(tk.END)

    # ----------------------
    def send_message(self, event=None):
        user_input = self.entry.get().strip()
        if not user_input:
            return
        self.entry.delete(0, tk.END)
        self.display_user(user_input)

        # Thread pour éviter de geler l'UI pendant l'appel IA
        threading.Thread(target=self._process_turn_async, args=(user_input,), daemon=True).start()

    def _process_turn_async(self, user_input: str):
        reply = self.game.process_turn(user_input)
        self.display_ai(reply)


if __name__ == "__main__":
    root = tk.Tk()
    app = DetectiveGUI(root)
    root.mainloop()
