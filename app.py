from flask import Flask, render_template_string, request, jsonify
from urllib.parse import quote_plus
import os

app = Flask(__name__)

HTML_PAGE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Argstone App (Beta)</title>
  <style>
    body { margin:0; height:100vh; display:flex; justify-content:center; align-items:center;
           background:radial-gradient(circle at top left,#050509,#0a0a0f 70%);
           font-family:Inter,sans-serif; color:#fff; overflow:hidden; }
    .arena { width:80%; max-width:900px; background:rgba(255,255,255,0.08);
            border:1px solid rgba(255,255,255,0.2); border-radius:20px; padding:28px;
            backdrop-filter:blur(18px) saturate(180%); box-shadow:0 8px 40px rgba(0,0,0,0.6),
            inset 0 1px 0 rgba(255,255,255,0.15); display:flex; flex-direction:column; gap:18px; }
    .small {font-size:12px;color:rgba(255,255,255,0.7);}
    .toolbar {display:flex;flex-wrap:wrap;gap:8px;margin-bottom:10px;}
    .btn { background:rgba(255,255,255,0.1); border:1px solid rgba(255,255,255,0.25);
          color:#e0e0e0; border-radius:8px; padding:8px 10px; font-size:13px; cursor:pointer;
          backdrop-filter:blur(12px); transition:all .2s ease; }
    .editor-wrapper {position:relative;}
    .editor { min-height:280px; background:rgba(255,255,255,0.08);
            border:1px solid rgba(255,255,255,0.15); border-radius:14px; padding:20px;
            color:#fff; overflow:auto; outline:none; z-index:2; backdrop-filter:blur(12px);
            caret-color:#fff; transition:box-shadow .2s ease; }
    .hint { position:absolute; top:20px; left:24px; color:rgba(255,255,255,0.5);
           pointer-events:none; font-size:15px; transition:opacity 0.3s ease; z-index:1; }
    .footer { display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; }
    .selectors { display:flex; align-items:center; gap:10px; flex-wrap:wrap; }
    select, input[type='number'] { background:rgba(255,255,255,0.1); color:#fff;
      border:1px solid rgba(255,255,255,0.25); border-radius:8px; padding:8px; width:140px;
      backdrop-filter:blur(10px); }
    .send { background:rgba(255,255,255,0.12); color:#fff; border:1px solid rgba(255,255,255,0.25);
           border-radius:10px; padding:10px 18px; cursor:pointer; font-size:15px;
           transition:all .25s ease; backdrop-filter:blur(10px); }
  </style>
</head>
<body>
  <div class="arena">
    <div class="small">Argstone 1.0.9 (preview)</div>

    <div class="toolbar">
      <button class="btn" data-cmd="bold"><strong>B</strong></button>
      <button class="btn" data-cmd="italic"><em>I</em></button>
      <button class="btn" data-cmd="code">&lt;/&gt;</button>
      <button class="btn" data-cmd="insertUnorderedList">• List</button>
      <button class="btn" data-cmd="insertOrderedList">1. List</button>
      <button class="btn" data-cmd="blockquote">❝</button>
      <button class="btn" data-cmd="h2">H2</button>
      <button class="btn" data-cmd="clearFormatting">Clear</button>
    </div>

    <div class="editor-wrapper">
      <div id="hint" class="hint">Write your question here...</div>
      <div id="editor" class="editor" contenteditable="true" spellcheck="true"></div>
    </div>

    <div class="footer">
      <div class="selectors">
        <label class="small">Type</label>
        <select id="typeSel">
          <option value="math">math</option>
          <option value="logic">logic</option>
          <option value="mcq">MCQ</option>
          <option value="other">other questions</option>
        </select>

        <label class="small">Num of Stones</label>
        <input type="number" id="stonesInput" min="1" placeholder="e.g. 3">

        <label class="small">Num of Kernels</label>
        <input type="number" id="kernelsInput" min="1" placeholder="e.g. 50">
      </div>
      <button id="sendBtn" class="send">Send Prompt</button>
    </div>
  </div>

  <script>
    const editor = document.getElementById('editor');
    const hint = document.getElementById('hint');
    const sendBtn = document.getElementById('sendBtn');
    const stonesInput = document.getElementById('stonesInput');
    const kernelsInput = document.getElementById('kernelsInput');
    const typeSel = document.getElementById('typeSel');

    editor.addEventListener('input', () => {
      hint.style.opacity = editor.textContent.trim() ? '0' : '1';
    });

    document.querySelectorAll('.toolbar .btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const cmd = btn.dataset.cmd;
        editor.focus();
        switch (cmd) {
          case 'code': document.execCommand('formatBlock', false, 'pre'); break;
          case 'h2': document.execCommand('formatBlock', false, 'h2'); break;
          case 'blockquote': document.execCommand('formatBlock', false, 'blockquote'); break;
          case 'clearFormatting': document.execCommand('removeFormat', false, null); break;
          default: document.execCommand(cmd, false, null);
        }
      });
    });

    sendBtn.addEventListener('click', async () => {
      const prompt = editor.innerText.trim();
      const stones = parseInt(stonesInput.value) || 1;
      const kernels = parseInt(kernelsInput.value) || 1;
      const type = typeSel.value || 'logic';
      if (!prompt) return;
      try {
        const res = await fetch(window.location.origin + '/open', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ prompt, stones, kernels, type })
        });
        if (!res.ok) {
          const err = await res.json().catch(()=>({error:'unknown'}));
          alert('Error: ' + (err.error || 'server error'));
          return;
        }
        const data = await res.json();
        for (let i = 0; i < (data.opened || 1); ++i) {
          window.open(data.url, '_blank');
        }
      } catch (err) {
        alert('Network error: ' + err.message);
      }
    });
  </script>
</body>
</html>
"""

def format_one_decimal(x):
    return f"{x:.1f}"

@app.route("/")
def index():
    return render_template_string(HTML_PAGE)

@app.route("/open", methods=["POST"])
def open_chat():
    data = request.get_json()
    prompt = data.get("prompt", "").strip()
    stones = int(data.get("stones", 1))
    kernels = int(data.get("kernels", 1))
    typ = (data.get("type") or "logic").lower()

    if not prompt:
        return jsonify({"error": "Empty prompt"}), 400
    if stones < 1 or kernels < 1:
        return jsonify({"error": "stones and kernels must be >= 1"}), 400

    if typ == "math":
        a = kernels / 10.0
        b = kernels / 2.0
        c = b - a
        system_prompt = (
            f"Generate exactly {kernels} unique answers divided as follows: "
            f"{format_one_decimal(a)} correct, {format_one_decimal(b)} sign variations, "
            f"{format_one_decimal(c)} uncertain. Question: {prompt}"
        )
    elif typ == "logic":
        system_prompt = (
            f"Generate {kernels} unique logical answers with reasoning. Question: {prompt}"
        )
    elif typ == "mcq":
        system_prompt = (
            f"Generate {kernels} unique MCQ-style answers with full working. Question: {prompt}"
        )
    else:
        system_prompt = (
            f"Generate {kernels} distinct answers showing full reasoning. Question: {prompt}"
        )

    encoded = quote_plus(system_prompt)
    url = f"https://chat.openai.com/?q={encoded}&temporary-chat=true"

    return jsonify({"status": "ok", "opened": stones, "url": url})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
