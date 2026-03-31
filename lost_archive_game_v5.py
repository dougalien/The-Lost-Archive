import csv
import io
import json
import random
from typing import Dict, List, Optional, Tuple

import streamlit as st

try:
    from openai import OpenAI
except Exception:
    OpenAI = None
import streamlit.components.v1 as components

st.set_page_config(page_title="The Lost Archive", page_icon="📚", layout="centered")

SIZE = 5
START = (0, 0)
VAULT = (SIZE - 1, SIZE - 1)
DIRECTIONS = {
    "north": (0, -1),
    "south": (0, 1),
    "west": (-1, 0),
    "east": (1, 0),
}

CSS = """
<style>
html, body, [class*="css"]  {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}
.block-container {
    max-width: 760px;
    padding-top: 0.8rem;
    padding-bottom: 2rem;
}
.stButton > button, .stDownloadButton > button {
    width: 100%;
    border-radius: 14px;
    padding: 0.62rem 0.72rem;
    border: 1px solid #d7e1ea;
}
.card {
    background: linear-gradient(180deg, #fbfdff 0%, #eef5ff 100%);
    border: 1px solid #d9e4f2;
    border-radius: 18px;
    padding: 0.92rem 1rem;
    margin-bottom: 0.75rem;
}
.soft {
    color: #5f6b78;
    font-size: 0.96rem;
}
.titleish {
    font-size: 1.25rem;
    font-weight: 700;
    margin-bottom: 0.2rem;
}
.story-log {
    background: #fbfcfe;
    border: 1px solid #e5ebf4;
    border-radius: 16px;
    padding: 0.8rem 0.9rem;
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
    font-size: 1.18rem;
    line-height: 1.42;
    text-align: center;
}
.small {
    color: #627181;
    font-size: 0.88rem;
}
.kicker {
    display: inline-block;
    padding: 0.2rem 0.52rem;
    border-radius: 999px;
    background: #edf3fb;
    border: 1px solid #dce6f2;
    margin-right: 0.3rem;
    margin-bottom: 0.25rem;
    font-size: 0.83rem;
}
.section-gap {
    margin-top: 0.5rem;
}
</style>
"""


STORY_SHELLS = [
    {
        "name": "Archive Drift",
        "setting_name": "The Lost Archive",
        "titles": ["The Lost Archive", "The Quiet Index", "The Luminous Stacks", "The Wandering Archive"],
        "subtitle": "A changing maze of shelves, side rooms, and study chambers.",
        "token_name": "Insight",
        "seal_name": "Archive Seal",
        "vault_name": "Heart Vault",
        "start_name": "Entry Foyer",
        "room_pool": [
            "Lantern Shelf", "Atlas Court", "Quiet Annex", "Signal Room", "North Stack", "Study Bay", "Index Hall",
            "Side Archive", "Map Desk", "Research Walk", "Margin Room", "Note Court", "Crossfile Nook", "Open Stacks",
            "Catalog Wing", "Reader's Bay", "Compass Shelf", "Hidden Alcove", "Focus Hall", "Bridge Desk", "Memory Court",
            "Transit Shelf", "Field Index", "Pattern Nook", "Scholar's Walk",
        ],
        "descriptors": [
            "The archive seems to rearrange itself around the questions you brought in.",
            "A calm glow returns as if the room approves of steady thinking.",
            "The shelves here feel less fixed than remembered.",
        ],
        "intro_templates": [
            "The archive has reshaped itself around {subject}. This run will not look quite like the last one.",
            "Rooms, labels, and side paths are drifting into a new order around {subject}.",
            "The building has taken your {subject} material and built a fresh route from it.",
        ],
        "milestones": [
            "A side index brightens. The archive is adapting to this particular run.",
            "A corridor splits where it did not before. The layout is learning from your progress.",
            "The deeper stacks feel newly arranged, as if this material has its own architecture.",
            "A low tone moves through the walls. The final chamber has recognized your path.",
        ],
        "completion_templates": [
            "The vault opens and the archive settles into a shape built from this run's material.",
            "The route resolves. What looked like wandering now feels deliberate and complete.",
        ],
    },
    {
        "name": "Field Route",
        "setting_name": "The Field Route",
        "titles": ["The Field Route", "The Drift Map", "The Learning Traverse", "The Survey Path"],
        "subtitle": "A route of camps, markers, and stations that shifts with each run.",
        "token_name": "Field Marks",
        "seal_name": "Survey Seal",
        "vault_name": "Summit Gate",
        "start_name": "Base Camp",
        "room_pool": [
            "North Marker", "Dry Gulch", "Signal Camp", "Waypoint Desk", "Ridge Station", "Observation Bay", "Transect Hall",
            "Compass Point", "Trail Nook", "Map Shelf", "Survey Court", "Cairn Room", "Sample Walk", "Moraine Turn",
            "Plateau Desk", "Lantern Camp", "Switchback Hall", "Guidepost Bay", "Delta Marker", "Quartz Stop", "Shaded Spur",
            "Field Annex", "Traverse Room", "Bench Ledge", "Summit Shelf",
        ],
        "descriptors": [
            "The route ahead feels hand-drawn, then revised, then hand-drawn again.",
            "A trail marker flickers as if it just chose this position for today's run.",
            "The path here feels earned rather than given.",
        ],
        "intro_templates": [
            "Today's route has formed around {subject}. The path looks familiar, but not repeated.",
            "A new traverse has been drawn from your {subject} material. The camps and markers have shifted.",
            "The field route has rebuilt itself for {subject}, using a different sequence of stops this time.",
        ],
        "milestones": [
            "A fresh marker appears on the route. Your progress is changing the map.",
            "Side trails now connect in a cleaner pattern than before.",
            "The route begins to feel coherent, like a field sketch turning into a real map.",
            "The final marker brightens. The end of the traverse is close.",
        ],
        "completion_templates": [
            "The Summit Gate opens and the whole route reads like one finished expedition.",
            "The map settles. This run becomes one complete traverse instead of scattered stops.",
        ],
    },
    {
        "name": "Studio Circuit",
        "setting_name": "The Studio Circuit",
        "titles": ["The Studio Circuit", "The Pattern District", "The Maker Route", "The Design Passage"],
        "subtitle": "A district of rooms, benches, and workspaces that remixes itself each run.",
        "token_name": "Sparks",
        "seal_name": "Circuit Seal",
        "vault_name": "Core Studio",
        "start_name": "Front Desk",
        "room_pool": [
            "Sketch Bay", "Maker Court", "Signal Bench", "Pattern Room", "Draft Hall", "Studio Shelf", "Quiet Bench",
            "Color Nook", "Form Desk", "Assembly Walk", "Light Court", "Workshop Wing", "Gesture Bay", "Plan Table",
            "Design Hall", "Warmup Room", "Model Court", "Idea Shelf", "Layout Desk", "Print Turn", "Surface Bay",
            "Open Bench", "Contrast Hall", "Measure Room", "Project Court",
        ],
        "descriptors": [
            "The room hums with that good feeling of work beginning to click.",
            "Something here feels rearranged for a new set of problems.",
            "The circuit seems designed to keep momentum going.",
        ],
        "intro_templates": [
            "The studio circuit has rebuilt itself around {subject}. This run gets a fresh layout and tone.",
            "A new maker route has formed from your {subject} pack. The benches and side rooms are not the same as last time.",
            "The district has taken today's material and remixed the route into a new working sequence.",
        ],
        "milestones": [
            "A side bench lights up. The circuit seems to reward rhythm as much as accuracy.",
            "A new corridor opens between workspaces that were separate before.",
            "The rooms now feel linked, as if the whole district is collaborating.",
            "The Core Studio begins to warm. The run is nearing its finish.",
        ],
        "completion_templates": [
            "The Core Studio opens and the circuit locks into one strong, coherent run.",
            "The district settles into a finished pattern. This route is complete.",
        ],
    },
    {
        "name": "Signal Campus",
        "setting_name": "The Signal Campus",
        "titles": ["The Signal Campus", "The Learning Grid", "The Quiet Network", "The Neighbor Signal"],
        "subtitle": "A campus-like network of rooms and hubs that changes shape each run.",
        "token_name": "Pulses",
        "seal_name": "Signal Seal",
        "vault_name": "Central Hub",
        "start_name": "Link Hall",
        "room_pool": [
            "North Hub", "Relay Room", "Pattern Court", "Guide Hall", "Signal Shelf", "Junction Desk", "Campus Bay",
            "Bridge Room", "Study Link", "Quiet Court", "Shared Bench", "Transit Hall", "Beacon Nook", "Route Desk",
            "Open Link", "Pulse Bay", "Coordination Wing", "Neighbor Hall", "Network Desk", "Logic Court", "Path Relay",
            "Support Room", "Soft Signal", "Circuit Walk", "Central Link",
        ],
        "descriptors": [
            "The network feels friendlier once a little progress has been earned.",
            "A quiet signal passes through the room like a status light coming back online.",
            "This part of the campus seems newly connected.",
        ],
        "intro_templates": [
            "The campus has remapped itself around {subject}. The network is fresh for this run.",
            "A new signal route has formed from your {subject} material. The hubs are not in yesterday's order.",
            "The grid has reconfigured itself around {subject}, giving this run a different shape and tone.",
        ],
        "milestones": [
            "A new relay comes online. The network is widening.",
            "Several dead ends now connect, as if the campus learned a better route from you.",
            "The grid is beginning to feel collaborative rather than scattered.",
            "The Central Hub responds. The run is close to completion.",
        ],
        "completion_templates": [
            "The Central Hub opens and the whole network stabilizes around this run's material.",
            "The campus settles into one connected system. This route is complete.",
        ],
    },
]


def infer_subject_label(topic: str, pack_name: str, pack: List[Dict]) -> str:
    if pack_name and pack_name not in {"", topic}:
        return pack_name.rsplit('.', 1)[0]
    sources = [q.get("source", "") for q in pack[:6] if q.get("source")]
    if sources:
        return sources[0]
    return topic


def choose_shell(seed: int, topic: str, pack: List[Dict]) -> Dict:
    rng = random.Random(seed + 700)
    tags = {tag.lower() for q in pack for tag in q.get("tags", [])}
    if topic == "Art" or {"painting", "design", "drawing", "portrait", "composition", "color theory"} & tags:
        preferred = [s for s in STORY_SHELLS if s["name"] == "Studio Circuit"]
    elif topic == "Dynamic Earth" or {"rocks", "tectonics", "igneous", "fossils", "minerals"} & tags:
        preferred = [s for s in STORY_SHELLS if s["name"] == "Field Route"]
    elif {"network", "signals", "support"} & tags:
        preferred = [s for s in STORY_SHELLS if s["name"] == "Signal Campus"]
    else:
        preferred = [s for s in STORY_SHELLS if s["name"] == "Archive Drift"]
    if rng.random() < 0.35:
        return rng.choice(STORY_SHELLS)
    return preferred[0]


def safe_json_extract(text: str) -> Optional[Dict]:
    text = text.strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except Exception:
        pass
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end+1])
        except Exception:
            return None
    return None


def build_free_run_packet(seed: int, topic: str, pack_name: str, pack: List[Dict], username: str) -> Dict:
    rng = random.Random(seed + 500)
    shell = choose_shell(seed, topic, pack)
    subject = infer_subject_label(topic, pack_name, pack)
    room_names = shell["room_pool"][:]
    rng.shuffle(room_names)
    intro = [
        rng.choice(shell["intro_templates"]).format(subject=subject),
        shell["subtitle"],
        f"Earn {difficulty_rules(st.session_state.difficulty)['seals_needed']} {shell['seal_name']}s to open the {shell['vault_name']}." if difficulty_rules(st.session_state.difficulty)['seals_needed'] != 1 else f"Earn 1 {shell['seal_name']} to open the {shell['vault_name']}."
    ]
    event_flavor = {
        "lumen_block": f"You find a rare helper node. Gain +3 {shell['token_name']} and +1 safeguard.",
        "token_cache": f"You find a small stash. Gain +2 {shell['token_name']}.",
        "secret_passage": f"A hidden route opens. Your next unrevealed room is free and still earns a {shell['seal_name']}.",
        "seal_fragment": f"You recover a partial marker. It counts as +1 {shell['seal_name']}.",
        "lights_out": "The controls dim and the route goes fuzzy for a moment.",
    }
    return {
        "title": rng.choice(shell["titles"]),
        "setting_name": shell["setting_name"],
        "subtitle": shell["subtitle"],
        "token_name": shell["token_name"],
        "seal_name": shell["seal_name"],
        "vault_name": shell["vault_name"],
        "start_name": shell["start_name"],
        "intro": intro,
        "milestones": shell["milestones"][:4],
        "room_names": room_names[: SIZE * SIZE],
        "room_descriptors": shell["descriptors"],
        "event_flavor": event_flavor,
        "completion_text": rng.choice(shell["completion_templates"]),
        "mode": "free-template",
    }


def generate_ai_run_packet(seed: int, topic: str, pack_name: str, pack: List[Dict], username: str) -> Optional[Dict]:
    api_key = st.secrets.get("OPENAI_API_KEY", "")
    if not api_key or OpenAI is None:
        return None

    tags = []
    for q in pack[:15]:
        for tag in q.get("tags", []):
            if tag not in tags:
                tags.append(tag)
    sources = []
    for q in pack[:10]:
        src = q.get("source")
        if src and src not in sources:
            sources.append(src)
    subject = infer_subject_label(topic, pack_name, pack)
    model = st.secrets.get("RUN_PACKET_MODEL", "gpt-5-mini")
    prompt = {
        "topic": topic,
        "pack_name": pack_name,
        "subject": subject,
        "difficulty": st.session_state.difficulty,
        "player_name": username or "Player",
        "tags": tags[:12],
        "sources": sources[:5],
        "question_examples": [q["q"] for q in pack[:4]],
        "requirements": {
            "make_one_run_feel_fresh": True,
            "avoid_war_zombies_apocalypse_spirituality": True,
            "uplifting": True,
            "no_correctness_logic": True,
            "room_name_count": SIZE * SIZE,
            "milestone_count": 4,
            "intro_count": 3,
        },
    }
    system = (
        "You design lightweight replayable run skins for an educational puzzle game. "
        "Return compact JSON only. Do not include markdown fences. "
        "Keep text warm, concise, and replay-friendly. Avoid doom, war, battle, or mystical language."
    )
    user = (
        "Generate a run packet JSON with keys: title, setting_name, subtitle, token_name, seal_name, vault_name, "
        "start_name, intro, milestones, room_names, room_descriptors, event_flavor, completion_text. "
        "intro must have 3 short strings. milestones must have 4 short strings. room_names must have exactly 25 short unique names. "
        "room_descriptors must have 3 short strings. event_flavor must be an object with keys lumen_block, token_cache, secret_passage, seal_fragment, lights_out. "
        "Keep everything concise and school-friendly. Base the style on this data: " + json.dumps(prompt)
    )
    try:
        client = OpenAI(api_key=api_key)
        resp = client.responses.create(
            model=model,
            input=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_output_tokens=900,
            temperature=0.9,
        )
        text = getattr(resp, "output_text", "") or ""
        data = safe_json_extract(text)
        if not isinstance(data, dict):
            return None
        required_keys = {"title", "setting_name", "subtitle", "token_name", "seal_name", "vault_name", "start_name", "intro", "milestones", "room_names", "room_descriptors", "event_flavor", "completion_text"}
        if not required_keys.issubset(data.keys()):
            return None
        if len(data.get("room_names", [])) < SIZE * SIZE:
            return None
        data["mode"] = "pro-ai"
        return data
    except Exception:
        return None


def build_run_packet(seed: int, topic: str, pack_name: str, pack: List[Dict], story_mode: str, username: str) -> Dict:
    free_packet = build_free_run_packet(seed, topic, pack_name, pack, username)
    if story_mode == "Pro AI run packet":
        ai_packet = generate_ai_run_packet(seed, topic, pack_name, pack, username)
        if ai_packet:
            return ai_packet
        free_packet["mode"] = "free-template-fallback"
    return free_packet


def packet_value(key: str, default=None):
    packet = st.session_state.get("run_packet") or {}
    return packet.get(key, default)


def packet_list(key: str, default: List[str]) -> List[str]:
    val = packet_value(key, default)
    return val if isinstance(val, list) and val else default


def get_game_title() -> str:
    return str(packet_value("title", "The Lost Archive"))


def get_token_name() -> str:
    return str(packet_value("token_name", "Insight"))


def get_seal_name() -> str:
    return str(packet_value("seal_name", "Archive Seal"))


def get_vault_name() -> str:
    return str(packet_value("vault_name", "Heart Vault"))


def get_start_name() -> str:
    return str(packet_value("start_name", "Entry Foyer"))


def get_story_intro(default_key: str) -> List[str]:
    return packet_list("intro", TOPIC_INTRO[default_key])


def get_story_milestones(default_key: str) -> List[str]:
    return packet_list("milestones", TOPIC_MILESTONES[default_key])


def get_room_pool(topic: str) -> List[str]:
    return packet_list("room_names", ROOM_NAMES.get(topic, ROOM_NAMES["Custom"]))


def get_room_descriptors() -> List[str]:
    return packet_list("room_descriptors", ROOM_DESCRIPTORS)

def qd(question: str, choices: List[str], answer: int, hint: str, explain: str, tags: List[str], source: str) -> Dict:
    return {
        "q": question,
        "choices": choices,
        "a": answer,
        "hint": hint,
        "explain": explain,
        "tags": tags,
        "source": source,
    }


QUESTION_BANKS = {
    "Dynamic Earth": [
        qd("Which rock type forms when magma or lava cools?", ["Igneous", "Sedimentary", "Metamorphic", "Organic"], 0, "Think fire and molten rock.", "Igneous rocks form from cooled magma or lava.", ["rocks", "igneous"], "Dynamic Earth"),
        qd("Which rock is a common intrusive igneous rock?", ["Granite", "Sandstone", "Limestone", "Slate"], 0, "It cools slowly underground and often has visible crystals.", "Granite is a classic intrusive igneous rock.", ["igneous", "minerals"], "Dynamic Earth"),
        qd("Metamorphic rocks are most often formed by what?", ["Heat and pressure", "Wind alone", "Freezing rain", "Plant decay"], 0, "They change without fully melting.", "Metamorphic rocks form when existing rocks are altered by heat and pressure.", ["metamorphic", "rocks"], "Dynamic Earth"),
        qd("What is the softest mineral on the Mohs hardness scale?", ["Gypsum", "Quartz", "Talc", "Calcite"], 2, "It is softer than a fingernail.", "Talc is the softest mineral on the Mohs scale.", ["minerals", "hardness"], "Dynamic Earth"),
        qd("Which sedimentary rock commonly reacts with dilute acid?", ["Limestone", "Shale", "Conglomerate", "Sandstone"], 0, "It often contains calcite.", "Limestone commonly fizzes because it often contains calcite.", ["sedimentary", "minerals"], "Dynamic Earth"),
        qd("What is a fossil?", ["A melted crystal", "Preserved remains or traces of life", "A type of magma", "A weather instrument"], 1, "It connects biology and geology.", "Fossils are preserved remains or traces of ancient organisms.", ["fossils", "sedimentary"], "Dynamic Earth"),
        qd("What is the name for a fracture along which movement has occurred?", ["Joint", "Fault", "Fold", "Vein"], 1, "It can offset rock layers.", "A fault is a fracture where movement has occurred.", ["tectonics", "faults"], "Dynamic Earth"),
        qd("Magma that reaches Earth’s surface is called what?", ["Ore", "Ash", "Lava", "Slurry"], 2, "Think volcano.", "Magma at the surface is called lava.", ["igneous", "volcanoes"], "Dynamic Earth"),
        qd("Which process breaks rock down in place?", ["Erosion", "Weathering", "Deposition", "Lithification"], 1, "Transport comes later.", "Weathering breaks rock down in place; erosion transports it.", ["weathering", "surface processes"], "Dynamic Earth"),
        qd("Which mineral is harder: quartz or calcite?", ["Calcite", "Quartz", "They are equal", "It depends on color"], 1, "Quartz is Mohs 7.", "Quartz is harder than calcite.", ["minerals", "hardness"], "Dynamic Earth"),
        qd("Which large landmass name refers to an ancient supercontinent?", ["Laurasia", "Pangaea", "Gondwana", "Panthalassa"], 1, "It once joined many continents together.", "Pangaea is the famous ancient supercontinent.", ["tectonics", "plate tectonics"], "Dynamic Earth"),
        qd("Basalt is especially common in which setting?", ["Oceanic crust", "Coal swamps", "Deserts only", "Glacier ice"], 0, "Think seafloor volcanic rock.", "Basalt is common in oceanic crust.", ["igneous", "plate tectonics"], "Dynamic Earth"),
    ],
    "Art": [
        qd("Which term describes colors opposite each other on the color wheel?", ["Analogous", "Complementary", "Monochrome", "Neutral"], 1, "These pairs create strong contrast.", "Complementary colors sit opposite each other on the color wheel.", ["color theory", "design"], "Art"),
        qd("Which medium is known for being transparent and water-based?", ["Watercolor", "Marble", "Pastel stone", "Bronze"], 0, "It often uses paper and washes.", "Watercolor is a transparent water-based painting medium.", ["media", "painting"], "Art"),
        qd("A sculpture is usually what?", ["Only black and white", "Three-dimensional", "Always painted", "A sound recording"], 1, "You can walk around it.", "Sculpture is generally three-dimensional.", ["sculpture", "form"], "Art"),
        qd("What art concept helps create the illusion of depth on a flat surface?", ["Perspective", "Symmetry", "Repetition", "Framing"], 0, "Parallel lines seem to meet in the distance.", "Perspective is used to create the illusion of depth.", ["perspective", "drawing"], "Art"),
        qd("Which drawing material is especially useful for quick value studies?", ["Charcoal", "Glass", "Clay", "Inkjet"], 0, "It smudges easily.", "Charcoal is often used for quick sketches and value studies.", ["drawing", "value"], "Art"),
        qd("In art, what does value refer to?", ["Price", "Lightness or darkness", "Frame size", "Museum age"], 1, "Think shadow versus highlight.", "Value refers to how light or dark something appears.", ["value", "drawing"], "Art"),
        qd("A collage is made by doing what?", ["Casting metal", "Arranging and attaching pieces", "Mixing pigments only", "Photographing motion"], 1, "Cut paper is a classic material.", "A collage is created by assembling attached pieces into a composition.", ["composition", "mixed media"], "Art"),
        qd("In basic perspective drawing, the horizon line is usually at what level?", ["The subject’s knee", "The viewer’s eye level", "The bottom of the page", "The top of the frame"], 1, "It matches how high you are looking from.", "The horizon line usually corresponds to the viewer’s eye level.", ["perspective", "drawing"], "Art"),
        qd("What is negative space?", ["The darkest shadow", "The area around and between subjects", "Broken canvas", "A sculpture mold"], 1, "It is not the object itself.", "Negative space is the area around and between the main subjects.", ["composition", "design"], "Art"),
        qd("Which medium generally dries faster: acrylic or oil paint?", ["Oil", "Acrylic", "They dry equally fast", "Neither dries"], 1, "One is popular partly because it dries quickly.", "Acrylic paint generally dries much faster than oil paint.", ["media", "painting"], "Art"),
        qd("A portrait most often focuses on what?", ["A landscape", "A building plan", "A person", "A weather pattern"], 2, "Face and expression matter here.", "A portrait focuses mainly on a person.", ["portrait", "subject matter"], "Art"),
        qd("Texture in art describes what?", ["Only color choice", "Surface quality, actual or implied", "The price tag", "The frame material"], 1, "It can look rough even when it is smooth.", "Texture refers to the surface quality of a work, whether real or implied.", ["texture", "design"], "Art"),
    ],
    "General Science": [
        qd("Photosynthesis helps plants do what?", ["Make sugar using light", "Create gravity", "Melt minerals", "Stop evaporation"], 0, "It stores energy from sunlight.", "Photosynthesis uses light energy to help plants make sugar.", ["biology", "energy"], "General Science"),
        qd("Evaporation is the change from what to what?", ["Gas to liquid", "Liquid to gas", "Solid to liquid", "Gas to solid"], 1, "Think of a puddle disappearing.", "Evaporation is the change from liquid to gas.", ["matter", "water"], "General Science"),
        qd("Why do planets orbit stars?", ["Magnet paint", "Gravity", "Wind pressure", "Moonlight"], 1, "It is the same force that keeps us on Earth.", "Gravity keeps planets in orbit around stars.", ["space", "forces"], "General Science"),
        qd("Which feature is typical of mammals?", ["They all lay eggs", "They have hair or fur", "They breathe through gills", "They are all tiny"], 1, "Think dogs, whales, and people.", "Mammals are characterized in part by hair or fur.", ["biology", "animals"], "General Science"),
        qd("An atom is best described as what?", ["A whole ecosystem", "A unit of an element", "A type of star", "A rock texture"], 1, "Elements are made of these.", "An atom is the basic unit of an element.", ["chemistry", "matter"], "General Science"),
        qd("What does a conductor do in electricity?", ["Blocks all current", "Allows current to flow easily", "Creates matter", "Stores fossils"], 1, "Metals often do this well.", "A conductor allows electrical current to flow relatively easily.", ["electricity", "physics"], "General Science"),
        qd("What mainly causes the phases of the Moon?", ["Earth’s shadow every week", "Our changing view of the lit half", "Cloud cover", "Ocean tides"], 1, "The Moon is always half lit by the Sun.", "Moon phases come from our changing view of the sunlit half of the Moon.", ["space", "moon"], "General Science"),
        qd("What does DNA carry?", ["Wind speed", "Genetic information", "Magnetic poles", "Water pressure"], 1, "It is central to heredity.", "DNA carries genetic information.", ["biology", "genetics"], "General Science"),
        qd("At sea level, water boils at about what temperature in Celsius?", ["0", "50", "100", "2120"], 2, "It is the same number used in many basic science labs.", "At sea level, water boils at about 100°C.", ["matter", "temperature"], "General Science"),
        qd("In a food chain, plants are usually what?", ["Consumers", "Producers", "Predators", "Decomposers only"], 1, "They make their own food.", "Plants are producers because they make their own food.", ["ecology", "biology"], "General Science"),
        qd("Which body system helps move oxygen around the body?", ["Circulatory system", "Skeletal system", "Digestive system", "Nervous system only"], 0, "Think heart and blood vessels.", "The circulatory system moves oxygen and nutrients through the body.", ["biology", "human body"], "General Science"),
        qd("Speed is distance divided by what?", ["Mass", "Area", "Time", "Temperature"], 2, "How long something takes matters here.", "Speed equals distance divided by time.", ["physics", "motion"], "General Science"),
    ],
}

BRAIN_BANK = [
    qd("Archive code: which number completes the pattern 2, 4, 8, 16, ?", ["18", "24", "32", "34"], 2, "Each term doubles.", "The pattern doubles each time, so the next number is 32.", ["patterns", "math"], "Brain Mix"),
    qd("A shelf lock needs the missing value: 3, 6, 9, ?, 15", ["10", "11", "12", "13"], 2, "Add the same amount each time.", "The pattern increases by 3, so the missing number is 12.", ["patterns", "math"], "Brain Mix"),
    qd("Which choice balances the code best: 7 + 5 = ?", ["11", "12", "13", "14"], 1, "Combine the two totals.", "7 + 5 = 12.", ["math", "fluency"], "Brain Mix"),
    qd("A route marker reads 20, 17, 14, 11, ?", ["10", "9", "8", "7"], 2, "Subtract the same amount each step.", "The pattern decreases by 3, so the next number is 8.", ["patterns", "math"], "Brain Mix"),
    qd("Which pair makes 10?", ["6 and 5", "7 and 2", "4 and 6", "3 and 8"], 2, "Look for the exact total.", "4 and 6 add to 10.", ["math", "fluency"], "Brain Mix"),
]

TOPIC_INTRO = {
    "Dynamic Earth": [
        "The Lost Archive dims and brightens in pulses, as if it remembers your class but not the order.",
        "Each chamber asks for one good answer before it trusts you with another step.",
        "Collect enough Archive Seals and the Heart Vault will reopen.",
    ],
    "Art": [
        "Frames, notes, and study tables sit in a quiet half-light across the archive.",
        "Each chamber must be earned, one clear answer at a time.",
        "Collect enough Archive Seals and the Heart Vault will reopen.",
    ],
    "General Science": [
        "The archive hums with old lab tags, diagrams, and locked side rooms.",
        "Each good answer reconnects one more path of learning.",
        "Collect enough Archive Seals and the Heart Vault will reopen.",
    ],
    "Mixed": [
        "Shelves, charts, and sketches have all been mixed together into one wandering maze.",
        "The archive wants breadth, attention, and steady thinking.",
        "Collect enough Archive Seals and the Heart Vault will reopen.",
    ],
    "Custom": [
        "A new pack of questions has been loaded into the archive.",
        "The rooms are ready. The route will now be shaped by the material you brought in.",
        "Collect enough Archive Seals and the Heart Vault will reopen.",
    ],
}

TOPIC_MILESTONES = {
    "Dynamic Earth": [
        "A side drawer clicks open. The archive seems to reward patient observation more than speed.",
        "A wall map brightens with coastlines, faults, and former seas.",
        "The deeper stacks begin to feel more coherent. You are turning facts back into pathways.",
        "A low vibration moves through the floor. The Heart Vault is beginning to wake.",
    ],
    "Art": [
        "A note appears under glass: seeing carefully is already a kind of understanding.",
        "A hidden panel reveals studies of color, structure, and intention.",
        "The rooms are growing brighter, as if composition itself is coming back online.",
        "The final wing begins to hum. The Heart Vault is beginning to wake.",
    ],
    "General Science": [
        "A narrow shelf slides out. Curiosity and evidence seem to be the archive’s preferred language.",
        "New lights come on around diagrams, models, and tagged drawers.",
        "The archive feels steadier now, as if the systems are starting to trust one another again.",
        "The final wing begins to hum. The Heart Vault is beginning to wake.",
    ],
    "Mixed": [
        "A note appears: every field begins when someone notices something worth asking.",
        "The shelves now mix diagrams, pigments, minerals, and pattern cards without losing their order.",
        "The archive seems pleased by range as much as precision.",
        "The final wing begins to hum. The Heart Vault is beginning to wake.",
    ],
    "Custom": [
        "A side drawer opens for your own material. The archive accepts new disciplines easily.",
        "The rooms now feel tailored to this run, as if the building learned your pack on the fly.",
        "The archive is clearly adapting to your content. Its structure holds.",
        "The final wing begins to hum. The Heart Vault is beginning to wake.",
    ],
}

ROOM_NAMES = {
    "Dynamic Earth": [
        "Basalt Shelf", "Fossil Gallery", "Fault Walk", "Crystal Bay", "Delta Case",
        "Strata Court", "Limestone Nook", "Magma Study", "Glacier Desk", "Core Ladder",
        "Rift Room", "Quartz Alcove", "Shale Landing", "Outcrop Hall", "Tectonic Stacks",
        "River Table", "Mineral Annex", "Canyon File", "Dune Wing", "Seafloor Bay",
        "Weathering Court", "Plate Junction", "Basin Stack", "Sediment Room", "Mantle Desk",
    ],
    "Art": [
        "Pigment Hall", "Canvas Walk", "Charcoal Desk", "Portrait Wing", "Texture Room",
        "Sculpture Nook", "Palette Court", "Studio Shelf", "Value Gallery", "Collage Bay",
        "Perspective Hall", "Brush Alcove", "Museum Stacks", "Light Study", "Print Room",
        "Sketch Annex", "Ceramic Court", "Design File", "Gesture Bay", "Form Room",
        "Contrast Hall", "Pattern Desk", "Line Study", "Museum Walk", "Surface Court",
    ],
    "General Science": [
        "Lab Annex", "Orbit Hall", "Cell Shelf", "Energy Room", "Wave Desk",
        "Matter Court", "Field Notes", "Gravity Walk", "Signal Bay", "Circuit Nook",
        "Eco Wing", "Motion Hall", "Water Desk", "Light Lab", "Pattern Shelf",
        "System Annex", "Species File", "Data Court", "Molecule Bay", "Forces Room",
        "Cycle Desk", "Sky Hall", "Pulse Nook", "Model Court", "Observation File",
    ],
    "Mixed": [
        "North Stack", "Quiet Annex", "Pattern Bay", "Signal Hall", "Field Shelf",
        "Study Court", "Maker Walk", "Memory Room", "Diagram Desk", "Idea Nook",
        "Open Stacks", "Atlas Hall", "Canvas Shelf", "Stone Room", "Lab Court",
        "Studio Bay", "Archive Walk", "Inquiry Desk", "Signal Court", "Bridge Shelf",
        "Green Room", "Pattern Desk", "Chart Bay", "Focus Hall", "Crossroads Nook",
    ],
    "Custom": [
        "North Stack", "Quiet Annex", "Pattern Bay", "Signal Hall", "Field Shelf",
        "Study Court", "Maker Walk", "Memory Room", "Diagram Desk", "Idea Nook",
        "Open Stacks", "Atlas Hall", "Canvas Shelf", "Stone Room", "Lab Court",
        "Studio Bay", "Archive Walk", "Inquiry Desk", "Signal Court", "Bridge Shelf",
        "Green Room", "Pattern Desk", "Chart Bay", "Focus Hall", "Crossroads Nook",
    ],
}

ROOM_DESCRIPTORS = [
    "Soft light returns to old labels and half-cleared tables.",
    "A small prompt panel waits for the next good answer.",
    "Dust lifts from the edges as if the room has been holding its breath.",
    "The chamber feels calm, organized, and just a little unfinished.",
    "A narrow side shelf slides out when you step inside.",
    "There is no urgency here, only the sense that progress matters.",
]

EVENT_LABELS = {
    "lumen_block": "Lumen Block",
    "token_cache": "Token Cache",
    "secret_passage": "Secret Passage",
    "seal_fragment": "Seal Fragment",
    "lights_out": "Lights Out",
}

SAMPLE_CSV = """question,choice_a,choice_b,choice_c,choice_d,correct_answer,explanation,hint,topic,tags,difficulty
Which mineral fizzes with dilute acid most reliably?,Quartz,Pyrite,Calcite,Feldspar,Calcite,Calcite commonly reacts with dilute acid.,Think carbonate.,Dynamic Earth,"minerals, carbonate",easy
What does weathering do to rock?,Moves it long distances,Breaks it down in place,Melts it into magma,Turns it into metal,Breaks it down in place,Weathering breaks rock down in place before erosion transports it.,Transport is not the same as breaking down.,Dynamic Earth,"weathering, surface processes",easy
Which artist painted the ceiling of the Sistine Chapel?,Monet,Michelangelo,Picasso,Kahlo,Michelangelo,Michelangelo painted the famous ceiling.,Think Renaissance master.,Art,"renaissance, painting",standard
What does value refer to in art?,Price,Lightness or darkness,Frame size,Brush size,Lightness or darkness,Value describes how light or dark something appears.,Think shadow versus highlight.,Art,"value, drawing",easy
"""

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
        .titleish { font-size: 1.42rem !important; }
        .map-box pre { font-size: 1.34rem !important; }
        </style>
        """)
    return "\n".join(extra)


def inject_accessibility_css() -> None:
    extra = build_accessibility_css()
    if extra:
        st.markdown(extra, unsafe_allow_html=True)


def render_brand_footer() -> None:
    st.markdown("---")
    st.markdown(
        f"<div class='small' style='text-align:center'><strong>We are dougalien</strong><br>{contact_email()}</div>",
        unsafe_allow_html=True,
    )


def render_brand_banner() -> None:
    st.markdown(
        f"<div class='small' style='text-align:center; margin-bottom:0.5rem;'><strong>We are dougalien</strong> · {contact_email()}</div>",
        unsafe_allow_html=True,
    )


def speak_text(text: str, key: str) -> None:
    if not text:
        return
    safe = json.dumps(text)
    components.html(
        f"""
        <script>
        const text = {safe};
        if (window.speechSynthesis) {{
            window.speechSynthesis.cancel();
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.lang = 'en-US';
            utterance.rate = 0.96;
            utterance.pitch = 1.0;
            window.speechSynthesis.speak(utterance);
        }}
        </script>
        """,
        height=0,
        key=key,
    )


def stop_speaking(key: str) -> None:
    components.html(
        """
        <script>
        if (window.speechSynthesis) {
            window.speechSynthesis.cancel();
        }
        </script>
        """,
        height=0,
        key=key,
    )


def render_accessibility_controls() -> None:
    with st.expander("Accessibility and voice"):
        st.checkbox("Accessible play mode", key="accessible_play_mode", help="Disables the Lights Out event and keeps room labels visible.")
        st.checkbox("High contrast", key="access_high_contrast")
        st.checkbox("Large text", key="access_large_text")
        st.checkbox("Voice read-aloud", key="voice_read_aloud", value=True, help="Uses your browser's built-in text-to-speech. Works best in Safari or Chrome.")
        st.markdown(
            "<div class='small'>Buttons and radios are keyboard-friendly. Text fields work with device dictation, Voice Control, and screen readers. On iPhone and iPad, Speak Screen and Dictation are good fallbacks if browser voice support is limited.</div>",
            unsafe_allow_html=True,
        )


def render_login() -> None:
    st.title("The Lost Archive")
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
    st.info("This version uses no required OpenAI calls, so it is even cheaper than a single-call app. You can add OPENAI_API_KEY later for optional AI features.")
    render_brand_footer()



def ensure_state() -> None:
    defaults = {
        "started": False,
        "username": "",
        "topic": "Dynamic Earth",
        "difficulty": "Standard",
        "seed": None,
        "tiles": {},
        "current_pos": START,
        "revealed": {START},
        "history": [START],
        "story_log": [],
        "tokens": 4,
        "safeguards": 0,
        "free_passes": 0,
        "darkness_turns": 0,
        "pending_move": None,
        "pending_question": None,
        "hint_shown": False,
        "hint_text": None,
        "correct_count": 0,
        "wrong_count": 0,
        "move_count": 0,
        "game_complete": False,
        "feedback": None,
        "seals": 0,
        "seals_needed": 12,
        "chapter_index": 0,
        "tag_stats": {},
        "question_log": [],
        "pack_name": "",
        "pack_source": "built-in",
        "pack_questions": [],
        "question_deck": [],
        "asked_questions": [],
        "deck_empty": False,
        "vault_ready": False,
        "best_streak": 0,
        "streak": 0,
        "hints_used": 0,
        "authenticated": False,
        "login_error": "",
        "accessible_play_mode": True,
        "access_high_contrast": False,
        "access_large_text": False,
        "voice_read_aloud": True,
        "story_mode": "Free rotating story",
        "run_packet": {},
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value



def difficulty_rules(name: str) -> Dict[str, int]:
    if name == "Easy":
        return {"start_tokens": 5, "hint_cost": 1, "wrong_cost": 0, "backstep": 0, "correct_reward": 1, "seals_needed": 8}
    if name == "Difficult":
        return {"start_tokens": 3, "hint_cost": 2, "wrong_cost": 1, "backstep": 1, "correct_reward": 1, "seals_needed": 16}
    return {"start_tokens": 4, "hint_cost": 1, "wrong_cost": 1, "backstep": 1, "correct_reward": 1, "seals_needed": 12}



def normalize_pack(questions: List[Dict], default_source: str) -> List[Dict]:
    normalized = []
    for raw in questions:
        question_text = str(raw.get("question") or raw.get("q") or "").strip()
        if not question_text:
            continue

        choices: List[str] = []
        raw_choices = raw.get("choices")
        if isinstance(raw_choices, list):
            choices = [str(c).strip() for c in raw_choices if str(c).strip()]
        elif isinstance(raw_choices, str) and raw_choices.strip():
            if "|" in raw_choices:
                choices = [c.strip() for c in raw_choices.split("|") if c.strip()]
            else:
                try:
                    parsed_choices = json.loads(raw_choices)
                    if isinstance(parsed_choices, list):
                        choices = [str(c).strip() for c in parsed_choices if str(c).strip()]
                except Exception:
                    choices = []
        else:
            for key in ["choice_a", "choice_b", "choice_c", "choice_d", "choice_e"]:
                val = raw.get(key)
                if val is not None and str(val).strip():
                    choices.append(str(val).strip())

        if len(choices) < 2:
            continue

        answer_raw = raw.get("correct_answer")
        if answer_raw is None:
            answer_raw = raw.get("answer")
        if answer_raw is None:
            answer_raw = raw.get("a")

        answer_index: Optional[int] = None
        if isinstance(answer_raw, int):
            if 0 <= answer_raw < len(choices):
                answer_index = answer_raw
        elif isinstance(answer_raw, str):
            ans = answer_raw.strip()
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

        tags_raw = raw.get("tags") or raw.get("tag") or raw.get("concepts") or "general"
        if isinstance(tags_raw, list):
            tags = [str(t).strip() for t in tags_raw if str(t).strip()]
        else:
            tags = [t.strip() for t in str(tags_raw).replace(";", ",").split(",") if t.strip()]
        if not tags:
            tags = ["general"]

        source = str(raw.get("topic") or raw.get("source") or default_source).strip() or default_source
        normalized.append(
            {
                "q": question_text,
                "choices": choices,
                "a": answer_index,
                "hint": str(raw.get("hint") or "Look for the most direct clue in the question.").strip(),
                "explain": str(raw.get("explanation") or raw.get("explain") or "That is the keyed answer for this pack.").strip(),
                "tags": tags,
                "source": source,
            }
        )
    return normalized



def parse_uploaded_pack(uploaded_file) -> Tuple[List[Dict], Optional[str]]:
    try:
        content = uploaded_file.getvalue()
        if uploaded_file.name.lower().endswith(".json"):
            data = json.loads(content.decode("utf-8"))
            if isinstance(data, dict):
                items = data.get("questions", [])
            elif isinstance(data, list):
                items = data
            else:
                return [], "JSON must be a list of question objects or an object with a 'questions' list."
            pack = dedupe_pack(normalize_pack(items, "Custom"))
            if not pack:
                return [], "No valid multiple-choice questions were found in the JSON file."
            return pack, None

        text = content.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        items = list(reader)
        pack = dedupe_pack(normalize_pack(items, "Custom"))
        if not pack:
            return [], "No valid multiple-choice questions were found in the CSV file."
        return pack, None
    except Exception as exc:
        return [], f"Could not read the uploaded file: {exc}"



def get_active_pack() -> List[Dict]:
    if st.session_state.pack_source == "uploaded" and st.session_state.pack_questions:
        return st.session_state.pack_questions

    if st.session_state.topic == "Mixed":
        pack: List[Dict] = []
        for name, questions in QUESTION_BANKS.items():
            pack.extend(questions)
        pack.extend(BRAIN_BANK)
        return dedupe_pack(pack)

    built_in = QUESTION_BANKS.get(st.session_state.topic, QUESTION_BANKS["Dynamic Earth"]).copy()
    built_in.extend(BRAIN_BANK)
    return dedupe_pack(built_in)


def unique_question_key(question: Dict) -> Tuple:
    return (
        str(question.get("q", "")).strip().lower(),
        tuple(str(choice).strip().lower() for choice in question.get("choices", [])),
        int(question.get("a", -1)),
    )


def dedupe_pack(pack: List[Dict]) -> List[Dict]:
    seen = set()
    out: List[Dict] = []
    for question in pack:
        key = unique_question_key(question)
        if key in seen:
            continue
        seen.add(key)
        out.append(question)
    return out


def recommended_pack_size(seals_needed: int) -> int:
    return max(seals_needed + 4, int(seals_needed * 1.5))


def pack_size_message(question_count: int, seals_needed: int) -> str:
    recommended = recommended_pack_size(seals_needed)
    if question_count < seals_needed:
        return (
            f"This pack has only {question_count} unique questions for a {seals_needed}-Seal run. "
            "That is too small for a no-repeat run."
        )
    if question_count < recommended:
        return (
            f"This pack has {question_count} unique questions. It will work, but for cleaner no-repeat play "
            f"aim for about {recommended}+ questions."
        )
    return f"This pack has {question_count} unique questions, which is a good size for this run."


def build_question_deck(pack: List[Dict], seed: int) -> List[Dict]:
    deck = [{**question} for question in dedupe_pack(pack)]
    rng = random.Random(seed + 101)
    rng.shuffle(deck)
    return deck


def draw_next_question() -> Optional[Dict]:
    if not st.session_state.question_deck:
        st.session_state.deck_empty = True
        return None

    question = st.session_state.question_deck.pop(0)
    st.session_state.asked_questions.append(question["q"])
    return question



def choose_event_positions(rng: random.Random) -> Dict[Tuple[int, int], str]:
    positions = [(x, y) for y in range(SIZE) for x in range(SIZE) if (x, y) not in {START, VAULT}]
    rng.shuffle(positions)
    event_types = ["lumen_block", "token_cache", "secret_passage", "seal_fragment", "lights_out"]
    return {positions[i]: event_types[i] for i in range(len(event_types))}




def build_tiles(seed: int, topic: str, pack: List[Dict]) -> Dict[Tuple[int, int], Dict]:
    rng = random.Random(seed)
    events = choose_event_positions(rng)
    names = get_room_pool(topic)[:]
    rng.shuffle(names)
    descriptor_pool = get_room_descriptors()

    tiles: Dict[Tuple[int, int], Dict] = {}
    for y in range(SIZE):
        for x in range(SIZE):
            pos = (x, y)
            if pos == START:
                tiles[pos] = {
                    "kind": "start",
                    "name": get_start_name(),
                    "desc": f"The first node is already lit. {packet_value('subtitle', 'A fresh run is waiting to unfold.')}",
                    "question": None,
                    "visited": True,
                    "event": None,
                    "event_used": True,
                }
                continue

            if pos == VAULT:
                tiles[pos] = {
                    "kind": "vault",
                    "name": get_vault_name(),
                    "desc": f"The final chamber is present but dormant. Enough {get_seal_name()}s will wake it.",
                    "question": None,
                    "visited": False,
                    "event": None,
                    "event_used": True,
                }
                continue

            event_type = events.get(pos)
            if event_type == "lumen_block":
                name = "Lumen Block Chamber"
                desc = "A slow-turning cube of light floats over a low pedestal. Something helpful is stored here."
            elif event_type == "token_cache":
                name = "Token Cache Room"
                desc = "A side drawer has been left half-open, as if the archive meant to reward someone careful."
            elif event_type == "secret_passage":
                name = "Passage Switchboard"
                desc = "Old routing levers and lit track markers suggest a hidden shortcut."
            elif event_type == "seal_fragment":
                name = "Seal Fragment Vaultlet"
                desc = "A small brass seal sits on felt, already warm to the touch."
            elif event_type == "lights_out":
                name = "Dark Relay Room"
                desc = "A control panel flickers, unstable but still responsive to the archive’s mood."
            else:
                name = names.pop() if names else f"Archive Room {x}-{y}"
                desc = rng.choice(descriptor_pool)

            tiles[pos] = {
                "kind": "standard",
                "name": name,
                "desc": desc,
                "question": None,
                "visited": False,
                "event": event_type,
                "event_used": False,
            }
    return tiles



def pos_key(pos: Tuple[int, int]) -> str:
    return f"{pos[0]},{pos[1]}"



def in_bounds(pos: Tuple[int, int]) -> bool:
    return 0 <= pos[0] < SIZE and 0 <= pos[1] < SIZE



def current_tile() -> Dict:
    return st.session_state.tiles[st.session_state.current_pos]



def neighbor_positions(pos: Tuple[int, int]) -> Dict[str, Tuple[int, int]]:
    neighbors = {}
    for direction, delta in DIRECTIONS.items():
        candidate = (pos[0] + delta[0], pos[1] + delta[1])
        if in_bounds(candidate):
            neighbors[direction] = candidate
    return neighbors



def add_log(text: str) -> None:
    st.session_state.story_log.append(text)
    st.session_state.story_log = st.session_state.story_log[-12:]



def maybe_add_story_milestone() -> None:
    thresholds = [
        max(1, st.session_state.seals_needed // 4),
        max(2, st.session_state.seals_needed // 2),
        max(3, (st.session_state.seals_needed * 3) // 4),
        st.session_state.seals_needed,
    ]
    topic = st.session_state.topic if st.session_state.pack_source == "built-in" else "Custom"
    milestones = get_story_milestones(topic)
    while st.session_state.chapter_index < len(thresholds) and st.session_state.seals >= thresholds[st.session_state.chapter_index]:
        add_log(milestones[st.session_state.chapter_index])
        st.session_state.chapter_index += 1



def update_vault_ready() -> None:
    if not st.session_state.vault_ready and st.session_state.seals >= st.session_state.seals_needed:
        st.session_state.vault_ready = True
        add_log(f"A strong tone rolls through {packet_value('setting_name', 'the route')}. The {get_vault_name()} is now ready to open.")



def record_question_outcome(question: Dict, correct: bool, hint_used: bool) -> None:
    tags = question.get("tags") or [question.get("source", "general")]
    for tag in tags:
        bucket = st.session_state.tag_stats.setdefault(tag, {"correct": 0, "wrong": 0, "hints": 0, "attempts": 0})
        bucket["attempts"] += 1
        if correct:
            bucket["correct"] += 1
        else:
            bucket["wrong"] += 1
        if hint_used:
            bucket["hints"] += 1
    st.session_state.question_log.append(
        {
            "question": question["q"],
            "tags": tags,
            "source": question.get("source", st.session_state.topic),
            "correct": correct,
            "hint_used": hint_used,
        }
    )



def apply_tile_event(pos: Tuple[int, int]) -> None:
    tile = st.session_state.tiles[pos]
    event_type = tile.get("event")
    if not event_type or tile.get("event_used"):
        return

    tile["event_used"] = True
    if event_type == "lumen_block":
        st.session_state.tokens += 3
        st.session_state.safeguards += 1
        add_log(packet_value("event_flavor", {}).get("lumen_block", f"You found the Lumen Block. Gain +3 {get_token_name()} and +1 safeguard."))
    elif event_type == "token_cache":
        gain = 2
        st.session_state.tokens += gain
        add_log(packet_value("event_flavor", {}).get("token_cache", f"You found a pile of tokens. Gain +{gain} {get_token_name()}."))
    elif event_type == "secret_passage":
        st.session_state.free_passes += 1
        add_log(packet_value("event_flavor", {}).get("secret_passage", f"A secret passage clicks into place. Your next unrevealed room opens for free and still earns a {get_seal_name()}."))
    elif event_type == "seal_fragment":
        if st.session_state.seals < st.session_state.seals_needed:
            st.session_state.seals += 1
            add_log(packet_value("event_flavor", {}).get("seal_fragment", f"You recover a fragment. It counts as +1 {get_seal_name()}."))
            maybe_add_story_milestone()
            update_vault_ready()
        else:
            st.session_state.tokens += 1
            add_log("You find a spare Seal Fragment after the goal is met. It converts into +1 Insight.")
    elif event_type == "lights_out":
        if st.session_state.get("accessible_play_mode"):
            st.session_state.tokens += 1
            add_log(f"The controls try to dim, but accessible play mode keeps labels visible. You get +1 {get_token_name()} instead.")
        else:
            st.session_state.darkness_turns = 1
            add_log(packet_value("event_flavor", {}).get("lights_out", "All the lights go out. On your next move, the direction buttons will lose their room labels."))



def move_to_revealed(pos: Tuple[int, int]) -> None:
    st.session_state.current_pos = pos
    st.session_state.history.append(pos)
    st.session_state.move_count += 1
    tile = st.session_state.tiles[pos]
    add_log(f"You move into {tile['name']}. {tile['desc']}")



def inspect_room_text() -> str:
    tile = current_tile()
    extras = {
        "start": f"The opening map suggests many routes, but only earned answers will stabilize new rooms in {packet_value('setting_name', 'this run') }.",
        "standard": "A small label suggests the archive improves through repetition, clarity, and steady effort.",
        "vault": f"The {get_vault_name()} is quiet for now. When enough {get_seal_name()}s are earned, it will be ready from anywhere in the map.",
    }
    return f"{tile['name']}: {tile['desc']} {extras.get(tile['kind'], '')}".strip()



def choose_direction(direction: str) -> None:
    if st.session_state.pending_move is not None or st.session_state.game_complete:
        return

    neighbors = neighbor_positions(st.session_state.current_pos)
    if direction not in neighbors:
        st.session_state.feedback = "That route is not available from here."
        return

    target = neighbors[direction]
    tile = st.session_state.tiles[target]
    st.session_state.feedback = None

    if st.session_state.darkness_turns > 0:
        st.session_state.darkness_turns -= 1

    if target in st.session_state.revealed:
        move_to_revealed(target)
        return

    if st.session_state.free_passes > 0:
        st.session_state.free_passes -= 1
        st.session_state.revealed.add(target)
        tile["visited"] = True
        st.session_state.current_pos = target
        st.session_state.history.append(target)
        st.session_state.move_count += 1
        st.session_state.seals += 1
        st.session_state.tokens += difficulty_rules(st.session_state.difficulty)["correct_reward"]
        add_log(f"A secret route opens. You enter {tile['name']} without a question and still earn 1 {get_seal_name()}.")
        maybe_add_story_milestone()
        update_vault_ready()
        apply_tile_event(target)
        return

    next_question = draw_next_question()
    if next_question is None:
        st.session_state.feedback = (
            "You have used every unique question in this run. Restart for a new run packet or use a larger pack for cleaner no-repeat play."
        )
        return

    st.session_state.pending_move = target
    st.session_state.pending_question = next_question
    st.session_state.hint_shown = False
    st.session_state.hint_text = None



def use_hint() -> None:
    question = st.session_state.pending_question
    if question is None or st.session_state.hint_shown:
        return

    cost = difficulty_rules(st.session_state.difficulty)["hint_cost"]
    if st.session_state.tokens < cost:
        st.session_state.hint_text = f"You need {cost} Insight token{'s' if cost != 1 else ''} for a hint."
        return

    st.session_state.tokens -= cost
    st.session_state.hint_shown = True
    st.session_state.hint_text = f"Hint: {question['hint']}"
    st.session_state.hints_used += 1



def answer_pending(choice_index: int) -> None:
    target = st.session_state.pending_move
    question = st.session_state.pending_question
    if target is None or question is None:
        return

    rules = difficulty_rules(st.session_state.difficulty)
    tile = st.session_state.tiles[target]
    hint_used = st.session_state.hint_shown

    if choice_index == question["a"]:
        st.session_state.correct_count += 1
        st.session_state.streak += 1
        st.session_state.best_streak = max(st.session_state.best_streak, st.session_state.streak)
        st.session_state.revealed.add(target)
        tile["visited"] = True
        st.session_state.current_pos = target
        st.session_state.history.append(target)
        st.session_state.move_count += 1
        st.session_state.tokens += rules["correct_reward"]
        st.session_state.seals += 1
        add_log(f"Correct. You enter {tile['name']}. {tile['desc']}")
        add_log(question["explain"])
        record_question_outcome(question, True, hint_used)
        maybe_add_story_milestone()
        update_vault_ready()
        apply_tile_event(target)
    else:
        st.session_state.wrong_count += 1
        st.session_state.streak = 0
        add_log(f"Not quite. {question['explain']}")
        record_question_outcome(question, False, hint_used)
        if st.session_state.safeguards > 0:
            st.session_state.safeguards -= 1
            add_log("Your safeguard absorbs the setback. You keep your place.")
        else:
            st.session_state.tokens = max(0, st.session_state.tokens - rules["wrong_cost"])
            if rules["backstep"] and len(st.session_state.history) > 1:
                st.session_state.history.pop()
                back_pos = st.session_state.history[-1]
                st.session_state.current_pos = back_pos
                back_name = st.session_state.tiles[back_pos]["name"]
                add_log(f"The lock rejects the answer. You slide back to {back_name} and the archive asks you to regroup.")
            else:
                add_log("The archive holds your place, but the route stays closed for now.")

    st.session_state.pending_move = None
    st.session_state.pending_question = None
    st.session_state.hint_shown = False
    st.session_state.hint_text = None



def room_status_text(pos: Tuple[int, int]) -> str:
    tile = st.session_state.tiles[pos]
    if pos in st.session_state.revealed:
        return tile["name"]
    return "Unknown chamber"



def map_cell(pos: Tuple[int, int]) -> str:
    if pos == st.session_state.current_pos:
        return "🟦"
    if pos not in st.session_state.revealed:
        return "⬛"
    if pos == START:
        return "🟩"
    if pos == VAULT:
        return "🟥" if st.session_state.vault_ready else "🟫"
    tile = st.session_state.tiles[pos]
    event_type = tile.get("event")
    if event_type == "lumen_block":
        return "🟪"
    if event_type == "token_cache":
        return "🟨"
    if event_type == "secret_passage":
        return "🟧"
    if event_type == "seal_fragment":
        return "🟪"
    if event_type == "lights_out":
        return "🟫"
    return "⬜"



def render_map() -> None:
    rows = []
    for y in range(SIZE):
        row = " ".join(map_cell((x, y)) for x in range(SIZE))
        rows.append(row)
    map_text = "\n".join(rows)
    st.markdown(f"<div class='map-box'><pre>{map_text}</pre></div>", unsafe_allow_html=True)
    st.markdown(
        "<span class='kicker'>🟦 you</span>"
        "<span class='kicker'>🟩 start</span>"
        "<span class='kicker'>⬜ room</span>"
        "<span class='kicker'>⬛ hidden</span>"
        "<span class='kicker'>🟥 vault ready</span>"
        "<span class='kicker'>🟨 cache</span>"
        "<span class='kicker'>🟧 passage</span>",
        unsafe_allow_html=True,
    )



def build_feedback_summary() -> Dict:
    attempts = st.session_state.correct_count + st.session_state.wrong_count
    accuracy = (st.session_state.correct_count / attempts * 100) if attempts else 0
    tag_rows = []
    for tag, stats in st.session_state.tag_stats.items():
        total = stats["correct"] + stats["wrong"]
        if total == 0:
            continue
        rate = stats["correct"] / total
        tag_rows.append(
            {
                "tag": tag,
                "attempts": total,
                "correct": stats["correct"],
                "wrong": stats["wrong"],
                "hints": stats["hints"],
                "rate": rate,
            }
        )
    tag_rows.sort(key=lambda row: (-row["rate"], -row["attempts"], row["tag"]))

    strengths = [row for row in tag_rows if row["attempts"] >= 1 and row["rate"] >= 0.75][:3]
    needs = sorted(
        [row for row in tag_rows if row["attempts"] >= 1 and row["rate"] < 0.7],
        key=lambda row: (row["rate"], -row["attempts"], row["tag"]),
    )[:3]

    recommendation = None
    if needs:
        recommendation = needs[0]["tag"]
    elif tag_rows:
        recommendation = tag_rows[min(1, len(tag_rows) - 1)]["tag"]

    return {
        "attempts": attempts,
        "accuracy": accuracy,
        "strengths": strengths,
        "needs": needs,
        "recommendation": recommendation,
    }



def reset_game(pack: Optional[List[Dict]] = None, pack_name: Optional[str] = None, pack_source: str = "built-in") -> None:
    topic = st.session_state.topic
    difficulty = st.session_state.difficulty
    rules = difficulty_rules(difficulty)
    if pack is None:
        pack = get_active_pack()
        pack_name = pack_name or (topic if pack_source == "built-in" else "Custom Pack")
    pack = dedupe_pack(pack or [])
    if not pack:
        st.session_state.feedback = "No question pack is loaded."
        return

    seed = random.randint(10000, 999999)
    run_topic = topic if pack_source == "built-in" else "Custom"
    run_packet = build_run_packet(seed, run_topic, pack_name or topic, pack, st.session_state.story_mode, st.session_state.username)
    st.session_state.run_packet = run_packet
    question_deck = build_question_deck(pack, seed)
    tiles = build_tiles(seed, run_topic, pack)
    intro_key = run_topic

    st.session_state.started = True
    st.session_state.seed = seed
    st.session_state.tiles = tiles
    st.session_state.current_pos = START
    st.session_state.revealed = {START}
    st.session_state.history = [START]
    st.session_state.run_packet = run_packet
    st.session_state.story_log = get_story_intro(intro_key)[:]
    st.session_state.tokens = rules["start_tokens"]
    st.session_state.safeguards = 0
    st.session_state.free_passes = 0
    st.session_state.darkness_turns = 0
    st.session_state.pending_move = None
    st.session_state.pending_question = None
    st.session_state.hint_shown = False
    st.session_state.hint_text = None
    st.session_state.correct_count = 0
    st.session_state.wrong_count = 0
    st.session_state.move_count = 0
    st.session_state.game_complete = False
    st.session_state.feedback = None
    st.session_state.seals = 0
    st.session_state.seals_needed = rules["seals_needed"]
    st.session_state.chapter_index = 0
    st.session_state.tag_stats = {}
    st.session_state.question_log = []
    st.session_state.pack_name = pack_name or topic
    st.session_state.pack_source = pack_source
    st.session_state.pack_questions = pack
    st.session_state.question_deck = question_deck
    st.session_state.asked_questions = []
    st.session_state.deck_empty = False
    st.session_state.vault_ready = False
    st.session_state.best_streak = 0
    st.session_state.streak = 0
    st.session_state.hints_used = 0



def render_start() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
    st.title("The Lost Archive")
    render_brand_banner()
    st.caption("A story-driven educational adventure that can run on built-in topics or uploaded question packs.")
    st.info("Free mode uses rotating built-in story shells. Pro mode uses one optional OpenAI run-packet call per run to freshen names, setting, milestones, and ending text while keeping the same answer key underneath.")
    st.markdown(
        "<div class='card'><div class='titleish'>Prototype focus</div>"
        "<div class='soft'>Win by earning a fixed number of Archive Seals. The map adds story, random finds, shortcuts, and setbacks, while the learning summary tells the player where they were strong and where they should review next.</div></div>",
        unsafe_allow_html=True,
    )

    st.text_input("Player name", key="username", placeholder="Doug")
    st.selectbox("Difficulty", ["Easy", "Standard", "Difficult"], key="difficulty")
    st.selectbox("Built-in topic", ["Dynamic Earth", "Art", "General Science", "Mixed"], key="topic")
    st.selectbox("Story variation", ["Free rotating story", "Pro AI run packet"], key="story_mode")

    st.markdown(
        "<span class='kicker'>Correct = move + 1 Seal</span>"
        "<span class='kicker'>Hints cost tokens</span>"
        "<span class='kicker'>Random finds can help</span>"
        "<span class='kicker'>Wrong answers may push you back</span>",
        unsafe_allow_html=True,
    )

    seals_needed = difficulty_rules(st.session_state.difficulty)["seals_needed"]
    built_in_pack = get_active_pack()
    st.markdown(
        f"<div class='small'>Current built-in pack: {len(built_in_pack)} unique questions · "
        f"{pack_size_message(len(built_in_pack), seals_needed)}</div>",
        unsafe_allow_html=True,
    )

    st.markdown("### Optional custom pack")
    uploaded = st.file_uploader(
        "Upload CSV or JSON question pack",
        type=["csv", "json"],
        help="If present, the uploaded pack overrides the built-in topic for this run."
    )
    uploaded_pack: List[Dict] = []
    upload_error: Optional[str] = None
    if uploaded is not None:
        uploaded_pack, upload_error = parse_uploaded_pack(uploaded)
        if upload_error:
            st.error(upload_error)
        else:
            st.success(f"Loaded {len(uploaded_pack)} unique questions from {uploaded.name}.")
            pack_msg = pack_size_message(len(uploaded_pack), seals_needed)
            if len(uploaded_pack) < seals_needed:
                st.warning(pack_msg)
            else:
                st.info(pack_msg)

    with st.expander("Upload format and template"):
        st.write("Each row is one question. The easiest path is to build a spreadsheet and save it as CSV.")
        st.markdown(
            "- `question`: the question text\n"
            "- `choice_a` to `choice_d`: answer choices\n"
            "- `correct_answer`: exact answer text, 0-based index, 1-based index, or letter A-D\n"
            "- `explanation`: short teaching feedback after the answer\n"
            "- `hint`: optional hint that costs tokens\n"
            "- `topic`: optional source label shown in the game\n"
            "- `tags`: comma-separated concept labels used for the learning summary\n"
            "- `difficulty`: optional note for your own organization"
        )
        st.code(
            "question,choice_a,choice_b,choice_c,choice_d,correct_answer,explanation,hint,topic,tags,difficulty\n"
            "Which mineral fizzes with dilute acid most reliably?,Quartz,Pyrite,Calcite,Feldspar,Calcite,"
            "Calcite commonly reacts with dilute acid.,Think carbonate.,Dynamic Earth,\"minerals, carbonate\",easy",
            language="text",
        )
        st.download_button("Download sample CSV", data=SAMPLE_CSV, file_name="lost_archive_sample_pack.csv", mime="text/csv")

    render_accessibility_controls()
    if st.session_state.story_mode == "Pro AI run packet" and not st.secrets.get("OPENAI_API_KEY", ""):
        st.warning("Pro AI run packet is selected, but OPENAI_API_KEY is empty. The app will fall back to a free rotating story shell.")

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Start built-in run"):
            reset_game(pack=built_in_pack, pack_name=st.session_state.topic, pack_source="built-in")
            st.rerun()
    with c2:
        if st.button("Start uploaded run"):
            if uploaded is None:
                st.warning("Upload a CSV or JSON pack first.")
            elif upload_error:
                st.error(upload_error)
            else:
                reset_game(pack=uploaded_pack, pack_name=uploaded.name, pack_source="uploaded")
                st.rerun()

    render_brand_footer()


def render_header() -> None:
    tile = current_tile()
    st.markdown(
        f"<div class='card'><div class='titleish'>{tile['name']}</div>"
        f"<div class='soft'>{tile['desc']}</div></div>",
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(get_seal_name() + "s", f"{st.session_state.seals}/{st.session_state.seals_needed}")
    c2.metric(get_token_name(), st.session_state.tokens)
    c3.metric("Safeguards", st.session_state.safeguards)
    c4.metric("Free Passes", st.session_state.free_passes)

    c5, c6, c7 = st.columns(3)
    c5.metric("Correct", st.session_state.correct_count)
    c6.metric("Wrong", st.session_state.wrong_count)
    c7.metric("Best streak", st.session_state.best_streak)

    st.markdown(
        f"<div class='small'>Run: {packet_value('mode', 'free-template')} · Pack: {st.session_state.pack_name} · Difficulty: {st.session_state.difficulty} · "
        f"Questions left: {len(st.session_state.question_deck)} · {get_vault_name()}: {'ready' if st.session_state.vault_ready else 'locked'}</div>",
        unsafe_allow_html=True,
    )



def render_story() -> None:
    recent_lines = st.session_state.story_log[-6:]
    st.markdown("<div class='story-log'>", unsafe_allow_html=True)
    for line in recent_lines:
        st.write(line)
    st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.get("voice_read_aloud") and recent_lines:
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Read latest story aloud"):
                speak_text(" ".join(recent_lines[-2:]), key=f"story_voice_{st.session_state.move_count}")
        with c2:
            if st.button("Stop voice"):
                stop_speaking(key=f"stop_story_{st.session_state.move_count}")



def render_actions() -> None:
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("Inspect room"):
            add_log(inspect_room_text())
            st.rerun()
    with c2:
        if st.button("Archive notes"):
            if st.session_state.vault_ready:
                add_log(f"The {get_vault_name()} is awake. You can finish the run whenever you want.")
            else:
                left = max(0, st.session_state.seals_needed - st.session_state.seals)
                add_log(f"The route estimates {left} more {get_seal_name()}{'s' if left != 1 else ''} are needed to wake the {get_vault_name()}.")
            st.rerun()
    with c3:
        if st.button("Open Heart Vault"):
            if st.session_state.vault_ready:
                finish_run()
                st.rerun()
            else:
                st.info(f"The {get_vault_name()} is still locked. Earn more {get_seal_name()}s first.")
    with c4:
        if st.button("Accessibility"):
            st.session_state.feedback = "Use the Accessibility and voice panel near the top of the page for high contrast, large text, and read-aloud controls."
            st.rerun()



def finish_run() -> None:
    st.session_state.game_complete = True
    add_log(packet_value("completion_text", f"The {get_vault_name()} opens and the route settles into place."))



def render_direction_buttons() -> None:
    neighbors = neighbor_positions(st.session_state.current_pos)
    hide_labels = st.session_state.darkness_turns > 0 and not st.session_state.get("accessible_play_mode")
    labels = {}
    for direction, pos in neighbors.items():
        if hide_labels:
            labels[direction] = direction.title()
        else:
            labels[direction] = f"{direction.title()} · {room_status_text(pos)}"

    col1, col2 = st.columns(2)
    if "north" in neighbors:
        with col1:
            if st.button(labels["north"], key=f"move_n_{st.session_state.current_pos}"):
                choose_direction("north")
                st.rerun()
    if "east" in neighbors:
        with col2:
            if st.button(labels["east"], key=f"move_e_{st.session_state.current_pos}"):
                choose_direction("east")
                st.rerun()

    col3, col4 = st.columns(2)
    if "south" in neighbors:
        with col3:
            if st.button(labels["south"], key=f"move_s_{st.session_state.current_pos}"):
                choose_direction("south")
                st.rerun()
    if "west" in neighbors:
        with col4:
            if st.button(labels["west"], key=f"move_w_{st.session_state.current_pos}"):
                choose_direction("west")
                st.rerun()



def render_question_card() -> None:
    target = st.session_state.pending_move
    question = st.session_state.pending_question
    if target is None or question is None:
        return

    tile = st.session_state.tiles[target]
    st.markdown("---")
    st.markdown(
        f"<div class='card'><div class='titleish'>Unlock {tile['name']}</div>"
        f"<div class='soft'>Answer correctly to move into this room and earn 1 {get_seal_name()}.</div></div>",
        unsafe_allow_html=True,
    )
    st.markdown(f"**Source:** {question.get('source', st.session_state.topic)}")
    st.markdown(f"<div class='small'>Unique questions left after this draw: {len(st.session_state.question_deck)}</div>", unsafe_allow_html=True)
    tag_line = ", ".join(question.get("tags", []))
    if tag_line:
        st.markdown(f"<div class='small'>Tags: {tag_line}</div>", unsafe_allow_html=True)
    st.write(question["q"])

    with st.form(f"question_form_{pos_key(target)}", clear_on_submit=False):
        answer = st.radio("Choose one", question["choices"], index=None)
        submitted = st.form_submit_button("Submit answer")
        if submitted and answer is not None:
            answer_pending(question["choices"].index(answer))
            st.rerun()

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Use hint", key=f"hint_{pos_key(target)}"):
            use_hint()
            st.rerun()
    with c2:
        if st.button("Cancel", key=f"cancel_{pos_key(target)}"):
            st.session_state.pending_move = None
            st.session_state.pending_question = None
            st.session_state.hint_shown = False
            st.session_state.hint_text = None
            st.rerun()
    with c3:
        if st.session_state.get("voice_read_aloud") and st.button("Read question", key=f"read_q_{pos_key(target)}"):
            speak_text(question["q"], key=f"question_voice_{pos_key(target)}")

    if st.session_state.hint_text:
        st.info(st.session_state.hint_text)



def render_feedback_panel() -> None:
    summary = build_feedback_summary()
    st.markdown("### Learning summary")
    attempts = summary["attempts"]
    accuracy_text = f"{summary['accuracy']:.0f}%" if attempts else "—"
    c1, c2, c3 = st.columns(3)
    c1.metric("Attempted", attempts)
    c2.metric("Accuracy", accuracy_text)
    c3.metric("Hints used", st.session_state.hints_used)

    strengths = summary["strengths"]
    needs = summary["needs"]

    left, right = st.columns(2)
    with left:
        st.markdown("**Strong areas**")
        if strengths:
            for row in strengths:
                st.write(f"- {row['tag']} ({row['correct']}/{row['attempts']})")
        else:
            st.write("- Not enough data yet.")
    with right:
        st.markdown("**Needs more work**")
        if needs:
            for row in needs:
                st.write(f"- {row['tag']} ({row['correct']}/{row['attempts']})")
        else:
            st.write("- Nothing stands out yet.")

    if summary["recommendation"]:
        st.markdown(f"<div class='small'>Suggested next focus: {summary['recommendation']}</div>", unsafe_allow_html=True)



def render_end() -> None:
    name = st.session_state.username or "Friend"
    st.success(f"{name}, you completed this run.")
    st.write(
        f"{packet_value('completion_text', 'The route resolves cleanly.')} This run still used a fixed {get_seal_name()} goal underneath, so the engine stays useful across topics while the wrapper changes from run to run."
    )
    render_feedback_panel()
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Play again"):
            reset_game(pack=st.session_state.pack_questions, pack_name=st.session_state.pack_name, pack_source=st.session_state.pack_source)
            st.rerun()
    with c2:
        if st.button("Back to setup"):
            st.session_state.started = False
            st.rerun()



def main() -> None:
    ensure_state()
    st.markdown(CSS, unsafe_allow_html=True)
    inject_accessibility_css()

    if not st.session_state.get("authenticated"):
        render_login()
        return

    if not st.session_state.started:
        render_start()
        return

    st.title(get_game_title())
    render_brand_banner()
    st.caption(f"Earn {get_seal_name()}s, discover side rewards, and finish with a clear learning summary.")
    render_accessibility_controls()

    if st.session_state.feedback:
        st.info(st.session_state.feedback)

    render_header()
    render_map()
    render_story()
    render_actions()

    if not st.session_state.game_complete:
        if st.session_state.pending_move is None:
            st.markdown("---")
            st.subheader("Choose your next move")
            st.markdown(
                "<div class='small'>Unrevealed rooms require a correct answer unless a Secret Passage is active. Revealed rooms are free to revisit.</div>",
                unsafe_allow_html=True,
            )
            render_direction_buttons()
        else:
            render_question_card()

    with st.expander("Run notes"):
        st.write(
            f"Pack: {st.session_state.pack_name} · Wrong answers: {st.session_state.wrong_count} · "
            f"Questions asked: {len(st.session_state.asked_questions)} · Questions left: {len(st.session_state.question_deck)} · Seed: {st.session_state.seed}"
        )
        st.write(f"Questions are drawn from a shuffled no-repeat deck for each run. Story mode: {st.session_state.story_mode}. Active run packet: {packet_value('mode', 'free-template')}. Use the upload option to turn the same engine into a review game for almost any discipline.")
        render_feedback_panel()

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Restart run"):
            reset_game(pack=st.session_state.pack_questions, pack_name=st.session_state.pack_name, pack_source=st.session_state.pack_source)
            st.rerun()
    with c2:
        if st.button("Back to setup"):
            st.session_state.started = False
            st.rerun()
    with c3:
        if st.button("Log out"):
            st.session_state.authenticated = False
            st.session_state.started = False
            st.rerun()

    if st.session_state.game_complete:
        render_end()

    render_brand_footer()


if __name__ == "__main__":
    main()
