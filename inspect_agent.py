#!/usr/bin/env python3
"""
Automaton Agent Inspector
Inspects wallet balance, active goals, decomposed tasks, and recent thought logs.
"""

import os
import sys
import json
import sqlite3
from datetime import datetime

# Windows encoding fix
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

USER_PROFILE = os.environ.get("USERPROFILE", os.path.expanduser("~"))
AUTOMATON_DIR = os.path.join(USER_PROFILE, ".automaton")
DB_PATH = os.path.join(AUTOMATON_DIR, "state.db")
CONFIG_PATH = os.path.join(AUTOMATON_DIR, "automaton.json")
WALLET_PATH = os.path.join(AUTOMATON_DIR, "wallet.json")


def load_json(path):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def format_time(ts_str):
    if not ts_str:
        return "N/A"
    try:
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return str(ts_str)


def inspect():
    print("=" * 65)
    print("        CONWAY AUTOMATON - GIÁM SÁT TÀI CHÍNH & KẾ HOẠCH       ")
    print("=" * 65)

    if not os.path.exists(DB_PATH):
        print(f"[-] Chua tim thay co so du lieu tai: {DB_PATH}")
        return

    config = load_json(CONFIG_PATH)
    wallet = load_json(WALLET_PATH)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 1. Identity & Wallet Info
    name = config.get("name", "hobie")
    address = wallet.get("address") or config.get("walletAddress", "Unknown")
    chain = config.get("chainType", "evm")
    model = config.get("inferenceModel", "gpt-4o")

    # State from DB
    state_row = cursor.execute("SELECT value FROM kv WHERE key = 'agent_state'").fetchone()
    agent_state = state_row["value"] if state_row else "idle"

    # Turn count
    turn_count_row = cursor.execute("SELECT count(*) as cnt FROM turns").fetchone()
    turn_count = turn_count_row["cnt"] if turn_count_row else 0

    # Start time
    start_time_row = cursor.execute("SELECT value FROM kv WHERE key = 'start_time'").fetchone()
    start_time = format_time(start_time_row["value"]) if start_time_row else "N/A"

    print("\n[1] THONG TIN DINH DANH & VI ON-CHAIN:")
    print(f"  - Ten Agent      : {name}")
    print(f"  - Trang thai     : {agent_state.upper()}")
    print(f"  - Blockchain     : {chain.upper()} (Base / Ethereum)")
    print(f"  - Dia chi vi     : {address}")
    if chain.lower() == "evm":
        print(f"  - BaseScan Link  : https://basescan.org/address/{address}")
    print(f"  - LLM Reasoning  : Antigravity Local Engine ({model})")
    print(f"  - Tong so Turn   : {turn_count} luot suy luan")
    print(f"  - Khoi dong luc  : {start_time}")

    # 2. Financial Balance
    balance_row = cursor.execute("SELECT value FROM kv WHERE key = 'last_known_balance'").fetchone()
    credits_cents = 100000
    usdc_bal = 0.0
    if balance_row and balance_row["value"]:
        try:
            bdata = json.loads(balance_row["value"])
            credits_cents = bdata.get("creditsCents", 100000)
            usdc_bal = bdata.get("usdcBalance", 0.0)
        except Exception:
            pass

    print("\n[2] SO DU & NANG LUONG SINH TON (SURVIVAL TIER):")
    print(f"  - So du USDC vi  : ${usdc_bal:.4f} USDC")
    print(f"  - Compute Credits: ${credits_cents / 100:.2f} (Conway / Local compute)")
    print(f"  - Chi phi LLM    : $0.00 (Chay mien phi tren Antigravity Local Engine)")

    # 3. Spend Limits & Safety Rules
    tp = config.get("treasuryPolicy", {})
    max_daily = tp.get("maxDailyTransferCents", 200) / 100.0
    max_hourly = tp.get("maxHourlyTransferCents", 100) / 100.0
    max_single = tp.get("maxSingleTransferCents", 50) / 100.0
    min_reserve = tp.get("minimumReserveCents", 500) / 100.0
    cooldown = tp.get("transferCooldownMs", 60000) / 1000.0
    max_cycle = config.get("maxTurnsPerCycle", 10)

    print("\n[3] GIOI HAN CHI TIEU & AN TOAN (SPEND LIMITS & ANTI-LOOP):")
    print(f"  🛡️ Han muc chi tieu/ngay : Toi da ${max_daily:.2f}/ngay (Spend Cap: $2.00)")
    print(f"  🛡️ Han muc chi tieu/gio  : Toi da ${max_hourly:.2f}/gio")
    print(f"  🛡️ Han muc 1 giao dich   : Toi da ${max_single:.2f}/lan")
    print(f"  🛡️ Quy du phong bat kha  : Luon giu lai it nhat ${min_reserve:.2f} trong vi")
    print(f"  🛡️ Gian cach chong loop  : {cooldown:.0f}s cooldown giua cac lan chi tieu")
    print(f"  🛡️ Tu dong ngat chu ky   : Toi da {max_cycle} turns/chu ky (ngung ngay neu loop)")

    # 4. Active Goals
    print("\n[4] MUC TIEU DANG THUC HIEN (ACTIVE GOALS):")
    try:
        goals = cursor.execute(
            "SELECT id, title, description, strategy, status, created_at FROM goals WHERE status != 'archived' ORDER BY created_at DESC"
        ).fetchall()
        if not goals:
            print("  (Chua co muc tieu nao duoc luu trong bang goals)")
        else:
            for g in goals:
                status_icon = "🟢" if g["status"] == "active" else "⚪"
                print(f"  {status_icon} Muc tieu: {g['title']} [{g['status'].upper()}]")
                print(f"    - ID       : {g['id']}")
                print(f"    - Mo ta    : {g['description']}")
                if g["strategy"]:
                    print(f"    - Chien luoc: {g['strategy']}")
                print(f"    - Khoi tao : {format_time(g['created_at'])}")
    except Exception as e:
        print(f"  Khong the truy van goals: {e}")

    # 4. Decomposed Tasks in Task Graph
    print("\n[4] CAC NHIEM VU CHI TIET TRONG KE HOACH (TASK GRAPH):")
    try:
        tasks = cursor.execute(
            "SELECT id, goal_id, title, agent_role, status, result, created_at FROM task_graph ORDER BY created_at ASC"
        ).fetchall()
        if not tasks:
            print("  (Orchestrator dang phan tich va lap task graph cho muc tieu tren)")
        else:
            for idx, t in enumerate(tasks, 1):
                t_status = t["status"].upper()
                s_icon = "✅" if t_status == "COMPLETED" else "⏳" if t_status == "RUNNING" else "⏹️"
                print(f"  {idx}. {s_icon} [{t_status}] {t['title']} (Role: {t['agent_role'] or 'Generalist'})")
                if t["result"]:
                    res_summary = t["result"][:120] + "..." if len(t["result"]) > 120 else t["result"]
                    print(f"     Ket qua: {res_summary}")
    except Exception as e:
        print(f"  (Bang task_graph chua khoi tao hoac khong co: {e})")

    # 5. Recent Thoughts & Actions (Turns)
    print("\n[5] 5 LUOT SUY LUAN & HANH DONG GAN NHAT CUA AI:")
    try:
        turns = cursor.execute(
            "SELECT id, state, input_source, thinking, tool_calls, created_at FROM turns ORDER BY rowid DESC LIMIT 5"
        ).fetchall()
        if not turns:
            print("  (Chua co du lieu luot suy luan)")
        else:
            for idx, t in enumerate(reversed(turns), 1):
                t_time = format_time(t["created_at"])
                print(f"\n  --- [Luot #{idx}] vao luc {t_time} (Nguon: {t['input_source'] or 'loop'}) ---")
                
                # Thinking
                thinking_text = t["thinking"] or ""
                if thinking_text:
                    clean_thought = thinking_text.strip().replace("\n", " ")
                    if len(clean_thought) > 180:
                        clean_thought = clean_thought[:180] + "..."
                    print(f"  🧠 Tu duy: {clean_thought}")

                # Tool calls
                tc_str = t["tool_calls"]
                tools_list = []
                if tc_str:
                    try:
                        parsed_tc = json.loads(tc_str)
                        for tc in parsed_tc:
                            fn_name = tc.get("name") or tc.get("function", {}).get("name")
                            fn_args = tc.get("arguments") or tc.get("function", {}).get("arguments") or {}
                            tools_list.append(f"{fn_name}({str(fn_args)[:60]})")
                    except Exception:
                        tools_list = [str(tc_str)[:60]]

                if tools_list:
                    print(f"  ⚡ Goi cong cu: {', '.join(tools_list)}")
    except Exception as e:
        print(f"  Khong the truy van turns: {e}")

    conn.close()
    print("\n" + "=" * 65)


if __name__ == "__main__":
    inspect()
