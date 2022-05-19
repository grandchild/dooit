from rich.console import RenderableType
from rich.text import Text
from textual.widgets import TreeNode

from . import TreeEdit


class DateTree(TreeEdit):
    async def edit_current_node(self) -> None:
        pass

    def render_node(self, node: TreeNode) -> RenderableType:

        color = "yellow"

        if data := node.data:
            label = Text(str(data.todo.due))
            match node.data.todo.due:
                case "COMPLETE":
                    color = "green"

                case "OVERDUE":
                    color = "red"
        else:
            label = Text()

        if not label.plain:
            label = Text("No due date")

        label = Text(" ") + label + " "
        if node.id == self.highlighted:
            label.stylize("bold reverse blue")

        label = Text.from_markup(f"[{color}]   [/{color}]") + label

        return label