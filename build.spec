# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 打包脚本（one-folder / windowed，无控制台黑窗）。

生成：dist/AT小PP/AT小PP.exe
用法：pyinstaller build.spec
"""

import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None
release_assets = os.path.join("build_assets", "optimized_assets")
assets_source = release_assets if os.path.isdir(release_assets) else "assets"


def _without_package_tests(name):
    return ".test" not in name.lower() and ".selftest" not in name.lower()

hiddenimports = [
    "PyQt6.QtCore", "PyQt6.QtGui", "PyQt6.QtWidgets", "PyQt6.QtMultimedia",
    "winreg",
    "Crypto.Cipher.DES",
    "Crypto.Cipher._raw_des",
] + collect_submodules("comtypes", filter=_without_package_tests) \
  + collect_submodules("opencc")

a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=[],
    datas=[
        (assets_source, "assets"),
        ("data/character_config.json", "data"),
        ("data/settings.json", "data"),
        ("data/voice/Generated Voice Media", "data/voice/Generated Voice Media"),
        ("data/voice/Upload Voice Media", "data/voice/Upload Voice Media"),
        ("uninstall_at_xiaopp.bat", "."),
        ("uninstall_launcher.vbs", "."),
    ] + collect_data_files("opencc") \
      + collect_data_files("pypinyin"),
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # 当前发行版只保留语音模仿接口，不内置 GPT-SoVITS 运行时/模型。
    # 这些包只用于离线生成或模型推理，排除后可减少打包体积和分析时间。
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
    [],
    exclude_binaries=True,
    name="AT小PP",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # 关键：不显示 cmd 黑窗
    icon="build_assets/app_icon.ico",
    version="version_info.txt",
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="AT小PP",
)
