# Modifier le site — mode d'emploi

## Ce qui se modifie, et où

| Ce que vous voulez changer | Où | Effet |
|---|---|---|
| Un horaire, un téléphone, l'adresse, l'e-mail | `_donnees/site.json` | **Se propage aux 10 pages d'un coup** |
| Le titre ou la description d'une page (ce que Google affiche) | `_donnees/pages.json` | La page concernée |
| Le texte d'une page | `_contenu/<page>.html` | La page concernée |
| Les photos | dossier `p/` | La galerie |
| La mise en page, les couleurs, les animations | `assets/site.css` — **ne pas y toucher sans prévenir** | Tout le site |

## Comment publier

**Depuis l'ordinateur :**

    cd ~/Downloads/louisette-git
    git pull
    # modifier les fichiers
    git add -A
    git commit -m "ce qui a change, en français"
    git push

Le robot reconstruit les pages tout seul, en une à deux minutes.

**Depuis un téléphone ou un autre ordinateur :** ouvrir le dépôt sur github.com, cliquer sur le fichier, sur le crayon, modifier, valider. Le robot fait le reste.

## La règle qui compte

**On ne modifie jamais un fichier `.html` de la racine à la main.** Ils sont reconstruits à chaque fois, et une modification manuelle serait effacée sans prévenir. Le texte des pages vit dans `_contenu/`, les informations dans `_donnees/`.

Seule exception : `index.html`, la page d'accueil, dont seuls la navigation, le pied de page et la barre d'action mobile sont reconstruits — le reste s'y modifie à la main, entre les marqueurs.

## Vérifier avant de publier

    python3 construire.py

Le script refuse de finir si une page a un lien mort, un horaire de 8h30, un prix qui n'aurait rien à y faire, une formulation « fait maison » interdite, ou si la mention sanitaire sur l'alcool manque.
