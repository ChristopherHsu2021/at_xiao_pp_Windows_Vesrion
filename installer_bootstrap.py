"""AT小PP 自定义安装器外壳。

用户双击这个 exe 时，只显示项目自定义 PyQt 安装向导；实际落盘、卸载注册表、
Windows 设置应用列表由内置 Inno Setup 安装包在后台静默完成。
"""

import os
import sys

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from app.core import assets, config
from app.ui.install_window import InstallerWindow, acquire_single_instance, show_running_warning
from app.ui.style import apply_theme


INNER_SETUP = "at_xiaopp_inner_setup.exe"


def _resource_dir():
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def main():
    setup_path = os.path.join(_resource_dir(), INNER_SETUP)
    app = QApplication(sys.argv)
    app.setApplicationName(config.character.app_name)
    app.setQuitOnLastWindowClosed(False)
    icon_path = assets.find_image("桌面图标")
    if icon_path:
        app.setWindowIcon(QIcon(icon_path))
    apply_theme(app)

    if not acquire_single_instance("Local\\ATXiaoPPInstaller"):
        show_running_warning("安装正在进行捏~")
        return 0

    window = InstallerWindow(inno_setup_path=setup_path)
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
