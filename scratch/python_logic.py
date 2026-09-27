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


