/* Menu mobile — une seule source pour toutes les pages.

   Le tiroir se declare role="dialog" aria-modal="true" : il doit donc retenir
   le clavier tant qu il est ouvert, sinon la tabulation sort vers des liens
   masques derriere lui et l annonce du lecteur d ecran est mensongere.
   Constate le 9 septembre : aucun piege de focus, aucun retour du focus. */
(function(){
  var b=document.getElementById('burger'),t=document.getElementById('tiroir'),x=document.getElementById('tiroirX');
  if(!b||!t)return;
  SEL='a[href],button:not([disabled]),[tabindex="0"]';
  function focalisables(){
    return [].slice.call(t.querySelectorAll(SEL)).filter(function(e){
      return e.offsetWidth||e.offsetHeight||e.getClientRects().length;});
  }
  function ouvrir(){
    t.classList.add('open');
    b.setAttribute('aria-expanded','true');
    b.setAttribute('aria-label','Fermer le menu');
    document.body.style.overflow='hidden';
    var f=focalisables(); if(f.length)f[0].focus();
  }
  function fermer(){
    t.classList.remove('open');
    b.setAttribute('aria-expanded','false');
    b.setAttribute('aria-label','Ouvrir le menu');
    document.body.style.overflow='';
    b.focus();
  }
  b.addEventListener('click',ouvrir);
  if(x)x.addEventListener('click',fermer);
  t.addEventListener('click',function(e){if(e.target.tagName==='A')fermer();});
  document.addEventListener('keydown',function(e){
    if(!t.classList.contains('open'))return;
    if(e.key==='Escape'){fermer();return;}
    if(e.key!=='Tab')return;
    var f=focalisables(); if(!f.length)return;
    var premier=f[0],dernier=f[f.length-1];
    if(e.shiftKey&&document.activeElement===premier){e.preventDefault();dernier.focus();}
    else if(!e.shiftKey&&document.activeElement===dernier){e.preventDefault();premier.focus();}
    else if(t.contains(document.activeElement)===false){e.preventDefault();premier.focus();}
  });
})();
