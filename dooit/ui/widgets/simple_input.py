import pyperclip
from typing import List, Literal, Optional, Tuple
from rich.console import RenderableType
from rich.panel import Panel
from rich.style import StyleType
from rich.text import Text, TextType
from rich.box import Box
from rich.align import AlignMethod
from textual.widget import Widget
from textual import events
from textual.reactive import Reactive


class View:
    """
    A class to manage current viewing portion of text input
    """

    def __init__(self, start: int = 0, end: int = 0) -> None:
        self.start = start
        self.end = end

    def shift_left(self, delta: int) -> None:
        """
        Shift the view to the left by provided delta
        """

        delta = min(delta, self.start)
        self.start -= delta
        self.end -= delta

    def shift_right(self, delta: int, max_val: int) -> None:
        """
        Shift the view to the left by provided delta
        """

        delta = min(delta, max_val - self.end)
        self.start += delta
        self.end += delta

    def __str__(self) -> str:
        return f"View({self.start}, {self.end})"


class SimpleInput(Widget):
    """
    A simple single line Text Input widget
    """

    value: str = ""
    cursor: str = "|"
    _cursor_position: int = 0
    _has_focus: Reactive[bool] = Reactive(False)

    def __init__(
        self,
        name: Optional[str] = None,
        title: TextType = "",
        title_align: AlignMethod = "center",
        border_style: StyleType = "blue",
        box: Optional[Box] = None,
        placeholder: TextType = Text("", style="dim white"),
        password: bool = False,
        list: Tuple[Literal["blacklist", "whitelist"], List[str]] = ("blacklist", []),
    ) -> None:
        super().__init__(name)
        self.title = title
        self.title_align: AlignMethod = title_align  # Silence compiler warning
        self.border_style: StyleType = border_style
        self.placeholder = placeholder
        self.password = password
        self.list = list
        self.box = box

        self._cursor_position = len(self.value)
        self.width = self.size.width - 4

    @property
    def has_focus(self) -> bool:
        return self._has_focus

    async def on_resize(self, _: events.Resize) -> None:
        self._set_view()
        self.update_view(self._cursor_position, 0)
        self._cursor_position = 0
        self.refresh()

    def _format_text(self, text: str) -> str:
        """
        Trims the non-visible part of the widget
        """
        return text[self.view.start : self.view.end]

    def _set_view(self):
        if self.box:
            self.width = self.size.width - 4
        else:
            self.width = self.size.width

        # self.width = self.size.width - 4
        self.view = View(0, self.width)

    def render(self) -> RenderableType:
        """
        Renders a Panel for the Text Input Box
        """

        if not hasattr(self, "view"):
            self._set_view()

        if self.has_focus:
            text = self._render_text_with_cursor()
        else:
            if len(self.value) == 0:
                return self.render_panel(self.placeholder)
            else:
                text = self.value

        formatted_text = Text.from_markup(self._format_text(text))
        return self.render_panel(formatted_text)

    def render_panel(self, text: TextType) -> RenderableType:
        """
        Builds a panel for the Inpux Box
        """

        if self.box:
            return Panel(
                text,
                title=self.title,
                title_align=self.title_align,
                height=3,
                border_style=("bold " if self.has_focus else "dim ")
                + str(self.border_style),
                box=self.box,
            )
        else:
            return text

    def _render_text_with_cursor(self) -> str:
        """
        Produces renderable Text object combining value and cursor
        """

        text = ""

        if self.password:
            text += "•" * self._cursor_position
            text += self.cursor
            text += "•" * (len(self.value) - self._cursor_position)
        else:
            text += self.value[: self._cursor_position]
            text += self.cursor
            text += self.value[self._cursor_position :]

        return text

    def on_focus(self, *_: events.Focus) -> None:
        self._has_focus = True

    def on_blur(self, *_: events.Blur) -> None:
        self._has_focus = False

    def clear(self) -> None:
        """
        Clears the Input Box
        """
        self.value = ""
        self._cursor_position = 0
        self.refresh()

    def _is_allowed(self, text: str) -> bool:
        if self.list[0] == "whitelist":
            for letter in text:
                if letter not in self.list[1]:
                    return False
        else:
            for letter in text:
                if letter in self.list[1]:
                    return False

        return True

    async def _insert_text(self, text: Optional[str] = None) -> None:
        """
        Inserts text where the cursor is
        """

        # Will throw an error if `xclip` if not installed on the linux(Xorg) system,
        # should work just fine on windows and mac

        if text is None:
            text = pyperclip.paste()

        self.value = (
            self.value[: self._cursor_position]
            + text
            + self.value[self._cursor_position :]
        )

        self._cursor_position += len(text)

    async def on_key(self, event: events.Key) -> None:
        """Send the key to the Input"""

        await self.handle_keypress(event.key)
        self.refresh()

    async def _move_cursor_backward(self, word=False, delete=False) -> None:
        """
        Moves the cursor backwards..
        Optionally jumps over a word when pressed ctrl+left
        Optionally deletes the letter in case of backspace
        """

        prev = self._cursor_position

        if not word:
            self._cursor_position = max(self._cursor_position - 1, 0)
        else:
            while self._cursor_position:
                if self.value[self._cursor_position - 1] != " " and (
                    self._cursor_position == 1
                    or self.value[self._cursor_position - 2] == " "
                ):
                    self._cursor_position -= 1
                    break

                self._cursor_position -= 1

        if delete:
            self.value = self.value[: self._cursor_position] + self.value[prev:]
            self.view.shift_left(prev - self._cursor_position)

    async def _move_cursor_forward(self, word=False, delete=False) -> None:
        """
        Moves the cursor forward..
        Optionally jumps over a word when pressed ctrl+right
        Optionally deletes the letter in case of del or ctrl+del
        """

        prev = self._cursor_position

        if not word:
            self._cursor_position = min(self._cursor_position + 1, len(self.value))
        else:

            while self._cursor_position < len(self.value):
                if (
                    self._cursor_position != prev
                    and self.value[self._cursor_position - 1] == " "
                    and (
                        self._cursor_position == len(self.value) - 1
                        or self.value[self._cursor_position] != " "
                    )
                ):
                    break

                self._cursor_position += 1

        if delete:
            self.value = self.value[:prev] + self.value[self._cursor_position :]
            self._cursor_position = prev  # Because the cursor never actually moved :)

    def update_view(self, prev: int, curr: int) -> None:
        """
        Updates the current view-able part of the text if there is an overflow
        """
        if not hasattr(self, "view"):
            self._set_view()

        if prev >= self.view.start and curr < self.view.start:
            self.view.shift_left(prev - curr)

        elif prev <= self.view.end and curr >= self.view.end:
            self.view.shift_right(curr - prev, len(self.value) + 1)

    async def clear_input(self):
        await self.handle_keypress("end")
        while self.value:
            await self.handle_keypress("ctrl+h")

    async def handle_keypress(self, key: str) -> None:
        """
        Handles Keypresses
        """
        prev = self._cursor_position

        if key == "left": # Moving backward
            await self._move_cursor_backward()

        if key == "ctrl+left":
            await self._move_cursor_backward(word=True)

        if key == "ctrl+h":  # Backspace
            await self._move_cursor_backward(delete=True)

        if key == "ctrl+w":
            await self._move_cursor_backward(word=True, delete=True)

        # Moving forward
        if key == "right":
            await self._move_cursor_forward()

        if key == "ctrl+right":
            await self._move_cursor_forward(word=True)

        if key == "delete":
            await self._move_cursor_forward(delete=True)

        if key == "ctrl+delete":
            await self._move_cursor_forward(word=True, delete=True)

        if key == "ctrl+l":
            await self.clear_input()

        # EXTRAS
        if key == "home":
            self._cursor_position = 0

        if key == "end":
            self._cursor_position = len(self.value)

        if key == "ctrl+i":
            await self._insert_text("\t")

        # COPY-PASTA
        if key == "ctrl+v":
            try:
                await self._insert_text()
            except:
                return

        if len(key) == 1:
            await self._insert_text(key)

        self.update_view(prev, self._cursor_position)
        self.refresh()
