import re
import flet as ft
from datetime import date, datetime, timedelta
from database import (
    add_event as db_add_event,
    get_events_for_day,
    update_event,
    delete_event,
    init_db,
    get_all_notes,
    add_note,
    get_note_by_id,
    update_note,
    delete_note,
)


def parse_dt_safe(dt_str: str) -> datetime:
    if " 24:00:00" in dt_str:
        dt_str = dt_str.replace(" 24:00:00", " 00:00:00")
        return datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S") + timedelta(days=1)
    return datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")


# --- CONSTANTS ---
PAGE_COLOR = ft.Colors.GREY_900
WINDOW_COLOR = ft.Colors.BLACK
BOX_COLOR = ft.Colors.GREY_800
TEXT_COLOR = ft.Colors.WHITE
LINE_COLOR = ft.Colors.GREY_700
LABEL_COLOR = ft.Colors.GREY_500
PADDING = 15
RADIUS = 10
HOUR_HEIGHT = 55
LABEL_WIDTH = 40
EVENT_HOURS = [9, 10, 14, 15, 16]
GRID_ITEM_COUNT = 48


# --- EVENT CLASS (The Child) ---

class Event:
    def __init__(self, timeline, event_data: dict):
        self.timeline = timeline
        self.main_page = timeline.main_page
        self.event_data = event_data

        self.start = parse_dt_safe(event_data["start_dt"])
        self.end = parse_dt_safe(event_data["end_dt"])

        self.color = getattr(ft.Colors, event_data.get("color", "BLUE_700"), ft.Colors.BLUE_700)
        self.duration_hours = max(1, (self.end - self.start).seconds / 3600)
        self._top = self.start.hour * HOUR_HEIGHT + self.start.minute * HOUR_HEIGHT / 60
        self._max_top = (24 * 60 - self.duration_hours * 60) * HOUR_HEIGHT / 60

        self._drag_initial_top = 0
        self._is_dragging = False

        self.container: ft.Container = None
        self._build_widget()

    def _build_widget(self):
        card_body = ft.Container(
            content=ft.Text(self.event_data["title"], color=ft.Colors.WHITE, size=13, weight=ft.FontWeight.BOLD),
            bgcolor=self.color,
            border_radius=6,
            padding=ft.Padding(8, 4, 8, 4),
            expand=True,
        )

        gesture = ft.GestureDetector(
            content=card_body,
            mouse_cursor=ft.MouseCursor.MOVE,
            on_tap=self._on_tap,
            on_pan_start=self._on_drag_start,
            on_pan_update=self._on_drag_update,
            on_pan_end=self._on_drag_end,
            expand=True,
        )

        self.container = ft.Container(
            top=self._top,
            left=LABEL_WIDTH,
            right=0,
            height=HOUR_HEIGHT * self.duration_hours,
            content=gesture,
            padding=0,
        )

    def _on_drag_start(self, e):
        self._drag_initial_top = self.container.top
        self._is_dragging = False

    def _on_drag_update(self, e):
        delta = e.global_delta.y if e.global_delta else 0
        if abs(delta) > 5:
            self._is_dragging = True
        if self._is_dragging:
            new_top = self._drag_initial_top + delta
            self.container.top = max(0, min(new_top, self._max_top))
            self.main_page.update()

    def _on_drag_end(self, e):
        if not self._is_dragging: return
        snap_px = HOUR_HEIGHT / 12
        snapped = round(self.container.top / snap_px) * snap_px
        self.container.top = max(0, min(snapped, self._max_top))

        total_mins = round(self.container.top * 60 / HOUR_HEIGHT / 5) * 5
        new_hour = total_mins // 60
        new_min = total_mins % 60

        new_start = f"{self.start.strftime('%Y-%m-%d')} {new_hour:02d}:{new_min:02d}:00"
        new_end = self.start.replace(hour=new_hour, minute=new_min) + timedelta(hours=self.duration_hours)

        update_event(
            self.event_data["id"], self.event_data["title"],
            new_start, new_end.strftime("%Y-%m-%d %H:%M:%S"),
            self.event_data.get("icon", "EVENT"), self.color
        )
        self.timeline.refresh_events()

    def _on_tap(self, _):
        if self._is_dragging: return

        def close_dlg(_):
            dlg.open = False
            self.main_page.update()

        def delete_ev(_):
            delete_event(self.event_data["id"])
            dlg.open = False
            self.timeline.refresh_events()

        dlg = ft.AlertDialog(
            title=ft.Text("Event Details"),
            content=ft.Column([
                ft.Text(f"Title: {self.event_data['title']}"),
            ], width=300, spacing=8),
            actions=[
                ft.TextButton("Delete", on_click=delete_ev),
                ft.TextButton("Close", on_click=close_dlg),
            ],
        )
        self.main_page.overlay.append(dlg)
        dlg.open = True
        self.main_page.update()

    @property
    def widget(self):
        return self.container


# --- TIMELINE CLASS ---

class Timeline(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.main_page = page
        self.current_date = date.today()

        self.bgcolor = BOX_COLOR
        self.border_radius = RADIUS
        self.padding = 0
        self.expand = True

        grid_controls = []
        for hour in range(24):
            y = hour * HOUR_HEIGHT
            grid_controls.append(ft.Text(f"{hour:02d}:00", top=y - 6, left=4, size=10, color=LABEL_COLOR))
            grid_controls.append(ft.Container(top=y, left=LABEL_WIDTH, right=0, height=1, bgcolor=LINE_COLOR))

        self.event_stack = ft.Stack(controls=grid_controls, height=24 * HOUR_HEIGHT)
        self.content = ft.ListView(controls=[self.event_stack], expand=True, spacing=0)

    def refresh_events(self):
        while len(self.event_stack.controls) > GRID_ITEM_COUNT:
            self.event_stack.controls.pop()

        for ev_data in get_events_for_day(self.current_date):
            event_obj = Event(timeline=self, event_data=ev_data)
            self.event_stack.controls.append(event_obj.widget)
        self.update()

    def add_new_event(self):
        existing = get_events_for_day(self.current_date)
        hour = EVENT_HOURS[len(existing) % len(EVENT_HOURS)]
        event_num = len(existing) + 1

        start_dt = f"{self.current_date} {hour:02d}:00:00"
        end_dt = (parse_dt_safe(start_dt) + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")

        db_add_event(f"Event {event_num}", start_dt, end_dt, "EVENT", "BLUE_700")
        self.refresh_events()


# --- NOTEPAD CLASS (Google Keep-style) ---

class Notepad(ft.Container):
    NOTE_COLORS = [
        "GREY_700", "RED_700", "ORANGE_700", "AMBER_700",
        "GREEN_700", "TEAL_700", "BLUE_700", "INDIGO_700",
        "PURPLE_700", "PINK_700",
    ]

    def __init__(self, page: ft.Page):
        super().__init__()
        self.main_page = page
        self.bgcolor = BOX_COLOR
        self.border_radius = RADIUS
        self.padding = 20
        self.expand = True

        self.current_note_id = None
        self.selected_color = "GREY_700"

        self._build_editor()
        self.grid_content = ft.Column(expand=True, spacing=15)

        self.content = ft.Stack(
            expand=True,
            controls=[self.grid_content, self.editor_content],
        )

    def _build_grid(self, notes):
        self.grid_content.visible = True
        self.editor_content.visible = False

        if not notes:
            self.grid_content.controls = [
                ft.Text("Notes", size=22, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("No notes yet", size=18, color=LABEL_COLOR),
                            ft.Text("Tap + to create one", size=14, color=LABEL_COLOR),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    alignment=ft.alignment.Alignment(0, 0),
                    expand=True,
                ),
            ]
            return

        grid_rows = []
        for i in range(0, len(notes), 2):
            chunk = notes[i:i+2]
            row_cards = [ft.Container(content=self._build_note_card(n), expand=True) for n in chunk]
            if len(chunk) == 1:
                row_cards.append(ft.Container(expand=True))
            grid_rows.append(ft.Row(row_cards, spacing=10, vertical_alignment=ft.CrossAxisAlignment.START))

        self.grid_content.controls = [
            ft.Text("Notes", size=22, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
            ft.Column(
                controls=grid_rows,
                expand=True,
                spacing=10,
                scroll=ft.ScrollMode.AUTO,
            ),
        ]

    def refresh_notes(self):
        notes = get_all_notes()
        self._build_grid(notes)

    def _build_editor(self):
        self.title_field = ft.TextField(
            hint_text="Title",
            border=ft.InputBorder.NONE,
            text_size=22,
            text_style=ft.TextStyle(weight=ft.FontWeight.BOLD),
            color=TEXT_COLOR,
            cursor_color=TEXT_COLOR,
            on_change=self._on_edit_changed,
        )

        self.content_field = ft.TextField(
            hint_text="Take a note...",
            multiline=True,
            min_lines=8,
            expand=True,
            border=ft.InputBorder.NONE,
            color=TEXT_COLOR,
            cursor_color=TEXT_COLOR,
            on_change=self._on_edit_changed,
        )

        self.showing_preview = False

        self.preview_markdown = ft.Markdown(
            value="",
            selectable=True,
            extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
            expand=True,
            visible=False,
        )

        color_dots = []
        for c in self.NOTE_COLORS:
            color_dots.append(
                ft.Container(
                    width=28, height=28,
                    bgcolor=getattr(ft.Colors, c),
                    border_radius=14,
                    ink=True,
                    on_click=lambda _, color=c: self._select_color(color),
                )
            )

        back_btn = ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color=TEXT_COLOR, on_click=self._close_editor)
        preview_btn = ft.IconButton(icon=ft.Icons.VISIBILITY, icon_color=TEXT_COLOR, on_click=self._toggle_preview)
        pin_btn = ft.IconButton(icon=ft.Icons.PUSH_PIN, icon_color=TEXT_COLOR, on_click=self._toggle_pin)
        delete_btn = ft.IconButton(icon=ft.Icons.DELETE, icon_color=TEXT_COLOR, on_click=self._delete_note)

        self.editor_content = ft.Column(
            visible=False,
            expand=True,
            spacing=10,
            controls=[
                ft.Row([back_btn, ft.Row([preview_btn, pin_btn, delete_btn], spacing=0)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                self.title_field,
                ft.Divider(height=1, color=LINE_COLOR),
                self.content_field,
                self.preview_markdown,
                ft.Row(color_dots, spacing=8),
            ],
        )

    def _toggle_preview(self, e):
        self.showing_preview = not self.showing_preview
        self.content_field.visible = not self.showing_preview
        self.preview_markdown.value = self.content_field.value
        self.preview_markdown.visible = self.showing_preview
        self.update()

    def _strip_markdown(self, text):
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'\*{1,3}(.*?)\*{1,3}', r'\1', text)
        text = re.sub(r'_(.*?)_', r'\1', text)
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
        text = re.sub(r'`([^`]+)`', r'\1', text)
        text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', r'\1', text)
        text = re.sub(r'^>\s+', '', text, flags=re.MULTILINE)
        return text.strip()

    def _on_edit_changed(self, e):
        if self.current_note_id:
            update_note(
                self.current_note_id,
                title=self.title_field.value,
                content=self.content_field.value,
            )

    def _select_color(self, color):
        self.selected_color = color
        if self.current_note_id:
            update_note(self.current_note_id, color=color)
        self._update_editor_bg()

    def _toggle_pin(self, e):
        if self.current_note_id:
            note = get_note_by_id(self.current_note_id)
            if note:
                update_note(self.current_note_id, pinned=not note["pinned"])

    def _delete_note(self, e):
        if self.current_note_id:
            delete_note(self.current_note_id)
            self.current_note_id = None
            self._close_editor()

    def _update_editor_bg(self):
        bg = getattr(ft.Colors, self.selected_color, ft.Colors.GREY_800)
        self.bgcolor = bg
        self.update()

    def _close_editor(self, e=None):
        self.grid_content.visible = True
        self.editor_content.visible = False
        self.bgcolor = BOX_COLOR
        self.current_note_id = None
        self.refresh_notes()
        self.update()



    def _format_date(self, date_str):
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            return dt.strftime("%b %d, %Y")
        except (ValueError, TypeError):
            return ""

    def _build_note_card(self, note):
        title = note.get("title", "")
        content = note.get("content", "")
        color = note.get("color", "GREY_700")
        pinned = note.get("pinned", 0)
        created_at = note.get("created_at", "")
        bg = getattr(ft.Colors, color, ft.Colors.GREY_700)

        card_controls = []

        if pinned:
            card_controls.append(
                ft.Row([
                    ft.Container(expand=True),
                    ft.Icon(ft.Icons.PUSH_PIN, size=16, color=ft.Colors.WHITE54),
                ])
            )

        if title:
            card_controls.append(
                ft.Text(
                    title, size=15, weight=ft.FontWeight.BOLD, color=TEXT_COLOR,
                    max_lines=2, overflow=ft.TextOverflow.ELLIPSIS,
                )
            )
        else:
            card_controls.append(
                ft.Text(
                    "New note", size=15, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE38,
                    italic=True, max_lines=1,
                )
            )

        if content:
            card_controls.append(
                ft.Text(
                    self._strip_markdown(content), size=13, color=ft.Colors.WHITE70,
                    max_lines=6, overflow=ft.TextOverflow.ELLIPSIS,
                )
            )

        formatted_date = self._format_date(created_at)
        card_controls.append(
            ft.Text(formatted_date, size=11, color=ft.Colors.WHITE38),
        )

        return ft.Container(
            content=ft.Column(card_controls, spacing=4),
            bgcolor=bg,
            border_radius=8,
            padding=12,
            ink=True,
            on_click=lambda _, n=note: self.open_note_editor(n),
        )

    def open_note_editor(self, note):
        self.current_note_id = note["id"]
        self.selected_color = note["color"]
        self.title_field.value = note["title"]
        self.content_field.value = note["content"]
        self._update_editor_bg()

        self.grid_content.visible = False
        self.editor_content.visible = True
        self.update()

    def add_new_note(self):
        note_id = add_note("", "", "GREY_700")
        note = get_note_by_id(note_id)
        if note:
            self.open_note_editor(note)


# --- ROOT ---

def main(page: ft.Page):
    init_db()
    page.bgcolor = PAGE_COLOR
    page.window.bgcolor = WINDOW_COLOR
    page.padding = 0

    my_timeline = Timeline(page)
    my_notepad = Notepad(page)

    viewport = ft.Container(content=my_timeline, expand=True, padding=PADDING)

    add_button = ft.FloatingActionButton(
        icon=ft.Icons.ADD,
        on_click=lambda _: my_timeline.add_new_event(),
        mini=True,
    )

    def change_view(e):
        selected = e.control.selected_index
        if selected == 0:
            viewport.content = my_timeline
            add_button.on_click = lambda _: my_timeline.add_new_event()
            add_button.visible = True
            my_timeline.refresh_events()
        elif selected == 1:
            viewport.content = my_notepad
            add_button.on_click = lambda _: my_notepad.add_new_note()
            add_button.visible = True
            my_notepad.refresh_notes()
        page.update()

    page.navigation_bar = ft.CupertinoNavigationBar(
        bgcolor=ft.Colors.with_opacity(0.25, ft.Colors.GREY_800),
        inactive_color=LABEL_COLOR,
        active_color=TEXT_COLOR,
        on_change=change_view,
        destinations=[
            ft.NavigationBarDestination(
                icon=ft.Icons.CALENDAR_MONTH,
                label="Timeline",
            ),
            ft.NavigationBarDestination(
                icon=ft.Icons.NOTE_ALT,
                label="Notes",
            ),
        ],
    )

    page.add(
        ft.Stack(
            expand=True,
            controls=[
                viewport,
                ft.Container(
                    content=add_button,
                    right=10,
                    bottom=70,
                ),
            ],
        )
    )

    my_timeline.refresh_events()


ft.run(main)