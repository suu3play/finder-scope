"""
Finder Scope メインエントリーポイント
"""
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

# パッケージパスを追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ui import MainWindow


def main() -> None:
    """メイン関数"""
    app = QApplication(sys.argv)
    
    # アプリケーション情報設定
    app.setApplicationName("Finder Scope")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Claude Code")
    
    # メインウィンドウ作成・表示
    window = MainWindow()
    window.show()
    
    # イベントループ開始
    sys.exit(app.exec())


if __name__ == "__main__":
    main()