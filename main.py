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
        mini=ADD_BUTTON_MINI,
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
                    right=ADD_BUTTON_RIGHT,
                    bottom=ADD_BUTTON_BOTTOM,
                ),
            ],
        )
    )

    my_timeline.refresh_events()


ft.run(main)
