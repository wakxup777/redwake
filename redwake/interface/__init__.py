"""Public package surface for ``redwake.interface``.

Importing this package MUST NOT have any side effects (notably, it must not
invoke ``main()``). CLI dispatch is handled by ``python -m redwake.interface.main``
or via the ``redwake`` console script defined in ``pyproject.toml``.
"""

from __future__ import annotations


__all__: list[str] = []
