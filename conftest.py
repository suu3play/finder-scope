"""
pytest設定ファイル
"""
import sys
import os
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
os.environ['PYTHONPATH'] = str(project_root)

# Qtアプリケーション設定
import pytest
from PySide6.QtWidgets import QApplication

@pytest.fixture(scope="session", autouse=True)
def qapp():
    """QApplicationのセッション単位フィクスチャ"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    # アプリケーションの終了処理は必要に応じて実装