import sys, json, os, datetime, threading, asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler

# Ensure we can import fetch.py from the same directory as this script
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch import run_fetch

ARTICLES_FILE = os.path.expanduser("~/.vibereader/articles.json")
PREFS_FILE = os.path.expanduser("~/.vibereader/preferences.json")
ACTIVITY_FILE = os.path.expanduser("~/.vibereader/activity-state.json")

def load_status():
    """Load Claude Code activity state."""
    import time
    try:
        with open(ACTIVITY_FILE) as f:
            state = json.load(f)
        now = int(time.time())
        last_tool = state.get("last_tool_call_ts", 0)
        idle_secs = now - last_tool
        return {
            "claude_active": idle_secs < 120,
            "idle_seconds": idle_secs,
            "tool_call_count": state.get("tool_call_count", 0),
            "last_push_ts": state.get("last_push_ts", 0),
            "unread_count": len([1 for _ in state.get("shown_ids", [])]),
        }
    except Exception:
        return {"claude_active": False, "idle_seconds": -1, "tool_call_count": 0}

HTML = """<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Vibereader</title><style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0f0f13;color:#e0e0e0;font-family:system-ui,sans-serif;padding:16px}
.container{max-width:800px;margin:0 auto}
header{display:flex;align-items:center;justify-content:space-between;padding:12px 0 20px;border-bottom:1px solid #2a2a3a;margin-bottom:20px;flex-wrap:wrap;gap:8px}
h1{font-size:1.5rem;color:#a78bfa}
#status{font-size:.8rem;color:#888}
button{background:#6d28d9;color:#fff;border:none;padding:8px 16px;border-radius:6px;cursor:pointer;font-size:.85rem}
button:hover{background:#7c3aed}
.article{background:#1a1a24;border:1px solid #2a2a3a;border-radius:8px;padding:14px;margin-bottom:12px}
.article a{color:#c4b5fd;text-decoration:none;font-size:1rem;font-weight:500;line-height:1.4}
.article a:hover{color:#a78bfa;text-decoration:underline}
.meta{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px;align-items:center}
.score{background:#6d28d9;color:#fff;padding:2px 8px;border-radius:12px;font-size:.75rem;font-weight:600}
.cat{background:#1e3a2f;color:#6ee7b7;padding:2px 8px;border-radius:12px;font-size:.72rem}
.source{color:#888;font-size:.78rem;margin-left:auto}
#list{min-height:100px}
</style></head><body><div class="container">
<header><h1>Vibereader</h1><span id="status">loading...</span><button onclick="refresh()">Refresh Feed</button></header>
<div id="list"></div></div>
<script>
function timeAgo(iso){if(!iso)return'unknown';const d=new Date(iso),now=new Date(),m=Math.round((now-d)/60000);if(m<1)return'just now';if(m<60)return m+'m ago';return Math.round(m/60)+'h ago'}
function render(arts,fetchedAt){
  document.getElementById('status').textContent='fetched '+timeAgo(fetchedAt);
  const el=document.getElementById('list');
  if(!arts.length){el.innerHTML='<p style="color:#888;padding:20px 0">No articles found.</p>';return}
  el.innerHTML=arts.map(a=>`<div class="article">
    <a href="${a.url||'#'}" target="_blank" rel="noopener">${a.title||'Untitled'}</a>
    <div class="meta">
      <span class="score">${(a.score||0).toFixed?.(1)??a.score}</span>
      ${(a.categories||[]).map(c=>`<span class="cat">${c}</span>`).join('')}
      <span class="source">${a.source||''}</span>
    </div></div>`).join('')}
function load(){fetch('/api/articles').then(r=>r.json()).then(d=>{render(d.articles||[],d.fetched_at||null)}).catch(()=>{})}
function refresh(){fetch('/refresh',{method:'POST'}).then(()=>{setTimeout(load,2000)}).catch(()=>{})}
load();setInterval(load,60000);
</script></body></html>"""

def load_data():
    articles, fetched_at = [], None
    try:
        with open(ARTICLES_FILE) as f:
            data = json.load(f)
            articles = data.get("articles", [])
            fetched_at = data.get("fetched_at")
    except Exception:
        pass
    prefs_cats = []
    try:
        with open(PREFS_FILE) as f:
            prefs_cats = json.load(f).get("categories", [])
    except Exception:
        pass
    if prefs_cats:
        filtered = [a for a in articles if set(a.get("categories", [])) & set(prefs_cats)]
        if len(filtered) < 5:
            filtered = articles
    else:
        filtered = articles
    filtered.sort(key=lambda a: a.get("score", 0), reverse=True)
    return filtered[:20], fetched_at

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_): pass

    def send_json(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/api/articles":
            arts, fetched_at = load_data()
            self.send_json(200, {"articles": arts, "fetched_at": fetched_at})
        elif self.path == "/api/status":
            self.send_json(200, load_status())
        elif self.path == "/":
            body = HTML.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", len(body))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_json(404, {"error": "not found"})

    def do_POST(self):
        if self.path == "/refresh":
            threading.Thread(target=lambda: asyncio.run(run_fetch()), daemon=True).start()
            self.send_json(200, {"status": "ok"})
        else:
            self.send_json(404, {"error": "not found"})

if __name__ == "__main__":
    # Initial fetch on startup
    threading.Thread(target=lambda: asyncio.run(run_fetch()), daemon=True).start()
    server = HTTPServer(("127.0.0.1", 8888), Handler)
    print("Vibereader dashboard running on http://localhost:8888")
    server.serve_forever()
