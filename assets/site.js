/* Menu mobile — une seule source pour toutes les pages. */
(function(){
  var b=document.getElementById('burger'),t=document.getElementById('tiroir'),x=document.getElementById('tiroirX');
  if(!b||!t)return;
  function ouvrir(){t.classList.add('open');b.setAttribute('aria-expanded','true');document.body.style.overflow='hidden';}
  function fermer(){t.classList.remove('open');b.setAttribute('aria-expanded','false');document.body.style.overflow='';}
  b.addEventListener('click',ouvrir);
  if(x)x.addEventListener('click',fermer);
  t.addEventListener('click',function(e){if(e.target.tagName==='A')fermer();});
  document.addEventListener('keydown',function(e){if(e.key==='Escape'&&t.classList.contains('open'))fermer();});
})();
