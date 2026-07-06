from __future__ import annotations

import json
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


def _extract_arg_titles(args: Any) -> list[str]:  # noqa: PLR0912
    """Pull titles out of raw LLM-supplied todo arguments.

    The backend may filter entries (e.g. drop empty titles), but the
    user wants to see what the LLM intended to plan. This reads from
    the raw args to surface that intent even when the result is empty.
    """
    if not isinstance(args, dict):
        return []

    titles: list[str] = []

    todos = args.get("todos")
    if isinstance(todos, list):
        for entry in todos:
            if isinstance(entry, dict):
                t = entry.get("title", "")
                if isinstance(t, str) and t.strip():
                    titles.append(t.strip())
            elif isinstance(entry, str) and entry.strip():
                titles.append(entry.strip())
    elif isinstance(todos, str):
        stripped = todos.strip()
        if stripped:
            # JSON-stringified list? Try to parse.
            try:
                parsed = json.loads(stripped)
                if isinstance(parsed, list):
                    for entry in parsed:
                        if isinstance(entry, dict):
                            t = entry.get("title", "")
                            if isinstance(t, str) and t.strip():
                                titles.append(t.strip())
                        elif isinstance(entry, str) and entry.strip():
                            titles.append(entry.strip())
                elif isinstance(parsed, dict):
                    t = parsed.get("title", "")
                    if isinstance(t, str) and t.strip():
                        titles.append(t.strip())
            except (ValueError, TypeError):
                # Plain text -> one title.
                titles.append(stripped)

    return titles


def _render_one_entry(text: Text, title: str, *, muted: bool = False) -> None:
    text.append("\n  ")
    text.append("[ ]", style="dim" if muted else "")
    text.append(" ")
    if muted:
        text.append(title, style="dim italic")
    else:
        text.append(title)


def _format_todo_lines(text: Text, result: dict[str, Any], args: Any = None) -> None:
    """Append todo list lines to the rendering Text.

    Priority order:
    1) Real todos in result["todos"] -> render with status markers.
    2) LLM passed entries in args but backend filtered them all out
       (result["created_count"] == 0 with todos empty) -> render the
       raw LLM intent as dim italic so the user sees the planned plan.
    3) Otherwise -> '(plan updated, nothing to add)' as a fallback.
    4) For list_todos on a fresh agent -> 'No todos yet'.
    """
    todos = result.get("todos")
    if isinstance(todos, list) and todos:
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
        return

    # Result has no todos. Look at the raw LLM args.
    created_count = result.get("created_count")
    if created_count is not None and args is not None:
        raw_titles = _extract_arg_titles(args)
        if raw_titles:
            for title in raw_titles:
                _render_one_entry(text, title, muted=True)
            text.append("\n  ")
            text.append("(filtered by backend)", style="dim italic")
            return

    if created_count is not None:
        text.append("\n  ")
        text.append("(plan updated, nothing to add)", style="dim italic")
        return

    # list_todos on a fresh agent
    text.append("\n  ")
    text.append("No todos yet", style="dim italic")


def _render_create_or_update(
    title: str,
    title_style: str,
    tool_data: dict[str, Any],
    error_default: str,
    pending_label: str,
) -> Static:
    """Common render path for CreateTodo / UpdateTodo.

    Always renders a Static so the user can see every planning step.
    """
    result = tool_data.get("result")
    args = tool_data.get("args")

    text = Text()
    text.append("📋 ")
    text.append(title, style=f"bold {title_style}")

    if isinstance(result, str) and result.strip():
        text.append("\n  ")
        text.append(result.strip(), style="dim")
    elif isinstance(result, dict):
        if result.get("success"):
            _format_todo_lines(text, result, args=args)
        else:
            error = result.get("error", error_default)
            text.append("\n  ")
            text.append(error, style="#ef4444")
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
    def render(cls, tool_data: dict[str, Any]) -> Static:
        return _render_create_or_update(
            title="Todo",
            title_style="#a78bfa",
            tool_data=tool_data,
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
    def render(cls, tool_data: dict[str, Any]) -> Static:
        return _render_create_or_update(
            title="Todo Updated",
            title_style="#a78bfa",
            tool_data=tool_data,
            error_default="Failed to update todo",
            pending_label="Updating...",
        )


@register_tool_renderer
class MarkTodoDoneRenderer(BaseToolRenderer):
    tool_name: ClassVar[str] = "mark_todo_done"
    css_classes: ClassVar[list[str]] = ["tool-call", "todo-tool"]

    @classmethod
    def render(cls, tool_data: dict[str, Any]) -> Static:
        return _render_create_or_update(
            title="Todo Completed",
            title_style="#a78bfa",
            tool_data=tool_data,
            error_default="Failed to mark todo done",
            pending_label="Marking done...",
        )


@register_tool_renderer
class MarkTodoPendingRenderer(BaseToolRenderer):
    tool_name: ClassVar[str] = "mark_todo_pending"
    css_classes: ClassVar[list[str]] = ["tool-call", "todo-tool"]

    @classmethod
    def render(cls, tool_data: dict[str, Any]) -> Static:
        return _render_create_or_update(
            title="Todo Reopened",
            title_style="#f59e0b",
            tool_data=tool_data,
            error_default="Failed to reopen todo",
            pending_label="Reopening...",
        )


@register_tool_renderer
class DeleteTodoRenderer(BaseToolRenderer):
    tool_name: ClassVar[str] = "delete_todo"
    css_classes: ClassVar[list[str]] = ["tool-call", "todo-tool"]

    @classmethod
    def render(cls, tool_data: dict[str, Any]) -> Static:
        return _render_create_or_update(
            title="Todo Removed",
            title_style="#94a3b8",
            tool_data=tool_data,
            error_default="Failed to remove todo",
            pending_label="Removing...",
        )
