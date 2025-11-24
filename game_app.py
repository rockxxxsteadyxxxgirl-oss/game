"""
Procedural mini RPG for the browser (Streamlit).
Story beats are auto-generated and each scene is resolved with one button.
"""

import random
import time
from typing import Dict, List

import streamlit as st


st.set_page_config(page_title="Procedural RPG", page_icon="🗺️", layout="wide")

Scene = Dict[str, str]


def new_seed() -> int:
    return int(time.time())


def ensure_state() -> None:
    if "seed" not in st.session_state:
        st.session_state.seed = new_seed()
    if "world" not in st.session_state:
        st.session_state.world = {}
    if "scenes" not in st.session_state:
        st.session_state.scenes: List[Scene] = []
    if "scene_idx" not in st.session_state:
        st.session_state.scene_idx = 0
    if "hp" not in st.session_state:
        st.session_state.hp = 30
    if "log" not in st.session_state:
        st.session_state.log: List[str] = []
    if "outcome" not in st.session_state:
        st.session_state.outcome = "ongoing"  # ongoing | won | lost


def generate_world(seed: int) -> Dict[str, str]:
    rng = random.Random(seed)
    hero = rng.choice(
        ["Lina the Cartographer", "Aki of the North Wind", "Silas the Lantern Bearer", "Mira the Scout", "Rho the Tinkerer"]
    )
    origin = rng.choice(["Ashenridge", "Valemoor", "Port Tallow", "Stonebrook", "Hollowmere"])
    relic = rng.choice(["Skyforge Compass", "Echo Shard", "Sunken Crown", "Glimmer Codex", "Ironbloom Seed"])
    villain = rng.choice(["The Pale Warden", "Oracle of Rust", "Queen of Thorns", "The Gilded Shade", "Lord of Cinders"])
    region = rng.choice(["The Indigo Steppe", "Mistwild Forest", "Glass Dunes", "Thorn Coast", "Cradle Peaks"])
    twist = rng.choice(
        [
            "the relic is incomplete",
            "the villain is bound to an oath",
            "the land itself remembers",
            "old maps hide safer passes",
            "the companion knows a secret route",
        ]
    )
    companion = rng.choice(["Kira the alchemist", "Tomas the archer", "Vela the medic", "Jun the bard", "Nox the stray wolf"])
    title = f"{hero} and the {relic}"
    summary = f"{hero} leaves {origin} to stop {villain} before the {region} falls. Rumor says {twist}."
    return {
        "hero": hero,
        "origin": origin,
        "relic": relic,
        "villain": villain,
        "region": region,
        "twist": twist,
        "companion": companion,
        "title": title,
        "summary": summary,
    }


def build_scenes(world: Dict[str, str], seed: int) -> List[Scene]:
    rng = random.Random(seed + 37)
    hero = world["hero"]
    villain = world["villain"]
    relic = world["relic"]
    region = world["region"]
    companion = world["companion"]
    scenes: List[Scene] = []

    scenes.append({"type": "lore", "text": f"{hero} and {companion} step into {region}, chasing whispers of the {relic}."})
    scenes.append(
        {"type": "choice", "text": "You reach a fork: a sunlit canyon or a shaded pass. One is faster, one is safer."}
    )
    scenes.append(
        {"type": "battle", "text": "Bandits hired by the villain block the trail with rusted blades and a hungry look."}
    )
    scenes.append({"type": "lore", "text": f"At an abandoned watchtower you learn that {villain} hunts the {relic} too."})
    scenes.append(
        {"type": "choice", "text": "A storm rolls in. Do you press forward through rain or make camp in the ruins?"}
    )
    scenes.append(
        {"type": "battle", "text": "A roaming beast, warped by old magic, prowls the path and lunges from the fog."}
    )
    scenes.append(
        {"type": "lore", "text": f"The map glows faintly; the land confirms that {world['twist']}."}
    )
    scenes.append({"type": "boss", "text": f"{villain} appears at the heart of {region}, grasping for the {relic}."})

    rng.shuffle(scenes[:-1])  # shuffle everything except the final boss to vary the path
    scenes.append(scenes.pop())  # ensure boss stays last
    return scenes


def start_new_game() -> None:
    st.session_state.seed = new_seed()
    st.session_state.world = generate_world(st.session_state.seed)
    st.session_state.scenes = build_scenes(st.session_state.world, st.session_state.seed)
    st.session_state.scene_idx = 0
    st.session_state.hp = 30
    st.session_state.log = []
    st.session_state.outcome = "ongoing"


def resolve_battle(text: str, boss: bool = False) -> None:
    rng = random.Random(st.session_state.seed + st.session_state.scene_idx)
    enemy_hp = 12 + rng.randint(0, 6) + (6 if boss else 0)
    hero_hp = st.session_state.hp
    rounds = 0
    lines: List[str] = [text]
    while hero_hp > 0 and enemy_hp > 0 and rounds < 6:
        dmg_to_enemy = rng.randint(3, 7)
        dmg_to_hero = rng.randint(0, 4) + (2 if boss else 0)
        enemy_hp -= dmg_to_enemy
        if enemy_hp <= 0:
            lines.append(f"You strike for {dmg_to_enemy} and drop the foe.")
            break
        hero_hp -= dmg_to_hero
        lines.append(f"You deal {dmg_to_enemy}, take {dmg_to_hero}.")
        rounds += 1
    st.session_state.hp = max(hero_hp, 0)
    if hero_hp <= 0:
        st.session_state.outcome = "lost"
        lines.append("You collapse. The journey ends here.")
    elif boss:
        st.session_state.outcome = "won"
        lines.append("The villain falls. The relic is safe.")
    else:
        lines.append("You survive and move on.")
    st.session_state.log.extend(lines)


def resolve_choice(text: str) -> None:
    rng = random.Random(st.session_state.seed + st.session_state.scene_idx * 3)
    success = rng.random() > 0.3
    if success:
        heal = rng.randint(2, 5)
        st.session_state.hp = min(st.session_state.hp + heal, 32)
        st.session_state.log.extend([text, f"You pick well. You recover +{heal} hp on the way."])
    else:
        hurt = rng.randint(3, 6)
        st.session_state.hp = max(st.session_state.hp - hurt, 0)
        st.session_state.log.extend([text, f"A bad turn costs you {hurt} hp."])
        if st.session_state.hp <= 0:
            st.session_state.outcome = "lost"
            st.session_state.log.append("You cannot continue.")


def resolve_lore(text: str) -> None:
    st.session_state.log.append(text)


def play_scene() -> None:
    if st.session_state.outcome != "ongoing":
        return
    if st.session_state.scene_idx >= len(st.session_state.scenes):
        st.session_state.outcome = "won"
        return
    scene = st.session_state.scenes[st.session_state.scene_idx]
    st.session_state.scene_idx += 1
    if scene["type"] == "battle":
        resolve_battle(scene["text"])
    elif scene["type"] == "boss":
        resolve_battle(scene["text"], boss=True)
    elif scene["type"] == "choice":
        resolve_choice(scene["text"])
    else:
        resolve_lore(scene["text"])


def sidebar_controls() -> None:
    st.sidebar.header("RPG Controls")
    st.sidebar.button("Start new story", type="primary", on_click=start_new_game)
    st.sidebar.write("Each click on 'Resolve next scene' advances the story and auto-resolves events.")
    st.sidebar.write("HP drops to 0 -> defeat. Reach the boss and win the fight -> victory.")


def render_status() -> None:
    world = st.session_state.world
    st.subheader(world.get("title", "Adventure"))
    st.caption(world.get("summary", ""))
    cols = st.columns(3)
    cols[0].metric("Hero", world.get("hero", "-"))
    cols[1].metric("Companion", world.get("companion", "-"))
    cols[2].metric("HP", st.session_state.hp)
    if st.session_state.outcome == "won":
        st.success("You saved the region. The relic is yours.")
    elif st.session_state.outcome == "lost":
        st.error("Defeated. Restart for a new story.")
    else:
        st.info("On the road...")


def render_log() -> None:
    st.markdown("### Story log")
    for line in st.session_state.log[-30:]:
        st.write(f"- {line}")


def render_actions() -> None:
    if st.session_state.outcome == "ongoing":
        st.button("Resolve next scene", type="primary", on_click=play_scene)
        remaining = len(st.session_state.scenes) - st.session_state.scene_idx
        st.caption(f"{remaining} scenes remain.")
    else:
        st.button("Restart adventure", type="secondary", on_click=start_new_game)


def main() -> None:
    ensure_state()
    if not st.session_state.world:
        start_new_game()
    sidebar_controls()
    render_status()
    render_actions()
    render_log()


if __name__ == "__main__":
    main()
