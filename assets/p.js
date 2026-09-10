function $(i){return document.getElementById(i);}
/* ---- 写真の切替・虫眼鏡・全画面拡大 ---- */
var CUR=0;
function showShot(b,i){CUR=i;var m=$("mainshot");if(m&&SHOTS[i])m.src=SHOTS[i];
  var t=document.querySelectorAll(".th");for(var k=0;k<t.length;k++)t[k].classList.remove("on");
  if(b)b.classList.add("on");}
function lbToggle(ev){if(ev)ev.stopPropagation();var im=$("lbimg");if(im)im.classList.toggle("full");lbCount();}
function lbCount(){var im=$("lbimg"),tip="";
  /* 画面いっぱいでも実寸に届かないときだけ「原寸で見る」を案内する（PCでは元々原寸のことが多い） */
  if(im&&im.naturalWidth){
    if(im.classList.contains("full")) tip="画像を押すと全体表示";
    else if(im.naturalWidth>im.getBoundingClientRect().width+2) tip="画像を押すと原寸";
  }
  var head=(SHOTS.length>1?((CUR+1)+" / "+SHOTS.length):"");
  var c=$("lbcnt");if(c)c.textContent=head+((head&&tip)?"　・　":"")+tip;
  var n=document.querySelectorAll(".lb .nav");
  for(var i=0;i<n.length;i++)n[i].style.display=SHOTS.length>1?"block":"none";}
function openLB(){if(!SHOTS.length)return;var im=$("lbimg");if(im){im.classList.remove("full");im.src=SHOTS[CUR];}
  var l=$("lb");if(l)l.classList.add("show");lbCount();}
function closeLB(){var l=$("lb");if(l)l.classList.remove("show");}
function lbBg(ev){if(ev.target&&ev.target.id==="lb")closeLB();}
function stepLB(d){if(SHOTS.length<2)return;CUR=(CUR+d+SHOTS.length)%SHOTS.length;
  var im=$("lbimg");if(im){im.classList.remove("full");im.src=SHOTS[CUR];}
  var m=$("mainshot");if(m)m.src=SHOTS[CUR];
  var t=document.querySelectorAll(".th");
  for(var i=0;i<t.length;i++){if(i===CUR)t[i].classList.add("on");else t[i].classList.remove("on");}
  lbCount();}
document.addEventListener("keydown",function(ev){
  var l=$("lb");if(!l||!l.classList.contains("show"))return;
  if(ev.key==="Escape")closeLB();
  else if(ev.key==="ArrowRight")stepLB(1);
  else if(ev.key==="ArrowLeft")stepLB(-1);});
/* 虫眼鏡：右下のボタンでON/OFF。写真の枠ごと約2.3倍（実サイズ÷表示サイズ）に拡大する */
var MAGON=false;
function hideMag(){var z=$("inzoom"),b=$("photobox");if(z)z.style.display="none";if(b)b.classList.remove("magon");}
function toggleMag(){MAGON=!MAGON;var b=$("magbtn");if(b)b.classList.toggle("on",MAGON);if(!MAGON)hideMag();}
function photoClick(){if(!MAGON)openLB();}
(function(){
  if(!window.matchMedia||!matchMedia("(hover:hover)").matches)return;
  var box=$("photobox"),img=$("mainshot");if(!box||!img)return;
  box.addEventListener("mousemove",function(ev){
    if(!MAGON||!img.naturalWidth)return;
    var r=img.getBoundingClientRect(),br=box.getBoundingClientRect();
    if(ev.clientX<r.left||ev.clientX>r.right||ev.clientY<r.top||ev.clientY>r.bottom){hideMag();return;}
    var zx=img.naturalWidth/r.width,zy=img.naturalHeight/r.height;
    var x=ev.clientX-r.left,y=ev.clientY-r.top;
    var z=$("inzoom");z.style.display="block";box.classList.add("magon");
    z.style.backgroundImage='url("'+img.src+'")';
    z.style.backgroundSize=img.naturalWidth+"px "+img.naturalHeight+"px";
    z.style.backgroundPosition=(-(x*zx-br.width/2))+"px "+(-(y*zy-br.height/2))+"px";
  });
  box.addEventListener("mouseleave",hideMag);
})();
function openQuote(){var e=$("m-err");if(e)e.style.display="none";var f=$("mform");if(f)f.style.display="flex";var ft=$("mfoot");if(ft)ft.style.display="block";var s=$("m-sent");if(s)s.classList.remove("show");var b=$("m-sub");if(b){b.disabled=false;b.textContent="この内容で問い合わせる";}["f-qty","f-co","f-name","f-mail","f-note","f-pref"].forEach(function(id){var el=$(id);if(el)el.value=(id==="f-qty"?"1":"");});fillPrefs();var ov=$("ov");if(ov)ov.classList.add("show");}
function closeQuote(){var ov=$("ov");if(ov)ov.classList.remove("show");}
// お届け先の都道府県（国内送料の計算に使う）
var PREFS=["北海道","青森県","岩手県","宮城県","秋田県","山形県","福島県","茨城県","栃木県","群馬県","埼玉県","千葉県","東京都","神奈川県","新潟県","富山県","石川県","福井県","山梨県","長野県","岐阜県","静岡県","愛知県","三重県","滋賀県","京都府","大阪府","兵庫県","奈良県","和歌山県","鳥取県","島根県","岡山県","広島県","山口県","徳島県","香川県","愛媛県","高知県","福岡県","佐賀県","長崎県","熊本県","大分県","宮崎県","鹿児島県","沖縄県"];
function fillPrefs(){var el=$("f-pref");if(!el||el.options.length>1)return;for(var i=0;i<PREFS.length;i++){var o=document.createElement("option");o.value=PREFS[i];o.textContent=PREFS[i];el.appendChild(o);}}
function submitQuote(){
  var qty=($("f-qty")||{}).value;qty=qty?qty.trim():"";
  var co=($("f-co")||{}).value;co=co?co.trim():"";
  var name=($("f-name")||{}).value;name=name?name.trim():"";
  var mail=($("f-mail")||{}).value;mail=mail?mail.trim():"";
  var note=($("f-note")||{}).value;note=note?note.trim():"";
  var pref=($("f-pref")||{}).value;pref=pref?pref.trim():"";
  var err=$("m-err");
  if(!co||!name||!mail||!qty||!pref){if(err){err.textContent="会社名・ご担当者名・メールアドレス・数量・お届け先の都道府県は必須です。";err.style.display="block";}return;}
  if(mail.indexOf("@")<0){if(err){err.textContent="メールアドレスの形式をご確認ください。";err.style.display="block";}return;}
  if(err)err.style.display="none";
  var b=$("m-sub");if(b){b.disabled=true;b.textContent="送信しています…";}
  var web=($("f-web")||{}).value||"";  /* 罠の欄（人には見えない・空が正常）*/
  var payload={article:ART,qty:qty,company:co,person:name,email:mail,note:note,pref:pref,website:web};
  fetch(RELAY,{method:"POST",headers:{"Content-Type":"application/json","Authorization":"Bearer "+SB_KEY,"apikey":SB_KEY},body:JSON.stringify(payload)})
  .then(function(r){return r.json();}).then(function(j){
    if(j.success){var f=$("mform");if(f)f.style.display="none";var ft=$("mfoot");if(ft)ft.style.display="none";var s=$("m-sent");if(s)s.classList.add("show");}
    else{throw new Error(j.error||"送信に失敗しました");}
  }).catch(function(e){if(err){err.textContent="送信に失敗しました。時間をおいて再度お試しください。";err.style.display="block";}if(b){b.disabled=false;b.textContent="この内容で問い合わせる";}});
}
(function(){var ov=$("ov");if(ov)ov.addEventListener("click",function(e){if(e.target.id==="ov")closeQuote();});})();