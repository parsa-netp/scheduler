import flet as ft
from datetime import date, timedelta
from calendar import monthrange
from libs.database import get_events_for_day, get_reminders_for_day
from libs.constants import BOX_COLOR, LABEL_COLOR, LINE_COLOR, TEXT_COLOR

def render_month_grid(timeline_obj):
    timeline_obj.month_grid.controls.clear()
    
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
    timeline_obj.month_grid.controls.append(headers)
    
    year = timeline_obj.current_date.year
    month = timeline_obj.current_date.month
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
                timeline_obj.current_date = d
                timeline_obj.view_dropdown.value = "Day"
                timeline_obj.update_header()
                timeline_obj.refresh_events()
                timeline_obj.view_dropdown.update()

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
        
        timeline_obj.month_grid.controls.append(ft.Row(row_controls, spacing=5, expand=True))
    
    timeline_obj.month_container.update()
