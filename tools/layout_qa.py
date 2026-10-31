#!/usr/bin/env python3
"""Two layout faults the owner will not accept (2026-10-31), measured in a real render.

  * Uneven row: boxes that sit side by side in one row -- cards, tiles, panels:
    anything with a visible border, background or shadow -- whose heights differ.
  * Bad wrap: a heading, card title, label or button whose text wraps so its last
    line is one short word, or a control (button, chip, badge, status) whose text
    wraps at all.

Renders each page at 375, 768 and 1440 inside an iframe (Chrome headless clamps
its own viewport to 500px; see visual_qa.py) and reads the result back from the
frame's title. Exit 1 if anything is found.

    python3 tools/layout_qa.py [page.html ...]     # default: every page
"""
import glob
import http.server
import json
import os
import re
import socketserver
import subprocess
import sys
import threading
import time

PORT = 8907
WIDTHS = [(375, "phone"), (768, "tablet"), (1440, "desktop")]
TOL = 3  # px: sub-pixel rounding and 1px borders are not a fault


def _browser():
    for p in sorted(glob.glob(os.path.expanduser(
            "~/.cache/puppeteer/chrome-headless-shell/*/chrome-headless-shell-*/chrome-headless-shell")) +
            glob.glob(os.path.expanduser(
            "~/Library/Caches/ms-playwright/chromium_headless_shell-*/chrome-headless-shell-*/chrome-headless-shell")),
            reverse=True):
        if os.access(p, os.X_OK):
            return [p]
    return ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "--headless"]


CHROME = _browser() + ["--disable-gpu", "--hide-scrollbars", "--disable-crash-reporter", "--disable-breakpad",
                       "--no-first-run", "--no-default-browser-check", "--disable-extensions"]
PROBE = r"""
<script>window.addEventListener('load',function(){setTimeout(function(){
var TOL=%TOL%, out={uneven:[],wraps:[],seen:{cards:0,rows:0,texts:0}};
var SKIP={PRE:1,CODE:1,IMG:1,SVG:1,TABLE:1,THEAD:1,TBODY:1,TR:1,TD:1,TH:1,INPUT:1,TEXTAREA:1,SELECT:1,IFRAME:1,VIDEO:1,FIGURE:1};
function vis(e){var r=e.getBoundingClientRect();return r.width>0&&r.height>0;}
function label(e){var c=typeof e.className==='string'?e.className.trim():'';
  return e.tagName.toLowerCase()+(c?'.'+c.split(/\s+/).slice(0,2).join('.'):'');}
function card(e){if(SKIP[e.tagName]||e.closest('pre,table,svg,.term'))return false;
  var r=e.getBoundingClientRect(); if(r.width<60||r.height<24)return false;
  var s=getComputedStyle(e); if(s.position==='fixed'||s.position==='sticky')return false;
  var bd=parseFloat(s.borderTopWidth)>0&&s.borderTopStyle!=='none'&&parseFloat(s.borderBottomWidth)>0;
  var bg=s.backgroundColor!=='rgba(0, 0, 0, 0)'&&s.backgroundColor!=='transparent';
  var sh=s.boxShadow&&s.boxShadow!=='none';
  return (bd||bg||sh)&&parseFloat(s.borderTopLeftRadius)>0;}
function row(e){var slot=e,a=e.parentElement,d=0;
  while(a&&a!==document.body&&d<5){
    var kids=[].filter.call(a.children,vis);
    if(kids.length>=2){var t=slot.getBoundingClientRect().top;
      if(kids.filter(function(k){return Math.abs(k.getBoundingClientRect().top-t)<2;}).length>=2)return [a,slot];}
    slot=a;a=a.parentElement;d++;}
  return null;}
var cards=[].filter.call(document.querySelectorAll('main *'),card); out.seen.cards=cards.length;
var groups=new Map();
cards.forEach(function(e){var rc=row(e); if(!rc)return;
  var sig=label(e)+'|'+Math.round(rc[1].getBoundingClientRect().top);
  if(!groups.has(rc[0]))groups.set(rc[0],{}); var g=groups.get(rc[0]); (g[sig]=g[sig]||[]).push(e);});
groups.forEach(function(g,box){Object.keys(g).forEach(function(sig){var es=g[sig]; if(es.length<2)return; out.seen.rows++;
  var hs=es.map(function(e){return e.getBoundingClientRect().height;});
  if(Math.max.apply(null,hs)-Math.min.apply(null,hs)>TOL&&out.uneven.length<15)
    out.uneven.push(label(box)+' > '+sig.split('|')[0]+': '+hs.map(Math.round).join('/')+' "'+(es[0].textContent||'').replace(/\s+/g,' ').trim().slice(0,32)+'"');});});
function hidden(n){var s=getComputedStyle(n);return n.classList.contains('visually-hidden')||s.clipPath!=='none'&&s.clipPath||s.clip&&s.clip!=='auto'||n.getBoundingClientRect().width<=2;}
function inlineChain(n,e){while(n&&n!==e){var d=getComputedStyle(n).display;if(d!=='inline'&&!(n.classList.contains('line')&&d==='inline-block'))return false;n=n.parentElement;}return true;}
function words(e,pureInline){var w=[],tw=document.createTreeWalker(e,NodeFilter.SHOW_TEXT,null),n;
  while((n=tw.nextNode())){var p=n.parentElement;if(!p||!vis(p)||hidden(p))continue;
    if(pureInline&&!inlineChain(p,e))continue;
    var re=/\S+/g,m; while((m=re.exec(n.data))){var r=document.createRange(); r.setStart(n,m.index); r.setEnd(n,m.index+m[0].length);
      var rc=r.getClientRects(); if(!rc.length)continue; var b=rc[rc.length-1];
      w.push({cy:(b.top+b.bottom)/2,h:b.height,x:m[0],p:p});}}
  return w;}
function lines(w){var L=[]; w.forEach(function(o){var hit=L.filter(function(l){return Math.abs(l.cy-o.cy)<0.5*Math.min(l.h,o.h);})[0];
  if(hit)hit.n.push(o); else L.push({cy:o.cy,h:o.h,n:[o]});}); return L.sort(function(a,b){return a.cy-b.cy;});}
var NOWRAP='.btn,button,.badge,.pd-chip,.pmap-st,.pbar-cta,.pbar-status,.pbar-layer,.stack-loc,.sec-no,.page-eyebrow,.card-new,.tag,.chip';
[].forEach.call(document.querySelectorAll(NOWRAP),function(e){if(!vis(e)||e.closest('nav.site-nav,.mobile-nav'))return; out.seen.texts++;
  // A control laid out as stacked blocks (a title over a sub-line) is meant to be two lines.
  if([].some.call(e.children,function(c){var d=getComputedStyle(c).display;return d==='block'||d==='grid'||d==='flex';}))return;
  var w=words(e,false), by=new Map(); w.forEach(function(o){if(!by.has(o.p))by.set(o.p,[]); by.get(o.p).push(o);});
  by.forEach(function(g){if(g.length<2)return; var L=lines(g);
    if(L.length>1&&out.wraps.length<20)out.wraps.push('wraps: '+label(e)+' "'+g.map(function(o){return o.x;}).join(' ').slice(0,40)+'" ('+L.length+' lines)');});});
var TITLES='h1,h2,h3,h4,.pmap-cell b,.lead-line,dt,.glance-title,figcaption,.cta-band p,.hero-note,.read-more';
function orphan(e,where){var w=words(e,true); if(w.length<3)return; var L=lines(w); if(L.length<2)return;
  // A single long word (organisations, architectures) on the last line is the measure, not an orphan.
  var last=L[L.length-1].n; if(last.length===1&&last[0].x.length<12&&out.wraps.length<20)
    out.wraps.push('orphan: '+where+' "...'+w.slice(-4).map(function(o){return o.x;}).join(' ').slice(-40)+'" (last line: '+last[0].x+')');}
[].forEach.call(document.querySelectorAll(TITLES),function(e){if(!vis(e)||e.closest('nav,footer'))return;
  out.seen.texts++; var ls=[].filter.call(e.querySelectorAll('.line'),function(s){return vis(s)&&getComputedStyle(s).display!=='inline';});
  if(ls.length)ls.forEach(function(s){orphan(s,label(e)+' line');}); else orphan(e,label(e));});
document.title='LQA '+JSON.stringify(out);},400);});</script>
""".replace("%TOL%", str(TOL))


def serve():
    handler = http.server.SimpleHTTPRequestHandler
    handler.log_message = lambda *a, **k: None
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(("127.0.0.1", PORT), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def source(path):
    """A local page, or a live URL fetched once with a <base> so its assets load from the live site."""
    if not path.startswith("http"):
        return open(path).read()
    html = subprocess.run(["curl", "-sSL", "-m", "30", path], capture_output=True, text=True).stdout
    return re.sub(r"<head([^>]*)>", lambda m: f'<head{m.group(1)}><base href="{path}">', html, count=1)


def probe(path, width):
    inner, outer = "_lqa.html", "_lqa_frame.html"
    open(inner, "w").write(source(path).replace("</body>", PROBE + "</body>", 1))
    open(outer, "w").write(
        f'<!DOCTYPE html><html><body style="margin:0">'
        f'<iframe id="f" src="/{inner}" style="width:{width}px;height:900px;border:0"></iframe>'
        f'<script>window.addEventListener("load",function(){{var n=0,t=setInterval(function(){{'
        f'var d=document.getElementById("f").contentDocument;'
        f'if(d&&d.title.indexOf("LQA ")===0){{document.title=d.title;clearInterval(t);}}'
        f'if(++n>80)clearInterval(t);}},100);}});</script></body></html>')
    try:
        out = subprocess.run(CHROME + [f"--window-size={max(width + 60, 620)},1000", "--virtual-time-budget=8000",
                                       "--dump-dom", f"http://127.0.0.1:{PORT}/{outer}"],
                             capture_output=True, text=True, timeout=120).stdout
    finally:
        for f in (inner, outer):
            if os.path.exists(f):
                os.remove(f)
    m = re.search(r"LQA (\{.*?\})</title>", out, re.S)
    return json.loads(m.group(1)) if m else None


def main():
    pages = sys.argv[1:] or sorted(p for p in glob.glob("*.html") + glob.glob("docs/*.html") + glob.glob("blog/*.html")
                                   if not os.path.basename(p).startswith("_"))
    httpd = serve()
    time.sleep(0.5)
    found, seen = {}, {"cards": 0, "rows": 0, "texts": 0}
    try:
        for page in pages:
            for width, name in WIDTHS:
                r = probe(page, width)
                if r is None:
                    found.setdefault((page, "probe did not report"), []).append(name)
                    continue
                for k in seen:
                    seen[k] += r["seen"][k]
                for msg in r["uneven"] + r["wraps"]:
                    found.setdefault((page, msg), []).append(name)
    finally:
        httpd.shutdown()
    print(f"rendered {len(pages)} page(s) x {len(WIDTHS)} widths; examined {seen}")
    if seen["rows"] == 0 or seen["texts"] == 0:
        print("a detector examined nothing -- the probe is broken, not the pages")
        sys.exit(1)
    for (page, msg), ws in sorted(found.items()):
        print(f"  {page} @{','.join(ws)}: {msg}")
    print(f"{len(found)} layout problem(s)" if found else "no layout problems")
    sys.exit(1 if found else 0)


if __name__ == "__main__":
    main()
