# Reprendre la main sur le site

Ce fichier existe pour une seule raison : aujourd'hui, une seule personne sait
faire tourner cette chaîne. Si elle n'est pas là, personne ne peut corriger une
faute en ligne. Ce document doit permettre à quelqu'un d'autre d'y arriver.

Dernière mise à jour : 9 septembre 2026.

## En trente secondes

Le site est **statique**. Il n'y a ni base de données, ni serveur applicatif.
Un script Python lit des données et écrit des pages HTML. C'est tout.

```
_donnees/*.json   +   _contenu/*.html   →   construire.py   →   *.html à la racine
```

Modifier le site = modifier un fichier dans `_donnees/` ou `_contenu/`,
relancer `python3 construire.py`, vérifier que la sortie dit « tout est bon »,
puis pousser.

## Modifier quelque chose

| Ce qu'on veut changer | Le fichier |
|---|---|
| Adresse, téléphones, horaires, réseaux, réservation, WhatsApp | `_donnees/site.json` |
| Titre et description d'une page, état brouillon | `_donnees/pages.json` |
| Le texte d'une page | `_contenu/<page>.html` |
| Les photos de la photothèque | `_donnees/photos.json` |
| La mise en forme | `assets/site.css` |
| L'accueil | `index.html` — **uniquement entre les marqueurs**, voir plus bas |

```bash
cd ~/Downloads/louisette-git
python3 construire.py        # doit finir par « controles : tout est bon. »
git add -A
git commit -m "ce que j ai change"
git push origin main
```

**Si le script s'arrête sur « CONTROLES EN ECHEC », ne pas pousser.** Il a déjà
écrit des fichiers ; l'état sur le disque est incohérent. Corriger ce qu'il
signale et relancer jusqu'à ce qu'il dise que tout est bon.

## Les deux pièges

**1. `index.html` est le seul fichier à édition partielle.** Le script n'y
remplace que les zones entre marqueurs : `<!-- NAV:debut -->…<!-- NAV:fin -->`,
`PIED`, `DOCK`, `GALERIE`. Tout le reste est écrit à la main et n'est jamais
régénéré. Supprimer un marqueur casse la mise à jour de ce bloc, en silence.

**2. Jamais d'entités HTML dans les fichiers `.json`.** On écrit `Bar & cocktails`,
pas `Bar &amp; cocktails`. Le script met en forme lui-même.

## Les garde-fous

Le script refuse de finir (code de sortie 1) si :

- un lien interne pointe vers une page qui n'existe pas ;
- un prix apparaît sur une page qui n'a pas le droit d'en porter ;
- il reste `8h30` quelque part (l'ouverture est à 8 h) ;
- une formulation « fait maison » étendue à toute la carte apparaît ;
- la mention alcool manque sur une page ;
- une image n'a pas de description ni de dimensions ;
- une note de travail traîne (`À CONFIRMER`, `TODO`, `VÉRIFIER`) ;
- une vignette de la photothèque ne correspond à aucune vue, ou l'inverse ;
- un fichier photo manque sur le disque ;
- un lien sortant a un `&` non échappé, ou n'ouvre pas dans un nouvel onglet,
  ou l'ouvre sans `rel="noopener"` ;
- la page carte est publiée alors qu'elle porte encore son marqueur de contenu
  à venir.

Ces contrôles ont chacun été mis en échec volontairement pour vérifier qu'ils
arrêtent bien la construction. Ils ne sont pas décoratifs.

## Le robot

`.github/workflows/construire.yml` relance la construction à chaque poussée qui
touche `_contenu/`, `_donnees/` ou `construire.py`, et republie si quelque chose
a changé.

- Il ne se redéclenche pas lui-même : les fichiers qu'il produit ne sont pas
  dans son filtre, et son commit porte `[skip ci]`.
- Deux poussées simultanées sont mises en file, jamais annulées.
- **Si la construction échoue, le robot ne pousse rien.** C'est le vrai filet :
  aucun état incohérent n'atteint la branche principale par ce chemin.
- En revanche il échoue **en silence** : le travail apparaît en rouge dans
  l'onglet Actions du dépôt, et rien ne prévient activement. À regarder après
  chaque modification.

## Revenir en arrière

```bash
cd ~/Downloads/louisette-git
git log --oneline -10          # trouver le commit fautif
git revert <le commit>         # annule ses modifications
git push origin main           # le robot reconstruit et republie
```

Compter dix à vingt minutes, publication comprise.

## Les accès — À COMPLÉTER PAR DAWOUD

C'est le trou de ce document, et le vrai risque. Rien de ce qui suit n'est
écrit nulle part dans le dépôt.

| Quoi | Où c'est réglé | Qui a l'accès |
|---|---|---|
| Dépôt GitHub `Dwd15/louisette-test` | github.com | [À COMPLÉTER] |
| Publication du site | Réglages du dépôt → Pages | [À COMPLÉTER] |
| Domaine `louisette-paris.com` | registrar (NordNet), messagerie Orange | [À COMPLÉTER] |
| Hébergement cible | IONOS, contrat existant | [À COMPLÉTER] |
| Réservation | compte Zenchef, `rid=364667` | [À COMPLÉTER] |
| Boîte `contact@louisette-paris.com` | Orange | [À COMPLÉTER] |
| WhatsApp Business | téléphone portant l'application | [À COMPLÉTER] |

**Si une seule ligne de ce tableau reste vide, la chaîne dépend d'une personne.**

## Ce qui n'a pas de solution de repli

| Dépendance | Ce qui se passe si elle tombe |
|---|---|
| GitHub Pages | site entièrement hors ligne, aucun hébergement de secours |
| Zenchef | tous les boutons « Réserver » morts en même temps ; le téléphone reste |
| Boîte `contact@` | toute demande écrite part dans le vide, y compris les demandes RGPD |
