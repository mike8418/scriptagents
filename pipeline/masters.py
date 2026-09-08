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
    "吳宇森": {
        "label": "吳宇森派 · 暴力美學",
        "structure_framework": "雙雄對立但惺惺相惜；情感推到極致再爆發成儀式化動作場面；犧牲換救贖。",
        "logline_formula": "兩個本應做敵人嘅男人，喺更大嘅邪惡面前互相成全。",
        "dialogue_rules": "對白浪漫化、講義氣多過講道理；關鍵對白會喺結尾迴響。",
        "signature": "白鴿慢鏡、雙槍芭蕾、男性情誼嘅歌劇化。",
        "forbidden_moves": ["冇儀式感嘅動作戲", "主角冇犧牲", "敵人純粹邪惡冇原則"],
    },
    "徐克": {
        "label": "徐克派 · 武俠奇觀",
        "structure_framework": "以武載道：每場打鬥都係人物關係嘅辯論；類型顛覆由視覺先行。",
        "logline_formula": "一個被時代夾住嘅異人，用一身冇人明嘅本事對抗一個正在成形嘅新秩序。",
        "dialogue_rules": "對白有江湖味同政治隱喻；金句短、快、有劍氣。",
        "signature": "視覺奇觀、武俠解構、亂世浪漫。",
        "forbidden_moves": ["為打而打冇人物含義", "視覺服務於冇嘢", "反傳統反到冇根"],
    },
    "黑澤明": {
        "label": "黑澤明派 · 史詩人本",
        "structure_framework": "天與地嘅構圖壓住人物掙扎；一個道德困境由頭帶到尾，結尾一個人性瞬間解鎖全片。",
        "logline_formula": "一個小人物喺腐敗系統入面做咗一件啱嘅事，代價係佢自己。",
        "dialogue_rules": "對白簡而重，人物立場講一句就企定；重要抉擇用行為唔用長對白。",
        "signature": "人本主義、天氣參與敘事、群像嘅道德試煉場。",
        "forbidden_moves": ["主角動機模糊", "冇一場戲冇用途", "絕望冇出路"],
    },
    "諾蘭": {
        "label": "諾蘭派 · 結構迷宮",
        "structure_framework": "用非線性結構做敘事引擎：時間/層級/視角交織，結尾對位收束；情感母題（愧疚/執念）扣住結構裝置。",
        "logline_formula": "一個被過去困住嘅人，要用一個反直覺嘅結構先可以解開件事。",
        "dialogue_rules": "對白資訊密度高但唔廢話；規則解釋要精準；關鍵台詞跨時間迴響。",
        "signature": "結構即主題、實景實感、IMAX 式決斷時刻。",
        "forbidden_moves": ["結構裝置同主題冇扣住", "規則講完又唔守", "感情線得個講字"],
    },
    "塔倫天奴": {
        "label": "塔倫天奴派 · 章回對白",
        "structure_framework": "章回式片段，開場日常閒談儲壓力，暴力喺你最唔為意嘅位爆；時間線任佢執。",
        "logline_formula": "一單江湖小事，因為每個人嘅自尊心，變咗一場冇人輸得起嘅困獸鬥。",
        "dialogue_rules": "對白係主角：吹水、講古、抬槓，每段閒談都有暗湧；角色靠講嘢建立。",
        "signature": "章回結構、長對白短暴力、流行文化考古。",
        "forbidden_moves": ["對白冇張力嘅閒談", "暴力冇後果", "冇嘢講嘅場口"],
    },
    "岩井俊二": {
        "label": "岩井俊二派 · 青春物哀",
        "structure_framework": "日常瑣碎累積成後勁；情感全部收埋，喺一個不經意瞬間先決堤；回憶同當下雙色調。",
        "logline_formula": "兩個人喺最好嘅年紀錯過咗一件事，要用成世人慢慢發現嗰件事係乜。",
        "dialogue_rules": "對白輕、多留白；講唔出口嘅先係重點；旁白式獨白可以出場。",
        "signature": "物哀、光害美感、青春嘅殘忍同溫柔。",
        "forbidden_moves": ["直接講我愛你/我恨你", "戲劇化衝突解決", "冇留白嘅場"],
    },
    "賈樟柯": {
        "label": "賈樟柯派 · 時代實錄",
        "structure_framework": "個人命運釘喺時代齒輪上；劇情淡化，生活質感同環境聲音做敘事；結尾唔收，留畀時代。",
        "logline_formula": "一個普通人喺巨變年代入面，守住一件冇人明點解咁重要嘅嘢。",
        "dialogue_rules": "對白口語化到似偷聽返嚟；方言/半鹹淡語言真實感行先。",
        "signature": "實錄感、流行曲做時代註腳、廢墟詩意。",
        "forbidden_moves": ["戲劇性巧合", "字幕講明時代背景", "冇煙火氣嘅佈景"],
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