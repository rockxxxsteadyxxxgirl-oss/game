import streamlit as st
from streamlit.components.v1 import html


st.set_page_config(page_title="Side Scroller - 障害物を避けるゲーム", page_icon="🏃", layout="centered")

st.title("横スクロール障害物ゲーム (やさしめ設定)")
st.caption("スペース / ↑ でジャンプ。障害物を避け続けてスコアを伸ばそう。Enter でリスタート。")

game_html = """
<style>
  body { margin: 0; background: #0d1117; color: #e6edf3; font-family: 'Segoe UI', sans-serif; }
  #wrap { display: flex; flex-direction: column; align-items: center; gap: 8px; padding: 8px; }
  canvas { background: linear-gradient(180deg, #0f172a 0%, #111827 70%, #0f172a 100%); border: 1px solid #1f2937; border-radius: 10px; box-shadow: 0 8px 24px rgba(0,0,0,0.35); }
  .hud { display: flex; gap: 12px; font-size: 14px; }
  .btn { background: #2563eb; color: white; border: none; border-radius: 6px; padding: 6px 12px; cursor: pointer; }
  .btn:active { transform: translateY(1px); }
</style>
<div id="wrap">
  <div class="hud">
    <div>Score: <span id="score">0</span></div>
    <div>Best: <span id="best">0</span></div>
    <button class="btn" id="restart">Restart</button>
  </div>
  <canvas id="game" width="820" height="420"></canvas>
  <div style="font-size:13px; color:#9ca3af;">Space/ArrowUp: Jump ・ Enter/Restart: 再開 ・ 少しゆっくりで間隔広め</div>
</div>
<script>
(() => {
  const canvas = document.getElementById("game");
  const ctx = canvas.getContext("2d");
  const scoreEl = document.getElementById("score");
  const bestEl = document.getElementById("best");
  const restartBtn = document.getElementById("restart");
  const groundY = canvas.height - 60;
  let player, obstacles, running, last, spawnTimer, score, best, speedBase;

  function reset() {
    player = { x: 100, y: groundY, w: 30, h: 30, vy: 0, onGround: true };
    obstacles = [];
    running = true;
    last = performance.now();
    spawnTimer = 0;
    score = 0;
    speedBase = 3; // 全体の進む速度を少し遅く
    renderHUD();
  }

  function loadBest() {
    const stored = localStorage.getItem("sideScrollerBest");
    best = stored ? Number(stored) : 0;
    bestEl.textContent = best.toFixed(0);
  }

  function saveBest() {
    localStorage.setItem("sideScrollerBest", String(best));
  }

  function jump() {
    if (!running) return;
    if (player.onGround) {
      player.vy = -11;
      player.onGround = false;
    }
  }

  function spawnObstacle() {
    const h = 18 + Math.random() * 40;  // 低めの障害
    const w = 18 + Math.random() * 32;  // 細めの幅
    const gap = 150 + Math.random() * 150; // 出現間隔を広めに
    const speed = speedBase + Math.min(score / 450, 4); // 加速を緩やかに
    obstacles.push({ x: canvas.width + 10, y: groundY + (30 - h), w, h, speed, gap });
  }

  function update(dt) {
    // gravity
    player.vy += 28 * dt;
    player.y += player.vy;
    if (player.y > groundY) {
      player.y = groundY;
      player.vy = 0;
      player.onGround = true;
    }
    // obstacles
    spawnTimer -= dt;
    if (spawnTimer <= 0) {
      spawnObstacle();
      spawnTimer = 1.35 - Math.min(score / 800, 0.75); // 出現頻度を控えめに
    }
    obstacles.forEach(o => { o.x -= o.speed * 60 * dt; });
    obstacles = obstacles.filter(o => o.x + o.w > -20);
    // scoring
    score += dt * 100;
    if (score > best) { best = score; saveBest(); }
    renderHUD();
    // collisions
    for (const o of obstacles) {
      if (player.x < o.x + o.w && player.x + player.w > o.x && player.y < o.y + o.h && player.y + player.h > o.y) {
        running = false;
      }
    }
  }

  function renderHUD() {
    scoreEl.textContent = score.toFixed(0);
    bestEl.textContent = best.toFixed(0);
  }

  function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    // ground
    ctx.fillStyle = "#1f2937";
    ctx.fillRect(0, groundY + 30, canvas.width, 60);
    ctx.fillStyle = "#374151";
    ctx.fillRect(0, groundY + 25, canvas.width, 5);
    // player
    ctx.fillStyle = running ? "#22d3ee" : "#ef4444";
    ctx.fillRect(player.x, player.y - player.h, player.w, player.h);
    // obstacles
    ctx.fillStyle = "#f97316";
    obstacles.forEach(o => {
      ctx.fillRect(o.x, o.y - o.h, o.w, o.h);
    });
    // text on game over
    if (!running) {
      ctx.fillStyle = "rgba(0,0,0,0.45)";
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.fillStyle = "#e5e7eb";
      ctx.font = "bold 28px 'Segoe UI'";
      ctx.textAlign = "center";
      ctx.fillText("Game Over - Enter で再開", canvas.width / 2, canvas.height / 2);
    }
  }

  function loop(timestamp) {
    const dt = Math.min((timestamp - last) / 1000, 0.05);
    if (running) {
      update(dt);
    }
    draw();
    last = timestamp;
    requestAnimationFrame(loop);
  }

  document.addEventListener("keydown", (e) => {
    if (e.code === "Space" || e.code === "ArrowUp") jump();
    if (e.code === "Enter" && !running) reset();
  });
  restartBtn.addEventListener("click", reset);
  canvas.addEventListener("pointerdown", () => jump());

  loadBest();
  reset();
  requestAnimationFrame(loop);
})();
</script>
"""

html(game_html, height=520, scrolling=False)
