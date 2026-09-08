/* ==========================================================================
   La Maison Louisette — mesure d'audience sans cookie
   --------------------------------------------------------------------------
   Fichier autonome, aucune dépendance, ES5 (compatible Safari ancien).

   CE QUE FAIT CE FICHIER
     - Il n'envoie RIEN par lui-même : il se contente d'appeler la fonction
       window.plausible() posée par le script de mesure chargé dans le <head>.
     - Il reconnaît les liens par leur href (délégation d'événement sur
       document). Aucun attribut à poser sur les liens : le défaut de
       l'ancien site (143 liens balisés sur ~200) disparaît par construction.
     - Il n'écrit ni cookie, ni localStorage, ni sessionStorage.
       Il ne lit qu'un seul drapeau, celui d'opposition, posé par le visiteur
       lui-même depuis la page « Politique de confidentialité ».
     - Si le script de mesure n'est pas là (bloqueur, panne, oubli), il met
       les événements en file quelques secondes puis se coupe proprement :
       il retire ses écouteurs et ne consomme plus rien.
     - Aucune ligne ne peut lever d'erreur JavaScript : tout est sous garde.

   CE QU'IL N'ENVOIE JAMAIS
     Aucun identifiant, aucun contenu de formulaire, aucune adresse e-mail
     saisie, aucun numéro de téléphone composé par le visiteur, aucun UTM.
     Trois familles d'événements seulement — présence sur une page, usage
     d'une fonctionnalité (clic), statistique de défilement — ce qui est
     exactement le périmètre admis par l'outil d'auto-évaluation CNIL
     « mesure d'audience exemptée de consentement » (juillet 2025).

   BRANCHEMENT (voir mesure-note.md pour les lignes exactes du <head>)
     <script defer data-domain="…" src="https://plausible.io/js/script.js"></script>
     <script>window.plausible=window.plausible||function(){(window.plausible.q=window.plausible.q||[]).push(arguments)}</script>
     <script defer src="/js/mesure.js"></script>
   ========================================================================== */

(function () {
  'use strict';

  /* =====================================================================
     1. RÉGLAGES — la seule zone à modifier
     ===================================================================== */

  var REGLAGES = {

    /* Hôtes sur lesquels on ne mesure PAS : poste de développement, aperçu
       GitHub Pages tant que le site est en noindex. Comparaison sur la fin
       du nom d'hôte, donc « github.io » couvre « dawoud.github.io ». */
    hotesExclus: ['localhost', '127.0.0.1', '::1', 'github.io', '.local'],

    /* Numéros de téléphone de la maison, en chiffres nus (indicatif compris).
       Clé = étiquette envoyée dans la propriété « type ». */
    telephones: {
      '33140342057': 'salle',
      '33974640384': 'groupes'
    },

    /* Reconnaissance des destinations par fragment de nom d'hôte ou d'URL.
       L'ordre compte : la première règle qui correspond gagne. */
    destinations: [
      { evenement: 'reservation_click', motifs: ['zenchef'] },
      { evenement: 'devis_click',       motifs: ['privateaser'] },
      { evenement: 'whatsapp_click',    motifs: ['wa.me', 'whatsapp.com'] },
      { evenement: 'itineraire_click',  motifs: ['google.com/maps', 'maps.google', 'goo.gl/maps', 'maps.app.goo.gl', 'waze.com'] }
    ],

    /* Sélecteurs du bouton d'ouverture du menu mobile (le « burger »). */
    selecteurBurger: '#burger, .burger, [data-burger], [data-menu-toggle]',

    /* Identifiant de la visionneuse photo (« lightbox »). */
    idGalerie: 'glb',

    /* Seuil de défilement, en pourcentage de la hauteur utile de la page. */
    seuilDefilement: 50,

    /* Hauteur défilable minimale (px) sous laquelle « 50 % » ne veut rien
       dire : une page courte atteindrait le seuil dès le chargement. */
    hauteurMiniDefilable: 300,

    /* Envoyer les propriétés (page, section, type…) ?
       Chez Plausible, les propriétés personnalisées sont une fonction du
       plan Business. Sur un plan Starter ou Growth, elles sont ignorées :
       passer « proprietes » à false et « suffixeSection » à true pour
       encoder la section dans le NOM de l'événement à la place. */
    proprietes: true,
    suffixeSection: false,

    /* Délai (ms) et nombre de tentatives avant de renoncer si la fonction
       de mesure n'apparaît jamais. */
    delaiAttente: 2000,
    tentativesMax: 3,

    /* Taille maximale de la file d'attente. Au-delà, on jette : mieux vaut
       perdre des événements que faire grossir la mémoire du navigateur. */
    fileMax: 20,

    /* Longueur maximale d'une valeur de propriété. */
    longueurMaxValeur: 60
  };

  /* =====================================================================
     2. ÉTAT INTERNE — variables simples, aucune persistance
     ===================================================================== */

  var actif = true;          // passe à false quand on renonce définitivement
  var file = [];             // événements en attente de la fonction de mesure
  var tentatives = 0;
  var minuteur = null;

  var defilementEnvoye = false;
  var dernierMenu = 0;       // horodatage, anti-doublon du menu
  var dernierGalerie = 0;
  var videosVues = [];       // tableau plutôt que WeakSet : ES5

  var observateurs = [];     // MutationObserver à débrancher si on renonce

  /* =====================================================================
     3. OUTILS — tous tolérants aux éléments absents
     ===================================================================== */

  /* Exécute f en avalant toute erreur. Rien dans ce fichier ne doit pouvoir
     casser la page : la mesure est accessoire, le site est l'essentiel. */
  function sur(f, valeurParDefaut) {
    try { return f(); } catch (e) { return valeurParDefaut; }
  }

  function texte(v) {
    if (v === null || v === undefined) return '';
    v = String(v).replace(/\s+/g, ' ').trim();
    return v.length > REGLAGES.longueurMaxValeur
      ? v.slice(0, REGLAGES.longueurMaxValeur)
      : v;
  }

  /* Remonte les ancêtres jusqu'au premier élément portant un id non vide.
     C'est cela, « la position du lien dans la page » : on saura si le clic
     vient du bandeau haut, du bloc « groupes », du pied de page, etc. */
  function sectionDe(element) {
    return sur(function () {
      var n = element && element.parentElement;
      var garde = 0;
      while (n && n.nodeType === 1 && garde < 30) {
        var id = n.getAttribute && n.getAttribute('id');
        if (id && id !== REGLAGES.idGalerie) return texte(id);
        n = n.parentElement;
        garde++;
      }
      return 'hors-section';
    }, 'hors-section');
  }

  /* Nom lisible de la page : data-page du <body> si le HTML le fournit,
     sinon déduit du chemin. « / » et « /index.html » deviennent « accueil ». */
  function nomPage() {
    return sur(function () {
      var attr = document.body && document.body.getAttribute('data-page');
      if (attr) return texte(attr);
      var chemin = (location.pathname || '/').toLowerCase();
      var fichier = chemin.split('/').pop() || '';
      fichier = fichier.replace(/\.html?$/, '');
      if (!fichier || fichier === 'index') return 'accueil';
      return texte(fichier);
    }, 'inconnue');
  }

  function langue() {
    return sur(function () {
      var l = document.documentElement.getAttribute('lang') || 'fr';
      return l.slice(0, 2).toLowerCase();
    }, 'fr');
  }

  /* Chiffres nus d'un numéro de téléphone : « tel:+33 1 40 34 20 57 »,
     « tel:0140342057 » et « tel:+33140342057 » doivent tous donner
     « 33140342057 ». Le 0 initial français est remplacé par 33. */
  function normaliserTelephone(href) {
    return sur(function () {
      var brut = href.replace(/^tel:/i, '').replace(/[^0-9+]/g, '');
      if (brut.charAt(0) === '+') brut = brut.slice(1);
      else if (brut.charAt(0) === '0') brut = '33' + brut.slice(1);
      return brut;
    }, '');
  }

  /* =====================================================================
     4. ENVOI — adaptateur unique vers l'outil de mesure
     --------------------------------------------------------------------
     Un seul endroit connaît le nom de l'outil. Changer de prestataire
     (Umami, Matomo, auto-hébergement) revient à réécrire cette fonction,
     rien d'autre dans le fichier n'y touche.
     ===================================================================== */

  function fonctionMesure() {
    return sur(function () {
      return (typeof window.plausible === 'function') ? window.plausible : null;
      /* Variante Umami :
         return (window.umami && typeof window.umami.track === 'function')
           ? function (nom, opt) { window.umami.track(nom, opt && opt.props); }
           : null; */
    }, null);
  }

  function transmettre(fn, nom, props) {
    sur(function () {
      if (REGLAGES.proprietes && props) fn(nom, { props: props });
      else fn(nom);
    });
  }

  function envoyer(nom, propsSup) {
    if (!actif) return;

    var props = sur(function () {
      var p = { page: nomPage(), langue: langue() };
      if (propsSup) {
        for (var k in propsSup) {
          if (Object.prototype.hasOwnProperty.call(propsSup, k) && propsSup[k]) {
            p[k] = texte(propsSup[k]);
          }
        }
      }
      return p;
    }, null);

    /* Repli sans propriétés (plan Starter/Growth) : la section entre dans
       le nom de l'événement, seul moyen de garder l'information. */
    if (REGLAGES.suffixeSection && props && props.section) {
      nom = nom + '_' + props.section;
    }

    var fn = fonctionMesure();
    if (fn) { transmettre(fn, nom, props); return; }

    if (file.length < REGLAGES.fileMax) file.push([nom, props]);
    if (!minuteur) minuteur = setTimeout(vider, REGLAGES.delaiAttente);
  }

  function vider() {
    minuteur = null;
    var fn = fonctionMesure();
    if (fn) {
      tentatives = 0;
      var aEnvoyer = file;
      file = [];
      for (var i = 0; i < aEnvoyer.length; i++) {
        transmettre(fn, aEnvoyer[i][0], aEnvoyer[i][1]);
      }
      return;
    }
    tentatives++;
    if (tentatives >= REGLAGES.tentativesMax) { renoncer(); return; }
    minuteur = setTimeout(vider, REGLAGES.delaiAttente);
  }

  /* Coupure propre : on retire tout, on ne laisse ni écouteur ni file. */
  function renoncer() {
    actif = false;
    file = [];
    if (minuteur) { clearTimeout(minuteur); minuteur = null; }
    sur(function () { document.removeEventListener('click', auClic, true); });
    sur(function () { document.removeEventListener('play', auPlay, true); });
    sur(function () { window.removeEventListener('scroll', auDefilement); });
    for (var i = 0; i < observateurs.length; i++) {
      sur(function () { observateurs[i].disconnect(); });
    }
    observateurs = [];
  }

  /* =====================================================================
     5. CLICS — une seule délégation sur document, en phase de capture
     --------------------------------------------------------------------
     La phase de capture garantit que l'événement nous parvient même si un
     script de la page appelle stopPropagation() sur son propre gestionnaire
     (c'était le cas de la visionneuse photo de l'ancien site).
     ===================================================================== */

  function auClic(e) {
    if (!actif) return;
    sur(function () {
      var cible = e.target;
      if (!cible || !cible.closest) return;      // vieux navigateur : on sort

      /* --- Menu mobile : le bouton n'est pas un lien, on le traite à part */
      var burger = cible.closest(REGLAGES.selecteurBurger);
      if (burger) {
        /* Si le bouton porte aria-expanded, l'observateur du §7 fait le
           travail (il capte aussi l'ouverture au clavier). Sinon, ici. */
        if (!burger.hasAttribute('aria-expanded')) menuOuvert(burger);
        return;
      }

      var lien = cible.closest('a[href], area[href]');
      if (!lien) return;

      var href = lien.getAttribute('href') || '';
      if (!href) return;

      var section = sectionDe(lien);
      var bas = href.toLowerCase();

      /* --- Téléphone ------------------------------------------------- */
      if (bas.indexOf('tel:') === 0) {
        var numero = normaliserTelephone(href);
        var type = REGLAGES.telephones[numero] || 'autre';
        envoyer('phone_click', { type: type, section: section });
        return;
      }

      /* --- E-mail ----------------------------------------------------
         On n'envoie QUE la boîte visée (« contact », « groupes »), jamais
         l'adresse complète du visiteur ni le corps du message. */
      if (bas.indexOf('mailto:') === 0) {
        var boite = sur(function () {
          return href.replace(/^mailto:/i, '').split('?')[0].split('@')[0];
        }, '');
        envoyer('email_click', { boite: boite || 'inconnue', section: section });
        return;
      }

      /* --- Destinations externes reconnues par l'URL -----------------
         On compare sur l'URL absolue (lien.href) : un lien écrit en
         relatif ou raccourci est ainsi résolu avant comparaison. */
      var absolu = sur(function () { return (lien.href || href).toLowerCase(); }, bas);
      var regles = REGLAGES.destinations;
      for (var i = 0; i < regles.length; i++) {
        var motifs = regles[i].motifs;
        for (var j = 0; j < motifs.length; j++) {
          if (absolu.indexOf(motifs[j]) > -1) {
            envoyer(regles[i].evenement, { section: section });
            return;
          }
        }
      }
    });
  }

  /* =====================================================================
     6. DÉFILEMENT — un seul envoi par page, jamais répété
     ===================================================================== */

  function auDefilement() {
    if (!actif || defilementEnvoye) return;
    sur(function () {
      var doc = document.documentElement;
      var hauteurUtile = (doc.scrollHeight || 0) - (window.innerHeight || 0);

      /* Page non défilable ou trop courte : le seuil de 50 % serait atteint
         au chargement et ne mesurerait rien. On ne l'arme pas. */
      if (hauteurUtile < REGLAGES.hauteurMiniDefilable) return;

      var position = (window.pageYOffset || doc.scrollTop || 0);
      var pourcent = (position / hauteurUtile) * 100;

      if (pourcent >= REGLAGES.seuilDefilement) {
        defilementEnvoye = true;
        window.removeEventListener('scroll', auDefilement);
        envoyer('scroll_50', null);
      }
    });
  }

  /* =====================================================================
     7. MENU MOBILE ET VISIONNEUSE — surveillés par MutationObserver
     --------------------------------------------------------------------
     On observe l'état du DOM plutôt que le clic : cela capte aussi les
     ouvertures au clavier et reste juste si le site change son gestionnaire.
     ===================================================================== */

  function menuOuvert(source) {
    var maintenant = Date.now ? Date.now() : +new Date();
    if (maintenant - dernierMenu < 500) return;   // anti-doublon
    dernierMenu = maintenant;
    envoyer('menu_ouvert', { section: source ? sectionDe(source) : 'entete' });
  }

  function galerieOuverte() {
    var maintenant = Date.now ? Date.now() : +new Date();
    if (maintenant - dernierGalerie < 500) return;
    dernierGalerie = maintenant;
    envoyer('galerie_ouverte', null);
  }

  function observer(cible, options, reaction) {
    sur(function () {
      if (!window.MutationObserver || !cible) return;
      var o = new MutationObserver(function (mutations) {
        sur(function () { reaction(mutations); });
      });
      o.observe(cible, options);
      observateurs.push(o);
    });
  }

  function brancherMenu() {
    sur(function () {
      var boutons = document.querySelectorAll(REGLAGES.selecteurBurger);
      for (var i = 0; i < boutons.length; i++) {
        (function (bouton) {
          if (!bouton.hasAttribute('aria-expanded')) return;   // géré au clic
          observer(bouton, { attributes: true, attributeFilter: ['aria-expanded'] },
            function () {
              if (bouton.getAttribute('aria-expanded') === 'true') menuOuvert(bouton);
            });
        })(boutons[i]);
      }
    });
  }

  /* Vrai si l'élément est visiblement ouvert : classe « open », aria-hidden
     à false, ou simplement affiché. On teste large, la visionneuse pouvant
     être ouverte par une classe, un attribut ou un style en ligne. */
  function estOuvert(el) {
    return sur(function () {
      if (!el) return false;
      if (el.hasAttribute('hidden')) return false;
      if (el.getAttribute('aria-hidden') === 'true') return false;
      if (el.className && String(el.className).indexOf('open') > -1) return true;
      if (el.getAttribute('aria-hidden') === 'false') return true;
      var style = window.getComputedStyle ? window.getComputedStyle(el) : null;
      if (style && (style.display === 'none' || style.visibility === 'hidden')) return false;
      return !!(el.offsetWidth || el.offsetHeight);
    }, false);
  }

  function brancherGalerie() {
    sur(function () {
      var etatPrecedent = false;

      function attacher(el) {
        etatPrecedent = estOuvert(el);
        if (etatPrecedent) galerieOuverte();   // déjà ouverte à l'attache
        observer(el,
          { attributes: true, attributeFilter: ['class', 'hidden', 'aria-hidden', 'style'] },
          function () {
            var ouvert = estOuvert(el);
            if (ouvert && !etatPrecedent) galerieOuverte();
            etatPrecedent = ouvert;
          });
      }

      var galerie = document.getElementById(REGLAGES.idGalerie);
      if (galerie) { attacher(galerie); return; }

      /* La visionneuse est souvent créée à la volée : on attend son
         insertion, puis on débranche le guetteur pour ne rien laisser
         tourner inutilement. */
      if (!window.MutationObserver || !document.body) return;
      var guetteur = new MutationObserver(function () {
        sur(function () {
          var tardive = document.getElementById(REGLAGES.idGalerie);
          if (!tardive) return;
          guetteur.disconnect();
          attacher(tardive);
        });
      });
      guetteur.observe(document.body, { childList: true, subtree: true });
      observateurs.push(guetteur);
    });
  }

  /* =====================================================================
     8. VIDÉOS — une lecture comptée une fois par élément
     --------------------------------------------------------------------
     L'événement « play » ne remonte pas (il ne bulle pas) : la phase de
     capture sur document est le seul moyen de l'attraper sans écouteur
     par vidéo, y compris pour une vidéo insérée après le chargement.
     ===================================================================== */

  function auPlay(e) {
    if (!actif) return;
    sur(function () {
      var v = e.target;
      if (!v || !v.tagName) return;
      var balise = v.tagName.toLowerCase();
      if (balise !== 'video' && balise !== 'audio') return;

      for (var i = 0; i < videosVues.length; i++) {
        if (videosVues[i] === v) return;             // déjà comptée
      }
      videosVues.push(v);

      /* Nom du fichier seulement : ni chemin complet, ni paramètre. */
      var source = sur(function () {
        var s = v.currentSrc || v.getAttribute('src') || '';
        if (!s) {
          var so = v.querySelector && v.querySelector('source');
          s = so ? (so.getAttribute('src') || '') : '';
        }
        return s.split('?')[0].split('/').pop();
      }, '');

      envoyer('film_lance', { fichier: source || 'inconnu', section: sectionDe(v) });
    });
  }

  /* =====================================================================
     9. DÉMARRAGE
     ===================================================================== */

  function hoteExclu() {
    return sur(function () {
      if (location.protocol === 'file:') return true;
      var h = (location.hostname || '').toLowerCase();
      var liste = REGLAGES.hotesExclus;
      for (var i = 0; i < liste.length; i++) {
        var e = liste[i].toLowerCase();
        if (h === e || h.slice(-e.length) === e) return true;
      }
      return false;
    }, false);
  }

  /* Opposition du visiteur. On LIT seulement : c'est la page « Politique de
     confidentialité » qui écrit ce drapeau, via seDesinscrire() ci-dessous.
     Ce drapeau n'est pas un identifiant : il ne vaut que « ne me mesure pas ». */
  function sestOppose() {
    return sur(function () {
      return window.localStorage &&
             window.localStorage.getItem('plausible_ignore') === 'true';
    }, false);
  }

  function demarrer() {
    if (hoteExclu() || sestOppose()) { actif = false; return; }

    document.addEventListener('click', auClic, true);
    document.addEventListener('play', auPlay, true);
    window.addEventListener('scroll', auDefilement,
      sur(function () {
        /* On tente { passive: true } ; si le navigateur ne connaît pas les
           options d'écouteur, il lira « false » comme useCapture, ce qui
           reste correct ici. */
        var teste = false;
        var opt = Object.defineProperty({}, 'passive', {
          get: function () { teste = true; return true; }
        });
        window.addEventListener('_t', null, opt);
        window.removeEventListener('_t', null, opt);
        return teste ? { passive: true } : false;
      }, false));

    brancherMenu();
    brancherGalerie();
    auDefilement();   // page déjà défilée au chargement (retour arrière)
  }

  /* Petite façade publique : uniquement ce dont la politique de
     confidentialité a besoin pour proposer le droit d'opposition exigé par
     la CNIL, plus un envoi manuel si une page a un besoin ponctuel. */
  window.LouisetteMesure = {
    envoyer: function (nom, props) { sur(function () { envoyer(nom, props); }); },
    actif: function () { return actif; },
    seDesinscrire: function () {
      return sur(function () {
        window.localStorage.setItem('plausible_ignore', 'true');
        renoncer();
        return true;
      }, false);
    },
    seReinscrire: function () {
      return sur(function () {
        window.localStorage.removeItem('plausible_ignore');
        return true;
      }, false);
    }
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () { sur(demarrer); });
  } else {
    sur(demarrer);
  }
})();
