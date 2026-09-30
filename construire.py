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
P_ = None
SITE = "https://louisette-paris.com/"
OG_IMAGE = "img/og-louisette.jpg"
OG_ALT = "Le neon Louisette au-dessus des banquettes de la salle, brasserie parisienne des Grands Boulevards"

DISTANCES = "_controle/quartier-2026-09-10.json"

def itineraires(corps):
    """Pose sur chaque fiche de salle un bouton d itineraire a pied.

    C est un lien, pas une carte : rien n est charge tant que personne ne
    clique. Une carte integree par salle aurait fait treize connexions a un
    service tiers a l ouverture de la page, avec les traceurs qui vont avec.
    Le point de depart est le restaurant, l arrivee les coordonnees mesurees
    le 10/09/2026 et rangees dans le meme fichier que les distances."""
    try:
        mesures = charger(DISTANCES)
    except SystemExit:
        return corps
    ref = {}
    for section in ("salles", "monuments", "parkings"):
        ref.update(mesures.get(section) or {})
    depart = "%s,%s" % (S["geo"]["lat"], S["geo"]["lon"]) if S.get("geo") else "48.8695081,2.3550087"

    def pose(m):
        nom = m.group(2)
        d = ref.get(nom) or {}
        if "lat" not in d: return m.group(0)
        lien = ("https://www.google.com/maps/dir/?api=1&amp;origin=%s&amp;destination=%s,%s&amp;travelmode=walking"
                % (depart, d["lat"], d["lon"]))
        propre = nom.replace("&amp;", "et")
        # Ce libelle est lu a voix haute par les lecteurs d ecran : "a Le Grand
        # Rex" ou "a Theatre Antoine" ne se disent pas. On choisit la
        # preposition sur le premier mot.
        premier = propre.split(" ", 1)[0]
        if premier in ("Le",):        cible = "au " + propre[3:]
        elif premier in ("La",):      cible = "à la " + propre[3:]
        elif premier in ("Les",):     cible = "aux " + propre[4:]
        elif premier in ("Indigo", "Interparking"):
            cible = "au parking " + propre
        elif premier in ("Théâtre", "Palais-Royal", "Splendid", "Gymnase",
                         "Passage", "Marché", "Musée", "Rex", "Jamel", "Max"):
            cible = "au " + propre
        elif premier in ("Porte", "Place", "Gare"):
            cible = "à la " + propre
        elif premier in ("Folies",):  cible = "aux " + propre
        else:                          cible = "à " + propre
        btn = ('<a class="itin" href="%s" target="_blank" rel="noopener" '
               'aria-label="Itinéraire à pied de Louisette %s, %d minutes">'
               'Itinéraire à pied</a>' % (lien, esc(cible), d["minutes"]))
        return m.group(0) + btn

    return re.sub(r'<div class="carte"><div class="d">([^<]*)</div><b>([^<]*)</b>', pose, corps)

def bouton_whatsapp():
    """Bouton WhatsApp de la page groupes, avec le message deja redige.

    Rien ne s affiche si aucun numero n est declare : la page reste correcte."""
    u = whatsapp()
    return ('<a class="b2" href="%s" target="_blank" rel="noopener">WhatsApp</a>' % esc(u)) if u else ""

def whatsapp(message=None):
    """Lien de conversation WhatsApp, ou chaine vide si aucun numero n est declare.

    Le numero est en clair dans l URL : le publier, c est le rendre lisible par
    n importe quel aspirateur d adresses. Il ne figure ici que parce que Dawoud
    l a decide le 09/09/2026. Retirer la cle "whatsapp" de site.json le fait
    disparaitre des dix pages d un coup."""
    w = S.get("whatsapp") or {}
    n = (w.get("numero") or "").strip()
    if not n: return ""
    t = message if message is not None else w.get("message", "")
    from urllib.parse import quote
    return "https://wa.me/%s%s" % (n, ("?text=" + quote(t)) if t else "")


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
    liens_soc = list(S.get("reseaux", []))
    w = whatsapp()
    if w: liens_soc.append(("WhatsApp", w))
    soc = "".join('<a href="%s" target="_blank" rel="noopener me">%s</a>' % (esc(u), esc(n))
                  for n, u in liens_soc)
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
    # L ordre compte. Un formulaire qui part par la messagerie du visiteur
    # echoue en silence : la RFC 6068 autorise le logiciel de courrier a jeter
    # les champs ranges en en-tetes, et sur Chrome Android sans application de
    # courrier il ne se passe rien du tout. Tant qu aucun prestataire n est
    # configure, les deux canaux qui fonctionnent vraiment passent devant.
    tete = ""
    if par_mail:
        wa = whatsapp("Bonjour Louisette, je souhaite un devis pour un groupe. "
                      "Date : … / Nombre de personnes : … / Occasion : …")
        boutons = ['<a class="b2" href="tel:%s">%s</a>'
                   % (esc(S["tel_groupes"]["lien"]), esc(S["tel_groupes"]["affiche"]))]
        if wa: boutons.insert(0, '<a class="b1" href="%s" target="_blank" rel="noopener">'
                                 'Demander par WhatsApp</a>' % esc(wa))
        tete = ('<section class="sect direct" id="devis-direct">'
                '<h2>Le plus rapide</h2>'
                '<p>Pour un devis de groupe, WhatsApp et le téléphone sont les deux voies '
                'les plus sûres&nbsp;: vous avez une réponse le jour même, souvent dans l\'heure.</p>'
                '<div class="btns">%s</div></section>' % "".join(boutons))
    h = [tete,
         '<section class="sect form" id="devis">',
         '<h2>Ou par formulaire</h2>',
         ('<p>Ce formulaire ouvre votre logiciel de courrier avec le message déjà '
          'rédigé. Si rien ne se passe — c\'est le cas sur beaucoup de téléphones — '
          'écrivez-nous directement à <a class="lien" href="mailto:%s">%s</a>, ou '
          'utilisez WhatsApp ci-dessus.</p>' % (esc(S["email"]), esc(S["email"])))
         if par_mail else
         ('<p>Répondez à ces quelques questions : nous revenons vers vous avec une '
          'proposition chiffrée. Pour un besoin urgent, appelez le '
          '<a class="lien" href="tel:%s">%s</a>.</p>'
          % (esc(S["tel_groupes"]["lien"]), esc(S["tel_groupes"]["affiche"]))),
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
             '<input id="c-site" name="site" type="text" tabindex="-1" autocomplete="off" aria-hidden="true"></p>')
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
         '<h2>Les dates qui valent le déplacement.</h2>',
         '<p>Vingt-sept salles de spectacle sont à un quart d\'heure de la maison, et '
         'le comptoir a ses soirées. Une fois par mois, nous envoyons les dates à '
         'retenir&nbsp;: les DJ, les soirées, ce qui change à la carte. %s</p>'
         % ("Rien d\'autre." if freq == "une fois par mois"
            else "Environ %s, jamais plus." % freq),
         '<p class="tc">Vous vous désinscrivez en un clic. Votre adresse ne part chez '
         'personne, et ne sert qu\'à ça.</p>']
    if par_mail:
        h.append('<p class="envoi"><a class="btn" href="mailto:%s'
                 '?subject=Inscription%%20a%%20la%%20lettre%%20d%%27actualites&body=%s">'
                 'M’inscrire — ouvre votre messagerie</a></p>' % (esc(S["email"]), corps))
        h.append('<p class="tc">Le message est déjà rédigé&nbsp;: il ne reste qu’à l’envoyer, '
                 'et il vaut preuve de votre accord. Si votre téléphone n’ouvre rien, '
                 'écrivez-nous à <a class="lien" href="mailto:%s">%s</a>. '
                 'Voir la <a class="lien" href="confidentialite.html">politique de '
                 'confidentialité</a>.</p>' % (esc(S["email"]), esc(S["email"])))
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
              '<input id="n-site" name="site" type="text" tabindex="-1" autocomplete="off" aria-hidden="true"></p>',
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
         '<meta property="og:url" content="%s%s">' % (SITE, f),
         '<meta property="og:image" content="%s%s">' % (SITE, OG_IMAGE),
         '<meta property="og:image:width" content="1200">',
         '<meta property="og:image:height" content="630">',
         '<meta property="og:image:alt" content="%s">' % esc(OG_ALT),
         '<meta name="twitter:card" content="summary_large_image">',
         '<meta name="twitter:title" content="%s">' % esc(m["og_titre"]),
         '<meta name="twitter:description" content="%s">' % esc(m["description"]),
         '<meta name="twitter:image" content="%s%s">' % (SITE, OG_IMAGE),
         '<link rel="canonical" href="%s%s">' % (SITE, f),
         POLICES,
         '<link rel="stylesheet" href="assets/site.css">',
         ariane_ld(m["ariane"], f),
         '</head>', '<body class="page">',
         '<a href="#contenu" class="skip">Aller au contenu</a>',
         '<div class="grain" aria-hidden="true"></div>',
         barre(f), tiroir(), fil(m["ariane"]),
         '<main id="contenu">', (itineraires(corps) if slug in ("theatres", "infos-pratiques", "quartier") else corps).replace("<!-- FORMULAIRE -->", formulaire()).replace("<!-- NEWSLETTER -->", newsletter()).replace("<!-- WHATSAPP -->", bouton_whatsapp()), '</main>',
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
    vues = _meta()
    if meta_js(vues): print("meta.js : regenere depuis _donnees/photos.json")
    pistes, nb_vues = galerie()
    # La lettre d actualites etait absente de la page la plus vue du site :
    # l accueil ne connaissait pas le marqueur. Il le connait maintenant, et
    # c est le meme bloc que sur les autres pages — une seule source.
    for nom, contenu in (("NAV", barre() + "\n" + tiroir()), ("PIED", pied()), ("DOCK", dock()),
                         ("GALERIE", pistes), ("NEWSLETTER", newsletter())):
        motif = re.compile(r'<!-- %s:debut -->.*?<!-- %s:fin -->' % (nom, nom), re.S)
        if motif.search(h):
            h = motif.sub(lambda _m, n=nom, c=contenu: '<!-- %s:debut -->%s<!-- %s:fin -->' % (n, c, n), h)
        else:
            print("   ATTENTION : marqueurs %s absents d'index.html, bloc non mis a jour" % nom)
    if h != avant:
        ecrire("index.html", h); return "mis a jour"
    return "deja a jour"

# ----------------------------------------------------------------- galerie
TUILES_EN_TETE = 24     # tuiles ecrites dans index.html, par piste
PISTES         = 5
SECONDES_TUILE = 4.32   # vitesse de defilement, inchangee depuis l origine

def _meta():
    """Rend la liste des vues, dans l ordre.

    La source est _donnees/photos.json : c est un des dossiers que le robot
    surveille, donc modifier une legende declenche la reconstruction. meta.js,
    lu par le navigateur, en est fabrique — il n est plus a editer a la main."""
    return charger("_donnees/photos.json")

def meta_js(vues):
    """Reecrit meta.js a partir de la source, seulement s il a change."""
    t = "window.GMETA=" + json.dumps(vues, ensure_ascii=False) + ";\n"
    try:
        if lire("meta.js") == t: return False
    except IOError:
        pass
    ecrire("meta.js", t); return True

def _tuile(m):
    n = "%03d" % m["i"]
    return ('<figure class="gtile" data-gi="%d" data-ii="%d" role="button" tabindex="0" aria-label="Agrandir : %s">'
            '<img data-src="t/%s.webp" alt="%s" decoding="async" width="480" height="320"></figure>'
            % (m["i"], m["i"], esc(m.get("cap", "")), n, esc(m.get("alt", ""))))

_SCRIPT_GALERIE = (
 # La suite de la phototheque n est ni dans le document ni chargee au demarrage :
 # elle arrive quand la bande approche de l ecran. Un visiteur qui ne descend
 # jamais jusqu a la galerie ne telecharge rien et ne calcule rien.
 # La charger des le chargement de la page repoussait le LCP a 6,3 s sur
 # 4 mesures sur 5 (essai du 9 septembre) : l insertion et la peinture des
 # 1 188 tuiles retombaient dans la fenetre de mesure.
 '<button type="button" class="gpause" id="gpause" aria-pressed="false">Arrêter le défilement</button>'
 '<script>(function(){'
 'var b=document.querySelector(".gband");if(!b)return;'
 'var bt=document.getElementById("gpause");'
 'if(bt){bt.addEventListener("click",function(){var s=b.classList.toggle("stop");'
 'bt.setAttribute("aria-pressed",s?"true":"false");'
 'bt.textContent=s?"Reprendre le défilement":"Arrêter le défilement";});}'
 'var vis=1,file=[],k=0,tourne=0,pose=0;'
 'function empiler(){file=file.concat([].slice.call(b.querySelectorAll("img[data-src]")));if(!tourne){tourne=1;vague();}}'
 'function vague(){var g=document.getElementById("glb");'
 'if(g&&g.classList.contains("open")){setTimeout(vague,400);return;}'
 'if(!vis){setTimeout(vague,600);return;}'
 'var n=0;while(k<file.length&&n<8){var e=file[k++];var d=e.getAttribute("data-src");if(d){e.src=d;e.removeAttribute("data-src");}n++;}'
 'if(k<file.length){setTimeout(vague,150);}else{tourne=0;}}'
 'function doubler(){var t=b.querySelectorAll(".gtrack");for(var i=0;i<t.length;i++){t[i].insertAdjacentHTML("beforeend",t[i].innerHTML);}}'
 'function suite(){if(pose)return;pose=1;function fini(){doubler();empiler();}'
 'try{fetch("photos-suite.json").then(function(r){return r.json();}).then(function(s){'
 'var t=b.querySelectorAll(".gtrack");for(var i=0;i<s.length&&i<t.length;i++){if(s[i]){t[i].insertAdjacentHTML("beforeend",s[i]);}}'
 'fini();}).catch(fini);}catch(x){fini();}}'
 'if("IntersectionObserver" in window){'
 'new IntersectionObserver(function(es){vis=es[0].isIntersecting?1:0;},{rootMargin:"300px"}).observe(b);'
 'var o=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){o.disconnect();suite();}});},{rootMargin:"600px"});o.observe(b);'
 '}else{addEventListener("load",suite);}'
 '})();</script>')

def galerie():
    """Fabrique les pistes de la phototheque a partir de meta.js.

    Seules les premieres tuiles de chaque piste (TUILES_EN_TETE) partent
    dans index.html ;
    la suite va dans photos-suite.json, chargee quand la bande approche de
    l ecran — jamais si le visiteur ne descend pas jusque-la.
    C est le poids du document qui retarde l affichage, pas le nombre
    d elements : mesure du 9 septembre, note 145."""
    vues = _meta()
    pistes = [[] for _ in range(PISTES)]
    for rang, m in enumerate(vues):
        pistes[rang % PISTES].append(m)
    tete, suite = [], []
    for i, piste in enumerate(pistes):
        dur = int(round(len(piste) * SECONDES_TUILE))
        cls = "gmq grev" if i % 2 else "gmq"
        tete.append('<div class="%s" style="--gdur:%ds"><div class="gtrack">%s</div></div>'
                    % (cls, dur, "".join(_tuile(m) for m in piste[:TUILES_EN_TETE])))
        suite.append("".join(_tuile(m) for m in piste[TUILES_EN_TETE:]))
    ecrire("photos-suite.json", json.dumps(suite, ensure_ascii=False))
    return "\n".join(tete) + "\n" + _SCRIPT_GALERIE, len(vues)

# ----------------------------------------------------------------- sitemap
def sitemap(faites):
    # faites contient deja les pages legales : les rajouter les dupliquait
    # dans le sitemap (12 entrees pour 10 pages, constate le 9 septembre).
    caches = set("%s.html" % k for k, v in P.items() if v.get("brouillon") or v.get("hors_navigation"))
    urls = [""] + [u for u in faites if u != "index.html" and u not in caches]
    from datetime import date
    d = date.today().isoformat()
    ecrire("sitemap.xml",
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join('<url><loc>https://louisette-paris.com/%s</loc><lastmod>%s</lastmod></url>\n' % (u, d) for u in urls)
        + '</urlset>\n')

# ----------------------------------------------------------------- controles
def controler(faites):
    pbs = []
    # Une variable CSS jamais declaree rend la declaration entiere invalide,
    # en silence : ni erreur, ni avertissement, la regle disparait simplement.
    # Le 10/09 quatre regles etaient mortes ainsi — dont le contour de focus du
    # bouton d arret du carrousel, pose le matin meme — parce qu elles
    # appelaient --rose quand le theme declare --or.
    # Exception : --gdur est pose en style en ligne sur chaque piste.
    try:
        css = lire("assets/site.css")
        declarees = set(re.findall(r"(--[a-z0-9-]+)\s*:", css))
        for v in sorted(set(re.findall(r"var\((--[a-z0-9-]+)\)", css)) - declarees - {"--gdur"}):
            pbs.append("assets/site.css : la variable %s est utilisee mais jamais declaree — "
                       "les regles qui l appellent sont mortes" % v)
    except IOError:
        pbs.append("assets/site.css introuvable")
    # Une page sortie du brouillon ne doit plus porter son marqueur de contenu
    # a venir : c est le seul garde-fou qui empeche de publier une coquille.
    for slug, m in P.items():
        f = slug + ".html"
        if f not in faites: continue
        marque = "CARTE-A-VENIR" in lire("_contenu/%s.html" % slug)
        if m.get("brouillon") and not marque:
            pbs.append("%s : la page est en brouillon mais le marqueur CARTE-A-VENIR a disparu ; "
                       "si le contenu est arrete, passer brouillon a false dans pages.json" % f)
        if not m.get("brouillon") and marque:
            pbs.append("%s : la page est publiee alors qu elle porte encore le marqueur "
                       "CARTE-A-VENIR — le contenu n est pas arrete" % f)
    # --- phototheque : la visionneuse resout data-gi par le NUMERO de la photo.
    # Un numero absent de meta.js ouvrirait une autre vue ; un fichier absent
    # afficherait un trou. Les deux bloquent la publication.
    try:
        vues = _meta()
        nums = set(m["i"] for m in vues)
        pages = lire("index.html") + " ".join(json.loads(lire("photos-suite.json")))
        gis = set(int(x) for x in re.findall(r'data-gi="(\d+)"', pages))
        for n in sorted(gis - nums):
            pbs.append("phototheque : la vignette %d n'existe pas dans meta.js" % n)
        for n in sorted(nums - gis):
            pbs.append("phototheque : la vue %d de meta.js n'est affichee nulle part" % n)
        for n in sorted(nums):
            for d in ("t", "p"):
                if not os.path.exists(os.path.join(RACINE, d, "%03d.webp" % n)):
                    pbs.append("phototheque : le fichier %s/%03d.webp manque" % (d, n))
        if len(gis) != len(vues):
            pbs.append("phototheque : %d tuiles pour %d vues" % (len(gis), len(vues)))
    except Exception as e:
        pbs.append("phototheque : controle impossible (%s)" % e)
    # --- une feuille de style ecrite avec des \\n litteraux au lieu de vrais
    # retours a la ligne met toute la regle sur une ligne, prefixee d un
    # caractere invalide : le navigateur jette le bloc entier, en silence.
    # C est arrive le 10/09 au bloc du canal direct, dont les boutons sont
    # restes des liens nus jusqu a la relecture visuelle.
    try:
        _css = lire("assets/site.css")
        if "\\n" in _css:
            pbs.append("assets/site.css : un \\n litteral casse la regle qui le suit")
        _ouv, _fer = _css.count("{"), _css.count("}")
        if _ouv != _fer:
            pbs.append("assets/site.css : %d accolades ouvertes pour %d fermees" % (_ouv, _fer))
    except Exception as e:
        pbs.append("assets/site.css : illisible (%s)" % e)

    # --- tout hote tiers appele au chargement d une page transmet l adresse IP
    # du visiteur a ce tiers. Le 11/09, la mesure du site en ligne en a trouve
    # un seul : fonts.googleapis.com. C est peu, mais c est un traitement de
    # donnee personnelle que le site ne declare pas, et la legende de la carte
    # affirme le contraire. La liste est explicite : tout ajout doit etre decide.
    # Trois hotes seulement, et chacun pour une raison ecrite :
    #  - fonts.googleapis.com et fonts.gstatic.com : les deux polices du site.
    #    Elles sont sous licence libre et pourraient etre hebergees ici meme ;
    #    tant qu elles ne le sont pas, le navigateur du visiteur les demande a
    #    Google, qui voit son adresse IP. C est le seul vrai point RGPD du site.
    #  - bookings.zenchef.com : une resolution DNS anticipee, pas une connexion.
    #    Elle fait gagner le temps de resolution au moment du clic sur Reserver.
    #    Aucune donnee du visiteur n atteint Zenchef tant qu il ne clique pas.
    # Toute autre adresse arrete la construction : un tiers ne s ajoute pas par
    # inadvertance.
    TIERS_ADMIS = {"fonts.googleapis.com", "fonts.gstatic.com", "bookings.zenchef.com"}
    # Seul ce qui se telecharge au chargement compte : un <a href> demande un
    # clic, un <link rel="canonical"> ne charge rien. Premiere version de ce
    # controle : elle signalait notre propre domaine canonique et le lien de
    # reservation. On ne regarde donc que les balises qui vont chercher un
    # fichier, et l attribut qui le designe.
    CHARGE = (("script", "src"), ("img", "src"), ("iframe", "src"),
              ("video", "src"), ("audio", "src"), ("source", "src"),
              ("embed", "src"), ("object", "data"))
    for f in faites + ["index.html"]:
        t0 = lire(f)
        vus = []
        for balise, attr in CHARGE:
            for m in re.finditer(r'<%s\b[^>]*?\b%s="https?://([^/"]+)' % (balise, attr), t0, re.I):
                vus.append((balise, m.group(1).lower()))
        # <link> ne charge que pour certains rel
        for m in re.finditer(r'<link\b([^>]*)>', t0, re.I):
            att = m.group(1)
            rel = (re.search(r'rel="([^"]*)"', att) or [None, ""])[1].lower()
            if not any(r in rel for r in ("stylesheet", "preload", "icon", "prefetch", "preconnect")):
                continue
            h2 = re.search(r'href="https?://([^/"]+)', att)
            if h2: vus.append(("link " + rel, h2.group(1).lower()))
        for balise, hote in vus:
            if hote not in TIERS_ADMIS:
                pbs.append("%s : chargement depuis un hote tiers non declare — %s (%s)"
                           % (f, hote, balise))

    presentes = set(os.listdir(RACINE))
    for f in faites + ["index.html"]:
        t = lire(f)
        # Les liens sortants n etaient pas controles : la page carte est partie
        # le 09/09 avec un & non echappe et sans rel=noopener, sans que rien
        # ne s en apercoive. On les regarde desormais un par un.
        for m in re.finditer(r'<a [^>]*href="(https?://[^"]+)"[^>]*>', t):
            balise, url = m.group(0), m.group(1)
            if "&" in url and "&amp;" not in url:
                pbs.append("%s : lien sortant avec un & non echappe — %s" % (f, url[:70]))
            if 'target="_blank"' not in balise:
                pbs.append("%s : lien sortant sans target=\"_blank\" — %s" % (f, url[:70]))
            elif "noopener" not in balise:
                pbs.append("%s : lien sortant en nouvel onglet sans rel=\"noopener\" — %s" % (f, url[:70]))
        for l in set(re.findall(r'href="([a-z0-9-]+\.html)(?:#[^"]*)?"', t)):
            if l not in presentes: pbs.append("%s : lien mort vers %s" % (f, l))
        slug = f[:-5]
        prix_ok = f == "index.html" or P.get(slug, {}).get("prix_autorises")
        # Un tarif de parking n est pas un prix de la carte : c est le prix d un
        # tiers, releve et range dans le fichier de mesures. On l autorise, mais
        # seulement lui : tout montant qui ne figure pas dans ce fichier arrete
        # la construction, sinon la page devient une porte d entree pour un prix
        # de plat non reconcilie.
        if not prix_ok:
            try:
                tarifs = set()
                for v in (json.loads(lire(DISTANCES)).get("parkings") or {}).values():
                    for cle in ("tarif_1h", "tarif_24h"):
                        if v.get(cle): tarifs.add(v[cle].replace("\u00a0", " ").strip())
            except Exception as e:
                tarifs = set(); pbs.append("%s : tarifs de reference illisibles (%s)" % (f, e))
            for m in re.finditer(r'\d[\d ,\.]*\s?€', t):
                montant = re.sub(r"\s+", " ", m.group(0)).strip()
                if montant not in tarifs:
                    pbs.append("%s : le montant %s apparait alors que les prix ne sont pas reconcilies"
                               % (f, montant))
        if "8h30" in t or "8 h 30" in t: pbs.append("%s : horaire 8h30" % f)
        # Un retour a la ligne au milieu d une phrase suffisait a faire passer
        # ces controles a cote : le 09/09, une septieme mention du Grand Rex
        # "a trois minutes" a survecu a six corrections pour cette seule raison.
        # On les fait donc travailler sur un texte a espaces normalises.
        plat = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t))

        # Les durees affichees sur les fiches sont mesurees, pas estimees :
        # _controle/quartier-2026-09-10.json, calculateur pieton Valhalla.
        # Le bareme precedent n avait jamais ete mesure et se trompait dans les
        # deux sens, jusqu a un facteur quatre. Toute fiche qui s ecarte de la
        # mesure arrete la construction.
        if f in ("theatres.html", "infos-pratiques.html", "quartier.html"):
            attendu = {"theatres.html": ("salles",),
                       "infos-pratiques.html": ("parkings",),
                       "quartier.html": ("monuments",)}[f]
            try:
                mes = json.loads(lire(DISTANCES))
                ref = {}
                for section in attendu: ref.update(mes[section])
            except Exception as e:
                pbs.append("%s : mesures de distances illisibles (%s)" % (f, e)); ref = {}
            vues = set()
            for mm in re.finditer(r'<div class="carte"><div class="d">([^<]*)</div><b>([^<]*)</b>', t):
                dit, nom = mm.group(1), mm.group(2); vues.add(nom)
                if nom not in ref:
                    pbs.append("%s : la fiche %s n a pas de distance mesuree" % (f, nom)); continue
                a = re.search(r"(\d[\d\s]*)\s*m", dit); b = re.search(r"(\d+)\s*min", dit)
                em = int(re.sub(r"\s", "", a.group(1))) if a else None
                emn = int(b.group(1)) if b else None
                if em != ref[nom]["metres"] or emn != ref[nom]["minutes"]:
                    pbs.append('%s : %s affiche "%s" au lieu de %d m et %d min mesures'
                               % (f, nom, dit, ref[nom]["metres"], ref[nom]["minutes"]))
            for nom in ref:
                if nom not in vues:
                    pbs.append("%s : le point mesure %s n est affiche nulle part" % (f, nom))
            n_fiches = t.count('<div class="carte">')
            n_itin = t.count('class="itin"')
            if n_itin != n_fiches:
                pbs.append("%s : %d fiches mais %d boutons d itineraire"
                           % (f, n_fiches, n_itin))

        # --- les deux comptages annonces en gros sur la page theatres sont
        # deduits des mesures, pas ecrits a la main. Le 10/09 la page annoncait
        # encore "5 salles a moins de trois minutes" alors qu il y en a sept :
        # une sous-estimation, mais fausse quand meme.
        if f == "theatres.html":
            try:
                sal = json.loads(lire(DISTANCES))["salles"]
                courtes = sum(1 for v in sal.values() if v["minutes"] <= 3)
                quart = sum(1 for v in sal.values() if v["minutes"] <= 15)
            except Exception as e:
                pbs.append("theatres.html : comptages impossibles (%s)" % e); courtes = quart = None
            if courtes is not None:
                m = re.search(r"<b>(\d+) salles</b>", t)
                if not m or int(m.group(1)) != courtes:
                    pbs.append("theatres.html : le bandeau annonce %s salles a trois minutes, il y en a %d"
                               % (m.group(1) if m else "?", courtes))
                m = re.search(r"<b>(\d+) lieux</b>", t)
                if not m or int(m.group(1)) != quart:
                    pbs.append("theatres.html : le bandeau annonce %s lieux a un quart d heure, il y en a %d"
                               % (m.group(1) if m else "?", quart))

        # --- deux lieux ont ete ecartes faute de preuve d activite ou parce qu ils
        # ne sont pas ou l on croyait. Ils ne doivent jamais revenir par un
        # copier-coller : le controle les cherche dans toutes les pages.
        for interdit, pourquoi in (
                ("Le Globo", "aucune source ne confirme une activite en 2026 : domaine mort, aucune programmation"),
                ("Golden Comedy", "n est pas boulevard de Bonne-Nouvelle mais 36 rue Dalayrac, a 1 668 m"),
                ("Parking des Récollets", "reserve aux abonnes, inutilisable pour un client")):
            if interdit in plat:
                pbs.append("%s : %s est cite alors qu il a ete ecarte — %s" % (f, interdit, pourquoi))

        # --- la salle est de plain-pied, mais la station de metro ne l est pas.
        # Publier l un sans l autre envoie un client en fauteuil dans un couloir
        # sans ascenseur. Les deux phrases partent ensemble ou pas du tout.
        if f == "infos-pratiques.html":
            if "mobilité réduite" in plat:
                # Le premier jet ne cherchait qu une phrase : la seconde pouvait
                # disparaitre sans rien declencher. On exige les trois elements
                # de l avertissement — le fait, la solution, et la station de
                # repli — sinon la page ment par omission a un client en fauteuil.
                nie = len(re.findall(r"ne l['\u2019]est pas", plat))
                if nie < 2:
                    pbs.append("infos-pratiques.html : la page annonce l accessibilite de la salle "
                               "sans dire deux fois, tableau et texte, que la station "
                               "Strasbourg-Saint-Denis n est pas accessible")
                if "20, 32, 38 et 39" not in plat:
                    pbs.append("infos-pratiques.html : l avertissement d accessibilite ne propose "
                               "plus les bus accessibles en solution de remplacement")
                if "ligne 14" not in plat:
                    pbs.append("infos-pratiques.html : la station accessible la plus proche "
                               "(Chatelet, ligne 14) n est plus citee")
            if "du lundi au samedi de 9 h à 20 h" not in plat:
                pbs.append("infos-pratiques.html : la regle du stationnement de surface a disparu")
            if "y compris au mois d" not in plat:
                pbs.append("infos-pratiques.html : le stationnement d aout est presente a tort "
                           "comme gratuit, ou la precision a disparu")

        # --- le statut patrimonial est juridique, pas decoratif. Classe et
        # inscrit ne sont pas synonymes : le 09/09 le site annonçait le decor du
        # Grand Rex "classe" alors qu il est inscrit depuis 1981. Chaque fiche de
        # la page quartier porte le statut releve dans la base Merimee, et il doit
        # etre recopie mot pour mot depuis le fichier de mesures.
        if f == "quartier.html":
            try:
                mons = json.loads(lire(DISTANCES))["monuments"]
            except Exception as e:
                pbs.append("quartier.html : statuts patrimoniaux illisibles (%s)" % e); mons = {}
            def _pli(s):
                s = re.sub(r"\s+", " ", s).strip().lower()
                for a, b in (("é","e"),("è","e"),("ê","e"),("à","a"),("ç","c"),("ô","o"),("û","u"),("î","i"),("'","'")):
                    s = s.replace(a, b)
                return s
            fiches = re.findall(r'<div class="carte"><div class="d">[^<]*</div><b>([^<]*)</b>'
                                r'.*?(?:<p class="stat">(.*?)</p>)?</div>', t, re.S)
            n_stat = t.count('<p class="stat">')
            n_cartes = t.count('<div class="carte">')
            if n_stat != n_cartes:
                pbs.append("quartier.html : %d fiches mais %d statuts patrimoniaux"
                           % (n_cartes, n_stat))
            for nom, stat in fiches:
                ref = (mons.get(nom) or {}).get("statut")
                if ref is None:
                    pbs.append("quartier.html : %s n a pas de statut releve" % nom); continue
                if _pli(re.sub(r"<[^>]+>", "", stat or "")) != _pli(ref):
                    pbs.append('quartier.html : %s affiche "%s" alors que la base Merimee dit "%s"'
                               % (nom, re.sub(r"<[^>]+>", "", stat or "")[:60], ref[:60]))
            # "classe" ecrit ailleurs que dans un statut releve : on refuse.
            for m in re.finditer(r"(?i)class[ée]e?s?\s+(?:monument|au titre des monuments)", plat):
                bout = plat[max(0, m.start()-90):m.start()+90]
                if not any(_pli(v["statut"])[:24] in _pli(bout) for v in mons.values()):
                    pbs.append('quartier.html : un "classe monument historique" sans notice Merimee — "%s"'
                               % bout[-90:])

        # --- un avis moyen que l on s attribue soi-meme dans le balisage est
        # interdit par Google (self-serving review) et invérifiable par le
        # lecteur. Il etait present depuis le debut : 4,6 sur 8 517 avis, sans
        # source ni date. Il ne doit jamais revenir.
        if "aggregateRating" in t or '"@type": "Review"' in t or '"@type":"Review"' in t:
            pbs.append("%s : une note moyenne auto-attribuee est dans le balisage — "
                       "interdit par Google et non sourcé sur la page" % f)
        # --- Google a supprime les resultats enrichis FAQ le 7 mai 2026 et HowTo
        # avant lui, et retire la documentation. Ce balisage ne sert plus a rien
        # et donne l illusion d un acquis.
        for mort in ("FAQPage", "HowTo"):
            if '"%s"' % mort in t:
                pbs.append("%s : balisage %s, supprime des resultats Google depuis mai 2026" % (f, mort))

        # --- un nombre de salles ecrit en toutes lettres dans une phrase echappait
        # a tous les controles : le 10/09 la page 404 renvoyait encore vers "les
        # treize salles" pendant que la page en affichait vingt-sept. On verifie
        # desormais chaque occurrence contre les deux seuls comptages qui existent.
        try:
            _s = json.loads(lire(DISTANCES))["salles"]
            _ok = {len(_s), sum(1 for v in _s.values() if v["minutes"] <= 3)}
            _mots = {"une":1,"deux":2,"trois":3,"quatre":4,"cinq":5,"six":6,"sept":7,"huit":8,
                     "neuf":9,"dix":10,"onze":11,"douze":12,"treize":13,"quatorze":14,"quinze":15,
                     "seize":16,"vingt":20,"vingt-sept":27,"trente":30}
            # « Deux salles et un gradin » decrit une salle voisine, pas notre
            # quartier : on ne verifie que les tournures qui parlent de l ensemble.
            _motif = (r"(?i)(?:\bles\s+([a-zà-ÿ-]+|\d+)\s+salles\b"
                      r"|\b([a-zà-ÿ-]+|\d+)\s+salles\s+de\s+spectacle\b)")
            for mm in re.finditer(_motif, plat):
                brut0 = mm.group(1) or mm.group(2)
                brut = brut0.lower()
                n = _mots.get(brut, int(brut) if brut.isdigit() else None)
                if n is not None and n not in _ok:
                    pbs.append('%s : "%s salles" alors que les mesures en comptent %s'
                               % (f, brut, " ou ".join(str(x) for x in sorted(_ok))))
        except Exception as e:
            pbs.append("%s : comptage des salles invérifiable (%s)" % (f, e))

        # --- une image declaree mais absente ne se voit pas a la relecture :
        # le 09/09 og:image pointait vers un fichier qui n existait pas et
        # chaque partage affichait une carte cassee. On verifie l existence.
        for src in set(re.findall(r'src="((?:img|assets)/[^"]+)"', t)):
            if not os.path.exists(os.path.join(RACINE, src)):
                pbs.append("%s : l image %s est declaree mais absente" % (f, src))

        # --- la legende du plan porte des distances qui ne sont dans aucune
        # fiche : elles echappaient au controle des cartes. On les compare aux
        # memes mesures.
        if 'class="plan-leg"' in t:
            try:
                _m = json.loads(lire(DISTANCES))
                _ref = {}
                for _sec in ("salles", "monuments", "parkings"): _ref.update(_m[_sec])
            except Exception as e:
                _ref = {}; pbs.append("%s : legende du plan invérifiable (%s)" % (f, e))
            _vus = 0
            for mm in re.finditer(r"<li[^>]*><b>[^<]+</b><span>([^<]+?)\s+—\s+(\d[\d\s]*)\s*m</span>", t):
                nom = mm.group(1).strip(); em = int(re.sub(r"\s", "", mm.group(2))); _vus += 1
                if nom in _ref:
                    if _ref[nom]["metres"] != em:
                        pbs.append("%s : la legende du plan donne %s a %d m, mesure a %d m"
                                   % (f, nom, em, _ref[nom]["metres"]))
                elif nom != "Métro Strasbourg-Saint-Denis":
                    pbs.append("%s : la legende du plan cite %s, qui n est pas mesure" % (f, nom))
            if _ref and _vus != t.count("<li class="):
                pbs.append("%s : %d entrees de legende lues sur %d"
                           % (f, _vus, t.count("<li class=")))

        # --- la lettre d actualites n etait sur qu une page sur neuf : huit pages
        # sur neuf ne proposaient aucun moyen de rester en contact. C est le
        # deuxieme objectif du site apres la reservation ; il doit etre partout.
        LEGALES = ("mentions-legales.html", "confidentialite.html")
        if f not in ("404.html",) + LEGALES and not P.get(f[:-5], {}).get("brouillon") \
           and not P.get(f[:-5], {}).get("hors_navigation"):
            if 'id="newsletter"' not in t:
                pbs.append("%s : la lettre d actualites est absente de cette page" % f)

        # --- sur la page groupes, le canal qui fonctionne doit passer avant celui
        # qui peut echouer en silence.
        # Ce controle a plante la premiere fois qu on l a casse, au lieu de
        # signaler : il cherchait une position avec index(), qui leve. On lit
        # les deux positions avec find(), et l absence est un echec comme un autre.
        if f == "groupes.html":
            # id="devis-direct" ne contient pas id="devis" — le guillemet les
            # separe — donc les deux positions se cherchent independamment.
            direct = t.find('id="devis-direct"')
            form = t.find('id="devis"')
            if direct < 0:
                pbs.append("groupes.html : le bloc WhatsApp et telephone a disparu")
            elif form < 0:
                pbs.append("groupes.html : le formulaire de devis a disparu")
            elif direct > form:
                pbs.append("groupes.html : le formulaire passe avant WhatsApp et le telephone")

        # Le Grand Rex est a 590 m, soit sept minutes. Toute autre duree
        # accolee a son nom est une affirmation qu un client dement avec son
        # telephone, debout sur le trottoir.
        for m in re.finditer(r"Grand Rex[^.]{0,80}", plat):
            bout = m.group(0)
            d = re.search(r"\b(une|deux|trois|quatre|cinq|six|huit|neuf|dix|\d+)\s*(minutes?|min)\b", bout)
            if d and "sept" not in bout:
                pbs.append('%s : le Grand Rex annonce a "%s" — il est a 590 m, soit sept minutes'
                           % (f, d.group(0)))

        # La mention "fait maison" est reglementee (decret 2014-797, art. D.121-13-1
        # du code de la consommation) : elle vise un plat elabore sur place a partir
        # de produits crus. Le site achete viennoiseries, glaces et charcuteries.
        # Toute formulation qui l etend a l ensemble de la carte est fausse.
        # Le 9 septembre le garde-fou a rate "Tout est fait maison" parce qu il ne
        # cherchait que "tout fait maison" : on cherche desormais la famille entiere.
        for motif, quoi in (
                (r"(?i)\b(tout|100\s*%|entièrement|intégralement)\b[^.]{0,40}\bfait[e]?s?\s+maison\b", "un « fait maison » etendu a toute la carte"),
                (r"(?i)\bfait\s+maison\b[^.]{0,30}\b(partout|sans exception)\b", "un « fait maison » sans exception"),
                (r"(?i)entièrement travaillée sur place", "« entièrement travaillée sur place »")):
            m = re.search(motif, plat)
            if m: pbs.append('%s : formulation interdite — %s : "%s"' % (f, quoi, m.group(0)[:70]))
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
    # --- les titres et descriptions vivent dans _donnees/pages.json, hors des
    # pages : le 10/09 la page theatres affichait vingt-sept salles pendant que
    # sa propre description en annonçait treize. Rien ne l avait vu.
    MOTS = {1:"une",2:"deux",3:"trois",4:"quatre",5:"cinq",6:"six",7:"sept",8:"huit",9:"neuf",
            10:"dix",11:"onze",12:"douze",13:"treize",14:"quatorze",15:"quinze",16:"seize",
            17:"dix-sept",18:"dix-huit",19:"dix-neuf",20:"vingt",21:"vingt et une",22:"vingt-deux",
            23:"vingt-trois",24:"vingt-quatre",25:"vingt-cinq",26:"vingt-six",27:"vingt-sept",
            28:"vingt-huit",29:"vingt-neuf",30:"trente",80:"quatre-vingts",11.5:"onze"}
    try:
        _m = json.loads(lire(DISTANCES))
        _sal = _m["salles"]; _mon = _m["monuments"]
        _att = {
          "theatres": [(len(_sal), "le nombre de salles"),
                       (sum(1 for v in _sal.values() if v["minutes"] <= 3), "les salles a trois minutes"),
                       (min(v["metres"] for v in _sal.values()), "la distance de la salle la plus proche")],
          "quartier": [(sum(1 for v in _mon.values()
                            if v["minutes"] <= 10 and not v["statut"].lower().startswith("non prot")),
                        "les monuments proteges a dix minutes")],
        }
        for _slug, _regles in _att.items():
            _txt = (P.get(_slug, {}).get("titre", "") + " " + P.get(_slug, {}).get("description", "")).lower()
            for _n, _quoi in _regles:
                _mot = MOTS.get(_n)
                if _mot is None:
                    pbs.append("pages.json : %s vaut %d, aucun mot pour le verifier" % (_quoi, _n)); continue
                if _mot not in _txt and str(_n) not in _txt:
                    pbs.append('pages.json : la description de %s ne dit pas %s (%d, "%s")'
                               % (_slug, _quoi, _n, _mot))
    except Exception as e:
        pbs.append("pages.json : coherence avec les mesures impossible (%s)" % e)
    # --- la carte : le pont avec le moteur de cartes imprimees.
    # carte.html n est pas ecrite a la main. _outils/carte-depuis-livraison.py
    # extrait les plats de la sortie du moteur (LIVRAISON_vNNN/site/*.html) et
    # depose son compte dans _controle/carte-source.json. Une page qui perd des
    # lignes en silence ne se voit pas a l oeil : ces controles la comptent.
    if "carte.html" in faites:
        t = lire("carte.html")
        plat = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t))
        try:
            src = json.loads(lire("_controle/carte-source-fr.json"))
        except (IOError, ValueError) as e:
            src = None
            pbs.append("carte.html : manifeste _controle/carte-source-fr.json illisible (%s) ; "
                       "relancer _outils/carte-depuis-livraison.py" % e)
        if src:
            n = t.count('<span class="mn">')
            if n != src["articles"]:
                pbs.append("carte.html : %d plats publies pour %d extraits de %s — "
                           "la page a perdu des lignes"
                           % (n, src["articles"], src["chemin_source"]))
            r = t.count('<h3 class="mrub">')
            if r != src["rubriques"]:
                pbs.append("carte.html : %d rubriques publiees pour %d extraites"
                           % (r, src["rubriques"]))
            vus = set(m.group(1).strip()
                      for m in re.finditer(r'<span class="mp">([^<]+)</span>', t))
            trop = vus - set(src["prix"])
            if trop:
                pbs.append("carte.html : prix publies absents du manifeste des prix "
                           "extraits : %s" % ", ".join(sorted(trop)))
            # Aucune donnee allergene ni allegation de regime ne se publie tant
            # que la cuisine ne les a pas revalidees : neuf questions de recette
            # restent ouvertes (sauce Cesar aux anchois, allegation sans gluten
            # de douze plats, code P de la planche de tapas). Les mots ci-dessous
            # n existent que dans une legende de codes ; le texte courant ecrit
            # gluten et sulfites en minuscules, il ne les declenche pas.
            if not src.get("allergenes"):
                for motif, dans_html, quoi in (
                        ("Crustaces", False, "legende des codes allergenes"),
                        ("Crustac\u00e9s", False, "legende des codes allergenes"),
                        ("Mollusques", False, "legende des codes allergenes"),
                        ("Fruits \u00e0 coque", False, "legende des codes allergenes"),
                        ('class="al"', True, "codes allergenes plat par plat"),
                        ('class="bg"', True, "badges de regime V / VG / SG"),
                        ("\u2731", True, "symbole de composition variable"),
                ):
                    if motif in (t if dans_html else plat):
                        pbs.append("carte.html : %s publiee alors que la cuisine n a pas "
                                   "revalide les donnees allergenes (ALLERGENES=1 pour "
                                   "les faire sortir)" % quoi)
        # Le moteur de cartes ecrit un numero de telephone de remplissage et un
        # bouton de reservation mort. Les deux sont partis en ligne une fois
        # ailleurs ; ils ne repartiront pas.
        if 'href="#"' in t:
            pbs.append("carte.html : un lien pointe encore vers #")
        # Le selecteur de service doit mener quelque part.
        for cible in re.findall(r'<a href="#([a-z]+)">', t):
            if 'id="%s"' % cible not in t:
                pbs.append("carte.html : le selecteur de service renvoie a #%s, "
                           "qui n existe pas dans la page" % cible)
    for f2 in faites:
        c = lire(f2)
        if "+33142000000" in c:
            pbs.append("%s : numero de telephone de remplissage du moteur de cartes "
                       "(+33142000000) au lieu du 01 40 34 20 57" % f2)
        # Origine des viandes : affichette en salle, jamais un engagement ecrit
        # sur la carte. La page dit ou l information se trouve, pas ce qu elle dit.
        if re.search(r"Origine des viandes bovines", c):
            pbs.append("%s : l origine des viandes est annoncee en clair ; "
                       "elle va sur l affichette en salle" % f2)
    # Google ne documente aucun resultat enrichi pour Menu ni pour hasMenu.
    # La seule forme documentee sur une fiche d etablissement est la propriete
    # "menu" en URL simple. Le JSON-LD Menu de la page carte sert aux assistants,
    # pas a Google Search : verifie sur developers.google.com le 30/09/2026.
    if "index.html" in faites:
        a = lire("index.html")
        if '"menu":' in a and P.get("carte", {}).get("brouillon"):
            pbs.append("index.html : la propriete menu annonce la carte alors que carte.html "
                       "est encore en brouillon, donc hors navigation et hors sitemap")
        if '"menu":' in a and "carte.html" not in a:
            pbs.append("index.html : la propriete menu ne pointe pas vers carte.html")

    # Une page peut etre construite, publiee, repondre 200 — et n etre liee
    # depuis nulle part. carte.html a vecu vingt jours ainsi : dans le depot,
    # dans la construction, en ligne, et injoignable. Un controle de contenu ne
    # voit pas ca : il regarde ce qu une page contient, jamais si on y arrive.
    ORPHELINES_ADMISES = {"introuvable.html", "404.html", "index.html"}
    liens = {}
    for src in faites:
        for cible in re.findall(r'href="([a-z0-9-]+\.html)(?:#[^"]*)?"', lire(src)):
            if cible != src:
                liens.setdefault(cible, set()).add(src)
    for f3 in sorted(set(faites) - ORPHELINES_ADMISES):
        if not liens.get(f3):
            pbs.append("%s : la page est publiee mais aucune autre page du site n y mene — "
                       "elle est injoignable autrement qu au clavier" % f3)

    # --- une langue par page, et pas de lien alterne vers une page absente.
    # Le francais vit dans carte.html, l anglais vivra dans carte-en.html. Tant
    # que la seconde n existe pas, aucun hreflang : un lien alterne vers une 404
    # est pire que pas de lien du tout.
    if "carte.html" in faites:
        c = lire("carte.html")
        try:
            langue = json.loads(lire("_controle/carte-source-fr.json")).get("langue")
        except (IOError, ValueError):
            langue = None
        if langue and langue != "fr":
            pbs.append("carte.html : construite depuis un manifeste en langue %s" % langue)
        for temoin in ("Every day", "Monday to Friday", "Saturday and Sunday",
                       "Please tell your server"):
            if temoin in c:
                pbs.append("carte.html : texte anglais sur la page francaise (%s) — "
                           "une langue par page" % temoin)
        en_existe = "carte-en.html" in faites
        for f4, autre in (("carte.html", "carte-en.html"), ("carte-en.html", "carte.html")):
            if f4 not in faites:
                continue
            a = 'hreflang' in lire(f4)
            if en_existe and not a:
                pbs.append("%s : les deux langues existent mais la page ne declare "
                           "aucun lien alterne hreflang vers %s" % (f4, autre))
            if not en_existe and a:
                pbs.append("%s : la page declare un hreflang alors que la version "
                           "anglaise n est pas construite" % f4)

    # --- la carte, donnees allergenes et filtre d exclusion.
    if "carte.html" in faites:
        c = lire("carte.html")
        try:
            m = json.loads(lire("_controle/carte-source-fr.json"))
        except (IOError, ValueError):
            m = None
        if m:
            # Le silence est une affirmation : toute rubrique sans aucun code
            # doit porter son avertissement. On le verifie en comptant.
            rub = re.findall(r'<h3 class="mrub">.*?(?=<h3 class="mrub">|</section>)', c, re.S)
            muettes = [r for r in rub if 'class="mal"' not in r]
            sans_avert = [r for r in muettes if 'class="mavert"' not in r]
            if sans_avert:
                pbs.append("carte.html : %d rubrique(s) sans aucun code allergene ne portent "
                           "pas l avertissement — le silence se lit comme rien a declarer"
                           % len(sans_avert))
            # Un code de filtre qui ne figure pas dans la legende est un piege.
            for code in sorted(set(x for v in re.findall(r'data-al="([^"]+)"', c)
                                   for x in v.split("|"))):
                if '<b>%s</b>' % code not in c:
                    pbs.append("carte.html : le code %s est pose sur un plat mais absent "
                               "de la legende" % code)
            if m.get("codes_inconnus"):
                pbs.append("carte.html : codes allergenes inconnus dans la source : %s"
                           % " ".join(m["codes_inconnus"]))
            # Les codes doivent etre separes : « G Œ L » colle en « GŒL » se lit
            # comme un seul code inconnu. Un separateur par code au-dela du premier.
            n_sep = c.count('class="msep"')
            if n_sep != m.get("separateurs_codes"):
                pbs.append("carte.html : %d separateurs entre codes allergenes pour %d "
                           "attendus — des codes sortent colles"
                           % (n_sep, m.get("separateurs_codes")))
            n_al = c.count('class="mal"')
            if n_al != m.get("articles_avec_code"):
                pbs.append("carte.html : %d blocs d allergenes publies pour %d extraits"
                           % (n_al, m.get("articles_avec_code")))
        # « Sans gluten » est une mention reglementee (regl. UE 828/2014, seuil
        # 20 mg/kg). Le badge du moteur est conserve, mais jamais sous ce libelle.
        if re.search(r'title="Sans gluten"', c) or "Sans gluten</b>" in c:
            pbs.append("carte.html : la mention reglementee « sans gluten » est employee "
                       "telle quelle (regl. (UE) 828/2014, seuil 20 mg/kg) — dire ce que "
                       "le badge veut dire, pas la mention protegee")
        # Reflow : columns CSS impose un defilement bidirectionnel a 320 px.
        css = lire("assets/site.css")
        bloc = css[css.find("/* ===== la carte ====="):]
        # minmax(21rem,...) impose une colonne de 336 px : a 320 px de large,
        # la page deborde de 42 px. Mesure du 30/09. min(...,100%) le borne.
        for m in re.finditer(r"minmax\((\d+(?:\.\d+)?)rem\s*,", bloc):
            pbs.append("assets/site.css : minmax(%srem) sans min(...,100%%) — la grille "
                       "impose %d px de large et deborde sous 320 px (WCAG 1.4.10)"
                       % (m.group(1), float(m.group(1)) * 16))
        if re.search(r"(?<![-\w])columns\s*:", bloc):
            pbs.append("assets/site.css : la carte utilise columns — defilement "
                       "bidirectionnel a 320 px et a 400 % de zoom (WCAG 1.4.10)")
        if ".sr{" not in css:
            pbs.append("assets/site.css : la classe .sr (texte pour lecteur d ecran) manque, "
                       "les mots d allergene en clair deviennent visibles")

    # --- interdits de regression du projet : jamais ecrits, meme en rappel.
    INTERDITS = ((r"\b2[25]0 (?:couverts|convives|assis|places)\b", "capacite 220/250"),
                 (r"\b8 ?h ?30\b", "ouverture a 8h30"),
                 (r"m[ée]diterran", "« mediterraneen »"))
    for f5 in faites:
        brut5 = lire(f5)
        # texte visible ET attributs (meta description, alt, og:) : un interdit
        # glisse dans une balise meta est lu par Google autant qu un paragraphe.
        plat5 = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", brut5)) + " " + brut5
        for motif, quoi in INTERDITS:
            if re.search(motif, plat5, re.I):
                pbs.append("%s : interdit de regression du projet (%s)" % (f5, quoi))
    # --- referencement : chaque page porte la requete qu elle vise, et le moteur
    # de recherche doit pouvoir afficher son titre sans le couper.
    import unicodedata
    def _sa(s):
        s = unicodedata.normalize("NFD", s.lower())
        return "".join(c for c in s if unicodedata.category(c) != "Mn")
    for slug, m in P.items():
        if (slug + ".html") not in faites or m.get("brouillon"): continue
        ti, de = m.get("titre", ""), m.get("description", "")
        if len(ti) > 62:
            pbs.append("pages.json : le titre de %s fait %d signes, Google le coupe vers 60" % (slug, len(ti)))
        if len(de) > 165:
            pbs.append("pages.json : la description de %s fait %d signes (165 au plus)" % (slug, len(de)))
        mc = m.get("mot_cle")
        if mc and _sa(mc) not in _sa(ti):
            pbs.append("pages.json : le titre de %s ne contient pas sa requete cible « %s »" % (slug, mc))
    # --- l accueil vise la premiere requete de decouverte hors brunch mesuree
    # sur la fiche Google : « restaurant strasbourg saint denis » (Malou,
    # juillet-aout 2026, periode sans surcomptage). Le titre la porte, entier.
    a0 = lire("index.html")
    t0 = re.search(r"<title>([^<]*)</title>", a0)
    d0 = re.search(r'<meta name="description" content="([^"]*)"', a0)
    t0 = t0.group(1) if t0 else ""; d0 = d0.group(1) if d0 else ""
    # Regle arbitree le 30/09 (red team titre, choix de Dawoud : chic et local)
    if len(t0) > 62:
        pbs.append("index.html : le titre fait %d signes, Google le coupe vers 60" % len(t0))
    if not d0 or not (130 <= len(d0) <= 165):
        pbs.append("index.html : description absente ou hors 130-165 signes (%d)" % len(d0))
    _n = lambda x: re.sub(r"[\s\-\u2011\u2010]+", " ", _sa(x))
    if not (_n(t0).startswith("louisette") or _n(t0).endswith("louisette")):
        pbs.append("index.html : le titre doit commencer ou finir par Louisette")
    if "brasserie" not in _n(t0):
        pbs.append("index.html : le titre doit contenir « brasserie » (categorie principale de la fiche)")
    if not any(r in _n(t0) for r in ("strasbourg saint denis", "grands boulevards", "porte saint denis", "paris 10")):
        pbs.append("index.html : le titre n a aucun repere local")
    if re.search(r"\d{1,2}\s?h\b", t0):
        pbs.append("index.html : aucune heure dans le titre (elle devient fausse un jour sur sept)")
    for mot in (r"m[ée]diterran", r"8 ?h ?30", r"fait maison", r"\b250\b", r"halal", r"meilleur", r"incontournable", r"!"):
        if re.search(mot, t0 + " " + d0, re.I):
            pbs.append("index.html : titre ou description contient un interdit (%s)" % mot)
    if re.search(r"\d{1,2}\s?h\b", re.sub(r"jusqu.\s?à 2\s?h", "", d0)):
        pbs.append("index.html : la description cite une heure autre que « jusqu'à 2 h »")
    if not re.search(r'"@type":\s*"WebSite"[^}]*"name":\s*"Louisette"', a0, re.S):
        pbs.append("index.html : WebSite name doit etre « Louisette » (ce que les gens cherchent)")
    if '"@type":"WebSite"' not in a0.replace(" ", ""):
        pbs.append("index.html : donnees WebSite absentes (nom du site dans Google)")
    # --- horaires : le dimanche, la maison ouvre a 9 h (fiche Google, carte du
    # Matin, decision de Dawoud du 31/08). Toute phrase qui annonce 8 h sans
    # dire dimanche, toute ligne « Dimanche 8 h », tout balisage qui ouvre le
    # dimanche a 8 h est bloquant.
    import html as _html
    for f9 in faites + ["index.html"]:
        t9 = lire(f9)
        t9b = re.sub(r"(?s)<(script|style|head)\b.*?</\1>", " ", t9)
        t9b = re.sub(r"(?i)</(td|tr|p|li|div|h[1-6]|dd|figcaption|summary)>|<br\s*/?>", ". ", t9b)
        vis = _html.unescape(re.sub(r"<[^>]+>", " ", t9b))
        vis = re.sub(r"\s+", " ", vis)
        for ph in re.split(r"(?<=[.!?])\s", vis):
            if (re.search(r"\b(?:de |dès |des )?8 ?h\b[^.]{0,30}\b2 ?h\b", ph)
                or re.search(r"(?i)\b8 ?h\b.{0,40}(sept jours sur sept|tous les jours|7 ?j ?/ ?7)|(sept jours sur sept|tous les jours|7 ?j ?/ ?7).{0,40}\b8 ?h\b", ph)) \
                    and not re.search(r"(?i)dimanche|dim\.", ph) \
                    and not re.match(r"(?i)\s*(lundi|mardi|mercredi|jeudi|vendredi|samedi)\b", ph):
                pbs.append("%s : horaire 8 h–2 h annonce sans le dimanche 9 h : « %s »" % (f9, ph.strip()[:90]))
        if "nbsp;" in vis or "&amp;" in vis:
            pbs.append("%s : entite HTML cassee visible dans le texte (nbsp; ou &amp;)" % f9)
        if re.search(r"Dimanche\s*</(?:em|th)>\s*<(?:span|td)>\s*8 ?h", t9):
            pbs.append("%s : la ligne Dimanche indique 8 h (9 h en realite)" % f9)
        if re.search(r'"Sunday"[^}]*"opens"\s*:\s*"08:00"', t9, re.S):
            pbs.append("%s : donnees structurees : ouverture le dimanche a 8 h" % f9)
    # --- les prix du brunch viennent de la carte, jamais d ailleurs.
    if "brunch.html" in faites:
        try:
            src = set(json.loads(lire("_controle/carte-source-fr.json"))["prix"])
            vus = set(re.sub(r"\s", " ", x).replace("&nbsp;", " ").strip()
                      for x in re.findall(r"(\d+(?:,\d+)?(?:&nbsp;|\s)?€)", lire("brunch.html")))
            norm = lambda s: s.replace(" ", " ").replace("&nbsp;", " ").replace(" €", " €")
            prix_carte = set(norm(x) for x in src)
            for v in sorted(vus):
                if norm(v) not in prix_carte and norm(v).replace(" ", "") not in {x.replace(" ", "") for x in prix_carte}:
                    pbs.append("brunch.html : le prix %s n existe pas sur la carte" % v)
        except (IOError, ValueError, KeyError) as e:
            pbs.append("brunch.html : manifeste de la carte illisible (%s)" % e)

    return pbs

if __name__ == "__main__":
    faites = [page(s) for s in sorted(P)]
    print("pages construites :", ", ".join(faites))
    print("accueil :", accueil())
    sitemap(faites); print("sitemap.xml ecrit")
    if "introuvable.html" in faites:
        ecrire("404.html", lire("introuvable.html")); print("404.html ecrit")
    pbs = controler(faites)
    if pbs:
        print("\nCONTROLES EN ECHEC :"); [print("   -", p) for p in pbs]; sys.exit(1)
    en_cours = [k for k, v in P.items() if v.get("brouillon")]
    if en_cours:
        print("\nEN BROUILLON, hors navigation et hors sitemap : %s" % ", ".join(sorted(en_cours)))
    print("\ncontroles : tout est bon.")
