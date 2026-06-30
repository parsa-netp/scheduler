import json
import flet as ft
from libs.constants import (
    SETTINGS_FILE,
    _cfg,
    BOX_COLOR,
    RADIUS,
    TEXT_COLOR,
    LABEL_COLOR
)

class SettingsView(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.main_page = page
        self.bgcolor = BOX_COLOR
        self.border_radius = RADIUS
        self.padding = 20
        self.expand = True

        self.inputs = {}

        # Build UI based on _cfg
        sections = []
        for section_name, section_data in _cfg.items():
            section_title = ft.Text(section_name.upper(), size=18, weight=ft.FontWeight.BOLD, color=TEXT_COLOR)
            controls = []
            
            for key, val in section_data.items():
                if isinstance(val, bool):
                    cb = ft.Switch(label=key, value=val, active_color=ft.Colors.BLUE_400)
                    self.inputs[(section_name, key)] = cb
                    controls.append(cb)
                elif isinstance(val, list):
                    # For lists like event_hours, comma separated
                    tf = ft.TextField(label=key, value=",".join(map(str, val)), text_size=14, color=TEXT_COLOR)
                    self.inputs[(section_name, key)] = tf
                    controls.append(tf)
                else:
                    # String or int
                    tf = ft.TextField(label=key, value=str(val), text_size=14, color=TEXT_COLOR)
                    self.inputs[(section_name, key)] = tf
                    controls.append(tf)
            
            sections.append(
                ft.Column(
                    [section_title, ft.Column(controls, spacing=10)],
                    spacing=15
                )
            )
        
        save_btn = ft.ElevatedButton("Save Settings", on_click=self.save_settings, bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE)
        info_txt = ft.Text("Note: You must restart the application for these changes to take effect.", color=LABEL_COLOR, size=12)

        self.content = ft.ListView(
            controls=sections + [ft.Container(height=20), save_btn, info_txt],
            expand=True,
            spacing=30
        )

    def save_settings(self, e):
        # Update _cfg from inputs
        has_errors = False
        
        for (section, key), control in self.inputs.items():
            if isinstance(control, ft.Switch):
                _cfg[section][key] = control.value
            else:
                val_str = control.value
                # Try to cast to appropriate type
                orig_val = _cfg[section][key]
                if isinstance(orig_val, int):
                    try:
                        _cfg[section][key] = int(val_str)
                    except ValueError:
                        has_errors = True
                elif isinstance(orig_val, list):
                    # parse comma separated ints
                    try:
                        _cfg[section][key] = [int(x.strip()) for x in val_str.split(",") if x.strip()]
                    except ValueError:
                        has_errors = True
                else:
                    _cfg[section][key] = val_str
        
        if has_errors:
            self.main_page.snack_bar = ft.SnackBar(
                ft.Text("Some settings failed to save due to invalid formatting (e.g. text in a number field).", color=ft.Colors.WHITE),
                bgcolor=ft.Colors.RED_700
            )
        else:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(_cfg, f, indent=4)
            self.main_page.snack_bar = ft.SnackBar(ft.Text("Settings saved! Please restart the app."))
            
        self.main_page.snack_bar.open = True
        self.main_page.update()
