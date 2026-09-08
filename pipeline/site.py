"""一頁式網站生成器 — site/index.html（由 pipeline 每次生成後重寫）。

風格：暗色編劇室（老闆指定 dark UI）。版面：
  拍板卡 → 分場大綱 → 第 1 場劇本 → 風控 → Showrunner 判決 → 圍讀
  → Pipeline 全紀錄 → 觸發表單 → 歷史
Worker 由 repo main 讀呢個檔案 serve 去 https://script.anidit.com。
"""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site" / "index.html"


def esc(s) -> str:
    return html.escape(str(s), quote=False)


def score_bar(name: str, score) -> str:
    try:
        v = float(score)
    except (TypeError, ValueError):
        v = 0
    pct = max(0, min(100, v * 10))
    color = "#e8b64c" if v >= 8 else "#c98a3d" if v >= 6 else "#b35b3d"
    return f"""
      <div class="score-row"><span>{esc(name)}</span>
        <div class="score-track"><div class="score-fill" style="width:{pct:.0f}%;background:{color}"></div></div>
        <b>{v:.0f}</b></div>"""


def build(state: dict, index: list) -> None:
    cfg = state.get("config", {})
    v = state.get("verdict", {})
    o = state.get("outline", {})
    r = state.get("risk", {})
    tr = state.get("table_read", {})
    d = state.get("directive", {})
    trace = state.get("trace", [])
    total_tokens = sum(t.get("tokens", 0) for t in trace)

    # 拍板取捨 decisions
    dec_html = "".join(
        f'<div class="decision"><span class="vd vd-{esc(x.get("verdict","").lower())}">{esc(x.get("verdict",""))}</span>'
        f'<div><b>{esc(x.get("topic",""))}</b><p>{esc(x.get("reason",""))}</p>'
        f'<span class="instr">→ {esc(x.get("instruction",""))}</span></div></div>'
        for x in d.get("decisions", [])[:14]
    ) or '<p class="muted">—</p>'

    # 分場大綱
    scenes_html = "".join(
        f'<tr><td class="sc-no">{int(s.get("no",0))}</td>'
        f'<td><b>{esc(s.get("heading",""))}</b><p>{esc(s.get("summary",""))}</p>'
        f'<span class="hook">↳ {esc(s.get("exit_hook",""))}</span></td></tr>'
        for s in o.get("scenes", [])
    ) or '<tr><td colspan="2" class="muted">—</td></tr>'

    # 風控 flags
    flags_html = "".join(
        f'<div class="flag flag-{esc(f.get("severity","")).lower()}"><span class="sev">{esc(f.get("severity",""))} · {esc(f.get("type",""))}</span>'
        f'<b>{esc(f.get("issue",""))}</b><p>{esc(f.get("suggestion",""))}</p></div>'
        for f in r.get("flags", [])
    ) or '<p class="muted">冇紅旗</p>'

    # 圍讀
    read_html = ""
    for key, label, emoji in (
        ("audience", "目標觀眾", "👀"),
        ("line_producer", "執行監製", "💰"),
        ("veteran_actor", "老戲骨", "🎭"),
    ):
        p = tr.get(key, {})
        read_html += (
            f'<div class="persona"><h4>{emoji} {label}</h4>'
            f'<p>{esc(p.get("reaction",""))}</p>'
            + (f'<blockquote>「{esc(p["quote"] if "quote" in p else p.get("mouth_feel", p.get("cost_note","")))}」</blockquote>' if p.get("quote") or p.get("mouth_feel") or p.get("cost_note") else "")
            + (f'<span class="worry">擔憂：{esc(p["worry"])}</span>' if p.get("worry") else "")
            + "</div>"
        )

    # trace
    trace_html = "".join(
        f'<tr><td>{esc(t["step"])}</td><td>{t.get("seconds","")}s</td>'
        f'<td>{t.get("tokens","")}</td><td>{t.get("reasoning","")}</td></tr>'
        for t in trace
    )

    # 歷史
    hist_html = "".join(
        f'<tr><td class="muted">{esc(h["run_id"])}</td><td><b>{esc(h.get("title",""))}</b></td>'
        f'<td>{esc(h.get("genre",""))} · {esc(h.get("master",""))}</td>'
        f'<td><span class="vd vd-{esc(h.get("decision","").lower())}">{esc(h.get("decision",""))}</span></td></tr>'
        for h in index[:15]
    )

    # 表單選項
    from .masters import GENRES, MASTERS
    genre_opts = "".join(f'<option>{g}</option>' for g in GENRES)
    master_opts = "".join(
        f'<option value="{m}"{" selected" if m == "杜琪峯" else ""}>{p["label"]}</option>'
        for m, p in MASTERS.items()
    )

    decision = v.get("decision", "")
    dec_badge = f'<span class="big-badge {"badge-pass" if decision == "PASS" else "badge-revise"}">{esc(decision)}</span>'

    page = f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ScriptAgents · AI 編劇室</title>
<style>
:root {{
  --bg:#0d0f14; --panel:#151823; --panel2:#1b1f2e; --border:#2a3048;
  --text:#e6e4dd; --muted:#8a8f9e; --amber:#e8b64c; --teal:#4ec9b0;
  --red:#d96459; --purple:#8a7ec8; --green:#6dbf7e;
}}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ background:var(--bg); color:var(--text); font-family:-apple-system,'PingFang TC','Noto Sans TC',sans-serif; line-height:1.75; }}
.wrap {{ max-width:880px; margin:0 auto; padding:32px 20px 80px; }}
a {{ color:var(--teal); text-decoration:none; }}
header {{ text-align:center; padding:36px 0 26px; border-bottom:1px solid var(--border); margin-bottom:28px; }}
h1 {{ font-size:30px; letter-spacing:2px; }}
h1 .brand {{ color:var(--amber); }}
.sub {{ color:var(--muted); font-size:13px; margin-top:6px; }}
.badges {{ margin-top:12px; }}
.badge {{ display:inline-block; padding:3px 12px; border:1px solid var(--border); border-radius:20px; font-size:12px; color:var(--muted); margin:0 4px; }}
.badge .dot {{ color:var(--green); }}
section {{ margin-bottom:34px; }}
h2 {{ font-size:15px; letter-spacing:3px; color:var(--muted); text-transform:uppercase; margin-bottom:14px; padding-bottom:8px; border-bottom:1px dashed var(--border); }}
h2 .no {{ color:var(--amber); }}
.card {{ background:var(--panel); border:1px solid var(--border); border-radius:14px; padding:22px 24px; margin-bottom:14px; }}
.logline {{ font-size:17px; color:var(--text); font-weight:500; }}
.meta {{ margin-top:10px; font-size:13px; color:var(--muted); }}
.meta b {{ color:var(--amber); }}
.chips span {{ display:inline-block; background:var(--panel2); border:1px solid var(--border); border-radius:6px; padding:2px 10px; margin:4px 6px 0 0; font-size:12px; color:var(--text); }}
.decision {{ display:flex; gap:14px; padding:12px 0; border-bottom:1px solid var(--border); }}
.decision:last-child {{ border-bottom:none; }}
.decision p {{ font-size:13px; color:var(--muted); margin:2px 0; }}
.decision .instr {{ font-size:12px; color:var(--teal); }}
.vd {{ flex:none; font-size:11px; font-weight:700; padding:2px 8px; border-radius:5px; margin-top:3px; text-align:center; }}
.vd-accept,.vd-pass {{ background:rgba(109,191,126,.15); color:var(--green); border:1px solid var(--green); }}
.vd-reject {{ background:rgba(217,100,89,.12); color:var(--red); border:1px solid var(--red); }}
.vd-modify,.vd-revise {{ background:rgba(232,182,76,.12); color:var(--amber); border:1px solid var(--amber); }}
table {{ width:100%; border-collapse:collapse; font-size:13.5px; }}
th {{ text-align:left; color:var(--muted); font-size:12px; font-weight:600; padding:8px 10px; border-bottom:1px solid var(--border); }}
td {{ padding:10px; border-bottom:1px solid var(--border); vertical-align:top; }}
tr:last-child td {{ border-bottom:none; }}
.sc-no {{ color:var(--amber); font-weight:700; width:36px; }}
.hook {{ font-size:12px; color:var(--teal); }}
.script {{ white-space:pre-wrap; font-family:'SF Mono','Courier New',monospace; font-size:14px; background:#10131c; border:1px solid var(--border); border-radius:10px; padding:26px 28px; line-height:1.9; }}
.flag {{ padding:11px 0; border-bottom:1px solid var(--border); }}
.flag:last-child {{ border-bottom:none; }}
.flag b {{ display:block; font-size:14px; }}
.flag p {{ font-size:12.5px; color:var(--muted); }}
.sev {{ font-size:11px; font-weight:700; margin-right:10px; }}
.flag-high .sev {{ color:var(--red); }} .flag-med .sev {{ color:var(--amber); }} .flag-low .sev {{ color:var(--muted); }}
.verdict-card {{ display:flex; gap:22px; align-items:flex-start; }}
.big-badge {{ flex:none; font-size:24px; font-weight:800; letter-spacing:3px; padding:10px 26px; border-radius:10px; }}
.badge-pass {{ background:rgba(109,191,126,.12); color:var(--green); border:2px solid var(--green); }}
.badge-revise {{ background:rgba(232,182,76,.1); color:var(--amber); border:2px dashed var(--amber); }}
.verdict-line {{ font-size:17px; font-weight:600; margin-bottom:8px; }}
.scores {{ margin-top:10px; }}
.score-row {{ display:flex; align-items:center; gap:12px; font-size:13px; margin:6px 0; }}
.score-row span {{ width:90px; color:var(--muted); }}
.score-row b {{ color:var(--amber); width:24px; text-align:right; }}
.score-track {{ flex:1; height:7px; background:var(--panel2); border-radius:4px; overflow:hidden; }}
.score-fill {{ height:100%; border-radius:4px; }}
.personas {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(230px,1fr)); gap:14px; }}
.persona {{ background:var(--panel2); border:1px solid var(--border); border-radius:10px; padding:16px 18px; font-size:13px; }}
.persona h4 {{ color:var(--amber); font-size:13px; margin-bottom:6px; }}
.persona blockquote {{ border-left:3px solid var(--purple); padding-left:10px; margin:8px 0; color:var(--text); font-size:12.5px; }}
.worry {{ color:var(--red); font-size:12px; }}
form .fld {{ margin-bottom:14px; }}
label {{ display:block; font-size:12px; color:var(--muted); margin-bottom:5px; letter-spacing:1px; }}
textarea, select {{ width:100%; background:var(--panel2); color:var(--text); border:1px solid var(--border); border-radius:8px; padding:10px 12px; font-size:14px; font-family:inherit; }}
textarea {{ min-height:88px; resize:vertical; }}
textarea:focus, select:focus {{ outline:none; border-color:var(--amber); }}
button {{ background:var(--amber); color:#141414; font-weight:700; font-size:15px; border:none; border-radius:9px; padding:12px 34px; cursor:pointer; width:100%; letter-spacing:2px; }}
button:disabled {{ opacity:.45; cursor:not-allowed; }}
.status {{ text-align:center; margin-top:14px; font-size:13px; color:var(--muted); min-height:22px; }}
.status a {{ color:var(--teal); }}
.muted {{ color:var(--muted); }}
footer {{ text-align:center; color:var(--muted); font-size:12px; margin-top:56px; padding-top:22px; border-top:1px solid var(--border); }}
@media(max-width:640px) {{ .verdict-card {{ flex-direction:column; }} .wrap {{ padding:20px 14px 60px; }} }}
</style>
</head>
<body>
<div class="wrap">

<header>
  <h1>SCRIPT<span class="brand">AGENTS</span> · AI 編劇室</h1>
  <p class="sub">多智能體劇本創作 — 分析師 → 力挺 vs 挑刺辯論 → 統籌拍板 → 主筆 → 風控 → Showrunner → 圍讀</p>
  <p class="sub">LLM：MiniMax-M3</p>
  <div class="badges">
    <span class="badge"><span class="dot">●</span> 全雲端自動生成</span>
    <span class="badge">更新於 {esc(state.get("finished_at",""))}</span>
    <span class="badge">{len(trace)} 次 LLM 調用 · {state.get("elapsed_seconds","")}s · {total_tokens} tokens</span>
  </div>
</header>

<section>
  <h2><span class="no">01</span> 拍板卡 · Creative Directive</h2>
  <div class="card">
    <p class="logline">「{esc(state.get("title",""))}」</p>
    <p class="logline" style="font-weight:400;font-size:15px;margin-top:6px">{esc(cfg.get("logline",""))}</p>
    <div class="meta">
      類型 <b>{esc(cfg.get("genre",""))}</b> ·
      大師手法 <b>{esc(cfg.get("master",""))}</b> ·
      場數 <b>{len(o.get("scenes",[]))}</b>
      {"· 每日自動班" if cfg.get("auto") else "· 手動觸發"}
    </div>
    <div class="chips" style="margin-top:10px">
      {"".join(f"<span>⛔ {esc(x)}</span>" for x in d.get("danger_list", [])[:6])}
    </div>
  </div>
  <div class="card">
    <h2 style="margin-bottom:6px;border:none">論點取捨紀錄（辯論 → 拍板）</h2>
    {dec_html}
  </div>
</section>

<section>
  <h2><span class="no">02</span> 分場大綱 · Scene Outline</h2>
  <div class="card" style="padding:0">
    <table>
      <tr><th style="width:36px">#</th><th>場次</th></tr>
      {scenes_html}
    </table>
  </div>
  {f'<p class="muted" style="font-size:13px">連載引擎：{esc(o.get("series_engine",""))}</p>' if o.get("series_engine") else ""}
</section>

<section>
  <h2><span class="no">03</span> 第 1 場 · 完整劇本</h2>
  <div class="script">{esc(state.get("scene_1",""))}</div>
</section>

<section>
  <h2><span class="no">04</span> 監製風控 · Risk Report</h2>
  <div class="card">
    {flags_html}
    <p class="muted" style="font-size:12.5px;margin-top:10px">{esc(r.get("overall",""))}</p>
  </div>
</section>

<section>
  <h2><span class="no">05</span> Showrunner 終審 · Final Verdict</h2>
  <div class="card verdict-card">
    {dec_badge}
    <div style="flex:1">
      <p class="verdict-line">{esc(v.get("verdict_line",""))}</p>
      <div class="scores">
        {score_bar("結構", v.get("scores",{}).get("structure"))}
        {score_bar("人物", v.get("scores",{}).get("characters"))}
        {score_bar("對白", v.get("scores",{}).get("dialogue"))}
        {score_bar("手法忠實度", v.get("scores",{}).get("style_fidelity"))}
        {score_bar("商業爽點", v.get("scores",{}).get("commercial_payoff"))}
      </div>
      {f'<p style="font-size:13px;margin-top:10px">下一場鉤子 ↳ {esc(v.get("next_episode_hook",""))}</p>' if v.get("next_episode_hook") else ""}
    </div>
  </div>
</section>

<section>
  <h2><span class="no">06</span> 模擬圍讀 · Table Read</h2>
  <div class="personas">{read_html}</div>
  {f'<p class="muted" style="font-size:13px;margin-top:10px">房溫：{esc(tr.get("room_temperature",""))}</p>' if tr.get("room_temperature") else ""}
</section>

<section>
  <h2><span class="no">07</span> Pipeline 全紀錄 · Engineering</h2>
  <div class="card" style="padding:0">
    <table>
      <tr><th>Step</th><th>耗時</th><th>Tokens</th><th>Reasoning</th></tr>
      {trace_html}
    </table>
  </div>
</section>

<section>
  <h2><span class="no">08</span> 開新一集 · Commission New Episode</h2>
  <div class="card">
    <div class="fld">
      <label>LOGLINE（一句話講晒呢個故事）</label>
      <textarea id="f-logline" placeholder="例：一個收數佬為咗還亡母心願，被迫接手一間就執笠嘅殯儀館，仲要同連環跳樓嘅地產商鬥法。"></textarea>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px">
      <div class="fld">
        <label>類型</label>
        <select id="f-genre">{genre_opts}</select>
      </div>
      <div class="fld">
        <label>大師手法</label>
        <select id="f-master">{master_opts}</select>
      </div>
    </div>
    <div class="fld">
      <label>自由備註（選填 — 老闆加料）</label>
      <textarea id="f-notes" style="min-height:52px" placeholder="例：主角一定要係中年女性；結尾唔好大團圓；想有場落雨天台戲……"></textarea>
    </div>
    <button id="f-go" onclick="fire()">🎬 開 機</button>
    <p class="status" id="f-status"></p>
  </div>
</section>

<section>
  <h2><span class="no">09</span> 歷史 · Archive</h2>
  <div class="card" style="padding:0">
    <table>
      <tr><th>Run</th><th>劇名</th><th>類型 · 大師</th><th>判決</th></tr>
      {hist_html}
    </table>
  </div>
</section>

<footer>
  ScriptAgents — TradingAgents 多智能體概念移植到劇本創作 · GitHub Actions + MiniMax-M3 + Cloudflare Workers<br>
  <a href="https://github.com/mike8418/scriptagents">github.com/mike8418/scriptagents</a>
</footer>

</div>
<script>
async function fire() {{
  var logline = document.getElementById('f-logline').value.trim();
  var btn = document.getElementById('f-go'), st = document.getElementById('f-status');
  if (logline.length < 10) {{ st.textContent = '⚠️ Logline 太短（至少 10 個字）'; return; }}
  btn.disabled = true; st.textContent = '遞交緊…';
  try {{
    var resp = await fetch('/api/run', {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{
        logline: logline,
        genre: document.getElementById('f-genre').value,
        master: document.getElementById('f-master').value,
        notes: document.getElementById('f-notes').value.trim()
      }})
    }});
    var data = await resp.json();
    if (!data.ok) {{ st.textContent = '✗ ' + (data.error || '觸發失敗'); btn.disabled = false; return; }}
    st.innerHTML = '✓ 編劇室開工：<a href="' + data.run_url + '" target="_blank">GitHub Actions #' + data.run_number + '</a>（約 3-6 分鐘）';
    poll();
  }} catch (e) {{
    st.textContent = '✗ 網絡錯誤：' + e.message; btn.disabled = false;
  }}
}}
async function poll() {{
  var st = document.getElementById('f-status');
  var iv = setInterval(async function() {{
    try {{
      var resp = await fetch('/api/status');
      var s = await resp.json();
      if (s.status === 'completed' && s.conclusion === 'success') {{
        clearInterval(iv); st.innerHTML = '✓ 新劇本出爐！重新整理…';
        setTimeout(function() {{ location.reload(); }}, 1500);
      }} else if (s.status === 'completed') {{
        clearInterval(iv); st.innerHTML = '✗ 今次 run ' + s.conclusion + ' — <a href="' + s.run_url + '" target="_blank">睇 log</a>';
      }} else {{
        st.textContent = '生成中…（' + s.status + '）';
      }}
    }} catch (e) {{}}
  }}, 12000);
}}
</script>
</body>
</html>"""

    SITE.parent.mkdir(parents=True, exist_ok=True)
    SITE.write_text(page, encoding="utf-8")


def build_placeholder(reason: str) -> None:
    """未有第一個 run 之前嘅佔位頁。"""
    SITE.parent.mkdir(parents=True, exist_ok=True)
    SITE.write_text(
        f"""<!DOCTYPE html>
<html lang="zh-Hant"><head><meta charset="UTF-8"><title>ScriptAgents · AI 編劇室</title>
<style>body{{background:#0d0f14;color:#e6e4dd;font-family:-apple-system,'PingFang TC',sans-serif;
display:flex;align-items:center;justify-content:center;height:100vh;margin:0;flex-direction:column}}
h1{{letter-spacing:3px}}.s{{color:#8a8f9e;margin-top:10px;font-size:14px}}</style></head>
<body><h1>SCRIPT<span style="color:#e8b64c">AGENTS</span> · AI 編劇室</h1>
<p class="s">{esc(reason)}</p></body></html>""",
        encoding="utf-8",
    )