"""
Frontend HTML/CSS/JS for IT Support demo.

Parameterized UI generation with service-specific branding.
"""

from config import Config


def get_html(config: Config) -> str:
    """Generate frontend HTML with service-specific branding."""
    html = r"""<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
<meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>IT Support Agent Pipeline</title>
<style>
/* ── Tokens ── */
:root{--bg:#f4f4f5;--surface:#fff;--card:#fff;--border:#d1d5db;--border2:#e5e7eb;
  --accent:#007a63;--p:#7c3aed;--g:#007a63;--b:#2563eb;--o:#dc4e2a;--y:#b45309;
  --text:#111827;--m:#6b7280;
  --mono:Consolas,'Courier New',monospace;--sans:Calibri,Arial,Helvetica,sans-serif;
  color-scheme:light}
[data-theme=dark]{--bg:#06080f;--surface:#0d1117;--card:#111827;--border:#1f2d3d;--border2:#253348;
  --accent:#00d4aa;--p:#b57bee;--g:#00d4aa;--b:#5b8cff;--o:#ff7c5c;--y:#f0c040;
  --text:#e2e8f0;--m:#64748b;color-scheme:dark}
*{box-sizing:border-box;margin:0;padding:0}
html,body{background:var(--bg);color:var(--text);font-family:var(--sans);
  font-size:.82rem;height:100vh;display:flex;flex-direction:column;overflow:hidden}
/* ── LLM Banner ── */
.llm-banner{display:flex;align-items:center;gap:.6rem;padding:.3rem 1rem;
  font-family:var(--mono);font-size:.7rem;border-bottom:1px solid var(--border);
  background:var(--surface);flex-shrink:0;flex-wrap:wrap}
.llm-dot{width:8px;height:8px;border-radius:50%;flex-shrink:0;animation:blink 2.5s infinite}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.35}}
.llm-mock{background:#dc4e2a}.llm-ollama{background:#007a63}
.llm-openai{background:#2563eb}.llm-anthropic{background:#7c3aed}
.llm-name{font-weight:700;color:var(--text)}.llm-model{color:var(--m)}
.llm-tag{font-size:.63rem;padding:.1rem .4rem;border-radius:3px;
  border:1px solid var(--border);color:var(--m);margin-left:auto}
/* ── Header ── */
header{background:var(--surface);border-bottom:1px solid var(--border);
  padding:.7rem 1.1rem;display:flex;align-items:center;justify-content:space-between;
  flex-wrap:wrap;gap:.5rem;flex-shrink:0}
.logo{font-size:.95rem;font-weight:700;color:var(--text)}
.logo span{color:var(--accent)}
.logo-sub{font-family:var(--mono);font-size:.62rem;color:var(--m);margin-top:.15rem}
.badges{display:flex;gap:.35rem;flex-wrap:wrap}
.badge{font-family:var(--mono);font-size:.6rem;padding:.15rem .55rem;
  border-radius:100px;border:1px solid;letter-spacing:.06em}
/* ── App shell ── */
.shell{display:grid;grid-template-columns:270px 1fr 250px;flex:1;overflow:hidden}
.col-panel{display:flex;flex-direction:column;border-right:1px solid var(--border);
  background:var(--card);overflow:hidden}
.col-panel:last-child{border-right:none}
/* ── Tabs ── */
.tab-bar{display:flex;border-bottom:1px solid var(--border);background:var(--surface);flex-shrink:0}
.tab-btn{flex:1;padding:.45rem .5rem;font-family:var(--mono);font-size:.63rem;font-weight:700;
  letter-spacing:.07em;border:none;background:transparent;color:var(--m);
  cursor:pointer;border-bottom:2px solid transparent;transition:color .15s,border-color .15s}
.tab-btn.active{color:var(--text);border-bottom-color:var(--accent)}
.tab-btn:hover:not(.active){color:var(--text)}
.tab-pane{display:none;flex:1;overflow-y:auto;padding:.65rem .75rem}
.tab-pane.active{display:block}
.tab-pane::-webkit-scrollbar{width:3px}
.tab-pane::-webkit-scrollbar-thumb{background:var(--border);border-radius:2px}
/* ── Section labels ── */
.slbl{font-family:var(--mono);font-size:.58rem;color:var(--m);letter-spacing:.12em;
  text-transform:uppercase;margin:.6rem 0 .3rem}
.slbl:first-child{margin-top:0}
/* ── User items ── */
.user-item{border:1px solid var(--border);border-radius:7px;padding:.5rem .65rem;
  cursor:pointer;transition:border-color .15s,background .15s;background:var(--surface);margin-bottom:.4rem}
.user-item:hover{border-color:var(--accent);background:var(--bg)}
.user-item.active{border-color:var(--accent);background:var(--bg)}
.user-name{font-weight:600;font-size:.8rem;margin-bottom:.15rem}
.user-meta{font-family:var(--mono);font-size:.62rem;color:var(--m);display:flex;gap:.4rem;flex-wrap:wrap}
.tier-1{color:var(--g)!important}.tier-2{color:var(--b)!important}
.tier-3{color:var(--y)!important}.tier-4{color:var(--o)!important}
/* ── Forms ── */
.form-label{font-family:var(--mono);font-size:.6rem;color:var(--m);display:block;margin-bottom:.18rem}
input[type=text],input[type=number],select,textarea{
  background:var(--bg);border:1px solid var(--border);border-radius:6px;
  padding:.38rem .65rem;color:var(--text);font-family:var(--mono);font-size:.72rem;
  outline:none;width:100%}
textarea{resize:vertical;min-height:70px;line-height:1.5}
input:focus,select:focus,textarea:focus{border-color:var(--accent)}
.form-gap{display:flex;flex-direction:column;gap:.45rem}
/* ── Buttons ── */
button{border:none;border-radius:7px;padding:.42rem 1rem;font-family:var(--mono);
  font-size:.7rem;font-weight:700;cursor:pointer;transition:opacity .15s;width:100%}
button:hover{opacity:.82}button:disabled{opacity:.35;cursor:not-allowed}
.btn-run{background:var(--accent);color:#fff;margin-top:.3rem}
.btn-seed{background:var(--surface);border:1px solid var(--border);color:var(--m);
  font-size:.63rem;padding:.32rem .65rem}
.btn-sm{background:var(--surface);border:1px solid var(--border);color:var(--m);
  font-size:.58rem;padding:.12rem .4rem;width:auto}
/* ── Agent cards ── */
.agent-card{background:var(--bg);border:1px solid var(--border);border-radius:7px;
  padding:.55rem .7rem;margin-bottom:.4rem}
.agent-card-name{font-family:var(--mono);font-size:.68rem;font-weight:700;color:var(--p);margin-bottom:.2rem}
.agent-card-desc{font-size:.7rem;color:var(--m);line-height:1.5}
.agent-card-skills{display:flex;flex-wrap:wrap;gap:.22rem;margin-top:.3rem}
.skill-pill{font-family:var(--mono);font-size:.56rem;padding:.1rem .38rem;
  border-radius:3px;border:1px solid var(--border);color:var(--m)}
/* ── Tool items ── */
.tool-item{background:var(--bg);border:1px solid var(--border);border-radius:6px;
  padding:.48rem .62rem;margin-bottom:.32rem}
.tool-name{font-family:var(--mono);font-size:.64rem;color:var(--y);font-weight:700;margin-bottom:.12rem}
.tool-desc{font-family:var(--mono);font-size:.61rem;color:var(--m);line-height:1.5}
/* ── Centre pipeline column ── */
.centre-col{display:flex;flex-direction:column;overflow:hidden;background:var(--card)}
.pipe-hdr{padding:.6rem .85rem;border-bottom:1px solid var(--border);
  background:var(--surface);flex-shrink:0}
.pipe-title-row{display:flex;align-items:center;gap:.6rem;margin-bottom:.45rem}
.pipe-title{font-family:var(--mono);font-size:.75rem;font-weight:700;color:var(--text)}
#pipeline-status{font-family:var(--mono);font-size:.63rem;color:var(--m)}
#session-tag{font-family:var(--mono);font-size:.6rem;color:var(--y);
  padding:.08rem .32rem;border:1px solid var(--y);border-radius:3px}
/* ── Agent flow strip ── */
.agent-flow{display:flex;align-items:center;gap:.3rem;flex-wrap:wrap;
  padding:.45rem .6rem;background:var(--bg);border-radius:7px;
  border:1px solid var(--border);margin-bottom:.45rem}
.af-agent{border-radius:5px;padding:.28rem .55rem;font-family:var(--mono);
  font-size:.63rem;border:1px solid;transition:all .25s}
.af-arrow{color:var(--m);font-size:.75rem}
.af-pending{background:var(--bg);border-color:var(--border);color:var(--m)}
.af-active{background:rgba(37,99,235,.15);border-color:var(--b);color:var(--b);animation:pulse-b 1s infinite}
@keyframes pulse-b{0%,100%{opacity:1}50%{opacity:.6}}
.af-complete{background:rgba(0,122,99,.12);border-color:var(--g);color:var(--g)}
/* ── Event stream ── */
.stream-wrap{flex:1;overflow-y:auto;padding:.45rem .7rem;
  font-family:var(--mono);font-size:.68rem;line-height:1.75}
.stream-wrap::-webkit-scrollbar{width:3px}
.stream-wrap::-webkit-scrollbar-thumb{background:var(--border);border-radius:2px}
.ev{padding:.28rem .42rem;border-radius:5px;margin-bottom:.2rem;
  display:flex;gap:.42rem;align-items:flex-start;border-left:2px solid transparent}
.ev-ts{color:var(--m);min-width:3.6rem;font-size:.61rem;flex-shrink:0}
.ev-kind{min-width:6.8rem;font-size:.59rem;opacity:.65;flex-shrink:0}
.ev-msg{flex:1;word-break:break-word;color:var(--text)}
.ev-harness_session  {background:rgba(37,99,235,.07);border-left-color:var(--b)}
.ev-harness_compaction{background:rgba(220,78,42,.08);border-left-color:var(--o)}
.ev-a2a_discover     {background:rgba(124,58,237,.07);border-left-color:var(--p)}
.ev-a2a_request      {background:rgba(0,122,99,.07);border-left-color:var(--g)}
.ev-a2a_response     {background:rgba(0,122,99,.1);border-left-color:var(--g)}
.ev-sdk_tool         {background:rgba(180,83,9,.07);border-left-color:var(--y)}
.ev-sdk_result       {background:rgba(180,83,9,.05);border-left-color:var(--y)}
.ev-memory           {background:rgba(100,116,139,.06);border-left-color:var(--m)}
.ev-done             {background:rgba(0,122,99,.12);border-left-color:var(--g);border-left-width:3px}
.ev-error            {background:rgba(220,78,42,.08);border-left-color:var(--o)}
/* ── Outcome result ── */
#outcome-result{padding:.45rem .75rem;border-top:1px solid var(--border);
  background:var(--surface);flex-shrink:0}
.outcome-badge{font-family:var(--mono);font-size:.76rem;font-weight:700;
  padding:.3rem .85rem;border-radius:6px;border:1px solid;display:inline-block;margin-bottom:.4rem}
.oc-resolved          {background:rgba(0,122,99,.12);border-color:var(--g);color:var(--g)}
.oc-workaround_applied{background:rgba(37,99,235,.12);border-color:var(--b);color:var(--b)}
.oc-escalated         {background:rgba(180,83,9,.12);border-color:var(--y);color:var(--y)}
.oc-escalated_to_l2   {background:rgba(180,83,9,.12);border-color:var(--y);color:var(--y)}
.oc-escalated_to_l3   {background:rgba(220,78,42,.12);border-color:var(--o);color:var(--o)}
.oc-pending           {background:rgba(100,116,139,.1);border-color:var(--m);color:var(--m)}
/* ── Right column ── */
.right-col{display:flex;flex-direction:column;overflow:hidden;background:var(--card)}
.phdr{padding:.5rem .8rem;border-bottom:1px solid var(--border);
  font-family:var(--mono);font-size:.65rem;letter-spacing:.1em;
  display:flex;align-items:center;justify-content:space-between;
  background:var(--surface);flex-shrink:0}
.history-wrap{flex:1;overflow-y:auto}
.history-wrap::-webkit-scrollbar{width:3px}
.history-wrap::-webkit-scrollbar-thumb{background:var(--border)}
.app-table{width:100%;border-collapse:collapse}
.app-table th{font-family:var(--mono);font-size:.58rem;letter-spacing:.08em;
  text-align:left;padding:.38rem .5rem;border-bottom:1px solid var(--border);
  color:var(--m);background:var(--surface);position:sticky;top:0}
.app-table td{padding:.38rem .5rem;border-bottom:1px solid var(--border2);
  color:var(--m);font-family:var(--mono);font-size:.66rem}
.app-table tbody tr:hover td{background:var(--bg)}
.st-resolved{color:var(--g);font-weight:600}.st-escalated{color:var(--y);font-weight:600}
.st-open{color:var(--b)}.st-closed{color:var(--m)}
.st-workaround_applied{color:var(--b);font-weight:600}
.st-escalated_to_l2{color:var(--y);font-weight:600}
.st-escalated_to_l3{color:var(--o);font-weight:600}
/* ── Memory 2x2 ── */
.mem-section{border-top:1px solid var(--border);flex-shrink:0;background:var(--surface)}
.mem-section .phdr{border-bottom:1px solid var(--border)}
.mem-grid{display:grid;grid-template-columns:1fr 1fr;gap:.55rem;padding:.6rem .8rem}
.mem-box{background:var(--card);border:1px solid var(--border);border-radius:7px;
  padding:.6rem .75rem;border-top-width:2px;min-height:120px;display:flex;flex-direction:column}
.mem-box.ctx{border-top-color:var(--b)}.mem-box.epi{border-top-color:var(--g)}
.mem-box.sem{border-top-color:var(--p)}.mem-box.wrk{border-top-color:var(--y)}
.mem-lbl{font-family:var(--mono);font-size:.58rem;color:var(--m);
  letter-spacing:.1em;margin-bottom:.28rem;text-transform:uppercase}
.mem-val{font-size:1.25rem;font-weight:700;line-height:1}
.mem-sub{font-family:var(--mono);font-size:.6rem;color:var(--m);margin-top:.12rem}
.mem-list{flex:1;overflow-y:auto;font-family:var(--mono);font-size:.62rem;
  color:var(--m);line-height:1.65;margin-top:.3rem}
.mem-list::-webkit-scrollbar{width:2px}
.mem-list::-webkit-scrollbar-thumb{background:var(--border)}
/* ── Theme toggle ── */
/* ── Inline theme toggle ── */
.theme-toggle-btn{display:flex;align-items:center;gap:.35rem;
  background:var(--bg);border:1px solid var(--border);border-radius:5px;
  padding:.18rem .55rem;cursor:pointer;font-family:var(--mono);font-size:.63rem;
  color:var(--m);transition:border-color .15s,color .15s;white-space:nowrap;
  width:auto;border-radius:5px}
.theme-toggle-btn:hover{border-color:var(--accent);color:var(--text);opacity:1}
.theme-toggle-btn svg{flex-shrink:0}
::-webkit-scrollbar{width:4px;height:4px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:var(--border);border-radius:2px}
</style>
</head>
<body>
<!-- LLM Banner -->
<div id="llm-banner" class="llm-banner">
  <span class="llm-dot llm-mock"></span>
  <span class="llm-name">Loading...</span>
</div>

<!-- Header -->
<header>
  <div>
    <div class="logo">IT Support Agent Platform <span>— Helpdesk Pipeline</span></div>
    <div class="logo-sub">SDK tools + Harness sessions + A2A protocol + 4 memory stores</div>
  </div>
  <div class="badges">
    <span class="badge" style="border-color:var(--b);color:var(--b)">SDK</span>
    <span class="badge" style="border-color:var(--g);color:var(--g)">Harness</span>
    <span class="badge" style="border-color:var(--p);color:var(--p)">A2A</span>
    <span class="badge" style="border-color:var(--y);color:var(--y)">Memory</span>
    <span class="badge" style="border-color:var(--m);color:var(--m)">port 8007</span>
  </div>
</header>

<!-- App shell -->
<div class="shell">

  <!-- ── LEFT: tabbed panel ── -->
  <div class="col-panel">
    <div class="tab-bar">
      <button class="tab-btn active" onclick="switchTab('reporters',this)">REPORTERS</button>
      <button class="tab-btn" onclick="switchTab('agents',this)">AGENTS &amp; TOOLS</button>
    </div>

    <!-- Reporters tab -->
    <div class="tab-pane active" id="tab-reporters">
      <div class="slbl">Select reporter</div>
      <div id="user-list"></div>

      <div class="slbl" style="margin-top:.8rem">Ticket details</div>
      <div class="form-gap">
        <div>
          <div class="form-label">Category</div>
          <select id="tk-category">
            <option>Network / VPN</option>
            <option>Software / Application</option>
            <option>Account / Access</option>
            <option>Hardware / Peripherals</option>
            <option>Performance / Crash</option>
            <option>Email / Calendar</option>
            <option>Security / Malware</option>
          </select>
        </div>
        <div>
          <div class="form-label">Priority</div>
          <select id="tk-priority">
            <option value="LOW">Low</option>
            <option value="MEDIUM" selected>Medium</option>
            <option value="HIGH">High</option>
            <option value="CRITICAL">Critical</option>
          </select>
        </div>
        <div>
          <div class="form-label">Description</div>
          <textarea id="tk-description">Cannot connect to VPN — error 800 timeout. Working from home. Have tried restarting router.</textarea>
        </div>
        <button class="btn-run" id="run-btn" onclick="runPipeline()">▶ Run Support Pipeline</button>
        <button class="btn-seed" onclick="seedData()">Seed 3 Sample Tickets</button>
      </div>
    </div>

    <!-- Agents & Tools tab -->
    <div class="tab-pane" id="tab-agents">
      <div class="slbl">A2A Agent cards</div>
      <div id="agent-cards"></div>
      <div class="slbl" style="margin-top:.7rem">SDK Tool registry</div>
      <div id="tool-list"></div>
    </div>
  </div>

  <!-- ── CENTRE: pipeline ── -->
  <div class="centre-col">
    <div class="pipe-hdr">
      <div class="pipe-title-row">
        <span class="pipe-title">A2A AGENT PIPELINE</span>
        <span id="pipeline-status">idle</span>
        <span id="session-tag"></span>
      </div>
      <div class="agent-flow">
        <div class="af-agent af-pending" id="af-triage">Triage</div>
        <span class="af-arrow">→</span>
        <div class="af-agent af-pending" id="af-diagnostic">Diagnostic</div>
        <span class="af-arrow">→</span>
        <div class="af-agent af-pending" id="af-resolution">Resolution</div>
        <span class="af-arrow">→</span>
        <div class="af-agent af-pending" id="af-escalation">Escalation</div>
      </div>
    </div>

    <div class="stream-wrap" id="stream">
      <div style="color:var(--m);font-size:.65rem;padding:.4rem 0">
        Select a reporter and configure the ticket, then click ▶ Run Support Pipeline.
      </div>
    </div>

    <div id="outcome-result"></div>

    <!-- Memory 2x2 -->
    <div class="mem-section">
      <div class="phdr" style="color:var(--g)">MEMORY STORES — LIVE ACTIVITY</div>
      <div class="mem-grid">
        <div class="mem-box ctx">
          <div class="mem-lbl">In-Context</div>
          <div class="mem-val" id="ctx-turns" style="color:var(--b)">0</div>
          <div class="mem-sub" id="ctx-sub">/ 10 turns</div>
          <div class="mem-list" id="ctx-list"></div>
        </div>
        <div class="mem-box epi">
          <div class="mem-lbl">Episodic / SQLite</div>
          <div class="mem-val" id="epi-count" style="color:var(--g)">0</div>
          <div class="mem-sub">audit events</div>
          <div class="mem-list" id="epi-list"></div>
        </div>
        <div class="mem-box sem">
          <div class="mem-lbl">Semantic / ChromaDB</div>
          <div class="mem-val" id="sem-count" style="color:var(--p)">0</div>
          <div class="mem-sub">KB articles indexed</div>
          <div class="mem-list" id="sem-list">Knowledge base + resolved tickets</div>
        </div>
        <div class="mem-box wrk">
          <div class="mem-lbl">Working / Redis</div>
          <div class="mem-val" id="wrk-count" style="color:var(--y)">0</div>
          <div class="mem-sub">active cache keys</div>
          <div class="mem-list" id="wrk-list"></div>
        </div>
      </div>
    </div>
  </div>

  <!-- ── RIGHT: Ticket history ── -->
  <div class="right-col">
    <div class="phdr" style="color:var(--g)">TICKET HISTORY
      <button class="btn-sm" onclick="loadTickets()">↺</button>
    </div>
    <div class="history-wrap">
      <table class="app-table">
        <thead><tr>
          <th>ID</th><th>Reporter</th><th>Cat</th><th>Status</th>
        </tr></thead>
        <tbody id="tkt-tbody">
          <tr><td colspan="4" style="color:var(--m);text-align:center;padding:.6rem">No tickets yet</td></tr>
        </tbody>
      </table>
    </div>
  </div>

</div><!-- end shell -->

<script>
// ── Tab switcher ─────────────────────────────────────────────────
function switchTab(name,btn){
  document.querySelectorAll(".tab-pane").forEach(p=>p.classList.remove("active"));
  document.querySelectorAll(".tab-btn").forEach(b=>b.classList.remove("active"));
  document.getElementById("tab-"+name).classList.add("active");
  btn.classList.add("active");}

// ── Theme ───────────────────────────────────────────────────────
(function(){
  var s=localStorage.getItem("theme")||"light";
  document.documentElement.setAttribute("data-theme",s);
  updateThemeBtn(s);
})();
function updateThemeBtn(theme){
  var btn=document.getElementById("theme-toggle-btn");
  if(!btn)return;
  var isDark=theme==="dark";
  btn.innerHTML=isDark
    ?'<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align:middle;margin-right:3px"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>LIGHT'
    :'<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align:middle;margin-right:3px"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>DARK';}
function toggleTheme(){
  var c=document.documentElement.getAttribute("data-theme")||"light";
  var n=c==="dark"?"light":"dark";
  document.documentElement.setAttribute("data-theme",n);
  localStorage.setItem("theme",n);
  updateThemeBtn(n);}

// ── LLM Banner ──────────────────────────────────────────────────
async function loadBanner(){
  try{const d=await fetch("/api/llm/status").then(r=>r.json());
  const b=document.getElementById("llm-banner");
  const cls=d.mock?"llm-mock":"llm-"+d.backend;
  b.innerHTML='<span class="llm-dot '+cls+'"></span>'
    +'<span class="llm-name">'+(d.mock?"MOCK MODE":d.backend.toUpperCase())+'</span>'
    +(d.model&&!d.mock?'<span class="llm-model">/ '+d.model+'</span>':"")
    +'<span class="llm-tag">'+(d.mock?"No Ollama / API key":"Live")+"</span>"
    +'<button class=\"theme-toggle-btn\" id=\"theme-toggle-btn\" onclick=\"toggleTheme()\"></button>'
    +'<span style="margin-left:.5rem;font-size:.63rem;color:var(--m)">IT Support Agent Pipeline</span>';
  updateThemeBtn(document.documentElement.getAttribute('data-theme')||'light');
  }catch(e){}}
loadBanner();setInterval(loadBanner,30000);

// ── Reporter list ────────────────────────────────────────────────
let selectedUser="USR001";
async function loadUsers(){
  const d=await fetch("/api/users").then(r=>r.json());
  const el=document.getElementById("user-list");
  el.innerHTML=d.users.map(u=>`
    <div class="user-item${u.id===selectedUser?" active":""}"
         onclick="selectUser('${u.id}',this)">
      <div class="user-name">${u.name}</div>
      <div class="user-meta">
        <span>${u.dept}</span>
        <span class="tier-${u.tier}">Tier ${u.tier}</span>
        <span>${u.device.split(" ").slice(0,2).join(" ")}</span>
      </div>
    </div>`).join("");}
function selectUser(id,el){
  selectedUser=id;
  document.querySelectorAll(".user-item").forEach(x=>x.classList.remove("active"));
  el.classList.add("active");}
loadUsers();

// ── Tools ────────────────────────────────────────────────────────
async function loadTools(){
  const d=await fetch("/api/tools").then(r=>r.json());
  document.getElementById("tool-list").innerHTML=d.tools.map(t=>`
    <div class="tool-item">
      <div class="tool-name">@tool ${t.name}()</div>
      <div class="tool-desc">${t.description}</div>
    </div>`).join("");}
loadTools();

// ── Agent cards ──────────────────────────────────────────────────
async function loadAgents(){
  const d=await fetch("/api/agents").then(r=>r.json());
  document.getElementById("agent-cards").innerHTML=d.agents.map(a=>`
    <div class="agent-card">
      <div class="agent-card-name">${a.name}</div>
      <div class="agent-card-desc">${a.description}</div>
      <div class="agent-card-skills">
        ${a.skills.map(s=>`<span class="skill-pill">${s}</span>`).join("")}
      </div>
    </div>`).join("");}
loadAgents();

// ── Ticket history ───────────────────────────────────────────────
async function loadTickets(){
  const d=await fetch("/api/tickets").then(r=>r.json());
  const tb=document.getElementById("tkt-tbody");
  if(!d.tickets.length){
    tb.innerHTML='<tr><td colspan="4" style="color:var(--m);text-align:center;padding:.6rem">No tickets yet</td></tr>';
    return;}
  tb.innerHTML=d.tickets.map(t=>`<tr>
    <td>${t.id}</td>
    <td>${t.reporter.split(" ")[0]}</td>
    <td style="font-size:.62rem">${t.category.split("/")[0].trim()}</td>
    <td class="st-${t.status}">${t.status.replace(/_/g," ").toUpperCase()}</td>
  </tr>`).join("");}

// ── Memory refresh ───────────────────────────────────────────────
let currentTicket=null;
async function refreshMemory(){
  const ctx=await fetch("/api/memory/context").then(r=>r.json());
  document.getElementById("ctx-turns").textContent=ctx.count;
  document.getElementById("ctx-sub").textContent=`/ ${ctx.limit} turns`;
  document.getElementById("ctx-list").innerHTML=
    ctx.items.slice(-3).map(m=>`<div>${m.role}: ${m.content.slice(0,55)}...</div>`).join("")||"empty";
  if(currentTicket){
    const ev=await fetch(`/api/events/${currentTicket}`).then(r=>r.json());
    document.getElementById("epi-count").textContent=ev.events.length;
    document.getElementById("epi-list").innerHTML=
      ev.events.slice(-3).map(e=>`<div>${e.agent}: ${e.event}</div>`).join("");}
  const wk=await fetch("/api/memory/working").then(r=>r.json());
  document.getElementById("wrk-count").textContent=wk.items.length;
  document.getElementById("wrk-list").innerHTML=
    wk.items.slice(0,4).map(i=>
      `<div style="display:flex;justify-content:space-between">
        <span>${i.key.replace("it:","")}</span>
        <span style="color:var(--y)">${i.ttl}s</span>
      </div>`).join("")||"empty";}

// ── Pipeline runner ──────────────────────────────────────────────
function setAgent(id,cls){
  const el=document.getElementById("af-"+id);
  if(el)el.className="af-agent "+cls;}

function addEv(d){
  const stream=document.getElementById("stream");
  const div=document.createElement("div");
  div.className="ev ev-"+d.kind;
  const label=d.msg||(d.result?String(d.result).slice(0,100):"");
  const detail=(d.msg&&d.result)
    ?`<div style="margin-top:.15rem;font-size:.63rem;color:var(--m);border-top:1px dashed var(--border2);padding-top:.1rem;word-break:break-word">${String(d.result).slice(0,180)}</div>`:"";
  div.innerHTML=`<span class="ev-ts">${d.ts||""}</span>`
    +`<span class="ev-kind">[${d.kind.replace(/_/g," ")}]</span>`
    +`<div style="flex:1"><span class="ev-msg">${label}</span>${detail}</div>`;
  stream.appendChild(div);stream.scrollTop=stream.scrollHeight;
  if(d.kind==="a2a_request"&&d.agent)
    ["triage","diagnostic","resolution","escalation"].forEach(a=>{
      if(a===d.agent)setAgent(a,"af-agent af-active");});
  if(d.kind==="a2a_response"&&d.agent)setAgent(d.agent,"af-agent af-complete");
  if(d.kind==="harness_session")
    document.getElementById("session-tag").textContent=`Session ${d.session}`;
  if(d.kind==="memory")setTimeout(refreshMemory,300);}

async function runPipeline(){
  const btn=document.getElementById("run-btn");
  const stream=document.getElementById("stream");
  btn.disabled=true;stream.innerHTML="";
  document.getElementById("outcome-result").innerHTML="";
  ["triage","diagnostic","resolution","escalation"].forEach(a=>setAgent(a,"af-agent af-pending"));
  document.getElementById("pipeline-status").textContent="running...";
  document.getElementById("session-tag").textContent="";
  currentTicket=null;
  const cat=document.getElementById("tk-category").value;
  const prio=document.getElementById("tk-priority").value;
  const desc=document.getElementById("tk-description").value;
  const url=`/api/run?user_id=${selectedUser}&category=${encodeURIComponent(cat)}&priority=${prio}&description=${encodeURIComponent(desc)}`;
  const es=new EventSource(url);
  es.onmessage=e=>{
    const d=JSON.parse(e.data);addEv(d);
    if(d.kind==="memory"&&d.store==="semantic"){
      const sc=document.getElementById("sem-count");
      sc.textContent=sc.textContent==="0"?"15+":parseInt(sc.textContent||"15")+1+"+";}
    if(d.kind==="done"){
      currentTicket=d.ticket_id;es.close();btn.disabled=false;
      document.getElementById("pipeline-status").textContent="complete";
      const oc=d.outcome.toLowerCase().replace(/ /g,"_");
      document.getElementById("outcome-result").innerHTML=
        `<div style="padding:.1rem 0">
          <span class="outcome-badge oc-${oc}">${d.outcome.replace(/_/g," ")}</span>
          <div style="font-size:.75rem;color:var(--m);line-height:1.6;margin-top:.25rem">${d.results.escalation||""}</div>
          <div style="font-family:var(--mono);font-size:.6rem;color:var(--m);margin-top:.25rem">
            ${d.sessions} sessions &nbsp;|&nbsp; ${d.agents_used} agents &nbsp;|&nbsp;
            ${d.tools_called} tools &nbsp;|&nbsp; ${d.memory_stores} stores &nbsp;|&nbsp;
            ${d.compactions} compaction(s)
          </div>
        </div>`;
      refreshMemory();loadTickets();}};
  es.onerror=()=>{es.close();btn.disabled=false;
    document.getElementById("pipeline-status").textContent="error";};}

async function seedData(){
  const btn=event.target;btn.disabled=true;btn.textContent="Seeding...";
  await fetch("/api/seed");
  btn.textContent="Seed 3 Sample Tickets";btn.disabled=false;loadTickets();}

setInterval(refreshMemory,8000);loadTickets();
</script>
</body>
</html>
"""
    return html
