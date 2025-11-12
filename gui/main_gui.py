# gui/main_gui.py
import os
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext

from core.game_manager import GameManager

# --- Image & son ---
from PIL import Image, ImageTk
import pygame


def playsound(path):
    """Petite fonction pour jouer le son."""
    try:
        if os.path.isfile(path):
            pygame.mixer.init()
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
    except Exception:
        pass


class DetectiveGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🕵️ AI Detective Game")
        self.root.geometry("1000x700")
        self.root.minsize(900, 600)

        # -----------------------
        # Chemins et couleurs
        # -----------------------
        self.theme_path = "data/themes/interrogation"
        self.colors = {
            "bg": "#0b0c10",
            "panel": "#151821",
            "text": "#f1f5f9",
            "user": "#93c5fd",
            "ai": "#fcd34d",
            "system": "#94a3b8",
            "accent": "#3b82f6",
        }

        # -----------------------
        # Fenêtre principale
        # -----------------------
        self.root.configure(bg=self.colors["bg"])
        self.bg_label = tk.Label(self.root)
        self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        # Chargement du fond
        self._load_background()

        # Barre du haut
        self.top_frame = tk.Frame(self.root, bg=self.colors["bg"])
        self.top_frame.pack(fill=tk.X, padx=12, pady=(12, 6))

        # Logo
        self.logo_label = tk.Label(self.top_frame, bg=self.colors["bg"])
        self.logo_label.pack(side=tk.LEFT, padx=(0, 10))
        self._load_logo()

        # Titre
        self.title_lbl = tk.Label(
            self.top_frame, text="AI Detective Game",
            font=("Poppins", 22, "bold"), fg=self.colors["text"], bg=self.colors["bg"]
        )
        self.title_lbl.pack(side=tk.LEFT)

        # Zone de texte
        self.text_frame = tk.Frame(self.root, bg=self.colors["bg"])
        self.text_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 8))

        self.text_area = scrolledtext.ScrolledText(
            self.text_frame,
            wrap=tk.WORD,
            font=("JetBrains Mono", 11),
            bg=self.colors["panel"],
            fg=self.colors["text"],
            insertbackground=self.colors["accent"],
            relief=tk.FLAT,
            padx=10,
            pady=10
        )
        self.text_area.pack(fill=tk.BOTH, expand=True)
        self.text_area.tag_configure("user", foreground=self.colors["user"])
        self.text_area.tag_configure("ai", foreground=self.colors["ai"])
        self.text_area.tag_configure("system", foreground=self.colors["system"])
        self.text_area.tag_configure("bold", font=("JetBrains Mono", 11, "bold"))

        # Bas de page
        self.bottom = tk.Frame(self.root, bg=self.colors["bg"])
        self.bottom.pack(fill=tk.X, padx=12, pady=(0, 12))

        self.entry = ttk.Entry(self.bottom, font=("Segoe UI", 12))
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.entry.bind("<Return>", self.send_message)

        self.send_btn = ttk.Button(self.bottom, text="Envoyer", command=self.send_message)
        self.send_btn.pack(side=tk.RIGHT)

        # Charger les avatars
        self.avatars = {}
        self._load_avatars()

        # Style bouton
        self._style_ttk()

        # Jeu
        self.game = GameManager()
        self.display_ai(self.game.start_game(), typewriter=False)

    # -----------------------
    # Chargement des assets
    # -----------------------

    def _style_ttk(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Accent.TButton",
            font=("Segoe UI", 11, "bold"),
            padding=8,
            background=self.colors["accent"],
            foreground="black",
        )
        self.send_btn.configure(style="Accent.TButton")

    def _load_background(self):
        bg_path = os.path.join(self.theme_path, "background.jpg")
        if os.path.isfile(bg_path):
            try:
                img = Image.open(bg_path)
                img = img.resize((1100, 750))
                self.bg_img = ImageTk.PhotoImage(img)
                self.bg_label.configure(image=self.bg_img)
            except Exception as e:
                print("Erreur background:", e)

    def _load_logo(self):
        logo_path = os.path.join(self.theme_path, "logo.png")
        if os.path.isfile(logo_path):
            try:
                img = Image.open(logo_path).resize((70, 70))
                self.logo_img = ImageTk.PhotoImage(img)
                self.logo_label.configure(image=self.logo_img)
            except Exception as e:
                print("Erreur logo:", e)

    def _load_avatars(self):
        avatars_dir = os.path.join(self.theme_path, "avatars")
        files = {
            "detective": "detective.png",
            "suspect1": "suspect1.png",
            "suspect2": "suspect2.png",
            "player": "player.png",
        }
        for key, name in files.items():
            path = os.path.join(avatars_dir, name)
            if os.path.isfile(path):
                try:
                    img = Image.open(path).resize((40, 40))
                    self.avatars[key] = ImageTk.PhotoImage(img)
                except Exception as e:
                    print(f"Erreur avatar {key}:", e)

    # -----------------------
    # Affichage messages
    # -----------------------

    def _avatar_for_message(self, text: str, is_user: bool):
        if is_user:
            return "player"
        t = text.lower()
        if "suspect 1" in t:
            return "suspect1"
        if "suspect 2" in t:
            return "suspect2"
        if "détective" in t or "detective" in t:
            return "detective"
        return "detective"

    def _insert_message(self, text: str, tag: str, role="detective"):
        """Affiche un message avec avatar"""
        avatar = self.avatars.get(role)
        if avatar:
            self.text_area.image_create(tk.END, image=avatar)
            self.text_area.insert(tk.END, " ")
        self.text_area.insert(tk.END, text + "\n", (tag,))
        self.text_area.see(tk.END)

    def display_user(self, text: str):
        role = self._avatar_for_message(text, is_user=True)
        self._insert_message(f"🧑 You: {text}", "user", role)

    def display_ai(self, text: str, typewriter=True):
        role = self._avatar_for_message(text, is_user=False)
        self._insert_message(f"🤖 {text}", "ai", role)
        playsound("data/sounds/ding.mp3")

    def display_system(self, text: str):
        self._insert_message(f"ℹ️ {text}", "system")

    # -----------------------
    # Interaction
    # -----------------------

    def send_message(self, event=None):
        user_input = self.entry.get().strip()
        if not user_input:
            return
        self.entry.delete(0, tk.END)
        self.display_user(user_input)
        threading.Thread(target=self._process_turn, args=(user_input,), daemon=True).start()

    def _process_turn(self, text: str):
        reply = self.game.process_turn(text)
        self.root.after(0, lambda: self.display_ai(reply))


if __name__ == "__main__":
    root = tk.Tk()
    app = DetectiveGUI(root)
    root.mainloop()
