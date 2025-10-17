from PIL import Image, ImageTk
import numpy as np
from numba import njit
import tkinter as t
from tkinter import filedialog as fd, ttk
import os
def o(p,s=None):
 i=Image.open(p).convert('RGB')
 return np.array(i.resize((int(i.width*float(s)),int(i.height*float(s)))) if s else i,dtype=np.float32)
@njit
def fl(a):
 h,w=a.shape
 for i in range(h-1):
  for j in range(1,w-1):
   v=a[i,j];n=255. if v>=128. else 0.;e=v-n;a[i,j]=n
   a[i,j+1]+=e*.4375;a[i+1,j-1]+=e*.1875;a[i+1,j]+=e*.3125;a[i+1,j+1]+=e*.0625
 return np.clip(a,0,255)
@njit
def a_(a):
 h,w=a.shape
 for i in range(h-2):
  for j in range(2,w-2):
   v=a[i,j];n=255. if v>=128. else 0.;e=v-n;a[i,j]=n
   for x,y in[(0,1),(1,-1),(1,0),(1,1),(2,0),(0,2)]:a[i+x,j+y]+=e*.125
 return np.clip(a,0,255)
@njit
def s(a):
 h,w=a.shape
 for i in range(h-2):
  for j in range(2,w-2):
   v=a[i,j];n=255. if v>=128. else 0.;e=v-n;a[i,j]=n
   for x,y,c in[(0,1,.2),(1,-1,.1),(1,0,.2),(1,1,.1),(2,0,.1),
                (0,2,.1),(2,2,.025),(1,-2,.05),(1,2,.05),
                (2,-2,.025),(2,1,.05),(2,-1,.05)]:a[i+x,j+y]+=e*c
 return np.clip(a,0,255)
@njit
def g(i):
 h,w=i.shape[:2];r=np.empty((h,w),np.float32)
 for y in range(h):
  for x in range(w):r[y,x]=.2989*i[y,x][0]+.587*i[y,x][1]+.114*i[y,x][2]
 return r
def conv(img):
    return(Image.fromarray(arr, mode='L'))


def decouper_image(path, nb_colonnes):
    image=(Image.fromarray(path.astype(np.uint8),'L'))
    image.show()
    largeur, hauteur=image.size
    if nb_colonnes > largeur:
        print(f"⚠️ Attention: nb_colonnes ({nb_colonnes}) trop grand, ajustement à {largeur}")
        nb_colonnes = largeur
    largeur_colonne = largeur // nb_colonnes
    hauteur_bloc = max(1, int(largeur_colonne * (5 / 3)))
    nb_blocs_verticaux = max(1, hauteur // hauteur_bloc)
    liste_blocs = []
    for col in range(nb_colonnes):
        x0 = col * largeur_colonne
        x1 = x0 + largeur_colonne
        colonne_blocs = []
        for ligne in range(nb_blocs_verticaux):
            y0 = ligne * hauteur_bloc
            y1 = y0 + hauteur_bloc
            bloc = image.crop((x0, y0, x1, y1))
            colonne_blocs.append(bloc)
        liste_blocs.append(colonne_blocs)

    return liste_blocs
def reduire_en_nb_2x4(image):
    image = image.convert("L")
    image = image.resize((2, 4), resample=Image.BICUBIC)
    image_bn = image.convert("1")
    return image_bn
def image_vers_caractere_braille(image):
    if image.size != (2, 4):
        raise ValueError("L'image doit faire exactement 2x4 pixels")
    image = image.convert("1")
    pixels = image.load()
    mapping = [(0, 0),(0, 1),(0, 2),(1, 0),(1, 1),(1, 2),(0, 3),(1, 3),]
    code_braille = 0
    for i, (x, y) in enumerate(mapping):
        if pixels[x, y] == 0:
            code_braille |= (1 << i)
    caractere = chr(0x2800 + code_braille)
    return caractere  
def inverser_braille(car):
    code = ord(car)
    if not (0x2800 <= code <= 0x28FF):
        raise ValueError("Caractère non braille.")
    bits = code - 0x2800
    bits_inverse = bits ^ 0b11111111
    return chr(0x2800 + bits_inverse)
def full_invert(liste):
    for i in range(len(liste)):
        for j in range(len(liste[0])):
            liste[i][j]=inverser_braille(liste[i][j])
    return liste
def enregistrer_liste_liste(fichier, tableau):
    with open(fichier, "w", encoding="utf-8") as f:
        for ligne in tableau:
            f.write("".join(ligne) + "\n")
    os.startfile(fichier)
def act(path, column, ver, quality=None, invert=True):
    img=g(o(path,quality))
    if ver==1:img=fl(img)
    elif ver==2:img=a_(img)
    else:img==s(img)
    img=decouper_image(img,column)
    img = [list(row) for row in zip(*img)]
    for i in range(len(img)):
        for j in range(len(img[0])):
            img[i][j]=image_vers_caractere_braille(reduire_en_nb_2x4(img[i][j]))
    if invert:
        img=full_invert(img)
    for i in range(len(img)):
        img[i]=''.join(img[i])
        print(img[i])
    enregistrer_liste_liste('a.txt',img)
    
act('asuka.jpg',50,2,3)