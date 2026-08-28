"""系统托盘：隐身恢复入口、设置、退出，以及闹钟/提醒的气泡通知。"""

import os

from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QAction
from PyQt6.QtGui import QIcon, QPixmap, QImage
from PyQt6.QtCore import Qt

from app.core import config, assets
from app.core.i18n import tr
from app.ui.common import keep_on_top


def _make_icon() -> QIcon:
    p = assets.find_image("桌面图标")
    if p and os.path.exists(p):
        pix = QPixmap(p).scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio,
                                Qt.TransformationMode.SmoothTransformation)
        return QIcon(pix)
    img = QImage(32, 32, QImage.Format.Format_ARGB32)
    img.fill(Qt.GlobalColor.transparent)
    return QIcon(QPixmap.fromImage(img))


class TrayManager(QSystemTrayIcon):
    def __init__(self, ctx, parent=None):
        super().__init__(_make_icon(), parent)
        self.ctx = ctx
        self.setToolTip(config.character.app_name)
        self._build_menu()
        self.activated.connect(self._on_activate)

    def _build_menu(self):
        menu = QMenu()
        menu.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        menu.aboutToShow.connect(lambda m=menu: keep_on_top(m, bring_to_front=True))
        menu.setStyleSheet(
            "QMenu{background:#fff;border:1px solid rgba(249,117,16,0.3);border-radius:10px;padding:6px;}"
            "QMenu::item{padding:7px 18px 7px 10px;border-radius:8px;color:#3d2b1f;font-size:13px;}"
            "QMenu::item:selected{background:rgba(249,117,16,0.14);color:#f97510;}"
        )
        todo_a = QAction("📋 " + tr("待办"), menu)
        todo_a.triggered.connect(lambda: self.ctx.open_todo())
        menu.addAction(todo_a)
        alarm_a = QAction("⏰ " + tr("闹钟"), menu)
        alarm_a.triggered.connect(lambda: self.ctx.open_alarm())
        menu.addAction(alarm_a)
        timer_a = QAction("⏱️ " + tr("计时"), menu)
        timer_a.triggered.connect(lambda: self.ctx.open_timer())
        menu.addAction(timer_a)
        set_a = QAction("⚙️ " + tr("设置"), menu)
        set_a.triggered.connect(lambda: self.ctx.open_settings())
        menu.addAction(set_a)
        quit_a = QAction("🚪 " + tr("退出"), menu)
        quit_a.triggered.connect(lambda: self.ctx.quit_app())
        menu.addAction(quit_a)
        self.setContextMenu(menu)

    def retranslate_ui(self):
        self._build_menu()

    def _on_activate(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.ctx.pet_hidden():
                self.ctx.restore_pet()
            else:
                self.ctx.hide_pet()

    def notify(self, title: str, message: str):
        self.showMessage(title, message, self.icon(), 4000)
