"""
Game & Watch style catch game.
- ゆっくりスタート (spawnBase=3.0) → 時間経過で徐々に難化
- 特殊宝石でスロー/フィーバー効果
- 断片を集めるとCSSテーマが進化（3テーマをループ）
- BGMはスコア帯でレイヤー追加（リード/ベース/ハット）
操作: 左右キー or A/D, Enter/Space または Restart で再開。タッチボタンあり。
"""

import streamlit as st
from streamlit.components.v1 import html


st.set_page_config(page_title="Game & Watch Catch", page_icon="GW", layout="centered")

st.title("Game & Watch style - Evolving look")
st.caption("ゆっくり始まり、時間でじわじわ難化。特殊宝石でスロー/フィーバー、断片3つでテーマ進化。")

markup = r"""
<style>
  :root {
    --bg: #0f172a;
    --frame: #0a1a30;
    --lcd1: #eefbe4;
    --lcd2: #cfe6bc;
    --pill-bg: #1f2937;
    --pill-border: #233044;
    --pill-text: #cbd5e1;
    --btn1: #2bc0ff;
    --btn2: #178adf;
  }
  body { margin: 0; background: var(--bg); color: #e2e8f0; font-family: "Segoe UI", sans-serif; }
  #wrap { display: flex; flex-direction: column; align-items: center; gap: 10px; padding: 10px; }
  canvas { border: 6px solid var(--frame); border-radius: 16px; box-shadow: 0 14px 32px rgba(0,0,0,0.4); }
  .hud { display: flex; gap: 10px; font-weight: 700; align-items: center; flex-wrap: wrap; justify-content: center; }
  .pill { background: var(--pill-bg); padding: 6px 12px; border-radius: 999px; border: 1px solid var(--pill-border); color: var(--pill-text); }
  .btn { background: linear-gradient(180deg, var(--btn1), var(--btn2)); color: #0a1525; border: none; border-radius: 10px; padding: 7px 14px; cursor: pointer; font-weight: 800; box-shadow: 0 4px 12px rgba(0,0,0,0.25); }
  .btn:active { transform: translateY(1px); }
  .soft { color: #9ca3af; font-size: 13px; }
</style>
<div id="wrap">
  <div class="hud">
    <div class="pill">Score: <span id="score">0</span></div>
    <div class="pill">Lives: <span id="lives">3</span></div>
    <div class="pill">Effect: <span id="effect">None</span></div>
    <div class="pill">Theme: <span id="themeName">Classic</span></div>
    <div class="pill">Fragments: <span id="fragments">0/3</span></div>
    <button class="btn" id="restart">Restart</button>
  </div>
  <canvas id="lcd" width="360" height="440"></canvas>
  <div class="soft">特殊宝石でスロー/フィーバー。断片3つでテーマ進化。左右キー/A・D、Enter/Spaceで再スタート。</div>
</div>
<script>
(() => {
  const cvs = document.getElementById("lcd");
  const ctx = cvs.getContext("2d");
  const scoreEl = document.getElementById("score");
  const livesEl = document.getElementById("lives");
  const effectEl = document.getElementById("effect");
  const themeEl = document.getElementById("themeName");
  const fragEl = document.getElementById("fragments");
  const restartBtn = document.getElementById("restart");

  const themes = [
    {
      name: "Classic Mint",
      bg: "#0f172a", frame: "#0a1a30", lcd1: "#eefbe4", lcd2: "#cfe6bc",
      grid: "#b9d7a0", ground: "#a6c48a",
      gemEdge: "#0f3c5c", gemTop: "#33bef2", gemBottom: "#0d74c4",
      playerDark: "#0b4f1f", playerLight: "#0e6f2b",
      pillBg: "#1f2937", pillBorder: "#233044", pillText: "#cbd5e1",
      btn1: "#2bc0ff", btn2: "#178adf", spark: "#fbbf24",
    },
    {
      name: "Sunset Amber",
      bg: "#1f0f1c", frame: "#3f1f33", lcd1: "#fef3c7", lcd2: "#fcd34d",
      grid: "#f59e0b", ground: "#f97316",
      gemEdge: "#7c2d12", gemTop: "#fb923c", gemBottom: "#ea580c",
      playerDark: "#7c3aed", playerLight: "#a855f7",
      pillBg: "#2b1b29", pillBorder: "#4b2e3f", pillText: "#fde68a",
      btn1: "#fb7185", btn2: "#ec4899", spark: "#fcd34d",
    },
    {
      name: "Deep Ocean",
      bg: "#0b1222", frame: "#0f1f3a", lcd1: "#dbeafe", lcd2: "#93c5fd",
      grid: "#60a5fa", ground: "#3b82f6",
      gemEdge: "#0f172a", gemTop: "#38bdf8", gemBottom: "#0ea5e9",
      playerDark: "#0b4f1f", playerLight: "#34d399",
      pillBg: "#0f172a", pillBorder: "#1e293b", pillText: "#c7d2fe",
      btn1: "#22d3ee", btn2: "#0ea5e9", spark: "#a5b4fc",
    },
  ];

  let themeColors = themes[0];
  let themeIndex = 0;
  let fragments = 0;
  const fragmentGoal = 3;

  let player, drops, sparks, score, lives, running, speedBase, spawnBase, spawnTimer, last, startedAt;
  let effect = { type: "none", timer: 0 }; // none | slow | fever
  let audioCtx = null;
  let bgmInterval = null;

  function applyTheme(theme) {
    themeColors = theme;
    const root = document.documentElement;
    root.style.setProperty("--bg", theme.bg);
    root.style.setProperty("--frame", theme.frame);
    root.style.setProperty("--lcd1", theme.lcd1);
    root.style.setProperty("--lcd2", theme.lcd2);
    root.style.setProperty("--pill-bg", theme.pillBg);
    root.style.setProperty("--pill-border", theme.pillBorder);
    root.style.setProperty("--pill-text", theme.pillText);
    root.style.setProperty("--btn1", theme.btn1);
    root.style.setProperty("--btn2", theme.btn2);
    if (themeEl) themeEl.textContent = theme.name;
  }

  function blip(freq, length, gainNode, volume = 0.35, type = "square") {
    const osc = audioCtx.createOscillator();
    const env = audioCtx.createGain();
    osc.type = type;
    osc.frequency.value = freq;
    env.gain.value = 0;
    osc.connect(env);
    env.connect(gainNode);
    const now = audioCtx.currentTime;
    env.gain.setValueAtTime(0, now);
    env.gain.linearRampToValueAtTime(volume, now + 0.02);
    env.gain.exponentialRampToValueAtTime(0.001, now + length);
    osc.start(now);
    osc.stop(now + length + 0.02);
  }

  function startBGM() {
    if (audioCtx) {
      if (audioCtx.state === "suspended") audioCtx.resume();
      return;
    }
    audioCtx = new AudioContext();
    const master = audioCtx.createGain();
    master.gain.value = 0.06;
    master.connect(audioCtx.destination);
    const leadGain = audioCtx.createGain(); leadGain.gain.value = 1.0; leadGain.connect(master);
    const bassGain = audioCtx.createGain(); bassGain.gain.value = 0.55; bassGain.connect(master);
    const hatGain = audioCtx.createGain(); hatGain.gain.value = 0.35; hatGain.connect(master);

    let step = 0;
    bgmInterval = setInterval(() => {
      const leadNotes = [196, 220, 247, 262, 294, 330, 349];
      blip(leadNotes[step % leadNotes.length], 0.5, leadGain, 0.35, "square");

      if (score >= 80) {
        const bassNotes = [98, 110, 123, 131];
        blip(bassNotes[step % bassNotes.length], 0.65, bassGain, 0.25, "triangle");
      }
      if (score >= 180 && step % 2 === 0) {
        blip(760, 0.15, hatGain, 0.18, "sawtooth");
      }
      step++;
    }, 600);
  }

  function ensureAudio() {
    startBGM();
  }

  function reset() {
    player = { x: cvs.width / 2 - 18, y: cvs.height - 54, w: 36, h: 16, vx: 0 };
    drops = [];
    sparks = [];
    score = 0;
    lives = 3;
    speedBase = 28;  // slow start
    spawnBase = 3.0; // generous interval start
    spawnTimer = 0.2;
    running = true;
    startedAt = performance.now();
    last = performance.now();
    effect = { type: "none", timer: 0 };
    fragments = 0;
    themeIndex = 0;
    applyTheme(themes[themeIndex]);
    updateHUD();
  }

  function updateHUD() {
    scoreEl.textContent = score;
    livesEl.textContent = lives;
    effectEl.textContent = effect.type === "none" ? "None" : `${effect.type} (${effect.timer.toFixed(1)}s)`;
    fragEl.textContent = `${fragments}/${fragmentGoal}`;
  }

  function difficultyFactor() {
    const elapsed = (performance.now() - startedAt) / 1000; // seconds
    return 1 + Math.min(elapsed / 100, 1.8); // up to ~2.8x
  }

  function effectSpeedMultiplier() {
    if (effect.type === "slow") return 0.55;
    if (effect.type === "fever") return 1.25;
    return 1.0;
  }

  function effectScoreMultiplier() {
    if (effect.type === "fever") return 2;
    return 1;
  }

  function spawnDrop() {
    const x = 18 + Math.random() * (cvs.width - 36);
    const vy = (speedBase * difficultyFactor() * effectSpeedMultiplier()) / 70;
    const special = Math.random() < 0.16; // 16%で特殊宝石
    const kind = special ? (Math.random() < 0.5 ? "slow" : "fever") : "normal";
    drops.push({ x, y: -12, w: 12, h: 12, vy, kind });
  }

  function spawnSparks(x, y) {
    for (let i = 0; i < 6; i++) {
      sparks.push({
        x, y,
        vx: (Math.random() - 0.5) * 90,
        vy: -20 - Math.random() * 30,
        life: 0.4
      });
    }
  }

  function applyEffect(kind) {
    if (kind === "slow") {
      effect = { type: "slow", timer: 6.0 };
    } else if (kind === "fever") {
      effect = { type: "fever", timer: 7.0 };
    }
  }

  function maybeAdvanceTheme() {
    if (fragments >= fragmentGoal) {
      fragments = 0;
      themeIndex = (themeIndex + 1) % themes.length;
      applyTheme(themes[themeIndex]);
    }
  }

  function step(dt) {
    if (effect.type !== "none") {
      effect.timer -= dt;
      if (effect.timer <= 0) {
        effect = { type: "none", timer: 0 };
      }
    }

    player.x += player.vx * dt;
    player.x = Math.max(6, Math.min(cvs.width - player.w - 6, player.x));

    spawnTimer -= dt;
    if (spawnTimer <= 0) {
      spawnDrop();
      const df = difficultyFactor();
      const eff = effect.type === "slow" ? 1.25 : effect.type === "fever" ? 0.85 : 1.0; // slowで間隔長め、feverで短め
      spawnTimer = Math.max(0.36, (spawnBase * eff) / df);
    }

    drops.forEach(d => d.y += d.vy * 60 * dt);

    for (let i = drops.length - 1; i >= 0; i--) {
      const d = drops[i];
      const hitX = d.x + d.w >= player.x && d.x <= player.x + player.w;
      const hitY = d.y + d.h >= player.y && d.y <= player.y + player.h;
      if (hitX && hitY) {
        drops.splice(i, 1);
        const baseGain = 10 * effectScoreMultiplier();
        score += baseGain;
        speedBase = Math.min(speedBase + 1.2, 150); // mild accel per catch
        if (d.kind !== "normal") {
          applyEffect(d.kind);
          if (Math.random() < 0.35) {
            fragments += 1;
            maybeAdvanceTheme();
          }
        }
        spawnSparks(player.x + player.w / 2, player.y);
        continue;
      }
      if (d.y > cvs.height + 10) {
        drops.splice(i, 1);
        lives -= 1;
        if (lives <= 0) running = false;
      }
    }

    for (let i = sparks.length - 1; i >= 0; i--) {
      const p = sparks[i];
      p.life -= dt;
      p.x += p.vx * dt;
      p.y += p.vy * dt;
      p.vy += 160 * dt;
      if (p.life <= 0) sparks.splice(i, 1);
    }

    updateHUD();
  }

  function drawBackground() {
    const g = ctx.createLinearGradient(0, 0, 0, cvs.height);
    g.addColorStop(0, themeColors.lcd1);
    g.addColorStop(1, themeColors.lcd2);
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, cvs.width, cvs.height);

    ctx.fillStyle = themeColors.grid;
    for (let y = 0; y < cvs.height; y += 24) {
      ctx.fillRect(0, y, cvs.width, 1);
    }
    ctx.fillStyle = themeColors.ground;
    ctx.fillRect(0, cvs.height - 38, cvs.width, 38);
  }

  function drawPlayer() {
    ctx.save();
    ctx.translate(Math.round(player.x), Math.round(player.y));
    ctx.fillStyle = "rgba(0,0,0,0.2)";
    ctx.fillRect(2, 6, player.w, 8);
    ctx.fillStyle = themeColors.playerDark;
    ctx.fillRect(0, 0, player.w, player.h);
    ctx.fillStyle = themeColors.playerLight;
    ctx.fillRect(4, 3, player.w - 8, player.h - 6);
    ctx.restore();
  }

  function drawDrops() {
    drops.forEach(d => {
      ctx.save();
      ctx.translate(Math.round(d.x), Math.round(d.y));
      const isSpecial = d.kind !== "normal";
      ctx.fillStyle = isSpecial ? "#6b21a8" : themeColors.gemEdge;
      ctx.fillRect(-1, -1, d.w + 2, d.h + 2);
      const gem = ctx.createLinearGradient(0, 0, d.w, d.h);
      if (isSpecial) {
        gem.addColorStop(0, "#e879f9");
        gem.addColorStop(1, d.kind === "slow" ? "#38bdf8" : "#f59e0b");
      } else {
        gem.addColorStop(0, themeColors.gemTop);
        gem.addColorStop(1, themeColors.gemBottom);
      }
      ctx.fillStyle = gem;
      ctx.fillRect(0, 0, d.w, d.h);
      ctx.fillStyle = "rgba(255,255,255,0.35)";
      ctx.fillRect(2, 2, d.w / 2, d.h / 2);
      ctx.restore();
    });
  }

  function drawSparks() {
    sparks.forEach(p => {
      ctx.globalAlpha = Math.max(p.life * 2.2, 0);
      ctx.fillStyle = themeColors.spark;
      ctx.fillRect(p.x, p.y, 3, 3);
      ctx.globalAlpha = 1;
    });
  }

  function drawOverlay() {
    if (!running) {
      ctx.fillStyle = "rgba(0,0,0,0.5)";
      ctx.fillRect(0, 0, cvs.width, cvs.height);
      ctx.fillStyle = "#f87171";
      ctx.font = "bold 22px 'Segoe UI'";
      ctx.textAlign = "center";
      ctx.fillText("GAME OVER", cvs.width / 2, cvs.height / 2 - 10);
      ctx.fillStyle = "#e2e8f0";
      ctx.font = "16px 'Segoe UI'";
      ctx.fillText("Press Restart / Enter / Space", cvs.width / 2, cvs.height / 2 + 14);
    }
  }

  function draw() {
    ctx.clearRect(0, 0, cvs.width, cvs.height);
    drawBackground();
    drawDrops();
    drawPlayer();
    drawSparks();
    drawOverlay();
  }

  function loop(ts) {
    const dt = Math.min((ts - last) / 1000, 0.05);
    if (running) step(dt);
    draw();
    last = ts;
    requestAnimationFrame(loop);
  }

  const pressed = new Set();
  function updateVel() {
    if (pressed.has("L") && !pressed.has("R")) player.vx = -120;
    else if (pressed.has("R") && !pressed.has("L")) player.vx = 120;
    else player.vx = 0;
  }

  document.addEventListener("keydown", e => {
    if (e.code === "ArrowLeft" || e.code === "KeyA") pressed.add("L");
    if (e.code === "ArrowRight" || e.code === "KeyD") pressed.add("R");
    if (!running && (e.code === "Enter" || e.code === "Space")) reset();
    ensureAudio();
    updateVel();
  });
  document.addEventListener("keyup", e => {
    if (e.code === "ArrowLeft" || e.code === "KeyA") pressed.delete("L");
    if (e.code === "ArrowRight" || e.code === "KeyD") pressed.delete("R");
    updateVel();
  });

  // mobile touch buttons
  const leftBtn = document.createElement("button");
  const rightBtn = document.createElement("button");
  leftBtn.textContent = "Left";
  rightBtn.textContent = "Right";
  [leftBtn, rightBtn].forEach(btn => {
    btn.className = "btn";
    btn.style.width = "86px";
    btn.style.margin = "4px";
  });
  const mobileBar = document.createElement("div");
  mobileBar.style.display = "flex";
  mobileBar.style.gap = "10px";
  mobileBar.style.marginTop = "6px";
  mobileBar.appendChild(leftBtn);
  mobileBar.appendChild(rightBtn);
  document.getElementById("wrap").appendChild(mobileBar);

  leftBtn.addEventListener("pointerdown", () => { pressed.add("L"); ensureAudio(); updateVel(); });
  rightBtn.addEventListener("pointerdown", () => { pressed.add("R"); ensureAudio(); updateVel(); });
  leftBtn.addEventListener("pointerup", () => { pressed.delete("L"); updateVel(); });
  rightBtn.addEventListener("pointerup", () => { pressed.delete("R"); updateVel(); });

  restartBtn.addEventListener("click", () => { ensureAudio(); reset(); });

  reset();
  requestAnimationFrame(loop);
})();
</script>
"""

html(markup, height=580, scrolling=False)
