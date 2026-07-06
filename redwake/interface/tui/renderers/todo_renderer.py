from typing import Any, ClassVar

from rich.text import Text
from textual.widgets import Static

from .base_renderer import BaseToolRenderer
from .registry import register_tool_renderer


STATUS_MARKERS: dict[str, str] = {
    "pending": "[ ]",
    "in_progress": "[~]",
    "done": "[•]",
}


def _format_todo_lines(text: Text, result: dict[str, Any]) -> None:
    """Append todo list lines to the rendering Text.

    For todos that were created/updated/marked in this call, render the
    items. For an empty agent (list_todos path), show 'No todos yet'.
    """
    todos = result.get("todos")
    if not isinstance(todos, list) or not todos:
        created_count = result.get("created_count")
        if created_count is not None:
            # create/update/mark path returned an empty list. The call was
            # successful; surface a dim 'plan updated' line so the user
            # can see the agent did something.
            text.append("\n  ")
            text.append("(plan updated, nothing to add)", style="dim italic")
            return
        # list_todos on a fresh agent
        text.append("\n  ")
        text.append("No todos yet", style="dim italic")
        return

    for todo in todos:
        status = todo.get("status", "pending")
        marker = STATUS_MARKERS.get(status, STATUS_MARKERS["pending"])

        title = todo.get("title", "").strip() or "(untitled)"

        text.append("\n  ")
        text.append(marker)
        text.append(" ")

        if status == "done":
            text.append(title, style="dim strike")
        elif status == "in_progress":
            text.append(title, style="italic")
        else:
            text.append(title)


def _render_create_or_update(
    title: str,
    title_style: str,
    result: Any,
    error_default: str,
    pending_label: str,
) -> Static | None:
    """Common render path for CreateTodo / UpdateTodo.

    Returns None ONLY when the backend reported a hard failure with no
    result payload (rare). Otherwise always returns a Static so the user
    can see every planning step in chat history.
    """
    text = Text()
    text.append("📋 ")
    text.append(title, style=f"bold {title_style}")

    if isinstance(result, str) and result.strip():
        text.append("\n  ")
        text.append(result.strip(), style="dim")
    elif isinstance(result, dict):
        if result.get("success"):
            _format_todo_lines(text, result)
        else:
            error = result.get("error", error_default)
            text.append("\n  ")
            text.append(error, style="#ef4444")
    elif result is None:
        text.append("\n  ")
        text.append(pending_label, style="dim")
    else:
        text.append("\n  ")
        text.append(pending_label, style="dim")

    css_classes = BaseToolRenderer.get_css_classes("completed")
    return Static(text, classes=css_classes)


@register_tool_renderer
class CreateTodoRenderer(BaseToolRenderer):
    tool_name: ClassVar[str] = "create_todo"
    css_classes: ClassVar[list[str]] = ["tool-call", "todo-tool"]

    @classmethod
    def render(cls, tool_data: dict[str, Any]) -> Static | None:
        return _render_create_or_update(
            title="Todo",
            title_style="#a78bfa",
            result=tool_data.get("result"),
            error_default="Failed to create todo",
            pending_label="Creating...",
        )


@register_tool_renderer
class ListTodosRenderer(BaseToolRenderer):
    tool_name: ClassVar[str] = "list_todos"
    css_classes: ClassVar[list[str]] = ["tool-call", "todo-tool"]

    @classmethod
    def render(cls, tool_data: dict[str, Any]) -> Static:
        result = tool_data.get("result")

        text = Text()
        text.append("📋 ")
        text.append("Todos", style="bold #a78bfa")

        if isinstance(result, str) and result.strip():
            text.append("\n  ")
            text.append(result.strip(), style="dim")
        elif isinstance(result, dict):
            if result.get("success"):
                _format_todo_lines(text, result)
            else:
                error = result.get("error", "Unable to list todos")
                text.append("\n  ")
                text.append(error, style="#ef4444")
        else:
            text.append("\n  ")
            text.append("Loading...", style="dim")

        css_classes = cls.get_css_classes("completed")
        return Static(text, classes=css_classes)


@register_tool_renderer
class UpdateTodoRenderer(BaseToolRenderer):
    tool_name: ClassVar[str] = "update_todo"
    css_classes: ClassVar[list[str]] = ["tool-call", "todo-tool"]

    @classmethod
    def render(cls, tool_data: dict[str, Any]) -> Static | None:
        return _render_create_or_update(
            title="Todo Updated",
            title_style="#a78bfa",
            result=tool_data.get("result"),
            error_default="Failed to update todo",
            pending_label="Updating...",
        )


@register_tool_renderer
class MarkTodoDoneRenderer(BaseToolRenderer):
    tool_name: ClassVar[str] = "mark_todo_done"
    css_classes: ClassVar[list[str]] = ["tool-call", "todo-tool"]

    @classmethod
    def render(cls, tool_data: dict[str, Any]) -> Static | None:
        return _render_create_or_update(
            title="Todo Completed",
            title_style="#a78bfa",
            result=tool_data.get("result"),
            error_default="Failed to mark todo done",
            pending_label="Marking done...",
        )


@register_tool_renderer
class MarkTodoPendingRenderer(BaseToolRenderer):
    tool_name: ClassVar[str] = "mark_todo_pending"
    css_classes: ClassVar[list[str]] = ["tool-call", "todo-tool"]

    @classmethod
    def render(cls, tool_data: dict[str, Any]) -> Static | None:
        return _render_create_or_update(
            title="Todo Reopened",
            title_style="#f59e0b",
            result=tool_data.get("result"),
            error_default="Failed to reopen todo",
            pending_label="Reopening...",
        )


@register_tool_renderer
class DeleteTodoRenderer(BaseToolRenderer):
    tool_name: ClassVar[str] = "delete_todo"
    css_classes: ClassVar[list[str]] = ["tool-call", "todo-tool"]

    @classmethod
    def render(cls, tool_data: dict[str, Any]) -> Static | None:
        return _render_create_or_update(
            title="Todo Removed",
            title_style="#94a3b8",
            result=tool_data.get("result"),
            error_default="Failed to remove todo",
            pending_label="Removing...",
        )
