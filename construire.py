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
         '<main id="contenu">', corps.replace("<!-- FORMULAIRE -->", formulaire()).replace("<!-- NEWSLETTER -->", newsletter()).replace("<!-- WHATSAPP -->", bouton_whatsapp()), '</main>',
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
    for nom, contenu in (("NAV", barre() + "\n" + tiroir()), ("PIED", pied()), ("DOCK", dock()), ("GALERIE", pistes)):
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
        if re.search(r'\d\s?€', t) and not prix_ok:
            pbs.append("%s : un prix apparait alors que les prix ne sont pas reconcilies" % f)
        if "8h30" in t or "8 h 30" in t: pbs.append("%s : horaire 8h30" % f)
        # Un retour a la ligne au milieu d une phrase suffisait a faire passer
        # ces controles a cote : le 09/09, une septieme mention du Grand Rex
        # "a trois minutes" a survecu a six corrections pour cette seule raison.
        # On les fait donc travailler sur un texte a espaces normalises.
        plat = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t))

        # Les treize durees de la page theatres sont mesurees, pas estimees :
        # _controle/distances-2026-09-10.json, calculateur pieton Valhalla.
        # Le bareme precedent n avait jamais ete mesure et se trompait dans les
        # deux sens, jusqu a un facteur quatre. Toute fiche qui s ecarte de la
        # mesure arrete la construction.
        if f == "theatres.html":
            try:
                ref = json.loads(lire("_controle/distances-2026-09-10.json"))["salles"]
            except Exception as e:
                pbs.append("theatres.html : mesures de distances illisibles (%s)" % e); ref = {}
            vues = set()
            for mm in re.finditer(r'<div class="carte"><div class="d">([^<]*)</div><b>([^<]*)</b>', t):
                dit, nom = mm.group(1), mm.group(2); vues.add(nom)
                if nom not in ref:
                    pbs.append("theatres.html : la salle %s n a pas de distance mesuree" % nom); continue
                a = re.search(r"(\d[\d\s]*)\s*m", dit); b = re.search(r"(\d+)\s*min", dit)
                em = int(re.sub(r"\s", "", a.group(1))) if a else None
                emn = int(b.group(1)) if b else None
                if em != ref[nom]["metres"] or emn != ref[nom]["minutes"]:
                    pbs.append('theatres.html : %s affiche "%s" au lieu de %d m et %d min mesures'
                               % (nom, dit, ref[nom]["metres"], ref[nom]["minutes"]))
            for nom in ref:
                if nom not in vues:
                    pbs.append("theatres.html : la salle mesuree %s n est affichee nulle part" % nom)

        # Le Grand Rex est a 543 m, soit sept minutes. Toute autre duree
        # accolee a son nom est une affirmation qu un client dement avec son
        # telephone, debout sur le trottoir.
        for m in re.finditer(r"Grand Rex[^.]{0,80}", plat):
            bout = m.group(0)
            d = re.search(r"\b(une|deux|trois|quatre|cinq|six|huit|neuf|dix|\d+)\s*(minutes?|min)\b", bout)
            if d and "sept" not in bout:
                pbs.append('%s : le Grand Rex annonce a "%s" — il est a 543 m, soit sept minutes'
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
