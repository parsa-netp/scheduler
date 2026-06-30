import flet as ft
from libs.database import init_db
from libs.mini_calendar import MiniCalendar
from libs.constants import (
    PAGE_COLOR,
    WINDOW_COLOR,
    PADDING,
    LABEL_COLOR,
    TEXT_COLOR,
    ADD_BUTTON_MINI,
    ADD_BUTTON_RIGHT,
    ADD_BUTTON_BOTTOM,
    BOX_COLOR,
    RADIUS,
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

    top_bar = ft.Container(
        content=my_timeline.header,
        visible=True,
        bgcolor=BOX_COLOR,
        border_radius=0,
        padding=0,
        margin=0,
    )

    viewport = ft.Container(
        content=my_timeline, 
        expand=True, 
        padding=ft.Padding(left=PADDING, top=0, right=PADDING, bottom=PADDING)
    )

    # --- Timeline speed-dial (Event + Reminder) ---
    create_btn = ft.PopupMenuButton(
        content=ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.ADD, color=TEXT_COLOR),
                ft.Text("Create", size=14, weight=ft.FontWeight.W_500, color=TEXT_COLOR),
                ft.Icon(ft.Icons.ARROW_DROP_DOWN, color=TEXT_COLOR)
            ], alignment=ft.MainAxisAlignment.CENTER),
            bgcolor="#2D2E30",
            border_radius=24,
            width=140,
            padding=ft.Padding(12, 12, 12, 12),
        ),
        items=[
            ft.PopupMenuItem(content=ft.Row([ft.Icon(ft.Icons.EVENT), ft.Text("Event")]), on_click=lambda _: my_timeline.add_new_event()),
            ft.PopupMenuItem(content=ft.Row([ft.Icon(ft.Icons.ALARM), ft.Text("Reminder")]), on_click=lambda _: my_timeline.add_new_reminder()),
        ]
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
            top_bar.visible = True
            create_btn.visible = True
            notes_fab.visible = False
            my_timeline.refresh_events()
            mini_cal.set_selected_date(my_timeline.current_date)
        elif selected == 1:
            viewport.content = my_notepad
            top_bar.visible = False
            create_btn.visible = False
            notes_fab.visible = True
            my_notepad.refresh_notes()
        elif selected == 2:
            viewport.content = my_settings
            top_bar.visible = False
            create_btn.visible = False
            create_menu.visible = False
            notes_fab.visible = False
        page.update()

    def go_to_settings(e):
        viewport.content = my_settings
        top_bar.visible = False
        create_btn.visible = False
        notes_fab.visible = False
        page.update()

    my_timeline.on_settings_click = go_to_settings

    nav_rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=100,
        min_extended_width=200,
        extended=True,
        expand=True,
        bgcolor=ft.Colors.TRANSPARENT,
        destinations=[
            ft.NavigationRailDestination(
                icon=ft.Icons.CALENDAR_MONTH_OUTLINED,
                selected_icon=ft.Icons.CALENDAR_MONTH,
                label="Timeline"
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.NOTE_ALT_OUTLINED,
                selected_icon=ft.Icons.NOTE_ALT,
                label="Notes"
            ),
        ],
        on_change=change_view,
        indicator_color=ft.Colors.with_opacity(0.15, ft.Colors.BLUE_400)
    )

    def on_mini_cal_date_selected(d):
        my_timeline.current_date = d
        my_timeline.update_header()
        my_timeline.refresh_events()
        
    mini_cal = MiniCalendar(on_date_selected=on_mini_cal_date_selected)

    sidebar = ft.Container(
        width=250,
        padding=ft.Padding(10, 10, 10, 10),
        visible=True,
        bgcolor="#202124",
        content=ft.Column([
            create_btn,
            mini_cal.container,
            ft.Container(height=10),
            nav_rail
        ], alignment=ft.MainAxisAlignment.START, expand=True)
    )

    def toggle_sidebar(e):
        sidebar.visible = not sidebar.visible
        page.update()

    my_timeline.hamburger.on_click = toggle_sidebar

    main_body = ft.Row([sidebar, viewport], expand=True, spacing=0)
    main_layout = ft.Column([top_bar, main_body], expand=True, spacing=0)



    page.add(
        ft.Stack(
            expand=True,
            controls=[
                main_layout,
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
