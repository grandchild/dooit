from os import get_terminal_size
from rich.align import Align
from rich.box import HEAVY
from rich.console import RenderableType
from rich.tree import Tree
from rich.panel import Panel
from rich.text import Text
from rich.style import StyleType
from textual.widget import Widget
from textual import events
from typing import List, Optional

from ...ui.events.events import ApplySortMethod, ChangeStatus
from ...utils.config import conf


class SortOptions(Widget):
    """
    A list class to show and select the items in a list
    """

    def __init__(
        self,
        name: Optional[str] = None,
        options: List[str] = [],
        style_unfocused: StyleType = "white",
        style_focused: StyleType = "bold reverse green ",
        pad: bool = True,
        rotate: bool = False,
        wrap: bool = True,
    ) -> None:
        super().__init__(name)
        self.options = options
        self.style_unfocused = style_unfocused
        self.style_focused = style_focused
        self.pad = pad
        self.rotate = rotate
        self.wrap = wrap
        self.highlighted = 0
        self.keys = conf.keys

    def highlight(self, id: int) -> None:
        self.highlighted = id
        self.refresh(layout=True)

    async def hide(self):
        await self.key_press(events.Key(self, "escape"))

    def move_cursor_down(self) -> None:
        """
        Moves the highlight down
        """

        if self.rotate:
            self.highlight((self.highlighted + 1) % len(self.options))
        else:
            self.highlight(min(self.highlighted + 1, len(self.options) - 1))

    def move_cursor_up(self) -> None:
        """
        Moves the highlight up
        """

        if self.rotate:
            self.highlight(
                (self.highlighted - 1 + len(self.options)) % len(self.options)
            )
        else:
            self.highlight(max(self.highlighted - 1, 0))

    def move_cursor_to_top(self) -> None:
        """
        Moves the cursor to the top
        """
        self.highlight(0)

    def move_cursor_to_bottom(self) -> None:
        """
        Moves the cursor to the bottom
        """

        self.highlight(len(self.options) - 1)

    async def key_press(self, event: events.Key) -> None:
        event.stop()

        key = self.keys
        if event.key == "escape":
            # self.visible = False
            # self.refresh()
            await self.post_message(ChangeStatus(self, "NORMAL"))
        elif event.key in key.move_down:
            self.move_cursor_down()
        elif event.key in key.move_up:
            self.move_cursor_up()
        elif event.key in key.move_to_top:
            self.move_cursor_to_top()
        elif event.key in key.move_to_bottom:
            self.move_cursor_to_bottom()
        elif event.key == "enter":
            await self.emit(ApplySortMethod(self, self.options[self.highlighted]))
            await self.hide()

    def add_option(self, option: str) -> None:
        self.options.append(option)
        self.refresh()

    def render(self) -> RenderableType:

        # 1 borders + 1 space padding on each side
        tree = Tree("")
        tree.hide_root = True
        tree.expanded = True

        for index, option in enumerate(self.options):
            label = Text(option)
            if option == "name":
                label = Text("    ") + label
            elif option == "date":
                label = Text("    ") + label
            elif option == "status":
                label = Text("    ") + label
            elif option == "urgency":
                label = Text("    ") + label

            label.pad_right(self.size.width)
            label.plain = label.plain.ljust(20)
            if index != self.highlighted:
                label.stylize(self.style_unfocused)
            else:
                label.stylize(self.style_focused)

            meta = {
                "@click": f"click_label({index})",
                "selected": index,
            }
            label.apply_meta(meta)
            tree.add(label)

        return self.render_panel(tree)

    def render_panel(self, tree) -> RenderableType:
        return Align.center(
            Panel.fit(
                tree,
                title="Sort",
                width=20,
                box=HEAVY,
            ),
            vertical="middle",
            height=round(get_terminal_size()[1] * 0.8),
        )

    async def action_click_label(self, id):
        self.highlight(id)
        await self.emit(ApplySortMethod(self, self.options[self.highlighted]))
        await self.hide()
