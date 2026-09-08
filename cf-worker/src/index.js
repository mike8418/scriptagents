/**
 * ScriptAgents Web — Cloudflare Worker
 *
 * 全雲端編劇室嘅閘門（架構照抄 HSI 交易室打晒仗嘅 pattern）：
 *   GET  /            → 一頁式編劇室網站（讀 repo main 嘅 site/index.html）
 *   POST /api/run     → 表單開機：dispatch GitHub Action（logline/genre/master/notes）
 *   GET  /api/status  → 最新 run 狀態（頁面 polling 用）
 *   GET  /api/latest  → 最新劇本 JSON（API 用）
 *   GET  /?workflow=write&auto=true → cron-job.org 每日自動班
 *
 * 排程鐵律：GitHub cron 必有排隊延遲 → 一律 cron-job.org 外部 ping 本 Worker。
 * 防雙重 guard：10 分鐘內已有 dispatch 就跳過（?force=1 蓋過）。
 *
 * Secrets: GITHUB_TOKEN（classic PAT — repo+workflow scope，dispatch 用）
 */

const GITHUB_OWNER = "mike8418";
const GITHUB_REPO = "scriptagents";
const WORKFLOW_FILE = "write.yml";

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    // GET / — 一頁式網站（有 query 參數時照走 dispatcher）
    if (url.pathname === "/" && ![...url.searchParams.keys()].length) {
      return serveRepoFile(env, "site/index.html");
    }

    // POST /api/run — 表單開機
    if (url.pathname === "/api/run" && request.method === "POST") {
      return apiRun(request, env);
    }

    // GET /api/status — 最新 run 狀態
    if (url.pathname === "/api/status") {
      return apiStatus(env);
    }

    // GET /api/latest — 最新劇本 JSON
    if (url.pathname === "/api/latest") {
      return serveRepoFile(env, "outputs/latest/run.json", "application/json");
    }

    // ?workflow=write[&auto=true] — cron-job.org / 手動補飛（write / write.yml 都得）
    const workflow = url.searchParams.get("workflow");
    if (workflow) {
      if (workflow !== WORKFLOW_FILE && workflow !== "write") {
        return json({ error: "invalid workflow", valid: [WORKFLOW_FILE, "write"] });
      }
      const auto = url.searchParams.get("auto") === "true";
      const force = url.searchParams.get("force") === "1";
      return dispatchRun(env, {
        logline: url.searchParams.get("logline") || "",
        genre: url.searchParams.get("genre") || "警匪",
        master: url.searchParams.get("master") || "杜琪峯",
        notes: url.searchParams.get("notes") || "",
        auto: auto ? "true" : "false",
      }, force);
    }

    return json({
      service: "scriptagents-web",
      endpoints: {
        home: "/",
        run: "POST /api/run {logline, genre, master, notes}",
        status: "/api/status",
        latest: "/api/latest",
        auto_daily: "/?workflow=write&auto=true",
      },
    });
  },
};

// ── 表單開機 ─────────────────────────────────────────────
async function apiRun(request, env) {
  let body;
  try {
    body = await request.json();
  } catch {
    return json({ ok: false, error: "invalid JSON" }, 400);
  }

  const logline = String(body.logline || "").trim();
  const genre = String(body.genre || "警匪").trim();
  const master = String(body.master || "杜琪峯").trim();
  const notes = String(body.notes || "").trim();

  if (logline.length < 10) {
    return json({ ok: false, error: "logline 太短（至少 10 個字）" }, 400);
  }
  if (logline.length > 500) {
    return json({ ok: false, error: "logline 太長（最多 500 字）" }, 400);
  }

  return dispatchRun(env, { logline, genre, master, notes, auto: "false" }, false);
}

// ── dispatch + 防雙重 guard ───────────────────────────────
async function dispatchRun(env, inputs, force) {
  if (!force) {
    const recent = await recentRunExists(env);
    if (recent) {
      return json({
        ok: false,
        error: "編劇室開緊工（10 分鐘內已有 run）— 等今次完成先",
        run_url: recent,
      }, 429);
    }
  }

  const result = await triggerWorkflow(env.GITHUB_TOKEN, inputs);
  return json(result, result.ok ? 200 : 502);
}

async function triggerWorkflow(token, inputs) {
  const url = `https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/actions/workflows/${WORKFLOW_FILE}/dispatches`;

  for (let attempt = 1; attempt <= 3; attempt++) {
    try {
      const resp = await fetch(url, {
        method: "POST",
        headers: githubHeaders(token),
        body: JSON.stringify({ ref: "main", inputs }),
      });

      if (resp.status === 204) {
        const s = await apiStatusData(token);
        return {
          ok: true,
          run_number: s.latest_run_number,
          run_url: s.latest_run_url,
          note: "GitHub Actions 開咗工，約 3-6 分鐘",
        };
      }

      const text = await resp.text();
      console.log(`[FAIL] attempt ${attempt}: ${resp.status} — ${text.slice(0, 200)}`);
      if (resp.status === 401 || resp.status === 403 || resp.status === 422) {
        return { ok: false, error: `GitHub API ${resp.status}: ${text.slice(0, 150)}` };
      }
    } catch (err) {
      console.log(`[ERROR] attempt ${attempt}: ${err.message}`);
    }
    if (attempt < 3) await new Promise((r) => setTimeout(r, 2000 * attempt));
  }
  return { ok: false, error: "dispatch 3 次重試都失敗" };
}

async function recentRunExists(env) {
  const since = new Date(Date.now() - 10 * 60 * 1000).toISOString();
  try {
    const resp = await fetch(
      `https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/actions/runs?per_page=10&created=%3E%3D${since}`,
      { headers: githubHeaders(env.GITHUB_TOKEN) }
    );
    if (!resp.ok) return null; // fail-open：寧可重跑都唔可以漏跑
    const data = await resp.json();
    const run = (data.workflow_runs || []).find(
      (r) => r.path === `.github/workflows/${WORKFLOW_FILE}`
    );
    return run ? run.html_url : null;
  } catch {
    return null;
  }
}

// ── 狀態 ─────────────────────────────────────────────────
async function apiStatusData(token) {
  const resp = await fetch(
    `https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/actions/workflows/${WORKFLOW_FILE}/runs?per_page=1`,
    { headers: githubHeaders(token) }
  );
  if (!resp.ok) throw new Error(`list runs ${resp.status}`);
  const data = await resp.json();
  const run = (data.workflow_runs || [])[0];
  if (!run) {
    return { status: "none", conclusion: null, run_url: null, latest_run_number: null, latest_run_url: null };
  }
  return {
    status: run.status,               // queued / in_progress / completed
    conclusion: run.conclusion,      // success / failure / …
    run_number: run.run_number,
    run_url: run.html_url,
    created_at: run.created_at,
    latest_run_number: run.run_number,
    latest_run_url: run.html_url,
  };
}

async function apiStatus(env) {
  try {
    return json(await apiStatusData(env.GITHUB_TOKEN));
  } catch (err) {
    return json({ status: "error", error: err.message }, 502);
  }
}

// ── 由 repo main 讀檔案 serve（同 HSI pattern）────────────
async function serveRepoFile(env, repoPath, contentType = "text/html; charset=utf-8") {
  try {
    const resp = await fetch(
      `https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/contents/${repoPath}?ref=main`,
      {
        headers: {
          ...githubHeaders(env.GITHUB_TOKEN),
          Accept: "application/vnd.github.raw+json",
        },
      }
    );
    if (!resp.ok) {
      const body = await resp.text();
      console.log(`[SERVE-FAIL] ${repoPath}: ${resp.status} — ${body.slice(0, 300)}`);
      const msg = resp.status === 404
        ? "頁面仲未生成（等第一班編劇室 CI commit）"
        : `讀取失敗：GitHub API ${resp.status} — ${body.slice(0, 200)}`;
      return new Response(msg, {
        status: 502,
        headers: { "Content-Type": "text/plain; charset=utf-8" },
      });
    }
    const body = await resp.text();
    return new Response(body, {
      headers: {
        "Content-Type": contentType,
        "Cache-Control": "public, max-age=120",
      },
    });
  } catch (err) {
    return new Response(`Worker 錯誤：${err.message}`, {
      status: 500,
      headers: { "Content-Type": "text/plain; charset=utf-8" },
    });
  }
}

function githubHeaders(token) {
  return {
    Accept: "application/vnd.github+json",
    Authorization: `Bearer ${token}`,
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "cloudflare-worker-scriptagents",
  };
}

function json(obj, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Access-Control-Allow-Origin": "*",
    },
  });
}