# commodity_lab.spec - PyInstaller配置文件
# 使用方式: pyinstaller commodity_lab.spec

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# 项目信息
APP_NAME = "Commodity-Lab"
ENTRY_POINT = os.path.join("app", "desktop_launcher.py")
ICON_PATH = os.path.join("app", "assets", "icon.ico") if os.path.exists(os.path.join("app", "assets", "icon.ico")) else None

# 数据文件收集
datas = [
    (os.path.join("app"), "app"),
    (os.path.join("core"), "core"),
    (os.path.join("data"), "data"),
]

# 隐藏导入模块
hiddenimports = [
    'streamlit',
    'streamlit.web',
    'streamlit.web.server',
    'streamlit.components',
    'duckdb',
    'pandas',
    'numpy',
    'plotly',
    'plotly.graph_objects',
    'plotly.express',
    'yfinance',
    'pytz',
    'dateutil',
]

# 构建a生成的Analysis对象
a = Analysis(
    [ENTRY_POINT],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludedimports=[],
    noarchive=False,
    optimize=0,
)

# 构建打包的执行文件
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# 创建exe
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Windows不显示控制台
    disable_windowed_traceback=False,
    icon=ICON_PATH,
    codesign_identity=None,
    entitlements_file=None,
)

# 收集额外的streamlit配置
streamlit_data = collect_data_files('streamlit')
for src, dest in streamlit_data:
    if (src, dest) not in exe.datas:
        exe.datas.append((src, dest))
