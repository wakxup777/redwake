import atexit
import contextlib
import logging
import signal
import sys
import threading
import time
from typing import Any

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

from redwake.config import load_settings
from redwake.core.runner import run_redwake_scan
from redwake.report.state import ReportState, set_global_report_state
from redwake.runtime import session_manager

from .utils import (
    build_live_stats_text,
    format_vulnerability_report,
)


logger = logging.getLogger(__name__)


def _resolve_sandbox_image() -> str:
    image = load_settings().runtime.image
    if not image:
        raise RuntimeError(
            "redwake_image is not configured. Set it in ~/.config/redwake/cli-config.json.",
        )
    return image


async def _render_demo_tui() -> None:
    """Render the TUI panels with mock data so users can preview the look."""
    console = Console()

    start_text = Text()
    start_text.append("Penetration test initiated", style="bold #ef4444")

    target_line = Text()
    target_line.append("Target   ", style="dim")
    target_line.append("http://testphp.vulnweb.com (demo)", style="bold white")

    output_line = Text()
    output_line.append("Output   ", style="dim")
    output_line.append("redwake_runs/demo/", style="#60a5fa")

    note_line = Text()
    note_line.append("\n", style="dim")
    note_line.append("Vulnerabilities will be displayed in real-time.", style="dim")

    startup_panel = Panel(
        Text.assemble(start_text, "\n\n", target_line, "\n", output_line, note_line),
        title="[bold #ef4444]REDWAKE",
        title_align="right",
        border_style="#ef4444",
        padding=(1, 2),
    )

    console.print("\n")
    console.print(startup_panel)
    console.print()

    # Live status panel (mock)
    status_text = Text()
    status_text.append("Penetration test in progress", style="bold #ef4444")
    status_text.append("\n\n")
    status_text.append("Status   ", style="dim")
    status_text.append("running recon (3/5 agents)", style="white")
    status_text.append("\n")
    status_text.append("Found    ", style="dim")
    status_text.append("2 vulnerabilities", style="bold #ef4444")
    status_text.append("\n")
    status_text.append("Elapsed  ", style="dim")
    status_text.append("00:02:31", style="white")
    status_text.append("\n")
    status_text.append("Budget   ", style="dim")
    status_text.append("$0.14 / $2.00", style="white")

    live_panel = Panel(
        status_text,
        title="[bold #ef4444]REDWAKE",
        title_align="right",
        border_style="#ef4444",
        padding=(1, 2),
    )
    console.print(live_panel)
    console.print()

    # Vulnerability panel (mock)
    vuln_text = Text()
    vuln_text.append("VULN-001", style="bold #ef4444")
    vuln_text.append("  ", style="dim")
    vuln_text.append("HIGH", style="bold #ef4444")
    vuln_text.append("  CVSS 7.5\n\n", style="dim")
    vuln_text.append("OpenAI-Compatible Models Endpoint\n", style="bold white")
    vuln_text.append(
        "The OpenAI-compatible /api/v1/models endpoint is exposed without "
        "authentication and returns the full catalog of AI models routed by "
        "the platform. The response tasks: (a) every upstream provider "
        "identifier...",
        style="white",
    )
    vuln_panel = Panel(
        vuln_text,
        title="[bold #ef4444]VULN-001",
        title_align="right",
        border_style="#ef4444",
        padding=(1, 2),
    )
    console.print(vuln_panel)
    console.print()
    console.print("[dim]This is a preview — no scan was started.[/]")


async def run_cli(args: Any) -> None:  # noqa: PLR0915
    if getattr(args, "demo", False):
        await _render_demo_tui()
        return

    console = Console()

    start_text = Text()
    start_text.append("Penetration test initiated", style="bold #ef4444")

    target_line = Text()
    target_line.append("Target   ", style="dim")
    if len(args.targets_info) == 1:
        target_line.append(args.targets_info[0]["original"], style="bold white")
    else:
        target_line.append(f"{len(args.targets_info)} targets", style="bold white")
        for target_info in args.targets_info:
            target_line.append("\n          ")
            target_line.append(target_info["original"], style="white")

    output_line = Text()
    output_line.append("Output   ", style="dim")
    output_line.append(f"redwake_runs/{args.run_name}", style="#60a5fa")

    note_line = Text()
    note_line.append("\n", style="dim")
    note_line.append("Vulnerabilities will be displayed in real-time.", style="dim")

    startup_panel = Panel(
        Text.assemble(
            start_text,
            "\n\n",
            target_line,
            "\n",
            output_line,
            note_line,
        ),
        title="[bold #ef4444]REDWAKE",
        title_align="right",
        border_style="#ef4444",
        padding=(1, 2),
    )

    console.print("\n")
    console.print(startup_panel)
    console.print()

    scan_mode = getattr(args, "scan_mode", "deep")

    scan_config: dict[str, Any] = {
        "scan_id": args.run_name,
        "targets": args.targets_info,
        "user_instructions": args.instruction or "",
        "run_name": args.run_name,
        "diff_scope": getattr(args, "diff_scope", {"active": False}),
        "scan_mode": scan_mode,
        "non_interactive": bool(getattr(args, "non_interactive", False)),
        "local_sources": getattr(args, "local_sources", None) or [],
        "scope_mode": getattr(args, "scope_mode", "auto"),
        "diff_base": getattr(args, "diff_base", None),
        "resume_instruction": getattr(args, "user_explicit_instruction", None) or "",
    }

    report_state = ReportState(args.run_name)
    report_state.hydrate_from_run_dir()
    report_state.set_scan_config(scan_config)
    report_state.save_run_data()

    def display_vulnerability(report: dict[str, Any]) -> None:
        report_id = report.get("id", "unknown")

        vuln_text = format_vulnerability_report(report)

        vuln_panel = Panel(
            vuln_text,
            title=f"[bold red]{report_id.upper()}",
            title_align="left",
            border_style="red",
            padding=(1, 2),
        )

        console.print(vuln_panel)
        console.print()

    report_state.vulnerability_found_callback = display_vulnerability

    def cleanup_on_exit() -> None:
        report_state.cleanup()

    def signal_handler(_signum: int, _frame: Any) -> None:
        report_state.cleanup(status="interrupted")
        sys.exit(1)

    atexit.register(cleanup_on_exit)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    if hasattr(signal, "SIGHUP"):
        signal.signal(signal.SIGHUP, signal_handler)

    set_global_report_state(report_state)

    def create_live_status() -> Panel:
        status_text = Text()
        status_text.append("Penetration test in progress", style="bold #ef4444")
        status_text.append("\n\n")

        stats_text = build_live_stats_text(report_state)
        if stats_text:
            status_text.append(stats_text)

        return Panel(
            status_text,
            title="[bold #ef4444]REDWAKE",
            title_align="right",
            border_style="#ef4444",
            padding=(1, 2),
        )

    try:
        console.print()

        with Live(
            create_live_status(), console=console, refresh_per_second=2, transient=False
        ) as live:
            stop_updates = threading.Event()

            def update_status() -> None:
                while not stop_updates.is_set():
                    try:
                        live.update(create_live_status())
                        time.sleep(2)
                    except Exception:
                        break

            update_thread = threading.Thread(target=update_status, daemon=True)
            update_thread.start()

            try:
                logger.info(
                    "CLI launching scan: run_name=%s targets=%d interactive=%s",
                    args.run_name,
                    len(scan_config.get("targets") or []),
                    bool(getattr(args, "interactive", False)),
                )
                await run_redwake_scan(
                    scan_config=scan_config,
                    scan_id=args.run_name,
                    image=_resolve_sandbox_image(),
                    local_sources=getattr(args, "local_sources", None) or [],
                    interactive=bool(getattr(args, "interactive", False)),
                    max_budget_usd=getattr(args, "max_budget_usd", None),
                )
            finally:
                stop_updates.set()
                update_thread.join(timeout=1)
                with contextlib.suppress(Exception):
                    await session_manager.cleanup(args.run_name)

    except Exception as e:
        console.print(f"[bold red]Error during penetration test:[/] {e}")
        raise

    if report_state.final_scan_result:
        console.print()

        final_report_text = Text()
        final_report_text.append("Penetration test summary", style="bold #60a5fa")

        final_report_panel = Panel(
            Text.assemble(
                final_report_text,
                "\n\n",
                report_state.final_scan_result,
            ),
            title="[bold white]REDWAKE",
            title_align="left",
            border_style="#60a5fa",
            padding=(1, 2),
        )

        console.print(final_report_panel)
        console.print()
