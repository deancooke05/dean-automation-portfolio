from __future__ import annotations

import argparse
import json
import mimetypes
import subprocess
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .product_runtime import analyse, apply_preview, spec


class ProductApplication:
    def __init__(self, product_id: str, base: Path):
        self.product_id = product_id
        self.base = base.resolve()
        self.spec = spec(product_id)
        self.last_result: dict | None = None

    def defaults(self) -> dict:
        return {**self.spec, "source": self.spec["default_input"], "options": option_defaults(self.product_id)}

    def run(self, payload: dict) -> dict:
        self.last_result = analyse(self.product_id, self.base, payload.get("source", ""), payload.get("options", {}))
        return self.last_result

    def apply(self) -> dict:
        if self.last_result is None:
            raise ValueError("Create and review a preview first")
        self.last_result = apply_preview(self.product_id, self.base, self.last_result)
        return self.last_result


def option_defaults(product_id: str) -> dict:
    if product_id == "007": return {"keywords": "automation, engineering, software, python, data", "minimum_value": 1000}
    if product_id == "013": return {"tax_rate": 20}
    return {}


def option_fields(product_id: str) -> str:
    if product_id == "007":
        return '<label>Capability keywords<input id="keywords" value="automation, engineering, software, python, data"></label><label>Minimum opportunity value<input id="minimum_value" type="number" value="1000"></label>'
    if product_id == "013":
        return '<label>Tax rate (%)<input id="tax_rate" type="number" min="0" max="100" step="0.1" value="20"></label>'
    return ""


def make_handler(app: ProductApplication):
    class Handler(BaseHTTPRequestHandler):
        server_version = "CookeProductStudio/2.0"
        def log_message(self, format: str, *args) -> None: return

        def do_GET(self):
            path=urlparse(self.path).path
            if path=="/": return self._send(index_html(app.spec),"text/html")
            if path=="/app.css": return self._send(CSS,"text/css")
            if path=="/app.js": return self._send(JS,"application/javascript")
            if path=="/api/defaults": return self._json(app.defaults())
            if path=="/report":
                report=app.base/"outputs"/"executive_report.html"
                if not report.exists(): return self.send_error(404)
                return self._send(report.read_bytes(),"text/html")
            self.send_error(404)

        def do_POST(self):
            try:
                length=int(self.headers.get("Content-Length","0")); payload=json.loads(self.rfile.read(length) or b"{}")
                path=urlparse(self.path).path
                if path=="/api/run": result=app.run(payload)
                elif path=="/api/apply": result=app.apply()
                elif path=="/api/choose": result={"path":choose_folder(app.base,payload.get("initial",""))}
                else: return self.send_error(404)
                self._json(result)
            except (ValueError,FileNotFoundError,KeyError,json.JSONDecodeError) as error: self._json({"error":str(error)},400)
            except Exception as error: self._json({"error":f"Unexpected error: {error}"},500)

        def _json(self,payload,status=200): self._send(json.dumps(payload,default=str).encode(),"application/json; charset=utf-8",status)
        def _send(self,body,content_type,status=200):
            if isinstance(body,str): body=body.encode()
            self.send_response(status); self.send_header("Content-Type",content_type); self.send_header("Content-Length",str(len(body))); self.send_header("Cache-Control","no-store"); self.end_headers(); self.wfile.write(body)
    return Handler


def choose_folder(base: Path, initial: str) -> str:
    path=Path(initial).expanduser(); path=path if path.is_absolute() else base/path
    if not path.exists(): path=base
    script="import sys,tkinter as t;from tkinter import filedialog;r=t.Tk();r.withdraw();r.attributes('-topmost',True);print(filedialog.askdirectory(title='Choose input',initialdir=sys.argv[1]));r.destroy()"
    result=subprocess.run([sys.executable,"-c",script,str(path)],capture_output=True,text=True,timeout=300)
    if result.returncode: raise ValueError("Folder chooser unavailable; paste the path instead")
    return result.stdout.strip()


def launch(product_id: str, base: Path) -> None:
    parser=argparse.ArgumentParser(description=f"Launch Product {product_id}"); parser.add_argument("--host",default="127.0.0.1"); parser.add_argument("--port",type=int,default=0); parser.add_argument("--no-browser",action="store_true"); args=parser.parse_args()
    app=ProductApplication(product_id,base); server=ThreadingHTTPServer((args.host,args.port),make_handler(app)); url=f"http://{args.host}:{server.server_port}"
    print(f"{app.spec['name']} is ready at {url}"); print("Press Control+C to stop it.")
    if not args.no_browser: threading.Timer(.4,lambda:webbrowser.open(url)).start()
    try: server.serve_forever()
    except KeyboardInterrupt: print("\nApplication stopped.")
    finally: server.server_close()


def index_html(product: dict) -> str:
    options=option_fields(product["id"])
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{product["name"]}</title><link rel="stylesheet" href="/app.css"></head><body data-product="{product["id"]}"><header><div class="brand"><i>C</i><span><b>COOKE</b><small>AUTOMATION SYSTEMS</small></span></div><div class="local"><i></i>Private & local</div></header><main><section id="setup" class="screen active"><div class="hero"><p class="eyebrow">PRODUCT {product["id"]} · {product["category"]}</p><h1>{title_markup(product["name"])}</h1><p class="promise">{product["promise"]}</p><div class="proof"><span>Local processing</span><span>Explainable results</span><span>Audit outputs</span></div></div><form id="form"><div class="form-title"><em>01</em><span><small>CHOOSE THE SOURCE</small><b>What should we analyse?</b></span></div><label>Input file or folder<div class="field"><input id="source" required><button id="browse" type="button">Browse</button><button id="demo" type="button">Demo</button></div></label>{options}<button class="primary" type="submit"><span>Build executive analysis</span><b>→</b></button><p class="assurance">Your source remains private and unchanged.</p></form></section><section id="result" class="screen"><div class="result-head"><button id="back">← New analysis</button><p class="eyebrow">EXECUTIVE RESULT</p><h1 id="headline"></h1><p id="summary"></p></div><div id="metrics" class="metrics"></div><div class="result-grid"><section class="panel insights"><div class="panel-title">What this means</div><div id="insights"></div></section><section class="panel evidence"><div class="panel-title"><span>Evidence and decisions</span><small id="rowCount"></small></div><div class="table-wrap"><table><thead><tr id="heads"></tr></thead><tbody id="rows"></tbody></table></div></section></div><div class="actionbar"><div><i>✓</i><span><b>Analysis complete</b><small>Results and audit artifacts saved locally</small></span></div><div class="actions"><a href="/report" target="_blank">Open report ↗</a><button id="apply" class="apply hidden">Apply approved plan →</button></div></div><div id="artifacts" class="artifacts"></div></section></main><div id="toast"></div><script src="/app.js"></script></body></html>'''


def title_markup(name: str) -> str:
    words=name.split(); split=max(1,len(words)//2); return " ".join(words[:split])+"<br><em>"+" ".join(words[split:])+".</em>"


CSS='''
:root{--n:#142b3a;--n2:#1e3a4b;--g:#b79a62;--p:#f5f8f8;--w:#fff;--s:#60737e;--l:#dbe3e6;--good:#39745b;--shadow:0 28px 75px rgba(14,35,46,.12)}*{box-sizing:border-box}html{background:var(--p)}body{margin:0;min-height:100vh;color:var(--n);font:14px Inter,Aptos,"Helvetica Neue",Arial;background:radial-gradient(circle at 88% 38%,rgba(183,154,98,.1),transparent 25%),linear-gradient(145deg,#fbfcfc,#eef3f3)}button,input{font:inherit}button,a{cursor:pointer}header{height:88px;padding:0 max(5vw,34px);display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid rgba(20,43,58,.09)}.brand{display:flex;gap:13px;align-items:center}.brand>i{display:grid;place-items:center;width:38px;height:38px;border:1px solid var(--g);transform:rotate(45deg);font:22px Georgia;color:var(--g)}.brand span b,.brand span small{display:block;letter-spacing:.18em}.brand span b{font-size:12px}.brand span small{font-size:8px;color:var(--s);margin-top:4px}.local{font-size:11px;color:var(--s);letter-spacing:.08em}.local i{display:inline-block;width:7px;height:7px;border-radius:50%;background:#4d876d;margin-right:8px;box-shadow:0 0 0 4px rgba(77,135,109,.1)}main{max-width:1380px;margin:auto;padding:70px max(5vw,34px)}.screen{display:none}.screen.active{display:grid}#setup{grid-template-columns:1.05fr .82fr;gap:9vw;align-items:center;min-height:calc(100vh - 230px)}.eyebrow{font-size:10px;font-weight:700;letter-spacing:.22em;color:var(--g);margin:0 0 22px}.hero h1,.result-head h1{font:400 clamp(50px,6vw,82px)/.98 Georgia,serif;letter-spacing:-.045em;margin:0;color:var(--n)}h1 em{color:var(--g);font-weight:400}.promise{max-width:570px;font-size:17px;line-height:1.75;color:var(--s);margin:30px 0}.proof{display:flex;gap:25px;color:var(--s);font-size:11px;margin-top:44px}.proof span:before{content:"✓";color:var(--g);margin-right:8px}form{position:relative;background:rgba(255,255,255,.94);padding:39px 42px;border:1px solid rgba(20,43,58,.12);box-shadow:var(--shadow)}form:before{content:"";position:absolute;left:0;top:0;bottom:0;width:3px;background:var(--g)}.form-title{display:flex;align-items:center;gap:18px;margin-bottom:28px}.form-title em{font:italic 22px Georgia;color:var(--g)}.form-title small,.form-title b{display:block}.form-title small{font-size:9px;letter-spacing:.15em;color:var(--s);margin-bottom:5px}.form-title b{font:24px Georgia}label{display:block;font-size:10px;font-weight:700;letter-spacing:.08em;color:var(--s);margin-top:19px}input{width:100%;margin-top:9px;border:1px solid var(--l);padding:15px 16px;background:#fbfcfc;color:var(--n);outline:0}input:focus{border-color:var(--g);box-shadow:0 0 0 3px rgba(183,154,98,.1)}.field{position:relative}.field input{padding-right:135px}.field button{position:absolute;right:7px;top:16px;bottom:7px;border:0;background:#edf2f3;font-size:9px;font-weight:700;padding:0 10px}.field #browse{right:57px}.primary{width:100%;height:56px;margin-top:24px;padding:0 20px;border:0;background:var(--n);color:#fff;display:flex;align-items:center;justify-content:space-between;font-size:11px;font-weight:700}.primary b{font-size:18px;color:#d7c6a4}.assurance{text-align:center;font-size:9px;color:#87959c;margin:12px 0 0}.result-head{text-align:center;margin-bottom:38px;position:relative}.result-head h1{font-size:56px}.result-head>p:last-child{max-width:760px;margin:16px auto;color:var(--s);line-height:1.7}.result-head #back{position:absolute;left:0;top:0;border:0;background:none;color:var(--s);font-size:10px}.metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}.metrics article{background:#fff;border:1px solid var(--l);padding:23px;min-height:125px;border-bottom:2px solid var(--g)}.metrics small,.metrics strong,.metrics span{display:block}.metrics small{font-size:9px;letter-spacing:.12em;color:var(--s)}.metrics strong{font:29px Georgia;margin:13px 0 6px}.metrics span{font-size:9px;color:var(--s)}.result-grid{display:grid;grid-template-columns:330px 1fr;gap:17px;margin-top:17px}.panel{background:#fff;border:1px solid var(--l);min-height:385px}.panel-title{height:59px;padding:0 20px;border-bottom:1px solid var(--l);display:flex;align-items:center;justify-content:space-between;font-size:11px;font-weight:700}.panel-title small{font-weight:400;color:var(--s)}.insight{padding:18px 20px;border-bottom:1px solid #edf1f2;border-left:2px solid var(--g)}.insight b{font-size:11px}.insight p{font-size:10px;line-height:1.55;color:var(--s);margin:7px 0 0}.table-wrap{overflow:auto;max-height:390px}table{width:100%;border-collapse:collapse}th,td{padding:13px 14px;text-align:left;border-bottom:1px solid #edf1f2;white-space:nowrap}th{font-size:8px;letter-spacing:.1em;color:var(--s);background:#fafbfb;position:sticky;top:0}td{font-size:10px;color:var(--s)}td:first-child{color:var(--n);font-weight:700}.actionbar{margin-top:17px;background:var(--n);color:#fff;padding:18px 21px;display:flex;align-items:center;justify-content:space-between}.actionbar>div:first-child{display:flex;gap:12px;align-items:center}.actionbar i{width:31px;height:31px;border:1px solid var(--g);display:grid;place-items:center;color:var(--g)}.actionbar b,.actionbar small{display:block}.actionbar b{font-size:11px}.actionbar small{font-size:9px;color:#bdc9ce;margin-top:4px}.actions{display:flex;gap:9px}.actions a,.actions button{border:0;background:#fff;color:var(--n);padding:14px 18px;text-decoration:none;font-size:10px;font-weight:700}.actions .apply{background:var(--g);color:#fff}.hidden{display:none!important}.artifacts{display:flex;gap:10px;flex-wrap:wrap;margin-top:12px}.artifact{border:1px solid var(--l);background:rgba(255,255,255,.7);padding:10px 13px;font-size:9px;color:var(--s)}#toast{position:fixed;right:25px;bottom:25px;background:#7f3434;color:#fff;padding:15px 20px;transform:translateY(100px);opacity:0;transition:.2s;font-size:11px}#toast.show{transform:none;opacity:1}@media(max-width:950px){#setup{grid-template-columns:1fr;gap:55px}.result-grid{grid-template-columns:1fr}.metrics{grid-template-columns:1fr 1fr}}@media(max-width:600px){header{padding:0 20px}.local{display:none}main{padding:45px 20px}#setup{display:none}#setup.active{display:grid}.hero h1{font-size:52px}form{padding:28px 22px}.proof{flex-wrap:wrap}.metrics{grid-template-columns:1fr}.result-head #back{position:static;margin-bottom:20px}.result-head h1{font-size:42px}.actionbar{flex-direction:column;align-items:stretch;gap:18px}.actions{flex-direction:column}.actions a,.actions button{text-align:center}}
'''

JS='''
const $=id=>document.getElementById(id);let defaults={},last=null;const esc=v=>String(v??'').replace(/[&<>\"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&#39;'}[c]));function view(id){['setup','result'].forEach(x=>$(x).classList.toggle('active',x===id));scrollTo(0,0)}function toast(m){$('toast').textContent=m;$('toast').classList.add('show');setTimeout(()=>$('toast').classList.remove('show'),4000)}async function req(url,opts={}){let r=await fetch(url,{headers:{'Content-Type':'application/json'},...opts}),d=await r.json();if(!r.ok)throw Error(d.error||'Request failed');return d}function options(){let o={};document.querySelectorAll('form input[id]:not(#source)').forEach(i=>o[i.id]=i.type==='number'?Number(i.value):i.value);return o}function render(d){last=d;$('headline').textContent=d.headline;$('summary').textContent=d.summary;$('metrics').innerHTML=d.metrics.map(m=>`<article><small>${esc(m.label)}</small><strong>${esc(m.value)}</strong><span>${esc(m.note)}</span></article>`).join('');$('insights').innerHTML=d.insights.map(i=>`<div class="insight"><b>${esc(i.title)}</b><p>${esc(i.body)}</p></div>`).join('');$('heads').innerHTML=d.columns.map(c=>`<th>${esc(c.label)}</th>`).join('');$('rows').innerHTML=d.rows.slice(0,100).map(r=>`<tr>${d.columns.map(c=>`<td>${esc(r[c.key])}</td>`).join('')}</tr>`).join('');$('rowCount').textContent=`${d.rows.length} record${d.rows.length===1?'':'s'}`;$('artifacts').innerHTML=d.artifacts.map(a=>`<span class="artifact"><b>${esc(a.name)}</b> · ${esc(a.description)}</span>`).join('');$('apply').classList.toggle('hidden',!d.can_apply);view('result')}fetch('/api/defaults').then(r=>r.json()).then(d=>{defaults=d;$('source').value=d.source});$('demo').onclick=()=>{$('source').value=defaults.source};$('back').onclick=()=>view('setup');$('form').onsubmit=async e=>{e.preventDefault();let b=e.submitter,before=b.querySelector('span').textContent;b.disabled=true;b.querySelector('span').textContent='Building analysis…';try{render(await req('/api/run',{method:'POST',body:JSON.stringify({source:$('source').value,options:options()})}))}catch(x){toast(x.message)}finally{b.disabled=false;b.querySelector('span').textContent=before}};$('apply').onclick=async()=>{if(!confirm('Apply the approved rename plan?'))return;try{render(await req('/api/apply',{method:'POST',body:'{}'}))}catch(x){toast(x.message)}};$('browse').onclick=async()=>{try{let d=await req('/api/choose',{method:'POST',body:JSON.stringify({initial:$('source').value})});if(d.path)$('source').value=d.path}catch(x){toast(x.message)}};
'''
