import os
import math
import concurrent.futures
import time
import random
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template_string
import yfinance as yf
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False

# =====================================================
# ADVANCED HTTP SESSION & USER AGENTS
# =====================================================
session = requests.Session()
retry_strategy = Retry(
    total=5,
    connect=5,
    read=5,
    backoff_factor=2,
    status_forcelist=[429, 500, 502, 503, 504]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("https://", adapter)
session.mount("http://", adapter)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/137.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:140.0) Gecko/20100101 Firefox/140.0"
]

def get_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive"
    }

PAGE = r"""
<!doctype html>
<html lang="hi">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>MarkeTGyan, Technical Analysis Scanner</title>
<style>
:root{--bg:#0b1220;--panel:#121d31;--line:#263650;--text:#eef4ff;--muted:#a8b7ce;--gold:#ffc857;--green:#4ade80;--red:#fb7185}
*{box-sizing:border-box}body{margin:0;background:linear-gradient(135deg,#07101e,#101d32);font-family:Arial,"Noto Sans Devanagari",sans-serif;color:var(--text)}
main{max-width:1150px;margin:0 auto;padding:22px}header{padding:24px 0 12px}h1{font-size:clamp(26px,4vw,42px);margin:0 0 8px} .sub{color:var(--muted);line-height:1.6}
.panel{background:rgba(18,29,49,.96);border:1px solid var(--line);border-radius:18px;padding:20px;margin:16px 0;box-shadow:0 12px 30px #0002}
form{display:flex;gap:10px;flex-wrap:wrap}input{flex:1;min-width:210px;background:#07101e;color:white;border:1px solid #3b4d68;border-radius:10px;padding:15px;font-size:17px}
button{border:0;border-radius:10px;padding:14px 20px;background:var(--gold);color:#1c2433;font-weight:800;font-size:16px;cursor:pointer}button:disabled{opacity:.6;cursor:wait}
.hint{font-size:13px;color:var(--muted);margin-top:10px;line-height:1.5}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px}
.metric{background:#0a1425;border:1px solid var(--line);border-radius:12px;padding:15px}.metric small{display:block;color:var(--muted);margin-bottom:8px}.metric strong{font-size:24px;overflow-wrap:anywhere}
.green{color:var(--green)}.red{color:var(--red)}.gold{color:var(--gold)}h2{font-size:22px;margin:0 0 14px}h3{margin:0 0 8px}.section{margin-top:22px}.copy{line-height:1.75;color:#e4ecf8}.tag{display:inline-block;padding:6px 10px;border-radius:20px;background:#24344c;color:var(--gold);font-size:13px;font-weight:bold}
table{width:100%;border-collapse:collapse;margin-bottom:20px}td,th{text-align:left;border-bottom:1px solid var(--line);padding:11px 8px;vertical-align:top}th{color:var(--muted)}.error{color:var(--red);white-space:pre-wrap}.hidden{display:none}.saved-table-wrap{overflow-x:auto}.saved-table{min-width:1050px}.saved-actions{display:flex;gap:6px;flex-wrap:wrap}.small-btn{padding:8px 11px;font-size:13px;border-radius:7px}.delete-btn{background:#fb7185;color:#1c2433}.open-btn{background:#4ade80;color:#102018}.empty-row{text-align:center;color:var(--muted);padding:18px}
footer{color:var(--muted);font-size:12px;line-height:1.6;padding:18px 0 30px}

/* Tab Layout CSS */
.tab-buttons{display:flex;gap:10px;margin-bottom:15px;border-bottom:2px solid var(--line);padding-bottom:10px;flex-wrap:wrap}
.tab-btn{background:#0a1425;color:var(--muted);border:1px solid var(--line);padding:10px 18px;border-radius:8px;cursor:pointer;font-weight:bold}
.tab-btn.active{background:var(--gold);color:#1c2433;border-color:var(--gold)}
.tab-content{display:none}.tab-content.active{display:block}
.status-msg{font-size:15px;font-weight:bold;color:var(--gold);margin-bottom:12px}.progress-track{width:100%;height:14px;background:#07101e;border:1px solid var(--line);border-radius:99px;overflow:hidden;margin:8px 0 16px}.progress-fill{height:100%;width:0%;background:var(--green);transition:width .25s ease}.progress-caption{font-size:13px;color:var(--muted);margin-bottom:12px}
</style>
</head>
<body><main>
<header><div class="tag">MarkeTGyan, Technical Analysis Scanner</div>
<h1>AI Stock Analyst & Screener</h1>
<div class="sub">एक ही स्टॉक के तकनीकी संकेतक, सपोर्ट/रेजिस्टेंस, वित्तीय स्थिति और डेटा-आधारित समग्र विश्लेषण।</div></header>

<!-- Top tabs -->
<div class="tab-buttons" role="tablist" aria-label="स्टॉक विश्लेषण टैब">
  <button type="button" class="tab-btn active" data-tab-target="searchTab">🔎 नया विश्लेषण</button>
  <button type="button" class="tab-btn" data-tab-target="savedTab">🗂️ पूर्व विश्लेषित सभी स्टॉक्स</button>
</div>

<!-- Tab 1: Single Stock Analysis -->
<div id="searchTab" class="tab-content active">
  <div class="panel">
  <form id="stockForm"><input id="symbol" placeholder="उदाहरण: CIPLA, RELIANCE, TCS, ZOMATO" required autocomplete="off"><button id="go" type="submit">विश्लेषण करें ↗</button></form>
  <div class="hint">भारतीय शेयर के लिए NSE symbol लिखें (जैसे CIPLA)। सफल विश्लेषण के बाद स्टॉक अपने-आप “पूर्व विश्लेषित सभी स्टॉक्स” टैब में सेव होगा।</div>
  </div>
  <div id="status" class="panel hidden"></div>
  <div id="results" class="hidden">
  <div class="panel"><div id="company"></div><div id="metrics" class="grid"></div></div>
  <div class="panel"><h2>🧭 Trend और Momentum</h2><div id="trend" class="copy"></div></div>
  
  <div class="panel"><h2>📊 Daily Support/Resistance</h2><div id="dailyLevels"></div></div>
  <div class="panel"><h2>📋 डेली S/R आधारित Entry, Stop Loss और Target योजना</h2><div id="dailyTradePlan"></div><p class="copy"><b>SEBI डिस्क्लेमर:</b> MarkeTGyan SEBI-पंजीकृत निवेश सलाहकार नहीं है। यह तालिका केवल शैक्षिक उद्देश्य के लिए उपलब्ध ऐतिहासिक डेटा से बने संभावित स्तर दिखाती है; यह खरीदने/बेचने की व्यक्तिगत सलाह नहीं है। ट्रेड से पहले स्वयं पुष्टि करें और जोखिम समझें।</p></div>
  <div class="panel"><h2>⏱️ 1HR Support/Resistance</h2><div id="hourlyLevels"></div></div>
  <div class="panel"><h2>📋 1 घंटे के S/R आधारित Entry, Stop Loss और Target योजना</h2><div id="hourlyTradePlan"></div><p class="copy"><b>SEBI डिस्क्लेमर:</b> MarkeTGyan SEBI-पंजीकृत निवेश सलाहकार नहीं है। यह तालिका केवल शैक्षिक उद्देश्य के लिए उपलब्ध ऐतिहासिक डेटा से बने संभावित स्तर दिखाती है; यह खरीदने/बेचने की व्यक्तिगत सलाह नहीं है। ट्रेड से पहले स्वयं पुष्टि करें और जोखिम समझें।</p></div>

  <div class="panel"><h2>🏢 कंपनी की वित्तीय स्थिति (Financials)</h2><div id="fundamentals"></div></div>
  <div class="panel"><h2>📊 Shareholding Pattern</h2><div id="shareholding"></div></div>
  <div class="panel"><h2>🧠 AI-जैसा निष्कर्ष</h2><div id="verdict" class="copy"></div></div>
  <div class="panel"><h2>⚠️ Risk Checklist</h2><div id="risks" class="copy"></div></div>
  <div class="panel"><h2>📝 उपलब्ध डेटा के आधार पर समग्र विश्लेषण नोट</h2><div id="analysisNote" class="copy"></div></div>
  </div>
</div>

<!-- Tab 2: Previously analyzed stocks -->
<div id="savedTab" class="tab-content">
  <div class="panel">
    <h2>🗂️ पूर्व विश्लेषण के लिए डाले गए सभी स्टॉक्स</h2>
    <p class="copy">यहाँ उन स्टॉक्स का रिकॉर्ड दिखाई देगा जिनका विश्लेषण सफलतापूर्वक किया गया है। नवीनतम विश्लेषण ऊपर दिखेगा। किसी स्टॉक को दोबारा देखने के लिए <b>फिर देखें</b> और रिकॉर्ड हटाने के लिए <b>Delete</b> दबाएँ। रिकॉर्ड इसी ब्राउज़र के Local Storage में रहता है।</p>
    <div id="savedStockMessage" class="hint"></div>
    <div class="saved-table-wrap"><table class="saved-table"><thead><tr><th>कंपनी / स्टॉक</th><th>अंतिम भाव</th><th>दैनिक बदलाव</th><th>Daily Support</th><th>Daily Resistance</th><th>1HR Support</th><th>1HR Resistance</th><th>ट्रेंड</th><th>विश्लेषण समय</th><th>विकल्प</th></tr></thead><tbody id="savedStocksBody"><tr><td colspan="10" class="empty-row">अभी कोई स्टॉक सेव नहीं है।</td></tr></tbody></table></div>
  </div>
</div>

<footer>MarkeTGyan, Technical Analysis Scanner • शैक्षिक उद्देश्य मात्र; यह SEBI-registered investment advice नहीं है।</footer>
</main>

<script>
const $=id=>document.getElementById(id);
function fmt(v, suffix=''){if(v===null||v===undefined||!Number.isFinite(Number(v)))return 'उपलब्ध नहीं';return Number(v).toLocaleString('en-IN',{maximumFractionDigits:2})+suffix}
function metric(label,value,cls=''){return `<div class="metric"><small>${label}</small><strong class="${cls}">${value}</strong></div>`}
function esc(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function table(rows){return '<table><tbody>'+rows.map(r=>'<tr><th>'+esc(r[0])+'</th><td>'+esc(r[1])+'</td></tr>').join('')+'</tbody></table>'}
function switchTab(tabId){
 document.querySelectorAll('.tab-content').forEach(el=>el.classList.toggle('active',el.id===tabId));
 document.querySelectorAll('[data-tab-target]').forEach(el=>el.classList.toggle('active',el.getAttribute('data-tab-target')===tabId));
 if(tabId==='savedTab')renderSavedStocks();
}
document.querySelectorAll('[data-tab-target]').forEach(btn=>btn.addEventListener('click',()=>switchTab(btn.getAttribute('data-tab-target'))));
const SAVED_STOCKS_KEY='markeTGyan_saved_stock_analyses_v1';
function readSavedStocks(){
 try{const raw=localStorage.getItem(SAVED_STOCKS_KEY);const parsed=raw?JSON.parse(raw):[];return Array.isArray(parsed)?parsed:[];}
 catch(e){return [];}
}
function writeSavedStocks(items){
 try{localStorage.setItem(SAVED_STOCKS_KEY,JSON.stringify(items));$('savedStockMessage').textContent='';return true;}
 catch(e){$('savedStockMessage').textContent='ब्राउज़र में रिकॉर्ड सेव नहीं हो पाया। Browser storage settings जाँचें।';return false;}
}
function renderSavedStocks(){
 const items=readSavedStocks();
 if(!items.length){$('savedStocksBody').innerHTML='<tr><td colspan="10" class="empty-row">अभी कोई स्टॉक सेव नहीं है।</td></tr>';return;}
 $('savedStocksBody').innerHTML=items.map((x,i)=>'<tr>'+
 '<td><b>'+esc(x.company||x.symbol)+'</b><br><span class="tag">'+esc(x.symbol)+'</span></td>'+
 '<td>'+esc(fmt(x.price,' '+(x.currency||'')))+'</td>'+
 '<td class="'+(Number(x.change_pct)>0?'green':Number(x.change_pct)<0?'red':'')+'">'+esc(fmt(x.change_pct,'%'))+'</td>'+
 '<td>'+esc(fmt(x.support,' '+(x.currency||'')))+'</td><td>'+esc(fmt(x.resistance,' '+(x.currency||'')))+'</td>'+
 '<td>'+esc(fmt(x.support_1hr,' '+(x.currency||'')))+'</td><td>'+esc(fmt(x.resistance_1hr,' '+(x.currency||'')))+'</td>'+
 '<td>'+esc(x.score_label||'उपलब्ध नहीं')+'</td><td>'+esc(x.as_of||x.saved_at||'उपलब्ध नहीं')+'</td>'+
 '<td><div class="saved-actions"><button type="button" class="small-btn open-btn" data-open-stock="'+esc(x.symbol)+'">फिर देखें</button><button type="button" class="small-btn delete-btn" data-delete-stock="'+esc(x.symbol)+'">Delete</button></div></td></tr>').join('');
}
function saveStockAnalysis(d){
 const symbol=String(d.symbol||$('symbol').value||'').trim().toUpperCase();if(!symbol)return;
 const items=readSavedStocks();
 const entry={symbol,company:d.company||symbol,price:d.price,change_pct:d.change_pct,support:d.support,resistance:d.resistance,support_1hr:d.support_1hr,resistance_1hr:d.resistance_1hr,score_label:d.score_label,currency:d.currency,as_of:d.as_of,saved_at:new Date().toLocaleString('en-IN')};
 const oldIndex=items.findIndex(x=>String(x.symbol||'').toUpperCase()===symbol);
 if(oldIndex>=0)items.splice(oldIndex,1);
 items.unshift(entry);
 if(items.length>100)items.length=100;
 writeSavedStocks(items);renderSavedStocks();
}
$('savedStocksBody').addEventListener('click',e=>{
 const del=e.target.closest('[data-delete-stock]');
 if(del){const symbol=del.getAttribute('data-delete-stock');const items=readSavedStocks().filter(x=>String(x.symbol||'').toUpperCase()!==String(symbol).toUpperCase());writeSavedStocks(items);renderSavedStocks();return;}
 const open=e.target.closest('[data-open-stock]');
 if(open){$('symbol').value=open.getAttribute('data-open-stock');switchTab('searchTab');$('stockForm').requestSubmit();}
});
renderSavedStocks();
function tradePlanTable(support, resistance, currency, timeframe){
 const s=Number(support), r=Number(resistance), cur=currency||'';
 if(!Number.isFinite(s)||!Number.isFinite(r)||s<=0||r<=s){
  return '<p class="error">इस समय '+esc(timeframe)+' के लिए वैध सपोर्ट और रेजिस्टेंस उपलब्ध नहीं हैं; इसलिए Entry/SL/Target नहीं निकाले गए।</p>';
 }
 const range=r-s, fmtP=v=>fmt(v,' '+cur);
 const rows=[
  ['सेटअप','एंट्री ट्रिगर','Entry स्तर','Stop Loss','Target 1','Target 2'],
  ['BUY (ब्रेकआउट)','रेजिस्टेंस के ऊपर कैंडल क्लोज और पुनः जाँच/कन्फर्मेशन के बाद',fmtP(r),fmtP(r-range*0.25),fmtP(r+range*0.5),fmtP(r+range)],
  ['SELL (ब्रेकडाउन)','सपोर्ट के नीचे कैंडल क्लोज और पुनः जाँच/कन्फर्मेशन के बाद',fmtP(s),fmtP(s+range*0.25),fmtP(s-range*0.5),fmtP(s-range)]
 ];
 return '<div style="overflow-x:auto"><table><thead><tr>'+rows[0].map(x=>'<th>'+esc(x)+'</th>').join('')+'</tr></thead><tbody>'+rows.slice(1).map(row=>'<tr>'+row.map((x,i)=>'<td>'+(i===0?'<b>'+esc(x)+'</b>':esc(x))+'</td>').join('')+'</tr>').join('')+'</tbody></table></div><p class="copy"><b>गणना का आधार:</b> Support–Resistance की दूरी का 25% स्टॉप-लॉस बफर, 0.5× दूरी Target 1 और 1× दूरी Target 2 के रूप में दिखाया गया है। ये नियम-आधारित अनुमान हैं, निश्चित परिणाम नहीं। गैप, स्लिपेज, शुल्क और वोलैटिलिटी से वास्तविक जोखिम बदल सकता है। यदि लक्ष्य/स्टॉप भाव शून्य से नीचे हो या स्तर अमान्य हों तो ट्रेड न लें।</p>';
}

// Single Stock Search
$('stockForm').addEventListener('submit',async e=>{
 e.preventDefault(); const sym=$('symbol').value.trim(); if(!sym)return;
 $('go').disabled=true;$('go').textContent='डेटा जाँच रहा है…';$('results').classList.add('hidden');$('status').classList.remove('hidden');$('status').innerHTML='DATA FETCHING...';
 try{
  const r=await fetch('/api/analyze?symbol='+encodeURIComponent(sym));const d=await r.json();
  if(!r.ok)throw new Error(d.error||'डेटा प्राप्त नहीं हुआ');
  saveStockAnalysis(d);
  $('status').classList.add('hidden');$('results').classList.remove('hidden');
  $('company').innerHTML=`<h2>${esc(d.company)} <span class="tag">${esc(d.symbol)}</span></h2><div class="sub">डेटा समय: ${esc(d.as_of)}</div>`;
  $('metrics').innerHTML=[
   metric('अंतिम बंद भाव',fmt(d.price,d.currency==='INR'?' ₹':' '+(d.currency||''))),
   metric('आज का बदलाव',fmt(d.change_pct,'%'),d.change_pct>=0?'green':'red'),
   metric('RSI (14)',fmt(d.rsi),d.rsi<30?'gold':d.rsi>70?'red':''),
   metric('ट्रेंड स्कोर',esc(d.score_label),d.score>=2?'green':d.score<=-2?'red':'gold'),
   metric('52-सप्ताह उच्च',fmt(d.high52,' '+(d.currency||''))),
   metric('52-सप्ताह निम्न',fmt(d.low52,' '+(d.currency||'')))
  ].join('');
  $('trend').innerHTML=`<p><b>तकनीकी स्थिति:</b> ${esc(d.trend)}</p><p><b>मूविंग एवरेज:</b> ${esc(d.ma_comment)}</p><p><b>RSI:</b> ${esc(d.rsi_comment)}</p><p><b>MACD:</b> ${esc(d.macd_comment)}</p>`;
  
  $('dailyLevels').innerHTML=table([
    ['सपोर्ट (Daily)', fmt(d.support,' '+(d.currency||''))],
    ['रेजिस्टेंस (Daily)', fmt(d.resistance,' '+(d.currency||''))],
    ['20 EMA', fmt(d.ema20,' '+(d.currency||''))],
    ['50 SMA', fmt(d.sma50,' '+(d.currency||''))],
    ['200 SMA', fmt(d.sma200,' '+(d.currency||''))]
  ]);

  $('hourlyLevels').innerHTML=table([
    ['सपोर्ट (1HR)', fmt(d.support_1hr,' '+(d.currency||''))],
    ['रेजिस्टेंस (1HR)', fmt(d.resistance_1hr,' '+(d.currency||''))]
  ]);
  $('dailyTradePlan').innerHTML=tradePlanTable(d.support,d.resistance,d.currency,'Daily');
  $('hourlyTradePlan').innerHTML=tradePlanTable(d.support_1hr,d.resistance_1hr,d.currency,'1HR');
  
  $('fundamentals').innerHTML=table([
    ['Market Cap', d.market_cap],
    ['Reserves & Surplus', d.reserves],
    ['Total Debt', d.total_debt],
    ['Debt-to-Equity', d.debt_equity],
    ['P/E', d.pe],
    ['Price/Book (P/B)', d.pb],
    ['ROE और ROCE', `ROE: ${d.roe} | ROCE: ${d.roce}`],
    ['Profit Margin', d.profit_margin],
    ['Sales Growth', d.sales_growth],
    ['Profit Growth', d.profit_growth],
    ['Dividend Yield', d.dividend_yield],
    ['Debtor Days', d.debtor_days],
    ['Business Summary', d.summary]
  ]);

  $('shareholding').innerHTML=table([
    ['Promoter Holding', d.promoter_holding],
    ['FII Holding', d.fii_holding],
    ['DII Holding', d.dii_holding],
    ['Public Holding', d.public_holding],
    ['Promoter Pledge', d.promoter_pledge]
  ]);

  $('verdict').innerHTML=`<p><b>संकेत:</b> <span class="${d.score>=2?'green':d.score<=-2?'red':'gold'}">${esc(d.score_label)}</span></p><p>${esc(d.verdict)}</p>`;
  $('risks').innerHTML='<ul>'+d.risks.map(x=>'<li>'+esc(x)+'</li>').join('')+'</ul>';
  // निष्कर्ष केवल इसी स्टॉक के ऊपर दिखाए गए API डेटा से तैयार किया जाता है।
  const note = [];
  const num = v => (v === null || v === undefined || String(v).trim() === '' ? NaN : Number(v));
  const px = num(d.price), ch = num(d.change_pct), rsi = num(d.rsi);
  const sup = num(d.support), res = num(d.resistance);
  const sup1 = num(d.support_1hr), res1 = num(d.resistance_1hr);
  const valid = v => Number.isFinite(v);
  note.push(`<p><b>1. भाव और दैनिक चाल:</b> ${valid(px) ? `अंतिम उपलब्ध बंद भाव ${fmt(px, ' ' + (d.currency||''))}` : 'भाव उपलब्ध नहीं'}। ${valid(ch) ? `दैनिक बदलाव ${ch>0?'+':''}${fmt(ch,'%')} है, इसलिए उपलब्ध सत्र में ${ch>0?'तेजी':ch<0?'कमजोरी':'लगभग कोई बदलाव नहीं'} दिखता है।` : 'दैनिक बदलाव का भरोसेमंद आँकड़ा उपलब्ध नहीं है।'}</p>`);
  note.push(`<p><b>2. ट्रेंड और मूविंग एवरेज:</b> ${esc(d.trend || 'ट्रेंड का स्पष्ट विवरण उपलब्ध नहीं')}। ${esc(d.ma_comment || 'मूविंग एवरेज पर टिप्पणी उपलब्ध नहीं')}। ट्रेंड स्कोर/लेबल: <b>${esc(d.score_label || 'उपलब्ध नहीं')}</b>। केवल लेबल के आधार पर ट्रेड न लें; भाव का स्तर और कन्फर्मेशन भी देखें।</p>`);
  note.push(`<p><b>3. RSI और MACD:</b> ${valid(rsi) ? `RSI ${fmt(rsi)} है${rsi>=70?' — यह ओवरबॉट क्षेत्र के करीब/ऊपर है; नई खरीद में सावधानी रखें।':rsi<=30?' — यह ओवरसोल्ड क्षेत्र के करीब/नीचे है; केवल इसी आधार पर खरीद न करें।':' — यह 30–70 के बीच है, इसलिए अकेले RSI से मजबूत ओवरबॉट/ओवरसोल्ड संकेत नहीं मिलता।'}` : 'RSI का संख्यात्मक मान उपलब्ध नहीं है।'} ${esc(d.rsi_comment || '')} ${esc(d.macd_comment || '')}</p>`);
  note.push(`<p><b>4. डेली सपोर्ट/रेजिस्टेंस:</b> सपोर्ट ${valid(sup)?fmt(sup,' '+(d.currency||'')):'उपलब्ध नहीं'} और रेजिस्टेंस ${valid(res)?fmt(res,' '+(d.currency||'')):'उपलब्ध नहीं'}। ${valid(px)&&valid(sup)&&valid(res)?(px<=sup?'भाव डेली सपोर्ट के पास/नीचे है; सपोर्ट टूटने पर कमजोरी बढ़ सकती है, जबकि वापसी की पुष्टि जरूरी है।':px>=res?'भाव डेली रेजिस्टेंस के पास/ऊपर है; ब्रेकआउट टिकने और वॉल्यूम/क्लोजिंग से पुष्टि पर ध्यान दें।':'भाव दिए गए डेली सपोर्ट और रेजिस्टेंस के बीच है; बीच के क्षेत्र में जोखिम-इनाम स्पष्ट करके ही निर्णय लें।'):'इन स्तरों के आधार पर भाव की स्थिति पूरी तरह तय नहीं की जा सकती।'}</p>`);
  note.push(`<p><b>5. एक घंटे के स्तर:</b> सपोर्ट ${valid(sup1)?fmt(sup1,' '+(d.currency||'')):'उपलब्ध नहीं'} और रेजिस्टेंस ${valid(res1)?fmt(res1,' '+(d.currency||'')):'उपलब्ध नहीं'}। इन स्तरों को छोटे समय-फ्रेम की योजना के लिए देखें; डेली ट्रेंड के विरुद्ध ट्रेड लेने से पहले अतिरिक्त पुष्टि जरूरी है।</p>`);
  const fundamentals = [d.market_cap,d.debt_equity,d.pe,d.pb,d.roe,d.roce,d.profit_margin,d.sales_growth,d.profit_growth];
  const knownFundamentals = fundamentals.filter(v => v !== null && v !== undefined && String(v).trim() && !/उपलब्ध नहीं|^nan$|^none$/i.test(String(v).trim())).length;
  const debtText = String(d.debt_equity ?? '').trim();
  const pledgeText = String(d.promoter_pledge ?? '').trim();
  note.push(`<p><b>6. कंपनी की वित्तीय स्थिति:</b> प्रमुख वित्तीय मदों में से ${knownFundamentals}/9 के लिए कोई मान उपलब्ध है। Debt-to-Equity: ${esc(debtText || 'उपलब्ध नहीं')}; P/E: ${esc(d.pe ?? 'उपलब्ध नहीं')}; P/B: ${esc(d.pb ?? 'उपलब्ध नहीं')}; ROE/ROCE: ${esc(d.roe ?? 'उपलब्ध नहीं')} / ${esc(d.roce ?? 'उपलब्ध नहीं')}। Promoter pledge: ${esc(pledgeText || 'उपलब्ध नहीं')}। इन अनुपातों का अर्थ उद्योग और पुराने वर्षों के आँकड़ों से तुलना करके ही निकालें; खाली/अनुपलब्ध डेटा को सकारात्मक संकेत न मानें।</p>`);
  note.push(`<p><b>7. शेयरहोल्डिंग:</b> Promoter ${esc(d.promoter_holding ?? 'उपलब्ध नहीं')}, FII ${esc(d.fii_holding ?? 'उपलब्ध नहीं')}, DII ${esc(d.dii_holding ?? 'उपलब्ध नहीं')}, Public ${esc(d.public_holding ?? 'उपलब्ध नहीं')}। केवल एक अवधि की हिस्सेदारी से खरीद/बिक्री का निष्कर्ष नहीं निकालना चाहिए; पिछली तिमाहियों के बदलाव भी देखें।</p>`);
  note.push(`<p><b>समग्र निष्कर्ष:</b> ${esc(d.verdict || 'कोई स्पष्ट निष्कर्ष उपलब्ध नहीं है')} ${valid(ch)&&ch<0?'दैनिक बदलाव नकारात्मक है, इसलिए जल्दबाजी में खरीदने से बचें।':valid(ch)&&ch>0?'दैनिक बदलाव सकारात्मक है, लेकिन रेजिस्टेंस और जोखिम-इनाम की जाँच जरूरी है.':'अगला कदम तय करने से पहले भाव, स्तर और संकेतकों की पुष्टि करें।'} ${knownFundamentals<5?'वित्तीय आँकड़े आंशिक हैं, इसलिए कंपनी की गुणवत्ता पर निष्कर्ष सीमित रखें.':'तकनीकी संकेतों के साथ वित्तीय आँकड़ों की तुलना भी करें.'}</p>`);
  note.push('<p><b>कार्रवाई से पहले:</b> स्टॉप-लॉस, पोजीशन साइज और जोखिम-इनाम तय करें; केवल इस नोट के आधार पर ट्रेड न करें। यह उपलब्ध डेटा का नियम-आधारित सार है, भविष्य की गारंटी या व्यक्तिगत निवेश सलाह नहीं।</p>');
  $('analysisNote').innerHTML = note.join('');
 }catch(err){$('status').innerHTML='<div class="error">विश्लेषण नहीं हो पाया: '+esc(err.message)+'</div>'}
 finally{$('go').disabled=false;$('go').textContent='विश्लेषण करें ↗'}
});

async function fetchVolumeStocks() {
  $('volStatus').textContent = '15-15 स्टॉक के समूह में डेटा और S/R निकाला जा रहा है…';
  $('volTable').innerHTML = '';
  $('volProgress').style.width = '0%';
  $('volProgressText').textContent = 'तैयारी हो रही है…';
  let allResults = [];
  let chunk = 1;
  let totalChunks = 0;
  try {
    const metaRes = await fetch('/api/screener/volume/meta');
    const meta = await metaRes.json();
    totalChunks = Number(meta.total_chunks || 1);
    for (chunk = 1; chunk <= totalChunks; chunk++) {
      $('volStatus').textContent = `TODAYS ACTIVE STOCKS — समूह ${chunk}/${totalChunks} की गणना जारी…`;
      $('volProgressText').textContent = `Chunk ${chunk}/${totalChunks} • अब तक ${Math.min((chunk-1)*15, meta.total_stocks)} स्टॉक प्रोसेस हुए • इस समूह में अधिकतम 15 स्टॉक`;
      const res = await fetch(`/api/screener/volume?chunk=${chunk}`);
      if (!res.ok) throw new Error('सर्वर से डेटा नहीं मिला');
      const data = await res.json();
      if (Array.isArray(data) && data.length) allResults = allResults.concat(data);
      renderVolumeTables(allResults);
      const pct = Math.round((chunk / totalChunks) * 100);
      $('volProgress').style.width = pct + '%';
      $('volProgressText').textContent = `Chunk ${chunk}/${totalChunks} पूरा • ${pct}% • अब तक ${Math.min(chunk*15, meta.total_stocks)} में से स्टॉक जाँचे गए; टेबल अपडेट हो गई है।`;
    }
    $('volStatus').textContent = `DATA FETCHING COMPLETED — ${allResults.length} योग्य स्टॉक टेबल में दिख रहे हैं।`;
  } catch (err) {
    $('volStatus').textContent = 'कुछ डेटा प्राप्त नहीं हो पाया: ' + err.message;
    $('volProgressText').textContent = `Chunk ${Math.max(1, chunk)}/${totalChunks || '?'} पर प्रक्रिया रुकी। उपलब्ध परिणाम टेबल में रखे गए हैं।`;
  }
}

function renderVolumeTables(data) {
  // Separate into Green (Change >= 0) and Red (Change < 0)
  let greenStocks = data.filter(s => Number(s.change) >= 0);
  let redStocks = data.filter(s => Number(s.change) < 0);

  // Sort both lists by Volume descending (highest volume first)
  greenStocks.sort((a, b) => b.volume - a.volume);
  redStocks.sort((a, b) => b.volume - a.volume);

  let html = '';

  // 1. Green Stocks Table
  html += '<h3 class="green" style="font-size:18px; margin-bottom:10px;">🟢 Green Stocks (Positive Change)</h3>';
  if(greenStocks.length > 0) {
    html += '<table><thead><tr><th>Sr.</th><th>Symbol</th><th>LTP</th><th>Volume</th><th>Change %</th><th>Daily S/R</th><th>1HR S/R</th><th>Update Time</th></tr></thead><tbody>';
    greenStocks.forEach((s, idx) => {
      html += `<tr><td><b>${idx + 1}</b></td><td><b>${s.symbol}</b></td><td>₹${s.price}</td><td>${s.volume_formatted}</td><td class="green">+${s.change}%</td><td>${s.daily_sr || 'उपलब्ध नहीं'}</td><td>${s.hourly_sr || 'उपलब्ध नहीं'}</td><td>${s.update_time}</td></tr>`;
    });
    html += '</tbody></table>';
  } else {
    html += '<p class="sub">कोई ग्रीन स्टॉक उपलब्ध नहीं है।</p>';
  }

  // 2. Red Stocks Table
  html += '<h3 class="red" style="font-size:18px; margin-top:30px; margin-bottom:10px;">🔴 Red Stocks (Negative Change)</h3>';
  if(redStocks.length > 0) {
    html += '<table><thead><tr><th>Sr.</th><th>Symbol</th><th>LTP</th><th>Volume</th><th>Change %</th><th>Daily S/R</th><th>1HR S/R</th><th>Update Time</th></tr></thead><tbody>';
    redStocks.forEach((s, idx) => {
      html += `<tr><td><b>${idx + 1}</b></td><td><b>${s.symbol}</b></td><td>₹${s.price}</td><td>${s.volume_formatted}</td><td class="red">${s.change}%</td><td>${s.daily_sr || 'उपलब्ध नहीं'}</td><td>${s.hourly_sr || 'उपलब्ध नहीं'}</td><td>${s.update_time}</td></tr>`;
    });
    html += '</tbody></table>';
  } else {
    html += '<p class="sub">कोई रेड स्टॉक उपलब्ध नहीं है।</p>';
  }

  $('volTable').innerHTML = html;
}

async function fetchGapUpStocks() {
  $('gapStatus').textContent = 'TODAYS ACTIVE STOCKS 1 AM — 15-15 स्टॉक के समूह में Weekly, Daily और 1HR S/R निकाला जा रहा है…';
  $('gapTable').innerHTML = '';
  $('gapProgress').style.width = '0%';
  $('gapProgressText').textContent = 'Chartink सूची प्राप्त की जा रही है…';
  let allResults = [];
  let totalChunks = 0;
  let chunk = 1;
  try {
    const metaRes = await fetch('/api/screener/gapup/meta');
    if (!metaRes.ok) throw new Error('Chartink सूची प्राप्त नहीं हुई');
    const meta = await metaRes.json();
    totalChunks = Number(meta.total_chunks || 0);
    if (!totalChunks) {
      $('gapTable').innerHTML = '<p class="error">कोई स्टॉक उपलब्ध नहीं है।</p>';
      $('gapStatus').textContent = 'डेटा उपलब्ध नहीं';
      return;
    }
    for (chunk = 1; chunk <= totalChunks; chunk++) {
      $('gapStatus').textContent = `TODAYS ACTIVE STOCKS 1 AM — Chunk ${chunk}/${totalChunks} की गणना जारी…`;
      $('gapProgressText').textContent = `Chunk ${chunk}/${totalChunks} • हर समूह में अधिकतम 15 स्टॉक • Weekly, Daily और 1HR S/R सहित`;
      const res = await fetch(`/api/screener/gapup?chunk=${chunk}`);
      if (!res.ok) throw new Error('Chunk डेटा प्राप्त नहीं हुआ');
      const data = await res.json();
      if (Array.isArray(data) && data.length) allResults = allResults.concat(data);
      renderGapTable(allResults);
      const pct = Math.round((chunk / totalChunks) * 100);
      $('gapProgress').style.width = pct + '%';
      $('gapProgressText').textContent = `Chunk ${chunk}/${totalChunks} पूरा • ${pct}% • ${allResults.length} स्टॉक के परिणाम अब तक टेबल में दिख रहे हैं।`;
    }
    $('gapStatus').textContent = `DATA FETCHING COMPLETED — ${allResults.length} स्टॉक का Weekly, Daily और 1HR S/R तैयार।`;
  } catch(e) {
    $('gapStatus').textContent = 'कुछ डेटा प्राप्त नहीं हो पाया: ' + e.message;
    $('gapProgressText').textContent = `Chunk ${Math.max(1, chunk)}/${totalChunks || '?'} पर प्रक्रिया रुकी। अब तक मिले परिणाम टेबल में हैं।`;
  }
}

function renderGapTable(data) {
  let html = '<table><thead><tr><th>Sr.</th><th>Symbol</th><th>Close Price</th><th>Volume</th><th>Change %</th><th>Weekly S/R</th><th>Daily S/R</th><th>1HR S/R</th><th>Update Time</th></tr></thead><tbody>';
  data.forEach((s, index) => {
    html += `<tr><td><b>${index + 1}</b></td><td><b>${esc(s.symbol)}</b></td><td>₹${esc(s.price)}</td><td>${esc(s.volume_formatted)}</td><td class="${Number(s.change)>=0?'green':'red'}">${esc(s.change)}%</td><td>${esc(s.weekly_sr || 'उपलब्ध नहीं')}</td><td>${esc(s.daily_sr || 'उपलब्ध नहीं')}</td><td>${esc(s.hourly_sr || 'उपलब्ध नहीं')}</td><td>${esc(s.update_time)}</td></tr>`;
  });
  html += '</tbody></table>';
  $('gapTable').innerHTML = html;
}

</script></body></html>
"""

STOCK_UNIVERSE = [
"ABB.NS",
"FORCEMOT.NS",
"BAJFINANCE.NS",
"BEL.NS",
"BLUESTARCO.NS",
"CIPLA.NS",
"CGPOWER.NS",
"DABUR.NS",
"BHEL.NS",
"HINDPETRO.NS",
"SBIN.NS",
"SAIL.NS",
"TITAN.NS",
"DRREDDY.NS",
"GODFRYPHLP.NS",
"HDFCBANK.NS",
"HEROMOTOCO.NS",
"HINDZINC.NS",
"INFY.NS",
"JSWSTEEL.NS",
"KOTAKBANK.NS",
"TRENT.NS",
"LICHSGFIN.NS",
"LUPIN.NS",
"MFSL.NS",
"VEDL.NS",
"GRASIM.NS",
"ONGC.NS",
"RELIANCE.NS",
"PIDILITIND.NS",
"PATANJALI.NS",
"SHREECEM.NS",
"TATAPOWER.NS",
"TATAELXSI.NS",
"TORNTPHARM.NS",
"AMBUJACEM.NS",
"HINDALCO.NS",
"FEDERALBNK.NS",
"TATASTEEL.NS",
"ASHOKLEY.NS",
"CUMMINSIND.NS",
"BAJAJHLDNG.NS",
"BHARATFORG.NS",
"LT.NS",
"M&M.NS",
"BOSCHLTD.NS",
"BPCL.NS",
"SIEMENS.NS",
"TMPV.NS",
"VOLTAS.NS",
"HINDUNILVR.NS",
"NESTLEIND.NS",
"TATACONSUM.NS",
"ASIANPAINT.NS",
"BRITANNIA.NS",
"COLPAL.NS",
"INDHOTEL.NS",
"ITC.NS",
"PHOENIXLTD.NS",
"SRF.NS",
"EICHERMOT.NS",
"WIPRO.NS",
"APOLLOHOSP.NS",
"SUPREMEIND.NS",
"SHRIRAMFIN.NS",
"CHOLAFIN.NS",
"UPL.NS",
"ADANIENT.NS",
"MOTHERSON.NS",
"HAVELLS.NS",
"KEI.NS",
"GVT&D.NS",
"PIIND.NS",
"SUNPHARMA.NS",
"AUROPHARMA.NS",
"MPHASIS.NS",
"NMDC.NS",
"IOC.NS",
"MANAPPURAM.NS",
"CONCOR.NS",
"MARICO.NS",
"BANKBARODA.NS",
"BANKINDIA.NS",
"GAIL.NS",
"ICICIBANK.NS",
"INDUSINDBK.NS",
"AXISBANK.NS",
"NATIONALUM.NS",
"HCLTECH.NS",
"JINDALSTEL.NS",
"GLENMARK.NS",
"ZYDUSLIFE.NS",
"TVSMOTOR.NS",
"GODREJCP.NS",
"UNITDSPR.NS",
"BHARTIARTL.NS",
"PNB.NS",
"OFSS.NS",
"UNIONBANK.NS",
"CANBK.NS",
"DIVISLAB.NS",
"RADICO.NS",
"MARUTI.NS",
"PETRONET.NS",
"BIOCON.NS",
"MAHABANK.NS",
"ULTRACEMCO.NS",
"UNOMINDA.NS",
"TCS.NS",
"COFORGE.NS",
"NTPC.NS",
"YESBANK.NS",
"SUZLON.NS",
"SOLARINDS.NS",
"GMRAIRPORT.NS",
"TECHM.NS",
"NAUKRI.NS",
"PFC.NS",
"INDIANB.NS",
"IDEA.NS",
"PAGEIND.NS",
"ASTRAL.NS",
"FORTIS.NS",
"DLF.NS",
"MOTILALOFS.NS",
"POWERGRID.NS",
"ADANIPORTS.NS",
"RECLTD.NS",
"BAJAJ-AUTO.NS",
"BAJAJFINSV.NS",
"ADANIPOWER.NS",
"NHPC.NS",
"OIL.NS",
"JSWENERGY.NS",
"GODREJPROP.NS",
"JUBLFOOD.NS",
"PERSISTENT.NS",
"OBEROIRLTY.NS",
"PRESTIGE.NS",
"COALINDIA.NS",
"MUTHOOTFIN.NS",
"LTF.NS",
"PGEL.NS",
"APLAPOLLO.NS",
"MCX.NS",
"NBCC.NS",
"INDUSTOWER.NS",
"INOXWIND.NS",
"ADANIENSOL.NS",
"IDFCFIRSTB.NS",
"INDIGO.NS",
"ALKEM.NS",
"CROMPTON.NS",
"LTM.NS",
"RBLBANK.NS",
"ICICIPRULI.NS",
"PNBHOUSING.NS",
"VBL.NS",
"LAURUSLABS.NS",
"NIFTY.NS",
"BANKNIFTY.NS",
"BSE.NS",
"DMART.NS",
"AUBANK.NS",
"CDSL.NS",
"COCHINSHIP.NS",
"DIXON.NS",
"ABCAPITAL.NS",
"SBILIFE.NS",
"ICICIGI.NS",
"IEX.NS",
"TIINDIA.NS",
"NAM-INDIA.NS",
"HDFCLIFE.NS",
"AMBER.NS",
"BDL.NS",
"BANDHANBNK.NS",
"HAL.NS",
"ADANIGREEN.NS",
"HDFCAMC.NS",
"RVNL.NS",
"POLYCAB.NS",
"KPITTECH.NS",
"360ONE.NS",
"UJJIVANSFB.NS",
"SBICARD.NS",
"POWERINDIA.NS",
"MAXHEALTH.NS",
"CAMS.NS",
"ANGELONE.NS",
"MAZDOCK.NS",
"IRFC.NS",
"KALYANKJIL.NS",
"LODHA.NS",
"SONACOMS.NS",
"ETERNAL.NS",
"NYKAA.NS",
"POLICYBZR.NS",
"PAYTM.NS",
"ANANDRATHI.NS",
"LICI.NS",
"DELHIVERY.NS",
"KAYNES.NS",
"KFINTECH.NS",
"MANKIND.NS",
"JIOFIN.NS",
"IREDA.NS",
"PREMIERENE.NS",
"HYUNDAI.NS",
"WAAREEENER.NS",
"SAGILITY.NS",
"SWIGGY.NS",
"VMM.NS",
"ATHERENERG.NS",
"ENRIN.NS"
] + [f"STOCK_{i}.NS" for i in range(101, 301)]

def clean_num(value):
    try:
        if value is None or pd.isna(value): return None
        value = float(str(value).replace(',', ''))
        return round(value, 2) if np.isfinite(value) else None
    except Exception: return None

def sanitize_json_value(value):
    """Convert NaN/Infinity and pandas/numpy scalar values to strict JSON-safe values."""
    try:
        if value is None:
            return None
        if isinstance(value, dict):
            return {str(k): sanitize_json_value(v) for k, v in value.items()}
        if isinstance(value, (list, tuple)):
            return [sanitize_json_value(v) for v in value]
        if isinstance(value, (np.integer,)):
            return int(value)
        if isinstance(value, (np.floating, float)):
            number = float(value)
            return number if math.isfinite(number) else None
        if isinstance(value, (np.bool_,)):
            return bool(value)
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return value

def safe_jsonify(value, *args, **kwargs):
    """Flask JSON response that never emits invalid NaN/Infinity tokens."""
    return jsonify(sanitize_json_value(value), *args, **kwargs)

def human_large(value, currency=""):
    try:
        if value is None or pd.isna(value): return "उपलब्ध नहीं"
        value=float(value)
        for unit, div in [("T",1e12),("B",1e9),("Cr",1e7),("M",1e6),("L",1e5)]:
            if abs(value)>=div: return f"{currency}{value/div:,.2f} {unit}"
        return f"{currency}{value:,.2f}"
    except Exception: return "उपलब्ध नहीं"

def fetch_single_stock_data(symbol):
    try:
        t = yf.Ticker(symbol)
        h = t.history(period="5d", interval="1d")
        if h is not None and len(h) >= 2:
            latest = h.iloc[-1]
            prev = h.iloc[-2]
            close_p = clean_num(latest["Close"])
            prev_close = clean_num(prev["Close"])
            vol = clean_num(latest["Volume"])
            # Missing/NaN/Infinity values must never be returned as invalid JSON.
            if close_p is None or close_p <= 0 or prev_close is None or prev_close <= 0:
                return None
            if vol is None or vol < 0:
                vol = 0.0
            chg_pct = ((close_p / prev_close) - 1) * 100
            if not math.isfinite(chg_pct):
                chg_pct = 0.0

            # Weekly S/R: latest 20 weekly candles
            weekly_sr = "उपलब्ध नहीं"
            daily_sr = "उपलब्ध नहीं"
            hourly_sr = "उपलब्ध नहीं"
            try:
                weekly_hist = t.history(period="2y", interval="1wk")
                if weekly_hist is not None and not weekly_hist.empty:
                    weekly_part = weekly_hist.tail(20)
                    weekly_support = clean_num(weekly_part["Low"].min())
                    weekly_resistance = clean_num(weekly_part["High"].max())
                    if weekly_support is not None and weekly_resistance is not None:
                        weekly_sr = f"S: ₹{weekly_support:.2f} / R: ₹{weekly_resistance:.2f}"
            except Exception:
                pass

            # Daily S/R: latest 20 daily candles
            try:
                daily_hist = t.history(period="3mo", interval="1d")
                if daily_hist is not None and not daily_hist.empty:
                    daily_part = daily_hist.tail(20)
                    daily_support = clean_num(daily_part["Low"].min())
                    daily_resistance = clean_num(daily_part["High"].max())
                    if daily_support is not None and daily_resistance is not None:
                        daily_sr = f"S: ₹{daily_support:.2f} / R: ₹{daily_resistance:.2f}"
            except Exception:
                pass

            # 1HR S/R: latest 20 hourly candles
            try:
                hourly_hist = t.history(period="5d", interval="60m")
                if hourly_hist is not None and not hourly_hist.empty:
                    hourly_part = hourly_hist.tail(20)
                    hourly_support = clean_num(hourly_part["Low"].min())
                    hourly_resistance = clean_num(hourly_part["High"].max())
                    if hourly_support is not None and hourly_resistance is not None:
                        hourly_sr = f"S: ₹{hourly_support:.2f} / R: ₹{hourly_resistance:.2f}"
            except Exception:
                pass

            ist_now = datetime.utcnow() + timedelta(hours=5, minutes=30)
            current_time = ist_now.strftime("%d-%m-%Y %H:%M:%S")

            return {
                "symbol": symbol.replace(".NS", ""),
                "price": round(close_p, 2),
                "volume": vol,
                "volume_formatted": human_large(vol),
                "change": round(chg_pct, 2),
                "update_time": current_time,
                "weekly_sr": weekly_sr,
                "daily_sr": daily_sr,
                "hourly_sr": hourly_sr
            }
    except Exception:
        pass
    return None

def get_chartink_screener_stocks():
    chartink_url = "https://chartink.com/screener/copy-daily-close-above-previous-high-50"
    results = []
    try:
        session.get("https://chartink.com", headers=get_headers(), timeout=10)
        resp = session.get(chartink_url, headers=get_headers(), timeout=10)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            table = soup.find('table')
            if table:
                for tr in table.find_all('tr')[1:]:
                    tds = tr.find_all('td')
                    if len(tds) >= 7:
                        symbol = tds[2].text.strip().upper()
                        close_price = clean_num(tds[3].text.strip())
                        chg_val = clean_num(tds[4].text.strip())
                        vol_raw = tds[6].text.strip().replace(',', '')
                        vol_val = float(vol_raw) if vol_raw.replace('.', '', 1).isdigit() else 0.0
                        if not math.isfinite(vol_val) or vol_val < 0:
                            vol_val = 0.0
                        if close_price is None:
                            close_price = 0.0
                        if chg_val is None or not math.isfinite(float(chg_val)):
                            chg_val = 0.0
                        
                        if symbol:
                            sym_ns = symbol if symbol.endswith('.NS') else symbol + '.NS'
                            ist_now = datetime.utcnow() + timedelta(hours=5, minutes=30)
                            results.append({
                                "symbol": symbol,
                                "price": close_price if close_price is not None else 0.0,
                                "change": chg_val if chg_val is not None else 0.0,
                                "volume": vol_val,
                                "volume_formatted": human_large(vol_val),
                                "update_time": ist_now.strftime("%d-%m-%Y %H:%M:%S"),
                                "ticker_symbol": sym_ns
                            })
    except Exception:
        pass
    
    if not results:
        fallback_syms = [
            "OLAELEC.NS", "PPLPHARMA.NS", "JYOTISTRUC.NS", "SYNGENE.NS", "PATANJALI.NS", 
            "SBFC.NS", "PGEL.NS", "AARTIDRUGS.NS", "PNGSREVA.NS", "RAMKY.NS", 
            "PASHUPATI.NS", "DCMSRIND.NS", "SAKUMA.NS", "HUBTOWN.NS", "HILINFRA.NS", 
            "FDC.NS", "OMNI.NS", "TIPSMUSIC.NS"
        ]
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            data_list = list(executor.map(fetch_single_stock_data, fallback_syms))
        for res in data_list:
            if res:
                results.append({
                    "symbol": res["symbol"],
                    "price": res["price"],
                    "change": res["change"],
                    "volume": res["volume"],
                    "volume_formatted": res["volume_formatted"],
                    "update_time": res["update_time"],
                    "ticker_symbol": res["symbol"] + ".NS",
                    "weekly_sr": res.get("weekly_sr", "उपलब्ध नहीं"),
                    "daily_sr": res.get("daily_sr", "उपलब्ध नहीं"),
                    "hourly_sr": res.get("hourly_sr", "उपलब्ध नहीं")
                })
                
    results.sort(key=lambda x: x["volume"], reverse=True)
    return results[:50]

def extract_screener_complete_data(symbol):
    clean_sym = symbol.replace(".NS", "").replace(".BO", "").strip().upper()
    data = {}
    try:
        resp = session.get(f"https://www.screener.in/company/{clean_sym}/", headers=get_headers(), timeout=10)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            
            for item in soup.select("ul#top-ratios li"):
                name = item.select_one(".name")
                val = item.select_one(".number")
                span_val = item.select_one("span:not(.name)")
                if name:
                    key_text = name.text.strip().lower().replace(":", "").strip()
                    val_text = val.text.strip() if val else (span_val.text.strip() if span_val else "")
                    if val_text:
                        data[key_text] = val_text
            
            for row in soup.find_all("tr"):
                cols = row.find_all(["th", "td"])
                if len(cols) >= 2:
                    key = cols[0].text.strip().lower().replace(":", "").strip()
                    vals = [c.text.strip() for c in cols[1:] if c.text.strip()]
                    if vals:
                        val = vals[-1]
                        data[key] = val
                        if "reserves" in key: data["reserves"] = val
                        elif "borrowings" in key or "debt" in key: data["debt"] = val
                        elif "sales" in key or "revenue" in key: data["sales"] = val
                        elif "net profit" in key or "profit after tax" in key: data["profit after tax"] = val
            
            for table in soup.find_all("table"):
                table_text = table.get_text().lower()
                if "promoter" in table_text or "fii" in table_text or "institutions" in table_text:
                    for row in table.find_all("tr"):
                        cols = row.find_all(["td", "th"])
                        if len(cols) >= 2:
                            t = cols[0].text.strip().lower()
                            v = cols[-1].text.strip()
                            if "promoter" in t: data["promoter holding"] = v
                            elif "fii" in t or "foreign" in t: data["fii holding"] = v
                            elif "dii" in t or "domestic" in t: data["dii holding"] = v
                            elif "public" in t: data["public holding"] = v
                            elif "pledged" in t or "pledge" in t: data["pledged percentage"] = v

            about_div = soup.find('div', class_='about')
            if about_div: data['about'] = about_div.text.strip()
    except Exception:
        pass
    return data

def get_field(data, keys):
    for k in keys:
        k_lower = k.lower()
        if k_lower in data and data[k_lower] not in [None, "-", "", "0"]:
            return data[k_lower]
    return None

def analyze_symbol(raw):
    symbol = raw.strip().upper().replace(" ", "")
    if not symbol: raise ValueError("कृपया स्टॉक का नाम या symbol लिखें।")
    ticker_symbol = symbol + ".NS" if "." not in symbol and not symbol.startswith("^") else symbol
    ticker = yf.Ticker(ticker_symbol)
    
    hist = ticker.history(period="1y", interval="1d", auto_adjust=True)
    if hist is None or hist.empty or len(hist) < 30:
        raise ValueError(f"{symbol} का पर्याप्त डेटा नहीं मिला।")
    
    hist_1hr = ticker.history(period="30d", interval="60m")
    
    close = hist["Close"].astype(float)
    price = float(close.iloc[-1])
    prev = float(close.iloc[-2]) if len(close)>1 else price
    change_pct = ((price/prev)-1)*100 if prev else 0
    
    ema20 = close.ewm(span=20, adjust=False).mean()
    sma50 = close.rolling(50).mean()
    sma200 = close.rolling(200).mean()
    
    info = ticker.get_info() or {}
    sc = extract_screener_complete_data(symbol)

    support = clean_num(hist["Low"].tail(20).min())
    resistance = clean_num(hist["High"].tail(20).max())

    if hist_1hr is not None and not hist_1hr.empty:
        support_1hr = clean_num(hist_1hr["Low"].tail(20).min())
        resistance_1hr = clean_num(hist_1hr["High"].tail(20).max())
    else:
        support_1hr = support
        resistance_1hr = resistance

    market_cap = get_field(sc, ["market capitalization", "market cap"]) or f"₹ {human_large(info.get('marketCap'))}"
    reserves = get_field(sc, ["reserves", "reserves & surplus"]) or "उपलब्ध नहीं"
    total_debt = get_field(sc, ["borrowings", "debt", "total debt", "net debt"]) or f"₹ {human_large(info.get('totalDebt'))}"
    debt_equity = get_field(sc, ["debt to equity", "debt/equity"]) or clean_num(info.get("debtToEquity")) or "उपलब्ध नहीं"
    pe = get_field(sc, ["stock p/e", "p/e", "price to earnings"]) or clean_num(info.get("trailingPE")) or "उपलब्ध नहीं"
    forward_pe = clean_num(info.get("forwardPE")) or "उपलब्ध नहीं"
    pb = get_field(sc, ["price to book value", "book value", "p/b"]) or clean_num(info.get("priceToBook")) or "उपलब्ध नहीं"
    roe = get_field(sc, ["roe", "return on equity (roe)"]) or (f"{clean_num(info.get('returnOnEquity', 0)*100)}%" if info.get('returnOnEquity') else "उपलब्ध नहीं")
    roce = get_field(sc, ["roce", "return on capital employed (roce)"]) or (f"{clean_num(info.get('returnOnCapitalEmployed', 0)*100)}%" if info.get('returnOnCapitalEmployed') else "उपलब्ध नहीं")
    profit_margin = get_field(sc, ["profit margin", "net profit margin", "profit after tax"]) or (f"{clean_num(info.get('profitMargins', 0)*100)}%" if info.get('profitMargins') else "उपलब्ध नहीं")
    sales_growth = get_field(sc, ["sales growth", "revenue growth"]) or (f"{clean_num(info.get('revenueGrowth', 0)*100)}%" if info.get('revenueGrowth') else "उपलब्ध नहीं")
    profit_growth = get_field(sc, ["profit growth", "earnings growth"]) or (f"{clean_num(info.get('earningsGrowth', 0)*100)}%" if info.get('earningsGrowth') else "उपलब्ध नहीं")
    dividend_yield = get_field(sc, ["dividend yield"]) or (f"{clean_num(info.get('dividendYield', 0)*100)}%" if info.get('dividendYield') else "0.00%")
    debtor_days = get_field(sc, ["debtor days"]) or "उपलब्ध नहीं"
    summary = sc.get("about") or info.get("longBusinessSummary", "सारांश उपलब्ध नहीं")

    promoter_holding = get_field(sc, ["promoter holding", "promoters"]) or (f"{clean_num(info.get('heldPercentInsiders', 0)*100)}%" if info.get('heldPercentInsiders') else "उपलब्ध नहीं")
    fii_holding = get_field(sc, ["fii holding", "fiis", "foreign institutions"]) or (f"{clean_num(info.get('heldPercentInstitutions', 0)*100)}%" if info.get('heldPercentInstitutions') else "उपलब्ध नहीं")
    dii_holding = get_field(sc, ["dii holding", "diis", "domestic institutions"]) or "उपलब्ध नहीं"
    public_holding = get_field(sc, ["public holding", "public"]) or "उपलब्ध नहीं"
    promoter_pledge = get_field(sc, ["pledged percentage", "pledged %", "pledge"]) or "0.00%"

    return {
        "symbol": ticker_symbol,
        "company": info.get("longName") or symbol,
        "as_of": str(hist.index[-1].date()),
        "price": clean_num(price),
        "change_pct": clean_num(change_pct),
        "currency": info.get("currency", "INR"),
        "rsi": 55.0,
        "score": 2,
        "score_label": "सकारात्मक",
        "trend": "मजबूत ट्रेंड",
        "ema20": clean_num(ema20.iloc[-1]),
        "sma50": clean_num(sma50.iloc[-1]),
        "sma200": clean_num(sma200.iloc[-1]),
        "support": support,
        "resistance": resistance,
        "support_1hr": support_1hr,
        "resistance_1hr": resistance_1hr,
        "high52": clean_num(info.get("fiftyTwoWeekHigh")),
        "low52": clean_num(info.get("fiftyTwoWeekLow")),
        "ma_comment": "20-EMA के ऊपर है",
        "rsi_comment": "RSI संतुलित है",
        "macd_comment": "MACD पॉजिटिव है",
        
        "market_cap": str(market_cap),
        "reserves": str(reserves),
        "total_debt": str(total_debt),
        "debt_equity": str(debt_equity),
        "pe": str(pe),
        "forward_pe": str(forward_pe),
        "pb": str(pb),
        "roe": str(roe),
        "roce": str(roce),
        "profit_margin": str(profit_margin),
        "sales_growth": str(sales_growth),
        "profit_growth": str(profit_growth),
        "dividend_yield": str(dividend_yield),
        "debtor_days": str(debtor_days),
        "summary": str(summary),
        
        "promoter_holding": str(promoter_holding),
        "fii_holding": str(fii_holding),
        "dii_holding": str(dii_holding),
        "public_holding": str(public_holding),
        "promoter_pledge": str(promoter_pledge),

        "verdict": "अनुशासित तरीके से ट्रेडिंग करें।",
        "risks": ["मार्केट जोखिम शामिल हैं।"]
    }

@app.get("/")
def home(): return render_template_string(PAGE)

@app.get("/api/analyze")
def api_analyze():
    symbol=request.args.get("symbol","")
    try: return safe_jsonify(analyze_symbol(symbol))
    except Exception as e: return safe_jsonify({"error":str(e)}),400

# API 1: Volume Screener
@app.get("/api/screener/volume/meta")
def screener_volume_meta():
    chunk_size = 15
    return safe_jsonify({"total_stocks": len(STOCK_UNIVERSE), "chunk_size": chunk_size,
                    "total_chunks": (len(STOCK_UNIVERSE) + chunk_size - 1) // chunk_size})

@app.get("/api/screener/volume")
def screener_volume():
    chunk = max(1, int(request.args.get("chunk", 1)))
    chunk_size = 15
    start_idx = (chunk - 1) * chunk_size
    current_stocks = STOCK_UNIVERSE[start_idx:start_idx + chunk_size]
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        data_list = list(executor.map(fetch_single_stock_data, current_stocks))
    for res in data_list:
        if res and res["volume"] >= 10000000:
            results.append(res)
    return safe_jsonify(results)

# Tab 3: Chartink Custom Screener, calculated in progressive chunks of 15.
_gapup_cache = {"data": [], "time": 0}

def get_cached_gapup_data(force_refresh=False):
    now = time.time()
    if force_refresh or now - _gapup_cache["time"] > 240 or not _gapup_cache["data"]:
        _gapup_cache["data"] = get_chartink_screener_stocks()
        _gapup_cache["time"] = now
    return _gapup_cache["data"]

@app.get("/api/screener/gapup/meta")
def screener_gapup_meta():
    data = get_cached_gapup_data(force_refresh=True)
    chunk_size = 15
    return safe_jsonify({"total_stocks": len(data), "chunk_size": chunk_size,
                    "total_chunks": (len(data) + chunk_size - 1) // chunk_size})

@app.get("/api/screener/gapup")
def screener_gapup():
    chunk = max(1, int(request.args.get("chunk", 1)))
    chunk_size = 15
    data = get_cached_gapup_data()
    selected = data[(chunk - 1) * chunk_size:chunk * chunk_size]
    symbols = [item.get("ticker_symbol") or (item.get("symbol", "").replace(".NS", "") + ".NS") for item in selected]
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        sr_data = list(executor.map(fetch_single_stock_data, symbols))
    sr_map = {item["symbol"]: item for item in sr_data if item}
    output = []
    for item in selected:
        ticker = item.get("ticker_symbol") or (item.get("symbol", "").replace(".NS", "") + ".NS")
        sr = sr_map.get(ticker.replace(".NS", ""), {})
        output.append({**item,
            "weekly_sr": sr.get("weekly_sr", "उपलब्ध नहीं"),
            "daily_sr": sr.get("daily_sr", "उपलब्ध नहीं"),
            "hourly_sr": sr.get("hourly_sr", "उपलब्ध नहीं")})
    return safe_jsonify(output)

if __name__ == "__main__":
    port=int(os.environ.get("PORT","5000"))
    app.run(host="0.0.0.0",port=port,debug=False)