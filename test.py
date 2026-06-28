import flet as ft
from libs.timeline import Timeline

def main(page: ft.Page):
    t = Timeline(page)
    t.view_dropdown.value = "3 Days"
    t.refresh_events()
    print("SUCCESS")

ft.app(target=main)
