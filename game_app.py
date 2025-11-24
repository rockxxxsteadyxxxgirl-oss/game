"""
Simple Game & Watch-style LCD game in the browser (Streamlit + vanilla JS).
Move left/right to catch falling blocks. Lose 1 life if you miss.
"""

import streamlit as st
from streamlit.components.v1 import html


st.set_page_config(page_title="Game & Watch風ミニゲーム", page_icon="🕹️", layout="centered")

st.title("Game & Watch 風キャッチゲーム")
st.caption("←/→ または A/D で移動。落ちてくるブロックをキャッチしてスコアを伸ばそう。")

game_markup = """
<style>
  body { margin: 0; background: #0f172a; color: #e2e8f0; font-family: "Segoe UI", sans-serif; }
  #wrap { display: flex; flex-direction: column; align-items: center; gap: 8px; padding: 8px; }
  canvas { background: #d7f8c6; border: 4px solid #0f172a; border-radius: 12px; image-rendering: pixelated; }
  .hud { display: flex; gap: 12px; font-weight: 600; }
  .btn { background: #0ea5e9; color: #0b1b2b; border: none; border-radius: 8px; padding: 6px 12px; cursor: pointer; font-weight: 700; }
  .btn:active { transform: translateY(1px); }
  .soft { color: #94a3b8; font-size: 13px; }
</style>
<div id="wrap">
  <div class="hud">
    <div>Score: <span id="score">0</span></div>
    <div>Lives: <span id="lives">3</span></div>
    <button class="btn" id="restart">Restart</button>
  </div>
  <canvas id="lcd" width="320" height="240"></canvas>
  <div class="soft">←/→ or A/D to move ・ 落下はだんだん速くなる</div>
</div>
<script>
(() => {
  const cvs = document.getElementById("lcd");
  const ctx = cvs.getContext("2d");
  const scoreEl = document.getElementById("score");
  const livesEl = document.getElementById("lives");
  const restartBtn = document.getElementById("restart");

  let player, drops, score, lives, running, speed, last;

  function reset() {
    player = { x: cvs.width / 2 - 16, y: cvs.height - 28, w: 32, h: 14, vx: 0 };
    drops = [];
    score = 0;
    lives = 3;
    speed = 55;
    running = true;
    last = performance.now();
    updateHUD();
  }

  function updateHUD() {
    scoreEl.textContent = score;
    livesEl.textContent = lives;
  }

  function spawnDrop() {
    const x = 12 + Math.random() * (cvs.width - 24);
    drops.push({ x, y: -10, w: 10, h: 10, vy: speed / 60 });
  }

  function loop(ts) {
    const dt = Math.min((ts - last) / 1000, 0.05);
    if (running) step(dt);
    draw();
    last = ts;
    requestAnimationFrame(loop);
  }

  function step(dt) {
    // movement
    player.x += player.vx * dt;
    player.x = Math.max(4, Math.min(cvs.width - player.w - 4, player.x));
    // spawn
    if (Math.random() < 0.9 * dt) spawnDrop();
    // move drops
    drops.forEach(d => d.y += d.vy * 60 * dt);
    // collisions
    for (let i = drops.length - 1; i >= 0; i--) {
      const d = drops[i];
      if (d.y + d.h >= player.y && d.y <= player.y + player.h && d.x + d.w >= player.x && d.x <= player.x + player.w) {
        drops.splice(i, 1);
        score += 10;
        speed = Math.min(speed + 1.8, 140); // slowly increase difficulty
        continue;
      }
      if (d.y > cvs.height + 4) {
        drops.splice(i, 1);
        lives -= 1;
        if (lives <= 0) running = false;
      }
    }
    updateHUD();
  }

  function drawLCDRect(x, y, w, h, color) {
    ctx.fillStyle = color;
    ctx.fillRect(Math.round(x), Math.round(y), Math.round(w), Math.round(h));
  }

  function draw() {
    ctx.clearRect(0, 0, cvs.width, cvs.height);
    // backdrop frame lines
    ctx.strokeStyle = "#9dc59a";
    ctx.lineWidth = 1;
    for (let i = 0; i < cvs.height; i += 20) {
      ctx.beginPath();
      ctx.moveTo(0, i + 0.5);
      ctx.lineTo(cvs.width, i + 0.5);
      ctx.stroke();
    }
    // player
    drawLCDRect(player.x, player.y, player.w, player.h, running ? "#0b4f1f" : "#7f1d1d");
    // drops
    drops.forEach(d => drawLCDRect(d.x, d.y, d.w, d.h, "#123c5a"));
    if (!running) {
      ctx.fillStyle = "rgba(0,0,0,0.45)";
      ctx.fillRect(0, 0, cvs.width, cvs.height);
      ctx.fillStyle = "#e11d48";
      ctx.font = "bold 22px 'Segoe UI'";
      ctx.textAlign = "center";
      ctx.fillText("GAME OVER - Restartで再開", cvs.width / 2, cvs.height / 2);
    }
  }

  // input
  const pressed = new Set();
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

  function updateVel() {
    if (pressed.has("L") && !pressed.has("R")) player.vx = -120;
    else if (pressed.has("R") && !pressed.has("L")) player.vx = 120;
    else player.vx = 0;
  }

  // touch/mouse buttons for mobile
  const btnLeft = document.createElement("button");
  const btnRight = document.createElement("button");
  btnLeft.textContent = "←";
  btnRight.textContent = "→";
  [btnLeft, btnRight].forEach(btn => {
    btn.className = "btn";
    btn.style.width = "64px";
    btn.style.margin = "4px";
  });
  const mobileBar = document.createElement("div");
  mobileBar.style.display = "flex";
  mobileBar.style.gap = "8px";
  mobileBar.appendChild(btnLeft);
  mobileBar.appendChild(btnRight);
  document.getElementById("wrap").appendChild(mobileBar);

  btnLeft.addEventListener("pointerdown", () => { pressed.add("L"); updateVel(); });
  btnRight.addEventListener("pointerdown", () => { pressed.add("R"); updateVel(); });
  btnLeft.addEventListener("pointerup", () => { pressed.delete("L"); updateVel(); });
  btnRight.addEventListener("pointerup", () => { pressed.delete("R"); updateVel(); });

  restartBtn.addEventListener("click", reset);

  reset();
  requestAnimationFrame(loop);
})();
</script>
"""

html(game_markup, height=420, scrolling=False)
