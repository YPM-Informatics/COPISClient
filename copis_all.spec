# -*- mode: python ; coding: utf-8 -*-


copis_client_a = Analysis(
    ['copisclient.py'],
    pathex=[],
    binaries=[],
    datas=[('img', 'img'), ('profiles', 'profiles'), ('db', 'db'), ('copis.ini', '.'), ('proxies', 'proxies'), ('canon', 'canon')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pose_img_linker_a = Analysis(
    ['pose_img_linker.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

composer_a = Analysis(
    ['compose.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

MERGE( (copis_client_a, 'copis_client', 'copis_client'), (pose_img_linker_a, 'pose_img_linker', 'pose_img_linker'), (composer_a, 'composer', 'composer') )

copis_client_pyz = PYZ(copis_client_a.pure)

copis_client_exe = EXE(
    copis_client_pyz,
    copis_client_a.dependencies,
    copis_client_a.scripts,
    [],
    exclude_binaries=True,
    name='copisclient',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['img\\client_logo.ico'],
    contents_directory='client',
)
copis_client_coll = COLLECT(
    copis_client_exe,
    copis_client_a.binaries,
    copis_client_a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='copisclient',
)


pose_img_linker_pyz = PYZ(pose_img_linker_a.pure)

pose_img_linker_exe = EXE(
    pose_img_linker_pyz,
    pose_img_linker_a.dependencies,
    pose_img_linker_a.scripts,
    [],
    exclude_binaries=True,
    name='pose_img_linker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    contents_directory='client',
)

pose_img_linker_coll = COLLECT(
    pose_img_linker_exe,
    pose_img_linker_a.binaries,
    pose_img_linker_a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='pose_img_linker',
)


composer_pyz = PYZ(composer_a.pure)

composer_exe = EXE(
    composer_pyz,
    composer_a.dependencies,
    composer_a.scripts,
    [],
    exclude_binaries=True,
    name='compose',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    contents_directory='client',
)
composer_coll = COLLECT(
    composer_exe,
    composer_a.binaries,
    composer_a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='compose',
)