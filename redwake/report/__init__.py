"""Report/finding helpers."""

from redwake.report.dedupe import check_duplicate
from redwake.report.state import ReportState, get_global_report_state, set_global_report_state


__all__ = [
    "ReportState",
    "check_duplicate",
    "get_global_report_state",
    "set_global_report_state",
]
