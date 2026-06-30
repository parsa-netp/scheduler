import re
import flet as ft
import threading
from datetime import datetime
from libs.database import get_all_notes, add_note, get_note_by_id, update_note, delete_note
from libs.constants import BOX_COLOR, RADIUS, TEXT_COLOR, LABEL_COLOR, LINE_COLOR


class Notepad(ft.Container):
    NOTE_COLORS = [
        "GREY_700", "RED_700", "ORANGE_700", "AMBER_700",
        "GREEN_700", "TEAL_700", "BLUE_700", "INDIGO_700",
        "PURPLE_700", "PINK_700",
    ]

    def __init__(self, page: ft.Page):
        super().__init__()
        self.main_page = page
        self.bgcolor = BOX_COLOR
        self.border_radius = RADIUS
        self.padding = 20
        self.expand = True

        self.current_note_id = None
        self.selected_color = "GREY_700"
        self._debounce_timer = None

        self._build_editor()
        self.grid_content = ft.Column(expand=True, spacing=15)

        self.content = ft.Stack(
            expand=True,
            controls=[self.grid_content, self.editor_content],
        )

    def _build_grid(self, notes):
        self.grid_content.visible = True
        self.editor_content.visible = False

        if not notes:
            self.grid_content.controls = [
                ft.Text("Notes", size=22, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("No notes yet", size=18, color=LABEL_COLOR),
                            ft.Text("Tap + to create one", size=14, color=LABEL_COLOR),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    alignment=ft.alignment.Alignment(0, 0),
                    expand=True,
                ),
            ]
            return

        grid_rows = []
        for i in range(0, len(notes), 2):
            chunk = notes[i:i+2]
            row_cards = [ft.Container(content=self._build_note_card(n), expand=True) for n in chunk]
            if len(chunk) == 1:
                row_cards.append(ft.Container(expand=True))
            grid_rows.append(ft.Row(row_cards, spacing=10, vertical_alignment=ft.CrossAxisAlignment.START))

        self.grid_content.controls = [
            ft.Text("Notes", size=22, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
            ft.Column(
                controls=grid_rows,
                expand=True,
                spacing=10,
                scroll=ft.ScrollMode.AUTO,
            ),
        ]

    def refresh_notes(self):
        notes = get_all_notes()
        self._build_grid(notes)

    def _build_editor(self):
        self.title_field = ft.TextField(
            hint_text="Title",
            border=ft.InputBorder.NONE,
            text_size=22,
            text_style=ft.TextStyle(weight=ft.FontWeight.BOLD),
            color=TEXT_COLOR,
            cursor_color=TEXT_COLOR,
            on_change=self._on_edit_changed,
        )

        self.content_field = ft.TextField(
            hint_text="Take a note...",
            multiline=True,
            min_lines=8,
            expand=True,
            border=ft.InputBorder.NONE,
            color=TEXT_COLOR,
            cursor_color=TEXT_COLOR,
            on_change=self._on_edit_changed,
        )

        self.showing_preview = False

        self.preview_markdown = ft.Markdown(
            value="",
            selectable=True,
            extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
            expand=True,
            visible=False,
        )

        color_dots = []
        for c in self.NOTE_COLORS:
            color_dots.append(
                ft.Container(
                    width=28, height=28,
                    bgcolor=getattr(ft.Colors, c),
                    border_radius=14,
                    ink=True,
                    on_click=lambda _, color=c: self._select_color(color),
                )
            )

        back_btn = ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color=TEXT_COLOR, on_click=self._close_editor)
        preview_btn = ft.IconButton(icon=ft.Icons.VISIBILITY, icon_color=TEXT_COLOR, on_click=self._toggle_preview)
        pin_btn = ft.IconButton(icon=ft.Icons.PUSH_PIN, icon_color=TEXT_COLOR, on_click=self._toggle_pin)
        delete_btn = ft.IconButton(icon=ft.Icons.DELETE, icon_color=TEXT_COLOR, on_click=self._delete_note)

        self.editor_content = ft.Column(
            visible=False,
            expand=True,
            spacing=10,
            controls=[
                ft.Row([back_btn, ft.Row([preview_btn, pin_btn, delete_btn], spacing=0)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                self.title_field,
                ft.Divider(height=1, color=LINE_COLOR),
                self.content_field,
                self.preview_markdown,
                ft.Row(color_dots, spacing=8),
            ],
        )

    def _toggle_preview(self, e):
        self.showing_preview = not self.showing_preview
        self.content_field.visible = not self.showing_preview
        self.preview_markdown.value = self.content_field.value
        self.preview_markdown.visible = self.showing_preview
        self.update()

    def _strip_markdown(self, text):
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'\*{1,3}(.*?)\*{1,3}', r'\1', text)
        text = re.sub(r'_(.*?)_', r'\1', text)
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
        text = re.sub(r'`([^`]+)`', r'\1', text)
        text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', r'\1', text)
        text = re.sub(r'^>\s+', '', text, flags=re.MULTILINE)
        return text.strip()

    def _on_edit_changed(self, e):
        if self.current_note_id:
            if self._debounce_timer:
                self._debounce_timer.cancel()
            
            def save_now():
                update_note(
                    self.current_note_id,
                    title=self.title_field.value,
                    content=self.content_field.value,
                )
                
            self._debounce_timer = threading.Timer(1.0, save_now)
            self._debounce_timer.start()

    def _select_color(self, color):
        self.selected_color = color
        if self.current_note_id:
            update_note(self.current_note_id, color=color)
        self._update_editor_bg()

    def _toggle_pin(self, e):
        if self.current_note_id:
            note = get_note_by_id(self.current_note_id)
            if note:
                update_note(self.current_note_id, pinned=not note["pinned"])

    def _delete_note(self, e):
        if self.current_note_id:
            delete_note(self.current_note_id)
            self.current_note_id = None
            self._close_editor()

    def _update_editor_bg(self):
        bg = getattr(ft.Colors, self.selected_color, ft.Colors.GREY_800)
        self.bgcolor = bg
        self.update()

    def _close_editor(self, e=None):
        self.grid_content.visible = True
        self.editor_content.visible = False
        self.bgcolor = BOX_COLOR
        self.current_note_id = None
        self.refresh_notes()
        self.update()

    def _format_date(self, date_str):
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            return dt.strftime("%b %d, %Y")
        except (ValueError, TypeError):
            return ""

    def _build_note_card(self, note):
        title = note.get("title", "")
        content = note.get("content", "")
        color = note.get("color", "GREY_700")
        pinned = note.get("pinned", 0)
        created_at = note.get("created_at", "")
        bg = getattr(ft.Colors, color, ft.Colors.GREY_700)

        card_controls = []

        if pinned:
            card_controls.append(
                ft.Row([
                    ft.Container(expand=True),
                    ft.Icon(ft.Icons.PUSH_PIN, size=16, color=ft.Colors.WHITE54),
                ])
            )

        if title:
            card_controls.append(
                ft.Text(
                    title, size=15, weight=ft.FontWeight.BOLD, color=TEXT_COLOR,
                    max_lines=2, overflow=ft.TextOverflow.ELLIPSIS,
                )
            )
        else:
            card_controls.append(
                ft.Text(
                    "New note", size=15, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE38,
                    italic=True, max_lines=1,
                )
            )

        if content:
            card_controls.append(
                ft.Text(
                    self._strip_markdown(content), size=13, color=ft.Colors.WHITE70,
                    max_lines=6, overflow=ft.TextOverflow.ELLIPSIS,
                )
            )

        formatted_date = self._format_date(created_at)
        card_controls.append(
            ft.Text(formatted_date, size=11, color=ft.Colors.WHITE38),
        )

        return ft.Container(
            content=ft.Column(card_controls, spacing=4),
            bgcolor=bg,
            border_radius=8,
            padding=12,
            ink=True,
            on_click=lambda _, n=note: self.open_note_editor(n),
        )

    def open_note_editor(self, note):
        self.current_note_id = note["id"]
        self.selected_color = note["color"]
        self.title_field.value = note["title"]
        self.content_field.value = note["content"]
        self._update_editor_bg()

        self.grid_content.visible = False
        self.editor_content.visible = True
        self.update()

    def add_new_note(self):
        note_id = add_note("", "", "GREY_700")
        note = get_note_by_id(note_id)
        if note:
            self.open_note_editor(note)
