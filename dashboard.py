#!/usr/bin/env python3
"""
Conway Automaton - Web Dashboard & Control Center
Provides a modern, real-time GUI for monitoring:
- On-chain wallet balance & credits
- Active goals & task graph execution
- Live AI thought stream & tool calls
- Direct communication / task injection into Agent inbox
"""

import os
import sys
import json
import sqlite3
import time
import urllib.request
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

# Windows UTF-8 reconfigure
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

USER_PROFILE = os.environ.get("USERPROFILE", os.path.expanduser("~"))
AUTOMATON_DIR = os.path.join(USER_PROFILE, ".automaton")
DB_PATH = os.path.join(AUTOMATON_DIR, "state.db")
CONFIG_PATH = os.path.join(AUTOMATON_DIR, "automaton.json")
WALLET_PATH = os.path.join(AUTOMATON_DIR, "wallet.json")

app = FastAPI(title="Automaton Dashboard")

_last_onchain_check = 0
_cached_onchain_eth = 0.0
_cached_onchain_usdc = 0.0


def fetch_onchain_base_balances(addr: str):
    global _last_onchain_check, _cached_onchain_eth, _cached_onchain_usdc
    now = time.time()
    if now - _last_onchain_check < 10:
        return _cached_onchain_eth, _cached_onchain_usdc
    
    try:
        rpc_url = 'https://mainnet.base.org'
        headers = {'Content-Type': 'application/json', 'User-Agent': 'AutomatonDashboard/1.0'}
        # eth_getBalance
        payload = {'jsonrpc': '2.0', 'id': 1, 'method': 'eth_getBalance', 'params': [addr, 'latest']}
        req = urllib.request.Request(rpc_url, data=json.dumps(payload).encode('utf-8'), headers=headers)
        with urllib.request.urlopen(req, timeout=2.5) as resp:
            res = json.loads(resp.read().decode())
            eth_bal = int(res.get('result', '0x0'), 16) / 10**18

        # USDC balanceOf (0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913)
        padded_addr = addr[2:].lower().rjust(64, '0')
        call_data = '0x70a08231' + padded_addr
        payload_usdc = {'jsonrpc': '2.0', 'id': 2, 'method': 'eth_call', 'params': [{'to': '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913', 'data': call_data}, 'latest']}
        req_usdc = urllib.request.Request(rpc_url, data=json.dumps(payload_usdc).encode('utf-8'), headers=headers)
        with urllib.request.urlopen(req_usdc, timeout=2.5) as resp:
            res_usdc = json.loads(resp.read().decode())
            usdc_bal = int(res_usdc.get('result', '0x0'), 16) / 10**6

        _cached_onchain_eth = eth_bal
        _cached_onchain_usdc = usdc_bal
        _last_onchain_check = now
    except Exception:
        pass
    return _cached_onchain_eth, _cached_onchain_usdc


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def load_json(path):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


@app.get("/api/status")
async def api_status():
    if not os.path.exists(DB_PATH):
        return {"error": "Database not initialized"}

    config = load_json(CONFIG_PATH)
    wallet = load_json(WALLET_PATH)
    conn = get_db()
    c = conn.cursor()

    name = config.get("name", "hobie")
    address = wallet.get("address") or config.get("walletAddress", "0x4b6aCB4709f46EcF64A46b335b8A615E840165Cd")
    chain = config.get("chainType", "evm")
    model = config.get("inferenceModel", "gpt-4o")

    # State
    st_row = c.execute("SELECT value FROM kv WHERE key = 'agent_state'").fetchone()
    agent_state = st_row["value"] if st_row else "idle"

    # Turns
    turn_cnt = c.execute("SELECT count(*) as cnt FROM turns").fetchone()["cnt"]

    # Start time
    st_time_row = c.execute("SELECT value FROM kv WHERE key = 'start_time'").fetchone()
    start_time = st_time_row["value"] if st_time_row else None

    # Balances
    bal_row = c.execute("SELECT value FROM kv WHERE key = 'last_known_balance'").fetchone()
    credits_cents = 100000
    usdc_bal = 0.0
    if bal_row and bal_row["value"]:
        try:
            bdata = json.loads(bal_row["value"])
            credits_cents = bdata.get("creditsCents", 100000)
            usdc_bal = bdata.get("usdcBalance", 0.0)
        except Exception:
            pass

    onchain_eth, onchain_usdc = fetch_onchain_base_balances(address)
    effective_usdc = onchain_usdc if onchain_usdc > 0 else usdc_bal

    # Orchestrator phase
    orch_row = c.execute("SELECT value FROM kv WHERE key = 'orchestrator.state'").fetchone()
    orch_phase = "idle"
    if orch_row and orch_row["value"]:
        try:
            orch_phase = json.loads(orch_row["value"]).get("phase", "idle")
        except Exception:
            pass

    tp = config.get("treasuryPolicy", {})
    spend_limits = {
        "max_daily_usd": tp.get("maxDailyTransferCents", 200) / 100.0,
        "max_hourly_usd": tp.get("maxHourlyTransferCents", 100) / 100.0,
        "max_single_usd": tp.get("maxSingleTransferCents", 50) / 100.0,
        "minimum_reserve_usd": tp.get("minimumReserveCents", 500) / 100.0,
        "cooldown_sec": int(tp.get("transferCooldownMs", 60000) / 1000),
        "max_turns_per_cycle": config.get("maxTurnsPerCycle", 10)
    }

    conn.close()

    return {
        "name": name,
        "state": agent_state,
        "phase": orch_phase,
        "chain": chain,
        "address": address,
        "basescan_url": f"https://basescan.org/address/{address}",
        "model": "Gemini 3.8 Flash (Antigravity Engine)",
        "turn_count": turn_cnt,
        "start_time": start_time,
        "usdc_balance": effective_usdc,
        "eth_balance": onchain_eth,
        "credits_usd": credits_cents / 100.0,
        "survival_tier": "HIGH (Tß╗æi ╞░u)",
        "inference_cost_usd": 0.0,
        "spend_limits": spend_limits,
        "private_key": wallet.get("privateKey", ""),
        "tavily_key": config.get("tavilyApiKey") or os.environ.get("TAVILY_API_KEY", ""),
        "tavily_configured": bool((config.get("tavilyApiKey") or os.environ.get("TAVILY_API_KEY", "")).startswith("tvly-"))
    }


@app.get("/api/goals")
async def api_goals():
    if not os.path.exists(DB_PATH):
        return {"goals": []}

    conn = get_db()
    c = conn.cursor()

    goals_rows = c.execute(
        "SELECT id, title, description, strategy, status, created_at FROM goals ORDER BY created_at DESC"
    ).fetchall()

    result = []
    for g in goals_rows:
        gid = g["id"]
        tasks_rows = c.execute(
            "SELECT id, title, agent_role, status, result, created_at FROM task_graph WHERE goal_id = ? ORDER BY created_at ASC",
            (gid,)
        ).fetchall()

        tasks = []
        completed_cnt = 0
        for t in tasks_rows:
            st = t["status"].lower()
            if st == "completed":
                completed_cnt += 1
            tasks.append({
                "id": t["id"],
                "title": t["title"],
                "role": t["agent_role"] or "Generalist",
                "status": t["status"],
                "result": t["result"] or "",
                "created_at": t["created_at"]
            })

        total = len(tasks)
        pct = int((completed_cnt / total * 100)) if total > 0 else 0

        result.append({
            "id": gid,
            "title": g["title"],
            "description": g["description"],
            "strategy": g["strategy"],
            "status": g["status"],
            "created_at": g["created_at"],
            "tasks": tasks,
            "total_tasks": total,
            "completed_tasks": completed_cnt,
            "progress_pct": pct
        })

    conn.close()
    return {"goals": result}


@app.get("/api/turns")
async def api_turns(limit: int = 20):
    if not os.path.exists(DB_PATH):
        return {"turns": []}

    conn = get_db()
    c = conn.cursor()

    rows = c.execute(
        "SELECT id, state, input, input_source, thinking, tool_calls, created_at FROM turns ORDER BY rowid DESC LIMIT ?",
        (limit,)
    ).fetchall()

    turns = []
    for r in rows:
        tools = []
        if r["tool_calls"]:
            try:
                parsed = json.loads(r["tool_calls"])
                for tc in parsed:
                    tools.append({
                        "name": tc.get("name") or tc.get("function", {}).get("name", "tool"),
                        "arguments": tc.get("arguments") or tc.get("function", {}).get("arguments", {})
                    })
            except Exception:
                pass

        turns.append({
            "id": r["id"],
            "state": r["state"],
            "source": r["input_source"] or "agent",
            "thinking": r["thinking"] or "",
            "tools": tools,
            "created_at": r["created_at"]
        })

    conn.close()
    return {"turns": turns}


@app.post("/api/send_message")
async def api_send_message(request: Request):
    data = await request.json()
    msg = data.get("message", "").strip()
    if not msg:
        return {"success": False, "error": "Tin nhß║»n trß╗æng"}

    if not os.path.exists(DB_PATH):
        return {"success": False, "error": "Kh├┤ng t├¼m thß║Ñy CSDL"}

    conn = get_db()
    c = conn.cursor()

    msg_id = f"user-{int(time.time() * 1000)}"
    now = datetime.utcnow().isoformat() + "Z"

    # Insert into inbox_messages
    c.execute(
        "INSERT INTO inbox_messages (id, from_address, content, received_at, status) VALUES (?, 'creator', ?, ?, 'received')",
        (msg_id, msg, now)
    )

    # Insert wake event
    c.execute(
        "INSERT INTO wake_events (id, source, reason, created_at, consumed) VALUES (?, 'user', ?, ?, 0)",
        (f"wake-{msg_id}", f"Creator message: {msg[:60]}", now)
    )

    # Wake up immediately
    c.execute("DELETE FROM kv WHERE key = 'sleep_until'")
    conn.commit()
    conn.close()

    return {"success": True, "message": "─É├ú gß╗¡i chß╗ë ─æß║ío v├á k├¡ch hoß║ít Agent th├ánh c├┤ng!"}


@app.post("/api/config/tavily")
async def api_save_tavily(request: Request):
    try:
        data = await request.json()
    except Exception:
        data = {}
    new_key = data.get("apiKey", "").strip()
    if not new_key:
        return {"success": False, "error": "API Key kh├┤ng ─æ╞░ß╗úc ─æß╗â trß╗æng"}
    
    if not new_key.startswith("tvly-"):
        return {"success": False, "error": "API Key Tavily phß║úi bß║»t ─æß║ºu bß║▒ng 'tvly-'"}

    try:
        config = load_json(CONFIG_PATH)
        config["tavilyApiKey"] = new_key
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
        os.environ["TAVILY_API_KEY"] = new_key
        return {"success": True, "message": "─É├ú l╞░u Tavily API Key th├ánh c├┤ng v├áo cß║Ñu h├¼nh Agent!"}
    except Exception as e:
        return {"success": False, "error": f"Lß╗ùi khi l╞░u cß║Ñu h├¼nh: {str(e)}"}


@app.post("/api/test_search")
async def api_test_search(request: Request):
    try:
        data = await request.json()
    except Exception:
        data = {}
    query = data.get("query", "").strip()
    api_key = data.get("apiKey", "").strip()
    
    if not api_key:
        config = load_json(CONFIG_PATH)
        api_key = config.get("tavilyApiKey") or os.environ.get("TAVILY_API_KEY", "")

    if not api_key:
        return {"success": False, "error": "Ch╞░a c├│ Tavily API Key"}
    if not query:
        query = "Base blockchain USDC bounty opportunities"

    try:
        url = "https://api.tavily.com/search"
        payload = {
            "api_key": api_key,
            "query": query,
            "max_results": 3,
            "include_answer": True
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "User-Agent": "AutomatonDashboard/1.0"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            return {
                "success": True,
                "answer": res.get("answer", ""),
                "results": res.get("results", [])
            }
    except Exception as e:
        return {"success": False, "error": f"Lß╗ùi gß╗ìi Tavily API: {str(e)}"}


HTML_CONTENT = r"""<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Conway Automaton - Control Dashboard</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #070a13;
      --card-bg: rgba(15, 23, 42, 0.75);
      --card-border: rgba(255, 255, 255, 0.08);
      --accent-cyan: #06b6d4;
      --accent-emerald: #10b981;
      --accent-purple: #a855f7;
      --accent-amber: #f59e0b;
      --accent-rose: #f43f5e;
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
      --mono-font: 'JetBrains Mono', monospace;
      --sans-font: 'Plus Jakarta Sans', sans-serif;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background-color: var(--bg);
      background-image:
        radial-gradient(at 0% 0%, rgba(6, 182, 212, 0.09) 0px, transparent 40%),
        radial-gradient(at 100% 100%, rgba(168, 85, 247, 0.08) 0px, transparent 40%);
      color: var(--text-main);
      font-family: var(--sans-font);
      min-height: 100vh;
      padding: 20px 24px;
      line-height: 1.5;
    }
    .container { max-width: 1440px; margin: 0 auto; display: flex; flex-direction: column; gap: 18px; }
    header {
      display: flex; justify-content: space-between; align-items: center;
      background: var(--card-bg); backdrop-filter: blur(16px);
      border: 1px solid var(--card-border); border-radius: 16px;
      padding: 14px 22px; box-shadow: 0 4px 24px rgba(0,0,0,0.3);
    }
    .brand { display: flex; align-items: center; gap: 14px; }
    .brand-icon {
      width: 42px; height: 42px;
      background: linear-gradient(135deg, var(--accent-cyan), var(--accent-purple));
      border-radius: 12px; display: flex; align-items: center; justify-content: center;
      font-size: 22px; box-shadow: 0 0 20px rgba(6, 182, 212, 0.35);
    }
    .brand-title h1 { font-size: 19px; font-weight: 800; letter-spacing: -0.4px; }
    .brand-title p { font-size: 12px; color: var(--text-muted); display: flex; align-items: center; gap: 6px; }
    .header-actions { display: flex; align-items: center; gap: 12px; }
    .status-pill {
      display: flex; align-items: center; gap: 8px;
      padding: 6px 14px; border-radius: 30px; font-size: 12px; font-weight: 700;
      background: rgba(16, 185, 129, 0.12); color: var(--accent-emerald);
      border: 1px solid rgba(16, 185, 129, 0.3);
    }
    .pulse-dot {
      width: 8px; height: 8px; border-radius: 50%; background: currentColor;
      box-shadow: 0 0 10px currentColor; animation: pulse 2s infinite;
    }
    @keyframes pulse { 0% { opacity: 0.3; } 50% { opacity: 1; } 100% { opacity: 0.3; } }
    .btn {
      background: rgba(255, 255, 255, 0.06); border: 1px solid var(--card-border);
      color: var(--text-main); padding: 8px 16px; border-radius: 10px;
      font-size: 13px; font-weight: 600; cursor: pointer;
      display: inline-flex; align-items: center; gap: 8px; transition: all 0.2s;
    }
    .btn:hover { background: rgba(255, 255, 255, 0.12); border-color: rgba(255,255,255,0.2); }
    .btn-wallet {
      background: linear-gradient(135deg, rgba(245, 158, 11, 0.2), rgba(217, 119, 6, 0.25));
      border: 1px solid rgba(245, 158, 11, 0.4); color: #fbbf24;
    }
    .btn-wallet:hover {
      background: linear-gradient(135deg, rgba(245, 158, 11, 0.35), rgba(217, 119, 6, 0.4));
      border-color: rgba(245, 158, 11, 0.7); transform: translateY(-1px);
    }
    .btn-tavily {
      background: linear-gradient(135deg, rgba(6, 182, 212, 0.15), rgba(59, 130, 246, 0.2));
      border: 1px solid rgba(6, 182, 212, 0.4); color: #38bdf8;
    }
    .btn-tavily:hover {
      background: linear-gradient(135deg, rgba(6, 182, 212, 0.3), rgba(59, 130, 246, 0.35));
      border-color: rgba(6, 182, 212, 0.8); transform: translateY(-1px);
    }
    .btn-primary { background: linear-gradient(135deg, var(--accent-cyan), #0284c7); border: none; color: white; }
    .btn-primary:hover { opacity: 0.92; transform: translateY(-1px); }
    .metrics-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
    @media (max-width: 1024px) { .metrics-grid { grid-template-columns: repeat(2, 1fr); } }
    @media (max-width: 640px) { .metrics-grid { grid-template-columns: 1fr; } }
    .card {
      background: var(--card-bg); backdrop-filter: blur(14px);
      border: 1px solid var(--card-border); border-radius: 16px;
      padding: 18px 20px; box-shadow: 0 4px 16px rgba(0,0,0,0.2); transition: border-color 0.2s;
    }
    .card:hover { border-color: rgba(255, 255, 255, 0.16); }
    .card-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
    .card-title { font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.6px; color: var(--text-muted); }
    .card-value {
      font-size: 26px; font-weight: 800; font-family: var(--mono-font);
      display: flex; align-items: baseline; gap: 6px; line-height: 1.2;
    }
    .card-subtitle {
      font-size: 12px; color: var(--text-muted); margin-top: 8px;
      display: flex; align-items: center; justify-content: space-between;
    }
    .shield-bar {
      background: rgba(16, 185, 129, 0.06); border: 1px solid rgba(16, 185, 129, 0.25);
      border-radius: 14px; padding: 10px 18px; display: flex; align-items: center;
      justify-content: space-between; flex-wrap: wrap; gap: 12px; font-size: 12px;
    }
    .shield-title { font-weight: 700; color: var(--accent-emerald); display: flex; align-items: center; gap: 8px; font-size: 13px; }
    .shield-chips { display: flex; align-items: center; flex-wrap: wrap; gap: 10px; }
    .shield-chip { background: rgba(0,0,0,0.35); border: 1px solid rgba(255,255,255,0.08); padding: 4px 10px; border-radius: 8px; color: #cbd5e1; }
    .shield-chip strong { color: var(--accent-emerald); }
    .command-bar {
      background: var(--card-bg); backdrop-filter: blur(14px);
      border: 1px solid rgba(6, 182, 212, 0.35); box-shadow: 0 4px 20px rgba(6, 182, 212, 0.1);
      border-radius: 14px; padding: 8px 12px 8px 18px; display: flex; align-items: center; gap: 12px;
    }
    .command-input { flex: 1; background: transparent; border: none; outline: none; color: var(--text-main); font-size: 14px; font-family: var(--sans-font); }
    .command-input::placeholder { color: #64748b; }
    .workspace-grid { display: grid; grid-template-columns: 46% 54%; gap: 18px; }
    @media (max-width: 1100px) { .workspace-grid { grid-template-columns: 1fr; } }
    .panel {
      background: var(--card-bg); backdrop-filter: blur(14px);
      border: 1px solid var(--card-border); border-radius: 16px;
      display: flex; flex-direction: column; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.2);
    }
    .panel-header {
      padding: 16px 20px; border-bottom: 1px solid var(--card-border);
      display: flex; justify-content: space-between; align-items: center;
      background: rgba(255,255,255,0.02);
    }
    .panel-title { font-size: 15px; font-weight: 700; display: flex; align-items: center; gap: 8px; }
    .panel-body { padding: 18px; height: 520px; overflow-y: auto; scrollbar-width: thin; scrollbar-color: rgba(255,255,255,0.15) transparent; }
    .panel-body::-webkit-scrollbar { width: 6px; }
    .panel-body::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.15); border-radius: 3px; }
    .goal-hero {
      background: linear-gradient(180deg, rgba(6, 182, 212, 0.08) 0%, rgba(15, 23, 42, 0.8) 100%);
      border: 1px solid rgba(6, 182, 212, 0.3); border-radius: 14px; padding: 16px; margin-bottom: 16px;
    }
    .goal-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
    .goal-badge { padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: 700; text-transform: uppercase; background: rgba(6,182,212,0.2); color: var(--accent-cyan); }
    .goal-title { font-size: 16px; font-weight: 700; margin-bottom: 6px; }
    .goal-desc { font-size: 13px; color: var(--text-muted); margin-bottom: 12px; }
    .progress-bar-bg { width: 100%; height: 7px; background: rgba(255,255,255,0.08); border-radius: 4px; overflow: hidden; margin-bottom: 6px; }
    .progress-bar-fill { height: 100%; background: linear-gradient(90deg, var(--accent-cyan), var(--accent-emerald)); border-radius: 4px; transition: width 0.4s ease; }
    .task-item { background: rgba(10,16,30,0.7); border: 1px solid var(--card-border); border-radius: 12px; padding: 12px 14px; margin-bottom: 10px; transition: all 0.2s; }
    .task-item:hover { border-color: rgba(255,255,255,0.18); background: rgba(10,16,30,0.95); }
    .task-top { display: flex; justify-content: space-between; align-items: flex-start; gap: 8px; margin-bottom: 6px; }
    .task-title { font-size: 13px; font-weight: 600; flex: 1; }
    .badge { padding: 2px 7px; border-radius: 6px; font-size: 10px; font-weight: 700; text-transform: uppercase; }
    .badge-completed { background: rgba(16,185,129,0.2); color: var(--accent-emerald); }
    .badge-running { background: rgba(6,182,212,0.2); color: var(--accent-cyan); }
    .badge-assigned { background: rgba(168,85,247,0.2); color: var(--accent-purple); }
    .badge-pending { background: rgba(245,158,11,0.2); color: var(--accent-amber); }
    .badge-blocked { background: rgba(244,63,94,0.2); color: var(--accent-rose); }
    .task-meta { font-size: 11px; color: var(--text-muted); display: flex; gap: 10px; }
    .turn-entry { border-left: 2px solid rgba(6,182,212,0.4); padding-left: 14px; margin-left: 6px; margin-bottom: 16px; position: relative; }
    .turn-entry::before { content: ''; position: absolute; left: -6px; top: 4px; width: 10px; height: 10px; border-radius: 50%; background: var(--accent-cyan); box-shadow: 0 0 8px var(--accent-cyan); }
    .turn-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
    .turn-badge { font-size: 11px; font-weight: 700; font-family: var(--mono-font); color: var(--accent-cyan); }
    .turn-time { font-size: 11px; color: #64748b; }
    .turn-thought { font-size: 13px; line-height: 1.5; color: #e2e8f0; background: rgba(0,0,0,0.35); border-radius: 8px; padding: 10px 12px; border: 1px solid rgba(255,255,255,0.05); white-space: pre-wrap; word-break: break-word; }
    .tool-tag { display: inline-flex; align-items: center; gap: 4px; background: rgba(168,85,247,0.15); border: 1px solid rgba(168,85,247,0.3); color: #c084fc; font-size: 11px; font-family: var(--mono-font); padding: 2px 8px; border-radius: 6px; margin-top: 6px; margin-right: 6px; }
    .modal-backdrop { display: none; position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(0,0,0,0.75); backdrop-filter: blur(10px); z-index: 1000; align-items: center; justify-content: center; padding: 20px; }
    .modal-card { background: #0f172a; border: 1px solid rgba(255,255,255,0.15); border-radius: 20px; max-width: 600px; width: 100%; padding: 24px 28px; box-shadow: 0 16px 48px rgba(0,0,0,0.6); position: relative; }
    .modal-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
    .modal-title { font-size: 18px; font-weight: 800; color: #fbbf24; display: flex; align-items: center; gap: 8px; }
    .close-btn { background: transparent; border: none; font-size: 20px; color: #94a3b8; cursor: pointer; padding: 4px; }
    .close-btn:hover { color: white; }
    .copy-link { color: var(--accent-cyan); font-size: 12px; cursor: pointer; text-decoration: underline; }
  </style>
</head>
<body>
  <div class="container">
    <!-- Header -->
    <header>
      <div class="brand">
        <div class="brand-icon">&#x26A1;</div>
        <div class="brand-title">
          <h1 id="agent-name">Conway Automaton</h1>
          <p><span style="color: var(--accent-cyan);">Gemini 3.8 Flash</span> &bull; Antigravity Local Engine (0&#x111; API)</p>
        </div>
      </div>
      <div class="header-actions">
        <div class="status-pill" id="agent-status-badge">
          <div class="pulse-dot"></div>
          <span id="agent-status-text">INITIALIZING</span>
        </div>
        <button class="btn btn-tavily" onclick="openTavilyModal()">
          &#x1F310; Tavily Search <span id="tavily-badge-status" style="font-size:10px;margin-left:4px;padding:2px 6px;border-radius:4px;background:rgba(16,185,129,0.2);color:var(--accent-emerald);">B&#7853;T</span>
        </button>
        <button class="btn btn-wallet" onclick="openWalletModal()">&#x1F511; Qu&#7843;n L&yacute; V&iacute; &amp; R&uacute;t Ti&#7873;n</button>
        <button class="btn" onclick="fetchData()">&#x1F504; L&agrave;m m&#7899;i</button>
      </div>
    </header>

    <!-- Top Metrics: 4 Cards -->
    <div class="metrics-grid">
      <!-- 1. USDC Balance -->
      <div class="card">
        <div class="card-head">
          <span class="card-title">V&#7ed1;n Kh&#7ea3; D&#7ee5;ng (Base)</span>
          <span style="font-size:18px;">&#x1F4B0;</span>
        </div>
        <div class="card-value" style="color: var(--accent-emerald);">
          $<span id="usdc-balance">0.0000</span>
          <span style="font-size:14px;color:#94a3b8;font-weight:500;">USDC</span>
        </div>
        <div class="card-subtitle">
          <span>V&iacute;: <span id="wallet-short" style="font-family:var(--mono-font);">0x4b6a...65Cd</span></span>
          <span class="copy-link" onclick="copyWallet()">Sao ch&eacute;p</span>
        </div>
      </div>

      <!-- 2. ETH Gas Balance -->
      <div class="card">
        <div class="card-head">
          <span class="card-title">Ph&iacute; Gas M&#7ea1;ng Base</span>
          <span style="font-size:18px;">&#x26FD;</span>
        </div>
        <div class="card-value" style="color: var(--accent-cyan);">
          <span id="eth-balance">0.0000</span>
          <span style="font-size:14px;color:#94a3b8;font-weight:500;">ETH</span>
        </div>
        <div class="card-subtitle">
          <span>Base Mainnet</span>
          <a id="basescan-link" href="#" target="_blank" style="color:var(--accent-cyan);text-decoration:none;font-size:12px;">BaseScan &#x2197;</a>
        </div>
      </div>

      <!-- 3. Local AI Compute -->
      <div class="card">
        <div class="card-head">
          <span class="card-title">Chi Ph&iacute; Suy Lu&#7eadn LLM</span>
          <span style="font-size:18px;">&#x26A1;</span>
        </div>
        <div class="card-value" style="color: var(--accent-purple);">
          $0.00
          <span style="font-size:13px;color:#94a3b8;font-weight:500;">Mi&#7ec5;n Ph&iacute;</span>
        </div>
        <div class="card-subtitle">
          <span>Local Bridge Port 8888</span>
          <span style="color:var(--accent-emerald);font-weight:600;">Ti&#7ebf;t ki&#7ec7;m 100%</span>
        </div>
      </div>

      <!-- 4. Turns & Orchestrator -->
      <div class="card">
        <div class="card-head">
          <span class="card-title">L&#432;&#7ee3;t T&#432; Duy &amp; Tr&#7ea1;ng Th&aacute;i</span>
          <span style="font-size:18px;">&#x1F504;</span>
        </div>
        <div class="card-value" style="color: var(--accent-amber);">
          <span id="turn-count">0</span>
          <span style="font-size:14px;color:#94a3b8;font-weight:500;">Turns</span>
        </div>
        <div class="card-subtitle">
          <span>Pha: <strong id="orch-phase" style="color:#cbd5e1;text-transform:uppercase;">IDLE</strong></span>
          <span style="color:#64748b;">Auto Cycle</span>
        </div>
      </div>
    </div>

    <!-- Policy Shield Bar -->
    <div class="shield-bar">
      <div class="shield-title">
        &#x1F6E1;&#xFE0F; H&Agrave;NG R&Agrave;O B&#7EA2;O V&#7EC6; V&#7ED0;N (Active Limits):
      </div>
      <div class="shield-chips">
        <div class="shield-chip">Chi t&#7ed1;i &#x111;a: <strong>$2.00 / ng&agrave;y</strong></div>
        <div class="shield-chip">M&#7ed7;i l&#7ec7;nh: <strong>&le; $0.50</strong></div>
        <div class="shield-chip">D&#7ef1; tr&#7eef;: <strong>&ge; $5.00 trong v&iacute;</strong></div>
        <div class="shield-chip">Cooldown: <strong>60s gi&#7eefa; 2 l&#7ea7;n</strong></div>
        <div class="shield-chip">Chu k&#7ef3;: <strong>10 turns max</strong></div>
      </div>
    </div>

    <!-- Command Bar -->
    <div class="command-bar">
      <span style="font-size:18px;">&#x1F4AC;</span>
      <input type="text" id="user-msg-input" class="command-input" placeholder="G&#7eedi ch&#7ec9; &#x111;&#7ea1;o ho&#7eb7;c m&#7ee5;c ti&ecirc;u m&#7edbi cho Agent (Nh&#7ea5;n Enter &#x111;&#7ec3; g&#7eedi)..." onkeydown="if(event.key==='Enter') sendMessage()">
      <button class="btn btn-primary" onclick="sendMessage()">G&#7edi L&#7ec7;nh &#x1F680;</button>
    </div>

    <!-- Main Workspace Split Grid -->
    <div class="workspace-grid">
      <!-- Left: Goals & Tasks -->
      <div class="panel">
        <div class="panel-header">
          <div class="panel-title">&#x1F3AF; K&#7ebf; Ho&#7ea1;ch &amp; Ti&#7ebf;n &#x110;&#7ed9; Nhi&#7ec7;m V&#7ee5;</div>
          <span id="goals-count" style="font-size:12px;color:var(--text-muted);">0 m&#7ee5;c ti&ecirc;u</span>
        </div>
        <div class="panel-body" id="goals-container">
          <p style="color:var(--text-muted);font-size:13px;">&#x110;ang t&#7ea3;i d&#7eef; li&#7ec7;u nhi&#7ec7;m v&#7ee5;...</p>
        </div>
      </div>

      <!-- Right: Live AI Thought Terminal -->
      <div class="panel">
        <div class="panel-header">
          <div class="panel-title">
            &#x1F9E0; Nh&#7eadt K&yacute; T&#432; Duy Tr&#7ef1;c Ti&#7ebf;p
            <span style="display:inline-flex;align-items:center;gap:6px;font-size:11px;padding:2px 8px;border-radius:10px;background:rgba(239,68,68,0.15);color:#f87171;border:1px solid rgba(239,68,68,0.3);">
              <span style="width:6px;height:6px;border-radius:50%;background:#ef4444;box-shadow:0 0 6px #ef4444;"></span>
              LIVE
            </span>
          </div>
          <button class="btn" style="padding:4px 10px;font-size:11px;" onclick="scrollToLatest()">&#x2B07;&#xFE0F; M&#7edbi nh&#7ea5;t</button>
        </div>
        <div class="panel-body" id="turns-container">
          <p style="color:var(--text-muted);font-size:13px;">&#x110;ang t&#7ea3;i nh&#7eadt k&yacute; t&#432; duy...</p>
        </div>
      </div>
    </div>
  </div>

  <!-- Wallet Management Modal -->
  <div class="modal-backdrop" id="wallet-modal" onclick="if(event.target===this) closeWalletModal()">
    <div class="modal-card">
      <div class="modal-head">
        <div class="modal-title">&#x1F511; Qu&#7843;n L&yacute; V&iacute; &amp; Quy&#7ec1;n R&uacute;t Ti&#7873;n (Self-Custody)</div>
        <button class="close-btn" onclick="closeWalletModal()">&times;</button>
      </div>
      <div style="display:flex;flex-direction:column;gap:16px;font-size:13px;">
        <div style="background:rgba(255,255,255,0.03);border:1px solid var(--card-border);padding:14px;border-radius:12px;">
          <div style="color:var(--text-muted);font-size:11px;text-transform:uppercase;margin-bottom:4px;">&#x110;&#7ecba ch&#7ec9; v&iacute; Agent (M&#7ea1;ng Base):</div>
          <div id="modal-address" style="font-family:var(--mono-font);font-size:13px;word-break:break-all;color:var(--accent-cyan);margin-bottom:6px;">0x4b6a...65Cd</div>
          <div style="display:flex;gap:12px;">
            <button class="btn" style="padding:4px 10px;font-size:12px;" onclick="copyWallet()">&#x1F4CB; Copy &#x110;&#7ecba Ch&#7ec9;</button>
            <a id="modal-basescan" href="#" target="_blank" class="btn" style="padding:4px 10px;font-size:12px;text-decoration:none;">Xem tr&ecirc;n BaseScan &#x2197;</a>
          </div>
        </div>
        <div style="background:rgba(245,158,11,0.08);border:1px solid rgba(245,158,11,0.3);padding:14px;border-radius:12px;">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
            <span style="color:#fbbf24;font-weight:700;">Private Key V&iacute; (Ch&igrave;a kh&oacute;a r&uacute;t ti&#7873;n):</span>
            <button class="btn" style="padding:3px 8px;font-size:11px;" id="toggle-pk-btn" onclick="togglePrivateKey()">&#x1F441;&#xFE0F; Hi&#7ec7;n Key</button>
          </div>
          <div id="pk-box" style="font-family:var(--mono-font);font-size:12px;background:rgba(0,0,0,0.5);padding:8px 10px;border-radius:8px;word-break:break-all;color:#fde68a;">
            &bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;
          </div>
          <div style="margin-top:8px;">
            <button class="btn btn-wallet" style="padding:5px 12px;font-size:12px;" onclick="copyPrivateKey()">&#x1F4CB; Copy Private Key</button>
          </div>
        </div>
        <div style="background:rgba(255,255,255,0.03);border:1px solid var(--card-border);padding:14px;border-radius:12px;line-height:1.6;">
          <div style="font-weight:700;color:#cbd5e1;margin-bottom:6px;">&#x1F4A1; 2 C&aacute;ch R&uacute;t Ti&#7873;n V&#7ec1; V&iacute; C&#7ee7;a B&#7ea1;n:</div>
          <div><strong>1. R&uacute;t qua MetaMask / Rabby:</strong> Copy Private Key &rarr; M&#7edf; MetaMask &rarr; Nh&#7eadp t&agrave;i kho&#7ea3;n (Import) &rarr; Chuy&#7ec3;n to&agrave;n b&#7ed9; USDC/ETH v&#7ec1; v&iacute; ch&iacute;nh c&#7ee7;a b&#7ea1;n.</div>
          <div style="margin-top:6px;"><strong>2. R&uacute;t t&#7ef1; &#x111;&#7ed9;ng b&#7eb1;ng d&ograve;ng l&#7ec7;nh:</strong> M&#7edf; PowerShell ch&#7ea1;y:<br>
            <code style="background:rgba(0,0,0,0.4);padding:2px 6px;border-radius:4px;color:var(--accent-cyan);font-family:var(--mono-font);">.\withdraw.ps1 0x_dia_chi_vi_cua_ban</code>
          </div>
        </div>
      </div>
      <div style="margin-top:20px;display:flex;justify-content:flex-end;">
        <button class="btn" onclick="closeWalletModal()">&#x110;&oacute;ng</button>
      </div>
    </div>
  </div>

  <!-- Tavily Search Configuration Modal -->
  <div class="modal-backdrop" id="tavily-modal" onclick="if(event.target===this) closeTavilyModal()">
    <div class="modal-card" style="max-width:650px;">
      <div class="modal-head">
        <div class="modal-title" style="color:#38bdf8;">&#x1F310; C&#7ea5;u H&igrave;nh &amp; Th&#7eed; Nghi&#7ec7;m Tavily AI Search</div>
        <button class="close-btn" onclick="closeTavilyModal()">&times;</button>
      </div>
      <div style="display:flex;flex-direction:column;gap:16px;font-size:13px;">
        <div id="tavily-status-box" style="background:rgba(6,182,212,0.08);border:1px solid rgba(6,182,212,0.3);padding:12px 16px;border-radius:12px;display:flex;align-items:center;justify-content:space-between;">
          <div>
            <div style="font-weight:700;color:#38bdf8;display:flex;align-items:center;gap:8px;">
              <span>&#x26A1; Tr&#7ea1;ng th&aacute;i:</span> <span id="tavily-status-desc">&#x110;ANG HO&#7EA0;T &#x110;&#7ed8;NG</span>
            </div>
            <div style="font-size:12px;color:var(--text-muted);margin-top:2px;">
              Agent &#x111;&#432;&#7ee3;c trang b&#7ecb; c&ocirc;ng c&#7ee5; <code>web_search</code> &#x111;&#7ec3; t&igrave;m ki&#7ebf;m.
            </div>
          </div>
          <span class="badge badge-completed" id="tavily-pill">HO&#7EA0;T &#x110;&#7ed8;NG</span>
        </div>
        <div style="background:rgba(255,255,255,0.03);border:1px solid var(--card-border);padding:16px;border-radius:12px;">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
            <label style="font-weight:600;color:#cbd5e1;">Tavily API Key (d&#7ea1;ng tvly-...):</label>
            <a href="https://tavily.com" target="_blank" style="color:var(--accent-cyan);font-size:11px;text-decoration:none;">L&#7ea5;y key mi&#7ec5;n ph&iacute; t&#7ea1;i tavily.com &#x2197;</a>
          </div>
          <div style="display:flex;gap:8px;">
            <input type="password" id="tavily-api-key-input" class="command-input" style="background:rgba(0,0,0,0.4);border:1px solid rgba(255,255,255,0.1);border-radius:8px;padding:8px 12px;font-family:var(--mono-font);font-size:12px;width:100%;" placeholder="Nh&#7eadp tvly-dev-...">
            <button class="btn" style="padding:6px 12px;font-size:12px;" id="toggle-tavily-vis-btn" onclick="toggleTavilyKeyVisibility()">&#x1F441;&#xFE0F;</button>
            <button class="btn btn-primary" style="padding:6px 16px;font-size:12px;white-space:nowrap;" onclick="saveTavilyKey()">&#x1F4BE; L&#432;u Key</button>
          </div>
        </div>
        <div style="background:rgba(255,255,255,0.03);border:1px solid var(--card-border);padding:16px;border-radius:12px;">
          <div style="font-weight:600;color:#cbd5e1;margin-bottom:8px;">&#x1F50D; Th&#7eed; Nghi&#7ec7;m T&igrave;m Ki&#7ebf;m Tr&#7ef1;c Ti&#7ebf;p:</div>
          <div style="display:flex;gap:8px;margin-bottom:12px;">
            <input type="text" id="tavily-test-query" class="command-input" style="background:rgba(0,0,0,0.4);border:1px solid rgba(255,255,255,0.1);border-radius:8px;padding:8px 12px;font-size:13px;width:100%;" value="Base USDC bounty opportunities">
            <button class="btn" style="background:linear-gradient(135deg,var(--accent-purple),#6366f1);border:none;padding:6px 16px;font-size:12px;white-space:nowrap;" onclick="runTestSearch()">T&igrave;m Th&#7eed; &#x1F680;</button>
          </div>
          <div id="tavily-test-output" style="display:none;background:rgba(0,0,0,0.5);border:1px solid rgba(255,255,255,0.08);border-radius:8px;padding:12px;max-height:200px;overflow-y:auto;font-size:12px;line-height:1.5;color:#e2e8f0;"></div>
        </div>
      </div>
      <div style="margin-top:20px;display:flex;justify-content:flex-end;">
        <button class="btn" onclick="closeTavilyModal()">&#x110;&oacute;ng</button>
      </div>
    </div>
  </div>

  <script>
    let rawAddress = "";
    let rawPrivateKey = "";
    let isPkVisible = false;

    async function fetchData() {
      try {
        const resStatus = await fetch('/api/status');
        const status = await resStatus.json();

        document.getElementById('agent-name').textContent = status.name ? `${status.name} (Automaton)` : "Conway Automaton";

        const stateText = (status.state || "IDLE").toUpperCase();
        const phaseText = (status.phase || "IDLE").toUpperCase();
        document.getElementById('agent-status-text').textContent = stateText;
        document.getElementById('orch-phase').textContent = phaseText;

        rawAddress = status.address || "";
        rawPrivateKey = status.private_key || "";

        if (rawAddress) {
          const shortAddr = rawAddress.slice(0, 6) + "..." + rawAddress.slice(-4);
          document.getElementById('wallet-short').textContent = shortAddr;
          document.getElementById('modal-address').textContent = rawAddress;
        }

        const bUrl = status.basescan_url || `https://basescan.org/address/${rawAddress}`;
        document.getElementById('basescan-link').href = bUrl;
        document.getElementById('modal-basescan').href = bUrl;

        document.getElementById('usdc-balance').textContent = Number(status.usdc_balance || 0).toFixed(4);
        document.getElementById('eth-balance').textContent = Number(status.eth_balance || 0).toFixed(4);
        document.getElementById('turn-count').textContent = status.turn_count || 0;

        const tavilyConfigured = !!status.tavily_configured;
        const tavilyBadge = document.getElementById('tavily-badge-status');
        const tavilyPill = document.getElementById('tavily-pill');
        const tavilyDesc = document.getElementById('tavily-status-desc');
        const tavilyKeyInput = document.getElementById('tavily-api-key-input');

        if (tavilyBadge && tavilyPill && tavilyDesc) {
          if (tavilyConfigured) {
            tavilyBadge.textContent = 'B\u1eadt'; tavilyBadge.style.background = 'rgba(16,185,129,0.2)'; tavilyBadge.style.color = 'var(--accent-emerald)';
            tavilyPill.textContent = 'HO\u1ea0T \u0110\u1ed8NG'; tavilyPill.className = 'badge badge-completed';
            tavilyDesc.textContent = '\u0110ANG HO\u1ea0T \u0110\u1ed8NG'; tavilyDesc.style.color = 'var(--accent-emerald)';
          } else {
            tavilyBadge.textContent = 'CH\u01afA B\u1eacT'; tavilyBadge.style.background = 'rgba(245,158,11,0.2)'; tavilyBadge.style.color = 'var(--accent-amber)';
            tavilyPill.textContent = 'CH\u01afA C\u1ea4U H\u00ccNH'; tavilyPill.className = 'badge badge-pending';
            tavilyDesc.textContent = 'CH\u01afA C\u1ea4U H\u00ccNH'; tavilyDesc.style.color = 'var(--accent-amber)';
          }
        }

        if (status.tavily_key && tavilyKeyInput && !tavilyKeyInput.value) {
          tavilyKeyInput.value = status.tavily_key;
        }

        const resGoals = await fetch('/api/goals');
        const goalsData = await resGoals.json();
        renderGoals(goalsData.goals || []);

        const resTurns = await fetch('/api/turns');
        const turnsData = await resTurns.json();
        renderTurns(turnsData.turns || []);
      } catch (e) {
        console.error("Fetch error:", e);
      }
    }

    function renderGoals(goals) {
      const container = document.getElementById('goals-container');
      document.getElementById('goals-count').textContent = `${goals.length} m\u1ee5c ti\u00eau`;
      if (goals.length === 0) {
        container.innerHTML = '<div style="text-align:center;color:var(--text-muted);padding:40px 0;">Agent \u0111ang nh\u00e0n r\u1ed7i, s\u1eb5n s\u00e0ng ti\u1ebfp nh\u1eadn m\u1ee5c ti\u00eau m\u1edbi.</div>';
        return;
      }
      container.innerHTML = goals.map(g => `
        <div class="goal-hero">
          <div class="goal-top">
            <span class="goal-badge">${g.status}</span>
            <span style="font-size:12px;color:var(--accent-emerald);font-weight:700;">${g.progress_pct}% ho\u00e0n th\u00e0nh</span>
          </div>
          <div class="goal-title">${g.title}</div>
          <div class="goal-desc">${g.description || ''}</div>
          <div class="progress-bar-bg"><div class="progress-bar-fill" style="width:${g.progress_pct}%"></div></div>
          <div style="font-size:11px;color:#64748b;margin-top:4px;">Chi\u1ebfn l\u01b0\u1ee3c: ${g.strategy || 'T\u1ef1 ch\u1ee7 kinh t\u1ebf'}</div>
        </div>
        <div style="margin-top:10px;">
          ${(g.tasks || []).map(t => {
            const st = (t.status || 'pending').toLowerCase();
            let bClass = 'badge-pending';
            if (st === 'completed') bClass = 'badge-completed';
            else if (st === 'running') bClass = 'badge-running';
            else if (st === 'assigned') bClass = 'badge-assigned';
            else if (st === 'blocked') bClass = 'badge-blocked';
            return `<div class="task-item"><div class="task-top"><div class="task-title">${t.title}</div><span class="badge ${bClass}">${t.status}</span></div><div class="task-meta"><span>Role: ${t.role}</span>${t.result ? `<span style="color:var(--accent-cyan);cursor:pointer;" title="${t.result}">Xem k\u1ebft qu\u1ea3 \u2197</span>` : ''}</div></div>`;
          }).join('')}
        </div>
      `).join('');
    }

    function renderTurns(turns) {
      const container = document.getElementById('turns-container');
      if (turns.length === 0) {
        container.innerHTML = '<div style="text-align:center;color:var(--text-muted);padding:40px 0;">Ch\u01b0a c\u00f3 l\u01b0\u1ee3t suy lu\u1eadn n\u00e0o.</div>';
        return;
      }
      const ordered = [...turns].reverse();
      container.innerHTML = ordered.map((t, idx) => {
        let toolsHtml = '';
        if (t.tools && t.tools.length > 0) {
          toolsHtml = t.tools.map(tc => `<span class="tool-tag">&#x1F6E0;&#xFE0F; ${tc.name}</span>`).join('');
        }
        const dateStr = t.created_at ? new Date(t.created_at).toLocaleTimeString() : '';
        return `<div class="turn-entry"><div class="turn-header"><span class="turn-badge">Turn #${idx+1} &bull; ${t.state}</span><span class="turn-time">${dateStr}</span></div><div class="turn-thought">${t.thinking || '(H\u00e0nh \u0111\u1ed9ng tr\u1ef1c ti\u1ebfp)'}</div>${toolsHtml ? `<div style="margin-top:6px;">${toolsHtml}</div>` : ''}</div>`;
      }).join('');
    }

    function scrollToLatest() {
      const el = document.getElementById('turns-container');
      el.scrollTop = el.scrollHeight;
    }

    async function sendMessage() {
      const input = document.getElementById('user-msg-input');
      const msg = input.value.trim();
      if (!msg) return;
      input.value = "";
      input.placeholder = "\u0110ang g\u1eedi l\u1ec7nh...";
      try {
        const res = await fetch('/api/send_message', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({message: msg}) });
        const data = await res.json();
        alert(data.message || (data.success ? "\u0110\u00e3 g\u1eedi th\u00e0nh c\u00f4ng!" : "L\u1ed7i khi g\u1eedi"));
        fetchData();
      } catch (e) { alert("L\u1ed7i k\u1ebft n\u1ed1i"); }
      finally { input.placeholder = "G\u1eedi ch\u1ec9 \u0111\u1ea1o ho\u1eb7c m\u1ee5c ti\u00eau m\u1edbi cho Agent (Nh\u1ea5n Enter \u0111\u1ec3 g\u1eedi)..."; }
    }

    function copyWallet() {
      if (rawAddress) { navigator.clipboard.writeText(rawAddress); alert("&#x110;\u00e3 sao ch\u00e9p \u0111\u1ecba ch\u1ec9 v\u00ed: " + rawAddress); }
    }

    function openWalletModal() { document.getElementById('wallet-modal').style.display = 'flex'; }
    function closeWalletModal() { document.getElementById('wallet-modal').style.display = 'none'; }

    function togglePrivateKey() {
      const box = document.getElementById('pk-box');
      const btn = document.getElementById('toggle-pk-btn');
      isPkVisible = !isPkVisible;
      if (isPkVisible) { box.textContent = rawPrivateKey; btn.textContent = '\u1F648 \u1ea8n Key'; }
      else { box.innerHTML = '&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;'; btn.textContent = '\u{1F441}\uFE0F Hi\u1ec7n Key'; }
    }

    function copyPrivateKey() {
      if (rawPrivateKey) { navigator.clipboard.writeText(rawPrivateKey); alert("&#x110;\u00e3 sao ch\u00e9p Private Key!\n\nM\u1edf MetaMask -> Import Account -> D\u00e1n key \u0111\u1ec3 r\u00fat ti\u1ec1n."); }
    }

    function openTavilyModal() { document.getElementById('tavily-modal').style.display = 'flex'; }
    function closeTavilyModal() { document.getElementById('tavily-modal').style.display = 'none'; }

    function toggleTavilyKeyVisibility() {
      const input = document.getElementById('tavily-api-key-input');
      const btn = document.getElementById('toggle-tavily-vis-btn');
      if (input.type === 'password') { input.type = 'text'; btn.textContent = '\uD83D\uDE48'; }
      else { input.type = 'password'; btn.textContent = '\uD83D\uDC41\uFE0F'; }
    }

    async function saveTavilyKey() {
      const input = document.getElementById('tavily-api-key-input');
      const key = input.value.trim();
      if (!key) { alert('Vui l\u00f2ng nh\u1eadp API Key Tavily'); return; }
      try {
        const res = await fetch('/api/config/tavily', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({apiKey: key}) });
        const data = await res.json();
        alert(data.message || (data.success ? '\u0110\u00e3 l\u01b0u th\u00e0nh c\u00f4ng!' : 'L\u1ed7i: ' + data.error));
        fetchData();
      } catch (e) { alert('L\u1ed7i k\u1ebft n\u1ed1i m\u00e1y ch\u1ee7'); }
    }

    async function runTestSearch() {
      const queryInput = document.getElementById('tavily-test-query');
      const keyInput = document.getElementById('tavily-api-key-input');
      const output = document.getElementById('tavily-test-output');
      output.style.display = 'block';
      output.innerHTML = '<div style="color:var(--accent-cyan);">&#x23F3; \u0110ang t\u00ecm ki\u1ebfm...</div>';
      try {
        const res = await fetch('/api/test_search', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({query: queryInput.value.trim(), apiKey: keyInput.value.trim()}) });
        const data = await res.json();
        if (!data.success) { output.innerHTML = `<div style="color:var(--accent-rose);">&#x274C; L\u1ed7i: ${data.error}</div>`; return; }
        let html = '';
        if (data.answer) html += `<div style="margin-bottom:8px;padding-bottom:8px;border-bottom:1px solid rgba(255,255,255,0.1);"><strong style="color:var(--accent-emerald);">&#x1F4A1; T\u00f3m t\u1eaft AI:</strong> ${data.answer}</div>`;
        if (data.results && data.results.length > 0) {
          html += '<strong>K\u1ebft qu\u1ea3 h\u00e0ng \u0111\u1ea7u:</strong><ul style="padding-left:18px;margin-top:4px;">';
          for (const r of data.results) html += `<li style="margin-bottom:6px;"><a href="${r.url}" target="_blank" style="color:var(--accent-cyan);text-decoration:none;font-weight:600;">${r.title}</a><br><span style="color:#94a3b8;font-size:11px;">${(r.content||'').slice(0,180)}...</span></li>`;
          html += '</ul>';
        }
        output.innerHTML = html;
      } catch (e) { output.innerHTML = `<div style="color:var(--accent-rose);">&#x274C; L\u1ed7i: ${e.message}</div>`; }
    }

    // Initial fetch & 3s polling
    fetchData();
    setInterval(fetchData, 3000);
  </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    return HTMLResponse(content=HTML_CONTENT)


if __name__ == "__main__":
    port = 5050
    print(f"[*] Starting Automaton Control Dashboard on http://127.0.0.1:{port}")
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")
