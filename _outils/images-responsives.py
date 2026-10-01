# -*- coding: utf-8 -*-
"""Chaine d'images responsives : pour chaque image affichee dans une page,
produit r/<nom>-<largeur>.avif et .webp (480, 800, 1200). Idempotent : ne
refait que ce qui manque ou ce dont la source a change. Source = fichier
deja publie (p/NNN.webp, feature-*.webp...). Pour une nouvelle photo du
shooting, deposer l'original en haute definition dans _source/ avec le meme
nom : il sera prefere."""
import os, re, sys, glob
from PIL import Image
LARG = (480, 800, 1200)
Q = {"avif": 52, "webp": 74}
def sources():
    vus = set()
    for f in glob.glob("_contenu/*.html") + ["index.html"]:
        for m in re.finditer(r'<img[^>]*?\bsrc="((?:p/\d+|feature-[a-z]+|hero-poster|plats-poster)\.webp)"', open(f, encoding="utf-8").read()):
            vus.add(m.group(1))
    return sorted(vus)
def faire(src):
    base = os.path.splitext(os.path.basename(src))[0]
    hd = os.path.join("_source", base + ".jpg")
    orig = hd if os.path.exists(hd) else src
    im = Image.open(orig); im.load()
    if im.mode not in ("RGB", "RGBA"): im = im.convert("RGB")
    w0 = im.width; faits = []
    # la largeur d origine s ajoute quand elle depasse 1200 px (grandes images
    # pleine largeur sur ordinateur : 1440 px et plus)
    for w in LARG + ((w0,) if w0 > LARG[-1] else ()):
        if w > w0 and w != LARG[0]: continue
        for fmt in ("avif", "webp"):
            out = "r/%s-%d.%s" % (base, w, fmt)
            if os.path.exists(out) and os.path.getmtime(out) >= os.path.getmtime(orig): continue
            r = im if w >= w0 else im.resize((w, round(im.height * w / w0)), Image.LANCZOS)
            r.save(out, fmt.upper(), quality=Q[fmt])
            faits.append(out)
    return faits
if __name__ == "__main__":
    n = 0
    for s in sources(): n += len(faire(s))
    print("images responsives : %d fichiers produits" % n)
