#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CONSTRUIT LE SITE DE LA MAISON LOUISETTE.

    python3 construire.py

Il lit :
    _donnees/site.json    les informations de la maison (horaires, telephones, liens, navigation)
    _donnees/pages.json   le titre et la description de chaque page
    _contenu/<page>.html  le texte de chaque page, sans en-tete ni pied de page

Il ecrit :
    <page>.html           les pages completes, pretes a publier
    index.html            uniquement la navigation et le pied de page y sont remis a jour
    sitemap.xml

RIEN D'AUTRE N'EST TOUCHE. Le fichier index.html garde tout son contenu :
seuls les blocs entre les marqueurs <!-- NAV:debut --> ... <!-- NAV:fin -->
et <!-- PIED:debut --> ... <!-- PIED:fin --> sont remplaces.
"""
import io, os, json, re, sys

RACINE = os.path.dirname(os.path.abspath(__file__))
def lire(p):  return io.open(os.path.join(RACINE, p), encoding="utf-8").read()
def ecrire(p, t): io.open(os.path.join(RACINE, p), "w", encoding="utf-8").write(t)

S = json.loads(lire("_donnees/site.json"))
P = json.loads(lire("_donnees/pages.json"))

# ----------------------------------------------------------------- morceaux communs
def navigation(courante):
    return ('<nav class="nav" aria-label="Navigation principale">'
            + "".join('<a href="%s"%s>%s</a>' % (h, ' aria-current="page"' if h == courante else '', l)
                      for h, l in S["navigation"]) + '</nav>')

def tiroir():
    liens = S["navigation"] + S["tiroir_extra"]
    return ('<div class="tiroir" id="tiroir" role="dialog" aria-modal="true" aria-label="Menu">'
            '<div class="haut"><span class="n"><b>L</b>ouisette</span>'
            '<button class="x" id="tiroirX" aria-label="Fermer le menu">✕</button></div>'
            + "".join('<a class="lien" href="%s">%s</a>' % (h, l) for h, l in liens)
            + '<a class="resa" href="%s" target="_blank" rel="noopener">Réserver une table</a></div>' % S["reservation"])

def barre(courante=None):
    return ('<div class="minihd" id="minihd">'
            '<span class="n"><a href="./" style="color:inherit;text-decoration:none"><b>L</b>ouisette</a></span>'
            + navigation(courante) +
            '<button class="burger" id="burger" aria-label="Ouvrir le menu" aria-expanded="false">☰</button>'
            '<a href="%s" target="_blank" rel="noopener">Réserver</a></div>' % S["reservation"])

def pied():
    cols = "".join('<div><h3>%s</h3>%s</div>' % (titre, "".join('<a href="%s">%s</a>' % (h, l) for h, l in liens))
                   for titre, liens in S["pied"])
    ts, tg = S["tel_salle"], S["tel_groupes"]
    return ('<footer class="foot"><div class="wrap">'
            '<div class="plan">' + cols + '</div>'
            '<b>%s</b>'
            '<p>%s — métro %s</p>'
            '<p>%s — <a href="tel:%s" style="color:inherit">%s</a> · groupes <a href="tel:%s" style="color:inherit">%s</a></p>'
            '<p><a href="mailto:%s" style="color:inherit">%s</a></p>'
            '<p class="evin">%s</p>'
            '</div></footer>' % (S["nom"], S["adresse"], S["metro"].split(" — ")[0],
                                 S["horaires"], ts["lien"], ts["affiche"], tg["lien"], tg["affiche"],
                                 S["email"], S["email"], S["mention_alcool"]))

def dock():
    ts, tg = S["tel_salle"], S["tel_groupes"]
    return ('<div class="dock" id="dock">'
            '<a class="btn" href="%s" target="_blank" rel="noopener">Réserver</a>'
            '<a class="btn ghost" href="tel:%s" aria-label="Appeler le %s">Appeler</a>'
            '<a class="btn ghost" href="tel:%s" aria-label="Appeler la ligne groupes">Groupe</a>'
            '</div>' % (S["reservation"], ts["lien"], ts["affiche"], tg["lien"]))

FAVICON = ("data:image/svg+xml,%3Csvg%20xmlns%3D%27http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%27%20viewBox%3D%270%200%2064%2064%27%3E"
           "%3Crect%20width%3D%2764%27%20height%3D%2764%27%20rx%3D%2712%27%20fill%3D%27%230C0910%27%2F%3E%3Ctext%20x%3D%2732%27%20"
           "y%3D%2746%27%20font-family%3D%27Didot%2CBodoni%20MT%2CTimes%20New%20Roman%2Cserif%27%20font-size%3D%2744%27%20"
           "font-style%3D%27italic%27%20fill%3D%27%23FF5FC4%27%20text-anchor%3D%27middle%27%3EL%3C%2Ftext%3E%3C%2Fsvg%3E")

POLICES = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
           '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
           '<link href="https://fonts.googleapis.com/css2?family=Bodoni+Moda:ital,opsz,wght@0,6..96,400;0,6..96,500;'
           '0,6..96,600;1,6..96,400;1,6..96,500&family=Instrument+Sans:wght@400;500;600&display=swap" rel="stylesheet">')

def fil(nom):
    return '<nav class="ariane" aria-label="Fil d\'Ariane"><a href="./">Accueil</a> · %s</nav>' % nom

def ariane_ld(nom, slug):
    return ('<script type="application/ld+json">{"@context":"https://schema.org","@type":"BreadcrumbList",'
            '"itemListElement":[{"@type":"ListItem","position":1,"name":"Accueil","item":"https://louisette-paris.com/"},'
            '{"@type":"ListItem","position":2,"name":"%s","item":"https://louisette-paris.com/%s"}]}</script>' % (nom, slug))

# ----------------------------------------------------------------- une page
def page(slug):
    m = P[slug]; f = slug + ".html"
    corps = lire("_contenu/%s.html" % slug)
    h = ['<!DOCTYPE html>', '<html lang="fr">', '<head>',
         '<meta charset="utf-8">',
         '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">',
         '<title>%s</title>' % m["titre"],
         '<meta name="description" content="%s">' % m["description"],
         '<meta name="robots" content="noindex,nofollow">',
         '<meta name="theme-color" content="#0C0910">',
         '<link rel="icon" href="%s">' % FAVICON,
         '<meta property="og:type" content="article">',
         '<meta property="og:site_name" content="%s">' % S["nom"],
         '<meta property="og:locale" content="fr_FR">',
         '<meta property="og:title" content="%s">' % m["og_titre"],
         '<meta property="og:description" content="%s">' % m["description"],
         '<link rel="canonical" href="https://louisette-paris.com/%s">' % f,
         POLICES,
         '<link rel="stylesheet" href="assets/site.css">',
         ariane_ld(m["ariane"], f),
         '</head>', '<body class="page">',
         '<a href="#contenu" class="skip">Aller au contenu</a>',
         '<div class="grain" aria-hidden="true"></div>',
         barre(f), tiroir(), fil(m["ariane"]),
         '<main id="contenu">', corps, '</main>',
         pied(), dock(),
         '<script src="assets/mesure.js" defer></script>',
         '<script src="assets/site.js" defer></script>',
         '</body>', '</html>']
    ecrire(f, "\n".join(h))
    return f

# ----------------------------------------------------------------- l'accueil
def accueil():
    """Ne remplace que les blocs marques. Tout le reste d'index.html est intact."""
    h = lire("index.html"); avant = h
    for nom, contenu in (("NAV", barre() + "\n" + tiroir()), ("PIED", pied()), ("DOCK", dock())):
        motif = re.compile(r'<!-- %s:debut -->.*?<!-- %s:fin -->' % (nom, nom), re.S)
        if motif.search(h):
            h = motif.sub('<!-- %s:debut -->%s<!-- %s:fin -->' % (nom, contenu, nom), h)
        else:
            print("   ATTENTION : marqueurs %s absents d'index.html, bloc non mis a jour" % nom)
    if h != avant:
        ecrire("index.html", h); return "mis a jour"
    return "deja a jour"

# ----------------------------------------------------------------- sitemap
def sitemap(faites):
    urls = [""] + faites + ["mentions-legales.html", "confidentialite.html"]
    from datetime import date
    d = date.today().isoformat()
    ecrire("sitemap.xml",
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join('<url><loc>https://louisette-paris.com/%s</loc><lastmod>%s</lastmod></url>\n' % (u, d) for u in urls)
        + '</urlset>\n')

# ----------------------------------------------------------------- controles
def controler(faites):
    pbs = []
    presentes = set(os.listdir(RACINE))
    for f in faites + ["index.html"]:
        t = lire(f)
        for l in set(re.findall(r'href="([a-z0-9-]+\.html)(?:#[^"]*)?"', t)):
            if l not in presentes: pbs.append("%s : lien mort vers %s" % (f, l))
        if re.search(r'\d\s?€', t) and f != "index.html":
            pbs.append("%s : un prix apparait alors que les prix ne sont pas reconcilies" % f)
        if "8h30" in t or "8 h 30" in t: pbs.append("%s : horaire 8h30" % f)
        for mot in ("100 % maison", "tout fait maison", "entièrement travaillée sur place"):
            if mot in t: pbs.append('%s : formulation interdite "%s"' % (f, mot))
        if "abus d'alcool" not in t: pbs.append("%s : mention alcool absente" % f)
    return pbs

if __name__ == "__main__":
    faites = [page(s) for s in sorted(P)]
    print("pages construites :", ", ".join(faites))
    print("accueil :", accueil())
    sitemap(faites); print("sitemap.xml ecrit")
    pbs = controler(faites)
    if pbs:
        print("\nCONTROLES EN ECHEC :"); [print("   -", p) for p in pbs]; sys.exit(1)
    print("\ncontroles : tout est bon.")
