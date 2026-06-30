import flet as ft
from datetime import datetime, timedelta
from libs.database import update_event, delete_event
from libs.helpers import parse_dt_safe
from libs.constants import HOUR_HEIGHT, LABEL_WIDTH


EVENT_ICONS = {
    "EVENT": ft.Icons.EVENT,
    "WORK": ft.Icons.BUSINESS_CENTER,
    "MEETING": ft.Icons.PEOPLE,
    "STUDY": ft.Icons.MENU_BOOK,
    "PERSONAL": ft.Icons.FAVORITE,
    "ALARM": ft.Icons.ACCESS_ALARM,
}


class Event:
    def __init__(self, timeline, event_data: dict, overlap_right: bool = False, is_multiday: bool = False):
        self.timeline = timeline
        self.main_page = timeline.main_page
        self.event_data = event_data
        self.overlap_right = overlap_right
        self.is_multiday = is_multiday

        self.start = parse_dt_safe(event_data["start_dt"])
        self.end = parse_dt_safe(event_data["end_dt"])

        self.color = getattr(ft.Colors, event_data.get("color", "BLUE_700"), ft.Colors.BLUE_700)
        self.duration_hours = max(0.5, (self.end - self.start).total_seconds() / 3600)
        self._top = self.start.hour * HOUR_HEIGHT + self.start.minute * HOUR_HEIGHT / 60
        self._max_top = (24 * 60 - self.duration_hours * 60) * HOUR_HEIGHT / 60

        self._drag_initial_top = 0
        self._is_dragging = False

        self.container: ft.Container = None
        self._build_widget()

    def _build_widget(self):
        icon_name = self.event_data.get("icon", "EVENT")
        icon_src = EVENT_ICONS.get(icon_name, ft.Icons.EVENT)
        description = self.event_data.get("description", "")
        TEXT_COLOR = ft.Colors.WHITE

        text_column = ft.Column(
            spacing=1,
            controls=[
                ft.Row([
                    ft.Icon(icon_src, size=11, color=TEXT_COLOR),
                    ft.Text(self.event_data["title"], size=11, color=TEXT_COLOR, weight=ft.FontWeight.BOLD, overflow=ft.TextOverflow.ELLIPSIS),
                ], spacing=4),
            ],
            expand=True,
        )

        if description:
            text_column.controls.append(
                ft.Text(description, size=9, color=ft.Colors.GREY_300, overflow=ft.TextOverflow.ELLIPSIS, max_lines=1)
            )

        card_body = ft.Container(
            content=text_column,
            bgcolor=self.color,
            border_radius=4,
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
            left=0 if self.is_multiday else LABEL_WIDTH,
            right=10 if self.is_multiday else (140 if self.overlap_right else 0),
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
            self.container.update()

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
            self.event_data.get("icon", "EVENT"), self.event_data.get("color", "BLUE_700"),
            self.event_data.get("description", "")
        )
        self.timeline.refresh_events()

    def _on_tap(self, _):
        if self._is_dragging: return
        from libs.dialogs import show_event_dialog
        show_event_dialog(self, self.main_page)

    @property
    def widget(self):
        return self.container
