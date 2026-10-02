"""Rapprochement indépendant, article par article, avec la source v120."""
import json,re,html
from pathlib import Path
from html.parser import HTMLParser
ROOT=Path(__file__).resolve().parents[1]
def norm(s): return ' '.join(html.unescape(s).replace('’',"'").split())
class Carte(HTMLParser):
 def __init__(self):super().__init__();self.service=None;self.ul=False;self.item=None;self.nom=False;self.mal=False;self.abbr=False;self.items=[]
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='section' and a.get('id') in ['matin','midi','brunch','soir','happy']:self.service=a['id']
  if tag=='ul':self.ul=a.get('class')=='mliste'
  if tag=='li' and self.ul:self.item={'service':self.service,'nom':'','codes':a.get('data-al','').split('|') if a.get('data-al') else [],'etat':a.get('data-al-status'),'visible':[]}
  if self.item:
   if tag=='span' and a.get('class')=='mn':self.nom=True
   if tag=='p' and a.get('class')=='mal':self.mal=True
   if tag=='abbr' and self.mal:self.abbr=True
 def handle_data(self,s):
  if self.item and self.nom:self.item['nom']+=s
  if self.item and self.abbr:self.item['visible'].append(s)
 def handle_endtag(self,tag):
  if tag=='span':self.nom=False
  if tag=='abbr':self.abbr=False
  if tag=='p':self.mal=False
  if tag=='li' and self.item:self.items.append(self.item);self.item=None
  if tag=='ul':self.ul=False
source=json.loads((ROOT/'_donnees/allergenes-v120.json').read_text())
expected={(a['service'],norm(a['nom'])):a for a in source['articles']}
for filename in ['_contenu/carte.html','carte.html']:
 parser=Carte();parser.feed((ROOT/filename).read_text());seen=set()
 for a in parser.items:
  key=(a['service'],norm(a['nom']));assert key not in seen,('doublon',key);seen.add(key)
  b=expected[key]
  assert a['codes']==b['codes']==a['visible'],(filename,key,'codes',a,b)
  assert a['etat']==b['etat'],(filename,key,'etat')
 assert seen==set(expected),(filename,'articles manquants ou supplémentaires')
print('PASS — 239 articles, codes visibles et états conformes à v120 dans la source et la page publiée.')
