import numpy as np
from PIL import Image
from numba import njit
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os

# --- Traitements N&B et Braille ---

def o(p, s=None):
    i = Image.open(p).convert('RGB')
    return np.array(i.resize((int(i.width * float(s)), int(i.height * float(s)))) if s else i, dtype=np.float32)

@njit
def fl(a):
    h, w = a.shape
    for i in range(h - 1):
        for j in range(1, w - 1):
            v = a[i, j]
            n = 255. if v >= 128. else 0.
            e = v - n
            a[i, j] = n
            a[i, j + 1] += e * 0.4375
            a[i + 1, j - 1] += e * 0.1875
            a[i + 1, j] += e * 0.3125
            a[i + 1, j + 1] += e * 0.0625
    return np.clip(a, 0, 255)

@njit
def a_(a):
    h, w = a.shape
    for i in range(h - 2):
        for j in range(2, w - 2):
            v = a[i, j]
            n = 255. if v >= 128. else 0.
            e = v - n
            a[i, j] = n
            for x, y in [(0, 1), (1, -1), (1, 0), (1, 1), (2, 0), (0, 2)]:
                a[i + x, j + y] += e * 0.125
    return np.clip(a, 0, 255)

@njit
def s(a):
    h, w = a.shape
    for i in range(h - 2):
        for j in range(2, w - 2):
            v = a[i, j]
            n = 255. if v >= 128. else 0.
            e = v - n
            a[i, j] = n
            for x, y, c in [(0, 1, .2), (1, -1, .1), (1, 0, .2), (1, 1, .1), (2, 0, .1),
                            (0, 2, .1), (2, 2, .025), (1, -2, .05), (1, 2, .05),
                            (2, -2, .025), (2, 1, .05), (2, -1, .05)]:
                a[i + x, j + y] += e * c
    return np.clip(a, 0, 255)

@njit
def g(i):
    h, w = i.shape[:2]
    r = np.empty((h, w), np.float32)
    for y in range(h):
        for x in range(w):
            r[y, x] = 0.2989 * i[y, x][0] + 0.587 * i[y, x][1] + 0.114 * i[y, x][2]
    return r

def decouper_image(path_array, nb_colonnes):
    image = Image.fromarray(path_array.astype(np.uint8), 'L')
    largeur, hauteur = image.size
    nb_colonnes = min(nb_colonnes, largeur)
    largeur_colonne = largeur // nb_colonnes
    hauteur_bloc = max(1, int(largeur_colonne * (5 / 3)))
    nb_blocs_verticaux = max(1, hauteur // hauteur_bloc)
    liste_blocs = []
    for col in range(nb_colonnes):
        x0, x1 = col * largeur_colonne, (col + 1) * largeur_colonne
        colonne_blocs = []
        for ligne in range(nb_blocs_verticaux):
            y0, y1 = ligne * hauteur_bloc, (ligne + 1) * hauteur_bloc
            bloc = image.crop((x0, y0, x1, y1))
            colonne_blocs.append(bloc)
        liste_blocs.append(colonne_blocs)
    return liste_blocs

def reduire_en_nb_2x4(image):
    image = image.convert("L")
    image = image.resize((2, 4), resample=Image.BICUBIC)
    return image.convert("1")

def image_vers_caractere_braille(image):
    pixels = image.load()
    mapping = [(0, 0), (0, 1), (0, 2), (1, 0),
               (1, 1), (1, 2), (0, 3), (1, 3)]
    code_braille = 0
    for i, (x, y) in enumerate(mapping):
        if pixels[x, y] == 0:
            code_braille |= (1 << i)
    return chr(0x2800 + code_braille)

def inverser_braille(car):
    code = ord(car)
    bits = code - 0x2800
    bits_inverse = bits ^ 0b11111111
    return chr(0x2800 + bits_inverse)

def full_invert(liste):
    return [[inverser_braille(car) for car in ligne] for ligne in liste]

def enregistrer_liste_liste(fichier, tableau):
    with open(fichier, "w", encoding="utf-8") as f:
        for ligne in tableau:
            f.write("".join(ligne) + "\n")
    os.startfile(fichier)

def act(path, column, ver, quality=None, invert=True, output="ascii.txt"):

    img = g(o(path, quality))
    if ver == 1:
        img = fl(img)
    elif ver == 2:
        img = a_(img)
    else:
        img = s(img)
    img = decouper_image(img, column)
    img = [list(row) for row in zip(*img)]
    for i in range(len(img)):
        for j in range(len(img[0])):
            img[i][j] = image_vers_caractere_braille(reduire_en_nb_2x4(img[i][j]))
    if invert:
        img = full_invert(img)
    for i in range(len(img)):
        img[i] = ''.join(img[i])
    enregistrer_liste_liste(output, img)


# --- Interface graphique ---

class BrailleApp:
    def __init__(self, root):
        self.root = root
        self.path = None
        root.title("Convertisseur Braille ⠿")
        frame = tk.Frame(root, padx=10, pady=10)
        frame.pack()

        tk.Button(frame, text="📂 Choisir une image", command=self.choisir_image).grid(row=0, column=0, columnspan=2, pady=8, sticky='ew')

        tk.Label(frame, text="Colonnes :").grid(row=1, column=0, sticky="e")
        self.colonnes_var = tk.IntVar(value=50)
        tk.Entry(frame, textvariable=self.colonnes_var).grid(row=1, column=1)

        tk.Label(frame, text="Qualité (1–5) :").grid(row=2, column=0, sticky="e")
        self.qualite_var = tk.DoubleVar(value=1.0)
        tk.Entry(frame, textvariable=self.qualite_var).grid(row=2, column=1)

        tk.Label(frame, text="Filtre :").grid(row=3, column=0, sticky="e")
        self.filtre_var = tk.StringVar(value="AR")
        ttk.Combobox(frame, textvariable=self.filtre_var, values=["Floyd", "AR", "Stucki"], state="readonly").grid(row=3, column=1)

        self.inverser_var = tk.BooleanVar(value=True)
        tk.Checkbutton(frame, text="Inverser l'image (braille négatif)", variable=self.inverser_var).grid(row=4, columnspan=2, pady=5)

        tk.Label(frame, text="Nom du fichier (ex: resultat.txt) :").grid(row=5, column=0, sticky="e")
        self.filename_var = tk.StringVar(value="ascii.txt")
        tk.Entry(frame, textvariable=self.filename_var).grid(row=5, column=1)

        tk.Button(frame, text="🔁 Lancer la conversion", command=self.lancer).grid(row=6, columnspan=2, pady=10, sticky='ew')

    def choisir_image(self):
        self.path = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.bmp")])

    def lancer(self):
        if not self.path or not os.path.exists(self.path):
            messagebox.showerror("Erreur", "Aucune image valide sélectionnée.")
            return

        try:
            col = int(self.colonnes_var.get())
            qual = float(self.qualite_var.get())
            if qual > 5.0:
                raise ValueError("Qualité trop élevée.")
            filtre = self.filtre_var.get().lower()
            ver = {"floyd": 1, "ar": 2, "stucki": 3}[filtre]
            inv = self.inverser_var.get()
            nom_fichier = self.filename_var.get().strip() or "ascii.txt"
            act(self.path, col, ver, qual, inv, nom_fichier)
            messagebox.showinfo("Succès", f"Conversion terminée ! Résultat enregistré dans '{nom_fichier}'")
        except Exception as e:
            messagebox.showerror("Oups !", f"Une erreur s’est produite :\n{e}")

# Lancement
if __name__ == "__main__":
    root = tk.Tk()
    app = BrailleApp(root)
    root.mainloop()
