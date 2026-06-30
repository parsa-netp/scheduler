import flet as ft
from datetime import date, timedelta
import calendar
from libs.constants import TEXT_COLOR, LABEL_COLOR

class MiniCalendar:
    def __init__(self, on_date_selected=None):
        self.on_date_selected = on_date_selected
        self.current_view_date = date.today().replace(day=1)
        self.selected_date = date.today()
        self.container = ft.Container(padding=ft.Padding(5, 20, 5, 20))
        self._build()
        
    def _build(self):
        self.header_text = ft.Text("", size=13, weight=ft.FontWeight.W_500, color=TEXT_COLOR)
        
        self.grid = ft.Column(spacing=4)
        
        content = ft.Column([
            ft.Row([
                self.header_text,
                ft.Row([
                    ft.IconButton(icon=ft.Icons.CHEVRON_LEFT, icon_color=TEXT_COLOR, icon_size=16, on_click=self.prev_month),
                    ft.IconButton(icon=ft.Icons.CHEVRON_RIGHT, icon_color=TEXT_COLOR, icon_size=16, on_click=self.next_month),
                ], spacing=0)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Row([ft.Text(day, size=10, color=LABEL_COLOR, weight=ft.FontWeight.W_500, width=24, text_align=ft.TextAlign.CENTER) for day in ["S", "M", "T", "W", "T", "F", "S"]], spacing=4),
            self.grid
        ], spacing=8)
        
        self.container.content = content
        self.update_grid()
        
    def prev_month(self, _):
        m = self.current_view_date.month - 1
        y = self.current_view_date.year
        if m < 1:
            m = 12
            y -= 1
        self.current_view_date = date(y, m, 1)
        self.update_grid()
        self.container.update()
        
    def next_month(self, _):
        m = self.current_view_date.month + 1
        y = self.current_view_date.year
        if m > 12:
            m = 1
            y += 1
        self.current_view_date = date(y, m, 1)
        self.update_grid()
        self.container.update()

    def set_selected_date(self, d):
        self.selected_date = d
        self.current_view_date = d.replace(day=1)
        self.update_grid()
        if self.container.page:
            self.container.update()

    def _on_day_click(self, d):
        self.selected_date = d
        self.update_grid()
        self.container.update()
        if self.on_date_selected:
            self.on_date_selected(d)

    def update_grid(self):
        year = self.current_view_date.year
        month = self.current_view_date.month
        
        self.header_text.value = self.current_view_date.strftime("%B %Y")
        
        self.grid.controls.clear()
        
        first_day_weekday, num_days = calendar.monthrange(year, month)
        start_offset = (first_day_weekday + 1) % 7
        
        grid_start = self.current_view_date - timedelta(days=start_offset)
        
        today = date.today()
        
        for r_idx in range(6):
            row_controls = []
            for c_idx in range(7):
                cell_date = grid_start + timedelta(days=r_idx * 7 + c_idx)
                is_curr_month = cell_date.month == month
                is_today = cell_date == today
                is_selected = cell_date == self.selected_date
                
                txt_color = TEXT_COLOR if is_curr_month else LABEL_COLOR
                bg_color = ft.Colors.TRANSPARENT
                
                if is_today:
                    bg_color = "#A8C7FA"
                    txt_color = ft.Colors.BLACK
                elif is_selected:
                    bg_color = ft.Colors.with_opacity(0.2, "#A8C7FA")
                    txt_color = "#A8C7FA"
                    
                cell = ft.Container(
                    content=ft.Text(str(cell_date.day), size=10, color=txt_color, text_align=ft.TextAlign.CENTER),
                    bgcolor=bg_color,
                    border_radius=12,
                    width=24, height=24,
                    alignment=ft.alignment.Alignment(0, 0),
                    on_click=lambda e, d=cell_date: self._on_day_click(d)
                )
                row_controls.append(cell)
            self.grid.controls.append(ft.Row(row_controls, spacing=4))
