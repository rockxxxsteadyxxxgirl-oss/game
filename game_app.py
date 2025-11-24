"""
Game & Watch style catch game (Streamlit + vanilla JS).
- Starts easy (spawnBase=3.0) and ramps difficulty over time
- Special gems: slow / fever / magnet / reflector / rainbow
- Combo: slow -> fever chain triggers rainbow (near-stop + 3x score)
- Timed missions every 30s; rewards = fragment + shield
- Collect 3 fragments to unlock/advance visual themes (saved to localStorage)
- Wind & drifting floor, magnet pull, reflector bounces, ghost replay
- BGM with layered lead/bass/hat/pad; tempo speeds up at higher scores
- Controls: Left/Right or A/D, Enter/Space/Restart to restart, touch buttons included
"""

import streamlit as st
from streamlit.components.v1 import html


st.set_page_config(page_title="Game & Watch Catch", page_icon="GW", layout="centered")

st.title("Game & Watch style - Evolving look")
st.caption(
    "Special gem combos trigger rainbow mode; fragments unlock new themes. Wind, missions, ghost replay, and layered chiptune BGM."
)

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
  #wrap { display: flex; flex-direction: column; align-items: center; gap: 10px; padding: 10px; padding-bottom: 220px; box-sizing: border-box; }
  canvas { border: 6px solid var(--frame); border-radius: 16px; box-shadow: 0 14px 32px rgba(0,0,0,0.4); width: min(98vw, 420px); height: auto; display: block; }
  .hud { display: flex; gap: 8px; font-weight: 700; align-items: center; flex-wrap: wrap; justify-content: center; }
  .pill { background: var(--pill-bg); padding: 6px 10px; border-radius: 999px; border: 1px solid var(--pill-border); color: var(--pill-text); }
  .btn { background: linear-gradient(180deg, var(--btn1), var(--btn2)); color: #0a1525; border: none; border-radius: 10px; padding: 7px 14px; cursor: pointer; font-weight: 800; box-shadow: 0 4px 12px rgba(0,0,0,0.25); }
  .btn:active { transform: translateY(1px); }
  .soft { color: #9ca3af; font-size: 13px; text-align: center; }
  select { padding: 4px 8px; border-radius: 8px; border: 1px solid #233044; background: #0f172a; color: #e5e7eb; }
  .joy-wrap { width: 110px; height: 110px; border-radius: 50%; border: 2px solid #e5e7eb; background: rgba(31,41,55,0.6); position: relative; touch-action: none; }
  .joy-knob { width: 42px; height: 42px; border-radius: 50%; background: linear-gradient(180deg, #22d3ee, #0ea5e9); position: absolute; left: 34px; top: 34px; box-shadow: 0 4px 10px rgba(0,0,0,0.35); }
  @media (max-width: 600px) {
    .hud { gap: 6px; }
    .pill { padding: 5px 8px; font-size: 12px; }
  }
</style>
<div id="wrap">
  <div class="hud">
    <div class="pill">Score: <span id="score">0</span></div>
    <div class="pill">Lives: <span id="lives">3</span></div>
    <div class="pill">Effect: <span id="effect">None</span></div>
    <div class="pill">Theme: <span id="themeName">Classic</span></div>
    <div class="pill">Fragments: <span id="fragments">0/3</span></div>
    <div class="pill">Mission: <span id="missionText">---</span></div>
    <button class="btn" id="restart">Restart</button>
  </div>
  <div class="hud">
    <label>Theme Select: <select id="themeSelect"></select></label>
  </div>
  <canvas id="lcd" width="420" height="450"></canvas>
  <div class="soft">Combo: slow -> fever = rainbow. Missions, wind, magnet, reflector, ghost replay. Enter/Space/Restart to retry. Mobile: swipe field or use joystick.</div>
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
  const missionEl = document.getElementById("missionText");
  const restartBtn = document.getElementById("restart");
  const themeSelect = document.getElementById("themeSelect");

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

  let unlocked = new Set([0]);
  let selectedTheme = 0;
  try {
    const saved = JSON.parse(localStorage.getItem("gwUnlocked") || "[]");
    saved.forEach(v => unlocked.add(v));
    const savedSel = Number(localStorage.getItem("gwThemeIdx"));
    if (!Number.isNaN(savedSel) && unlocked.has(savedSel)) selectedTheme = savedSel;
  } catch (_) {}

  let themeColors = themes[selectedTheme];
  const fragmentGoal = 3;
  let fragments = 0;

  let player, drops, sparks, score, lives, running, speedBase, spawnBase, spawnTimer, last, startedAt;
  let effects = { slow: 0, fever: 0, rainbow: 0, magnet: 0, reflector: 0, shield: 0 };
  let chainStage = 0; // 0 none, 1 slow, chain to fever -> rainbow
  let audioCtx = null;
  let bgmInterval = null;
  let wind = 0;
  let windTimer = 0;
  const windLockout = 15.0; // first 15s no wind
  let floorPhase = 0;

  let mission = null;
  let lastMissTime = 0;
  let missionTimer = 0;

  let ghostData = null;
  let ghostSample = [];
  let themeIndex = selectedTheme;

  function initGhost() {
    try {
      ghostData = JSON.parse(localStorage.getItem("gwGhost") || "null");
    } catch (_) {
      ghostData = null;
    }
  }

  function saveGhost(run) {
    try {
      localStorage.setItem("gwGhost", JSON.stringify(run));
    } catch (_) {}
  }

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
    themeEl.textContent = theme.name;
  }

  function renderThemeSelect() {
    themeSelect.innerHTML = "";
    themes.forEach((t, idx) => {
      const opt = document.createElement("option");
      opt.value = idx;
      opt.textContent = unlocked.has(idx) ? t.name : `${t.name} (Locked)`;
      opt.disabled = !unlocked.has(idx);
      if (idx === selectedTheme) opt.selected = true;
      themeSelect.appendChild(opt);
    });
  }

  function unlockTheme(idx) {
    unlocked.add(idx);
    localStorage.setItem("gwUnlocked", JSON.stringify([...unlocked]));
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
    master.gain.value = 0.07;
    master.connect(audioCtx.destination);
    const leadGain = audioCtx.createGain(); leadGain.gain.value = 1.0; leadGain.connect(master);
    const bassGain = audioCtx.createGain(); bassGain.gain.value = 0.6; bassGain.connect(master);
    const hatGain = audioCtx.createGain(); hatGain.gain.value = 0.35; hatGain.connect(master);
    const padGain = audioCtx.createGain(); padGain.gain.value = 0.3; padGain.connect(master);

    const chords = [
      [196, 247, 294], // Gm-ish
      [220, 262, 330], // A sus
      [174, 220, 262], // F-ish
      [247, 311, 370], // Bdim-ish
    ];

    function padChord(freqs, length = 0.9) {
      freqs.forEach((f, i) => {
        blip(f, length, padGain, 0.15, i % 2 === 0 ? "triangle" : "sine");
      });
    }

    let step = 0;
    function loopBeat() {
      const base = 520;
      const bpmAdjust = score >= 300 ? 0.75 : score >= 150 ? 0.85 : 1.0;
      const interval = base * bpmAdjust;
      const chord = chords[step % chords.length];
      const leadNotes = [...chord, chord[0] * 2];
      const ln = leadNotes[(step * 2) % leadNotes.length];
      blip(ln, 0.35, leadGain, 0.32, "square");
      if (step % 2 === 0) blip(chord[0] / 2, 0.6, bassGain, 0.28, "triangle");
      blip(820 + Math.random() * 120, 0.08, hatGain, 0.15, "sawtooth");
      if (step % 4 === 0) padChord(chord);
      if (effects.rainbow > 0) blip(1200 + Math.random() * 200, 0.18, leadGain, 0.22, "triangle");
      step++;
      bgmInterval = setTimeout(loopBeat, interval);
    }
    if (bgmInterval) clearTimeout(bgmInterval);
    loopBeat();
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
    speedBase = 28;
    spawnBase = 3.0;
    spawnTimer = 0.2;
    running = true;
    startedAt = performance.now();
    last = performance.now();
    effects = { slow: 0, fever: 0, rainbow: 0, magnet: 0, reflector: 0, shield: 0 };
    chainStage = 0;
    fragments = 0;
    themeIndex = selectedTheme;
    applyTheme(themes[themeIndex]);
    wind = 0;
    windTimer = 4;
    floorPhase = 0;
    mission = null;
    missionTimer = 0;
    lastMissTime = performance.now();
    ghostSample = [];
    initMission();
    updateHUD();
    renderThemeSelect();
  }

  function updateHUD() {
    scoreEl.textContent = score;
    livesEl.textContent = lives;
    const active = Object.entries(effects).filter(([k, v]) => v > 0).map(([k, v]) => `${k}:${v.toFixed(1)}s`);
    effectEl.textContent = active.length ? active.join(",") : "None";
    fragEl.textContent = `${fragments}/${fragmentGoal}`;
    missionEl.textContent = mission ? mission.text : "---";
  }

  function difficultyFactor() {
    const elapsed = (performance.now() - startedAt) / 1000;
    return 1 + Math.min(elapsed / 100, 1.8);
  }

  function speedMultiplier() {
    let m = 1;
    if (effects.slow > 0) m *= 0.55;
    if (effects.fever > 0) m *= 1.25;
    if (effects.rainbow > 0) m *= 0.05;
    return m;
  }

  function scoreMultiplier() {
    let m = 1;
    if (effects.fever > 0) m *= 2;
    if (effects.rainbow > 0) m *= 3;
    return m;
  }

  function spawnDrop() {
    const x = 18 + Math.random() * (cvs.width - 36);
    const vy = (speedBase * difficultyFactor() * speedMultiplier()) / 70;
    const special = Math.random() < 0.18;
    const kinds = ["slow", "fever", "magnet", "reflector", "rainbow"];
    const kind = special ? kinds[Math.floor(Math.random() * kinds.length)] : "normal";
    drops.push({ x, y: -12, w: 12, h: 12, vy, kind, vx: 0 });
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
    if (kind === "slow") effects.slow = 6.0;
    if (kind === "fever") effects.fever = 7.0;
    if (kind === "rainbow") effects.rainbow = 3.0;
    if (kind === "magnet") effects.magnet = 6.0;
    if (kind === "reflector") effects.reflector = 7.0;
  }

  function handleCombo(kind) {
    if (kind === "slow") {
      chainStage = 1;
      applyEffect("slow");
      return;
    }
    if (kind === "fever") {
      if (chainStage === 1) {
        chainStage = 0;
        applyEffect("rainbow");
      } else {
        chainStage = 0;
        applyEffect("fever");
      }
      return;
    }
    if (kind === "rainbow") {
      chainStage = 0;
      applyEffect("rainbow");
      return;
    }
    chainStage = 0;
    applyEffect(kind);
  }

  function initMission() {
    const types = ["right", "left", "specials", "no_miss"];
    const t = types[Math.floor(Math.random() * types.length)];
    const now = performance.now();
    missionTimer = now + 30000;
    if (t === "right") mission = { type: t, target: 3, progress: 0, text: "Catch 3 on right (30s)" };
    if (t === "left") mission = { type: t, target: 3, progress: 0, text: "Catch 3 on left (30s)" };
    if (t === "specials") mission = { type: t, target: 2, progress: 0, text: "Catch 2 special gems (30s)" };
    if (t === "no_miss") mission = { type: t, target: 15, progress: 0, text: "15s no miss (30s)" };
  }

  function completeMission() {
    fragments += 1;
    effects.shield = 5.0;
    maybeAdvanceTheme();
    initMission();
  }

  function updateMission(onCatch, drop) {
    const now = performance.now();
    if (!mission) return;
    if (mission.type === "right" && onCatch && drop.x > cvs.width / 2) mission.progress++;
    if (mission.type === "left" && onCatch && drop.x < cvs.width / 2) mission.progress++;
    if (mission.type === "specials" && onCatch && drop.kind !== "normal") mission.progress++;
    if (mission.type === "no_miss") {
      const sinceMiss = (now - lastMissTime) / 1000;
      mission.progress = Math.max(mission.progress, Math.min(mission.target, sinceMiss));
    }
    if (mission.progress >= mission.target) completeMission();
    if (now > missionTimer) initMission();
  }

  function maybeAdvanceTheme() {
    if (fragments >= fragmentGoal) {
      fragments = 0;
      const next = (themeIndex + 1) % themes.length;
      unlockTheme(next);
      themeIndex = next;
      selectedTheme = next;
      localStorage.setItem("gwThemeIdx", selectedTheme);
      applyTheme(themes[themeIndex]);
      renderThemeSelect();
    }
  }

  function step(dt) {
    Object.keys(effects).forEach(k => { if (effects[k] > 0) effects[k] = Math.max(0, effects[k] - dt); });

    player.x += player.vx * dt;
    player.x = Math.max(6, Math.min(cvs.width - player.w - 6, player.x));

    windTimer -= dt;
    const aliveTime = (performance.now() - startedAt) / 1000;
    if (aliveTime >= windLockout) {
      if (windTimer <= 0) {
        wind = (Math.random() - 0.5) * 60;
        windTimer = 6 + Math.random() * 6;
      }
    } else {
      wind = 0;
      windTimer = 1; // keep simple countdown until unlock
    }
    floorPhase += dt;

    spawnTimer -= dt;
    if (spawnTimer <= 0) {
      spawnDrop();
      const df = difficultyFactor();
      const eff = effects.slow > 0 ? 1.25 : effects.fever > 0 ? 0.85 : 1.0;
      spawnTimer = Math.max(0.36, (spawnBase * eff) / df);
    }

    const timeScale = speedMultiplier();
    drops.forEach(d => {
      if (effects.reflector > 0 && d.vx === 0) d.vx = (Math.random() - 0.5) * 50;
      if (effects.reflector > 0) {
        d.x += d.vx * dt;
        if (d.x < 2 || d.x > cvs.width - d.w - 2) d.vx *= -1;
      }
      d.x += wind * dt * 0.25;
      d.y += d.vy * 60 * dt * timeScale;
      if (effects.magnet > 0) {
        const target = player.x + player.w / 2;
        d.x += (target - d.x) * 0.6 * dt;
      }
    });

    for (let i = drops.length - 1; i >= 0; i--) {
      const d = drops[i];
      const hitX = d.x + d.w >= player.x && d.x <= player.x + player.w;
      const hitY = d.y + d.h >= player.y && d.y <= player.y + player.h;
      if (hitX && hitY) {
        drops.splice(i, 1);
        const gain = 10 * scoreMultiplier();
        score += gain;
        speedBase = Math.min(speedBase + 1.2, 150);
        if (d.kind !== "normal") {
          handleCombo(d.kind);
          if (Math.random() < 0.35) {
            fragments += 1;
            maybeAdvanceTheme();
          }
        }
        spawnSparks(player.x + player.w / 2, player.y);
        updateMission(true, d);
        continue;
      }
      if (d.y > cvs.height + 10) {
        drops.splice(i, 1);
        const insideX = d.x + d.w > 0 && d.x < cvs.width;
        if (insideX && effects.shield <= 0) {
          lives -= 1;
          lastMissTime = performance.now();
          if (lives <= 0) running = false;
        }
        // screen-out misses (outside X range) are ignored
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

    updateMission(false, null);
    updateHUD();
  }

  function drawBackground() {
    const g = ctx.createLinearGradient(0, 0, 0, cvs.height);
    g.addColorStop(0, themeColors.lcd1);
    g.addColorStop(1, themeColors.lcd2);
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, cvs.width, cvs.height);

    ctx.fillStyle = themeColors.grid;
    const drift = Math.sin(floorPhase * 0.4) * 8;
    for (let y = 0; y < cvs.height; y += 24) {
      ctx.fillRect(drift, y, cvs.width, 1);
    }
    ctx.fillStyle = themeColors.ground;
    ctx.fillRect(drift, cvs.height - 38, cvs.width, 38);
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
        const tail = d.kind === "slow" ? "#38bdf8" : d.kind === "fever" ? "#f59e0b" : "#a3e635";
        gem.addColorStop(1, tail);
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

  function drawGhost(elapsed) {
    if (!ghostData || !ghostData.samples || ghostData.samples.length === 0) return;
    const samples = ghostData.samples;
    let gx = samples[samples.length - 1].x;
    for (let i = 0; i < samples.length; i++) {
      if (samples[i].t >= elapsed) { gx = samples[i].x; break; }
    }
    ctx.save();
    ctx.globalAlpha = 0.35;
    ctx.fillStyle = "#e5e7eb";
    ctx.fillRect(gx, player.y, player.w, player.h);
    ctx.restore();
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
    drawGhost((performance.now() - startedAt) / 1000);
    drawPlayer();
    drawSparks();
    drawOverlay();
  }

  function loop(ts) {
    const dt = Math.min((ts - last) / 1000, 0.05);
    if (running) {
      step(dt);
      if (ghostSample.length === 0 || ts - ghostSample[ghostSample.length - 1].raw > 100) {
        ghostSample.push({ t: (ts - startedAt) / 1000, x: player.x, raw: ts });
      }
    } else {
      if (ghostSample.length > 10) {
        saveGhost({ samples: ghostSample.map(s => ({ t: s.t, x: s.x })) });
      }
    }
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

  themeSelect.addEventListener("change", e => {
    const idx = Number(e.target.value);
    if (unlocked.has(idx)) {
      selectedTheme = idx;
      themeIndex = idx;
      localStorage.setItem("gwThemeIdx", selectedTheme);
      applyTheme(themes[idx]);
    }
  });

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
  mobileBar.style.flexDirection = "column";
  mobileBar.style.alignItems = "center";
  mobileBar.style.gap = "10px";
  mobileBar.style.marginTop = "8px";
  mobileBar.style.marginBottom = "16px";
  mobileBar.style.width = "100%";
  mobileBar.style.maxWidth = "480px";
  const btnRow = document.createElement("div");
  btnRow.style.display = "flex";
  btnRow.style.gap = "10px";
  btnRow.style.justifyContent = "center";
  btnRow.appendChild(leftBtn);
  btnRow.appendChild(rightBtn);
  mobileBar.appendChild(btnRow);
  document.getElementById("wrap").appendChild(mobileBar);

  leftBtn.addEventListener("pointerdown", () => { pressed.add("L"); ensureAudio(); updateVel(); });
  rightBtn.addEventListener("pointerdown", () => { pressed.add("R"); ensureAudio(); updateVel(); });
  leftBtn.addEventListener("pointerup", () => { pressed.delete("L"); updateVel(); });
  rightBtn.addEventListener("pointerup", () => { pressed.delete("R"); updateVel(); });

  // mobile: swipe to move (tap alone does not move)
  let dragActive = false;
  let dragStartX = 0;
  let dragStartPlayer = 0;
  function clampPlayer(x) {
    return Math.max(6, Math.min(cvs.width - player.w - 6, x));
  }
  cvs.addEventListener("pointerdown", e => {
    dragActive = true;
    dragStartX = e.clientX;
    dragStartPlayer = player.x;
    ensureAudio();
  });
  cvs.addEventListener("pointermove", e => {
    if (!dragActive) return;
    const dx = e.clientX - dragStartX;
    player.x = clampPlayer(dragStartPlayer + dx);
  });
  cvs.addEventListener("pointerup", () => { dragActive = false; });
  cvs.addEventListener("pointerleave", () => { dragActive = false; });

  // pseudo joystick (mobile friendly)
  const joyWrap = document.createElement("div");
  joyWrap.className = "joy-wrap";
  const joyKnob = document.createElement("div");
  joyKnob.className = "joy-knob";
  joyWrap.appendChild(joyKnob);
  const joyLabel = document.createElement("div");
  joyLabel.textContent = "Joystick";
  joyLabel.style.color = "#e5e7eb";
  joyLabel.style.fontSize = "12px";
  joyLabel.style.textAlign = "center";
  joyLabel.style.width = "110px";
  joyLabel.style.marginBottom = "4px";
  const joyColumn = document.createElement("div");
  joyColumn.style.display = "flex";
  joyColumn.style.flexDirection = "column";
  joyColumn.style.alignItems = "center";
  joyColumn.appendChild(joyLabel);
  joyColumn.appendChild(joyWrap);
  mobileBar.appendChild(joyColumn);
  let joyActive = false;
  let joyCenter = { x: 0, y: 0 };
  function setJoyPos(dx, dy) {
    const radius = 35;
    const len = Math.hypot(dx, dy);
    const scale = len > radius ? radius / len : 1;
    joyKnob.style.left = `${34 + dx * scale}px`;
    joyKnob.style.top = `${34 + dy * scale}px`;
  }
  function joyStart(e) {
    joyActive = true;
    const rect = joyWrap.getBoundingClientRect();
    joyCenter = { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 };
    joyMove(e);
  }
  function joyMove(e) {
    if (!joyActive) return;
    const dx = e.clientX - joyCenter.x;
    const dy = e.clientY - joyCenter.y;
    setJoyPos(dx, dy);
    const normX = Math.max(-1, Math.min(1, dx / 35));
    player.vx = normX * 140;
  }
  function joyEnd() {
    joyActive = false;
    setJoyPos(0, 0);
    player.vx = 0;
  }
  joyWrap.addEventListener("pointerdown", e => { ensureAudio(); joyStart(e); });
  joyWrap.addEventListener("pointermove", joyMove);
  joyWrap.addEventListener("pointerup", joyEnd);
  joyWrap.addEventListener("pointerleave", joyEnd);

  restartBtn.addEventListener("click", () => { ensureAudio(); reset(); });

  initGhost();
  applyTheme(themes[selectedTheme]);
  renderThemeSelect();
  reset();
  requestAnimationFrame(loop);
})();
</script>
"""

html(markup, height=1200, scrolling=False)
