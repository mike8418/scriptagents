"""ScriptAgents 編劇室 — 11 個 agent 嘅 prompt 合約。

TradingAgents 概念移植：
  分析師團隊（人物/受眾/結構）→ 力挺派 vs 挑刺派辯論 → 統籌拍板
  → 主筆編劇（唯一執筆者，temp 0.8）→ 監製風控 → Showrunner 終審 → 模擬圍讀

設計原則：
  - 分析/風控/終審 temp 0.1-0.3（求穩）；辯論 0.5；主筆 0.7-0.8（求靈）
  - 全部結構化輸出走 JSON（extract_json 容錯解析）
  - 論點取捨有 decision log（每個 accept/reject 附理由 — 可追溯）
"""
from __future__ import annotations

import json
import re

from .llm import chat
from .masters import style_brief

# ── JSON 容錯解析 ─────────────────────────────────────────

def extract_json(text: str):
    """由 LLM 回覆度抽 JSON（M3 偶爾會喺前面漏思考文字）：
    1. 剝 code fence
    2. 掃晒全部 { / [ 開頭位，逐個試 raw_decode
    3. 揀「跨度最大」嘅可解析對象（避開散落喺 prose 入面嘅碎 brace）
    """
    text = re.sub(r"```(?:json)?\s*", "", text)
    text = text.replace("```", "")
    dec = json.JSONDecoder()
    best = None  # (obj, span)
    for opener in ("{", "["):
        for m in re.finditer(re.escape(opener), text):
            try:
                obj, end = dec.raw_decode(text[m.start():])
                if isinstance(obj, (dict, list)) and (best is None or end > best[1]):
                    best = (obj, end)
            except json.JSONDecodeError:
                continue
    if best is not None:
        return best[0]
    raise ValueError(f"抽唔到 JSON：{text[:200]}...")


def call_agent(step: str, system: str, user: str, temp: float, max_tokens: int, trace: list):
    """統一 agent 調用 + trace 記賬（step 名、耗時、tokens）。"""
    content, usage = chat(system, user, temperature=temp, max_tokens=max_tokens)
    trace.append({
        "step": step,
        "seconds": usage["seconds"],
        "tokens": usage["completion_tokens"],
        "reasoning": usage["reasoning_tokens"],
    })
    return content


def call_json(step: str, system: str, user: str, temp: float, max_tokens: int, trace: list,
              required: list | None = None):
    """JSON 崗位專用：解析失敗 or 缺 required keys → 帶糾正提示重試一次。"""
    content = call_agent(step, system, user, temp, max_tokens, trace)

    def _ok(obj):
        if required is None:
            return True
        return isinstance(obj, dict) and all(k in obj for k in required)

    try:
        obj = extract_json(content)
        if _ok(obj):
            return obj
        raise ValueError(f"缺 required keys {required}")
    except ValueError:
        retry = (
            "你上次嘅輸出解析失敗或者形狀唔啱。"
            f"重新輸出：**淨係一個 JSON object**，必須齊呢啲頂層 key：{required or '正確結構'}"
            "（之前之後唔可以有其他文字，第一個字元必須係 `{`）。\n\n"
            "上次回覆開頭（僅供參考）：\n" + content[:300]
        )
        content2 = call_agent(step, system, user + "\n\n" + retry, temp, max_tokens, trace)
        obj = extract_json(content2)
        if _ok(obj) or required is None:
            return obj
        raise ValueError(f"{step} 重試後仍然缺 keys：{obj if isinstance(obj, dict) else type(obj)}")


def wrap_list(obj, key: str):
    """M3 有時會出頂層 array（得其中一個欄位）— 包返做 {key: [...]}。"""
    if isinstance(obj, list):
        return {key: obj}
    return obj


# ── 分析師團隊（temp 0.3）─────────────────────────────────

def analyst_character(logline: str, genre: str, trace: list) -> dict:
    sys_ = "你係 ScriptAgents 編劇室嘅人物分析師。只輸出 JSON，唔好輸出其他嘢。"
    usr = f"""Logline：{logline}
類型：{genre}

分析呢個故事嘅人物骨架，輸出 JSON：
{{
  "protagonist": {{"name_suggestion": "", "desire": "", "fear": "", "flaw": "", "arc": ""}},
  "antagonist": {{"name_suggestion": "", "goal": "", "why_they_think_they_are_right": ""}},
  "pressure_source": "呢個故事最致命嘅壓力來源",
  "central_relationship": "最有力嘅人物關係軸",
  "casting_hooks": ["三個選角/寫戲時最搶眼嘅人物瞬間"]
}}"""
    return call_json("analyst_character", sys_, usr, 0.3, 6000, trace, required=["protagonist"])


def analyst_audience(logline: str, genre: str, trace: list) -> dict:
    sys_ = "你係 ScriptAgents 編劇室嘅受眾分析師。只輸出 JSON，唔好輸出其他嘢。"
    usr = f"""Logline：{logline}
類型：{genre}

分析目標受眾，輸出 JSON：
{{
  "target_audience": "",
  "platform": "最適合嘅平台/載體（劇集/電影/微短劇）",
  "payoff_expectations": ["觀眾入場最想睇到嘅三樣嘢"],
  "genre_conventions_to_honor": ["必須遵守嘅類型慣例"],
  "genre_conventions_to_subvert": ["可以反套路上位嘅位"],
  "taboo_risks": ["呢個題材最易踩嘅受眾雷區"]
}}"""
    return call_json("analyst_audience", sys_, usr, 0.3, 6000, trace, required=["target_audience"])


def analyst_structure(logline: str, genre: str, scene_count: int, trace: list) -> dict:
    sys_ = "你係 ScriptAgents 編劇室嘅結構分析師。只輸出 JSON，唔好輸出其他嘢。"
    usr = f"""Logline：{logline}
類型：{genre}
預計場數：{scene_count}

設計節拍骨架（輸出 JSON）：
{{
  "opening_hook": "開場 30 秒點樣抓住觀眾",
  "inciting_incident": "",
  "midpoint_reversal": "中點反轉",
  "low_point": "低谷",
  "climax": "",
  "resolution": "結尾（唔好預支大團圓，留餘味）",
  "act_breaks": ["每個轉折位一句話"]
}}"""
    return call_json("analyst_structure", sys_, usr, 0.3, 6000, trace, required=["opening_hook"])


# ── 力挺派 vs 挑刺派辯論（temp 0.5）───────────────────────

def bull_researcher(logline: str, genre: str, analyses: dict, trace: list, opponent: dict | None = None) -> dict:
    sys_ = "你係編劇室嘅力挺派研究員（Bull Researcher）。你嘅職責係論證呢個故事最值得寫。只輸出 JSON。"
    round_hint = (
        f"\n【第 2 輪 · 駁論】挑刺派啱啱反駁過你：{json.dumps(opponent, ensure_ascii=False)}\n"
        "逐條駁斥佢嘅風險論點（指出佢睇漏咗啲乜），再強化你自己最有力嘅一條論點。\n"
        if opponent else ""
    )
    usr = f"""【輸出合約】淨係輸出一個 JSON object。頂層 keys 必須係 ["arguments", "one_line_pitch"]。
- "arguments" = array，必須有 3 個 object，每個 object 有 "point" / "evidence" / "how_to_execute" 三個非空字串
- "one_line_pitch" = 一個非空字串
- 之前之後唔可以有任何文字，第一個字元必須係 {{

Logline：{logline}
類型：{genre}
分析師報告：{json.dumps(analyses, ensure_ascii=False)}
{round_hint}
提出三個「呢個故事非寫不可」嘅最強論點。
結構示例（內容只係示意，唔好照抄）：
{{"arguments": [{{"point": "例：殯儀館 vs 地產商嘅空間鬥爭自帶香港當下性", "evidence": "例：受眾分析指出港人對收樓有集體焦慮", "how_to_execute": "例：開場用一單真實收樓場面鉤住觀眾"}}], "one_line_pitch": "例：呢個係一代人同一個時代的告別儀式"}}"""
    step = "bull_rebuttal" if opponent else "bull_researcher"
    return call_json(step, sys_, usr, 0.5, 6000, trace, required=["arguments"])


def bear_researcher(logline: str, genre: str, analyses: dict, trace: list, opponent: dict | None = None) -> dict:
    sys_ = "你係編劇室嘅挑刺派研究員（Bear Researcher）。你嘅職責係搵出呢個故事最易寫壞嘅位。不留情面，但每個批評都要附補救方案。只輸出 JSON。"
    round_hint = (
        f"\n【第 2 輪 · 駁論】力挺派啱啱話咗：{json.dumps(opponent, ensure_ascii=False)}\n"
        "逐條拆佢嘅論點（指出佢嘅執行要許有乜盲點），再強化你自己最致命嘅一條風險。\n"
        if opponent else ""
    )
    usr = f"""【輸出合約】淨係輸出一個 JSON object。頂層 keys 必須係 ["risks", "kill_shot"]。
- "risks" = array，必須有 3 個 object，每個 object 有 "risk" / "why_it_fails" / "remedy" 三個非空字串
- "kill_shot" = 一個非空字串
- 之前之後唔可以有任何文字，第一個字元必須係 {{

Logline：{logline}
類型：{genre}
分析師報告：{json.dumps(analyses, ensure_ascii=False)}
{round_hint}
提出三個最大嘅「會寫壞」風險，不留情面，但每個批評都要附補救方案。
結構示例（內容只係示意，唔好照抄）：
{{"risks": [{{"risk": "例：殯儀館題材易變獵奇展覽", "why_it_fails": "例：失去對死亡嘅尊重就冇戲可做", "remedy": "例：所有靈堂戲用固定長鏡頭，唔剪接渲染"}}], "kill_shot": "例：主角同阿媽嘅感情線唔夠深，補一場生前遺願戲先落筆"}}"""
    step = "bear_rebuttal" if opponent else "bear_researcher"
    return call_json(step, sys_, usr, 0.5, 6000, trace, required=["risks"])


# ── 統籌拍板（temp 0.2 — 委員會終結者）───────────────────

def script_manager(logline: str, genre: str, master_name: str, analyses: dict,
                   bull: dict, bear: dict, scene_count: int, trace: list) -> dict:
    sys_ = ("你係編劇室嘅統籌（Script Manager）。辯論唔係為咗共識，係為咗拍板。"
            "你逐條論點取捨，每個決定寫低理由，形成一份冇歧義嘅創作指令交畀主筆。只輸出 JSON。")
    usr = f"""Logline：{logline}
類型：{genre}
大師手法：{style_brief(master_name)}
分析師報告：{json.dumps(analyses, ensure_ascii=False)}
力挺派論點：{json.dumps(bull, ensure_ascii=False)}
挑刺派風險：{json.dumps(bear, ensure_ascii=False)}
預計場數：{scene_count}

拍板，輸出 JSON：
{{
  "decisions": [
    {{"topic": "", "verdict": "ACCEPT | REJECT | MODIFY", "reason": "", "instruction": "落實到指令層面嘅一句話"}},
    ...（逐條論點/風險都要有取捨）
  ],
  "beat_sheet": ["{scene_count} 個節拍，每個一句話，對應場次結構"],
  "style_directives": ["畀主筆嘅風格指令（含大師手法要求）"],
  "danger_list": ["主筆唔可以掂嘅雷區"],
  "protagonist_lock": {{"name": "", "desire": "", "flaw": ""}},
  "tone": ""
}}"""
    return call_json("script_manager", sys_, usr, 0.2, 8000, trace, required=["decisions", "beat_sheet"])


# ── 主筆編劇（唯一執筆者 · temp 0.8）─────────────────────

def head_writer_outline(logline: str, genre: str, master_name: str, directive: dict,
                        scene_count: int, trace: list) -> dict:
    sys_ = ("你係編劇室嘅主筆編劇（Head Writer）。全室得你一枝筆，統籌指令係聖旨，"
            "大師手法係你嘅筆法。先出分場大綱。只輸出 JSON。")
    usr = f"""Logline：{logline}
類型：{genre}
大師手法：{style_brief(master_name)}
統籌創作指令：{json.dumps(directive, ensure_ascii=False)}

寫一份 {scene_count} 場嘅分場大綱，輸出 JSON：
{{
  "title": "劇名",
  "scenes": [
    {{
      "no": 1,
      "heading": "INT./EXT. 場景 - 日/夜",
      "summary": "呢場做乜（兩句內）",
      "beats": ["場內節拍"],
      "exit_hook": "觀眾點解要追落去",
      "purpose": "呢場喺結構上嘅功能"
    }},
    ...
  ],
  "series_engine": "如果拍成劇集，呢個故事嘅持續引擎係乜"
}}"""
    return call_json("head_writer_outline", sys_, usr, 0.7, 8000, trace, required=["title", "scenes"])


def head_writer_scene(logline: str, genre: str, master_name: str, directive: dict,
                      outline: dict, scene_no: int, trace: list,
                      revision_notes: str = "", previous_draft: str = "", revision_count: int = 0) -> str:
    scene = next((s for s in outline.get("scenes", []) if int(s.get("no", 0)) == scene_no), None)
    sys_ = ("你係編劇室嘅主筆編劇（Head Writer）。執筆寫第 {n} 場完整劇本。"
            "劇本格式：場景 heading · 動作描寫（現在式）· 角色名大寫企中 · 對白。"
            "統籌指令係聖旨，禁忌唔可以掂。只輸出劇本本文，唔好輸出任何解釋。").format(n=scene_no)
    revise_hint = ""
    if revision_notes:
        revise_hint = f"""
【修稿任務 · 第 {revision_count} 次覆寫】Showrunner 判咗 REVISE，逐條要改：
{revision_notes}

你上一稿：
{previous_draft}

重寫第 {scene_no} 場：上面每一條都要落實改，但保留上一稿做得好嘅位（評分卡嘅 highlights）。
成場由 heading 重新出，唔好出「修改說明」。"""
    usr = f"""Logline：{logline}
類型：{genre}
大師手法：{style_brief(master_name)}
統籌創作指令：{json.dumps(directive, ensure_ascii=False)}
分場大綱：{json.dumps(outline.get("scenes", []), ensure_ascii=False)}

本場大綱：{json.dumps(scene, ensure_ascii=False)}
{revise_hint}
寫第 {scene_no} 場完整劇本（中文 1500-2500 字，約 2-4 頁）。
要求：
1. 跟足本場大綱嘅節拍同 exit hook
2. 對白要有人聲區分（每個角色講嘢方式唔同）
3. 大師手法嘅對白法則全程生效
4. 動作描寫係畫面（可拍），唔係小說心理描寫
5. 場景 heading 用標準格式：INT./EXT. 地點 - 日/夜"""
    step = f"head_writer_scene_r{revision_count}" if revision_count else "head_writer_scene"
    return strip_preamble(call_agent(step, sys_, usr, 0.8, 10000, trace))


def strip_preamble(text: str) -> str:
    """M3 有時喺劇本前漏思考文字 — 由第一個 INT./EXT. 場景 heading 開始斬。"""
    m = re.search(r"(?:^|\n)\s*(?:INT\.|EXT\.|內景|外景)", text, re.IGNORECASE)
    if m and m.start() > 0:
        return text[m.start():].lstrip("\n")
    return text


# ── 監製風控組（temp 0.1 — 求穩）─────────────────────────

def risk_team(logline: str, directive: dict, outline: dict, scene_text: str,
              master_name: str, trace: list) -> dict:
    sys_ = ("你係編劇室嘅監製風控組（Risk Team）。你唔改稿，只出紅旗報告："
            "連戲、邏輯、對白資訊量、節奏、拍攝可行性。只輸出 JSON。")
    usr = f"""Logline：{logline}
大師手法禁忌：{style_brief(master_name)}
統籌指令（雷區）：{json.dumps(directive.get('danger_list', []), ensure_ascii=False)}
分場大綱：{json.dumps(outline.get('scenes', []), ensure_ascii=False)}

第 1 場劇本：
{scene_text}

紅旗審查，輸出 JSON：
{{
  "flags": [
    {{"type": "CONTINUITY | LOGIC | EXPOSITION | PACING | BUDGET | TABOO", "severity": "HIGH | MED | LOW", "issue": "", "suggestion": ""}}
  ],
  "taboo_violations": ["統籌雷區違規（冇就空 array）"],
  "greenlights": ["明顯過關嘅位"],
  "overall": "一段總結"
}}"""
    return wrap_list(call_json("risk_team", sys_, usr, 0.1, 6000, trace), "flags")


# ── Showrunner 終審（temp 0.2）───────────────────────────

def showrunner(logline: str, genre: str, master_name: str, directive: dict,
               outline: dict, scene_text: str, risk: dict, trace: list,
               revision_count: int = 0, prev_verdict: dict | None = None) -> dict:
    sys_ = ("你係 Showrunner（終審）。你有 5 個評分維度：結構、人物、對白、手法忠實度、商業爽點。"
            "判決只有 PASS 定 REVISE（附 revision notes）。只輸出 JSON。")
    recheck_hint = ""
    if revision_count:
        recheck_hint = f"""
【覆審 · 第 {revision_count} 次修稿後】你上輪判咗 REVISE，revision notes 係：
{json.dumps((prev_verdict or {}).get('revision_notes', []), ensure_ascii=False)}
今稿係主筆照你嘅 notes 修過嘅版本。如果你嘅要求已落實 → PASS；如果仲有大問題 → REVISE 附新 notes。
唔好為雞毛蒜皮再判 REVISE — 修稿機會有限，要用喺大嘢上面。"""
    usr = f"""Logline：{logline}
類型：{genre}
大師手法：{style_brief(master_name)}
統籌指令：{json.dumps(directive, ensure_ascii=False)}
分場大綱：{json.dumps(outline.get('scenes', []), ensure_ascii=False)}
第 1 場劇本：{scene_text}
風控報告：{json.dumps(risk, ensure_ascii=False)}
{recheck_hint}
終審判決，輸出 JSON：
{{
  "decision": "PASS | REVISE",
  "scores": {{"structure": 0, "characters": 0, "dialogue": 0, "style_fidelity": 0, "commercial_payoff": 0}},
  "verdict_line": "一句判語",
  "highlights": ["最亮嘅位"],
  "revision_notes": ["如果 REVISE，要改乜（PASS 就空 array）"],
  "next_episode_hook": "呢集寫完，下一場最想睇乜"
}}"""
    step = f"showrunner_recheck_{revision_count}" if revision_count else "showrunner"
    return call_json(step, sys_, usr, 0.2, 6000, trace, required=["decision", "scores"])


# ── 模擬圍讀（temp 0.7 — 反饋迴路）───────────────────────

def table_read(logline: str, genre: str, outline: dict, scene_text: str,
               verdict: dict, trace: list) -> dict:
    sys_ = ("你係模擬圍讀主持人。三個 persona 朗讀完劇本後俾反應："
            "① 目標觀眾（反應直接、殘酷誠實）② 執行監製（諗錢同拍攝）"
            "③ 老戲骨演員（諗角色可唔可以演、對白順唔順口）。只輸出 JSON。")
    usr = f"""Logline：{logline}
類型：{genre}
分場大綱：{json.dumps(outline.get('scenes', []), ensure_ascii=False)}
第 1 場劇本：
{scene_text}
Showrunner 判決：{json.dumps(verdict, ensure_ascii=False)}

三個 persona 嘅圍讀反應，輸出 JSON：
{{
  "audience": {{"reaction": "", "quote": "佢最記得嘅一句台詞/畫面", "worry": ""}},
  "line_producer": {{"reaction": "", "cost_note": "", "worry": ""}},
  "veteran_actor": {{"reaction": "", "mouth_feel": "對白讀出口嘅手感", "worry": ""}},
  "room_temperature": "成個房嘅溫度總結（一句）"
}}"""
    return call_json("table_read", sys_, usr, 0.7, 6000, trace, required=["audience", "line_producer", "veteran_actor"])