# ScriptAgents · AI 編劇室

多智能體劇本創作系統 — 把 [TradingAgents](https://github.com/tauricresearch/tradingagents)
（多 agent 辯論決策交易框架）嘅骨架移植到編劇室，全雲端運行，唔使開 Mac。

## 架構

```
瀏覽器 → https://script.anidit.com
   ↓
Cloudflare Worker (cf-worker/) — 網站 + dispatch 閘門
   ↓ workflow_dispatch
GitHub Actions (.github/workflows/write.yml)
   ↓ 跑 pipeline/（純 stdlib Python，零第三方依賴）
MiniMax M3 (api.minimaxi.com/v1)
   ↓
分析師×3 → 力挺vs挑刺辯論 → 統籌拍板 → 主筆大綱+第1場 → 風控 → Showrunner → 圍讀
   ↓ commit outputs/ + site/index.html
Worker serve 一頁式成品頁
```

排程鐵律：**唔用 GitHub cron**（會排隊延遲 15 分鐘至幾個鐘）。
每日自動班由 cron-job.org 定時 ping Worker `/?workflow=write&auto=true` 觸發。

## Pipeline（11 個 agent）

| 崗位 | 溫度 | 職責 |
|---|---|---|
| 人物分析師 | 0.3 | 主角慾望/恐懼、對手、壓力來源 |
| 受眾分析師 | 0.3 | 目標觀眾、平台、爽點、雷區 |
| 結構分析師 | 0.3 | 節拍表（開場鉤子→中點反轉→低谷→高潮） |
| 力挺派研究員 | 0.5 | 三個「非寫不可」論點 |
| 挑刺派研究員 | 0.5 | 三個「會寫壞」風險 + 補救 |
| 統籌（拍板） | 0.2 | 逐條論點取捨 → 冇歧義嘅創作指令 |
| 主筆編劇 | 0.8 | 唯一執筆者：分場大綱 + 第 1 場完整劇本 |
| 監製風控組 | 0.1 | 連戲/邏輯/對白/節奏/雷區紅旗 |
| Showrunner | 0.2 | 終審 PASS/REVISE + 5 維度評分 |
| 模擬圍讀 | 0.7 | 目標觀眾 / 執行監製 / 老戲骨 反饋 |

## 大師手法庫（MVP 香港五派）

王晶 · 杜琪峯 · 周星馳 · 韋家輝 · 彭浩翔 — 每派一個 prompt pack
（結構框架 / logline 公式 / 對白法則 / 招牌質感 / 禁忌），注入主筆 + 統籌 + Showrunner。

## 手動開機

```bash
# 本地（要 MINIMAX_API_KEY 環境變量）
python -m pipeline.run --logline "一句話 logline" --genre 警匪 --master 杜琪峯

# 雲端 — 表單：https://script.anidit.com 或
curl -X POST https://script.anidit.com/api/run \
  -H 'Content-Type: application/json' \
  -d '{"logline":"...","genre":"警匪","master":"杜琪峯","notes":""}'
```

## Secrets（GitHub Actions）

- `MINIMAX_API_KEY` — MiniMax 國內端 key（api.minimaxi.com）

## Secrets（Cloudflare Worker）

- `GITHUB_TOKEN` — classic PAT（repo + workflow scope，dispatch 用）