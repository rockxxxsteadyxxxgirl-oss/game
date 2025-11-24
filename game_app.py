import random
import time
from typing import List

import streamlit as st


st.set_page_config(page_title="ライトアウト - Python ブラウザゲーム", page_icon="🎮", layout="wide")

Board = List[List[bool]]


def init_board(size: int, density: float) -> Board:
    """サイズと光の密度から初期盤面を作る。全消灯は避ける。"""
    board = [[random.random() < density for _ in range(size)] for _ in range(size)]
    if all(not cell for row in board for cell in row):
        board[0][0] = True
    return board


def reset_game() -> None:
    size = st.session_state.board_size
    density = st.session_state.density
    st.session_state.board = init_board(size, density)
    st.session_state.moves = 0
    st.session_state.started_at = time.time()
    st.session_state.won = False


def ensure_state() -> None:
    if "board_size" not in st.session_state:
        st.session_state.board_size = 5
    if "density" not in st.session_state:
        st.session_state.density = 0.45
    if "board" not in st.session_state:
        reset_game()
    if "history" not in st.session_state:
        st.session_state.history = []
    if "started_at" not in st.session_state:
        st.session_state.started_at = time.time()
    if "won" not in st.session_state:
        st.session_state.won = False


def toggle_cell(board: Board, row: int, col: int) -> None:
    size = len(board)
    for r, c in [(row, col), (row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)]:
        if 0 <= r < size and 0 <= c < size:
            board[r][c] = not board[r][c]


def handle_click(row: int, col: int) -> None:
    if st.session_state.won:
        return
    toggle_cell(st.session_state.board, row, col)
    st.session_state.moves += 1
    if all(not cell for r in st.session_state.board for cell in r):
        st.session_state.won = True
        elapsed = time.time() - st.session_state.started_at
        st.session_state.history.append(
            {
                "サイズ": st.session_state.board_size,
                "密度": st.session_state.density,
                "手数": st.session_state.moves,
                "秒": round(elapsed, 2),
            }
        )


def sidebar_controls() -> None:
    st.sidebar.title("設定")
    size = st.sidebar.slider("盤面サイズ", min_value=3, max_value=7, value=st.session_state.board_size, step=1)
    density = st.sidebar.slider("初期の灯りの多さ", min_value=0.15, max_value=0.75, value=st.session_state.density, step=0.05)
    if size != st.session_state.board_size or density != st.session_state.density:
        st.session_state.board_size = size
        st.session_state.density = density
        reset_game()
    if st.sidebar.button("新しく始める", type="primary"):
        reset_game()
    st.sidebar.markdown(
        """
        **遊び方**
        - 光っているマスをすべて消灯させればクリア。
        - マスをクリックするとそのマスと上下左右が反転。
        - 盤面サイズと光の密度を変えて難易度を調整。
        """
    )


def render_board() -> None:
    board: Board = st.session_state.board
    st.subheader("ライトアウト盤面")
    for row_idx, row in enumerate(board):
        cols = st.columns(len(row), gap="small")
        for col_idx, cell in enumerate(row):
            label = "●" if cell else "○"
            help_text = "クリックでこのマスと上下左右を反転"
            if cols[col_idx].button(label, key=f"{row_idx}-{col_idx}", use_container_width=True, help=help_text):
                handle_click(row_idx, col_idx)


def render_status() -> None:
    st.write(
        f"手数: **{st.session_state.moves}** / サイズ: **{st.session_state.board_size}x{st.session_state.board_size}** "
        f"/ 密度: **{st.session_state.density:.2f}**"
    )
    if st.session_state.won:
        st.success("おめでとう！全部消灯しました。")
    else:
        st.info("すべての光を消してクリアを目指そう。")


def render_history() -> None:
    if not st.session_state.history:
        return
    st.markdown("#### クリア履歴")
    st.dataframe(st.session_state.history, use_container_width=True, hide_index=True)


def main() -> None:
    ensure_state()
    st.title("ブラウザで遊べるライトアウト (Python + Streamlit)")
    st.caption("オープンソースな Python だけで作れるブラウザゲームのサンプル")
    sidebar_controls()
    render_status()
    render_board()
    render_history()


if __name__ == "__main__":
    main()
