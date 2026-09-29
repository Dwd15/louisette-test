# -*- coding: utf-8 -*-
"""Pont entre le moteur de cartes imprimees et le site, une langue a la fois.

  python3 _outils/carte-depuis-livraison.py ../LIVRAISON_v114/site fr
  python3 _outils/carte-depuis-livraison.py ../LIVRAISON_v114/site en   (pas encore possible)

Une langue = une page, jamais deux langues sur la meme page. Le francais sort
dans _contenu/carte.html, l anglais sortira dans _contenu/carte-en.html. Chaque
sortie depose son manifeste dans _controle/carte-source-<langue>.json, que les
controles bloquants de construire.py relisent.

Donnees allergenes : elles ne sortent que si ALLERGENES=1 est passe en
environnement. Par defaut les codes, les badges de regime et le symbole de
composition variable restent a la porte. Ce n est pas une formalite de
signature : neuf questions de recette restent sans reponse (QUESTIONS_AU_CHEF
dans la livraison), dont la sauce Cesar aux anchois, l allegation sans gluten
de douze plats et le code P de la planche de tapas.
"""
import json, os, re, sys, unicodedata
from bs4 import BeautifulSoup

SOURCE  = sys.argv[1] if len(sys.argv) > 1 else "../LIVRAISON_v114/site"
LANGUE  = (sys.argv[2] if len(sys.argv) > 2 else "fr").lower()
ALLERG  = os.environ.get("ALLERGENES") == "1"

SERVICES = [
    ("matin",  "Le Matin",   "Tous les jours 8 h – 11 h, dimanche 9 h – 11 h",
                             "Every day 8 am – 11 am, Sunday 9 am – 11 am"),
    ("midi",   "Le Midi",    "Du lundi au vendredi, 11 h – 17 h",
                             "Monday to Friday, 11 am – 5 pm"),
    ("brunch", "Le Brunch",  "Samedi et dimanche, 11 h – 18 h",
                             "Saturday and Sunday, 11 am – 6 pm"),
    ("soir",   "Le Soir",    "Tous les jours à partir de 17 h, service en salle jusqu’à 2 h",
                             "Every day from 5 pm, served until 2 am"),
    ("happy",  "Happy Hour", "Tous les jours, 15 h – minuit",
                             "Every day, 3 pm – midnight"),
]
RENVOIS = {   # une rubrique de la carte qui a deja sa page sur le site
    "AVANT LE THEATRE": ("theatres.html", "les vingt-sept salles à un quart d’heure",
                                          "the twenty-seven venues within a fifteen-minute walk"),
    "PRIVATISER  ORGANISER  SUR DEVIS": ("groupes.html", "la page groupes et privatisation",
                                          "our groups and private hire page"),
}
# Corrections tracees de la copie venue du moteur. Chacune porte sa raison.
# Elles ne modifient pas la carte imprimee : elles empechent seulement le site
# de republier une affirmation deja mesuree comme fausse.
CORRECTIONS = [
    ("Renaissance, BO Saint-Martin, Splendid, Gymnase Marie Bell et Grand Rex "
     "à moins de six minutes à pied.",
     "Renaissance, Porte Saint-Martin, Splendid, Gymnase Marie-Bell et Grand Rex : "
     "de deux à sept minutes à pied.",
     "mesure Valhalla du 10/09 : Gymnase Marie-Bell 508 m / 7 min et Grand Rex 590 m / "
     "7 min. « moins de six minutes » est faux pour deux des cinq salles."),
]

T = {
 "fr": {
  "sortie": "_contenu/carte.html", "cle_desc": "fr", "horaire": 2, "renvoi": 1,
  "sur": "La table", "titre": "La carte.",
  "chapeau": ("Une cuisine française et italienne, servie sans interruption de 8 h à 2 h, "
              "sept jours sur sept. Le café du matin, le déjeuner, le goûter et le dernier "
              "plat du soir sortent de la même cuisine, au même comptoir. Les prix sont "
              "nets, service compris."),
  "nav": "Les cinq services", "voir": "Voir aussi",
  "h_info": "Allergènes, régimes et origines.",
  "info_off": ("Les quatorze allergènes à déclaration obligatoire sont signalés plat par plat "
               "sur la carte remise en salle, ainsi que les plats végétariens, végétaliens et "
               "sans gluten. Cette page ne reproduit pas ces codes tant que la cuisine ne les "
               "a pas revalidés. Signalez une allergie ou une intolérance au moment de la "
               "commande, la cuisine en tient compte (règlement (UE) n&deg;&nbsp;1169/2011)."),
  "info_on":  ("Les quatorze allergènes à déclaration obligatoire sont signalés plat par plat "
               "ci-dessus et sur la carte remise en salle. Signalez une allergie ou une "
               "intolérance au moment de la commande (règlement (UE) n&deg;&nbsp;1169/2011)."),
  "friture": ("Nos frites sont cuites dans un bain de friture dédié, distinct des produits "
              "panés. Les boissons ne portent pas de code allergène&nbsp;: toutes nos bières "
              "contiennent du gluten, y compris la 0,0&nbsp;%&nbsp;; tous nos vins, champagnes, "
              "prosecco, portos et vermouths contiennent des sulfites&nbsp;; nos cafés lactés, "
              "chocolats, matchas et milkshakes contiennent du lait."),
  "legal": ("L’origine de nos viandes est affichée en salle, conformément aux décrets "
            "applicables. Prix nets en euros, service compris. L’abus d’alcool est dangereux "
            "pour la santé, à consommer avec modération. La vente d’alcool est interdite aux "
            "mineurs de moins de dix-huit ans (art. L.3342-1 du code de la santé publique)."),
  "h_cta": "Une table&nbsp;?",
  "cta": ("8 boulevard Saint-Denis, 75010 Paris, métro Strasbourg&#8209;Saint&#8209;Denis. "
          "Ouvert sept jours sur sept, de 8 h à 2 h."),
  "b_res": "Réserver une table",
 },
 "en": {
  "sortie": "_contenu/carte-en.html", "cle_desc": "en", "horaire": 3, "renvoi": 2,
  "sur": "The table", "titre": "The menu.",
  "chapeau": ("French and Italian cooking, served without a break from 8 am to 2 am, seven "
              "days a week. Prices are net, service included."),
  "nav": "The five services", "voir": "See also",
  "h_info": "Allergens, diets and origins.",
  "info_off": ("The fourteen declarable allergens are listed dish by dish on the menu handed "
               "to you at the table. This page does not reproduce those codes yet. Please "
               "tell your server about any allergy or intolerance when ordering "
               "(Regulation (EU) No&nbsp;1169/2011)."),
  "info_on":  ("The fourteen declarable allergens are listed dish by dish above and on the "
               "menu handed to you at the table. Please tell your server about any allergy "
               "or intolerance when ordering (Regulation (EU) No&nbsp;1169/2011)."),
  "friture": ("Our fries are cooked in a dedicated fryer, separate from breaded products. "
              "Drinks carry no allergen code: all our beers contain gluten, including the "
              "0.0&nbsp;%; all our wines, champagnes, prosecco, ports and vermouths contain "
              "sulphites; our milk coffees, chocolates, matchas and milkshakes contain milk."),
  "legal": ("The origin of our beef is displayed in the dining room. Net prices in euros, "
            "service included. Alcohol abuse is dangerous for your health, consume in "
            "moderation. The sale of alcohol to under-18s is prohibited."),
  "h_cta": "A table&nbsp;?",
  "cta": ("8 boulevard Saint-Denis, 75010 Paris, Strasbourg&#8209;Saint&#8209;Denis metro. "
          "Open seven days a week, 8 am to 2 am."),
  "b_res": "Book a table",
 },
}
if LANGUE not in T:
    sys.exit("langue inconnue : %s (fr ou en)" % LANGUE)
L = T[LANGUE]

def sansacc(s):
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^A-Z0-9 ]", " ", s.upper()).strip()

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def corriger(s, journal):
    for avant, apres, raison in CORRECTIONS:
        if avant in s:
            s = s.replace(avant, apres)
            journal.append({"avant": avant, "apres": apres, "raison": raison})
    return s

items, prix, rubriques, journal, manques = 0, set(), 0, [], []
corps = ['<section class="phero">',
         '  <div class="k">%s</div>' % L["sur"],
         '  <h1>%s</h1>' % L["titre"],
         '  <p class="pchap">%s</p>' % L["chapeau"],
         '</section>',
         '<nav class="serv" aria-label="%s">' % L["nav"]]
for s in SERVICES:
    corps.append('  <a href="#%s">%s</a>' % (s[0], s[1]))
corps.append('</nav>')

for slug, nom, h_fr, h_en in SERVICES:
    soup = BeautifulSoup(open(os.path.join(SOURCE, slug + ".html"), encoding="utf-8").read(),
                         "html.parser")
    corps.append('<section class="sect mets" id="%s">' % slug)
    corps.append('  <h2>%s</h2>' % nom)
    corps.append('  <p class="hserv">%s</p>' % (h_fr if LANGUE == "fr" else h_en))
    for sec in soup.select("main section"):
        h2, arts = sec.find("h2"), sec.find_all("article")
        if not h2 or not arts:
            continue                      # rubrique vide : elle ne descend pas sur le web
        titre = h2.get_text(" ", strip=True)
        rubriques += 1
        corps.append('  <h3 class="mrub">%s</h3>' % esc(titre))
        for note in sec.find_all("p", class_="note"):
            est_en = "en" in (note.get("class") or [])
            if est_en == (LANGUE == "en"):
                corps.append('  <p class="mnote">%s</p>'
                             % esc(corriger(note.get_text(" ", strip=True), journal)))
        corps.append('  <ul class="mliste">')
        for a in arts:
            nspan, pspan = a.find("span", class_="n"), a.find("span", class_="p")
            if not nspan:
                continue
            if not ALLERG:
                for mort in nspan.find_all("span", class_=["al", "bg"]):
                    mort.decompose()
            nom_plat = nspan.get_text(" ", strip=True)
            if not ALLERG:
                nom_plat = nom_plat.replace("✱", "").strip()
            d = a.find("p", class_=L["cle_desc"])
            if LANGUE == "en" and d is None and a.find("p", class_="fr"):
                manques.append(nom_plat)   # un plat decrit en francais mais pas en anglais
            desc = corriger(d.get_text(" ", strip=True), journal) if d else ""
            p = pspan.get_text(" ", strip=True) if pspan else ""
            if p:
                prix.add(p)
            items += 1
            ligne = '    <li><span class="mn">%s</span>' % esc(nom_plat)
            if p:
                ligne += '<span class="mp">%s</span>' % esc(p)
            if desc:
                ligne += '<p class="md">%s</p>' % esc(desc)
            corps.append(ligne + '</li>')
        corps.append('  </ul>')
        r = RENVOIS.get(sansacc(titre))
        if r:
            corps.append('  <p class="mnote">%s <a class="lien" href="%s">%s</a>.</p>'
                         % (L["voir"], r[0], r[L["renvoi"]]))
    corps.append('</section>')

corps += ['<section class="sect">',
          '  <h2>%s</h2>' % L["h_info"],
          '  <p>%s</p>' % (L["info_on"] if ALLERG else L["info_off"]),
          '  <p>%s</p>' % L["friture"],
          '  <p>%s</p>' % L["legal"],
          '</section>',
          '<!-- NEWSLETTER -->',
          '<section class="presa">',
          '  <h2>%s</h2>' % L["h_cta"],
          '  <p style="margin:0 auto;max-width:560px">%s</p>' % L["cta"],
          '  <div class="btns">',
          '    <a class="b1" href="https://bookings.zenchef.com/results?rid=364667&amp;pid=1001"'
          ' target="_blank" rel="noopener">%s</a>' % L["b_res"],
          '    <a class="b2" href="tel:+33140342057">01 40 34 20 57</a>',
          '  </div>',
          '</section>']

open(L["sortie"], "w", encoding="utf-8").write("\n".join(corps) + "\n")
os.makedirs("_controle", exist_ok=True)
json.dump({"langue": LANGUE, "chemin_source": SOURCE, "allergenes": ALLERG,
           "articles": items, "rubriques": rubriques, "prix": sorted(prix),
           "corrections": journal, "descriptions_manquantes": sorted(set(manques)),
           "methode": ("Extraction bs4 des <article> de chaque section de "
                       "LIVRAISON/site/*.html. Une langue par page. Sans ALLERGENES=1, "
                       "les spans .al et .bg et le symbole U+2731 sont supprimes.")},
          open("_controle/carte-source-%s.json" % LANGUE, "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("%s : %d articles, %d rubriques, %d prix, allergenes=%s%s"
      % (L["sortie"], items, rubriques, len(prix), ALLERG,
         (", %d plats sans description dans cette langue" % len(set(manques))) if manques else ""))
