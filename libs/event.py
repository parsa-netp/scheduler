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
            content=ft.Row(
                [
                    ft.Container(width=3, bgcolor=TEXT_COLOR, border_radius=1),
                    text_column,
                ],
                spacing=6,
            ),
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

        curr_title = self.event_data["title"]
        curr_desc = self.event_data.get("description", "")
        curr_color = self.event_data.get("color", "BLUE_700")
        curr_icon = self.event_data.get("icon", "EVENT")
        
        start_time = parse_dt_safe(self.event_data["start_dt"])
        end_time = parse_dt_safe(self.event_data["end_dt"])
        
        selected_date = start_time.date()
        selected_start_time = start_time.time()
        selected_end_time = end_time.time()

        title_tf = ft.TextField(
            label="Title",
            value=curr_title,
            autofocus=True,
            border_color=ft.Colors.GREY_700,
            cursor_color=ft.Colors.WHITE,
        )
        desc_tf = ft.TextField(
            label="Description",
            value=curr_desc,
            multiline=True,
            min_lines=2,
            max_lines=3,
            border_color=ft.Colors.GREY_700,
            cursor_color=ft.Colors.WHITE,
        )

        # Modern Pickers & Handlers
        def on_date_selected(e):
            nonlocal selected_date
            if e.control.value:
                selected_date = e.control.value.date()
                date_btn.content = ft.Text(selected_date.strftime("%b %d, %Y"))
                date_btn.update()

        date_picker = ft.DatePicker(
            value=datetime.combine(selected_date, datetime.min.time()),
            on_change=on_date_selected,
        )
        self.main_page.overlay.append(date_picker)

        def show_date_picker(e):
            date_picker.open = True
            self.main_page.update()

        date_btn = ft.OutlinedButton(
            content=ft.Text(selected_date.strftime("%b %d, %Y")),
            icon=ft.Icons.CALENDAR_MONTH,
            on_click=show_date_picker,
        )

        def on_start_time_selected(e):
            nonlocal selected_start_time
            if e.control.value:
                selected_start_time = e.control.value
                start_time_btn.content = ft.Text(selected_start_time.strftime("%H:%M"))
                start_time_btn.update()

        start_time_picker = ft.TimePicker(
            value=selected_start_time,
            on_change=on_start_time_selected,
        )
        self.main_page.overlay.append(start_time_picker)

        def show_start_picker(e):
            start_time_picker.open = True
            self.main_page.update()

        start_time_btn = ft.OutlinedButton(
            content=ft.Text(selected_start_time.strftime("%H:%M")),
            icon=ft.Icons.ACCESS_TIME,
            on_click=show_start_picker,
        )

        def on_end_time_selected(e):
            nonlocal selected_end_time
            if e.control.value:
                selected_end_time = e.control.value
                end_time_btn.content = ft.Text(selected_end_time.strftime("%H:%M"))
                end_time_btn.update()

        end_time_picker = ft.TimePicker(
            value=selected_end_time,
            on_change=on_end_time_selected,
        )
        self.main_page.overlay.append(end_time_picker)

        def show_end_picker(e):
            end_time_picker.open = True
            self.main_page.update()

        end_time_btn = ft.OutlinedButton(
            content=ft.Text(selected_end_time.strftime("%H:%M")),
            icon=ft.Icons.ACCESS_TIME,
            on_click=show_end_picker,
        )

        date_row = ft.Row([
            ft.Text("Date:", width=80, weight=ft.FontWeight.BOLD),
            date_btn,
        ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER)

        start_row = ft.Row([
            ft.Text("Start Time:", width=80, weight=ft.FontWeight.BOLD),
            start_time_btn,
        ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER)

        end_row = ft.Row([
            ft.Text("End Time:", width=80, weight=ft.FontWeight.BOLD),
            end_time_btn,
        ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER)

        # Color Selector
        colors_list = ["BLUE_700", "RED_700", "GREEN_700", "AMBER_700", "PURPLE_700", "TEAL_700", "PINK_700", "INDIGO_700"]
        color_row = ft.Row(spacing=8)
        
        def select_color(e, color_name):
            nonlocal curr_color
            curr_color = color_name
            for child in color_row.controls:
                child.border = ft.Border.all(2, ft.Colors.WHITE if child.key == curr_color else ft.Colors.TRANSPARENT)
            color_row.update()

        for c in colors_list:
            is_selected = (c == curr_color)
            color_row.controls.append(
                ft.Container(
                    key=c,
                    width=28,
                    height=28,
                    bgcolor=getattr(ft.Colors, c),
                    border_radius=14,
                    border=ft.Border.all(2, ft.Colors.WHITE if is_selected else ft.Colors.TRANSPARENT),
                    on_click=lambda e, col=c: select_color(e, col),
                    tooltip=c.replace("_", " ").title(),
                )
            )

        # Icon Selector
        icons_list = ["EVENT", "WORK", "MEETING", "STUDY", "PERSONAL", "ALARM"]
        icon_row = ft.Row(spacing=8)

        def select_icon(e, icon_name):
            nonlocal curr_icon
            curr_icon = icon_name
            for child in icon_row.controls:
                is_sel = (child.key == curr_icon)
                child.bgcolor = ft.Colors.BLUE_700 if is_sel else ft.Colors.GREY_800
                child.icon_color = ft.Colors.WHITE if is_sel else ft.Colors.GREY_400
            icon_row.update()

        for ico in icons_list:
            is_selected = (ico == curr_icon)
            icon_row.controls.append(
                ft.IconButton(
                    key=ico,
                    icon=EVENT_ICONS[ico],
                    icon_size=18,
                    bgcolor=ft.Colors.BLUE_700 if is_selected else ft.Colors.GREY_800,
                    icon_color=ft.Colors.WHITE if is_selected else ft.Colors.GREY_400,
                    on_click=lambda e, idx=ico: select_icon(e, idx),
                    tooltip=ico.title(),
                )
            )

        error_txt = ft.Text("", color=ft.Colors.RED_400, size=12, visible=False)

        def remove_pickers():
            if date_picker in self.main_page.overlay:
                date_picker.open = False
                self.main_page.overlay.remove(date_picker)
            if start_time_picker in self.main_page.overlay:
                start_time_picker.open = False
                self.main_page.overlay.remove(start_time_picker)
            if end_time_picker in self.main_page.overlay:
                end_time_picker.open = False
                self.main_page.overlay.remove(end_time_picker)

        def close_dlg(_):
            remove_pickers()
            dlg.open = False
            self.main_page.update()

        def delete_ev(_):
            remove_pickers()
            delete_event(self.event_data["id"])
            dlg.open = False
            self.main_page.update()
            self.timeline.refresh_events()

        def save_ev(_):
            nonlocal curr_color, curr_icon, selected_date, selected_start_time, selected_end_time
            
            start_dt = datetime.combine(selected_date, selected_start_time)
            end_dt = datetime.combine(selected_date, selected_end_time)

            if end_dt <= start_dt:
                error_txt.value = "Error: End time must be after start time."
                error_txt.visible = True
                error_txt.update()
                return

            new_start_dt = start_dt.strftime("%Y-%m-%d %H:%M:%S")
            new_end_dt = end_dt.strftime("%Y-%m-%d %H:%M:%S")

            update_event(
                self.event_data["id"],
                title_tf.value or "Untitled Event",
                new_start_dt,
                new_end_dt,
                curr_icon,
                curr_color,
                desc_tf.value
            )

            remove_pickers()
            dlg.open = False
            self.main_page.update()
            self.timeline.refresh_events()

        dlg = ft.AlertDialog(
            title=ft.Text("Edit Event"),
            content=ft.Column([
                title_tf,
                desc_tf,
                ft.Text("Category / Icon:", weight=ft.FontWeight.BOLD),
                icon_row,
                ft.Text("Color:", weight=ft.FontWeight.BOLD),
                color_row,
                date_row,
                start_row,
                end_row,
                error_txt,
            ], width=350, spacing=12, tight=True, scroll=ft.ScrollMode.AUTO),
            actions=[
                ft.Row(
                    [
                        ft.TextButton("Delete", on_click=delete_ev, style=ft.ButtonStyle(color=ft.Colors.RED_400)),
                        ft.Row(
                            [
                                ft.TextButton("Cancel", on_click=close_dlg),
                                ft.TextButton("Save", on_click=save_ev),
                            ],
                            spacing=4,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                )
            ],
        )
        self.main_page.overlay.append(dlg)
        dlg.open = True
        self.main_page.update()

    @property
    def widget(self):
        return self.container
