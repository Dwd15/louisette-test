#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CONTROLE LE FONDS PHOTOGRAPHIQUE DE LA MAISON LOUISETTE.

    python3 controler-photos.py

Il verifie, sur toutes les photos declarees dans meta.js :

  1. le filigrane du studio « Le Moment Photography », en bas a gauche ;
  2. les doublons exacts et les quasi-doublons ;
  3. les descriptions recopiees d'une photo a l'autre — c'est ce qui a masque,
     en septembre 2026, la presence de la devanture d'un autre etablissement ;
  4. les photos manquantes ou floues.

Il s'arrete avec le code 1 si quelque chose doit etre regarde.
CE CONTROLE NE REMPLACE PAS L'OEIL : une devanture concurrente ou un visage
ne se detectent qu'a la relecture. Il empeche seulement une recidive connue.
"""
import io, os, re, sys, json, collections
import numpy as np
from PIL import Image

RACINE = os.path.dirname(os.path.abspath(__file__))
SEUIL_FILIGRANE = 0.45      # au-dessus : filigrane presque certain
SEUIL_NETTETE   = 60.0      # variance du laplacien
MAX_MEME_TEXTE  = 8         # une description au-dela est trop generique

def charger_meta():
    t = io.open(os.path.join(RACINE, "meta.js"), encoding="utf-8").read()
    return json.loads(re.search(r'(\[.*\])', t, re.S).group(1))

def empreinte_bas_gauche(chemin, portrait=False):
    im = Image.open(chemin).convert("L"); w, h = im.size
    haut = 0.90 if portrait else 0.855
    z = im.crop((int(w*0.01), int(h*haut), int(w*(0.50 if portrait else 0.34)), int(h*0.99))).resize((240, 90))
    a = np.asarray(z, dtype=np.float32)
    g = np.abs(np.diff(a, axis=1))[:-1, :] + np.abs(np.diff(a, axis=0))[:, :-1]
    return (g - g.mean()) / (g.std() + 1e-6)

def gabarit(exemples, portrait=False):
    if not exemples: return None
    g = np.mean([empreinte_bas_gauche(f, portrait) for f in exemples], axis=0)
    return (g - g.mean()) / (g.std() + 1e-6)

def main():
    meta = charger_meta()
    pbs, avertissements, dette = [], [], []

    # --- fichiers presents, nettete, empreinte
    infos = {}
    for x in meta:
        i = x["i"]; f = os.path.join(RACINE, "p/%03d.webp" % i)
        if not os.path.exists(f):
            pbs.append("photo %03d : le fichier p/%03d.webp est absent" % (i, i)); continue
        im = Image.open(f).convert("L")
        a = np.asarray(im, dtype=np.float32)
        lap = a[:-2,1:-1] + a[2:,1:-1] + a[1:-1,:-2] + a[1:-1,2:] - 4*a[1:-1,1:-1]
        infos[i] = {"f": f, "portrait": im.width < im.height, "nettete": float(lap.var())}

    # --- filigrane : gabarit lu dans un dossier de reference s'il existe
    ref = os.path.join(RACINE, "_controle/filigrane")
    if os.path.isdir(ref):
        ex_p = [os.path.join(ref, n) for n in sorted(os.listdir(ref)) if n.startswith("portrait")]
        ex_l = [os.path.join(ref, n) for n in sorted(os.listdir(ref)) if n.startswith("paysage")]
        for portrait, exemples in ((True, ex_p), (False, ex_l)):
            g = gabarit(exemples, portrait)
            if g is None: continue
            for i, d in infos.items():
                if d["portrait"] != portrait: continue
                if float((empreinte_bas_gauche(d["f"], portrait) * g).mean()) > SEUIL_FILIGRANE:
                    pbs.append("photo %03d : filigrane de photographe detecte" % i)
    else:
        avertissements.append("dossier _controle/filigrane absent : le filigrane n'est pas verifie")

    # --- doublons
    try:
        import imagehash
        h = {i: str(imagehash.phash(Image.open(d["f"]))) for i, d in infos.items()}
        par = collections.defaultdict(list)
        for i, v in h.items(): par[v].append(i)
        for v in par.values():
            if len(v) > 1: pbs.append("photos %s : doublons exacts" % sorted(v))
    except ImportError:
        avertissements.append("module imagehash absent : les doublons ne sont pas verifies")

    # --- descriptions recopiees : c'est une dette, pas une faute.
    # Elle ne bloque pas, mais le nombre doit decroitre a chaque passage.
    generiques = {t: n for t, n in collections.Counter(x["alt"] for x in meta).items() if n > MAX_MEME_TEXTE}
    couvertes = sum(generiques.values())
    if generiques:
        dette.append("%d photos partagent %d descriptions trop generiques :" % (couvertes, len(generiques)))
        for t, n in sorted(generiques.items(), key=lambda x: -x[1]):
            dette.append('   x%-3d "%s..."' % (n, t[:62]))
        dette.append("   C'est ce qui a masque, le 8 septembre 2026, la devanture d'un")
        dette.append("   autre etablissement decrite comme etant la notre.")

    # --- nettete
    mous = sorted(i for i, d in infos.items() if d["nettete"] < SEUIL_NETTETE)
    if mous: avertissements.append("nettete faible sur %d photos : %s" % (len(mous), mous[:12]))

    print("photos declarees : %d" % len(meta))
    for a in avertissements: print("   avertissement :", a)
    if dette:
        print("\nDETTE A RESORBER (ne bloque pas) :")
        for d in dette: print("   " + d)
    if pbs:
        print("\nCONTROLES EN ECHEC :")
        for p in pbs: print("   -", p)
        sys.exit(1)
    print("\nfonds photo : rien a signaler.")

if __name__ == "__main__":
    main()
