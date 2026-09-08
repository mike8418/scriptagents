"""ScriptAgents pipeline 主入口 — GitHub Actions 入面跑。

用法：
  python -m pipeline.run --logline "..." --genre 警匪 --master 杜琪峯 --notes "..."
  python -m pipeline.run --auto          # 由 config/logline_queue.json 輪選

流程（全雲端，11 次 LLM 調用）：
  分析師×3 → 力挺vs挑刺 → 統籌拍板 → 主筆大綱 → 主筆第1場 → 風控 → Showrunner → 圍讀
輸出（outputs/，commit 返 repo 畀 Worker serve）：
  <run_id>/…全紀錄 · latest/ 指針 · index.json 歷史 · site/index.html 一頁網站
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

from . import agents, site
from .masters import DEFAULT_GENRE, DEFAULT_MASTER, GENRES, MASTERS, master_pack

ROOT = Path(__file__).resolve().parent.parent
OUTPUTS = ROOT / "outputs"
CQ = ROOT / "config" / "logline_queue.json"

HKT = timezone(timedelta(hours=8))


def now_hkt() -> str:
    return datetime.now(HKT).strftime("%Y-%m-%d %H:%M HKT")


def load_queue() -> dict:
    return json.loads(CQ.read_text(encoding="utf-8")) if CQ.exists() else {"next": 0, "loglines": []}


def save_queue(q: dict) -> None:
    CQ.parent.mkdir(parents=True, exist_ok=True)
    CQ.write_text(json.dumps(q, ensure_ascii=False, indent=2), encoding="utf-8")


def pick_auto() -> dict:
    """auto 模式：輪選 logline 隊列 + 隨機組合類型/大師，保證出街有變化。"""
    import random

    q = load_queue()
    idx = q["next"] % len(q["loglines"])
    item = q["loglines"][idx]
    q["next"] = idx + 1
    save_queue(q)

    master = item.get("master") or random.choice(list(MASTERS))
    return {
        "logline": item["logline"],
        "genre": item.get("genre") or random.choice(GENRES),
        "master": master,
        "notes": item.get("notes", ""),
        "auto": True,
    }


def run(cfg: dict) -> dict:
    run_id = datetime.now(HKT).strftime("%Y%m%d_%H%M")
    logline, genre, master_name = cfg["logline"], cfg["genre"], cfg["master"]
    notes = cfg.get("notes", "")
    scene_count = int(cfg.get("scene_count", 9))

    print(f"[ScriptAgents] 開工 run={run_id} 類型={genre} 大師={master_name}")
    print(f"[ScriptAgents] Logline: {logline}")

    t_start = time.time()
    trace: list = []
    state: dict = {"run_id": run_id, "config": cfg}

    # 1. 分析師團隊
    print("[1/9] 分析師團隊：人物 / 受眾 / 結構 …")
    analyses = {
        "character": agents.analyst_character(logline, genre, trace),
        "audience": agents.analyst_audience(logline, genre, trace),
        "structure": agents.analyst_structure(logline, genre, scene_count, trace),
    }
    if notes:
        analyses["boss_notes"] = notes

    # 2. 辯論：力挺派 vs 挑刺派
    print("[2/9] 力挺派 vs 挑刺派 …")
    bull = agents.bull_researcher(logline, genre, analyses, trace)
    bear = agents.bear_researcher(logline, genre, analyses, trace)

    # 3. 統籌拍板
    print("[3/9] 統籌拍板（論點取捨）…")
    directive = agents.script_manager(logline, genre, master_name, analyses, bull, bear, scene_count, trace)

    # 4. 主筆：分場大綱
    print(f"[4/9] 主筆分場大綱（{scene_count} 場）…")
    outline = agents.head_writer_outline(logline, genre, master_name, directive, scene_count, trace)
    actual_scenes = len(outline.get("scenes", []))

    # 5. 主筆：第 1 場完整劇本
    print("[5/9] 主筆執筆第 1 場 …")
    scene_text = agents.head_writer_scene(logline, genre, master_name, directive, outline, 1, trace)

    # 6. 監製風控
    print("[6/9] 監製風控紅旗審查 …")
    risk = agents.risk_team(logline, directive, outline, scene_text, master_name, trace)

    # 7. Showrunner 終審
    print("[7/9] Showrunner 終審 …")
    verdict = agents.showrunner(logline, genre, master_name, directive, outline, scene_text, risk, trace)

    # 8. 模擬圍讀
    print("[8/9] 模擬圍讀（3 persona）…")
    read = agents.table_read(logline, genre, outline, scene_text, verdict, trace)

    elapsed = round(time.time() - t_start, 1)
    print(f"[9/9] 完成，全流程 {elapsed}s · {len(trace)} 次 LLM 調用")

    state.update({
        "finished_at": now_hkt(),
        "elapsed_seconds": elapsed,
        "title": outline.get("title", ""),
        "analyses": analyses,
        "bull": bull,
        "bear": bear,
        "directive": directive,
        "outline": outline,
        "scene_1": scene_text,
        "risk": risk,
        "verdict": verdict,
        "table_read": read,
        "trace": trace,
    })

    # ── 寫 outputs ──
    run_dir = OUTPUTS / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "run.json").write_text(
        json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    (run_dir / "scene_1.md").write_text(f"# {state['title']}\n\n{scene_text}", encoding="utf-8")

    latest = OUTPUTS / "latest"
    latest.mkdir(parents=True, exist_ok=True)
    (latest / "run.json").write_text(
        json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

    # 歷史索引（保留最近 60 個 run）
    index_path = OUTPUTS / "index.json"
    index = json.loads(index_path.read_text(encoding="utf-8")) if index_path.exists() else []
    index.insert(0, {
        "run_id": run_id,
        "finished_at": state["finished_at"],
        "title": state["title"],
        "logline": logline,
        "genre": genre,
        "master": master_name,
        "decision": verdict.get("decision", ""),
        "auto": cfg.get("auto", False),
        "elapsed_seconds": elapsed,
    })
    index = index[:60]
    index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")

    # ── 生成一頁網站 ──
    site.build(state, index)
    print(f"[ScriptAgents] ✓ outputs/{run_id}/ + site/index.html 已更新")
    return state


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--logline")
    p.add_argument("--genre", default=DEFAULT_GENRE)
    p.add_argument("--master", default=DEFAULT_MASTER)
    p.add_argument("--notes", default="")
    p.add_argument("--scene-count", type=int, default=9)
    p.add_argument("--auto", action="store_true")
    args = p.parse_args()

    if args.auto:
        cfg = pick_auto()
    else:
        if not args.logline or len(args.logline.strip()) < 5:
            print("ERROR: --logline 必須至少 5 個字", file=sys.stderr)
            return 1
        cfg = {
            "logline": args.logline.strip(),
            "genre": args.genre if args.genre in GENRES else DEFAULT_GENRE,
            "master": args.master if args.master in MASTERS else DEFAULT_MASTER,
            "notes": args.notes.strip(),
            "scene_count": args.scene_count,
            "auto": False,
        }

    cfg.setdefault("scene_count", args.scene_count)
    state = run(cfg)
    print(f"\n=== 劇名：{state['title']} ===")
    print(f"=== Showrunner：{state['verdict'].get('decision', '?')} — {state['verdict'].get('verdict_line', '')} ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())