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

DANS LES FICHIERS _donnees/*.json ON ECRIT DU TEXTE ORDINAIRE.
On ecrit "Bar & cocktails", pas "Bar &amp; cocktails" : le generateur
s'occupe seul de la mise en forme HTML. Les deux ecritures fonctionnent,
mais le texte ordinaire est celui qu'il faut utiliser.
"""
import io, os, json, re, sys

RACINE = os.path.dirname(os.path.abspath(__file__))
def lire(p):  return io.open(os.path.join(RACINE, p), encoding="utf-8").read()
def ecrire(p, t): io.open(os.path.join(RACINE, p), "w", encoding="utf-8").write(t)

def charger(p):
    """Lit un fichier de donnees et s'arrete avec un message clair s'il est mal ecrit."""
    try:
        return json.loads(lire(p))
    except ValueError as e:
        print("ARRET : le fichier %s est mal ecrit." % p)
        print("        %s" % e)
        print("        Cherchez a cet endroit une virgule en trop, une virgule qui manque,")
        print("        un guillemet non ferme ou une accolade en trop. Rien n'a ete publie.")
        sys.exit(1)
    except IOError:
        print("ARRET : le fichier %s est introuvable. Rien n'a ete publie." % p)
        sys.exit(1)

S = charger("_donnees/site.json")
P = charger("_donnees/pages.json")

def esc(t):
    """Met un texte en forme pour le HTML. Deja mis en forme, il ne bouge pas."""
    t = re.sub(r'&(?!#?[0-9A-Za-z]{1,10};)', '&amp;', str(t))
    return t.replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')

def txt(t):
    """Texte nu, pour le JSON-LD : les entites HTML y sont interdites."""
    t = str(t).replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"')
    return json.dumps(t, ensure_ascii=False)

# ----------------------------------------------------------------- morceaux communs
def navigation(courante):
    return ('<nav class="nav" aria-label="Navigation principale">'
            + "".join('<a href="%s"%s>%s</a>' % (esc(h), ' aria-current="page"' if h == courante else '', esc(l))
                      for h, l in S["navigation"]) + '</nav>')

def tiroir():
    liens = S["navigation"] + S["tiroir_extra"]
    return ('<div class="tiroir" id="tiroir" role="dialog" aria-modal="true" aria-label="Menu">'
            '<div class="haut"><span class="n"><b>L</b>ouisette</span>'
            '<button class="x" id="tiroirX" aria-label="Fermer le menu">&#10005;</button></div>'
            + "".join('<a class="lien" href="%s">%s</a>' % (esc(h), esc(l)) for h, l in liens)
            + '<a class="resa" href="%s" target="_blank" rel="noopener">Réserver une table</a></div>' % esc(S["reservation"]))

def barre(courante=None):
    return ('<div class="minihd" id="minihd">'
            '<span class="n"><a href="./" style="color:inherit;text-decoration:none"><b>L</b>ouisette</a></span>'
            + navigation(courante) +
            '<button class="burger" id="burger" aria-label="Ouvrir le menu" aria-expanded="false">&#9776;</button>'
            '<a href="%s" target="_blank" rel="noopener">Réserver</a></div>' % esc(S["reservation"]))

def pied():
    cols = "".join('<div><h3>%s</h3>%s</div>' % (esc(titre), "".join('<a href="%s">%s</a>' % (esc(h), esc(l)) for h, l in liens))
                   for titre, liens in S["pied"])
    ts, tg = S["tel_salle"], S["tel_groupes"]
    soc = "".join('<a href="%s" target="_blank" rel="noopener me">%s</a>' % (esc(u), esc(n))
                  for n, u in S.get("reseaux", []))
    soc = ('<div class="soc" aria-label="Nos reseaux">' + soc + '</div>') if soc else ""
    return ('<footer class="foot"><div class="wrap">'
            '<div class="plan">' + cols + '</div>' + soc +
            '<b>%s</b>'
            '<p>%s — métro %s</p>'
            '<p>%s — <a href="tel:%s" style="color:inherit">%s</a> · groupes <a href="tel:%s" style="color:inherit">%s</a></p>'
            '<p><a href="mailto:%s" style="color:inherit">%s</a></p>'
            '<p class="evin">%s</p>'
            '</div></footer>' % (esc(S["nom"]), esc(S["adresse"]), esc(S["metro"].split(" — ")[0]),
                                 esc(S["horaires"]), esc(ts["lien"]), esc(ts["affiche"]), esc(tg["lien"]), esc(tg["affiche"]),
                                 esc(S["email"]), esc(S["email"]), esc(S["mention_alcool"])))

def dock():
    ts, tg = S["tel_salle"], S["tel_groupes"]
    return ('<div class="dock" id="dock">'
            '<a class="btn" href="%s" target="_blank" rel="noopener">Réserver</a>'
            '<a class="btn ghost" href="tel:%s" aria-label="Appeler le %s">Appeler</a>'
            '<a class="btn ghost" href="tel:%s" aria-label="Appeler la ligne groupes">Groupe</a>'
            '</div>' % (esc(S["reservation"]), esc(ts["lien"]), esc(ts["affiche"]), esc(tg["lien"])))

FAVICON = ("data:image/svg+xml,%3Csvg%20xmlns%3D%27http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%27%20viewBox%3D%270%200%2064%2064%27%3E"
           "%3Crect%20width%3D%2764%27%20height%3D%2764%27%20rx%3D%2712%27%20fill%3D%27%230C0910%27%2F%3E%3Ctext%20x%3D%2732%27%20"
           "y%3D%2746%27%20font-family%3D%27Didot%2CBodoni%20MT%2CTimes%20New%20Roman%2Cserif%27%20font-size%3D%2744%27%20"
           "font-style%3D%27italic%27%20fill%3D%27%23FF5FC4%27%20text-anchor%3D%27middle%27%3EL%3C%2Ftext%3E%3C%2Fsvg%3E")

# La feuille de Google bloquait l'affichage pendant 400 ms : on la charge
# sans bloquer, et le navigateur affiche le texte avec la police de secours
# en attendant (display=swap).
_GF = ("https://fonts.googleapis.com/css2?family=Bodoni+Moda:ital,opsz,wght@0,6..96,400;0,6..96,500;"
       "0,6..96,600;1,6..96,400;1,6..96,500&family=Instrument+Sans:wght@400;500;600&display=swap")
POLICES = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
           '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
           '<link rel="preload" as="style" href="%s">'
           '<link rel="stylesheet" href="%s" media="print" onload="this.media=\'all\'">'
           '<noscript><link rel="stylesheet" href="%s"></noscript>' % (_GF, _GF, _GF))

def fil(nom):
    return '<nav class="ariane" aria-label="Fil d\'Ariane"><a href="./">Accueil</a> · %s</nav>' % esc(nom)

def ariane_ld(nom, slug):
    return ('<script type="application/ld+json">{"@context":"https://schema.org","@type":"BreadcrumbList",'
            '"itemListElement":[{"@type":"ListItem","position":1,"name":"Accueil","item":"https://louisette-paris.com/"},'
            '{"@type":"ListItem","position":2,"name":%s,"item":"https://louisette-paris.com/%s"}]}</script>' % (txt(nom), slug))

def formulaire():
    """Demande de devis groupe. Sans prestataire configure, le formulaire
    ouvre la messagerie du visiteur avec tout deja rempli : il fonctionne
    des le premier jour, sans compte a creer nulle part."""
    f = S.get("formulaire_groupe", {}) or {}
    action = f.get("action") or ""
    par_mail = not action
    champs = [
        ("nom",       "Votre nom",                "text",  True,  "", "name"),
        ("email",     "Votre e-mail",             "email", True,  "", "email"),
        ("tel",       "Votre téléphone",          "tel",   True,  "", "tel"),
        ("date",      "Date souhaitée",           "date",  True,  "", ""),
        ("personnes", "Nombre de personnes",      "number","True", "min=\"8\" max=\"400\"", ""),
    ]
    h = ['<section class="sect form" id="devis">',
         '<h2>Demander un devis</h2>',
         '<p>Répondez à ces quelques questions : nous revenons vers vous avec une '
         'proposition chiffrée. Pour un besoin urgent, appelez le '
         '<a class="lien" href="tel:%s">%s</a>.</p>' % (esc(S["tel_groupes"]["lien"]), esc(S["tel_groupes"]["affiche"])),
         '<form class="devis" method="%s" action="%s"%s>' % (
             "get" if par_mail else "post",
             ("mailto:" + esc(S["email"])) if par_mail else esc(action),
             ' enctype="text/plain"' if par_mail else '')]
    for nom, lab, typ, requis, extra, auto in champs:
        h.append('<p class="champ"><label for="c-%s">%s%s</label>'
                 '<input id="c-%s" name="%s" type="%s"%s%s%s></p>' % (
                     nom, lab, " *" if requis else "", nom, nom, typ,
                     " required" if requis else "",
                     (" autocomplete=\"%s\"" % auto) if auto else "",
                     (" " + extra) if extra else ""))
    h.append('<p class="champ"><label for="c-occasion">Type d\'occasion</label>'
             '<select id="c-occasion" name="occasion">'
             '<option>Repas d\'entreprise</option><option>Anniversaire</option>'
             '<option>Mariage ou fiançailles</option><option>Cocktail dînatoire</option>'
             '<option>Privatisation complète</option><option>Autre</option></select></p>')
    h.append('<p class="champ"><label for="c-message">Votre message</label>'
             '<textarea id="c-message" name="message" rows="4" '
             'placeholder="Horaire, contraintes, budget…"></textarea></p>')
    # piege a robots : un humain ne remplit jamais ce champ, il est cache
    h.append('<p class="miel" aria-hidden="true"><label for="c-site">Ne pas remplir</label>'
             '<input id="c-site" name="site" type="text" tabindex="-1" autocomplete="off"></p>')
    h.append('<p class="envoi"><button type="submit" class="btn">Envoyer ma demande</button></p>')
    h.append('<p class="tc">Les informations transmises servent uniquement à répondre à '
             'votre demande. Voir la <a class="lien" href="confidentialite.html">politique de '
             'confidentialité</a>.</p>')
    h.append('</form></section>')
    return "\n".join(h)

def newsletter():
    """Inscription a la lettre d'actualites.

    Le consentement doit etre libre, specifique, eclaire et univoque : la case
    n'est jamais pre-cochee, la finalite est ecrite au-dessus, et le retrait
    est annonce avant l'envoi. Sans prestataire configure, l'inscription part
    par la messagerie du visiteur : le message qu'il envoie lui-meme, depuis
    sa propre boite, vaut preuve de consentement — plus solide qu'une case."""
    n = S.get("newsletter", {}) or {}
    action = n.get("action") or ""
    par_mail = not action
    freq = esc(n.get("frequence") or "une fois par mois")
    corps = ("Bonjour,%0D%0A%0D%0AJe souhaite recevoir la lettre d'actualites de "
             "La Maison Louisette a cette adresse.%0D%0A%0D%0AJ'ai lu la politique "
             "de confidentialite et je sais que je peux me desinscrire a tout "
             "moment.%0D%0A%0D%0APrenom :%0D%0A")
    h = ['<section class="sect news" id="newsletter">',
         '<h2>Nos actualités</h2>',
         '<p>Les soirées, les nouveautés de la carte, les dates à retenir. '
         'Environ %s, jamais plus. Vous vous désinscrivez en un clic, '
         'et nous ne transmettons votre adresse à personne.</p>' % freq]
    if par_mail:
        h.append('<p class="envoi"><a class="btn" href="mailto:%s'
                 '?subject=Inscription%%20a%%20la%%20lettre%%20d%%27actualites&body=%s">'
                 'M’inscrire par e-mail</a></p>' % (esc(S["email"]), corps))
        h.append('<p class="tc">Votre message d’inscription nous sert de preuve de votre accord. '
                 'Voir la <a class="lien" href="confidentialite.html">politique de '
                 'confidentialité</a>.</p>')
    else:
        h += ['<form class="inscription" method="post" action="%s">' % esc(action),
              '<p class="champ"><label for="n-email">Votre e-mail</label>'
              '<input id="n-email" name="email" type="email" required autocomplete="email"></p>',
              '<p class="champ"><label for="n-prenom">Votre prénom</label>'
              '<input id="n-prenom" name="prenom" type="text" autocomplete="given-name"></p>',
              '<p class="accord"><input id="n-ok" name="consentement" type="checkbox" required value="oui">'
              '<label for="n-ok">J’accepte de recevoir la lettre d’actualités de '
              'La Maison Louisette et je peux me désinscrire à tout moment.</label></p>',
              '<p class="miel" aria-hidden="true"><label for="n-site">Ne pas remplir</label>'
              '<input id="n-site" name="site" type="text" tabindex="-1" autocomplete="off"></p>',
              '<p class="envoi"><button type="submit" class="btn">M’inscrire</button></p>',
              '<p class="tc">Vos données servent uniquement à vous envoyer cette lettre. '
              'Voir la <a class="lien" href="confidentialite.html">politique de '
              'confidentialité</a>.</p>',
              '</form>']
    h.append('</section>')
    return "\n".join(h)

# ----------------------------------------------------------------- une page
def page(slug):
    m = P[slug]; f = slug + ".html"
    corps = lire("_contenu/%s.html" % slug)
    h = ['<!DOCTYPE html>', '<html lang="fr">', '<head>',
         '<meta charset="utf-8">',
         '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">',
         '<title>%s</title>' % esc(m["titre"]),
         '<meta name="description" content="%s">' % esc(m["description"]),
         '<meta name="robots" content="noindex,nofollow">',
         '<meta name="theme-color" content="#0C0910">',
         '<link rel="icon" href="%s">' % FAVICON,
         '<meta property="og:type" content="article">',
         '<meta property="og:site_name" content="%s">' % esc(S["nom"]),
         '<meta property="og:locale" content="fr_FR">',
         '<meta property="og:title" content="%s">' % esc(m["og_titre"]),
         '<meta property="og:description" content="%s">' % esc(m["description"]),
         '<link rel="canonical" href="https://louisette-paris.com/%s">' % f,
         POLICES,
         '<link rel="stylesheet" href="assets/site.css">',
         ariane_ld(m["ariane"], f),
         '</head>', '<body class="page">',
         '<a href="#contenu" class="skip">Aller au contenu</a>',
         '<div class="grain" aria-hidden="true"></div>',
         barre(f), tiroir(), fil(m["ariane"]),
         '<main id="contenu">', corps.replace("<!-- FORMULAIRE -->", formulaire()).replace("<!-- NEWSLETTER -->", newsletter()), '</main>',
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
            h = motif.sub(lambda _m, n=nom, c=contenu: '<!-- %s:debut -->%s<!-- %s:fin -->' % (n, c, n), h)
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
        slug = f[:-5]
        prix_ok = f == "index.html" or P.get(slug, {}).get("prix_autorises")
        if re.search(r'\d\s?€', t) and not prix_ok:
            pbs.append("%s : un prix apparait alors que les prix ne sont pas reconcilies" % f)
        if "8h30" in t or "8 h 30" in t: pbs.append("%s : horaire 8h30" % f)
        for mot in ("100 % maison", "tout fait maison", "entièrement travaillée sur place"):
            if mot in t: pbs.append('%s : formulation interdite "%s"' % (f, mot))
        if "abus d'alcool" not in t: pbs.append("%s : mention alcool absente" % f)
        for img in (re.findall(r'<img [^>]*>', t) if f != "index.html" else []):
            if not re.search(r'alt="[^"]+"', img):
                pbs.append("%s : une image n'a pas de description alt" % f)
            if not (re.search(r'width="\d+"', img) and re.search(r'height="\d+"', img)):
                pbs.append("%s : une image n'a pas ses dimensions, la page sautera au chargement" % f)
        for note in re.findall(r'<!--(.*?)-->', t, re.S):
            if re.search(r'CONTR[OÔ]LE BLOQUANT|[AÀ] CONFIRMER|TODO|REMPLACER|V[EÉ]RIFIER', note, re.I):
                pbs.append("%s : une note de travail est restee dans le fichier publie" % f)
                break
        if "&amp;amp;" in t: pbs.append("%s : double mise en forme (&amp;amp;), une donnee a ete traitee deux fois" % f)
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
