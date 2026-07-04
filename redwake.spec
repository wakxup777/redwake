# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

project_root = Path(SPECPATH)
redwake_root = project_root / 'redwake'

datas = []

for md_file in redwake_root.rglob('skills/**/*.md'):
    rel_path = md_file.relative_to(project_root)
    datas.append((str(md_file), str(rel_path.parent)))

for jinja_file in redwake_root.rglob('agents/**/*.jinja'):
    rel_path = jinja_file.relative_to(project_root)
    datas.append((str(jinja_file), str(rel_path.parent)))

for xml_file in redwake_root.rglob('*.xml'):
    rel_path = xml_file.relative_to(project_root)
    datas.append((str(xml_file), str(rel_path.parent)))

for tcss_file in redwake_root.rglob('*.tcss'):
    rel_path = tcss_file.relative_to(project_root)
    datas.append((str(tcss_file), str(rel_path.parent)))

# Runtime hooks: strip __doc__/metadata from license module
import os as _os
_rthooks = []
_rthook_path = _os.path.join(SPECPATH, 'rthooks', 'rthook_redwake_antire.py')
if _os.path.exists(_rthook_path):
    _rthooks.append(_rthook_path)

datas += collect_data_files('textual')

datas += collect_data_files('tiktoken')
datas += collect_data_files('tiktoken_ext')

datas += collect_data_files('litellm')

datas += collect_data_files('agents', includes=['**/*.md', '**/*.jinja', '**/*.json'])

hiddenimports = [
    # Core dependencies
    'litellm',
    'litellm.llms',
    'litellm.llms.openai',
    'litellm.llms.anthropic',
    'litellm.llms.vertex_ai',
    'litellm.llms.bedrock',
    'litellm.utils',
    'litellm.caching',

    # Textual TUI
    'textual',
    'textual.app',
    'textual.widgets',
    'textual.containers',
    'textual.screen',
    'textual.binding',
    'textual.reactive',
    'textual.css',
    'textual._text_area_theme',

    # Rich console
    'rich',
    'rich.console',
    'rich.panel',
    'rich.text',
    'rich.markup',
    'rich.style',
    'rich.align',
    'rich.live',

    # Pydantic
    'pydantic',
    'pydantic.fields',
    'pydantic_core',
    'email_validator',

    # Docker
    'docker',
    'docker.api',
    'docker.models',
    'docker.errors',

    # HTTP/Networking
    'httpx',
    'httpcore',
    'requests',
    'urllib3',
    'certifi',

    # Jinja2 templating
    'jinja2',
    'jinja2.ext',
    'markupsafe',

    # XML parsing
    'xmltodict',
    'defusedxml',
    'defusedxml.ElementTree',

    # Syntax highlighting
    'pygments',
    'pygments.lexers',
    'pygments.styles',
    'pygments.util',

    # Tiktoken (for token counting)
    'tiktoken',
    'tiktoken_ext',
    'tiktoken_ext.openai_public',

    # Tenacity retry
    'tenacity',

    # CVSS scoring
    'cvss',

    # RedWake modules
    'redwake',
    'redwake.interface',
    'redwake.interface.main',
    'redwake.interface.cli',
    'redwake.interface.tui',
    'redwake.interface.tui.app',
    'redwake.interface.tui.history',
    'redwake.interface.tui.live_view',
    'redwake.interface.tui.messages',
    'redwake.interface.tui.renderers',
    'redwake.interface.tui.renderers.agent_message_renderer',
    'redwake.interface.tui.renderers.agents_graph_renderer',
    'redwake.interface.tui.renderers.base_renderer',
    'redwake.interface.tui.renderers.finish_renderer',
    'redwake.interface.tui.renderers.notes_renderer',
    'redwake.interface.tui.renderers.proxy_renderer',
    'redwake.interface.tui.renderers.registry',
    'redwake.interface.tui.renderers.reporting_renderer',
    'redwake.interface.tui.renderers.thinking_renderer',
    'redwake.interface.tui.renderers.todo_renderer',
    'redwake.interface.tui.renderers.user_message_renderer',
    'redwake.interface.tui.renderers.web_search_renderer',
    'redwake.interface.utils',
    'redwake.agents',
    'redwake.agents.factory',
    'redwake.agents.prompt',
    'redwake.config.models',
    'redwake.core',
    'redwake.core.agents',
    'redwake.core.execution',
    'redwake.core.inputs',
    'redwake.core.paths',
    'redwake.core.runner',
    'redwake.core.sessions',
    'redwake.report',
    'redwake.report.dedupe',
    'redwake.report.state',
    'redwake.report.writer',
    'redwake.runtime',
    'redwake.runtime.backends',
    'redwake.runtime.caido_bootstrap',
    'redwake.runtime.docker_client',
    'redwake.runtime.session_manager',
    'redwake.telemetry',
    'redwake.telemetry.logging',
    'redwake.telemetry.posthog',
    'redwake.tools',
    'redwake.tools.agents_graph.tools',
    'redwake.tools.finish.tool',
    'redwake.tools.notes.tools',
    'redwake.tools.proxy._calls',
    'redwake.tools.proxy.tools',
    'redwake.tools.python.tool',
    'redwake.tools.reporting.tool',
    'redwake.tools.thinking.tool',
    'redwake.tools.todo.tools',
    'redwake.tools.web_search.tool',
    'redwake.skills',
]

hiddenimports += collect_submodules('litellm')
hiddenimports += collect_submodules('textual')
hiddenimports += collect_submodules('rich')
hiddenimports += collect_submodules('pydantic')
hiddenimports += collect_submodules('pygments')

excludes = [
    # Sandbox-only packages
    'playwright',
    'playwright.sync_api',
    'playwright.async_api',
    'IPython',
    'ipython',
    'libtmux',
    'pyte',
    'openhands_aci',
    'openhands-aci',
    'numpydoc',

    # Google Cloud / Vertex AI
    'google.cloud',
    'google.cloud.aiplatform',
    'google.api_core',
    'google.auth',
    'google.oauth2',
    'google.protobuf',
    'grpc',
    'grpcio',
    'grpcio_status',

    # Test frameworks
    'pytest',
    'pytest_asyncio',
    'pytest_cov',
    'pytest_mock',

    # Development tools
    'mypy',
    'ruff',
    'black',
    'isort',
    'pylint',
    'pyright',
    'bandit',
    'pre_commit',

    # Unnecessary for runtime
    'tkinter',
    'matplotlib',
    'numpy',
    'pandas',
    'scipy',
    'PIL',
    'cv2',
]

a = Analysis(
    ['redwake/interface/main.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=_rthooks,
    excludes=excludes,
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='redwake',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
