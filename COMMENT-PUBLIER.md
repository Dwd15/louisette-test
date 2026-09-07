# Publier le site Louisette en une commande

Ce dossier est une copie complète du dépôt `Dwd15/louisette-test`, prête à publier.
Un commit y attend déjà d'être envoyé (suppression des 28 Mo de fichiers inutiles).

## Une seule fois : autoriser votre Mac

1. Ouvrir https://github.com/settings/personal-access-tokens/new
   (menu GitHub : photo de profil → Settings → Developer settings →
   Personal access tokens → Fine-grained tokens → Generate new token)

2. Remplir :
   - Token name .......... Mac Dawoud — site Louisette
   - Expiration .......... 1 an
   - Resource owner ...... Dwd15
   - Repository access ... Only select repositories → louisette-test
   - Permissions ......... Repository permissions → Contents → Read and write

3. Cliquer « Generate token » et COPIER le jeton affiché.
   Il ne s'affiche qu'une seule fois. Le coller dans un gestionnaire de mots de passe.

4. Ouvrir le Terminal (Applications → Utilitaires → Terminal) et coller :

       git config --global credential.helper osxkeychain
       cd ~/Downloads/louisette-site-git
       git push

   Git demande :
       Username for 'https://github.com':   -> Dwd15
       Password for 'https://Dwd15@github.com':  -> coller le JETON (pas le mot de passe GitHub)

   Rien ne s'affiche pendant que vous collez le jeton : c'est normal. Appuyer sur Entrée.

5. C'est fini. macOS a mémorisé le jeton dans le trousseau ;
   les prochains `git push` ne demanderont plus rien.

## Ensuite : publier une modification

       cd ~/Downloads/louisette-site-git
       git add -A
       git commit -m "ce que j'ai change"
       git push

Le site se met à jour sur https://dwd15.github.io/louisette-test/ en une à deux minutes.

## Récupérer les modifications faites ailleurs

       cd ~/Downloads/louisette-site-git
       git pull

## Si git n'est pas installé

La commande `git --version` ouvre une fenêtre proposant d'installer les outils
de développement Apple. Accepter, attendre la fin, puis reprendre à l'étape 4.

## Ce que ce dossier contient

  index.html                page du site
  meta.js                   legendes et textes alternatifs des 622 photos
  t/000.webp .. t/621.webp  vignettes du bandeau (420 px)
  p/000.webp .. p/621.webp  images de la visionneuse (1200 px)
  mentions-legales.html, confidentialite.html, robots.txt, sitemap.xml
  hero.mp4, visite.mp4, plats.mp4 et leurs variantes mobiles
