# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Change this path to point to your downloaded Soulstruct repo (no trailing backslashes).
SOULSTRUCT_PATH = "C:\\Dark Souls\\soulstruct-git"

added_files = [
    (f"{SOULSTRUCT_PATH}\\VERSION", "."),
    (f"{SOULSTRUCT_PATH}\\soulstruct\\base\\ai\\lua\\x64\\DSLuaDecompiler.exe", "base\\ai\\lua\\x64"),
    (f"{SOULSTRUCT_PATH}\\soulstruct\\base\\ai\\lua\\x64\\Lua.exe", "base\\ai\\lua\\x64"),
    (f"{SOULSTRUCT_PATH}\\soulstruct\\base\\ai\\lua\\x64\\LuaC.exe", "base\\ai\\lua\\x64"),
    (f"{SOULSTRUCT_PATH}\\soulstruct\\base\\ai\\lua\\x64\\SoulsFormats.dll", "base\\ai\\lua\\x64"),
    (f"{SOULSTRUCT_PATH}\\soulstruct\\base\\ai\\lua\\x86\\lua50.dll", "base\\ai\\lua\\x86"),
    (f"{SOULSTRUCT_PATH}\\soulstruct\\base\\ai\\lua\\x86\\lua50.exe", "base\\ai\\lua\\x86"),
    (f"{SOULSTRUCT_PATH}\\soulstruct\\base\\ai\\lua\\x86\\luac50.exe", "base\\ai\\lua\\x86"),
    (f"{SOULSTRUCT_PATH}\\soulstruct\\base\\ezstate\\esd\\functions.pyi", "base\\ezstate\\esd"),
    (f"{SOULSTRUCT_PATH}\\soulstruct\\darksouls1ptde\\params\\resources\\darksouls1ptde.paramdefbnd", "darksouls1ptde\\params\\resources"),
    (f"{SOULSTRUCT_PATH}\\soulstruct\\darksouls1ptde\\events", "darksouls1ptde\\events"),
    (f"{SOULSTRUCT_PATH}\\soulstruct\\darksouls1r\\events", "darksouls1r\\events"),
    (f"{SOULSTRUCT_PATH}\\soulstruct\\darksouls1r\\params\\resources\\darksouls1r.paramdefbnd.dcx", "darksouls1r\\params\\resources"),
    (f"{SOULSTRUCT_PATH}\\soulstruct\\bloodborne\\events", "bloodborne\\events"),
    (f"{SOULSTRUCT_PATH}\\soulstruct\\bloodborne\\params\\resources\\bloodborne.paramdefbnd.dcx", "bloodborne\\params\\resources"),
    (f"{SOULSTRUCT_PATH}\\soulstruct\\eldenring\\events", "eldenring\\events"),
]

a = Analysis(
    [f"{SOULSTRUCT_PATH}\\soulstruct\\__main__.py"],
    pathex=[SOULSTRUCT_PATH],
    binaries=[],
    datas=added_files,
    hiddenimports=[
        "soulstruct_gui.darksouls1ptde.project",
        "soulstruct_gui.darksouls1r.project",
        "soulstruct_gui.bloodborne.project",
        "soulstruct_gui.eldenring.project",
    ],
    hookspath=[],
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
    name="SoulstructProjectEditor",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    icon="soulstruct_gui\\base\\project\\resources\\soulstruct.ico",
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
)
