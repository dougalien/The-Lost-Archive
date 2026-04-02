
import csv
import io
import json
import random
from collections import OrderedDict, defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Contrabulator Quiz", page_icon="💎", layout="centered")

APP_TITLE = "Contrabulator Quiz"
GRID_W = 4
GRID_H = 4

CSS = """
<style>
html, body, [class*="css"]  {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}
.block-container {
    max-width: 850px;
    padding-top: 0.8rem;
    padding-bottom: 2rem;
}
.stButton > button, .stDownloadButton > button {
    width: 100%;
    border-radius: 12px;
    padding: 0.58rem 0.72rem;
    border: 1px solid #d7e1ea;
}
.card {
    background: linear-gradient(180deg, #fbfdff 0%, #eef5ff 100%);
    border: 1px solid #d9e4f2;
    border-radius: 16px;
    padding: 0.9rem 1rem;
    margin-bottom: 0.75rem;
}
.soft {
    color: #53606d;
    font-size: 0.95rem;
}
.small {
    color: #5c6978;
    font-size: 0.86rem;
}
.kicker {
    display: inline-block;
    padding: 0.18rem 0.52rem;
    border-radius: 999px;
    background: #edf3fb;
    border: 1px solid #dce6f2;
    margin-right: 0.3rem;
    margin-bottom: 0.25rem;
    font-size: 0.83rem;
}
.story-log {
    background: #fbfcfe;
    border: 1px solid #e5ebf4;
    border-radius: 16px;
    padding: 0.85rem 0.9rem;
}
.map-box {
    background: #f8fbff;
    border: 1px solid #e1e8f2;
    border-radius: 16px;
    padding: 0.7rem 0.9rem;
    margin-top: 0.25rem;
    margin-bottom: 0.45rem;
}
.map-box pre {
    margin: 0;
    font-size: 1.15rem;
    line-height: 1.42;
    text-align: center;
}
</style>
"""

ROOM_FLAVOR = [
    "The room feels like a small lesson space carved out of the building.",
    "A faint hum suggests the Contrabulator can almost make sense of this topic.",
    "Notes, diagrams, and quiet little clues are tucked into the corners here.",
    "This room feels familiar, as if it was built from a chapter heading and a study guide.",
]

SURPRISES = [
    "A wall panel flickers and reveals a tiny schematic of the Contrabulator.",
    "You spot a note in the margin: steady review beats panic every time.",
    "For a second the room glows and the machine sounds almost repaired.",
    "A side drawer opens and closes on its own, as if the room approves of careful thinking.",
]

DEMO_PACK = [
    {
        "question": "Which rock type forms when magma cools?",
        "choice_a": "Igneous",
        "choice_b": "Sedimentary",
        "choice_c": "Metamorphic",
        "choice_d": "Organic",
        "correct_answer": "Igneous",
        "topic": "Geology Demo",
        "room": "Igneous Basics",
        "tags": "igneous, magma",
        "hint": "Think molten rock.",
        "explanation": "Igneous rocks form from cooled magma or lava."
    },
    {
        "question": "Which sedimentary rock commonly reacts with dilute acid?",
        "choice_a": "Shale",
        "choice_b": "Limestone",
        "choice_c": "Sandstone",
        "choice_d": "Slate",
        "correct_answer": "Limestone",
        "topic": "Geology Demo",
        "room": "Sedimentary Basics",
        "tags": "sedimentary, carbonate",
        "hint": "Think calcite.",
        "explanation": "Limestone commonly contains calcite, which reacts with acid."
    },
    {
        "question": "What is the softest mineral on the Mohs scale?",
        "choice_a": "Quartz",
        "choice_b": "Talc",
        "choice_c": "Gypsum",
        "choice_d": "Calcite",
        "correct_answer": "Talc",
        "topic": "Geology Demo",
        "room": "Minerals",
        "tags": "minerals, hardness",
        "hint": "It is softer than a fingernail.",
        "explanation": "Talc is the softest mineral on the Mohs scale."
    },
    {
        "question": "Which planet is a gas giant?",
        "choice_a": "Mars",
        "choice_b": "Venus",
        "choice_c": "Jupiter",
        "choice_d": "Mercury",
        "correct_answer": "Jupiter",
        "topic": "Geology Demo",
        "room": "Planets",
        "tags": "planets, gas giants",
        "hint": "It is the largest planet.",
        "explanation": "Jupiter is a gas giant."
    },
    {
        "question": "Weathering breaks rock down ____.",
        "choice_a": "in place",
        "choice_b": "only underwater",
        "choice_c": "only by heat",
        "choice_d": "inside magma chambers",
        "correct_answer": "in place",
        "topic": "Geology Demo",
        "room": "Surface Processes",
        "tags": "weathering, erosion",
        "hint": "Transport happens later.",
        "explanation": "Weathering breaks rock down in place; erosion transports it."
    },
    {
        "question": "Which layer lies directly below the lithosphere?",
        "choice_a": "Inner core",
        "choice_b": "Asthenosphere",
        "choice_c": "Outer core",
        "choice_d": "Upper crust",
        "correct_answer": "Asthenosphere",
        "topic": "Geology Demo",
        "room": "Earth Interior",
        "tags": "lithosphere, asthenosphere",
        "hint": "It is weaker and can flow slowly.",
        "explanation": "The lithosphere lies above the asthenosphere."
    },
]

ROOM_HINTS = {
    "Cosmos and Big Bang": "Think heliocentric model, redshift, expansion, or the age of the universe.",
    "Stars, Elements, and Solar System Birth": "Think stellar fusion, supernovas, or solar wind.",
    "Planets and Moon": "Think terrestrial planets, gas giants, Kepler, or the Moon.",
    "Early Earth, Core, and Magnetic Shield": "Think density, convection, or Earth's magnetic field.",
    "Earth Composition, Materials, and Igneous Rocks": "Think silicates, volatiles, granite, or natural glass.",
    "Earth Interior and Seismic Structure": "Think seismic waves, the Moho, depth, and temperature.",
    "Crust, Ophiolites, and Lithosphere": "Think crust type, lithosphere, asthenosphere, and oceanic crust.",
}

MARSHAK_ROOM_ORDER = [
    "Cosmos and Big Bang",
    "Stars, Elements, and Solar System Birth",
    "Planets and Moon",
    "Early Earth, Core, and Magnetic Shield",
    "Earth Composition, Materials, and Igneous Rocks",
    "Earth Interior and Seismic Structure",
    "Crust, Ophiolites, and Lithosphere",
]

MARSHAK_LAYOUT = {
    1: (1, 0),  # q1
    2: (1, 0),  # q2 etc unused
}

def get_secret(name: str, default=None):
    try:
        return st.secrets[name]
    except Exception:
        return default

def contact_email() -> str:
    return str(get_secret("CONTACT_EMAIL", "set CONTACT_EMAIL in secrets"))

def build_accessibility_css() -> str:
    extra = []
    if st.session_state.get("access_high_contrast"):
        extra.append("""
        <style>
        body, .stApp { background: #ffffff !important; color: #111111 !important; }
        .card, .story-log, .map-box { background: #ffffff !important; border: 2px solid #1f2937 !important; }
        .soft, .small { color: #1f2937 !important; }
        .stButton > button, .stDownloadButton > button { border: 2px solid #1f2937 !important; }
        </style>
        """)
    if st.session_state.get("access_large_text"):
        extra.append("""
        <style>
        html, body, [class*="css"], .stMarkdown, .stText, label, p, li, .stRadio label { font-size: 1.08rem !important; }
        .map-box pre { font-size: 1.3rem !important; }
        </style>
        """)
    return "\n".join(extra)

def inject_accessibility_css():
    extra = build_accessibility_css()
    if extra:
        st.markdown(extra, unsafe_allow_html=True)

def render_brand_footer():
    st.markdown("---")
    st.markdown(
        f"<div class='small' style='text-align:center'><strong>We are dougalien</strong><br>{contact_email()}</div>",
        unsafe_allow_html=True,
    )

def render_brand_banner():
    st.markdown(
        f"<div class='small' style='text-align:center; margin-bottom:0.5rem;'><strong>We are dougalien</strong> · {contact_email()}</div>",
        unsafe_allow_html=True,
    )

def slugify(text: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "-" for ch in text).strip("-")

def is_missing(val) -> bool:
    return val is None or (isinstance(val, float) and pd.isna(val)) or str(val).strip() == "" or str(val).lower() == "nan"

def default_explanation(answer_text: str) -> str:
    return f"The keyed answer is: {answer_text}."

def default_hint(topic: str, room: str) -> str:
    if room in ROOM_HINTS:
        return ROOM_HINTS[room]
    if room:
        return f"Think about the core idea of {room.lower()}."
    return f"Look for the most direct clue in this {topic.lower()} question."

def infer_room_from_text(question_text: str, topic: str = "", tags: str = "") -> str:
    text = " ".join([str(question_text), str(topic), str(tags)]).lower()
    if "chapter 1 - the earth in context" in text or "earth in context" in text:
        if any(k in text for k in ["geocentric", "heliocentric", "big bang", "red shift", "red shifts", "blue shifts", "doppler", "universe", "expanding"]):
            return "Cosmos and Big Bang"
        if any(k in text for k in ["supernova", "supernovas", "hydrogen", "helium", "solar wind", "first stars", "elements in earth's rocks"]):
            return "Stars, Elements, and Solar System Birth"
        if any(k in text for k in ["terrestrial planets", "jovian", "gas giant", "ellipse", "kepler", "moon", "pluto", "planetesimals", "planet or moon"]):
            return "Planets and Moon"
        if any(k in text for k in ["magnetic field", "solar wind and cosmic radiation", "dipole", "convection", "aurorae", "liquid outer core", "differentiation of the core", "metal alloy"]):
            return "Early Earth, Core, and Magnetic Shield"
        if any(k in text for k in ["atmosphere", "hydrocarbons", "silicates", "ultramafic", "mafic", "natural glass", "granite", "crust of earth are", "whole earth, the four most common elements", "volatiles"]):
            return "Earth Composition, Materials, and Igneous Rocks"
        if any(k in text for k in ["seismic waves", "geothermal gradient", "moho", "inner core", "temperature", "pressure", "thickness of earth's crust"]):
            return "Earth Interior and Seismic Structure"
        if any(k in text for k in ["ophiolite", "oceanic crust", "lithosphere", "asthenosphere", "crust and mantle", "rigidity", "cooler and less able to flow", "found deeper underneath continents"]):
            return "Crust, Ophiolites, and Lithosphere"

    if not is_missing(tags):
        tag_list = [t.strip() for t in str(tags).replace(";", ",").split(",") if t.strip()]
        if tag_list:
            return tag_list[0].title()
    if not is_missing(topic):
        return str(topic).strip()
    return "General"

def normalize_pack(items: List[Dict], default_source: str = "Custom Pack") -> List[Dict]:
    normalized = []
    for raw in items:
        q_text = str(raw.get("question") or raw.get("q") or "").strip()
        if not q_text:
            continue

        choices = []
        raw_choices = raw.get("choices")
        if isinstance(raw_choices, list):
            choices = [str(c).strip() for c in raw_choices if str(c).strip()]
        elif isinstance(raw_choices, str) and raw_choices.strip():
            if "|" in raw_choices:
                choices = [c.strip() for c in raw_choices.split("|") if c.strip()]
        if not choices:
            for key in ["choice_a", "choice_b", "choice_c", "choice_d", "choice_e"]:
                value = raw.get(key)
                if not is_missing(value):
                    choices.append(str(value).strip())

        if len(choices) < 2:
            continue

        answer_raw = raw.get("correct_answer", raw.get("answer", raw.get("a")))
        answer_index = None
        answer_text = None

        if isinstance(answer_raw, int):
            if 0 <= answer_raw < len(choices):
                answer_index = answer_raw
        elif not is_missing(answer_raw):
            ans = str(answer_raw).strip()
            answer_text = ans
            if ans.isdigit():
                idx = int(ans)
                if 0 <= idx < len(choices):
                    answer_index = idx
                elif 1 <= idx <= len(choices):
                    answer_index = idx - 1
            elif len(ans) == 1 and ans.upper() in "ABCDE":
                idx = ord(ans.upper()) - ord("A")
                if 0 <= idx < len(choices):
                    answer_index = idx
            else:
                lowered = ans.lower()
                for i, choice in enumerate(choices):
                    if choice.lower() == lowered:
                        answer_index = i
                        break

        if answer_index is None:
            continue
        answer_text = choices[answer_index]

        topic = str(raw.get("topic") or raw.get("source") or default_source).strip() or default_source
        room = str(raw.get("room") or raw.get("subtopic") or "").strip()
        tags_raw = raw.get("tags") or raw.get("tag") or ""
        if not room:
            room = infer_room_from_text(q_text, topic, str(tags_raw))

        if isinstance(tags_raw, list):
            tags = [str(t).strip() for t in tags_raw if str(t).strip()]
        else:
            tags = [t.strip() for t in str(tags_raw).replace(";", ",").split(",") if t.strip()]

        if not tags:
            tags = [room, slugify(room).replace("-", " ")]

        hint = str(raw.get("hint") or "").strip()
        explanation = str(raw.get("explanation") or raw.get("explain") or "").strip()
        if not hint:
            hint = default_hint(topic, room)
        if not explanation:
            explanation = default_explanation(answer_text)

        normalized.append(
            {
                "q": q_text,
                "choices": choices,
                "a": answer_index,
                "answer_text": answer_text,
                "hint": hint,
                "explain": explanation,
                "topic": topic,
                "room": room,
                "tags": tags,
            }
        )
    return normalized

def dedupe_pack(pack: List[Dict]) -> List[Dict]:
    seen = set()
    out = []
    for q in pack:
        key = (
            q["q"].strip().lower(),
            tuple(c.strip().lower() for c in q["choices"]),
            int(q["a"]),
            q["room"].strip().lower(),
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(q)
    return out

def parse_uploaded_pack(uploaded_file):
    try:
        content = uploaded_file.getvalue()
        if uploaded_file.name.lower().endswith(".json"):
            data = json.loads(content.decode("utf-8"))
            if isinstance(data, dict):
                items = data.get("questions", [])
            else:
                items = data
        else:
            text = content.decode("utf-8-sig")
            items = list(csv.DictReader(io.StringIO(text)))
        pack = dedupe_pack(normalize_pack(items, default_source=uploaded_file.name))
        if not pack:
            return [], "No valid multiple-choice questions were found."
        return pack, None
    except Exception as exc:
        return [], f"Could not read the uploaded file: {exc}"

def demo_pack():
    return dedupe_pack(normalize_pack(DEMO_PACK, default_source="Geology Demo"))

def ordered_rooms(pack: List[Dict]) -> List[str]:
    seen = OrderedDict()
    for q in pack:
        room = q["room"].strip()
        if room and room not in seen:
            seen[room] = None
    rooms = list(seen.keys())
    if not rooms:
        return ["General"]
    return rooms

def group_by_room(pack: List[Dict]) -> Dict[str, List[Dict]]:
    grouped = OrderedDict()
    for room in ordered_rooms(pack):
        grouped[room] = []
    for q in pack:
        grouped.setdefault(q["room"], []).append(q)
    return grouped

def layout_for_room_count(n: int) -> List[Tuple[int, int]]:
    templates = {
        1: [(1, 1)],
        2: [(1, 1), (2, 1)],
        3: [(1, 0), (1, 1), (2, 1)],
        4: [(1, 0), (0, 1), (1, 1), (2, 1)],
        5: [(1, 0), (0, 1), (1, 1), (2, 1), (1, 2)],
        6: [(1, 0), (0, 1), (1, 1), (2, 1), (1, 2), (2, 2)],
        7: [(1, 0), (0, 1), (1, 1), (2, 1), (0, 2), (1, 2), (2, 2)],
        8: [(1, 0), (0, 1), (1, 1), (2, 1), (0, 2), (1, 2), (2, 2), (1, 3)],
        9: [(1, 0), (0, 1), (1, 1), (2, 1), (0, 2), (1, 2), (2, 2), (1, 3), (2, 3)],
    }
    if n in templates:
        return templates[n]
    coords = []
    base = templates[9][:]
    while len(coords) < n:
        coords.extend(base)
    return coords[:n]

def build_story_map(rooms: List[str], seed: int) -> Dict:
    rng = random.Random(seed)
    room_list = rooms[:]
    if rooms != MARSHAK_ROOM_ORDER[: len(rooms)]:
        rng.shuffle(room_list)
    coords = layout_for_room_count(len(room_list))
    room_positions = dict(zip(room_list, coords))
    pos_to_room = {v: k for k, v in room_positions.items()}
    exits = {}
    deltas = {"north": (0, -1), "south": (0, 1), "west": (-1, 0), "east": (1, 0)}
    for room, (x, y) in room_positions.items():
        e = {}
        for direction, (dx, dy) in deltas.items():
            candidate = (x + dx, y + dy)
            if candidate in pos_to_room:
                e[direction] = pos_to_room[candidate]
        exits[room] = e
    start_room = room_list[0]
    return {
        "room_positions": room_positions,
        "pos_to_room": pos_to_room,
        "exits": exits,
        "start_room": start_room,
        "room_list": room_list,
    }

def room_question_decks(grouped: Dict[str, List[Dict]], seed: int) -> Dict[str, List[Dict]]:
    rng = random.Random(seed + 100)
    decks = {}
    for room, questions in grouped.items():
        qlist = [dict(q) for q in questions]
        rng.shuffle(qlist)
        decks[room] = qlist
    return decks

def suggest_crystals_needed(room_count: int) -> int:
    if room_count <= 4:
        return room_count
    return min(6, room_count)

def summarize_results(log: List[Dict]) -> Dict:
    attempts = len([x for x in log if x["result"] in {"correct", "wrong"}])
    correct = len([x for x in log if x["result"] == "correct"])
    wrong = len([x for x in log if x["result"] == "wrong"])
    skipped = len([x for x in log if x["result"] == "skipped"])
    accuracy = round((correct / attempts) * 100) if attempts else 0

    by_room = defaultdict(lambda: {"correct": 0, "wrong": 0, "skipped": 0})
    for row in log:
        room = row["room"]
        by_room[room][row["result"]] += 1

    room_rows = []
    for room, stats in by_room.items():
        att = stats["correct"] + stats["wrong"]
        rate = stats["correct"] / att if att else 0
        room_rows.append((room, stats, rate, att))
    room_rows.sort(key=lambda x: (-x[2], -x[3], x[0]))

    strong = [f"{room} ({stats['correct']}/{att})" for room, stats, _, att in room_rows if att > 0][:3]
    weak_candidates = sorted(room_rows, key=lambda x: (x[2], -x[3], x[0]))
    needs = [f"{room} ({stats['correct']}/{att})" for room, stats, _, att in weak_candidates if att > 0][:3]

    return {
        "attempts": attempts,
        "correct": correct,
        "wrong": wrong,
        "skipped": skipped,
        "accuracy": accuracy,
        "strong": strong,
        "needs": needs,
    }

def ensure_state():
    defaults = {
        "authenticated": False,
        "login_error": "",
        "app_mode": "Plain Quiz",
        "player_name": "",
        "question_count": 10,
        "difficulty": "Standard",
        "pack_source_name": "Demo pack",
        "pack": [],
        "uploaded_pack_name": "",
        "pack_ready": False,
        "access_high_contrast": False,
        "access_large_text": False,
        "story_started": False,
        "story_seed": None,
        "story_map": {},
        "story_rooms": [],
        "story_decks": {},
        "story_current_room": None,
        "story_visited_rooms": set(),
        "story_room_clear": set(),
        "story_wrong_answers": 0,
        "story_wrong_limit": 3,
        "story_crystals_found": 0,
        "story_crystals_needed": 6,
        "story_disabled_exits": {},
        "story_pending_question": None,
        "story_question_active": False,
        "story_log": [],
        "story_question_log": [],
        "story_status": "setup",
        "story_look_count": 0,
        "plain_started": False,
        "plain_deck": [],
        "plain_index": 0,
        "plain_current": None,
        "plain_results": [],
        "plain_filter_room": "All rooms",
        "plain_status": "setup",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

def render_accessibility_controls():
    with st.expander("Accessibility"):
        st.checkbox("High contrast", key="access_high_contrast")
        st.checkbox("Large text", key="access_large_text")
        st.markdown(
            "<div class='small'>The app uses clear buttons, simple movement controls, and short feedback blocks. High contrast and larger text can be toggled here.</div>",
            unsafe_allow_html=True,
        )

def render_login():
    st.markdown(CSS, unsafe_allow_html=True)
    inject_accessibility_css()
    st.title(APP_TITLE)
    render_brand_banner()
    st.caption("Enter the app password to continue.")
    with st.container(border=True):
        st.text_input("Password", type="password", key="login_password")
        if st.button("Enter app"):
            expected = get_secret("APP_PASSWORD", "")
            if not expected:
                st.session_state.login_error = "Add APP_PASSWORD to Streamlit secrets first."
            elif st.session_state.get("login_password", "") == str(expected):
                st.session_state.authenticated = True
                st.session_state.login_error = ""
                st.rerun()
            else:
                st.session_state.login_error = "Incorrect password."
        if st.session_state.get("login_error"):
            st.error(st.session_state.login_error)
    render_accessibility_controls()
    render_brand_footer()

def setup_pack_from_upload(uploaded):
    if uploaded is None:
        return demo_pack(), "Demo pack", None
    pack, error = parse_uploaded_pack(uploaded)
    if error:
        return [], uploaded.name, error
    return pack, uploaded.name, None

def render_pack_preview(pack: List[Dict], source_name: str):
    rooms = ordered_rooms(pack)
    grouped = group_by_room(pack)
    st.markdown(
        f"<div class='small'>Pack: {source_name} · {len(pack)} questions · {len(rooms)} rooms</div>",
        unsafe_allow_html=True,
    )
    room_parts = [f"{room} ({len(grouped[room])})" for room in rooms]
    st.markdown(
        "<div class='small'>Rooms: " + " · ".join(room_parts) + "</div>",
        unsafe_allow_html=True,
    )

def render_setup():
    st.markdown(CSS, unsafe_allow_html=True)
    inject_accessibility_css()
    st.title(APP_TITLE)
    render_brand_banner()
    st.caption("One app, two modes: a plain quiz for straightforward review and a story game that uses room-based subtopics.")
    st.text_input("Player name", key="player_name", placeholder="Doug")
    st.radio("Mode", ["Plain Quiz", "Story Game"], key="app_mode", horizontal=True)

    uploaded = st.file_uploader("Upload CSV or JSON question pack", type=["csv", "json"])
    pack, source_name, error = setup_pack_from_upload(uploaded)
    if error:
        st.error(error)
    else:
        st.session_state.pack = pack
        st.session_state.pack_source_name = source_name
        st.session_state.pack_ready = True
        render_pack_preview(pack, source_name)

    if st.session_state.app_mode == "Plain Quiz":
        rooms = ["All rooms"] + ordered_rooms(pack) if pack else ["All rooms"]
        st.selectbox("Room filter", rooms, key="plain_filter_room")
        st.selectbox("Number of questions", [5, 10, 15, 20, "All"], key="question_count")
        st.markdown(
            "<div class='card'><strong>Plain Quiz</strong><br><span class='soft'>Ask questions one at a time, give immediate feedback, and finish with a clean summary.</span></div>",
            unsafe_allow_html=True,
        )
        if st.button("Start plain quiz", disabled=not bool(pack)):
            start_plain_quiz()
            st.rerun()
    else:
        st.selectbox("Story difficulty", ["Easy", "Standard", "Difficult"], key="difficulty")
        st.markdown(
            "<div class='card'><strong>Story Game</strong><br><span class='soft'>Move room to room with arrow buttons, look around for story beats, and answer room-linked questions to collect crystals and repair the Contrabulator.</span></div>",
            unsafe_allow_html=True,
        )
        if st.button("Start story game", disabled=not bool(pack)):
            start_story_game()
            st.rerun()

    render_accessibility_controls()
    with st.expander("Expected CSV columns"):
        st.code(
            "question,choice_a,choice_b,choice_c,choice_d,correct_answer,explanation,hint,topic,room,tags,difficulty",
            language="text",
        )
        st.markdown(
            "- `room` is the new field that drives the story map.\n"
            "- If `room` is missing, the app will try to infer it from the question text, topic, or tags.\n"
            "- `tags` can still be used for summary and later analytics."
        )
    render_brand_footer()

def filtered_plain_pack(pack: List[Dict]) -> List[Dict]:
    if st.session_state.plain_filter_room == "All rooms":
        return pack[:]
    return [q for q in pack if q["room"] == st.session_state.plain_filter_room]

def start_plain_quiz():
    pack = filtered_plain_pack(st.session_state.pack)
    rng = random.Random(20260402)
    deck = pack[:]
    rng.shuffle(deck)
    count = st.session_state.question_count
    if count != "All":
        deck = deck[: int(count)]
    st.session_state.plain_deck = deck
    st.session_state.plain_index = 0
    st.session_state.plain_results = []
    st.session_state.plain_status = "active"
    st.session_state.plain_started = True
    st.session_state.plain_current = deck[0] if deck else None

def answer_plain(choice_index: int):
    q = st.session_state.plain_current
    if q is None:
        return
    result = "correct" if choice_index == q["a"] else "wrong"
    st.session_state.plain_results.append(
        {
            "question": q["q"],
            "room": q["room"],
            "result": result,
            "answer_text": q["answer_text"],
            "explain": q["explain"],
        }
    )
    st.session_state.plain_index += 1
    if st.session_state.plain_index >= len(st.session_state.plain_deck):
        st.session_state.plain_current = None
        st.session_state.plain_status = "done"
    else:
        st.session_state.plain_current = st.session_state.plain_deck[st.session_state.plain_index]

def start_story_game():
    pack = st.session_state.pack[:]
    rooms = ordered_rooms(pack)
    grouped = group_by_room(pack)
    seed = random.randint(1000, 999999)
    story_map = build_story_map(rooms, seed)
    st.session_state.story_seed = seed
    st.session_state.story_map = story_map
    st.session_state.story_rooms = rooms
    st.session_state.story_decks = room_question_decks(grouped, seed)
    st.session_state.story_current_room = story_map["start_room"]
    st.session_state.story_visited_rooms = {story_map["start_room"]}
    st.session_state.story_room_clear = set()
    st.session_state.story_wrong_answers = 0
    st.session_state.story_wrong_limit = 3
    st.session_state.story_crystals_found = 0
    st.session_state.story_crystals_needed = suggest_crystals_needed(len(rooms))
    st.session_state.story_disabled_exits = {room: set() for room in rooms}
    st.session_state.story_pending_question = None
    st.session_state.story_question_active = False
    st.session_state.story_log = [
        "The Contrabulator is broken.",
        "Each room represents a subtopic from your question pack.",
        "Find enough crystals by answering room-linked questions correctly and the machine will work again.",
    ]
    st.session_state.story_question_log = []
    st.session_state.story_status = "active"
    st.session_state.story_started = True
    st.session_state.story_look_count = 0

def current_story_room() -> str:
    return st.session_state.story_current_room

def room_cleared(room: str) -> bool:
    return room in st.session_state.story_room_clear

def room_has_questions(room: str) -> bool:
    return len(st.session_state.story_decks.get(room, [])) > 0

def random_story_flavor(room: str) -> str:
    rng = random.Random(st.session_state.story_seed + st.session_state.story_look_count + len(room))
    return rng.choice(ROOM_FLAVOR)

def maybe_story_surprise() -> Optional[str]:
    rng = random.Random(st.session_state.story_seed + st.session_state.story_look_count * 11)
    if rng.random() < 0.22:
        return rng.choice(SURPRISES)
    return None

def look_around():
    if st.session_state.story_status != "active":
        return
    room = current_story_room()
    st.session_state.story_look_count += 1
    st.session_state.story_log.append(f"You look around {room}. {random_story_flavor(room)}")
    surprise = maybe_story_surprise()
    if surprise:
        st.session_state.story_log.append(surprise)

    if not room_has_questions(room):
        st.session_state.story_log.append("No question appears here right now. You can keep moving.")
        return

    chance = 0.60 if not room_cleared(room) else 0.35
    rng = random.Random(st.session_state.story_seed + st.session_state.story_look_count * 17 + len(room))
    if rng.random() <= chance:
        q = st.session_state.story_decks[room].pop(0)
        st.session_state.story_pending_question = q
        st.session_state.story_question_active = True
        st.session_state.story_log.append(f"A question appears in {room}.")
    else:
        st.session_state.story_log.append("The room stays quiet for now. No question appears.")

def disable_one_exit(room: str) -> Optional[str]:
    exits = st.session_state.story_map["exits"].get(room, {})
    blocked = st.session_state.story_disabled_exits.get(room, set())
    candidates = [d for d in exits.keys() if d not in blocked]
    if len(candidates) <= 1:
        return None
    rng = random.Random(st.session_state.story_seed + st.session_state.story_wrong_answers * 31 + len(room))
    direction = rng.choice(candidates)
    st.session_state.story_disabled_exits[room].add(direction)
    return direction

def answer_story(choice_index: int):
    q = st.session_state.story_pending_question
    if q is None:
        return
    room = q["room"]
    correct = choice_index == q["a"]
    if correct:
        new_crystal = room not in st.session_state.story_room_clear
        if new_crystal:
            st.session_state.story_room_clear.add(room)
            st.session_state.story_crystals_found += 1
            st.session_state.story_log.append(f"Correct. You earn the crystal from {room}.")
        else:
            st.session_state.story_log.append("Correct. You already found this room's crystal, but the answer still counts in your stats.")
        st.session_state.story_log.append(q["explain"])
        result = "correct"
    else:
        st.session_state.story_wrong_answers += 1
        blocked = disable_one_exit(current_story_room())
        if blocked:
            st.session_state.story_log.append(f"Not quite. The {blocked.upper()} exit is now blocked from this room.")
        else:
            st.session_state.story_log.append("Not quite. No more exits can be removed safely from this room.")
        st.session_state.story_log.append(q["explain"])
        result = "wrong"

    st.session_state.story_question_log.append(
        {"question": q["q"], "room": room, "result": result, "answer_text": q["answer_text"], "explain": q["explain"]}
    )
    st.session_state.story_pending_question = None
    st.session_state.story_question_active = False

    if st.session_state.story_crystals_found >= st.session_state.story_crystals_needed:
        st.session_state.story_status = "won"
        st.session_state.story_log.append("The Contrabulator whirs back to life. You repaired it.")
    elif st.session_state.story_wrong_answers >= st.session_state.story_wrong_limit:
        st.session_state.story_status = "lost"
        st.session_state.story_log.append("There are not enough crystals left to repair the Contrabulator on this run. Restart and try a new path.")

def skip_story_question():
    q = st.session_state.story_pending_question
    if q is None:
        return
    st.session_state.story_question_log.append(
        {"question": q["q"], "room": q["room"], "result": "skipped", "answer_text": q["answer_text"], "explain": q["explain"]}
    )
    st.session_state.story_log.append("You skip the question and move on. No crystal is earned.")
    st.session_state.story_pending_question = None
    st.session_state.story_question_active = False

def move_story(direction: str):
    if st.session_state.story_status != "active":
        return
    room = current_story_room()
    exits = st.session_state.story_map["exits"].get(room, {})
    blocked = st.session_state.story_disabled_exits.get(room, set())
    if direction not in exits:
        st.warning("That direction is not available from here.")
        return
    if direction in blocked:
        st.warning(f"The {direction.upper()} exit is blocked from this room.")
        return
    new_room = exits[direction]
    st.session_state.story_current_room = new_room
    st.session_state.story_visited_rooms.add(new_room)
    st.session_state.story_log.append(f"You move {direction.upper()} into {new_room}.")
    st.session_state.story_question_active = False
    st.session_state.story_pending_question = None

def render_story_map():
    room_positions = st.session_state.story_map["room_positions"]
    grid = [["   " for _ in range(GRID_W)] for _ in range(GRID_H)]
    for room, (x, y) in room_positions.items():
        if room == current_story_room():
            cell = "🟦"
        elif room in st.session_state.story_room_clear:
            cell = "💎"
        elif room in st.session_state.story_visited_rooms:
            cell = "⬜"
        else:
            cell = "⬛"
        grid[y][x] = cell
    text = "\n".join(" ".join(row) for row in grid)
    st.markdown(f"<div class='map-box'><pre>{text}</pre></div>", unsafe_allow_html=True)
    st.markdown(
        "<span class='kicker'>🟦 you</span>"
        "<span class='kicker'>💎 crystal found</span>"
        "<span class='kicker'>⬜ visited room</span>"
        "<span class='kicker'>⬛ unvisited room</span>",
        unsafe_allow_html=True,
    )

def render_story_header():
    room = current_story_room()
    grouped = group_by_room(st.session_state.pack)
    st.markdown(
        f"<div class='card'><strong>{room}</strong><br><span class='soft'>This room draws from {len(grouped.get(room, []))} question(s) in your pack.</span></div>",
        unsafe_allow_html=True,
    )
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Crystals", f"{st.session_state.story_crystals_found}/{st.session_state.story_crystals_needed}")
    c2.metric("Wrong", f"{st.session_state.story_wrong_answers}/{st.session_state.story_wrong_limit}")
    c3.metric("Rooms visited", len(st.session_state.story_visited_rooms))
    c4.metric("Questions used", len(st.session_state.story_question_log))

def render_story_log():
    lines = st.session_state.story_log[-6:]
    st.markdown("<div class='story-log'>", unsafe_allow_html=True)
    for line in lines:
        st.write(line)
    st.markdown("</div>", unsafe_allow_html=True)

def render_story_actions():
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Look Around"):
            look_around()
            st.rerun()
    with c2:
        if st.button("Restart Game"):
            start_story_game()
            st.rerun()
    with c3:
        if st.button("Back to Setup", key="story_back_setup"):
            st.session_state.story_started = False
            st.session_state.story_status = "setup"
            st.rerun()

def render_story_movement():
    room = current_story_room()
    exits = st.session_state.story_map["exits"].get(room, {})
    blocked = st.session_state.story_disabled_exits.get(room, set())

    def label(direction: str) -> str:
        if direction in exits:
            target = exits[direction]
            if direction in blocked:
                return f"{direction.upper()} · blocked"
            return f"{direction.upper()} · {target}"
        return direction.upper()

    r1c1, r1c2 = st.columns(2)
    with r1c1:
        st.button(label("north"), disabled=("north" not in exits or "north" in blocked), on_click=move_story, args=("north",))
    with r1c2:
        st.button(label("east"), disabled=("east" not in exits or "east" in blocked), on_click=move_story, args=("east",))
    r2c1, r2c2 = st.columns(2)
    with r2c1:
        st.button(label("south"), disabled=("south" not in exits or "south" in blocked), on_click=move_story, args=("south",))
    with r2c2:
        st.button(label("west"), disabled=("west" not in exits or "west" in blocked), on_click=move_story, args=("west",))

def render_story_question():
    q = st.session_state.story_pending_question
    if q is None:
        return
    st.markdown("---")
    st.markdown(
        f"<div class='card'><strong>Question from {q['room']}</strong><br><span class='soft'>A correct answer earns the room crystal if you have not already collected it.</span></div>",
        unsafe_allow_html=True,
    )
    st.write(q["q"])
    st.caption(f"Hint available: {q['hint']}")
    with st.form("story_question_form"):
        answer = st.radio("Choose one", q["choices"], index=None)
        submitted = st.form_submit_button("Submit answer")
        if submitted and answer is not None:
            answer_story(q["choices"].index(answer))
            st.rerun()
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Skip Question"):
            skip_story_question()
            st.rerun()
    with c2:
        if st.button("Cancel Question"):
            st.session_state.story_pending_question = None
            st.session_state.story_question_active = False
            st.rerun()

def render_story_summary():
    summary = summarize_results(st.session_state.story_question_log)
    st.markdown("### Story stats")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Attempted", summary["attempts"])
    c2.metric("Accuracy", f"{summary['accuracy']}%")
    c3.metric("Correct", summary["correct"])
    c4.metric("Skipped", summary["skipped"])
    left, right = st.columns(2)
    with left:
        st.markdown("**Strong rooms**")
        if summary["strong"]:
            for line in summary["strong"]:
                st.write(f"- {line}")
        else:
            st.write("- Not enough data yet.")
    with right:
        st.markdown("**Needs review**")
        if summary["needs"]:
            for line in summary["needs"]:
                st.write(f"- {line}")
        else:
            st.write("- Nothing stands out yet.")

def render_story_game():
    st.markdown(CSS, unsafe_allow_html=True)
    inject_accessibility_css()
    st.title(APP_TITLE)
    render_brand_banner()
    st.caption("Story mode: move through topic rooms, look around, answer random room-linked questions, and repair the Contrabulator.")
    render_story_header()
    render_story_map()
    render_story_log()
    render_story_actions()
    if st.session_state.story_status == "active":
        if st.session_state.story_question_active:
            render_story_question()
        else:
            st.subheader("Move")
            render_story_movement()
    elif st.session_state.story_status == "won":
        st.success("You repaired the Contrabulator. Nicely done.")
        render_story_summary()
    elif st.session_state.story_status == "lost":
        st.info("This run ran out of viable crystals. Restart and try again.")
        render_story_summary()

    with st.expander("Run details"):
        st.write(f"Pack: {st.session_state.pack_source_name}")
        st.write(f"Rooms: {', '.join(st.session_state.story_rooms)}")
        st.write(f"Seed: {st.session_state.story_seed}")
    render_brand_footer()

def render_plain_quiz():
    st.markdown(CSS, unsafe_allow_html=True)
    inject_accessibility_css()
    st.title(APP_TITLE)
    render_brand_banner()
    st.caption("Plain quiz mode: simple review with immediate feedback and a clean summary.")
    q = st.session_state.plain_current
    total = len(st.session_state.plain_deck)
    idx = st.session_state.plain_index + 1 if q else total
    if st.session_state.plain_status == "active" and q is not None:
        st.markdown(
            f"<div class='card'><strong>Question {idx} of {total}</strong><br><span class='soft'>Room: {q['room']} · Pack: {st.session_state.pack_source_name}</span></div>",
            unsafe_allow_html=True,
        )
        st.write(q["q"])
        with st.form("plain_quiz_form"):
            answer = st.radio("Choose one", q["choices"], index=None)
            submitted = st.form_submit_button("Submit answer")
            if submitted and answer is not None:
                answer_plain(q["choices"].index(answer))
                st.rerun()
        c1, c2 = st.columns(2)
        with c1:
            st.info(f"Hint: {q['hint']}")
        with c2:
            if st.button("Back to Setup", key="plain_back_setup_active"):
                st.session_state.plain_started = False
                st.session_state.plain_status = "setup"
                st.rerun()
    else:
        summary = summarize_results(st.session_state.plain_results)
        st.success("Quiz complete.")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Attempted", summary["attempts"])
        c2.metric("Accuracy", f"{summary['accuracy']}%")
        c3.metric("Correct", summary["correct"])
        c4.metric("Wrong", summary["wrong"])
        left, right = st.columns(2)
        with left:
            st.markdown("**Strong rooms**")
            if summary["strong"]:
                for line in summary["strong"]:
                    st.write(f"- {line}")
            else:
                st.write("- Not enough data.")
        with right:
            st.markdown("**Needs review**")
            if summary["needs"]:
                for line in summary["needs"]:
                    st.write(f"- {line}")
            else:
                st.write("- Nothing stands out yet.")

        if st.session_state.plain_results:
            st.markdown("### Response log")
            for row in st.session_state.plain_results:
                icon = "✅" if row["result"] == "correct" else "❌"
                st.write(f"{icon} **{row['room']}** — {row['question']}")
                st.write(f"Answer: {row['answer_text']}")
                st.write(row["explain"])

        c1, c2 = st.columns(2)
        with c1:
            if st.button("Start another plain quiz"):
                start_plain_quiz()
                st.rerun()
        with c2:
            if st.button("Back to Setup", key="plain_back_setup_done"):
                st.session_state.plain_started = False
                st.session_state.plain_status = "setup"
                st.rerun()
    render_brand_footer()

def main():
    ensure_state()
    if not st.session_state.authenticated:
        render_login()
        return

    if st.session_state.app_mode == "Story Game" and st.session_state.story_started:
        render_story_game()
        return
    if st.session_state.app_mode == "Plain Quiz" and st.session_state.plain_started:
        render_plain_quiz()
        return

    render_setup()

if __name__ == "__main__":
    main()
