# -*- mode: python ; coding: utf-8 -*-
"""自定义安装器外壳打包脚本（one-file / windowed，无控制台黑窗）。

生成：release/AT小PP-version-1.0-setup.exe
用法：pyinstaller bootstrap.spec --clean --noconfirm
"""

import os

from PyInstaller.utils.hooks import collect_submodules

block_cipher = None
installer_assets = "build_assets/installer_assets"
assets_source = installer_assets if os.path.isdir(installer_assets) else "assets"


def _without_package_tests(name):
    return ".test" not in name.lower() and ".selftest" not in name.lower()


hiddenimports = [
    "PyQt6.QtCore",
    "PyQt6.QtGui",
    "PyQt6.QtWidgets",
    "winreg",
] + collect_submodules("comtypes", filter=_without_package_tests)

a = Analysis(
    ["installer_bootstrap.py"],
    pathex=["."],
    binaries=[],
    datas=[
        (assets_source, "assets"),
        ("release/at_xiaopp_inner_setup.exe", "."),
        ("uninstall_at_xiaopp.bat", "."),
        ("uninstall_launcher.vbs", "."),
    ],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "my_local_tts",
        "numpy",
        "soundfile",
        "torch",
        "torchaudio",
        "librosa",
        "scipy",
        "numba",
        "llvmlite",
        "onnxruntime",
        "transformers",
        "gradio",
        "fastapi",
        "uvicorn",
        "Crypto",
        "opencc",
    ],
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
    a.datas,
    [],
    name="AT小PP-version-1.0-setup",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon="build_assets/app_icon.ico",
    version="version_info.txt",
    uac_admin=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
