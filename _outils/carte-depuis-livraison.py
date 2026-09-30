# -*- coding: utf-8 -*-
"""Rend la carte du site depuis la sortie du moteur de cartes imprimees.

  python3 _outils/carte-depuis-livraison.py ../LIVRAISON_v114/site fr

STRATEGIE WEB (arbitree le 30/09/2026, apres red team) — ce qui est decide ici
et pourquoi, pour que la prochaine personne ne defasse pas par ignorance :

1. UNE SEULE URL. Le decoupage en cinq pages de service ne rapporte rien tant
   que le site est en noindex sur une URL de test, et il creerait une taxonomie
   web maintenue a la main contre un moteur qui sort trois a quatre versions par
   jour. Declencheur ecrit du decoupage : bascule sur louisette-paris.com, puis
   quatre semaines de Search Console. Pas avant.
2. AUCUNE TAXONOMIE A LA MAIN. Les 51 rubriques du moteur passent telles quelles.
   Un regroupement web se ferait dans le moteur, jamais ici.
3. LE PRIX NE VIT JAMAIS SANS SON HORAIRE. Un meme article vaut 2,60 EUR le midi
   et 5,00 EUR le soir. Chaque prix est sous le titre de son service, et l horaire
   du service est colle a ce titre. C est ce qui rend le double prix lisible au
   lieu d etre trompeur.
4. LE SILENCE EST UNE AFFIRMATION. 98 blocs de codes allergenes d un cote et
   rien de l autre se lit comme rien a declarer. Toute rubrique dont aucun
   article ne porte de code recoit l avertissement. Regle mecanique, sans
   classement a la main : elle ne peut pas se tromper de rubrique.
5. UN CODE SE LIT ET SE CHERCHE. Chaque code sort en abreviation visible plus le
   mot en clair pour les lecteurs d ecran et pour la recherche du navigateur :
   chercher arachide doit trouver le plat, pas la lettre A.
6. LE FILTRE EXCLUT, IL NE CERTIFIE PAS. Exclure les plats contenant X. Jamais
   sans gluten, qui est une mention reglementee (regl. UE 828/2014, seuil
   20 mg/kg) : le badge du moteur est conserve mais sa legende dit exactement ce
   qu il veut dire, sans reprendre la mention protegee.
7. UNE LANGUE PAR PAGE. Le moteur met le titre francais dans span et l anglais
   dans em : on ne prend que span.
"""
import json, os, re, sys, unicodedata
from bs4 import BeautifulSoup

SOURCE = sys.argv[1] if len(sys.argv) > 1 else "../LIVRAISON_v114/site"
LANGUE = (sys.argv[2] if len(sys.argv) > 2 else "fr").lower()
if LANGUE != "fr":
    sys.exit("seul le francais est traite pour l instant (decision du 30/09/2026)")

SERVICES = [
    ("matin",  "Le Matin",   "Tous les jours 8 h – 11 h, dimanche 9 h – 11 h"),
    ("midi",   "Le Midi",    "Du lundi au vendredi, 11 h – 17 h"),
    ("brunch", "Le Brunch",  "Samedi et dimanche, 11 h – 18 h"),
    ("soir",   "Le Soir",    "Tous les jours à partir de 17 h, service en salle jusqu’à 2 h"),
    ("happy",  "Happy Hour", "Tous les jours, 15 h – minuit"),
]
ALLERGENES = [("G","gluten"), ("C","crustacés"), ("Œ","œufs"), ("P","poissons"),
              ("A","arachides"), ("S","soja"), ("L","lait"), ("F","fruits à coque"),
              ("Cé","céleri"), ("MOU","moutarde"), ("SÉ","sésame"), ("SUL","sulfites"),
              ("LU","lupin"), ("M","mollusques")]
MOT = dict(ALLERGENES)
BADGES = {"V": ("Végétarien", "recette sans viande ni poisson"),
          "VG": ("Végétalien", "recette sans aucun produit animal"),
          "SG": ("Sans ingrédient contenant du gluten",
                 "aucun ingrédient de la recette n’apporte de gluten ; "
                 "la cuisine n’est pas dédiée")}
VARIABLE = "composition variable, demandez-nous avant de commander"
RENVOIS = {"AVANT LE THEATRE": ("theatres.html", "les vingt-sept salles à un quart d’heure"),
           "PRIVATISER  ORGANISER  SUR DEVIS": ("groupes.html", "la page groupes et privatisation")}
AVERTISSEMENT = ("Aucun article de cette rubrique ne porte de code&nbsp;: demandez-nous avant "
                 "de commander. Toutes nos bières contiennent du gluten, y compris la "
                 "0,0&nbsp;%&nbsp;; tous nos vins, champagnes, prosecco, portos et vermouths "
                 "contiennent des sulfites&nbsp;; nos cafés lactés, chocolats, matchas et "
                 "milkshakes contiennent du lait.")
CORRECTIONS = [
    ("Renaissance, BO Saint-Martin, Splendid, Gymnase Marie Bell et Grand Rex "
     "à moins de six minutes à pied.",
     "Renaissance, Porte Saint-Martin, Splendid, Gymnase Marie-Bell et Grand Rex : "
     "de deux à sept minutes à pied.",
     "mesure Valhalla du 10/09 : Gymnase Marie-Bell 508 m / 7 min et Grand Rex 590 m / 7 min. "
     "« moins de six minutes » est faux pour deux des cinq salles."),
]

def sansacc(s):
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^A-Z0-9 ]", " ", s.upper()).strip()

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def corriger(s, j):
    for a, b, r in CORRECTIONS:
        if a in s:
            s = s.replace(a, b); j.append({"avant": a, "apres": b, "raison": r})
    return s

def decoder(txt):
    """'G · Œ · L' -> ['G','Œ','L'], en ignorant le symbole de composition variable."""
    out = []
    for m in re.split(r"[·,]", txt or ""):
        m = m.strip()
        if m and m != "✱":
            out.append(m)
    return out

# --- le filtre d exclusion, en clair et sans dependance.
# Regle d honnetete du filtre : un plat SANS code declare n est jamais masque,
# parce qu on ne peut pas affirmer une absence. Le compteur dit combien de plats
# affiches sont dans ce cas, sinon la liste obtenue se lirait comme une garantie.
FILTRE_JS = """<script>(function(){
var f=document.getElementById('filtre');if(!f)return;
var cases=[].slice.call(f.querySelectorAll('input[data-al]'));
var plats=[].slice.call(document.querySelectorAll('ul.mliste>li'));
var listes=[].slice.call(document.querySelectorAll('ul.mliste'));
var cpt=document.getElementById('fcount'),raz=document.getElementById('fraz');
function s(n){return n>1?'s':'';}
function appliquer(){
var ex=cases.filter(function(c){return c.checked;}).map(function(c){return c.getAttribute('data-al');});
var caches=0,vus=0,muets=0;
plats.forEach(function(li){
var d=li.getAttribute('data-al'),hit=false;
if(d&&ex.length){var l=d.split('|');hit=ex.some(function(x){return l.indexOf(x)>=0;});}
li.hidden=hit;
if(hit){caches++;}else{vus++;if(!d){muets++;}}});
listes.forEach(function(ul){
var vide=ul.querySelectorAll('li:not([hidden])').length===0;
ul.hidden=vide;
var el=ul.previousElementSibling,pile=[];
while(el&&el.tagName!=='H3'){pile.push(el);el=el.previousElementSibling;}
if(el){pile.push(el);}
pile.forEach(function(x){x.hidden=vide;});});
cpt.textContent=ex.length?(caches+' plat'+s(caches)+' \u00e9cart\u00e9'+s(caches)+' \u00b7 '+vus+' affich\u00e9'+s(vus)+', dont '+muets+' sans code d\u00e9clar\u00e9 \u2014 demandez-nous.'):'';
}
cases.forEach(function(c){c.addEventListener('change',appliquer);});
raz.addEventListener('click',function(){cases.forEach(function(c){c.checked=false;});appliquer();});
appliquer();})();</script>"""

items, prix, rubriques, journal = 0, set(), 0, []
separateurs = [0]
inconnus, sans_code, avec_code, codes_vus = set(), 0, 0, set()
# JSON-LD : Google ne documente aucun resultat enrichi pour Menu (verifie le
# 30/09/2026). Il est la pour les assistants. Donc on n y met que ce que le HTML
# n exprime que visuellement : quel prix appartient a quel service. Pas de
# description, pas d allergene — ils sont deja dans la page, les recopier
# doublerait le poids pour rien.
menu_ld = {"@context": "https://schema.org", "@type": "Menu",
           "name": "La carte de La Maison Louisette", "inLanguage": "fr-FR",
           "hasMenuSection": []}
service_ld = None

corps = ['<section class="phero">',
         '  <div class="k">La table</div>',
         '  <h1>La carte.</h1>',
         '  <p class="pchap">Une cuisine française et italienne, du petit-déjeuner, dès 8 h (9 h le dimanche), '
         'au dîner&nbsp;; la maison reste ouverte jusqu’à 2 h, sept jours sur sept. Le café du matin, '
         'le déjeuner, le goûter et le dernier plat du soir sortent de la même cuisine. Les prix sont '
         'nets, service compris&nbsp;: <b>ils changent selon le service, et chaque prix est '
         'affiché sous l’horaire du service qui l’applique.</b></p>',
         '</section>',
         '<nav class="serv" aria-label="Les cinq services">']
for s in SERVICES:
    corps.append('  <a href="#%s">%s</a>' % (s[0], s[1]))
corps.append('</nav>')

# --- le filtre d exclusion et la legende, en tete, replies par defaut
corps.append('<section class="sect outils" id="outils">')
corps.append('  <details class="filtre" id="filtre">')
corps.append('    <summary>Écarter les plats qui contiennent un allergène</summary>')
corps.append('    <p class="fnote">La liste obtenue s’appuie sur les ingrédients déclarés de '
             'chaque recette. Notre cuisine n’est pas dédiée&nbsp;: une contamination croisée '
             'ne peut pas être exclue. Signalez toujours votre allergie au service avant de '
             'commander.</p>')
corps.append('    <div class="fcases">')
for c, mot in ALLERGENES:
    corps.append('      <label><input type="checkbox" data-al="%s"> %s</label>' % (esc(c), mot))
corps.append('    </div>')
corps.append('    <p class="fcount" id="fcount" role="status" aria-live="polite"></p>')
corps.append('    <p><button type="button" class="fraz" id="fraz">Tout réafficher</button></p>')
corps.append('    <noscript><p class="fnote">Ce tri demande JavaScript. Les codes restent '
             'lisibles sous chaque plat.</p></noscript>')
corps.append('  </details>')
corps.append('  <details class="legende">')
corps.append('    <summary>Lire les codes de la carte</summary>')
corps.append('    <p>%s</p>' % " · ".join("<b>%s</b> %s" % (esc(c), m) for c, m in ALLERGENES))
corps.append('    <p>%s</p>' % " · ".join("<b>%s</b> %s (%s)" % (esc(k), v[0], v[1])
                                          for k, v in BADGES.items()))
corps.append('    <p><b>✱</b> %s</p>' % VARIABLE)
corps.append('  </details>')
corps.append('</section>')

for slug, nom, horaire in SERVICES:
    soup = BeautifulSoup(open(os.path.join(SOURCE, slug + ".html"), encoding="utf-8").read(),
                         "html.parser")
    service_ld = {"@type": "MenuSection", "name": "%s — %s" % (nom, horaire),
                  "hasMenuSection": []}
    menu_ld["hasMenuSection"].append(service_ld)
    corps.append('<section class="sect mets" id="%s">' % slug)
    corps.append('  <h2>%s</h2>' % nom)
    corps.append('  <p class="hserv">%s — les prix de cette rubrique s’appliquent à ce '
                 'service.</p>' % horaire)
    for sec in soup.select("main section"):
        h2, arts = sec.find("h2"), sec.find_all("article")
        if not h2 or not arts:
            continue
        sp = h2.find("span")                       # span = francais, em = anglais
        titre = (sp or h2).get_text(" ", strip=True)
        rubriques += 1
        sec_ld = {"@type": "MenuSection", "name": titre, "hasMenuItem": []}
        corps.append('  <h3 class="mrub">%s</h3>' % esc(titre))
        for note in sec.find_all("p", class_="note"):
            if "en" not in (note.get("class") or []):
                corps.append('  <p class="mnote">%s</p>'
                             % esc(corriger(note.get_text(" ", strip=True), journal)))
        codes_rubrique = 0
        lignes = []
        for a in arts:
            nspan, pspan = a.find("span", class_="n"), a.find("span", class_="p")
            if not nspan:
                continue
            al = decoder(a.find("span", class_="al").get_text(" ", strip=True)
                         if a.find("span", class_="al") else "")
            bg = [b.strip() for b in re.split(r"[,·]",
                  a.find("span", class_="bg").get_text(" ", strip=True)
                  if a.find("span", class_="bg") else "") if b.strip()]
            for x in al:
                codes_vus.add(x)
                if x not in MOT:
                    inconnus.add(x)
            for mort in nspan.find_all("span", class_=["al", "bg"]):
                mort.decompose()
            nom_plat = nspan.get_text(" ", strip=True)
            variable = "✱" in nom_plat
            nom_plat = nom_plat.replace("✱", "").strip()
            d = a.find("p", class_="fr")
            desc = corriger(d.get_text(" ", strip=True), journal) if d else ""
            p = pspan.get_text(" ", strip=True) if pspan else ""
            if p:
                prix.add(p)
            items += 1
            if al:
                codes_rubrique += 1; avec_code += 1
            else:
                sans_code += 1
            li = ['    <li%s>' % (' data-al="%s"' % esc("|".join(al)) if al else "")]
            li.append('<span class="mn">%s</span>' % esc(nom_plat))
            if p:
                li.append('<span class="mp">%s</span>' % esc(p))
            if bg:
                li.append('<span class="mbg">%s</span>'
                          % "".join('<abbr title="%s">%s</abbr>'
                                    % (esc(BADGES.get(b, (b, ""))[0]), esc(b)) for b in bg))
            if desc:
                li.append('<p class="md">%s</p>' % esc(desc))
            if al or variable:
                bits = ['<p class="mal"><span class="mlab">Allergènes déclarés&nbsp;: </span>']
                for i, c in enumerate(al):
                    if i:
                        bits.append('<span class="msep" aria-hidden="true"> \u00b7 </span>')
                        separateurs[0] += 1
                    bits.append('<abbr title="%s">%s</abbr>' % (esc(MOT.get(c, c)), esc(c)))
                    bits.append('<span class="sr">%s%s</span>'
                                % (esc(MOT.get(c, c)), ", " if i < len(al) - 1 else ""))
                if variable:
                    bits.append('<span class="mvar" aria-hidden="true">✱</span>')
                    bits.append('<span class="sr"> — %s</span>' % VARIABLE)
                bits.append('</p>')
                li.append("".join(bits))
            lignes.append("".join(li) + '</li>')
            art_ld = {"@type": "MenuItem", "name": nom_plat}
            mm = re.match(r"^(\d+(?:,\d+)?)\s*€$", p.replace("\u202f", " ").strip())
            if mm:
                art_ld["offers"] = {"@type": "Offer", "price": mm.group(1).replace(",", "."),
                                    "priceCurrency": "EUR"}
            sec_ld["hasMenuItem"].append(art_ld)
        if codes_rubrique == 0:
            corps.append('  <p class="mavert">%s</p>' % AVERTISSEMENT)
        corps.append('  <ul class="mliste">')
        corps += lignes
        corps.append('  </ul>')
        r = RENVOIS.get(sansacc(titre))
        if r:
            corps.append('  <p class="mnote">Voir aussi <a class="lien" href="%s">%s</a>.</p>'
                         % (r[0], r[1]))
        service_ld["hasMenuSection"].append(sec_ld)
    corps.append('</section>')

corps += ['<section class="sect">',
          '  <h2>Allergènes, régimes et origines.</h2>',
          '  <p>Les quatorze allergènes à déclaration obligatoire sont signalés plat par plat '
          'ci-dessus et sur la carte remise en salle (règlement (UE) n&deg;&nbsp;1169/2011). '
          'Ils portent sur les ingrédients volontairement incorporés à la recette. '
          '<b>Notre cuisine n’est pas dédiée&nbsp;: une contamination croisée ne peut pas être '
          'exclue.</b> Signalez une allergie ou une intolérance au moment de la commande.</p>',
          '  <p>Nos frites sont cuites dans un bain de friture dédié, distinct des produits '
          'panés. Les boissons ne portent pas de code&nbsp;: la rubrique concernée le rappelle '
          'à chaque fois.</p>',
          '  <p>L’origine de nos viandes est affichée en salle, conformément aux décrets '
          'applicables. Prix nets en euros, service compris. L’abus d’alcool est dangereux pour '
          'la santé, à consommer avec modération. La vente d’alcool est interdite aux mineurs '
          'de moins de dix-huit ans (art. L.3342-1 du code de la santé publique).</p>',
          '</section>',
          '<script type="application/ld+json">%s</script>'
          % json.dumps(menu_ld, ensure_ascii=False, separators=(",", ":")),
          FILTRE_JS,
          '<!-- NEWSLETTER -->',
          '<section class="presa">',
          '  <h2>Une table&nbsp;?</h2>',
          '  <p style="margin:0 auto;max-width:560px">8 boulevard Saint-Denis, 75010 Paris, '
          'métro Strasbourg&#8209;Saint&#8209;Denis. Ouvert sept jours sur sept, de 8 h (9 h le dimanche) à 2 h.</p>',
          '  <div class="btns">',
          '    <a class="b1" href="https://bookings.zenchef.com/results?rid=364667&amp;pid=1001"'
          ' target="_blank" rel="noopener">Réserver une table</a>',
          '    <a class="b2" href="tel:+33140342057">01 40 34 20 57</a>',
          '  </div>',
          '</section>']

open("_contenu/carte.html", "w", encoding="utf-8").write("\n".join(corps) + "\n")
os.makedirs("_controle", exist_ok=True)
json.dump({"langue": "fr", "chemin_source": SOURCE, "allergenes": True,
           "articles": items, "rubriques": rubriques, "prix": sorted(prix),
           "articles_avec_code": avec_code, "separateurs_codes": separateurs[0], "articles_sans_code": sans_code,
           "codes_vus": sorted(codes_vus), "codes_inconnus": sorted(inconnus),
           "corrections": journal,
           "methode": ("Extraction bs4. Titre de rubrique = span du h2 (em = anglais, ecarte). "
                       "Codes allergenes rendus en abbr + mot en clair pour lecteur d ecran et "
                       "recherche navigateur, plus data-al pour le filtre d exclusion. Toute "
                       "rubrique sans aucun code porte l avertissement.")},
          open("_controle/carte-source-fr.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("carte fr : %d articles (%d codes, %d sans), %d rubriques, %d prix, %d sections JSON-LD"
      % (items, avec_code, sans_code, rubriques, len(prix), sum(len(s["hasMenuSection"]) for s in menu_ld["hasMenuSection"])))
if inconnus:
    print("  CODES INCONNUS :", " ".join(sorted(inconnus)))
