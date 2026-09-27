#!/usr/bin/env python3
"""
Local Antigravity Bridge for Automaton
Provides an OpenAI-compatible /v1/chat/completions endpoint on http://127.0.0.1:8888
Powered by Antigravity's local engine (agy.exe)
"""

import os
import sys

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import json
import time
import subprocess
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI(title="Antigravity Local Bridge")

AGY_EXE = r"C:\Users\phu09\AppData\Local\agy\bin\agy.exe"
DEFAULT_MODEL = "gemini-3.8-flash-high"


def run_agy(prompt: str, model: str = DEFAULT_MODEL) -> str:
    """Invoke agy.exe via stream-json to support arbitrary prompt lengths without Windows WinError 206."""
    cmd = [
        AGY_EXE,
        "--input-format", "stream-json",
        "--output-format", "stream-json",
        "--model", model,
        "--dangerously-skip-permissions"
    ]
    input_payload = json.dumps({"event": "user", "message": {"content": prompt}}) + "\n"
    try:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        stdout, stderr = proc.communicate(input=input_payload, timeout=180)

        # Look for result event in NDJSON output
        for line in reversed(stdout.strip().split("\n")):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                if data.get("event") == "result":
                    res = data.get("result", {})
                    response_text = res.get("response", "")
                    if response_text:
                        return response_text.strip()
            except Exception:
                continue

        # Fallback to text_delta in step_update
        deltas = []
        for line in stdout.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                if data.get("event") == "step_update":
                    update = data.get("step_update", {})
                    delta = update.get("text_delta")
                    if delta:
                        deltas.append(delta)
            except Exception:
                continue
        if deltas:
            return "".join(deltas).strip()

        return "I am awake, assessing my state and goals."
    except Exception as e:
        print(f"Execution error: {e}", file=sys.stderr)
        return f"Bridge error: {e}"


@app.get("/v1/models")
async def list_models():
    return {
        "object": "list",
        "data": [
            {"id": "gpt-4.1", "object": "model", "owned_by": "antigravity"},
            {"id": "gpt-4o", "object": "model", "owned_by": "antigravity"},
            {"id": "gemini-3.8-flash-high", "object": "model", "owned_by": "antigravity"},
            {"id": "claude-sonnet-4-6", "object": "model", "owned_by": "antigravity"}
        ]
    }


@app.post("/v1/chat/completions")
@app.post("/chat/completions")
async def chat_completions(request: Request):
    data = await request.json()
    messages = data.get("messages", [])
    tools = data.get("tools", [])
    model_req = data.get("model", "gpt-4o")

    # Determine backend Antigravity model
    target_model = DEFAULT_MODEL
    if "claude" in model_req.lower():
        target_model = "claude-sonnet-4-6"
    elif "pro" in model_req.lower():
        target_model = "gemini-3.1-pro-high"

    # Build prompt
    prompt_parts = [
        "[CRITICAL SYSTEM DIRECTIVE]\n"
        "You are acting strictly as an LLM reasoning backend for an autonomous AI agent (Automaton).\n"
        "DO NOT invoke any Antigravity tools (such as run_command, view_file, write_to_file, etc.) yourself.\n"
        "To invoke an Automaton tool, you must reply with the JSON tool_calls block specified below.\n"
        "If no tool is needed, reply with normal text thought/reasoning.\n\n"
    ]
    
    # Tool instructions if tools are provided
    if tools:
        tool_desc = json.dumps(tools, indent=2, ensure_ascii=False)
        prompt_parts.append(
            f"You have access to the following tools:\n{tool_desc}\n\n"
            "If you decide to invoke a tool, you MUST respond in valid JSON with this format:\n"
            "```json\n"
            "{\n"
            '  "tool_calls": [\n'
            '    {\n'
            '      "name": "tool_name",\n'
            '      "arguments": { "arg1": "value1" }\n'
            '    }\n'
            '  ],\n'
            '  "thought": "Your reasoning here"\n'
            "}\n"
            "```\n"
            "If no tool is needed, respond with standard text.\n"
        )

    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "system":
            prompt_parts.append(f"[SYSTEM INSTRUCTION]\n{content}\n")
        elif role == "assistant":
            prompt_parts.append(f"[ASSISTANT]\n{content}\n")
        elif role == "tool":
            prompt_parts.append(f"[TOOL RESULT]\n{content}\n")
        else:
            prompt_parts.append(f"[USER]\n{content}\n")

    full_prompt = "\n".join(prompt_parts)

    # Call agy.exe
    start_time = time.time()
    raw_response = run_agy(full_prompt, target_model)
    elapsed = time.time() - start_time

    # Parse response for tool calls
    tool_calls = []
    message_content = raw_response

    # Check if response has JSON tool_calls
    cleaned = raw_response.strip()
    json_candidate = None
    if "```json" in cleaned:
        json_candidate = cleaned.split("```json")[1].split("```")[0].strip()
    elif "```" in cleaned and "{" in cleaned:
        parts = cleaned.split("```")
        for p in parts:
            if "{" in p and "}" in p:
                json_candidate = p.strip()
                break
    elif cleaned.startswith("{") and cleaned.endswith("}"):
        json_candidate = cleaned
    elif '{"tool_calls"' in cleaned or '{\n  "tool_calls"' in cleaned:
        start_idx = cleaned.find("{")
        end_idx = cleaned.rfind("}")
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            json_candidate = cleaned[start_idx:end_idx + 1]

    if json_candidate:
        try:
            parsed = json.loads(json_candidate)
            if "tool_calls" in parsed:
                for idx, tc in enumerate(parsed["tool_calls"]):
                    tool_calls.append({
                        "id": f"call_{idx}_{int(time.time())}",
                        "type": "function",
                        "function": {
                            "name": tc.get("name"),
                            "arguments": json.dumps(tc.get("arguments", {}))
                        }
                    })
                message_content = parsed.get("thought", "") or raw_response
        except Exception:
            pass

    return {
        "id": f"chatcmpl-antigravity-{int(time.time())}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": target_model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": message_content,
                    **( {"tool_calls": tool_calls} if tool_calls else {} )
                },
                "finish_reason": "tool_calls" if tool_calls else "stop"
            }
        ],
        "usage": {
            "prompt_tokens": len(full_prompt) // 4,
            "completion_tokens": len(raw_response) // 4,
            "total_tokens": (len(full_prompt) + len(raw_response)) // 4
        }
    }


if __name__ == "__main__":
    port = 8888
    print(f"[*] Starting Antigravity Local Bridge on http://127.0.0.1:{port}")
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")
