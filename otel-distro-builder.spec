# PyInstaller spec for otel-distro-builder CLI (one-file binary).
# Run from repo root: pyinstaller otel-distro-builder.spec
# Package data must appear under sys._MEIPASS/builder/ and builder/src/ (see builder/src/resources.py).

import os

block_cipher = None

# Paths relative to repo root (run pyinstaller from repo root)
repo_root = os.getcwd()
builder_dir = os.path.join(repo_root, 'builder')
builder_src = os.path.join(builder_dir, 'src')

# Package data for frozen binary (dest paths match resources._frozen_base() layout)
datas = [
    (os.path.join(builder_dir, 'versions.yaml'), 'builder'),
    (os.path.join(builder_dir, 'templates'), 'builder/templates'),
    (os.path.join(builder_src, 'components.yaml'), 'builder/src'),
    (os.path.join(builder_src, 'bindplane_components.yaml'), 'builder/src'),
]

# Entry point: run via package so main.py's relative imports work when frozen
a = Analysis(
    [os.path.join(repo_root, 'cli_entry.py')],
    pathex=[repo_root],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'builder.src.main',
        'builder.src.build',
        'builder.src.version',
        'builder.src.resources',
        'builder.src.platforms',
        'builder.src.logger',
        'builder.src.manifest_generator',
        'builder.src.component_registry',
        'builder.src.config_parser',
        'builder.src.goreleaser_downloader',
        'builder.src.ocb_downloader',
        'builder.src.supervisor_downloader',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='otel-distro-builder',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
