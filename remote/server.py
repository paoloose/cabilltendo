#!/usr/bin/env python3
import os
from os import path
import subprocess
from flask import Flask, render_template_string, request

app = Flask(__name__)
SCRIPT_DIR = path.dirname(path.abspath(__file__))
REPO_ROOT = path.dirname(SCRIPT_DIR)
INJECT = os.environ.get('INJECT_SCRIPT', path.join(REPO_ROOT, 'scripts', 'inject_input.py'))
PYTHON_BIN = os.environ.get('PYTHON_BIN', '/usr/bin/python3')
REMOTE_PORT = int(os.environ.get('REMOTE_PORT', 8080))

HTML = r"""<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Cabilltendo Remote</title>
<style>
  body { background: #000; color:#fff; font-family:sans-serif;
         display:flex; flex-direction:column; align-items:center; padding:20px; margin:0; }
  h2   { color:#ffc800; }
  .pad { display:grid; grid-template-columns:repeat(3,80px);
         grid-template-rows:repeat(3,80px); gap:8px; margin:20px; }
  button { background:#1e1e4e; border:2px solid #ffc800; color:#fff; font-size:1.4rem;
           border-radius:12px; cursor:pointer; -webkit-tap-highlight-color:transparent; }
  button:active { background:#ffc800; color:#000; }
  .wide { width:176px; height:150px; font-size:1rem; }
</style>
</head>
<body>
<h2>Cabilltendo</h2>
<div class="pad">
  <div></div><button onpointerdown="send('up')">&#9650;</button><div></div>
  <button onpointerdown="send('left')">&#9664;</button>
  <button onpointerdown="send('a')">A</button>
  <button onpointerdown="send('right')">&#9654;</button>
  <div></div><button onpointerdown="send('down')">&#9660;</button><div></div>
</div>
<div style="display: flex; gap: 10px;">
  <button class="wide" onpointerdown="send('b')">B</button>
  <button class="wide" onpointerdown="send('start')">START</button>
</div>
<script>
function send(btn) { fetch('/input?btn=' + btn); }
</script>
</body>
</html>"""

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/input")
def handle_input():
    btn = request.args.get("btn", "")
    subprocess.run([PYTHON_BIN, INJECT, btn], timeout=2)
    return "ok"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=REMOTE_PORT, debug=False)
