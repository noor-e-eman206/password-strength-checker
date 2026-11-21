import string
from pathlib import Path

from nicegui import ui

MAX_SCORE = 7

# Header colors
HEADER_BG = "#FFC107"    # yellow
HEADER_TEXT = "#009688"  # teal
COMMON_FILE = Path(__file__).with_name("common.txt")

# Used only if common.txt is missing, so the app still runs
FALLBACK_COMMON = {
    "password", "password123", "123456", "12345678", "qwerty", "abc123",
    "letmein", "welcome", "hello world", "johnsmith", "agent007", "iloveyou",
}

# Look of each verdict: emoji, Quasar color (bar/badge), Tailwind text color
THEMES = {
    "common": ("🚫", "negative", "text-red-600"),
    "weak": ("😟", "negative", "text-red-600"),
    "okay": ("😐", "orange", "text-orange-500"),
    "good": ("🙂", "info", "text-blue-600"),
    "strong": ("💪", "positive", "text-green-600"),
}


def load_common() -> set[str]:
    if COMMON_FILE.exists():
        text = COMMON_FILE.read_text(encoding="utf-8", errors="ignore")
        return set(text.splitlines())
    return FALLBACK_COMMON


COMMON = load_common()


def evaluate(password: str) -> dict:
    """Same scoring rules as the video: length (0-4) + character types (0-3)."""
    length = len(password)
    types = {
        "Uppercase": any(c in string.ascii_uppercase for c in password),
        "Lowercase": any(c in string.ascii_lowercase for c in password),
        "Special": any(c in string.punctuation for c in password),
        "Digits": any(c in string.digits for c in password),
    }

    if password in COMMON:
        return {"common": True, "score": 0, "length": length, "types": types,
                "length_points": 0, "type_points": 0}

    length_points = sum(length > n for n in (8, 12, 17, 20))
    type_points = max(sum(types.values()) - 1, 0)

    return {"common": False, "score": length_points + type_points, "length": length,
            "types": types, "length_points": length_points, "type_points": type_points}


def verdict_for(result: dict) -> tuple[str, str]:
    """Return (label, theme key)."""
    if result["common"]:
        return "Found in a common password list. Useless!", "common"
    score = result["score"]
    if score < 4:
        return "Quite weak", "weak"
    if score == 4:
        return "Okay", "okay"
    if score < 6:
        return "Pretty good", "good"
    return "Strong", "strong"


@ui.page("/")
def index():
    # Animated rainbow-ish page background
    ui.add_css("""
        body {
            background: linear-gradient(-45deg, #ffd1dc, #c7ceea, #b5ead7, #fff1b8);
            background-size: 400% 400%;
            animation: bgmove 15s ease infinite;
            min-height: 100vh;
        }
        @keyframes bgmove {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
    """)

    # Chip colors for each character type (Quasar color names)
    type_colors = {"Uppercase": "blue", "Lowercase": "purple",
                   "Special": "orange", "Digits": "teal"}

    with ui.card().classes("w-full max-w-xl mx-auto mt-12 p-0 overflow-hidden "
                           "rounded-2xl shadow-2xl"):
        # Gradient header
        with ui.column().classes("w-full p-6 gap-1").style(
                f"background: {HEADER_BG}; color: {HEADER_TEXT}"):
            ui.label("🔐 Password Strength Checker").classes("text-2xl font-extrabold")
            ui.label("Results update live as you type. Nothing is stored or sent anywhere.") \
                .classes("text-sm font-bold")

        with ui.column().classes("w-full p-6 gap-3"):
            pw = ui.input("Enter a password", password=True, password_toggle_button=True) \
                .props("outlined clearable color=deep-purple").classes("w-full")

            bar = ui.linear_progress(value=0, show_value=False, size="22px") \
                .props("rounded color=grey")

            with ui.row().classes("items-center justify-between w-full"):
                with ui.row().classes("items-center gap-3"):
                    emoji_label = ui.label("✨").classes("text-4xl")
                    verdict_label = ui.label("Start typing to see the strength") \
                        .classes("text-lg font-semibold text-gray-500")
                score_badge = ui.badge(f"0 / {MAX_SCORE}").props("color=grey") \
                    .classes("text-lg px-3 py-1")

            details = ui.column().classes("gap-2 mt-2 w-full")

        def update(e):
            password = e.value or ""
            details.clear()

            if not password:
                bar.set_value(0)
                bar.props("color=grey")
                score_badge.set_text(f"0 / {MAX_SCORE}")
                score_badge.props("color=grey")
                emoji_label.set_text("✨")
                verdict_label.set_text("Start typing to see the strength")
                verdict_label.classes(replace="text-lg font-semibold text-gray-500")
                return

            result = evaluate(password)
            label, key = verdict_for(result)
            emoji, color, text_class = THEMES[key]

            bar.set_value(result["score"] / MAX_SCORE)
            bar.props(f"color={color}")
            score_badge.set_text(f"{result['score']} / {MAX_SCORE}")
            score_badge.props(f"color={color}")
            emoji_label.set_text(emoji)
            verdict_label.set_text(label)
            verdict_label.classes(replace=f"text-lg font-semibold {text_class}")

            with details:
                not_common = not result["common"]
                ui.chip("Not in common password list" if not_common
                        else "Found in common password list",
                        icon="verified" if not_common else "block",
                        color="green" if not_common else "red",
                        text_color="white")

                if not_common:
                    ui.chip(f"Length {result['length']} (+{result['length_points']})",
                            icon="straighten",
                            color="indigo" if result["length_points"] else "grey-4",
                            text_color="white" if result["length_points"] else "grey-7")

                    with ui.row().classes("flex-wrap gap-1"):
                        for name, present in result["types"].items():
                            ui.chip(name,
                                    icon="check_circle" if present else "cancel",
                                    color=type_colors[name] if present else "grey-4",
                                    text_color="white" if present else "grey-7")

                    n_types = sum(result["types"].values())
                    ui.chip(f"{n_types} character types (+{result['type_points']})",
                            icon="palette",
                            color="pink" if result["type_points"] else "grey-4",
                            text_color="white" if result["type_points"] else "grey-7")

        pw.on_value_change(update)


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title="Password Strength Checker")