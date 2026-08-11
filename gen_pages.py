#!/usr/bin/env python3
# 型番ページ Phase 2 — 公開ページ自動生成（AI費用ゼロ）
# 公開カタログ(catalog ビュー・publishable key)だけを読む。JC痕跡・ユーロ・価格は一切出さない。
# 生成物: p/<slug>.html（型番ごと）＋ sitemap.xml。在庫から消えた型番の p/*.html は削除。
import os, re, json, html, datetime
import urllib.request, urllib.parse, urllib.error

SB_URL = os.environ.get("SB_URL", "https://vprtbkkqqdfidzvfwhzo.supabase.co")
SB_KEY = os.environ.get("SB_KEY", "sb_publishable_qVTKT3ZOy8RL-5k2M94fVw_iOowUGWy")
SITE   = "https://geoport.co.jp"
RELAY  = SB_URL + "/functions/v1/quote-relay"
OUT    = "p"
PAGE   = 1000

CSS = """:root{--black:#0b0d10;--dark:#11151a;--panel:#161b22;--border:#262e39;--accent:#e8a020;--accent2:#f4c552;--text:#e6edf3;--muted:#8a94a0;--green:#2ea043;--line:#0d1014}
*{margin:0;padding:0;box-sizing:border-box}
body{background:var(--black);color:var(--text);font-family:'Noto Sans JP',sans-serif;font-size:14px;line-height:1.7;-webkit-font-smoothing:antialiased}
header{background:linear-gradient(180deg,var(--dark),var(--black));border-bottom:1px solid var(--border);position:sticky;top:0;z-index:30}
.bar{max-width:900px;margin:0 auto;padding:14px 20px;display:flex;align-items:center;gap:18px}
.logo{font-family:'Barlow Condensed',sans-serif;font-weight:700;font-size:24px;letter-spacing:2px;display:flex;align-items:center;gap:9px;text-decoration:none;color:inherit}
.logo b{color:var(--accent)}.logo .dot{width:9px;height:9px;background:var(--accent);transform:rotate(45deg)}
.back{margin-left:auto;color:var(--muted);text-decoration:none;font-size:12px}
.back:hover{color:var(--accent)}
.wrap{max-width:900px;margin:0 auto;padding:20px}
.crumb{font-size:12px;color:var(--muted);margin-bottom:16px}
.crumb a{color:var(--muted);text-decoration:none}.crumb a:hover{color:var(--accent)}
.top{display:grid;grid-template-columns:280px 1fr;gap:24px;align-items:start}
@media(max-width:640px){.top{grid-template-columns:1fr}}
.photo{background:repeating-linear-gradient(45deg,#10151b,#10151b 10px,#0d1116 10px,#0d1116 20px);border:1px solid var(--border);border-radius:12px;height:230px;display:flex;flex-direction:column;align-items:center;justify-content:center;color:#4a5563;gap:8px}
.photo .pn{font-family:'Barlow',sans-serif;font-weight:600;font-size:18px;color:#5b6774;word-break:break-all;text-align:center;padding:0 14px}
.photo .note{font-size:11px;color:var(--muted)}
.brand{font-size:12px;color:var(--accent);letter-spacing:1.5px;font-weight:700;text-transform:uppercase}
h1{font-family:'Barlow',sans-serif;font-size:30px;font-weight:600;word-break:break-all;margin:6px 0 4px}
.series{color:var(--muted);font-size:13px;margin-bottom:14px}
.badge{display:inline-flex;align-items:center;gap:6px;background:rgba(46,160,67,.15);color:var(--green);border:1px solid rgba(46,160,67,.4);font-size:12px;font-weight:700;padding:5px 11px;border-radius:6px}
.spec{width:100%;border-collapse:collapse;margin:16px 0}
.spec th,.spec td{text-align:left;padding:9px 12px;border:1px solid var(--border);font-size:13px;vertical-align:top}
.spec th{background:var(--dark);color:var(--muted);font-weight:500;white-space:nowrap;width:34%}
.cta{display:inline-block;background:var(--accent);color:#1a1205;font-weight:700;font-size:15px;padding:13px 26px;border-radius:9px;text-decoration:none;margin-top:6px;border:none;cursor:pointer;font-family:inherit}
.cta:hover{background:var(--accent2)}
.overlay{position:fixed;inset:0;background:rgba(3,5,8,.78);display:none;align-items:flex-start;justify-content:center;z-index:50;padding:24px 16px;overflow-y:auto}
.overlay.show{display:flex}
.modal{background:var(--panel);border:1px solid var(--border);border-radius:14px;width:100%;max-width:460px;margin:auto}
.mhead{padding:18px 20px;border-bottom:1px solid var(--border);display:flex;justify-content:space-between;align-items:flex-start}
.mhead h3{font-family:'Barlow Condensed',sans-serif;font-size:20px;letter-spacing:1px}
.mhead .x{background:none;border:none;color:var(--muted);font-size:22px;cursor:pointer}
.mhead .sub{font-size:12px;color:var(--accent);margin-top:3px;font-family:'Barlow',sans-serif;word-break:break-all}
.mbody{padding:18px 20px;display:flex;flex-direction:column;gap:13px}
.field label{display:block;font-size:12px;color:var(--muted);margin-bottom:5px}
.field .req{color:#e5736b}
.field input,.field textarea{width:100%;background:var(--line);border:1px solid var(--border);color:var(--text);padding:10px 12px;border-radius:8px;font-family:inherit;font-size:14px}
.field input:focus,.field textarea:focus{outline:none;border-color:var(--accent)}
.row2{display:flex;gap:11px}.row2 .field{flex:1}
.mnote{font-size:11px;color:var(--muted);background:var(--line);border-radius:8px;padding:10px 12px;line-height:1.5}
.merr{font-size:12px;color:#e5736b;display:none}
.mfoot{padding:0 20px 20px}
.mbtn{width:100%;background:var(--accent);color:#1a1205;font-weight:700;font-size:15px;padding:13px;border:none;border-radius:9px;cursor:pointer;font-family:inherit}
.mbtn:disabled{opacity:.6;cursor:not-allowed}
.sent{text-align:center;padding:30px 20px;color:var(--green);display:none}.sent.show{display:block}
.note2{font-size:12px;color:var(--muted);margin-top:10px;line-height:1.6}
.sec{margin-top:30px}
.sec h2{font-family:'Barlow Condensed',sans-serif;font-size:18px;letter-spacing:1px;color:var(--text);border-left:3px solid var(--accent);padding-left:10px;margin-bottom:10px}
.sec p{color:#c7ced6;margin-bottom:10px}
.disc{background:rgba(232,160,32,.06);border:1px solid rgba(232,160,32,.25);border-radius:10px;padding:12px 15px;font-size:12px;color:var(--muted);margin-top:26px}
footer{border-top:1px solid var(--border);padding:22px 20px;text-align:center;color:var(--muted);font-size:11px;line-height:1.9;margin-top:40px}
footer a{color:var(--accent);text-decoration:underline}"""

def fetch_catalog():
    # description_ja がまだ公開ビューに無い場合(view更新前)は、その列を外して取得する
    cols = "article,brand,family,condition,stock,description_ja"
    try:
        return _fetch(cols)
    except urllib.error.HTTPError as ex:
        if ex.code == 400 and "description_ja" in cols:
            print("note: description_ja 列が catalog に無いため、説明なしで生成します（view更新前）")
            return _fetch("article,brand,family,condition,stock")
        raise

def _fetch(cols):
    rows, off = [], 0
    while True:
        url = (SB_URL + "/rest/v1/catalog?select=" + cols +
               "&order=article&limit=%d&offset=%d&apikey=%s" % (PAGE, off, SB_KEY))
        req = urllib.request.Request(url, headers={"apikey": SB_KEY})
        with urllib.request.urlopen(req, timeout=60) as r:
            batch = json.load(r)
        rows += batch
        if len(batch) < PAGE:
            break
        off += PAGE
    return rows

def slugify(article):
    s = re.sub(r"[^a-z0-9._-]+", "-", (article or "").lower()).strip("-")
    return s or "item"

def e(s):
    return html.escape("" if s is None else str(s), quote=True)

def _clean_field(v):
    # データ上の "None"/"N/A"/空 は「値なし」として扱う
    s = (v or "").strip()
    return "" if s.lower() in ("none", "n/a", "null", "-") else s

# Phase 1 生成物には2種類のノイズがある：
#  (1) 末尾の内部注記「（※…）」…本体の説明は有効。注記だけ外す（約15%）。
#  (2) 丸ごと断り文「申し訳ございませんが…作成できません」…本体が無い（約1%）。→定型文へ。
_NOTE = re.compile(r"[（(]\s*※[^）)]*[）)]")   # 内部注記「（※…）」（位置を問わず）
_REFUSAL = ("申し訳", "作成することができ", "作成できま", "作成できかね",
            "判読することができ", "情報が限られ", "提供いただいた情報では")

_HEDGE_KEYS = ("不明", "限られ", "限定的", "情報がな", "情報が少な", "判読", "推測", "断片")

def _is_hedge(sentence):
    return "控え" in sentence and any(k in sentence for k in _HEDGE_KEYS)

def clean_desc(text):
    t = (text or "").strip()
    t = _NOTE.sub("", t)              # 「（※…）」注記を除去（末尾でも文中でも）
    t = re.sub(r"\s+", " ", t)
    # 末尾の「…不明なため、詳細は控えています。」型の逃げ口上を落とす
    parts = re.split(r"(?<=。)", t)
    while parts:
        last = parts[-1].strip()
        if last == "" or _is_hedge(last):
            parts.pop()
        else:
            break
    t = "".join(parts)
    t = t.replace("、。", "。").replace(" 。", "。").replace(" 、", "、")
    t = re.sub(r"[、\s]+$", "", t).strip()   # 末尾の読点/空白を落とす
    return t

def is_refusal(text):
    return any(m in (text or "") for m in _REFUSAL)

def desc_paras(text):
    text = (text or "").strip()
    if not text:
        return ""
    parts = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    return "\n  ".join("<p>%s</p>" % e(p.replace("\n", " ")) for p in parts)

def render(row, slug):
    art   = row.get("article") or ""
    brand = _clean_field(row.get("brand"))
    fam   = _clean_field(row.get("family"))
    dj    = clean_desc(row.get("description_ja"))   # 末尾注記を外す
    if is_refusal(dj):                              # 丸ごと断り文なら定型文へ
        dj = ""
    stock = row.get("stock")
    badge_txt = f"在庫 {stock} 点（新古品）" if isinstance(stock, int) and stock > 0 else "在庫あり（新古品）"
    sbkey_json = json.dumps(SB_KEY)
    relay_json = json.dumps(RELAY)
    art_json   = json.dumps(art)
    canon = f"{SITE}/{OUT}/{slug}.html"
    title = f"{art} {brand}｜GEOPORT" if brand else f"{art}｜GEOPORT"
    fam_paren = f"（{fam}）" if fam else ""
    metad = (f"{brand}{fam_paren}{art} の在庫・お見積り。新古品、初期不良は納品後1年以内保証。"
             f"型番から在庫確認・お見積りをご依頼いただけます。｜GEOPORT")
    ogt = f"{art} {brand}｜GEOPORT" if brand else title
    ogd = f"{brand}{fam_paren}{art} の在庫・お見積り。新古品・初期不良1年保証。"
    ld_desc = dj[:160] if dj else (" ".join(x for x in (brand, fam) if x) + " の新古品。").strip()
    ld = {"@context": "https://schema.org", "@type": "Product", "name": art, "sku": art,
          "mpn": art, "brand": {"@type": "Brand", "name": brand}, "description": ld_desc}
    if fam:
        ld["category"] = fam
    crumb = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "製品カタログ", "item": SITE + "/"},
        {"@type": "ListItem", "position": 2, "name": art, "item": canon}]}
    about = desc_paras(dj) or (f"<p>{e(art)} の新古品（未使用在庫品）です。詳しい仕様・在庫状況は、"
                               f"下のボタンよりお問い合わせください。</p>")
    series_html = f'<div class="series">{e(fam)} シリーズ</div>' if fam else ""
    brand_html  = f'<div class="brand">{e(brand)}</div>' if brand else ""
    brand_trow  = f"<tr><th>メーカー</th><td>{e(brand)}</td></tr>" if brand else ""
    fam_row     = f"<tr><th>シリーズ</th><td>{e(fam)}</td></tr>" if fam else ""
    return f"""<!DOCTYPE html>
<html lang="ja"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{e(title)}</title>
<meta name="description" content="{e(metad)}">
<link rel="canonical" href="{e(canon)}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="GEOPORT">
<meta property="og:locale" content="ja_JP">
<meta property="og:title" content="{e(ogt)}">
<meta property="og:description" content="{e(ogd)}">
<meta property="og:url" content="{e(canon)}">
<meta name="twitter:card" content="summary">
<script type="application/ld+json">
{json.dumps(ld, ensure_ascii=False)}
</script>
<script type="application/ld+json">
{json.dumps(crumb, ensure_ascii=False)}
</script>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@300;400;500;700&family=Barlow+Condensed:wght@500;600;700&family=Barlow:wght@400;500;600&display=swap" rel="stylesheet">
<style>
{CSS}
</style></head><body>
<header><div class="bar">
<a class="logo" href="../index.html"><span class="dot"></span>GEO<b>PORT</b></a>
<a class="back" href="../index.html">← 製品カタログへ戻る</a>
</div></header>

<div class="wrap">
<div class="crumb"><a href="../index.html">製品カタログ</a> ／ {e(art)}</div>

<div class="top">
  <div class="photo">
    <span class="pn">{e(art)}</span>
    <span class="note">製品写真は準備中です</span>
  </div>
  <div>
    {brand_html}
    <h1>{e(art)}</h1>
    {series_html}
    <span class="badge">● {e(badge_txt)}</span>
    <table class="spec">
      <tr><th>型番</th><td>{e(art)}</td></tr>
      {brand_trow}
      {fam_row}
      <tr><th>品質区分</th><td>新古品（未使用在庫品）</td></tr>
      <tr><th>納期</th><td>ご入金確認後、約10〜14日でお届け（輸送状況により前後する場合がございます）</td></tr>
      <tr><th>保証</th><td>製品本来の欠陥による初期不良に限り、納品後1年以内を保証</td></tr>
      <tr><th>価格</th><td>お見積り（お問い合わせフォームより個別にご提示）</td></tr>
    </table>
    <button class="cta" type="button" onclick="openQuote()">この製品の見積を確認する</button>
    <div class="note2">価格は掲載しておりません。上のボタンからお問い合わせいただくと、担当より在庫状況・お見積り金額・納期を折り返しご連絡いたします（法人・事業者様向け）。</div>
  </div>
</div>

<div class="sec">
  <h2>製品について</h2>
  {about}
</div>

<div class="disc">※ 当社は各メーカーの正規代理店ではありません。取り扱う製品はメーカー保証の対象外となりますが、当社保証規定に基づき対応いたします。掲載のメーカー名および商標は各権利者に帰属します。詳細は<a href="../guide.html#warranty" style="color:var(--accent)">サービス案内・保証規定</a>をご確認ください。</div>
</div>

<footer>GEOPORT株式会社 — FA機器 / 登録番号 T1290001098731<br>
掲載中の在庫品を、通常10〜14日でお届けします。価格・お見積りはお問い合わせください。<br>
<a href="../guide.html">サービス案内・保証規定</a> ｜ <a href="../company.html">会社情報</a></footer>

<div class="overlay" id="ov"><div class="modal">
<div class="mhead"><div><h3>見積・在庫確認</h3><div class="sub">{e(art)}</div></div><button class="x" type="button" onclick="closeQuote()">&times;</button></div>
<div class="mbody" id="mform">
<div class="mnote">在庫状況・お見積り（価格）・納期を、担当より折り返しご連絡いたします。お支払いは銀行振込にて承ります。</div>
<div class="field"><label>数量 <span class="req">*</span></label><input id="f-qty" type="number" value="1" min="1"></div>
<div class="row2"><div class="field"><label>会社名 <span class="req">*</span></label><input id="f-co" type="text"></div>
<div class="field"><label>ご担当者名 <span class="req">*</span></label><input id="f-name" type="text"></div></div>
<div class="field"><label>メールアドレス <span class="req">*</span></label><input id="f-mail" type="email"></div>
<div class="field"><label>ご要望・備考（任意）</label><textarea id="f-note" rows="2"></textarea></div>
<div class="merr" id="m-err"></div></div>
<div class="mfoot" id="mfoot"><button class="mbtn" id="m-sub" type="button" onclick="submitQuote()">この内容で問い合わせる</button></div>
<div class="sent" id="m-sent"><div style="font-weight:600;color:var(--text)">送信しました</div><div style="color:var(--muted);font-size:13px;margin-top:6px">担当より折り返しご連絡いたします。</div></div>
</div></div>

<script>
var SB_KEY={sbkey_json};
var RELAY={relay_json};
var ART={art_json};
function $(i){{return document.getElementById(i);}}
function openQuote(){{var e=$("m-err");if(e)e.style.display="none";var f=$("mform");if(f)f.style.display="flex";var ft=$("mfoot");if(ft)ft.style.display="block";var s=$("m-sent");if(s)s.classList.remove("show");var b=$("m-sub");if(b){{b.disabled=false;b.textContent="この内容で問い合わせる";}}["f-qty","f-co","f-name","f-mail","f-note"].forEach(function(id){{var el=$(id);if(el)el.value=(id==="f-qty"?"1":"");}});var ov=$("ov");if(ov)ov.classList.add("show");}}
function closeQuote(){{var ov=$("ov");if(ov)ov.classList.remove("show");}}
function submitQuote(){{
  var qty=($("f-qty")||{{}}).value;qty=qty?qty.trim():"";
  var co=($("f-co")||{{}}).value;co=co?co.trim():"";
  var name=($("f-name")||{{}}).value;name=name?name.trim():"";
  var mail=($("f-mail")||{{}}).value;mail=mail?mail.trim():"";
  var note=($("f-note")||{{}}).value;note=note?note.trim():"";
  var err=$("m-err");
  if(!co||!name||!mail||!qty){{if(err){{err.textContent="会社名・ご担当者名・メールアドレス・数量は必須です。";err.style.display="block";}}return;}}
  if(mail.indexOf("@")<0){{if(err){{err.textContent="メールアドレスの形式をご確認ください。";err.style.display="block";}}return;}}
  if(err)err.style.display="none";
  var b=$("m-sub");if(b){{b.disabled=true;b.textContent="送信しています…";}}
  var payload={{article:ART,qty:qty,company:co,person:name,email:mail,note:note}};
  fetch(RELAY,{{method:"POST",headers:{{"Content-Type":"application/json","Authorization":"Bearer "+SB_KEY,"apikey":SB_KEY}},body:JSON.stringify(payload)}})
  .then(function(r){{return r.json();}}).then(function(j){{
    if(j.success){{var f=$("mform");if(f)f.style.display="none";var ft=$("mfoot");if(ft)ft.style.display="none";var s=$("m-sent");if(s)s.classList.add("show");}}
    else{{throw new Error(j.error||"送信に失敗しました");}}
  }}).catch(function(e){{if(err){{err.textContent="送信に失敗しました。時間をおいて再度お試しください。";err.style.display="block";}}if(b){{b.disabled=false;b.textContent="この内容で問い合わせる";}}}});
}}
(function(){{var ov=$("ov");if(ov)ov.addEventListener("click",function(e){{if(e.target.id==="ov")closeQuote();}});}})();
</script>
<!-- Cloudflare Web Analytics --><script defer src="https://static.cloudflareinsights.com/beacon.min.js" data-cf-beacon='{{"token": "1f55d2e30afe4d8a806863540932191d"}}'></script><!-- End Cloudflare Web Analytics -->
</body></html>
"""

def write_sitemap(slugs, lastmod):
    base = [("/", "daily", "1.0"), ("/company.html", "monthly", "0.5"),
            ("/guide.html", "monthly", "0.5")]
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, cf, pr in base:
        out.append(f'  <url><loc>{SITE}{loc}</loc><lastmod>{lastmod}</lastmod>'
                   f'<changefreq>{cf}</changefreq><priority>{pr}</priority></url>')
    for slug in slugs:
        out.append(f'  <url><loc>{SITE}/{OUT}/{slug}.html</loc><lastmod>{lastmod}</lastmod>'
                   f'<changefreq>weekly</changefreq><priority>0.6</priority></url>')
    out.append('</urlset>')
    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")

def main():
    lastmod = os.environ.get("LASTMOD") or datetime.date.today().isoformat()
    rows = fetch_catalog()
    print("catalog rows: %d" % len(rows))
    os.makedirs(OUT, exist_ok=True)
    seen, slugs, wrote, no_desc = {}, [], 0, 0
    for row in rows:
        art = row.get("article") or ""
        if not art:
            continue
        slug = slugify(art)
        if slug in seen:
            n = 2
            while f"{slug}-{n}" in seen:
                n += 1
            slug = f"{slug}-{n}"
        seen[slug] = art
        slugs.append(slug)
        _dj = clean_desc(row.get("description_ja"))
        if not _dj or is_refusal(_dj):
            no_desc += 1
        with open(os.path.join(OUT, slug + ".html"), "w", encoding="utf-8") as f:
            f.write(render(row, slug))
        wrote += 1
    keep = set(s + ".html" for s in slugs)
    removed = 0
    if os.path.isdir(OUT):
        for fn in os.listdir(OUT):
            if fn.endswith(".html") and fn not in keep:
                os.remove(os.path.join(OUT, fn))
                removed += 1
    slugs.sort()
    write_sitemap(slugs, lastmod)
    print("wrote: %d / removed(stale): %d / no description_ja(fallback used): %d"
          % (wrote, removed, no_desc))

if __name__ == "__main__":
    main()
