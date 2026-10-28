# -*- mode: python ; coding: utf-8 -*-
import sys

a = Analysis(
    ["candidate_main.py"],
    pathex=[],
    binaries=[],
    datas=[("resources/arena/english.json", "resources/arena"), ("resources/datasets/*.json", "resources/datasets"), ("resources/icons/draft.png", "resources/icons"), ("themes/*.tcl", "themes"), ("resources/localization/cards.json", "resources/localization"), ("fixtures/localization/FRA_QuickDraft_All_Data.json", "fixtures/localization"), ("fixtures/localization/fra-pack.json", "fixtures/localization"), ("fixtures/localization/fixed-dataset.json", "fixtures/localization"), ("LICENSE", ".")],
    hiddenimports=[




        "PIL._tkinter_finder",
        "PIL._imagingtk_finder",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

if sys.platform == "darwin":
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name="MTGA_17Lands_ZH_Candidate",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
    )
    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=False,
        name="MTGA_17Lands_ZH_Candidate",
    )
    app = BUNDLE(
        coll,
        name="MTGA_17Lands_ZH_Candidate.app",
        icon="resources/icons/draft.icns",
        bundle_identifier="local.neil.mtga17lands.zh.candidate",
        info_plist={
            "CFBundleShortVersionString": "4.23.3",
            "CFBundleVersion": "42303",
            "NSHighResolutionCapable": "True",
            "LSBackgroundOnly": "False",
        },
    )
else:
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name="MTGA_17Lands_ZH_Candidate",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
    )
