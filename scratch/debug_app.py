import flet as ft
from libs.database import init_db, add_event, get_all_events
from libs.timeline import Timeline
from libs.event import Event

def main(page: ft.Page):
    init_db()
    # Add a mock event if none exist
    events = get_all_events()
    if not events:
        add_event("Test Event", "2026-06-25 09:00:00", "2026-06-25 10:00:00")
        events = get_all_events()
    
    my_timeline = Timeline(page)
    # MUST add it to page so it has a reference to page
    page.add(my_timeline)
    
    event_data = events[0]
    event_obj = Event(my_timeline, event_data)
    
    # Try to open tap dialog
    print("Opening tap dialog...")
    event_obj._on_tap(None)
    print("Dialog opened successfully!")
    page.update()

ft.run(main)
