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
PAGE   = 1000          # REST取得のページサイズ（PostgRESTの上限1000）
LIST   = "list"        # 一覧（目次）ページの出力先
LIST_PER = 150         # 一覧1ページあたりの型番数
RELATED_N = 12         # 型番ページに出す「関連製品」の数

CSS = """:root{--black:#f5f7fa;--dark:#eef2f7;--panel:#ffffff;--border:#e2e8f0;--accent:#1c5fb0;--accent2:#2b74cf;--text:#1a2634;--muted:#5b6b7d;--green:#15803d;--line:#f1f4f8}
*{margin:0;padding:0;box-sizing:border-box}
body{background:var(--black);color:var(--text);font-family:'Noto Sans JP',sans-serif;font-size:14px;line-height:1.7;-webkit-font-smoothing:antialiased}
header{background:linear-gradient(180deg,var(--dark),var(--black));border-bottom:1px solid var(--border);position:sticky;top:0;z-index:30}
.bar{max-width:900px;margin:0 auto;padding:14px 20px;display:flex;align-items:center;gap:18px}
.logo{font-family:'Barlow Condensed',sans-serif;font-weight:700;font-size:24px;letter-spacing:2px;display:flex;align-items:center;gap:9px;text-decoration:none;color:inherit}
.logo b{color:var(--accent)}.logo .dot{width:9px;height:9px;background:var(--accent);transform:rotate(45deg)}
.back{margin-left:auto;color:var(--muted);text-decoration:none;font-size:12px;white-space:nowrap}
.back:hover{color:var(--accent)}
/* ヘッダー右端の案内ボタン（アイコン＋枠線）。スマホは幅が足りないので出さない */
.hnav{display:flex;margin-left:auto;gap:9px;align-items:center}
.hnav a{display:inline-flex;align-items:center;gap:6px;white-space:nowrap;text-decoration:none;
  color:#dbe7f5;font-size:12px;border:1px solid rgba(255,255,255,.35);border-radius:18px;
  padding:6px 14px 6px 11px;transition:.15s}
.hnav a:hover{background:rgba(255,255,255,.14);border-color:#7fb0e8;color:#fff}
.hnav svg{fill:none;stroke:currentColor;stroke-width:2}
@media(max-width:640px){.hnav{display:none}}
.wrap{max-width:900px;margin:0 auto;padding:20px}
.crumb{font-size:12px;color:var(--muted);margin-bottom:16px;display:flex;justify-content:space-between;align-items:baseline;gap:14px;flex-wrap:wrap}
.crumb a{color:var(--muted);text-decoration:none}.crumb a:hover{color:var(--accent)}
.top{display:grid;grid-template-columns:380px 1fr;gap:28px;align-items:stretch}
/* 写真の列を伸縮させ、右の仕様表と上端・下端を揃える（デザインの安定感） */
.gal{display:flex;flex-direction:column}
.gal .photo{flex:1 1 auto;aspect-ratio:auto;min-height:360px}
@media(max-width:720px){.top{grid-template-columns:1fr}
  .gal .photo{flex:0 0 auto;aspect-ratio:1/1;min-height:0}}
.photo{border:1px solid var(--border);border-radius:12px;background:#fff;aspect-ratio:1/1;display:flex;align-items:center;justify-content:center;padding:14px;overflow:hidden;position:relative}
.photo img{max-width:100%;max-height:100%;object-fit:contain}
.photo.zoomable img{cursor:zoom-in}
/* 虫眼鏡（マウスのある端末だけ）。写真の上でカーソルに追従して約2.3倍に拡大する */
.inzoom{display:none;position:absolute;inset:0;background-color:#fff;background-repeat:no-repeat;pointer-events:none;z-index:5;border-radius:11px}
.photo.magon img{opacity:0}
/* 写真の枠の中・右下に置く記号ボタン（虫眼鏡 / 全画面） */
.pctl{position:absolute;right:9px;bottom:9px;display:flex;gap:6px;z-index:6}
.pctl button{width:34px;height:34px;display:flex;align-items:center;justify-content:center;background:rgba(255,255,255,.92);border:1px solid var(--border);border-radius:8px;cursor:pointer;padding:0;box-shadow:0 2px 8px rgba(15,47,92,.14);transition:.15s}
.pctl button:hover{background:#fff;border-color:var(--accent)}
.pctl button svg{stroke:var(--text);fill:none;stroke-width:2}
.pctl button:hover svg{stroke:var(--accent)}
.pctl button.on{background:var(--accent);border-color:var(--accent)}
.pctl button.on svg{stroke:#fff}
@media (hover:none){.pctl button.mag{display:none}}
/* 全画面拡大（PC・スマホ共通） */
.lb{position:fixed;inset:0;background:rgba(8,12,18,.93);display:none;z-index:60}
.lb.show{display:block}
/* 画像より枠が小さいときも端が切れないよう、スクロール枠＋margin:auto で中央寄せする */
.lbscroll{position:absolute;inset:0;overflow:auto;display:flex;-webkit-overflow-scrolling:touch}
.lb img{margin:auto;max-width:92vw;max-height:82vh;object-fit:contain;cursor:zoom-in}
.lb img.full{max-width:none;max-height:none;cursor:zoom-out}
.lb .x{position:fixed;top:12px;right:16px;background:none;border:none;color:#fff;font-size:30px;line-height:1;cursor:pointer;z-index:2}
.lb .nav{position:fixed;top:50%;transform:translateY(-50%);background:rgba(255,255,255,.15);border:none;color:#fff;font-size:24px;width:46px;height:62px;border-radius:9px;cursor:pointer;z-index:2}
.lb .nav:hover{background:rgba(255,255,255,.28)}
.lb .prev{left:12px}.lb .next{right:12px}
.lb .cnt{position:fixed;bottom:14px;left:0;right:0;text-align:center;color:#cdd9e8;font-size:12px;z-index:2}
.photo.ph{background:repeating-linear-gradient(45deg,#eef2f6,#eef2f6 10px,#e6ecf3 10px,#e6ecf3 20px);flex-direction:column;color:#aab6c4;gap:8px}
.photo .pn{font-family:'Barlow',sans-serif;font-weight:600;font-size:18px;color:#aab6c4;word-break:break-all;text-align:center;padding:0 14px}
.photo .note{font-size:11px;color:var(--muted)}
.thumbs{display:flex;gap:6px;margin-top:9px}
/* 枚数が多いときは自動で縮んで1段に収まる（6枚=56px / 7枚=約48px） */
.th{flex:0 1 56px;max-width:56px;min-width:30px;height:56px;border:1px solid var(--border);border-radius:8px;background:#fff;padding:3px;cursor:pointer;overflow:hidden;transition:.15s}
.th img{width:100%;height:100%;object-fit:contain;display:block}
.th:hover{border-color:var(--accent)}
.th.on{border-color:var(--accent);box-shadow:0 0 0 1px var(--accent)}
.brand{font-size:12px;color:var(--accent);letter-spacing:1.5px;font-weight:700;text-transform:uppercase}
h1{font-family:'Barlow',sans-serif;font-size:30px;font-weight:600;word-break:break-all;margin:6px 0 4px}
.series{color:var(--muted);font-size:13px;margin-bottom:14px}
.badge{display:inline-flex;align-items:center;gap:6px;background:rgba(21,128,61,.15);color:var(--green);border:1px solid rgba(21,128,61,.4);font-size:12px;font-weight:700;padding:5px 11px;border-radius:6px}
.spec{width:100%;border-collapse:collapse;margin:16px 0 0}
.spec th,.spec td{text-align:left;padding:9px 12px;border:1px solid var(--border);font-size:13px;vertical-align:top}
.spec th{background:var(--dark);color:var(--muted);font-weight:500;white-space:nowrap;width:34%}
.wlink{margin-left:14px;color:var(--accent);text-decoration:underline}
.cta{display:inline-block;background:var(--accent);color:#ffffff;font-weight:700;font-size:15px;padding:13px 26px;border-radius:9px;text-decoration:none;margin-top:6px;border:none;cursor:pointer;font-family:inherit}
.cta:hover{background:var(--accent2)}
.spec td .cta{margin:2px 0;font-size:14px;padding:11px 20px}
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
.field input,.field textarea,.field select{width:100%;background:var(--line);border:1px solid var(--border);color:var(--text);padding:10px 12px;border-radius:8px;font-family:inherit;font-size:14px}
.field input:focus,.field textarea:focus,.field select:focus{outline:none;border-color:var(--accent)}
/* プルダウンの見た目を他の入力欄に揃える（OS既定の枠を消して矢印を自前で描く） */
.field select{appearance:none;-webkit-appearance:none;line-height:1.4;cursor:pointer;padding-right:34px;background-image:url("data:image/svg+xml;charset=utf-8,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 12 8'%3E%3Cpath d='M1 1l5 5 5-5' fill='none' stroke='%235b6b7d' stroke-width='1.8' stroke-linecap='round'/%3E%3C/svg%3E");background-repeat:no-repeat;background-position:right 12px center;background-size:12px 8px}
.row2{display:flex;gap:11px}.row2 .field{flex:1}
.mnote{font-size:11px;color:var(--muted);background:var(--line);border-radius:8px;padding:10px 12px;line-height:1.5}
.merr{font-size:12px;color:#e5736b;display:none}
.mfoot{padding:0 20px 20px}
.mbtn{width:100%;background:var(--accent);color:#ffffff;font-weight:700;font-size:15px;padding:13px;border:none;border-radius:9px;cursor:pointer;font-family:inherit}
.mbtn:disabled{opacity:.6;cursor:not-allowed}
.sent{text-align:center;padding:30px 20px;color:var(--green);display:none}.sent.show{display:block}
.note2{font-size:12px;color:var(--muted);margin-top:10px;line-height:1.6}
.sec{margin-top:30px}
.sec h2{font-family:'Barlow Condensed',sans-serif;font-size:18px;letter-spacing:1px;color:var(--text);border-left:3px solid var(--accent);padding-left:10px;margin-bottom:10px}
.sec p{color:#33475c;margin-bottom:10px}
.specbox{margin-top:18px;border:1px solid var(--border);border-radius:10px;background:var(--panel);overflow:hidden}
.specbox>summary{list-style:none;cursor:pointer;padding:13px 16px;font-family:'Barlow Condensed',sans-serif;font-size:16px;letter-spacing:1px;color:var(--text);font-weight:600;display:flex;justify-content:space-between;align-items:center}
.specbox>summary::-webkit-details-marker{display:none}
.specbox>summary::after{content:"▾ 開く";color:var(--accent);font-size:12px;letter-spacing:0;font-family:'Noto Sans JP',sans-serif}
.specbox[open]>summary::after{content:"▴ 閉じる"}
.spec2{width:100%;border-collapse:collapse;margin:0}
.spec2 th,.spec2 td{text-align:left;padding:9px 16px;border-top:1px solid var(--border);font-size:13px;vertical-align:top}
.spec2 th{background:var(--dark);color:var(--muted);font-weight:500;white-space:nowrap;width:38%}
.disc{background:rgba(28,95,176,.06);border:1px solid rgba(28,95,176,.25);border-radius:10px;padding:12px 15px;font-size:12px;color:var(--muted);margin-top:26px}
footer{border-top:1px solid var(--border);padding:22px 20px;text-align:center;color:var(--muted);font-size:11px;line-height:1.9;margin-top:40px}
footer a{color:var(--accent);text-decoration:underline}
header{background:#0f2f5c;border-color:#123354}
.logo{color:#ffffff}.logo b{color:#7fb0e8}

.rel{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:9px;margin-top:4px}
.rel a{display:block;background:var(--panel);border:1px solid var(--border);border-radius:9px;padding:10px 13px;text-decoration:none;transition:.15s}
.rel a:hover{border-color:var(--accent);transform:translateY(-1px)}
.rel .a{font-family:'Barlow',sans-serif;font-weight:600;font-size:14px;color:var(--accent);word-break:break-all;display:block}
.rel .b{font-size:11px;color:var(--muted);display:block;margin-top:2px}
.relmore{font-size:12px;margin-top:11px}
.relmore a{color:var(--accent)}
.lgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:10px;margin-top:6px}
.lcard{display:block;background:var(--panel);border:1px solid var(--border);border-radius:10px;padding:13px 15px;text-decoration:none;transition:.15s}
.lcard:hover{border-color:var(--accent);transform:translateY(-1px)}
.lcard .a{font-family:'Barlow',sans-serif;font-weight:600;font-size:15px;color:var(--accent);word-break:break-all;display:block}
.lcard .b{font-size:11px;color:var(--muted);display:block;margin-top:3px}
.lcard .n{float:right;font-size:11px;color:var(--muted);font-weight:400}
.pager{display:flex;gap:7px;flex-wrap:wrap;align-items:center;margin-top:24px;font-size:13px}
.pager a,.pager span{display:inline-block;padding:7px 12px;border:1px solid var(--border);border-radius:8px;background:var(--panel);text-decoration:none;color:var(--accent)}
.pager .cur{background:var(--accent);color:#fff;border-color:var(--accent);font-weight:700}
.pager .gap{border:none;background:none;color:var(--muted);padding:7px 2px}
.lead{color:#33475c;margin-bottom:6px}"""

def fetch_catalog():
    # description_ja がまだ公開ビューに無い場合(view更新前)は、その列を外して取得する
    cols = "article,brand,family,condition,stock,weight_kg,image_url,description_ja,warranty_years"
    try:
        rows = _fetch(cols)
    except urllib.error.HTTPError as ex:
        if ex.code == 400 and "description_ja" in cols:
            print("note: description_ja 列が catalog に無いため、説明なしで生成します（view更新前）")
            rows = _fetch("article,brand,family,condition,stock,weight_kg,image_url,warranty_years")
        else:
            raise
    _attach_dims(rows)
    return rows

def _attach_dims(rows):
    # 仕様(寸法/HSコード/EAN)は別の公開ビュー product_dims から取得して型番で結合する。
    # ビューが未作成でも落ちないようにする（仕様なしで継続）。
    specs, off = {}, 0
    try:
        while True:
            url = (SB_URL + "/rest/v1/product_dims?select=article,dimensions,commodity_code,ean,image_count"
                   "&order=article&limit=%d&offset=%d&apikey=%s" % (PAGE, off, SB_KEY))
            req = urllib.request.Request(url, headers={"apikey": SB_KEY})
            with urllib.request.urlopen(req, timeout=60) as r:
                batch = json.load(r)
            for d in batch:
                specs[d.get("article")] = d
            if len(batch) < PAGE:
                break
            off += PAGE
        nd = sum(1 for d in specs.values() if d.get("dimensions"))
        print(f"仕様(寸法/HS/EAN): {len(specs)} 件を結合（寸法 {nd} 件）")
    except Exception as ex:
        print("note: product_dims ビュー未取得（仕様なしで継続）:", str(ex)[:100])
    for row in rows:
        d = specs.get(row.get("article")) or {}
        row["dimensions"]     = d.get("dimensions") or ""
        row["commodity_code"] = d.get("commodity_code") or ""
        row["ean"]            = d.get("ean") or ""
        try:
            row["image_count"] = int(d.get("image_count") or 0)
        except (TypeError, ValueError):
            row["image_count"] = 0

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

OTHER = "その他"

def gslug(name, fallback="other"):
    s = re.sub(r"[^a-z0-9._-]+", "-", (name or "").lower()).strip("-")
    return s or fallback

def build_index(rows):
    """メーカー → シリーズ → 型番 の目次を組み立てる（表示順とURLのslugをここで確定）。"""
    brands = {}
    for r in rows:
        if not (r.get("article") or ""):
            continue
        b = _clean_field(r.get("brand")) or OTHER
        f = _clean_field(r.get("family")) or OTHER
        brands.setdefault(b, {}).setdefault(f, []).append(r)
    used = set()
    def uniq(base):
        s, n = base, 2
        while s in used:
            s = "%s-%d" % (base, n)
            n += 1
        used.add(s)
        return s
    out = []
    for bname, fams in brands.items():
        bslug = uniq(gslug(bname))
        groups = []
        for fname, items in fams.items():
            items.sort(key=lambda r: (r.get("article") or "").lower())
            groups.append({"brand": bname, "bslug": bslug, "name": fname,
                           "slug": uniq("%s-%s" % (bslug, gslug(fname))),
                           "items": items})
        # 在庫数の多い順。ただし「その他（シリーズ未設定）」は必ず最後
        groups.sort(key=lambda g: (g["name"] == OTHER, -len(g["items"]), g["name"].lower()))
        out.append({"name": bname, "slug": bslug, "groups": groups,
                    "count": sum(len(g["items"]) for g in groups)})
    out.sort(key=lambda b: (-b["count"], b["name"].lower()))
    return out

def group_label(g):
    """一覧ページの見出し用ラベル。シリーズ未設定は「その他の型番」と表す。"""
    return f"{g['brand']} {g['name']}" if g["name"] != OTHER else f"{g['brand']}（その他の型番）"

def page_slug(g, i):
    return g["slug"] if i == 0 else "%s-p%d" % (g["slug"], i + 1)

def chunk(items, per=LIST_PER):
    return [items[i:i + per] for i in range(0, len(items), per)] or [[]]

ICON_GUIDE = ('<svg width="14" height="14" viewBox="0 0 24 24"><path d="M9 11l3 3L22 4"/>'
              '<path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>')
ICON_COMPANY = ('<svg width="14" height="14" viewBox="0 0 24 24"><path d="M3 21h18"/>'
                '<path d="M5 21V7l8-4v18"/><path d="M19 21V11l-6-4"/></svg>')

def hnav(updir):
    """ヘッダー右端の案内ボタン（サービス案内／会社情報）"""
    return (f'<span class="hnav">'
            f'<a href="{updir}guide.html">{ICON_GUIDE}サービス案内</a>'
            f'<a href="{updir}company.html">{ICON_COMPANY}会社情報</a></span>')

def _shell(title, metad, canon, h1, crumb_html, body, jsonld, updir="../"):
    """一覧ページ共通のガワ（型番ページと同じ見た目・同じCSS）。"""
    return f"""<!DOCTYPE html>
<html lang="ja"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<title>{e(title)}</title>
<meta name="description" content="{e(metad)}">
<link rel="canonical" href="{e(canon)}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="GEOPORT">
<meta property="og:locale" content="ja_JP">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(metad)}">
<meta property="og:url" content="{e(canon)}">
<meta name="twitter:card" content="summary">
<script type="application/ld+json">
{json.dumps(jsonld, ensure_ascii=False)}
</script>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@300;400;500;700&family=Barlow+Condensed:wght@500;600;700&family=Barlow:wght@400;500;600&display=swap" rel="stylesheet">
<style>
{CSS}
</style></head><body>
<header><div class="bar">
<a class="logo" href="{updir}"><svg class="gmark" width="28" height="28" viewBox="0 0 36 36" fill="none" stroke="#7fb0e8" stroke-width="2.3"><circle cx="18" cy="18" r="13"/><ellipse cx="18" cy="18" rx="5.6" ry="13" stroke-width="1.5"/><line x1="5.2" y1="18" x2="30.8" y2="18" stroke-width="1.5"/><line x1="7.5" y1="11.5" x2="28.5" y2="11.5" stroke-width="1.2"/><line x1="7.5" y1="24.5" x2="28.5" y2="24.5" stroke-width="1.2"/></svg>GEO<b>PORT</b></a>
{hnav(updir)}
</div></header>

<div class="wrap">
<div class="crumb"><span>{crumb_html}</span><a class="back" href="{updir}">← 製品カタログへ戻る</a></div>
<h1 style="font-size:24px;margin-bottom:6px">{e(h1)}</h1>
{body}
</div>

<footer>GEOPORT株式会社 — FA機器 / 登録番号 T1290001098731<br>
掲載中の在庫品を短納期でお届けします。価格・お見積りはお問い合わせください。<br>
<a href="{updir}list/">メーカー・シリーズ一覧</a> ｜ <a href="{updir}guide.html">サービス案内・保証規定</a> ｜ <a href="{updir}company.html">会社情報</a></footer>
<!-- Cloudflare Web Analytics --><script defer src="https://static.cloudflareinsights.com/beacon.min.js" data-cf-beacon='{{"token": "1f55d2e30afe4d8a806863540932191d"}}'></script><!-- End Cloudflare Web Analytics -->
</body></html>
"""

def _crumb_ld(items):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": u}
                                for i, (n, u) in enumerate(items)]}

def _pager(pages, cur, base_url_fn):
    """ページ送り。前後2ページ＋先頭/末尾を出す。"""
    if pages <= 1:
        return ""
    out = ['<div class="pager">']
    if cur > 0:
        out.append(f'<a href="{base_url_fn(cur - 1)}" rel="prev">← 前へ</a>')
    shown = sorted(set([0, pages - 1] + list(range(max(0, cur - 2), min(pages, cur + 3)))))
    prev = None
    for i in shown:
        if prev is not None and i - prev > 1:
            out.append('<span class="gap">…</span>')
        out.append(f'<span class="cur">{i + 1}</span>' if i == cur
                   else f'<a href="{base_url_fn(i)}">{i + 1}</a>')
        prev = i
    if cur < pages - 1:
        out.append(f'<a href="{base_url_fn(cur + 1)}" rel="next">次へ →</a>')
    out.append("</div>")
    return "".join(out)

def render_list_top(brands):
    total = sum(b["count"] for b in brands)
    cards = []
    for b in brands:
        tops = "・".join(g["name"] for g in b["groups"][:3] if g["name"] != OTHER)
        cards.append(f'<a class="lcard" href="{b["slug"]}.html"><span class="n">{b["count"]:,} 点</span>'
                     f'<span class="a">{e(b["name"])}</span>'
                     f'<span class="b">{e(tops) if tops else "在庫一覧"}</span></a>')
    body = (f'<p class="lead">在庫としてお出しできる {total:,} 点を、メーカー別・シリーズ別に一覧にしています。'
            f'型番をお探しの場合は、メーカーを選んでお進みください。</p>'
            f'<div class="lgrid">{"".join(cards)}</div>')
    return _shell("メーカー・シリーズ一覧｜在庫のあるFA機器を型番まで一覧｜GEOPORT",
                  f"GEOPORTが取り扱う産業用FA機器 {total:,} 点の在庫を、メーカー別・シリーズ別に一覧できます。"
                  f"Siemens・Schneider Electric・ABB・Fanuc ほか。型番から在庫確認・お見積りをご依頼いただけます。",
                  f"{SITE}/{LIST}/", "メーカー・シリーズ一覧",
                  '<a href="../">製品カタログ</a> ／ メーカー・シリーズ一覧', body,
                  _crumb_ld([("製品カタログ", SITE + "/"), ("メーカー・シリーズ一覧", f"{SITE}/{LIST}/")]))

_BL_RE = re.compile(r"(<!--BRANDLINKS-->)(.*?)(<!--/BRANDLINKS-->)", re.S)
_BS_RE = re.compile(r"(<!--BRANDSERIES-->)(.*?)(<!--/BRANDSERIES-->)", re.S)

def update_index_brandlinks(brands):
    """トップページの2か所を、在庫の実態に合わせて自動更新する（目印の間だけ書き換え）。
      ① フッターのメーカーリンク … Googleが辿れる“ふつうのリンク”（JavaScript不要）
      ② シリーズ一覧のデータ    … メーカーボタンに重ねたとき出るポップの中身"""
    try:
        with open("index.html", encoding="utf-8") as f:
            src = f.read()
    except OSError:
        print("note: index.html が読めないためトップページは更新しません")
        return False
    if not _BL_RE.search(src) or not _BS_RE.search(src):
        print("note: index.html に目印(BRANDLINKS/BRANDSERIES)が無いため更新しません")
        return False
    links = "".join(f'<a href="./{LIST}/{b["slug"]}.html">{e(b["name"])}</a>' for b in brands)
    data = {b["name"]: {"slug": b["slug"], "n": b["count"],
                        "s": [[g["name"] if g["name"] != OTHER else "その他の型番",
                               g["slug"], len(g["items"])] for g in b["groups"]]}
            for b in brands}
    payload = ('<script type="application/json" id="brandseries">'
               + json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
               + "</script>")
    out = _BL_RE.sub(lambda m: m.group(1) + links + m.group(3), src)
    out = _BS_RE.sub(lambda m: m.group(1) + payload + m.group(3), out)
    if out == src:
        return False
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(out)
    print("index.html を更新: メーカー %d 社 / シリーズ %d 組"
          % (len(brands), sum(len(b["groups"]) for b in brands)))
    return True

def render_list_brand(b):
    cards = []
    for g in b["groups"]:
        nm = g["name"] if g["name"] != OTHER else "その他の型番"
        cards.append(f'<a class="lcard" href="{g["slug"]}.html"><span class="n">{len(g["items"]):,} 点</span>'
                     f'<span class="a">{e(nm)}</span>'
                     f'<span class="b">{e(b["name"])}</span></a>')
    body = (f'<p class="lead">{e(b["name"])} の在庫 {b["count"]:,} 点を、シリーズ別に一覧にしています。'
            f'新古品（未使用在庫品）と J-Certified規格のリファビッシュ品を扱っており、'
            f'品質区分は各製品ページに表示しています。価格はお見積りにてご提示します。</p>'
            f'<div class="lgrid">{"".join(cards)}</div>')
    return _shell(f'{b["name"]} 在庫一覧（{b["count"]:,}点）｜GEOPORT',
                  f'{b["name"]} の産業用FA機器 {b["count"]:,} 点の在庫一覧。シリーズ別に型番を確認できます。'
                  f'初期不良を保証（期間は製品ページに表示）。型番から在庫確認・お見積りをご依頼いただけます。｜GEOPORT',
                  f'{SITE}/{LIST}/{b["slug"]}.html', f'{b["name"]} 在庫一覧',
                  f'<a href="../">製品カタログ</a> ／ <a href="./">メーカー・シリーズ一覧</a> ／ {e(b["name"])}',
                  body,
                  _crumb_ld([("製品カタログ", SITE + "/"), ("メーカー・シリーズ一覧", f"{SITE}/{LIST}/"),
                             (b["name"], f'{SITE}/{LIST}/{b["slug"]}.html')]))

def render_list_group(g, page_i, pages_total, items):
    label = group_label(g)
    n = len(g["items"])
    cards = []
    for r in items:
        fam = _clean_field(r.get("family"))
        sub = f'{g["brand"]}{"　" + fam if fam else ""}'
        cards.append(f'<a class="lcard" href="../{OUT}/{r["_slug"]}.html">'
                     f'<span class="a">{e(r.get("article") or "")}</span>'
                     f'<span class="b">{e(sub)}</span></a>')
    suffix = f'（{page_i + 1}/{pages_total}ページ）' if pages_total > 1 else ""
    pager = _pager(pages_total, page_i, lambda i: f"{page_slug(g, i)}.html")
    body = (f'<p class="lead">{e(label)} の在庫 {n:,} 点の型番一覧です{e(suffix)}。'
            f'型番をクリックすると、仕様・在庫数の確認とお見積りのご依頼ができます。</p>'
            f'<div class="lgrid">{"".join(cards)}</div>{pager}')
    canon = f'{SITE}/{LIST}/{page_slug(g, page_i)}.html'
    title = f'{label} 型番一覧（{n:,}点）{suffix}｜GEOPORT'
    return _shell(title,
                  f'{label} の在庫 {n:,} 点の型番一覧{suffix}。初期不良を保証（期間は製品ページに表示）。'
                  f'型番から在庫確認・お見積りをご依頼いただけます。｜GEOPORT',
                  canon, f'{label} 型番一覧',
                  f'<a href="../">製品カタログ</a> ／ <a href="./">メーカー・シリーズ一覧</a>'
                  f' ／ <a href="{g["bslug"]}.html">{e(g["brand"])}</a> ／ {e(g["name"] if g["name"] != OTHER else "その他の型番")}',
                  body,
                  _crumb_ld([("製品カタログ", SITE + "/"), ("メーカー・シリーズ一覧", f"{SITE}/{LIST}/"),
                             (g["brand"], f'{SITE}/{LIST}/{g["bslug"]}.html'),
                             (g["name"] if g["name"] != OTHER else "その他の型番", canon)]))

def related_html(g, pos):
    """同じシリーズの近い型番（型番順で前後）を最大 RELATED_N 件。"""
    items = g["items"]
    n = len(items)
    if n <= 1:
        return ""
    half = RELATED_N // 2
    start = max(0, pos - half)
    end = min(n, start + RELATED_N + 1)
    start = max(0, end - RELATED_N - 1)
    picked = [(i, it) for i, it in enumerate(items[start:end], start) if i != pos][:RELATED_N]
    cards = []
    for _, r in picked:
        cards.append(f'<a href="{r["_slug"]}.html"><span class="a">{e(r.get("article") or "")}</span>'
                     f'<span class="b">{e(g["brand"])}</span></a>')
    label = group_label(g)
    more = (f'<div class="relmore"><a href="../{LIST}/{g["slug"]}.html">'
            f'{e(label)} の在庫 {n:,} 点をすべて見る →</a></div>')
    return (f'<div class="sec"><h2>同じシリーズの製品</h2>'
            f'<div class="rel">{"".join(cards)}</div>{more}</div>')

def render(row, slug, g=None, pos=0):
    art   = row.get("article") or ""
    brand = _clean_field(row.get("brand"))
    fam   = _clean_field(row.get("family"))
    dj    = clean_desc(row.get("description_ja"))   # 末尾注記を外す
    if is_refusal(dj):                              # 丸ごと断り文なら定型文へ
        dj = ""
    stock = row.get("stock")
    badge_txt = f"在庫 {stock} 点" if isinstance(stock, int) and stock > 0 else "在庫あり"
    # 品質区分。リファビッシュ品は説明ページ（3工程・ISO・Q&A）へリンクする。
    is_ref = "リファビッシュ" in (row.get("condition") or "")
    if is_ref:
        cond_html = ('リファビッシュ品（J-Certified）'
                     '<a class="wlink" href="../refurbished.html">※J-Certified規格について</a>')
    else:
        cond_html = '新古品（未使用在庫品）'
    # ★保証期間は catalog.warranty_years の値をそのまま出す（2026-08-29）。
    #   以前は「新古品=1年／リファ=2年」とここに直接書いていたが、見積書PDF側にも
    #   別に「1年」と書いてあり、**偶然一致しているだけ**の危うい状態だった（S指摘）。
    #   いまは sync.py が決めた値をページも見積書も読む＝出どころが1つ。
    wy = row.get("warranty_years")
    wy = 1 if wy in (None, "") else int(wy)
    warr_html = f'{wy}年保証<a class="wlink" href="../guide.html#warranty">※保証規定をご確認ください</a>' 
    sbkey_json = json.dumps(SB_KEY)
    relay_json = json.dumps(RELAY)
    art_json   = json.dumps(art)
    canon = f"{SITE}/{OUT}/{slug}.html"
    title = f"{art} {brand}｜GEOPORT" if brand else f"{art}｜GEOPORT"
    fam_paren = f"（{fam}）" if fam else ""
    _cond_txt = "リファビッシュ品" if is_ref else "新古品"
    metad = (f"{brand}{fam_paren}{art} の在庫・お見積り。{_cond_txt}、初期不良は納品後{wy}年以内保証。"
             f"型番から在庫確認・お見積りをご依頼いただけます。｜GEOPORT")
    ogt = f"{art} {brand}｜GEOPORT" if brand else title
    ogd = f"{brand}{fam_paren}{art} の在庫・お見積り。{_cond_txt}・初期不良{wy}年保証。"
    # 商品(Product)の構造化データは掲載しない：価格(offers)/レビュー/評価が無く
    # Search Consoleで「商品スニペット」不備の警告になるため（見積制で価格非公開）。パンくずのみ残す。
    # パンくず＝製品カタログ／メーカー・シリーズ一覧／メーカー／シリーズ／型番（一覧ページへの内部リンクを兼ねる）
    trail = [("製品カタログ", SITE + "/", "../"),
             ("メーカー・シリーズ一覧", f"{SITE}/{LIST}/", f"../{LIST}/")]
    if g:
        trail.append((g["brand"], f'{SITE}/{LIST}/{g["bslug"]}.html', f'../{LIST}/{g["bslug"]}.html'))
        if g["name"] != OTHER:
            # パンくずは「Siemens ／ Simatic S7」。メーカー名の重複は出さない
            trail.append((g["name"], f'{SITE}/{LIST}/{g["slug"]}.html', f'../{LIST}/{g["slug"]}.html'))
    crumb = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement":
             [{"@type": "ListItem", "position": i + 1, "name": nm, "item": u}
              for i, (nm, u, _) in enumerate(trail)] +
             [{"@type": "ListItem", "position": len(trail) + 1, "name": art, "item": canon}]}
    crumb_html = " ／ ".join(f'<a href="{href}">{e(nm)}</a>' for nm, _, href in trail) + f" ／ {e(art)}"
    related = related_html(g, pos) if g else ""
    # ★2026-09-02：ここは品質区分で文言を変える。
    #   リファビッシュ品を掲載し始めたのに「新古品（未使用在庫品）です」と固定で書いており、
    #   説明文が無い 23,465 件（＝ほぼ全部のリファ品）で**お客様に誤った説明**が出ていた。
    _about_cond = "J-Certified規格のリファビッシュ品" if is_ref else "新古品（未使用在庫品）"
    about = desc_paras(dj) or (f"<p>{e(art)} の{_about_cond}です。詳しい仕様・在庫状況は、"
                               f"下のボタンよりお問い合わせください。</p>")
    series_html = f'<div class="series">{e(fam)} シリーズ</div>' if fam else ""
    brand_html  = f'<div class="brand">{e(brand)}</div>' if brand else ""
    brand_trow  = f"<tr><th>メーカー</th><td>{e(brand)}</td></tr>" if brand else ""
    fam_row     = f"<tr><th>シリーズ</th><td>{e(fam)}</td></tr>" if fam else ""
    # 製品仕様（説明の下に折りたたみで表示）。フィードにある項目だけを出す（推測しない）。
    dims = _clean_field(row.get("dimensions"))
    hs   = _clean_field(row.get("commodity_code"))
    ean  = _clean_field(row.get("ean"))
    wt   = row.get("weight_kg")
    try:
        wtxt = (("%g" % float(wt)) + " kg") if wt not in (None, "") and float(wt) > 0 else ""
    except (TypeError, ValueError):
        wtxt = ""
    _srows = [
        f"<tr><th>メーカー</th><td>{e(brand)}</td></tr>" if brand else "",
        f"<tr><th>シリーズ</th><td>{e(fam)}</td></tr>" if fam else "",
        f"<tr><th>型番</th><td>{e(art)}</td></tr>",
        f"<tr><th>外形寸法 (W×D×H)</th><td>{e(dims)}</td></tr>" if dims else "",
        f"<tr><th>質量</th><td>{e(wtxt)}</td></tr>" if wtxt else "",
        f"<tr><th>HSコード</th><td>{e(hs)}</td></tr>" if hs else "",
        f"<tr><th>EAN</th><td>{e(ean)}</td></tr>" if ean else "",
    ]
    spec_extra = ('<details class="specbox" open><summary>製品仕様</summary>'
                  '<table class="spec2">' + "".join(s for s in _srows if s) +
                  '</table></details>')
    # 製品写真（自社ストレージの公開URLのみ。無ければ準備中プレースホルダ）
    # 2枚目以降は x/<slug>_N.jpg。サムネイルを押すと大きい写真が入れ替わる。
    img_url = (row.get("image_url") or "").strip()
    shots_json = "[]"
    if img_url:
        n_img = max(1, int(row.get("image_count") or 1))
        shots = [img_url] + [f"{SB_URL}/storage/v1/object/public/product-images/x/{slug}_{i}.jpg"
                             for i in range(1, n_img)]
        shots_json = json.dumps(shots)
        thumbs = ""
        if len(shots) > 1:
            btns = "".join(
                f'<button type="button" class="th{" on" if i == 0 else ""}" '
                f'onclick="showShot(this,{i})" aria-label="写真{i + 1}">'
                f'<img src="{e(u)}" alt="" loading="lazy"></button>'
                for i, u in enumerate(shots))
            thumbs = f'<div class="thumbs">{btns}</div>'
        photo_html = (f'<div class="gal"><div class="photo zoomable" id="photobox">'
                      f'<img id="mainshot" src="{e(img_url)}" alt="{e(art)} {e(brand)}" '
                      f'onclick="photoClick()">'
                      f'<div class="inzoom" id="inzoom"></div>'
                      f'<div class="pctl">'
                      f'<button type="button" class="mag" id="magbtn" onclick="toggleMag()" '
                      f'title="虫眼鏡（拡大して見る）" aria-label="虫眼鏡">'
                      f'<svg width="17" height="17" viewBox="0 0 24 24"><circle cx="11" cy="11" r="7"/>'
                      f'<path d="M21 21l-4.3-4.3"/><path d="M11 8v6"/><path d="M8 11h6"/></svg></button>'
                      f'<button type="button" onclick="openLB()" title="全画面で拡大" aria-label="全画面で拡大">'
                      f'<svg width="17" height="17" viewBox="0 0 24 24"><path d="M15 3h6v6"/>'
                      f'<path d="M9 21H3v-6"/><path d="M21 3l-7 7"/><path d="M3 21l7-7"/></svg></button>'
                      f'</div></div>'
                      f'{thumbs}</div>')
    else:
        photo_html = (f'<div class="gal"><div class="photo ph"><span class="pn">{e(art)}</span>'
                      f'<span class="note">製品写真は準備中です</span></div></div>')
    # 全画面拡大の器（写真がある場合だけ）
    lightbox = ("" if not img_url else
                '<div class="lb" id="lb" onclick="lbBg(event)">'
                '<button class="x" type="button" onclick="closeLB()" aria-label="閉じる">&times;</button>'
                '<button class="nav prev" type="button" onclick="stepLB(-1)" aria-label="前の写真">&#8249;</button>'
                '<div class="lbscroll"><img id="lbimg" alt="" onclick="lbToggle(event)" onload="lbCount()"></div>'
                '<button class="nav next" type="button" onclick="stepLB(1)" aria-label="次の写真">&#8250;</button>'
                '<div class="cnt" id="lbcnt"></div></div>')
    return f"""<!DOCTYPE html>
<html lang="ja"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
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
{json.dumps(crumb, ensure_ascii=False)}
</script>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@300;400;500;700&family=Barlow+Condensed:wght@500;600;700&family=Barlow:wght@400;500;600&display=swap" rel="stylesheet">
<style>
{CSS}
</style></head><body>
<header><div class="bar">
<a class="logo" href="../"><svg class="gmark" width="28" height="28" viewBox="0 0 36 36" fill="none" stroke="#7fb0e8" stroke-width="2.3"><circle cx="18" cy="18" r="13"/><ellipse cx="18" cy="18" rx="5.6" ry="13" stroke-width="1.5"/><line x1="5.2" y1="18" x2="30.8" y2="18" stroke-width="1.5"/><line x1="7.5" y1="11.5" x2="28.5" y2="11.5" stroke-width="1.2"/><line x1="7.5" y1="24.5" x2="28.5" y2="24.5" stroke-width="1.2"/></svg>GEO<b>PORT</b></a>
{hnav("../")}
</div></header>

<div class="wrap">
<div class="crumb"><span>{crumb_html}</span><a class="back" href="../">← 製品カタログへ戻る</a></div>

<div class="top">
  {photo_html}
  <div>
    {brand_html}
    <h1>{e(art)}</h1>
    {series_html}
    <span class="badge">● {e(badge_txt)}</span>
    <table class="spec">
      <tr><th>型番</th><td>{e(art)}</td></tr>
      {brand_trow}
      {fam_row}
      <tr><th>品質区分</th><td>{cond_html}</td></tr>
      <tr><th>納期</th><td>通常 約10〜14日でお届け</td></tr>
      <tr><th>保証</th><td>{warr_html}</td></tr>
      <tr><th>価格</th><td><button class="cta" type="button" onclick="openQuote()">この製品の見積を確認する</button></td></tr>
    </table>
  </div>
</div>

<div class="sec">
  <h2>製品について</h2>
  {about}
</div>

{spec_extra}

{related}

<div class="disc">※ 当社は各メーカーの正規代理店ではありません。取り扱う製品はメーカー保証の対象外となりますが、当社保証規定に基づき対応いたします。掲載のメーカー名および商標は各権利者に帰属します。詳細は<a href="../guide.html#warranty" style="color:var(--accent)">サービス案内・保証規定</a>をご確認ください。</div>
</div>

<footer>GEOPORT株式会社 — FA機器 / 登録番号 T1290001098731<br>
掲載中の在庫品を短納期でお届けします。価格・お見積りはお問い合わせください。<br>
<a href="../{LIST}/">メーカー・シリーズ一覧</a> ｜ <a href="../guide.html">サービス案内・保証規定</a> ｜ <a href="../company.html">会社情報</a></footer>

{lightbox}

<div class="overlay" id="ov"><div class="modal">
<div class="mhead"><div><h3>見積・在庫確認</h3><div class="sub">{e(art)}</div></div><button class="x" type="button" onclick="closeQuote()">&times;</button></div>
<div class="mbody" id="mform">
<div class="mnote">在庫状況・お見積り（価格）・納期を、担当より折り返しご連絡いたします。お支払いは銀行振込にて承ります。国内送料はお届け先までの実費を別途申し受けますので、都道府県をお選びください。※法人・事業者様向けのサービスです。</div>
<div class="field"><label>数量 <span class="req">*</span></label><input id="f-qty" type="number" value="1" min="1"></div>
<div class="row2"><div class="field"><label>会社名 <span class="req">*</span></label><input id="f-co" type="text"></div>
<div class="field"><label>ご担当者名 <span class="req">*</span></label><input id="f-name" type="text"></div></div>
<div class="field"><label>メールアドレス <span class="req">*</span></label><input id="f-mail" type="email"></div>
<div class="field"><label>お届け先の都道府県 <span class="req">*</span></label><select id="f-pref"><option value="">選択してください</option></select></div>
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
/* ---- 写真の切替・虫眼鏡・全画面拡大 ---- */
var SHOTS={shots_json}, CUR=0;
function showShot(b,i){{CUR=i;var m=$("mainshot");if(m&&SHOTS[i])m.src=SHOTS[i];
  var t=document.querySelectorAll(".th");for(var k=0;k<t.length;k++)t[k].classList.remove("on");
  if(b)b.classList.add("on");}}
function lbToggle(ev){{if(ev)ev.stopPropagation();var im=$("lbimg");if(im)im.classList.toggle("full");lbCount();}}
function lbCount(){{var im=$("lbimg"),tip="";
  /* 画面いっぱいでも実寸に届かないときだけ「原寸で見る」を案内する（PCでは元々原寸のことが多い） */
  if(im&&im.naturalWidth){{
    if(im.classList.contains("full")) tip="画像を押すと全体表示";
    else if(im.naturalWidth>im.getBoundingClientRect().width+2) tip="画像を押すと原寸";
  }}
  var head=(SHOTS.length>1?((CUR+1)+" / "+SHOTS.length):"");
  var c=$("lbcnt");if(c)c.textContent=head+((head&&tip)?"　・　":"")+tip;
  var n=document.querySelectorAll(".lb .nav");
  for(var i=0;i<n.length;i++)n[i].style.display=SHOTS.length>1?"block":"none";}}
function openLB(){{if(!SHOTS.length)return;var im=$("lbimg");if(im){{im.classList.remove("full");im.src=SHOTS[CUR];}}
  var l=$("lb");if(l)l.classList.add("show");lbCount();}}
function closeLB(){{var l=$("lb");if(l)l.classList.remove("show");}}
function lbBg(ev){{if(ev.target&&ev.target.id==="lb")closeLB();}}
function stepLB(d){{if(SHOTS.length<2)return;CUR=(CUR+d+SHOTS.length)%SHOTS.length;
  var im=$("lbimg");if(im){{im.classList.remove("full");im.src=SHOTS[CUR];}}
  var m=$("mainshot");if(m)m.src=SHOTS[CUR];
  var t=document.querySelectorAll(".th");
  for(var i=0;i<t.length;i++){{if(i===CUR)t[i].classList.add("on");else t[i].classList.remove("on");}}
  lbCount();}}
document.addEventListener("keydown",function(ev){{
  var l=$("lb");if(!l||!l.classList.contains("show"))return;
  if(ev.key==="Escape")closeLB();
  else if(ev.key==="ArrowRight")stepLB(1);
  else if(ev.key==="ArrowLeft")stepLB(-1);}});
/* 虫眼鏡：右下のボタンでON/OFF。写真の枠ごと約2.3倍（実サイズ÷表示サイズ）に拡大する */
var MAGON=false;
function hideMag(){{var z=$("inzoom"),b=$("photobox");if(z)z.style.display="none";if(b)b.classList.remove("magon");}}
function toggleMag(){{MAGON=!MAGON;var b=$("magbtn");if(b)b.classList.toggle("on",MAGON);if(!MAGON)hideMag();}}
function photoClick(){{if(!MAGON)openLB();}}
(function(){{
  if(!window.matchMedia||!matchMedia("(hover:hover)").matches)return;
  var box=$("photobox"),img=$("mainshot");if(!box||!img)return;
  box.addEventListener("mousemove",function(ev){{
    if(!MAGON||!img.naturalWidth)return;
    var r=img.getBoundingClientRect(),br=box.getBoundingClientRect();
    if(ev.clientX<r.left||ev.clientX>r.right||ev.clientY<r.top||ev.clientY>r.bottom){{hideMag();return;}}
    var zx=img.naturalWidth/r.width,zy=img.naturalHeight/r.height;
    var x=ev.clientX-r.left,y=ev.clientY-r.top;
    var z=$("inzoom");z.style.display="block";box.classList.add("magon");
    z.style.backgroundImage='url("'+img.src+'")';
    z.style.backgroundSize=img.naturalWidth+"px "+img.naturalHeight+"px";
    z.style.backgroundPosition=(-(x*zx-br.width/2))+"px "+(-(y*zy-br.height/2))+"px";
  }});
  box.addEventListener("mouseleave",hideMag);
}})();
function openQuote(){{var e=$("m-err");if(e)e.style.display="none";var f=$("mform");if(f)f.style.display="flex";var ft=$("mfoot");if(ft)ft.style.display="block";var s=$("m-sent");if(s)s.classList.remove("show");var b=$("m-sub");if(b){{b.disabled=false;b.textContent="この内容で問い合わせる";}}["f-qty","f-co","f-name","f-mail","f-note","f-pref"].forEach(function(id){{var el=$(id);if(el)el.value=(id==="f-qty"?"1":"");}});fillPrefs();var ov=$("ov");if(ov)ov.classList.add("show");}}
function closeQuote(){{var ov=$("ov");if(ov)ov.classList.remove("show");}}
// お届け先の都道府県（国内送料の計算に使う）
var PREFS=["北海道","青森県","岩手県","宮城県","秋田県","山形県","福島県","茨城県","栃木県","群馬県","埼玉県","千葉県","東京都","神奈川県","新潟県","富山県","石川県","福井県","山梨県","長野県","岐阜県","静岡県","愛知県","三重県","滋賀県","京都府","大阪府","兵庫県","奈良県","和歌山県","鳥取県","島根県","岡山県","広島県","山口県","徳島県","香川県","愛媛県","高知県","福岡県","佐賀県","長崎県","熊本県","大分県","宮崎県","鹿児島県","沖縄県"];
function fillPrefs(){{var el=$("f-pref");if(!el||el.options.length>1)return;for(var i=0;i<PREFS.length;i++){{var o=document.createElement("option");o.value=PREFS[i];o.textContent=PREFS[i];el.appendChild(o);}}}}
function submitQuote(){{
  var qty=($("f-qty")||{{}}).value;qty=qty?qty.trim():"";
  var co=($("f-co")||{{}}).value;co=co?co.trim():"";
  var name=($("f-name")||{{}}).value;name=name?name.trim():"";
  var mail=($("f-mail")||{{}}).value;mail=mail?mail.trim():"";
  var note=($("f-note")||{{}}).value;note=note?note.trim():"";
  var pref=($("f-pref")||{{}}).value;pref=pref?pref.trim():"";
  var err=$("m-err");
  if(!co||!name||!mail||!qty||!pref){{if(err){{err.textContent="会社名・ご担当者名・メールアドレス・数量・お届け先の都道府県は必須です。";err.style.display="block";}}return;}}
  if(mail.indexOf("@")<0){{if(err){{err.textContent="メールアドレスの形式をご確認ください。";err.style.display="block";}}return;}}
  if(err)err.style.display="none";
  var b=$("m-sub");if(b){{b.disabled=true;b.textContent="送信しています…";}}
  var payload={{article:ART,qty:qty,company:co,person:name,email:mail,note:note,pref:pref}};
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

_LOC_RE = re.compile(r"<loc>([^<]+)</loc>\s*<lastmod>([^<]+)</lastmod>")

def read_old_lastmod():
    """前回のsitemapから URL→最終更新日 を読む。中身が変わっていないページは日付を据え置く。"""
    try:
        with open("sitemap.xml", encoding="utf-8") as f:
            return dict(_LOC_RE.findall(f.read()))
    except (OSError, ValueError):
        return {}

class Writer:
    """内容が変わったファイルだけ書き出し、sitemapのlastmodも実際に変わった日にする。"""
    def __init__(self, today, old):
        self.today, self.old = today, old
        self.urls, self.changed, self.same = [], 0, 0

    def put(self, path, content, url, changefreq, priority):
        try:
            with open(path, encoding="utf-8") as f:
                prev = f.read()
        except OSError:
            prev = None
        if prev == content:
            lastmod = self.old.get(url) or self.today
            self.same += 1
        else:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            lastmod = self.today
            self.changed += 1
        self.urls.append((url, lastmod, changefreq, priority))

    def write_sitemap(self):
        out = ['<?xml version="1.0" encoding="UTF-8"?>',
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
        for url, lm, cf, pr in sorted(self.urls):   # URL順に固定（毎回の差分を最小に）
            out.append(f'  <url><loc>{url}</loc><lastmod>{lm}</lastmod>'
                       f'<changefreq>{cf}</changefreq><priority>{pr}</priority></url>')
        out.append('</urlset>')
        body = "\n".join(out) + "\n"
        try:
            with open("sitemap.xml", encoding="utf-8") as f:
                if f.read() == body:
                    return False
        except OSError:
            pass
        with open("sitemap.xml", "w", encoding="utf-8") as f:
            f.write(body)
        return True

def main():
    today = os.environ.get("LASTMOD") or datetime.date.today().isoformat()
    rows = fetch_catalog()
    print("catalog rows: %d" % len(rows))
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(LIST, exist_ok=True)

    # ① 型番ごとのURL(slug)を先に確定させる（一覧・関連製品からリンクするため）
    seen, live = {}, []
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
        row["_slug"] = slug
        live.append(row)

    # ② メーカー→シリーズ の目次を組み立てる
    brands = build_index(live)
    ngroups = sum(len(b["groups"]) for b in brands)
    print("目次: メーカー %d 社 / シリーズ %d 組" % (len(brands), ngroups))

    # トップページのメーカーリンク行を在庫の実態に合わせる
    idx_changed = update_index_brandlinks(brands)

    w = Writer(today, read_old_lastmod())
    # 固定ページ（会社情報・サービス案内）はこの生成の対象外なので日付を据え置く
    for loc, cf, pr in [("/", "daily", "1.0"), ("/company.html", "monthly", "0.5"),
                        ("/guide.html", "monthly", "0.5")]:
        lm = today if (loc == "/" and idx_changed) else (w.old.get(SITE + loc) or today)
        w.urls.append((SITE + loc, lm, cf, pr))

    # ③ 型番ページ（パンくず＋同じシリーズの関連製品つき）
    no_desc = 0
    for b in brands:
        for g in b["groups"]:
            for pos, row in enumerate(g["items"]):
                _dj = clean_desc(row.get("description_ja"))
                if not _dj or is_refusal(_dj):
                    no_desc += 1
                slug = row["_slug"]
                w.put(os.path.join(OUT, slug + ".html"), render(row, slug, g, pos),
                      f"{SITE}/{OUT}/{slug}.html", "weekly", "0.6")

    # ④ 一覧（目次）ページ
    w.put(os.path.join(LIST, "index.html"), render_list_top(brands),
          f"{SITE}/{LIST}/", "weekly", "0.8")
    list_files = ["index.html"]
    for b in brands:
        fn = b["slug"] + ".html"
        list_files.append(fn)
        w.put(os.path.join(LIST, fn), render_list_brand(b),
              f"{SITE}/{LIST}/{fn}", "weekly", "0.7")
        for g in b["groups"]:
            pages = chunk(g["items"])
            for i, items in enumerate(pages):
                fn = page_slug(g, i) + ".html"
                list_files.append(fn)
                w.put(os.path.join(LIST, fn), render_list_group(g, i, len(pages), items),
                      f"{SITE}/{LIST}/{fn}", "weekly", "0.6")

    # ⑤ 在庫から消えた型番ページ・使わなくなった一覧ページを削除
    removed = 0
    for d, keep in ((OUT, set(r["_slug"] + ".html" for r in live)), (LIST, set(list_files))):
        if not os.path.isdir(d):
            continue
        for fn in os.listdir(d):
            if fn.endswith(".html") and fn not in keep:
                os.remove(os.path.join(d, fn))
                removed += 1

    sm = w.write_sitemap()
    print("型番ページ %d 件 / 一覧ページ %d 件" % (len(live), len(list_files)))
    print("更新: %d / 変更なし(据え置き): %d / 削除: %d / sitemap: %s"
          % (w.changed, w.same, removed, "更新" if sm else "変更なし"))
    print("no description_ja(fallback used): %d" % no_desc)

if __name__ == "__main__":
    main()
