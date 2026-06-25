import flet as ft
from datetime import date, timedelta
from libs.database import get_events_for_day, add_event as db_add_event
from libs.constants import BOX_COLOR, RADIUS, HOUR_HEIGHT, LABEL_WIDTH, LABEL_COLOR, LINE_COLOR, EVENT_HOURS, GRID_ITEM_COUNT
from libs.helpers import parse_dt_safe
from libs.event import Event


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

    def refresh_events(self, open_event_id=None):
        while len(self.event_stack.controls) > GRID_ITEM_COUNT:
            self.event_stack.controls.pop()

        for ev_data in get_events_for_day(self.current_date):
            event_obj = Event(timeline=self, event_data=ev_data)
            self.event_stack.controls.append(event_obj.widget)
            if open_event_id and ev_data["id"] == open_event_id:
                event_obj._on_tap(None)
        self.update()

    def add_new_event(self):
        existing = get_events_for_day(self.current_date)
        hour = EVENT_HOURS[len(existing) % len(EVENT_HOURS)]
        event_num = len(existing) + 1

        start_dt = f"{self.current_date} {hour:02d}:00:00"
        end_dt = (parse_dt_safe(start_dt) + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")

        event_id = db_add_event(f"New Event {event_num}", start_dt, end_dt, "EVENT", "BLUE_700")
        self.refresh_events(open_event_id=event_id)
