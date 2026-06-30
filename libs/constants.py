import os
import json
import flet as ft

SETTINGS_DIR = "settings"
SETTINGS_FILE = os.path.join(SETTINGS_DIR, "settings.json")

DEFAULT_SETTINGS = {
    "ui": {
        "page_color": "#202124",
        "window_color": "#202124",
        "box_color": "#202124",
        "text_color": "#E3E3E3",
        "line_color": "#444746",
        "label_color": "#9AA0A6"
    },
    "layout": {
        "padding": 15,
        "radius": 10,
        "hour_height": 60,
        "label_width": 55
    },
    "behavior": {
        "event_hours": [9, 10, 14, 15, 16]
    },
    "fab": {
        "mini": False,
        "right": 30,
        "bottom": 30
    }
}

def load_settings():
    if not os.path.exists(SETTINGS_DIR):
        os.makedirs(SETTINGS_DIR)
    
    if not os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_SETTINGS, f, indent=4)
        return DEFAULT_SETTINGS
    
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            user_settings = json.load(f)
            # Basic merge to ensure keys exist
            for section in DEFAULT_SETTINGS:
                if section not in user_settings:
                    user_settings[section] = DEFAULT_SETTINGS[section]
                else:
                    for key in DEFAULT_SETTINGS[section]:
                        if key not in user_settings[section]:
                            user_settings[section][key] = DEFAULT_SETTINGS[section][key]
            return user_settings
    except Exception:
        return DEFAULT_SETTINGS

_cfg = load_settings()

def get_color(color_name):
    # Retrieve Flet color enum if it exists, otherwise assume it's a hex color string
    return getattr(ft.Colors, str(color_name).upper(), color_name)

PAGE_COLOR = get_color(_cfg["ui"]["page_color"])
WINDOW_COLOR = get_color(_cfg["ui"]["window_color"])
BOX_COLOR = get_color(_cfg["ui"]["box_color"])
TEXT_COLOR = get_color(_cfg["ui"]["text_color"])
LINE_COLOR = get_color(_cfg["ui"]["line_color"])
LABEL_COLOR = get_color(_cfg["ui"]["label_color"])

PADDING = _cfg["layout"]["padding"]
RADIUS = _cfg["layout"]["radius"]
HOUR_HEIGHT = _cfg["layout"]["hour_height"]
LABEL_WIDTH = _cfg["layout"]["label_width"]

EVENT_HOURS = _cfg["behavior"]["event_hours"]

ADD_BUTTON_MINI = _cfg["fab"]["mini"]
ADD_BUTTON_RIGHT = _cfg["fab"]["right"]
ADD_BUTTON_BOTTOM = _cfg["fab"]["bottom"]
