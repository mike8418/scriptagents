"""大師手法庫（Style Bible 預設 prompt pack）+ 類型清單。

MVP 先出香港五派（概念文檔優先次序：香港四派 + 彭浩翔）。
每個 pack 注入主筆 + 統籌 + Showrunner prompt（Showrunner 評分有「手法忠實度」維度）。
"""
from __future__ import annotations

GENRES = [
    "警匪", "黑幫", "喜劇", "愛情", "懸疑", "科幻", "驚悚", "家庭",
    "商戰", "古裝", "奇幻", "年代", "職人", "青春", "政治", "戰爭",
    "文藝", "微短劇",
]

MASTERS: dict[str, dict] = {
    "王晶": {
        "label": "王晶派 · 密集爽點",
        "structure_framework": "三分鐘一個小鉤子，十分鐘一個大反轉；結構服務爽感，節奏行先過深度。",
        "logline_formula": "一個賤精/衰人被迫做好事，笑住贏到最後。",
        "dialogue_rules": "對白抵死、快、有梗；角色講嘢永遠比觀眾預期快半拍。",
        "signature": "市井智慧、賤格幽默、計算精準嘅通俗劇引擎。",
        "forbidden_moves": ["長篇內心獨白", "冇笑位嘅連續三場戲", "角色自憐超過 30 秒"],
    },
    "杜琪峯": {
        "label": "杜琪峯派 · 靜與爆",
        "structure_framework": "靜極必爆：用長時間靜場儲壓力，一次爆發解鎖全部；結尾留宿命餘味。",
        "logline_formula": "兩個各有原則嘅人困在同一個局，結局早註定，但過程令你唔捨得眨眼。",
        "dialogue_rules": "對白少而重；角色唔解釋自己，用行為講嘢；沉默都係對白。",
        "signature": "場面調度、群像站位、宿命感、男人之間唔講出口嘅義。",
        "forbidden_moves": ["角色解釋自己動機超過三句", "煽情配樂提示觀眾幾時感動", "大團圓冇代價"],
    },
    "周星馳": {
        "label": "周星馳派 · 悲喜反差",
        "structure_framework": "先將小人物踩到最底（喜劇處理），佢掙扎尊嚴嘅過程同時係全片最悲嘅部分；笑住喊。",
        "logline_formula": "一個俾人睇死嘅小人物，用最卑微嘅方式贏返一次尊嚴。",
        "dialogue_rules": "對白看似無厘頭實則句句有底；重要嘢用笑話講，講完先知痛。",
        "signature": "小人物尊嚴、悲喜同框、誇張表演下嘅真心。",
        "forbidden_moves": ["冇俾主角真正痛過", "純搞笑冇感情底", "配角冇記憶點"],
    },
    "韋家輝": {
        "label": "韋家輝派 · 敘事詭計",
        "structure_framework": "開場俾觀眾一個看似合理嘅假設，結尾反轉令佢重新理解成件事；執念驅動人物。",
        "logline_formula": "一個執念深種嘅人追查一件事，真相改寫佢對自己嘅全部認知。",
        "dialogue_rules": "對白表面講一件事，其實講另一件；關鍵台詞要可以喺結尾讀出第二個意思。",
        "signature": "敘事詭計、宿命執念、銀河映像式雙線交纏。",
        "forbidden_moves": ["反轉冇伏筆", "為扭而扭", "主角執念冇根源"],
    },
    "彭浩翔": {
        "label": "彭浩翔派 · 市井黑色幽默",
        "structure_framework": "一件荒謬小事滾雪球到不可收拾；每個決定都合理，夾埋嚟卻係災難。",
        "logline_formula": "一個普通港男為咗一個自私嘅小理由，捲入一單越描越黑嘅荒謬事件。",
        "dialogue_rules": "對白貼地、粗口生活化、認真討論荒謬嘢（一本正經胡說八道）。",
        "signature": "港式市井、黑色幽默、賤格但有底線嘅人情味。",
        "forbidden_moves": ["荒謬冇內在邏輯", "離地中產視角", "教訓觀眾"],
    },
}

DEFAULT_MASTER = "杜琪峯"
DEFAULT_GENRE = "警匪"


def master_pack(name: str) -> dict:
    """攞大師 prompt pack；唔識嘅名 fallback 去預設。"""
    return MASTERS.get(name, MASTERS[DEFAULT_MASTER])


def style_brief(name: str) -> str:
    """將大師 pack 濃縮成一段可注入 prompt 嘅文字。"""
    m = master_pack(name)
    return (
        f"【大師手法：{m['label']}】\n"
        f"- 結構框架：{m['structure_framework']}\n"
        f"- Logline 公式：{m['logline_formula']}\n"
        f"- 對白法則：{m['dialogue_rules']}\n"
        f"- 招牌質感：{m['signature']}\n"
        f"- 禁忌：{'；'.join(m['forbidden_moves'])}"
    )