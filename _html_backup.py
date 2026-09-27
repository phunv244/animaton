HTML_CONTENT = """<!DOCTYPE html>
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

    /* Top Navigation Header */
    header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: var(--card-bg);
      backdrop-filter: blur(16px);
      border: 1px solid var(--card-border);
      border-radius: 16px;
      padding: 14px 22px;
      box-shadow: 0 4px 24px rgba(0,0,0,0.3);
    }

    .brand { display: flex; align-items: center; gap: 14px; }
    .brand-icon {
      width: 42px; height: 42px;
      background: linear-gradient(135deg, var(--accent-cyan), var(--accent-purple));
      border-radius: 12px;
      display: flex; align-items: center; justify-content: center;
      font-size: 22px;
      box-shadow: 0 0 20px rgba(6, 182, 212, 0.35);
    }
    .brand-title h1 { font-size: 19px; font-weight: 800; letter-spacing: -0.4px; }
    .brand-title p { font-size: 12px; color: var(--text-muted); display: flex; align-items: center; gap: 6px; }

    .header-actions { display: flex; align-items: center; gap: 12px; }
    
    .status-pill {
      display: flex; align-items: center; gap: 8px;
      padding: 6px 14px; border-radius: 30px;
      font-size: 12px; font-weight: 700;
      background: rgba(16, 185, 129, 0.12);
      color: var(--accent-emerald);
      border: 1px solid rgba(16, 185, 129, 0.3);
    }
    .pulse-dot {
      width: 8px; height: 8px; border-radius: 50%;
      background: currentColor;
      box-shadow: 0 0 10px currentColor;
      animation: pulse 2s infinite;
    }
    @keyframes pulse { 0% { opacity: 0.3; } 50% { opacity: 1; } 100% { opacity: 0.3; } }

    .btn {
      background: rgba(255, 255, 255, 0.06);
      border: 1px solid var(--card-border);
      color: var(--text-main);
      padding: 8px 16px; border-radius: 10px;
      font-size: 13px; font-weight: 600; cursor: pointer;
      display: inline-flex; align-items: center; gap: 8px;
      transition: all 0.2s;
    }
    .btn:hover { background: rgba(255, 255, 255, 0.12); border-color: rgba(255,255,255,0.2); }
    .btn-wallet {
      background: linear-gradient(135deg, rgba(245, 158, 11, 0.2), rgba(217, 119, 6, 0.25));
      border: 1px solid rgba(245, 158, 11, 0.4);
      color: #fbbf24;
    }
    .btn-wallet:hover {
      background: linear-gradient(135deg, rgba(245, 158, 11, 0.35), rgba(217, 119, 6, 0.4));
      border-color: rgba(245, 158, 11, 0.7);
      transform: translateY(-1px);
    }
    .btn-tavily {
      background: linear-gradient(135deg, rgba(6, 182, 212, 0.15), rgba(59, 130, 246, 0.2));
      border: 1px solid rgba(6, 182, 212, 0.4);
      color: #38bdf8;
    }
    .btn-tavily:hover {
      background: linear-gradient(135deg, rgba(6, 182, 212, 0.3), rgba(59, 130, 246, 0.35));
      border-color: rgba(6, 182, 212, 0.8);
      transform: translateY(-1px);
    }
    .btn-primary {
      background: linear-gradient(135deg, var(--accent-cyan), #0284c7);
      border: none; color: white;
    }
    .btn-primary:hover { opacity: 0.92; transform: translateY(-1px); }

    /* Top Metrics 4-Card Grid */
    .metrics-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 16px;
    }
    @media (max-width: 1024px) {
      .metrics-grid { grid-template-columns: repeat(2, 1fr); }
    }
    @media (max-width: 640px) {
      .metrics-grid { grid-template-columns: 1fr; }
    }

    .card {
      background: var(--card-bg);
      backdrop-filter: blur(14px);
      border: 1px solid var(--card-border);
      border-radius: 16px;
      padding: 18px 20px;
      box-shadow: 0 4px 16px rgba(0,0,0,0.2);
      transition: border-color 0.2s;
    }
    .card:hover { border-color: rgba(255, 255, 255, 0.16); }

    .card-head {
      display: flex; justify-content: space-between; align-items: center;
      margin-bottom: 8px;
    }
    .card-title {
      font-size: 12px; font-weight: 700;
      text-transform: uppercase; letter-spacing: 0.6px;
      color: var(--text-muted);
    }
    .card-value {
      font-size: 26px; font-weight: 800;
      font-family: var(--mono-font);
      display: flex; align-items: baseline; gap: 6px;
      line-height: 1.2;
    }
    .card-subtitle {
      font-size: 12px; color: var(--text-muted); margin-top: 8px;
      display: flex; align-items: center; justify-content: space-between;
    }

    /* Policy Shield Bar */
    .shield-bar {
      background: rgba(16, 185, 129, 0.06);
      border: 1px solid rgba(16, 185, 129, 0.25);
      border-radius: 14px;
      padding: 10px 18px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 12px;
      font-size: 12px;
    }
    .shield-title {
      font-weight: 700; color: var(--accent-emerald);
      display: flex; align-items: center; gap: 8px;
      font-size: 13px;
    }
    .shield-chips {
      display: flex; align-items: center; flex-wrap: wrap; gap: 10px;
    }
    .shield-chip {
      background: rgba(0, 0, 0, 0.35);
      border: 1px solid rgba(255, 255, 255, 0.08);
      padding: 4px 10px;
      border-radius: 8px;
      color: #cbd5e1;
    }
    .shield-chip strong { color: var(--accent-emerald); }

    /* Command Palette Bar */
    .command-bar {
      background: var(--card-bg);
      backdrop-filter: blur(14px);
      border: 1px solid rgba(6, 182, 212, 0.35);
      box-shadow: 0 4px 20px rgba(6, 182, 212, 0.1);
      border-radius: 14px;
      padding: 8px 12px 8px 18px;
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .command-input {
      flex: 1; background: transparent; border: none; outline: none;
      color: var(--text-main); font-size: 14px; font-family: var(--sans-font);
    }
    .command-input::placeholder { color: #64748b; }

    /* Main Workspace Split Grid */
    .workspace-grid {
      display: grid;
      grid-template-columns: 46% 54%;
      gap: 18px;
    }
    @media (max-width: 1100px) {
      .workspace-grid { grid-template-columns: 1fr; }
    }

    .panel {
      background: var(--card-bg);
      backdrop-filter: blur(14px);
      border: 1px solid var(--card-border);
      border-radius: 16px;
      display: flex; flex-direction: column;
      overflow: hidden;
      box-shadow: 0 4px 20px rgba(0,0,0,0.2);
    }
    .panel-header {
      padding: 16px 20px;
      border-bottom: 1px solid var(--card-border);
      display: flex; justify-content: space-between; align-items: center;
      background: rgba(255, 255, 255, 0.02);
    }
    .panel-title {
      font-size: 15px; font-weight: 700; display: flex; align-items: center; gap: 8px;
    }
    .panel-body {
      padding: 18px;
      height: 520px;
      overflow-y: auto;
      scrollbar-width: thin;
      scrollbar-color: rgba(255,255,255,0.15) transparent;
    }
    .panel-body::-webkit-scrollbar { width: 6px; }
    .panel-body::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.15); border-radius: 3px; }

    /* Goal & Task Styles */
    .goal-hero {
      background: linear-gradient(180deg, rgba(6, 182, 212, 0.08) 0%, rgba(15, 23, 42, 0.8) 100%);
      border: 1px solid rgba(6, 182, 212, 0.3);
      border-radius: 14px;
      padding: 16px;
      margin-bottom: 16px;
    }
    .goal-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
    .goal-badge {
      padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: 700;
      text-transform: uppercase; background: rgba(6, 182, 212, 0.2); color: var(--accent-cyan);
    }
    .goal-title { font-size: 16px; font-weight: 700; margin-bottom: 6px; }
    .goal-desc { font-size: 13px; color: var(--text-muted); margin-bottom: 12px; }
    .progress-bar-bg {
      width: 100%; height: 7px; background: rgba(255,255,255,0.08);
      border-radius: 4px; overflow: hidden; margin-bottom: 6px;
    }
    .progress-bar-fill {
      height: 100%; background: linear-gradient(90deg, var(--accent-cyan), var(--accent-emerald));
      border-radius: 4px; transition: width 0.4s ease;
    }

    .task-item {
      background: rgba(10, 16, 30, 0.7);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 12px 14px;
      margin-bottom: 10px;
      transition: all 0.2s;
    }
    .task-item:hover { border-color: rgba(255,255,255,0.18); background: rgba(10, 16, 30, 0.95); }
    .task-top { display: flex; justify-content: space-between; align-items: flex-start; gap: 8px; margin-bottom: 6px; }
    .task-title { font-size: 13px; font-weight: 600; flex: 1; }
    .badge {
      padding: 2px 7px; border-radius: 6px;
      font-size: 10px; font-weight: 700; text-transform: uppercase;
    }
    .badge-completed { background: rgba(16, 185, 129, 0.2); color: var(--accent-emerald); }
    .badge-running { background: rgba(6, 182, 212, 0.2); color: var(--accent-cyan); }
    .badge-assigned { background: rgba(168, 85, 247, 0.2); color: var(--accent-purple); }
    .badge-pending { background: rgba(245, 158, 11, 0.2); color: var(--accent-amber); }
    .badge-blocked { background: rgba(244, 63, 94, 0.2); color: var(--accent-rose); }
    .task-meta { font-size: 11px; color: var(--text-muted); display: flex; gap: 10px; }

    /* Live Stream Timeline Styles */
    .turn-entry {
      border-left: 2px solid rgba(6, 182, 212, 0.4);
      padding-left: 14px;
      margin-left: 6px;
      margin-bottom: 16px;
      position: relative;
    }
    .turn-entry::before {
      content: '';
      position: absolute;
      left: -6px; top: 4px;
      width: 10px; height: 10px;
      border-radius: 50%;
      background: var(--accent-cyan);
      box-shadow: 0 0 8px var(--accent-cyan);
    }
    .turn-header {
      display: flex; justify-content: space-between; align-items: center;
      margin-bottom: 6px;
    }
    .turn-badge {
      font-size: 11px; font-weight: 700; font-family: var(--mono-font);
      color: var(--accent-cyan);
    }
    .turn-time { font-size: 11px; color: #64748b; }
    .turn-thought {
      font-size: 13px; line-height: 1.5; color: #e2e8f0;
      background: rgba(0, 0, 0, 0.35);
      border-radius: 8px; padding: 10px 12px;
      border: 1px solid rgba(255,255,255,0.05);
      white-space: pre-wrap; word-break: break-word;
    }
    .tool-tag {
      display: inline-flex; align-items: center; gap: 4px;
      background: rgba(168, 85, 247, 0.15); border: 1px solid rgba(168, 85, 247, 0.3);
      color: #c084fc; font-size: 11px; font-family: var(--mono-font);
      padding: 2px 8px; border-radius: 6px; margin-top: 6px; margin-right: 6px;
    }

    /* Modal Styles */
    .modal-backdrop {
      display: none;
      position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
      background: rgba(0, 0, 0, 0.75);
      backdrop-filter: blur(10px);
      z-index: 1000;
      align-items: center; justify-content: center;
      padding: 20px;
    }
    .modal-card {
      background: #0f172a;
      border: 1px solid rgba(255, 255, 255, 0.15);
      border-radius: 20px;
      max-width: 600px; width: 100%;
      padding: 24px 28px;
      box-shadow: 0 16px 48px rgba(0,0,0,0.6);
      position: relative;
    }
    .modal-head {
      display: flex; justify-content: space-between; align-items: center;
      margin-bottom: 20px;
    }
    .modal-title { font-size: 18px; font-weight: 800; color: #fbbf24; display: flex; align-items: center; gap: 8px; }
    .close-btn {
      background: transparent; border: none; font-size: 20px; color: #94a3b8;
      cursor: pointer; padding: 4px;
    }
    .close-btn:hover { color: white; }
    .copy-link {
      color: var(--accent-cyan); font-size: 12px; cursor: pointer; text-decoration: underline;
    }
  </style>
</head>
<body>
  <div class="container">
    <!-- Header -->
    <header>
      <div class="brand">
        <div class="brand-icon">âš¡</div>
        <div class="brand-title">
          <h1 id="agent-name">Conway Automaton</h1>
          <p><span style="color: var(--accent-cyan);">Gemini 3.8 Flash</span> &bull; Antigravity Local Engine (0Ä‘ API)</p>
        </div>
      </div>
      <div class="header-actions">
        <div class="status-pill" id="agent-status-badge">
          <div class="pulse-dot"></div>
          <span id="agent-status-text">INITIALIZING</span>
        </div>
        <button class="btn btn-tavily" onclick="openTavilyModal()">
          ðŸŒ Tavily Search <span id="tavily-badge-status" style="font-size: 10px; margin-left: 4px; padding: 2px 6px; border-radius: 4px; background: rgba(16, 185, 129, 0.2); color: var(--accent-emerald);">Báº¬T</span>
        </button>
        <button class="btn btn-wallet" onclick="openWalletModal()">ðŸ”‘ Quáº£n LÃ½ VÃ­ &amp; RÃºt Tiá»n</button>
        <button class="btn" onclick="fetchData()">ðŸ”„ LÃ m má»›i</button>
      </div>
    </header>

    <!-- Top Metrics: 4 Clean & Balanced Cards -->
    <div class="metrics-grid">
      <!-- 1. USDC Balance -->
      <div class="card">
        <div class="card-head">
          <span class="card-title">Vá»‘n Kháº£ Dá»¥ng (Base)</span>
          <span style="font-size: 18px;">ðŸ’°</span>
        </div>
        <div class="card-value" style="color: var(--accent-emerald);">
          $<span id="usdc-balance">0.0000</span>
          <span style="font-size: 14px; color: #94a3b8; font-weight: 500;">USDC</span>
        </div>
        <div class="card-subtitle">
          <span>VÃ­: <span id="wallet-short" style="font-family: var(--mono-font);">0x4b6a...65Cd</span></span>
          <span class="copy-link" onclick="copyWallet()">Sao chÃ©p</span>
        </div>
      </div>

      <!-- 2. ETH Gas Balance -->
      <div class="card">
        <div class="card-head">
          <span class="card-title">PhÃ­ Gas Máº¡ng Base</span>
          <span style="font-size: 18px;">â›½</span>
        </div>
        <div class="card-value" style="color: var(--accent-cyan);">
          <span id="eth-balance">0.0000</span>
          <span style="font-size: 14px; color: #94a3b8; font-weight: 500;">ETH</span>
        </div>
        <div class="card-subtitle">
          <span>Base Mainnet</span>
          <a id="basescan-link" href="#" target="_blank" style="color: var(--accent-cyan); text-decoration: none; font-size: 12px;">BaseScan â†—</a>
        </div>
      </div>

      <!-- 3. Local AI Compute -->
      <div class="card">
        <div class="card-head">
          <span class="card-title">Chi PhÃ­ Suy Luáº­n LLM</span>
          <span style="font-size: 18px;">âš¡</span>
        </div>
        <div class="card-value" style="color: var(--accent-purple);">
          $0.00
          <span style="font-size: 13px; color: #94a3b8; font-weight: 500;">Miá»…n PhÃ­</span>
        </div>
        <div class="card-subtitle">
          <span>Local Bridge Port 8888</span>
          <span style="color: var(--accent-emerald); font-weight: 600;">Tiáº¿t kiá»‡m 100%</span>
        </div>
      </div>

      <!-- 4. Turns & Orchestrator -->
      <div class="card">
        <div class="card-head">
          <span class="card-title">LÆ°á»£t TÆ° Duy &amp; Tráº¡ng ThÃ¡i</span>
          <span style="font-size: 18px;">ðŸ”„</span>
        </div>
        <div class="card-value" style="color: var(--accent-amber);">
          <span id="turn-count">0</span>
          <span style="font-size: 14px; color: #94a3b8; font-weight: 500;">Turns</span>
        </div>
        <div class="card-subtitle">
          <span>Pha: <strong id="orch-phase" style="color: #cbd5e1; text-transform: uppercase;">IDLE</strong></span>
          <span style="color: #64748b;">Auto Cycle</span>
        </div>
      </div>
    </div>

    <!-- Policy Shield Bar -->
    <div class="shield-bar">
      <div class="shield-title">
        ðŸ›¡ï¸ HÃ€NG RÃ€O Báº¢O Vá»† Vá»N (Active Limits):
      </div>
      <div class="shield-chips">
        <div class="shield-chip">Chi tá»‘i Ä‘a: <strong>$2.00 / ngÃ y</strong></div>
        <div class="shield-chip">Má»—i lá»‡nh: <strong>&le; $0.50</strong></div>
        <div class="shield-chip">Dá»± trá»¯: <strong>&ge; $5.00 trong vÃ­</strong></div>
        <div class="shield-chip">Cooldown: <strong>60s giá»¯a 2 láº§n</strong></div>
        <div class="shield-chip">Chu ká»³: <strong>10 turns max</strong></div>
      </div>
    </div>

    <!-- Command Bar -->
    <div class="command-bar">
      <span style="font-size: 18px;">ðŸ’¬</span>
      <input type="text" id="user-msg-input" class="command-input" placeholder="Gá»­i chá»‰ Ä‘áº¡o hoáº·c má»¥c tiÃªu má»›i cho Agent (Nháº¥n Enter Ä‘á»ƒ gá»­i)..." onkeydown="if(event.key==='Enter') sendMessage()">
      <button class="btn btn-primary" onclick="sendMessage()">Gá»­i Lá»‡nh ðŸš€</button>
    </div>

    <!-- Main Workspace Split Grid -->
    <div class="workspace-grid">
      <!-- Left: Goals & Tasks -->
      <div class="panel">
        <div class="panel-header">
          <div class="panel-title">ðŸŽ¯ Káº¿ Hoáº¡ch &amp; Tiáº¿n Äá»™ Nhiá»‡m Vá»¥</div>
          <span id="goals-count" style="font-size: 12px; color: var(--text-muted);">0 má»¥c tiÃªu</span>
        </div>
        <div class="panel-body" id="goals-container">
          <p style="color: var(--text-muted); font-size: 13px;">Äang táº£i dá»¯ liá»‡u nhiá»‡m vá»¥...</p>
        </div>
      </div>

      <!-- Right: Live AI Thought Terminal -->
      <div class="panel">
        <div class="panel-header">
          <div class="panel-title">
            ðŸ§  Nháº­t KÃ½ TÆ° Duy Trá»±c Tiáº¿p
            <span style="display: inline-flex; align-items: center; gap: 6px; font-size: 11px; padding: 2px 8px; border-radius: 10px; background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3);">
              <span style="width: 6px; height: 6px; border-radius: 50%; background: #ef4444; box-shadow: 0 0 6px #ef4444;"></span>
              LIVE
            </span>
          </div>
          <button class="btn" style="padding: 4px 10px; font-size: 11px;" onclick="scrollToLatest()">â¬‡ï¸ Má»›i nháº¥t</button>
        </div>
        <div class="panel-body" id="turns-container">
          <p style="color: var(--text-muted); font-size: 13px;">Äang táº£i nháº­t kÃ½ tÆ° duy...</p>
        </div>
      </div>
    </div>
  </div>

  <!-- Wallet Management Modal -->
  <div class="modal-backdrop" id="wallet-modal" onclick="if(event.target===this) closeWalletModal()">
    <div class="modal-card">
      <div class="modal-head">
        <div class="modal-title">ðŸ”‘ Quáº£n LÃ½ VÃ­ &amp; Quyá»n RÃºt Tiá»n (Self-Custody)</div>
        <button class="close-btn" onclick="closeWalletModal()">&times;</button>
      </div>

      <div style="display: flex; flex-direction: column; gap: 16px; font-size: 13px;">
        <div style="background: rgba(255,255,255,0.03); border: 1px solid var(--card-border); padding: 14px; border-radius: 12px;">
          <div style="color: var(--text-muted); font-size: 11px; text-transform: uppercase; margin-bottom: 4px;">Äá»‹a chá»‰ vÃ­ Agent (Máº¡ng Base):</div>
          <div id="modal-address" style="font-family: var(--mono-font); font-size: 13px; word-break: break-all; color: var(--accent-cyan); margin-bottom: 6px;">
            0x4b6a...65Cd
          </div>
          <div style="display: flex; gap: 12px;">
            <button class="btn" style="padding: 4px 10px; font-size: 12px;" onclick="copyWallet()">ðŸ“‹ Copy Äá»‹a Chá»‰</button>
            <a id="modal-basescan" href="#" target="_blank" class="btn" style="padding: 4px 10px; font-size: 12px; text-decoration: none;">Xem trÃªn BaseScan â†—</a>
          </div>
        </div>

        <div style="background: rgba(245, 158, 11, 0.08); border: 1px solid rgba(245, 158, 11, 0.3); padding: 14px; border-radius: 12px;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
            <span style="color: #fbbf24; font-weight: 700;">Private Key VÃ­ (ChÃ¬a khÃ³a rÃºt tiá»n):</span>
            <button class="btn" style="padding: 3px 8px; font-size: 11px;" id="toggle-pk-btn" onclick="togglePrivateKey()">ðŸ‘ï¸ Hiá»‡n Key</button>
          </div>
          <div id="pk-box" style="font-family: var(--mono-font); font-size: 12px; background: rgba(0,0,0,0.5); padding: 8px 10px; border-radius: 8px; word-break: break-all; color: #fde68a;">
            â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢
          </div>
          <div style="margin-top: 8px;">
            <button class="btn btn-wallet" style="padding: 5px 12px; font-size: 12px;" onclick="copyPrivateKey()">ðŸ“‹ Copy Private Key</button>
          </div>
        </div>

        <div style="background: rgba(255,255,255,0.03); border: 1px solid var(--card-border); padding: 14px; border-radius: 12px; line-height: 1.6;">
          <div style="font-weight: 700; color: #cbd5e1; margin-bottom: 6px;">ðŸ’¡ 2 CÃ¡ch RÃºt Tiá»n Vá» VÃ­ Cá»§a Báº¡n:</div>
          <div><strong>1. RÃºt qua MetaMask / Rabby:</strong> Copy Private Key á»Ÿ trÃªn $\rightarrow$ Má»Ÿ MetaMask $\rightarrow$ Nháº­p tÃ i khoáº£n (Import) $\rightarrow$ Chuyá»ƒn toÃ n bá»™ USDC/ETH vá» vÃ­ chÃ­nh cá»§a báº¡n.</div>
          <div style="margin-top: 6px;"><strong>2. RÃºt tá»± Ä‘á»™ng báº±ng dÃ²ng lá»‡nh:</strong> Má»Ÿ PowerShell cháº¡y:<br>
            <code style="background: rgba(0,0,0,0.4); padding: 2px 6px; border-radius: 4px; color: var(--accent-cyan); font-family: var(--mono-font);">.\\withdraw.ps1 0x_dia_chi_vi_cua_ban</code>
          </div>
        </div>
      </div>

      <div style="margin-top: 20px; display: flex; justify-content: flex-end;">
        <button class="btn" onclick="closeWalletModal()">ÄÃ³ng</button>
      </div>
    </div>
  </div>

  <!-- Tavily Search Configuration Modal -->
  <div class="modal-backdrop" id="tavily-modal" onclick="if(event.target===this) closeTavilyModal()">
    <div class="modal-card" style="max-width: 650px;">
      <div class="modal-head">
        <div class="modal-title" style="color: #38bdf8;">ðŸŒ Cáº¥u HÃ¬nh &amp; Thá»­ Nghiá»‡m Tavily AI Search</div>
        <button class="close-btn" onclick="closeTavilyModal()">&times;</button>
      </div>

      <div style="display: flex; flex-direction: column; gap: 16px; font-size: 13px;">
        <!-- Status Banner -->
        <div id="tavily-status-box" style="background: rgba(6, 182, 212, 0.08); border: 1px solid rgba(6, 182, 212, 0.3); padding: 12px 16px; border-radius: 12px; display: flex; align-items: center; justify-content: space-between;">
          <div>
            <div style="font-weight: 700; color: #38bdf8; display: flex; align-items: center; gap: 8px;">
              <span>âš¡ Tráº¡ng thÃ¡i:</span> <span id="tavily-status-desc">ÄANG HOáº T Äá»˜NG</span>
            </div>
            <div style="font-size: 12px; color: var(--text-muted); margin-top: 2px;">
              Agent Ä‘Æ°á»£c trang bá»‹ cÃ´ng cá»¥ <code>web_search</code> Ä‘á»ƒ tÃ¬m kiáº¿m thá»‹ trÆ°á»ng thá»i gian thá»±c (Bounties, Crypto, Fix bugs).
            </div>
          </div>
          <span class="badge badge-completed" id="tavily-pill">HOáº T Äá»˜NG</span>
        </div>

        <!-- API Key Input -->
        <div style="background: rgba(255,255,255,0.03); border: 1px solid var(--card-border); padding: 16px; border-radius: 12px;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <label style="font-weight: 600; color: #cbd5e1;">Tavily API Key (dáº¡ng tvly-...):</label>
            <a href="https://tavily.com" target="_blank" style="color: var(--accent-cyan); font-size: 11px; text-decoration: none;">Láº¥y key miá»…n phÃ­ táº¡i tavily.com â†—</a>
          </div>
          <div style="display: flex; gap: 8px;">
            <input type="password" id="tavily-api-key-input" class="command-input" style="background: rgba(0,0,0,0.4); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; padding: 8px 12px; font-family: var(--mono-font); font-size: 12px; width: 100%;" placeholder="Nháº­p tvly-dev-...">
            <button class="btn" style="padding: 6px 12px; font-size: 12px;" id="toggle-tavily-vis-btn" onclick="toggleTavilyKeyVisibility()">ðŸ‘ï¸</button>
            <button class="btn btn-primary" style="padding: 6px 16px; font-size: 12px; white-space: nowrap;" onclick="saveTavilyKey()">ðŸ’¾ LÆ°u Key</button>
          </div>
        </div>

        <!-- Interactive Search Tester -->
        <div style="background: rgba(255,255,255,0.03); border: 1px solid var(--card-border); padding: 16px; border-radius: 12px;">
          <div style="font-weight: 600; color: #cbd5e1; margin-bottom: 8px;">ðŸ” Thá»­ Nghiá»‡m TÃ¬m Kiáº¿m Trá»±c Tiáº¿p:</div>
          <div style="display: flex; gap: 8px; margin-bottom: 12px;">
            <input type="text" id="tavily-test-query" class="command-input" style="background: rgba(0,0,0,0.4); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; padding: 8px 12px; font-size: 13px; width: 100%;" value="Base USDC bounty opportunities" placeholder="Nháº­p cÃ¢u há»i tÃ¬m kiáº¿m thá»­...">
            <button class="btn" style="background: linear-gradient(135deg, var(--accent-purple), #6366f1); border: none; padding: 6px 16px; font-size: 12px; white-space: nowrap;" onclick="runTestSearch()">TÃ¬m Thá»­ ðŸš€</button>
          </div>
          <div id="tavily-test-output" style="display: none; background: rgba(0,0,0,0.5); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 12px; max-height: 200px; overflow-y: auto; font-size: 12px; line-height: 1.5; color: #e2e8f0;">
          </div>
        </div>
      </div>

      <div style="margin-top: 20px; display: flex; justify-content: flex-end;">
        <button class="btn" onclick="closeTavilyModal()">ÄÃ³ng</button>
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
        document.getElementById('agent-status-text').textContent = `${stateText}`;
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

        // Tavily status
        const tavilyConfigured = !!status.tavily_configured;
        const tavilyBadge = document.getElementById('tavily-badge-status');
        const tavilyPill = document.getElementById('tavily-pill');
        const tavilyDesc = document.getElementById('tavily-status-desc');
        const tavilyKeyInput = document.getElementById('tavily-api-key-input');

        if (tavilyBadge && tavilyPill && tavilyDesc) {
          if (tavilyConfigured) {
            tavilyBadge.textContent = 'Báº¬T';
            tavilyBadge.style.background = 'rgba(16, 185, 129, 0.2)';
            tavilyBadge.style.color = 'var(--accent-emerald)';
            tavilyPill.textContent = 'HOáº T Äá»˜NG';
            tavilyPill.className = 'badge badge-completed';
            tavilyDesc.textContent = 'ÄANG HOáº T Äá»˜NG';
            tavilyDesc.style.color = 'var(--accent-emerald)';
          } else {
            tavilyBadge.textContent = 'CHÆ¯A Báº¬T';
            tavilyBadge.style.background = 'rgba(245, 158, 11, 0.2)';
            tavilyBadge.style.color = 'var(--accent-amber)';
            tavilyPill.textContent = 'CHÆ¯A Cáº¤U HÃŒNH';
            tavilyPill.className = 'badge badge-pending';
            tavilyDesc.textContent = 'CHÆ¯A Cáº¤U HÃŒNH';
            tavilyDesc.style.color = 'var(--accent-amber)';
          }
        }

        if (status.tavily_key && tavilyKeyInput && !tavilyKeyInput.value) {
          tavilyKeyInput.value = status.tavily_key;
        }

        // Fetch Goals
        const resGoals = await fetch('/api/goals');
        const goalsData = await resGoals.json();
        renderGoals(goalsData.goals || []);

        // Fetch Turns
        const resTurns = await fetch('/api/turns');
        const turnsData = await resTurns.json();
        renderTurns(turnsData.turns || []);
      } catch (e) {
        console.error("Fetch error:", e);
      }
    }

    function renderGoals(goals) {
      const container = document.getElementById('goals-container');
      document.getElementById('goals-count').textContent = `${goals.length} má»¥c tiÃªu`;

      if (goals.length === 0) {
        container.innerHTML = '<div style="text-align: center; color: var(--text-muted); padding: 40px 0;">Agent Ä‘ang nhÃ n rá»—i, sáºµn sÃ ng tiáº¿p nháº­n má»¥c tiÃªu má»›i.</div>';
        return;
      }

      container.innerHTML = goals.map(g => `
        <div class="goal-hero">
          <div class="goal-top">
            <span class="goal-badge">${g.status}</span>
            <span style="font-size: 12px; color: var(--accent-emerald); font-weight: 700;">${g.progress_pct}% hoÃ n thÃ nh</span>
          </div>
          <div class="goal-title">${g.title}</div>
          <div class="goal-desc">${g.description || ''}</div>
          <div class="progress-bar-bg">
            <div class="progress-bar-fill" style="width: ${g.progress_pct}%"></div>
          </div>
          <div style="font-size: 11px; color: #64748b; margin-top: 4px;">Chiáº¿n lÆ°á»£c: ${g.strategy || 'Tá»± chá»§ kinh táº¿'}</div>
        </div>

        <div style="margin-top: 10px;">
          ${(g.tasks || []).map(t => {
            const st = (t.status || 'pending').toLowerCase();
            let bClass = 'badge-pending';
            if (st === 'completed') bClass = 'badge-completed';
            else if (st === 'running') bClass = 'badge-running';
            else if (st === 'assigned') bClass = 'badge-assigned';
            else if (st === 'blocked') bClass = 'badge-blocked';

            return `
              <div class="task-item">
                <div class="task-top">
                  <div class="task-title">${t.title}</div>
                  <span class="badge ${bClass}">${t.status}</span>
                </div>
                <div class="task-meta">
                  <span>Role: ${t.role}</span>
                  ${t.result ? `<span style="color: var(--accent-cyan); cursor: pointer;" title="${t.result}">Xem káº¿t quáº£ â†—</span>` : ''}
                </div>
              </div>
            `;
          }).join('')}
        </div>
      `).join('');
    }

    function renderTurns(turns) {
      const container = document.getElementById('turns-container');
      if (turns.length === 0) {
        container.innerHTML = '<div style="text-align: center; color: var(--text-muted); padding: 40px 0;">ChÆ°a cÃ³ lÆ°á»£t suy luáº­n nÃ o Ä‘Æ°á»£c ghi nháº­n.</div>';
        return;
      }

      // Sort chronological for terminal flow
      const ordered = [...turns].reverse();

      container.innerHTML = ordered.map((t, idx) => {
        let toolsHtml = '';
        if (t.tools && t.tools.length > 0) {
          toolsHtml = t.tools.map(tc => `<span class="tool-tag">ðŸ› ï¸ ${tc.name}</span>`).join('');
        }

        const dateStr = t.created_at ? new Date(t.created_at).toLocaleTimeString() : '';

        return `
          <div class="turn-entry">
            <div class="turn-header">
              <span class="turn-badge">Turn #${idx + 1} &bull; ${t.state}</span>
              <span class="turn-time">${dateStr}</span>
            </div>
            <div class="turn-thought">${t.thinking || '(HÃ nh Ä‘á»™ng trá»±c tiáº¿p khÃ´ng suy nghÄ© dÃ i)'}</div>
            ${toolsHtml ? `<div style="margin-top: 6px;">${toolsHtml}</div>` : ''}
          </div>
        `;
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
      input.placeholder = "Äang gá»­i lá»‡nh...";
      try {
        const res = await fetch('/api/send_message', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: msg })
        });
        const data = await res.json();
        alert(data.message || (data.success ? "ÄÃ£ gá»­i thÃ nh cÃ´ng!" : "Lá»—i khi gá»­i"));
        fetchData();
      } catch (e) {
        alert("Lá»—i káº¿t ná»‘i tá»›i mÃ¡y chá»§");
      } finally {
        input.placeholder = "Gá»­i chá»‰ Ä‘áº¡o hoáº·c má»¥c tiÃªu má»›i cho Agent (Nháº¥n Enter Ä‘á»ƒ gá»­i)...";
      }
    }

    function copyWallet() {
      if (rawAddress) {
        navigator.clipboard.writeText(rawAddress);
        alert("ÄÃ£ sao chÃ©p Ä‘á»‹a chá»‰ vÃ­: " + rawAddress);
      }
    }

    function openWalletModal() {
      document.getElementById('wallet-modal').style.display = 'flex';
    }

    function closeWalletModal() {
      document.getElementById('wallet-modal').style.display = 'none';
    }

    function togglePrivateKey() {
      const box = document.getElementById('pk-box');
      const btn = document.getElementById('toggle-pk-btn');
      isPkVisible = !isPkVisible;
      if (isPkVisible) {
        box.textContent = rawPrivateKey;
        btn.textContent = 'ðŸ™ˆ áº¨n Key';
      } else {
        box.textContent = 'â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢';
        btn.textContent = 'ðŸ‘ï¸ Hiá»‡n Key';
      }
    }

    function copyPrivateKey() {
      if (rawPrivateKey) {
        navigator.clipboard.writeText(rawPrivateKey);
        alert("ÄÃ£ sao chÃ©p Private Key!\n\nBáº¡n cÃ³ thá»ƒ má»Ÿ MetaMask -> Chá»n Import Account -> DÃ¡n key vÃ o Ä‘á»ƒ rÃºt tiá»n vá» vÃ­ cá»§a báº¡n báº¥t ká»³ lÃºc nÃ o.");
      }
    }

    function openTavilyModal() {
      document.getElementById('tavily-modal').style.display = 'flex';
    }

    function closeTavilyModal() {
      document.getElementById('tavily-modal').style.display = 'none';
    }

    function toggleTavilyKeyVisibility() {
      const input = document.getElementById('tavily-api-key-input');
      const btn = document.getElementById('toggle-tavily-vis-btn');
      if (input.type === 'password') {
        input.type = 'text';
        btn.textContent = 'ðŸ™ˆ';
      } else {
        input.type = 'password';
        btn.textContent = 'ðŸ‘ï¸';
      }
    }

    async function saveTavilyKey() {
      const input = document.getElementById('tavily-api-key-input');
      const key = input.value.trim();
      if (!key) {
        alert('Vui lÃ²ng nháº­p API Key Tavily');
        return;
      }

      try {
        const res = await fetch('/api/config/tavily', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ apiKey: key })
        });
        const data = await res.json();
        alert(data.message || (data.success ? 'ÄÃ£ lÆ°u thÃ nh cÃ´ng!' : 'Lá»—i: ' + data.error));
        fetchData();
      } catch (e) {
        alert('Lá»—i káº¿t ná»‘i mÃ¡y chá»§');
      }
    }

    async function runTestSearch() {
      const queryInput = document.getElementById('tavily-test-query');
      const keyInput = document.getElementById('tavily-api-key-input');
      const output = document.getElementById('tavily-test-output');
      const query = queryInput.value.trim();

      output.style.display = 'block';
      output.innerHTML = '<div style="color: var(--accent-cyan);">â³ Äang gá»­i yÃªu cáº§u tÃ¬m kiáº¿m lÃªn Tavily AI Search...</div>';

      try {
        const res = await fetch('/api/test_search', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query, apiKey: keyInput.value.trim() })
        });
        const data = await res.json();

        if (!data.success) {
          output.innerHTML = `<div style="color: var(--accent-rose);">âŒ Lá»—i tÃ¬m kiáº¿m: ${data.error}</div>`;
          return;
        }

        let html = '';
        if (data.answer) {
          html += `<div style="margin-bottom: 8px; padding-bottom: 8px; border-bottom: 1px solid rgba(255,255,255,0.1);"><strong style="color: var(--accent-emerald);">ðŸ’¡ TÃ³m táº¯t AI:</strong> ${data.answer}</div>`;
        }

        if (data.results && data.results.length > 0) {
          html += '<strong>Káº¿t quáº£ hÃ ng Ä‘áº§u:</strong><ul style="padding-left: 18px; margin-top: 4px;">';
          for (const r of data.results) {
            html += `<li style="margin-bottom: 6px;"><a href="${r.url}" target="_blank" style="color: var(--accent-cyan); text-decoration: none; font-weight: 600;">${r.title}</a><br><span style="color: #94a3b8; font-size: 11px;">${(r.content || '').slice(0, 180)}...</span></li>`;
          }
          html += '</ul>';
        } else {
          html += '<div>KhÃ´ng tÃ¬m tháº¥y káº¿t quáº£ phÃ¹ há»£p.</div>';
        }

        output.innerHTML = html;
      } catch (e) {
        output.innerHTML = `<div style="color: var(--accent-rose);">âŒ Lá»—i káº¿t ná»‘i khi tÃ¬m kiáº¿m: ${e.message}</div>`;
      }
    }

    // Initial Fetch & 3s polling
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

