"""validate_config — 設定相容性檢查（純代碼，零 LLM）。

對應 TradingAgents 嘅 validate_config 節點 + 技術方案 v3 設計：
  - 矛盾組合偵測：類型 × 大師手法 × 備註之間嘅硬衝突
  - 自動修正：能救嘅唔阻住（微短劇自動斬場數）
  - 網頁版語境：冇得中途問老闆 → 硬衝突照行但落警告入成品頁，
    統籌 prompt 會收到 warnings（拍板時會知點解事）

回傳 {"warnings": [...], "adjustments": [...], "hard_stops": []}
hard_stops 非空 → pipeline 拒絕開工（淨係用喺真係冇得救嘅組合）。
"""
from __future__ import annotations

from .masters import MASTERS


def _master_tags(name: str) -> set[str]:
    """大師派別標籤（用嚟做類型親和度規則）。"""
    tags = {
        "王晶": {"commercial", "comedy"},
        "杜琪峯": {"crime", "fatalism", "minimal_dialogue"},
        "周星馳": {"comedy", "drama", "underdog"},
        "韋家輝": {"mystery", "twist"},
        "彭浩翔": {"comedy", "absurd", "hk_local"},
        "吳宇森": {"action", "heroic", "melodrama"},
        "徐克": {"action", "fantasy", "visual"},
        "黑澤明": {"epic", "humanism", "period"},
        "諾蘭": {"structure_maze", "scifi"},
        "塔倫天奴": {"crime", "dialogue_masturbation", "chapters"},
        "岩井俊二": {"youth", "mono_no_aware", "poetic"},
        "賈樟柯": {"realism", "era", "documentary"},
    }
    return tags.get(name, set())


# 類型 ↔ 大師親和度（唔喺度 = 有張力，警告但唔停；!! = 硬衝突）
_AFFINITY: dict[str, dict[str, str]] = {
    "文藝": {"王晶": "衝突：王晶派係密集爽點商業引擎，文藝類型靠留白餘味 — 統籌會被迫二揀一，成品有機會兩頭唔到岸"},
    "青春": {"黑澤明": "張力組合：黑澤明式史詩人本主義寫青春題，重心會自然移去「後青春嘅重量」— 可行但要統籌刻意平衡"},
    "微短劇": {
        "黑澤明": "衝突：史詩式沉緩節奏 vs 微短劇 90 秒一鉤 — 統籌會自動轉快，手法忠實度評分會跌",
        "岩井俊二": "張力組合：物哀慢鏡喺微短劇只剩一兩個鏡位用得着",
    },
    "古裝": {"彭浩翔": "張力組合：市井粗口幽默放落古裝要重新校語感（建議備註話明語言質感）"},
    "戰爭": {"王晶": "衝突：喜劇爽感處理戰爭題材易踩冒犯雷 — 除非明確係荒謬喜劇路線"},
}


def validate_config(cfg: dict) -> dict:
    warnings: list[str] = []
    adjustments: list[str] = []
    hard_stops: list[str] = []

    genre = cfg.get("genre", "")
    master = cfg.get("master", "")
    notes = (cfg.get("notes") or "").lower()
    scene_count = int(cfg.get("scene_count", 9))

    # 1. 類型 × 大師親和度
    rule = _AFFINITY.get(genre, {}).get(master)
    if rule:
        warnings.append(f"[類型×手法] {genre} × {master}：{rule}")

    # 2. 微短劇場數自動斬（呢個唔係警告，係自動修正）
    if genre == "微短劇" and scene_count > 4:
        cfg["scene_count"] = 4
        adjustments.append(f"微短劇自動斬場數 {scene_count} → 4（90 秒一鉤嘅體載冇得咁多場）")

    # 3. 備註 × 大師禁忌
    m = MASTERS.get(master)
    if m:
        if "大團圓" in notes and "大團圓" in "".join(m.get("forbidden_moves", [])):
            warnings.append(f"[備註×禁忌] 你想要大團圓結局，但 {master}派禁忌明文寫住「大團圓冇代價」— 統籌會以大師手法為準，最多做到「有代價嘅準團圓」")
        if ("搞笑" in notes or "爆笑" in notes) and master in ("杜琪峯", "黑澤明", "岩井俊二", "賈樟柯"):
            warnings.append(f"[備註×手法] 你要求爆笑，但 {master}派係沉重系手法 — 統籌會改做「沉重框架偶有幽默位」")

    # 4. logline 長度（真係冇得救先 hard stop）
    if len((cfg.get("logline") or "").strip()) < 10:
        hard_stops.append("Logline 太短（<10 字）— 冇故事骨幹，唔開工")

    # 5. notes 過長會吃 token — 提示但唔停
    if len(cfg.get("notes") or "") > 2000:
        warnings.append("[備註] 自由備註超過 2000 字 — 統籌會優先消化前面 2000 字")

    return {"warnings": warnings, "adjustments": adjustments, "hard_stops": hard_stops}