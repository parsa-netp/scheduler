import flet as ft
from datetime import datetime
from libs.database import update_event, delete_event, add_reminder as db_add_reminder
from libs.helpers import parse_dt_safe

# We define EVENT_ICONS here as well to avoid circular imports.
EVENT_ICONS = {
    "EVENT": ft.Icons.EVENT,
    "WORK": ft.Icons.BUSINESS_CENTER,
    "MEETING": ft.Icons.PEOPLE,
    "STUDY": ft.Icons.MENU_BOOK,
    "PERSONAL": ft.Icons.FAVORITE,
    "ALARM": ft.Icons.ACCESS_ALARM,
}

def show_event_dialog(event_obj, main_page):
    curr_title = event_obj.event_data["title"]
    curr_desc = event_obj.event_data.get("description", "")
    curr_color = event_obj.event_data.get("color", "BLUE_700")
    curr_icon = event_obj.event_data.get("icon", "EVENT")
    
    start_time = parse_dt_safe(event_obj.event_data["start_dt"])
    end_time = parse_dt_safe(event_obj.event_data["end_dt"])
    
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
    main_page.overlay.append(date_picker)

    def show_date_picker(e):
        date_picker.open = True
        main_page.update()

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
    main_page.overlay.append(start_time_picker)

    def show_start_picker(e):
        start_time_picker.open = True
        main_page.update()

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
    main_page.overlay.append(end_time_picker)

    def show_end_picker(e):
        end_time_picker.open = True
        main_page.update()

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
        if date_picker in main_page.overlay:
            date_picker.open = False
            main_page.overlay.remove(date_picker)
        if start_time_picker in main_page.overlay:
            start_time_picker.open = False
            main_page.overlay.remove(start_time_picker)
        if end_time_picker in main_page.overlay:
            end_time_picker.open = False
            main_page.overlay.remove(end_time_picker)

    def close_dlg(_):
        remove_pickers()
        dlg.open = False
        main_page.update()

    def delete_ev(_):
        remove_pickers()
        delete_event(event_obj.event_data["id"])
        dlg.open = False
        main_page.update()
        event_obj.timeline.refresh_events()

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
            event_obj.event_data["id"],
            title_tf.value or "Untitled Event",
            new_start_dt,
            new_end_dt,
            curr_icon,
            curr_color,
            desc_tf.value
        )

        remove_pickers()
        dlg.open = False
        main_page.update()
        event_obj.timeline.refresh_events()

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
    main_page.overlay.append(dlg)
    dlg.open = True
    main_page.update()


def show_reminder_dialog(timeline, main_page, current_date):
    selected_date = current_date
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
    main_page.overlay.append(date_picker)

    def show_date_picker(e):
        date_picker.open = True
        main_page.update()

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
    main_page.overlay.append(time_picker)

    def show_time_picker(e):
        time_picker.open = True
        main_page.update()

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
        if date_picker in main_page.overlay:
            date_picker.open = False
            main_page.overlay.remove(date_picker)
        if time_picker in main_page.overlay:
            time_picker.open = False
            main_page.overlay.remove(time_picker)

    def close_dlg(e):
        remove_pickers()
        dlg.open = False
        main_page.update()

    def save(e):
        is_all_day = 1 if all_day_cb.value else 0
        rem_time = selected_time if not all_day_cb.value else datetime.min.time()
        reminder_dt = datetime.combine(selected_date, rem_time).strftime("%Y-%m-%d %H:%M:%S")
        db_add_reminder(title_tf.value or "Reminder", reminder_dt, selected_color, is_all_day)
        remove_pickers()
        dlg.open = False
        main_page.update()
        timeline.refresh_events()

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
    main_page.overlay.append(dlg)
    dlg.open = True
    main_page.update()
