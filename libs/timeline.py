import flet as ft
from datetime import date, datetime, timedelta
from calendar import monthrange
from libs.database import (
    get_events_for_day,
    add_event as db_add_event,
    get_reminders_for_day,
    add_reminder as db_add_reminder,
    delete_reminder as db_delete_reminder,
    update_reminder as db_update_reminder,
)
from libs.constants import BOX_COLOR, RADIUS, HOUR_HEIGHT, LABEL_WIDTH, LABEL_COLOR, LINE_COLOR, TEXT_COLOR, EVENT_HOURS
from libs.helpers import parse_dt_safe
from libs.event import Event


class TimedReminder:
    def __init__(self, timeline, reminder_data: dict, top_pos: float, is_multiday: bool = False):
        self.timeline = timeline
        self.reminder_data = reminder_data
        self._top = top_pos
        self.is_multiday = is_multiday
        self.color_name = reminder_data.get("color", "AMBER_700")
        self.color = getattr(ft.Colors, self.color_name, ft.Colors.AMBER_700)
        self._max_top = 24 * HOUR_HEIGHT - 24
        self._drag_initial_top = 0
        self._is_dragging = False
        
        self.container = None
        self._build_widget()

    def _build_widget(self):
        rem_dt = parse_dt_safe(self.reminder_data["reminder_dt"])
        time_str = rem_dt.strftime("%H:%M")
        
        card_body = ft.Container(
            bgcolor=ft.Colors.with_opacity(0.15, self.color),
            border=ft.Border(left=ft.BorderSide(3, self.color)),
            border_radius=4,
            content=ft.Row([
                ft.Icon(ft.Icons.ALARM, size=11, color=self.color),
                ft.Text(
                    f"{time_str} {self.reminder_data['title']}",
                    size=10,
                    color=TEXT_COLOR,
                    overflow=ft.TextOverflow.ELLIPSIS,
                    weight=ft.FontWeight.W_500,
                ),
            ], spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.Padding(6, 0, 6, 0),
            expand=True,
        )

        gesture = ft.GestureDetector(
            content=card_body,
            mouse_cursor=ft.MouseCursor.MOVE,
            on_tap=lambda e: self.timeline._on_reminder_tap(self.reminder_data, e),
            on_pan_start=self._on_drag_start,
            on_pan_update=self._on_drag_update,
            on_pan_end=self._on_drag_end,
            expand=True,
        )

        self.container = ft.Container(
            top=self._top,
            left=5 if self.is_multiday else None,
            right=5 if self.is_multiday else 10,
            width=None if self.is_multiday else 120,
            height=24,
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
        if not self._is_dragging:
            return
        # Snap to 5-minute interval
        snap_px = HOUR_HEIGHT / 12  # 5 minutes
        snapped = round(self.container.top / snap_px) * snap_px
        self.container.top = max(0, min(snapped, self._max_top))

        total_mins = round(self.container.top * 60 / HOUR_HEIGHT / 5) * 5
        new_hour = total_mins // 60
        new_min = total_mins % 60

        rem_dt_obj = parse_dt_safe(self.reminder_data["reminder_dt"])
        new_dt = rem_dt_obj.replace(hour=new_hour, minute=new_min)
        new_dt_str = new_dt.strftime("%Y-%m-%d %H:%M:%S")

        db_update_reminder(self.reminder_data["id"], reminder_dt=new_dt_str)
        self.timeline.refresh_events()


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
            # Lower the 00:00 label slightly so it is not cut off by the top border
            label_top = y + 2 if hour == 0 else y - 6
            grid_controls.append(ft.Text(f"{hour:02d}:00", top=label_top, left=4, size=10, color=LABEL_COLOR))
            grid_controls.append(ft.Container(top=y, left=LABEL_WIDTH, right=0, height=1, bgcolor=LINE_COLOR))

        self.grid_stack = ft.Stack(controls=grid_controls, height=24 * HOUR_HEIGHT)
        self.event_stack = ft.Stack(controls=[], height=24 * HOUR_HEIGHT)
        
        self.combined_stack = ft.Stack(
            controls=[self.grid_stack, self.event_stack],
            height=24 * HOUR_HEIGHT
        )

        self.reminder_row = ft.Row(wrap=True, spacing=6, run_spacing=6)
        self.reminder_section = ft.Container(
            visible=False,
            padding=ft.Padding(LABEL_WIDTH + 8, 8, 12, 8),
            border=ft.Border(bottom=ft.BorderSide(1, LINE_COLOR)),
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.ALARM, size=14, color=LABEL_COLOR),
                    ft.Text("All-Day Reminders", size=11, color=LABEL_COLOR, weight=ft.FontWeight.BOLD),
                ], spacing=6),
                self.reminder_row,
            ], spacing=6),
        )

        self.list_view = ft.ListView(
            controls=[self.reminder_section, self.combined_stack],
            expand=True,
            spacing=0,
        )

        self.date_text = ft.Text(self.current_date.strftime("%B %d, %Y"), size=16, weight=ft.FontWeight.BOLD, color=TEXT_COLOR)

        def prev_date(e):
            v = self.view_dropdown.value
            if v == "Day":
                self.current_date -= timedelta(days=1)
            elif v == "3 Days":
                self.current_date -= timedelta(days=3)
            elif v == "Week":
                self.current_date -= timedelta(days=7)
            elif v == "Month":
                curr_month = self.current_date.month
                curr_year = self.current_date.year
                if curr_month == 1:
                    self.current_date = self.current_date.replace(year=curr_year - 1, month=12)
                else:
                    try:
                        self.current_date = self.current_date.replace(month=curr_month - 1)
                    except ValueError:
                        self.current_date = self.current_date.replace(month=curr_month - 1, day=28)
            self.update_header()
            self.refresh_events()
            try:
                self.update()
            except RuntimeError:
                pass

        def next_date(e):
            v = self.view_dropdown.value
            if v == "Day":
                self.current_date += timedelta(days=1)
            elif v == "3 Days":
                self.current_date += timedelta(days=3)
            elif v == "Week":
                self.current_date += timedelta(days=7)
            elif v == "Month":
                curr_month = self.current_date.month
                curr_year = self.current_date.year
                if curr_month == 12:
                    self.current_date = self.current_date.replace(year=curr_year + 1, month=1)
                else:
                    try:
                        self.current_date = self.current_date.replace(month=curr_month + 1)
                    except ValueError:
                        self.current_date = self.current_date.replace(month=curr_month + 1, day=28)
            self.update_header()
            self.refresh_events()
            try:
                self.update()
            except RuntimeError:
                pass

        def on_view_changed(e):
            self.update_header()
            self.refresh_events()
            try:
                self.update()
            except RuntimeError:
                pass

        self.view_dropdown = ft.Dropdown(
            value="Day",
            options=[
                ft.dropdown.Option("Day"),
                ft.dropdown.Option("3 Days"),
                ft.dropdown.Option("Week"),
                ft.dropdown.Option("Month"),
            ],
            width=100,
            text_size=12,
            height=40,
            content_padding=10,
        )
        self.view_dropdown.on_change = on_view_changed

        self.header = ft.Container(
            padding=ft.Padding(10, 10, 10, 5),
            content=ft.Row([
                ft.Row([
                    ft.IconButton(icon=ft.Icons.CHEVRON_LEFT, on_click=prev_date, icon_color=TEXT_COLOR),
                    self.date_text,
                    ft.IconButton(icon=ft.Icons.CHEVRON_RIGHT, on_click=next_date, icon_color=TEXT_COLOR),
                ], alignment=ft.MainAxisAlignment.START),
                self.view_dropdown
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        )

        self.column_headers_row = ft.Row(
            spacing=0,
            visible=False,
            height=30,
        )

        self.month_grid = ft.Column(spacing=5, expand=True)
        self.month_container = ft.Container(
            content=self.month_grid,
            visible=False,
            expand=True,
            padding=10,
        )

        self.content = ft.Column([
            self.header,
            self.column_headers_row,
            self.list_view,
            self.month_container
        ], expand=True, spacing=0)

    def update_header(self):
        v = self.view_dropdown.value
        if v == "Day":
            self.date_text.value = self.current_date.strftime("%B %d, %Y")
        elif v == "3 Days":
            end_date = self.current_date + timedelta(days=2)
            if self.current_date.year == end_date.year:
                self.date_text.value = f"{self.current_date.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')}"
            else:
                self.date_text.value = f"{self.current_date.strftime('%b %d, %Y')} - {end_date.strftime('%b %d, %Y')}"
        elif v == "Week":
            end_date = self.current_date + timedelta(days=6)
            if self.current_date.year == end_date.year:
                self.date_text.value = f"{self.current_date.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')}"
            else:
                self.date_text.value = f"{self.current_date.strftime('%b %d, %Y')} - {end_date.strftime('%b %d, %Y')}"
        elif v == "Month":
            self.date_text.value = self.current_date.strftime("%B %Y")
        try:
            self.date_text.update()
        except RuntimeError:
            pass

    def refresh_events(self, open_event_id=None):
        self.event_stack.controls.clear()
        v = self.view_dropdown.value
        
        if v == "Month":
            self.list_view.visible = False
            self.column_headers_row.visible = False
            self.month_container.visible = True
            try:
                self.list_view.update()
                self.column_headers_row.update()
                self.month_container.update()
            except RuntimeError:
                pass
            self.render_month_grid()
            return
            
        self.list_view.visible = True
        self.month_container.visible = False
        try:
            self.list_view.update()
            self.month_container.update()
        except RuntimeError:
            pass

        is_multiday = v in ["3 Days", "Week"]
        num_days = 3 if v == "3 Days" else (7 if v == "Week" else 1)

        # Build column headers
        self.column_headers_row.controls.clear()
        if is_multiday:
            self.column_headers_row.controls.append(ft.Container(width=LABEL_WIDTH))
            for d_idx in range(num_days):
                d = self.current_date + timedelta(days=d_idx)
                header_text = d.strftime("%a %d")
                is_today = d == date.today()
                text_color = ft.Colors.BLUE_400 if is_today else TEXT_COLOR
                self.column_headers_row.controls.append(
                    ft.Container(
                        content=ft.Text(header_text, size=11, color=text_color, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                        expand=True,
                        alignment=ft.alignment.Alignment(0, 0),
                        border=ft.Border(bottom=ft.BorderSide(2, ft.Colors.BLUE_400 if is_today else ft.Colors.TRANSPARENT))
                    )
                )
            self.column_headers_row.visible = True
        else:
            self.column_headers_row.visible = False
        try:
            self.column_headers_row.update()
        except RuntimeError:
            pass

        # Gather all-day reminders
        all_day_rems = []
        for d_idx in range(num_days):
            day_date = self.current_date + timedelta(days=d_idx)
            day_reminders = get_reminders_for_day(day_date)
            all_day_rems.extend([r for r in day_reminders if r.get("all_day", 0) == 1])

        if is_multiday:
            # We explicitly define the height to match the timeline height so children stacks and dividers draw fully
            columns_row = ft.Row(left=LABEL_WIDTH, right=0, top=0, bottom=0, height=24 * HOUR_HEIGHT, spacing=0)
            
            for d_idx in range(num_days):
                day_date = self.current_date + timedelta(days=d_idx)
                day_events = get_events_for_day(day_date)
                day_reminders = get_reminders_for_day(day_date)
                day_timed_rems = [r for r in day_reminders if r.get("all_day", 0) == 0]
                
                # Height must be provided for a Stack containing absolute elements
                day_stack = ft.Stack(controls=[], height=24 * HOUR_HEIGHT)
                
                # Render events
                for ev_data in day_events:
                    ev_start = parse_dt_safe(ev_data["start_dt"])
                    ev_end = parse_dt_safe(ev_data["end_dt"])
                    
                    has_overlap = False
                    for rem in day_timed_rems:
                        rem_dt = parse_dt_safe(rem["reminder_dt"])
                        if ev_start <= rem_dt < ev_end:
                            has_overlap = True
                            break
                    
                    event_obj = Event(timeline=self, event_data=ev_data, overlap_right=has_overlap, is_multiday=True)
                    day_stack.controls.append(event_obj.widget)
                    if open_event_id and ev_data["id"] == open_event_id:
                        event_obj._on_tap(None)
                
                # Render timed reminders
                for rem in day_timed_rems:
                    rem_dt = parse_dt_safe(rem["reminder_dt"])
                    top_pos = rem_dt.hour * HOUR_HEIGHT + rem_dt.minute * HOUR_HEIGHT / 60
                    rem_widget = TimedReminder(self, rem, top_pos, is_multiday=True).container
                    day_stack.controls.append(rem_widget)
                
                columns_row.controls.append(
                    ft.Container(
                        content=day_stack,
                        expand=True,
                        border=ft.Border(right=ft.BorderSide(1, LINE_COLOR))
                    )
                )
            
            self.event_stack.controls.append(columns_row)
        else:
            # Single Day layout
            day_events = get_events_for_day(self.current_date)
            day_reminders = get_reminders_for_day(self.current_date)
            day_timed_rems = [r for r in day_reminders if r.get("all_day", 0) == 0]

            for ev_data in day_events:
                ev_start = parse_dt_safe(ev_data["start_dt"])
                ev_end = parse_dt_safe(ev_data["end_dt"])
                
                has_overlap = False
                for rem in day_timed_rems:
                    rem_dt = parse_dt_safe(rem["reminder_dt"])
                    if ev_start <= rem_dt < ev_end:
                        has_overlap = True
                        break
                
                event_obj = Event(timeline=self, event_data=ev_data, overlap_right=has_overlap, is_multiday=False)
                self.event_stack.controls.append(event_obj.widget)
                if open_event_id and ev_data["id"] == open_event_id:
                    event_obj._on_tap(None)

            for rem in day_timed_rems:
                rem_dt = parse_dt_safe(rem["reminder_dt"])
                top_pos = rem_dt.hour * HOUR_HEIGHT + rem_dt.minute * HOUR_HEIGHT / 60
                rem_widget = TimedReminder(self, rem, top_pos, is_multiday=False).container
                self.event_stack.controls.append(rem_widget)

        # Render All Day section
        if all_day_rems:
            cards = [self._build_all_day_reminder_card(rem) for rem in all_day_rems]
            self.reminder_row.controls = cards
            self.reminder_section.visible = True
        else:
            self.reminder_section.visible = False

        try:
            self.event_stack.update()
            self.reminder_section.update()
        except RuntimeError:
            pass

    def render_month_grid(self):
        self.month_grid.controls.clear()
        
        # Grid Headers
        weekdays = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        headers = ft.Row(
            controls=[
                ft.Container(
                    content=ft.Text(w, size=11, color=LABEL_COLOR, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                    expand=True,
                    alignment=ft.alignment.Alignment(0, 0)
                ) for w in weekdays
            ],
            spacing=5
        )
        self.month_grid.controls.append(headers)
        
        year = self.current_date.year
        month = self.current_date.month
        first_day_weekday, num_days = monthrange(year, month)
        
        # Adjust Sun=0 to Sat=6 (first_day_weekday is Mon=0 to Sun=6)
        start_offset = (first_day_weekday + 1) % 7
        first_day_of_month = date(year, month, 1)
        grid_start = first_day_of_month - timedelta(days=start_offset)
        
        for r_idx in range(6):
            row_controls = []
            for c_idx in range(7):
                cell_date = grid_start + timedelta(days=r_idx * 7 + c_idx)
                is_curr_month = cell_date.month == month
                is_today = cell_date == date.today()
                
                day_events = get_events_for_day(cell_date)
                day_reminders = get_reminders_for_day(cell_date)
                
                mixed_items = []
                for ev in day_events:
                    mixed_items.append((ev["title"], ev.get("color", "BLUE_700"), "E"))
                for rem in day_reminders:
                    mixed_items.append((rem["title"], rem.get("color", "AMBER_700"), "R"))
                
                indicators = []
                for title, color_name, item_type in mixed_items[:3]:
                    color = getattr(ft.Colors, color_name, ft.Colors.BLUE_700)
                    prefix = "• " if item_type == "E" else "⏰ "
                    indicators.append(
                        ft.Container(
                            content=ft.Text(f"{prefix}{title}", size=8, color=TEXT_COLOR, overflow=ft.TextOverflow.ELLIPSIS, max_lines=1),
                            bgcolor=ft.Colors.with_opacity(0.15, color),
                            border_radius=2,
                            padding=ft.Padding(4, 1, 4, 1),
                        )
                    )
                
                lbl_color = TEXT_COLOR if is_curr_month else LABEL_COLOR
                lbl_weight = ft.FontWeight.BOLD if is_today else ft.FontWeight.NORMAL
                lbl_bg = ft.Colors.BLUE_700 if is_today else ft.Colors.TRANSPARENT
                
                day_num_btn = ft.Container(
                    content=ft.Text(str(cell_date.day), size=10, color=ft.Colors.WHITE if is_today else lbl_color, weight=lbl_weight),
                    width=18,
                    height=18,
                    bgcolor=lbl_bg,
                    border_radius=9,
                    alignment=ft.alignment.Alignment(0, 0)
                )
                
                cell_content = ft.Column(
                    [
                        ft.Row([day_num_btn], alignment=ft.MainAxisAlignment.END),
                        ft.Column(indicators, spacing=2, expand=True, scroll=ft.ScrollMode.HIDDEN)
                    ],
                    spacing=4,
                    tight=True
                )
                
                def on_cell_click(e, d=cell_date):
                    self.current_date = d
                    self.view_dropdown.value = "Day"
                    self.update_header()
                    self.refresh_events()
                    self.view_dropdown.update()

                row_controls.append(
                    ft.Container(
                        content=cell_content,
                        expand=True,
                        bgcolor=BOX_COLOR if is_curr_month else ft.Colors.with_opacity(0.03, BOX_COLOR),
                        border=ft.Border.all(1, LINE_COLOR),
                        border_radius=4,
                        padding=5,
                        on_click=lambda e, d=cell_date: on_cell_click(e, d),
                    )
                )
            
            self.month_grid.controls.append(ft.Row(row_controls, spacing=5, expand=True))
        
        self.month_container.update()

    def _build_all_day_reminder_card(self, reminder_data):
        color_name = reminder_data.get("color", "AMBER_700")
        color = getattr(ft.Colors, color_name, ft.Colors.AMBER_700)
        
        v = self.view_dropdown.value
        is_multiday = v in ["3 Days", "Week"]
        title_prefix = ""
        if is_multiday:
            rem_dt = parse_dt_safe(reminder_data["reminder_dt"])
            title_prefix = f"{rem_dt.strftime('%b %d')}: "

        return ft.Container(
            content=ft.Row([
                ft.Container(width=3, height=14, bgcolor=color, border_radius=1),
                ft.Icon(ft.Icons.ALARM, size=11, color=color),
                ft.Text(f"{title_prefix}{reminder_data['title']}", size=11, color=TEXT_COLOR, weight=ft.FontWeight.W_500),
            ], spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=ft.Colors.with_opacity(0.12, color),
            border_radius=6,
            padding=ft.Padding(8, 4, 8, 4),
            on_click=lambda e, rd=reminder_data: self._on_reminder_tap(rd, e),
        )

    def _on_reminder_tap(self, reminder_data, e):
        def delete(e):
            db_delete_reminder(reminder_data["id"])
            dlg.open = False
            self.main_page.update()
            self.refresh_events()

        def close(e):
            dlg.open = False
            self.main_page.update()

        is_all_day = reminder_data.get("all_day", 0) == 1
        rem_dt = parse_dt_safe(reminder_data["reminder_dt"])
        if is_all_day:
            time_display = f"Date: {rem_dt.strftime('%b %d, %Y')} (All Day)"
        else:
            time_display = f"Time: {rem_dt.strftime('%b %d, %Y at %H:%M')}"

        dlg = ft.AlertDialog(
            title=ft.Text(reminder_data["title"]),
            content=ft.Text(time_display),
            actions=[
                ft.Row([
                    ft.TextButton("Delete", on_click=delete, style=ft.ButtonStyle(color=ft.Colors.RED_400)),
                    ft.TextButton("Close", on_click=close),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ],
        )
        self.main_page.overlay.append(dlg)
        dlg.open = True
        self.main_page.update()

    def add_new_reminder(self):
        selected_date = self.current_date
        now = datetime.now()
        default_hour = (now.hour + 1) % 24
        selected_time = now.replace(hour=default_hour, minute=0, second=0, microsecond=0).time()
        selected_color = "AMBER_700"

        title_tf = ft.TextField(
            label="Title",
            autofocus=True,
            border_color=ft.Colors.GREY_700,
            cursor_color=ft.Colors.WHITE,
        )

        all_day_cb = ft.Checkbox(
            label="All day",
            value=False,
            fill_color=ft.Colors.BLUE_700,
        )

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

        def on_time_selected(e):
            nonlocal selected_time
            if e.control.value:
                selected_time = e.control.value
                time_btn.content = ft.Text(selected_time.strftime("%H:%M"))
                time_btn.update()

        time_picker = ft.TimePicker(value=selected_time, on_change=on_time_selected)
        self.main_page.overlay.append(time_picker)

        def show_time_picker(e):
            time_picker.open = True
            self.main_page.update()

        time_btn = ft.OutlinedButton(
            content=ft.Text(selected_time.strftime("%H:%M")),
            icon=ft.Icons.ACCESS_TIME,
            on_click=show_time_picker,
        )

        def on_all_day_changed(e):
            time_btn.visible = not all_day_cb.value
            time_btn.update()

        all_day_cb.on_change = on_all_day_changed

        colors_list = ["AMBER_700", "RED_700", "BLUE_700", "GREEN_700", "PURPLE_700"]
        color_row = ft.Row(spacing=8)

        def select_color(e, color_name):
            nonlocal selected_color
            selected_color = color_name
            for child in color_row.controls:
                child.border = ft.Border.all(2, ft.Colors.WHITE if child.key == selected_color else ft.Colors.TRANSPARENT)
            color_row.update()

        for c in colors_list:
            is_selected = (c == selected_color)
            color_row.controls.append(
                ft.Container(
                    key=c, width=24, height=24,
                    bgcolor=getattr(ft.Colors, c),
                    border_radius=12,
                    border=ft.Border.all(2, ft.Colors.WHITE if is_selected else ft.Colors.TRANSPARENT),
                    on_click=lambda e, col=c: select_color(e, col),
                )
            )

        def remove_pickers():
            if date_picker in self.main_page.overlay:
                date_picker.open = False
                self.main_page.overlay.remove(date_picker)
            if time_picker in self.main_page.overlay:
                time_picker.open = False
                self.main_page.overlay.remove(time_picker)

        def close_dlg(e):
            remove_pickers()
            dlg.open = False
            self.main_page.update()

        def save(e):
            is_all_day = 1 if all_day_cb.value else 0
            rem_time = selected_time if not all_day_cb.value else datetime.min.time()
            reminder_dt = datetime.combine(selected_date, rem_time).strftime("%Y-%m-%d %H:%M:%S")
            db_add_reminder(title_tf.value or "Reminder", reminder_dt, selected_color, is_all_day)
            remove_pickers()
            dlg.open = False
            self.main_page.update()
            self.refresh_events()

        dlg = ft.AlertDialog(
            title=ft.Text("New Reminder"),
            content=ft.Column([
                title_tf,
                all_day_cb,
                ft.Text("Date & Time:", weight=ft.FontWeight.BOLD),
                date_btn,
                time_btn,
                ft.Text("Color:", weight=ft.FontWeight.BOLD),
                color_row,
            ], width=300, spacing=10, tight=True),
            actions=[
                ft.Row([
                    ft.TextButton("Cancel", on_click=close_dlg),
                    ft.TextButton("Save", on_click=save),
                ], alignment=ft.MainAxisAlignment.END, spacing=4),
            ],
        )
        self.main_page.overlay.append(dlg)
        dlg.open = True
        self.main_page.update()

    def add_new_event(self):
        existing = get_events_for_day(self.current_date)
        hour = EVENT_HOURS[len(existing) % len(EVENT_HOURS)]
        event_num = len(existing) + 1

        start_dt = f"{self.current_date} {hour:02d}:00:00"
        end_dt = (parse_dt_safe(start_dt) + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")

        event_id = db_add_event(f"New Event {event_num}", start_dt, end_dt, "EVENT", "BLUE_700")
        self.refresh_events(open_event_id=event_id)
