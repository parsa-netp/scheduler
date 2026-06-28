import flet as ft
from libs.database import init_db
from libs.constants import (
    PAGE_COLOR,
    WINDOW_COLOR,
    PADDING,
    LABEL_COLOR,
    TEXT_COLOR,
    ADD_BUTTON_MINI,
    ADD_BUTTON_RIGHT,
    ADD_BUTTON_BOTTOM,
)
from libs.timeline import Timeline
from libs.notepad import Notepad
from libs.settings_view import SettingsView


def main(page: ft.Page):
    init_db()
    page.bgcolor = PAGE_COLOR
    page.window.bgcolor = WINDOW_COLOR
    page.padding = 0

    my_timeline = Timeline(page)
    my_notepad = Notepad(page)
    my_settings = SettingsView(page)

    viewport = ft.Container(content=my_timeline, expand=True, padding=PADDING)

    # --- Timeline speed-dial (Event + Reminder) ---
    create_menu_visible = False

    def close_create_menu():
        nonlocal create_menu_visible
        create_menu_visible = False
        create_menu.visible = False
        timeline_fab.icon = ft.Icons.ADD
        timeline_fab.bgcolor = None
        create_menu.update()
        timeline_fab.update()

    def add_event_from_menu(e):
        close_create_menu()
        my_timeline.add_new_event()

    def add_reminder_from_menu(e):
        close_create_menu()
        my_timeline.add_new_reminder()

    def make_menu_item(icon, text, color, on_click):
        item = ft.Container(
            content=ft.Row([
                ft.Icon(icon, color=color, size=18),
                ft.Text(text, color=TEXT_COLOR, size=13, weight=ft.FontWeight.W_500),
            ], spacing=10),
            padding=ft.Padding(16, 10, 16, 10),
            on_click=on_click,
            border_radius=8,
        )
        
        def on_hover(e):
            item.bgcolor = ft.Colors.with_opacity(0.08, ft.Colors.WHITE) if e.data == "true" else ft.Colors.TRANSPARENT
            item.update()
            
        item.on_hover = on_hover
        return item

    reminder_item = make_menu_item(ft.Icons.ALARM, "Reminder", ft.Colors.AMBER_400, add_reminder_from_menu)
    event_item = make_menu_item(ft.Icons.EVENT, "Event", ft.Colors.BLUE_400, add_event_from_menu)
    divider = ft.Divider(height=1, thickness=1, color=ft.Colors.GREY_800)

    create_menu = ft.Container(
        visible=False,
        width=150,
        bgcolor=ft.Colors.GREY_900,
        border_radius=12,
        border=ft.Border.all(1, ft.Colors.GREY_800),
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=15,
            color=ft.Colors.with_opacity(0.4, ft.Colors.BLACK),
            offset=ft.Offset(0, 4)
        ),
        padding=ft.Padding(4, 4, 4, 4),
        content=ft.Column([
            reminder_item,
            divider,
            event_item,
        ], spacing=0, tight=True)
    )

    timeline_fab = ft.FloatingActionButton(
        icon=ft.Icons.ADD,
        on_click=lambda _: toggle_create_menu(),
        mini=ADD_BUTTON_MINI,
    )

    def toggle_create_menu():
        nonlocal create_menu_visible
        create_menu_visible = not create_menu_visible
        create_menu.visible = create_menu_visible
        if create_menu_visible:
            timeline_fab.icon = ft.Icons.CLOSE
            timeline_fab.bgcolor = ft.Colors.RED_700
        else:
            timeline_fab.icon = ft.Icons.ADD
            timeline_fab.bgcolor = None
        create_menu.update()
        timeline_fab.update()

    timeline_create_group = ft.Column(
        horizontal_alignment=ft.CrossAxisAlignment.END,
        spacing=8,
        controls=[create_menu, timeline_fab],
    )

    # --- Notes single FAB ---
    notes_fab = ft.FloatingActionButton(
        icon=ft.Icons.ADD,
        on_click=lambda _: my_notepad.add_new_note(),
        mini=ADD_BUTTON_MINI,
        visible=False,
    )

    def change_view(e):
        selected = e.control.selected_index
        if selected == 0:
            viewport.content = my_timeline
            timeline_create_group.visible = True
            notes_fab.visible = False
            create_menu_visible = False
            create_menu.visible = False
            timeline_fab.icon = ft.Icons.ADD
            timeline_fab.bgcolor = None
            my_timeline.refresh_events()
        elif selected == 1:
            viewport.content = my_notepad
            timeline_create_group.visible = False
            notes_fab.visible = True
            my_notepad.refresh_notes()
        elif selected == 2:
            viewport.content = my_settings
            timeline_create_group.visible = False
            notes_fab.visible = False
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
            ft.NavigationBarDestination(
                icon=ft.Icons.SETTINGS,
                label="Settings",
            ),
        ],
    )

    page.add(
        ft.Stack(
            expand=True,
            controls=[
                viewport,
                ft.Container(
                    content=timeline_create_group,
                    right=ADD_BUTTON_RIGHT,
                    bottom=ADD_BUTTON_BOTTOM,
                ),
                ft.Container(
                    content=notes_fab,
                    right=ADD_BUTTON_RIGHT,
                    bottom=ADD_BUTTON_BOTTOM,
                ),
            ],
        )
    )

    my_timeline.refresh_events()


ft.run(main)
