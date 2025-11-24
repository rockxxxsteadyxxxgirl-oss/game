"""
Game & Watch style catch game with a cleaner look.
Controls: Left/Right or A/D. Catch falling gems, lose a life when missed.
"""

import streamlit as st
from streamlit.components.v1 import html


st.set_page_config(page_title="Game & Watch Catch", page_icon="GW", layout="centered")

st.title("Game & Watch style - Clean look")
st.caption("Left/Right or A/D to move. Catch falling gems. Miss three times and it's game over.")

markup = """
<style>
  :root {
    --bg: #0f172a;
    --frame: #0a1a30;
    --lcd: #e8f5d4;
    --ink: #0b3a3e;
    --accent: #18a0fb;
    --shadow: rgba(0,0,0,0.32);
  }
  body { margin: 0; background: var(--bg); color: #e2e8f0; font-family: "Segoe UI", sans-serif; }
  #wrap { display: flex; flex-direction: column; align-items: center; gap: 10px; padding: 10px; }
  canvas { border: 6px solid var(--frame); border-radius: 16px; box-shadow: 0 14px 32px rgba(0,0,0,0.4); }
  .hud { display: flex; gap: 14px; font-weight: 700; align-items: center; }
  .pill { background: #1f2937; padding: 6px 12px; border-radius: 999px; border: 1px solid #233044; color: #cbd5e1; }
  .btn { background: linear-gradient(180deg, #2bc0ff, #178adf); color: #0a1525; border: none; border-radius: 10px; padding: 7px 14px; cursor: pointer; font-weight: 800; box-shadow: 0 4px 12px rgba(0,0,0,0.25); }
  .btn:active { transform: translateY(1px); }
  .soft { color: #9ca3af; font-size: 13px; }
</style>
<div id="wrap">
  <div class="hud">
    <div class="pill">Score: <span id="score">0</span></div>
    <div class="pill">Lives: <span id="lives">3</span></div>
    <button class="btn" id="restart">Restart</button>
  </div>
  <canvas id="lcd" width="360" height="440"></canvas>
  <div class="soft">Left/Right or A/D to move. Touch buttons below on mobile. Speed rises slowly.</div>
</div>
<script>
(() => {
  const cvs = document.getElementById("lcd");
  const ctx = cvs.getContext("2d");
  const scoreEl = document.getElementById("score");
  const livesEl = document.getElementById("lives");
  const restartBtn = document.getElementById("restart");

  let player, drops, sparks, score, lives, running, speed, spawnTimer, last;

  function reset() {
    player = { x: cvs.width / 2 - 18, y: cvs.height - 54, w: 36, h: 16, vx: 0 };
    drops = [];
    sparks = [];
    score = 0;
    lives = 3;
    speed = 50;
    spawnTimer = 0;
    running = true;
    last = performance.now();
    updateHUD();
  }

  function updateHUD() {
    scoreEl.textContent = score;
    livesEl.textContent = lives;
  }

  function spawnDrop() {
    const x = 18 + Math.random() * (cvs.width - 36);
    const vy = speed / 70;
    drops.push({ x, y: -12, w: 12, h: 12, vy });
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

  function step(dt) {
    player.x += player.vx * dt;
    player.x = Math.max(6, Math.min(cvs.width - player.w - 6, player.x));

    spawnTimer -= dt;
    if (spawnTimer <= 0) {
      spawnDrop();
      spawnTimer = 0.8 - Math.min(score / 1500, 0.55);
    }

    drops.forEach(d => d.y += d.vy * 60 * dt);

    for (let i = drops.length - 1; i >= 0; i--) {
      const d = drops[i];
      const hitX = d.x + d.w >= player.x && d.x <= player.x + player.w;
      const hitY = d.y + d.h >= player.y && d.y <= player.y + player.h;
      if (hitX && hitY) {
        drops.splice(i, 1);
        score += 10;
        speed = Math.min(speed + 2.4, 150);
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
    g.addColorStop(0, "#eefbe4");
    g.addColorStop(1, "#cfe6bc");
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, cvs.width, cvs.height);

    ctx.fillStyle = "#b9d7a0";
    for (let y = 0; y < cvs.height; y += 24) {
      ctx.fillRect(0, y, cvs.width, 1);
    }
    ctx.fillStyle = "#a6c48a";
    ctx.fillRect(0, cvs.height - 38, cvs.width, 38);
  }

  function drawPlayer() {
    ctx.save();
    ctx.translate(Math.round(player.x), Math.round(player.y));
    ctx.fillStyle = "rgba(0,0,0,0.2)";
    ctx.fillRect(2, 6, player.w, 8);
    ctx.fillStyle = "#0b4f1f";
    ctx.fillRect(0, 0, player.w, player.h);
    ctx.fillStyle = "#0e6f2b";
    ctx.fillRect(4, 3, player.w - 8, player.h - 6);
    ctx.restore();
  }

  function drawDrops() {
    drops.forEach(d => {
      ctx.save();
      ctx.translate(Math.round(d.x), Math.round(d.y));
      ctx.fillStyle = "#0f3c5c";
      ctx.fillRect(-1, -1, d.w + 2, d.h + 2);
      const gem = ctx.createLinearGradient(0, 0, d.w, d.h);
      gem.addColorStop(0, "#33bef2");
      gem.addColorStop(1, "#0d74c4");
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
      ctx.fillStyle = "#fbbf24";
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
      ctx.fillText("Press Restart or Enter", cvs.width / 2, cvs.height / 2 + 14);
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
    if (pressed.has("L") && !pressed.has("R")) player.vx = -130;
    else if (pressed.has("R") && !pressed.has("L")) player.vx = 130;
    else player.vx = 0;
  }

  document.addEventListener("keydown", e => {
    if (e.code === "ArrowLeft" || e.code === "KeyA") pressed.add("L");
    if (e.code === "ArrowRight" || e.code === "KeyD") pressed.add("R");
    if (!running && e.code === "Enter") reset();
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

  leftBtn.addEventListener("pointerdown", () => { pressed.add("L"); updateVel(); });
  rightBtn.addEventListener("pointerdown", () => { pressed.add("R"); updateVel(); });
  leftBtn.addEventListener("pointerup", () => { pressed.delete("L"); updateVel(); });
  rightBtn.addEventListener("pointerup", () => { pressed.delete("R"); updateVel(); });

  restartBtn.addEventListener("click", reset);

  reset();
  requestAnimationFrame(loop);
})();
</script>
"""

html(markup, height=520, scrolling=False)
