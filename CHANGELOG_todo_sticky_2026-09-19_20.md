# 变更日志：任务清单 / 便签卡片模块（2026-09-19 16:22 → 2026-09-20 01:02）

> 用途：梳理本时段内对「任务清单列表页」「添加/编辑页」「便签卡片窗口」及其右键菜单、i18n 所做的**全部代码改动**，描述**最终落定状态**（对比改动前原始实现）。
> 重点面向**跨平台（macOS）迁移**：凡涉及 Windows 专属 API / 字体 / 窗口层级的地方，均在文末「跨平台迁移重点」中单列。
> 阅读约定：T = 任务清单（TodoWindow / TaskRow），S = 便签卡片（StickyNoteWindow / StickyContextMenu），RE = 富文本编辑器（RichEditor），CM = 共享右键菜单（EditContextMenu），I18N = 多语言（i18n.py）。

---

## 0. 范围与基线

- 本日志覆盖 **2026-09-19 16:22 起至 2026-09-20 01:02** 之间的改动。同一天更早期还有多轮 UI 重构（列表页重构、添加/编辑页、卜卜 PeekCard 渲染、便签窗口严格对齐 HTML、卡顿优化等），那些轮次的**最终代码形态**已体现在本日志涉及的文件里，但逐轮历史不在此展开。
- 所有改动目前**未 git 提交、未重新打包**（状态持续至今）。
- 涉及主文件：`app/ui/todo_window.py`、`app/ui/rich_editor.py`、`app/ui/common.py`、`app/ui/context_menu.py`、`app/core/i18n.py`；验证脚本：`atpp_validate.py` 及若干 `atpp_verify_*.py`。

---

## 1. 任务清单列表页（T）

### 1.1 列表行标题过长 → 省略号 + hover 滑动看全  【新增 ElideLabel】
- **文件**：`app/ui/todo_window.py` —— 新增 `class ElideLabel(QLabel)`；`TaskRow.__init__` 用 `ElideLabel` 替换原 `QLabel`；`_apply` 增加 `self.text.set_done(...)`。
- **原始**：标题是普通 `QLabel`。过长时被静默裁切（无省略号），且 `QLabel.minimumSizeHint()` 以全文宽度兜底，长标题会撑宽行 / 挤压或遮挡右侧的「提醒时间 + 优先级」标签。
- **最终方案**：
  - `ElideLabel` 覆盖 `minimumSizeHint()` 返回 `QSize(1, fm.height())`，横向 `sizePolicy = Ignored` → **允许被 HBoxLayout 压缩**，把空间让给右侧 `meta`（`TagLabel`，`Fixed/Fixed` 不收缩）→ 从布局根上**永不遮挡**提醒时间与优先级。
  - `paintEvent` 自绘三态：放得下→原文；放不下且未悬停→右侧 `ElideRight` 省略号；**悬停且被截断→整体左移 `offset` 露出中后段**（`QPropertyAnimation` 驱动，时长随超长幅度 1.2–6s）。
  - ⚠️ **绘制红线（踩坑）**：滑动矩形必须 `rect.adjusted(-off, 0, 0, 0)`（**只移左边界、右边界不动**）。若写成 `adjusted(-off,0,-off,0)`（整体平移），`drawText` 会在平移后的右边界二次裁切，offset 越大尾部越被截→「hover 也看不全」。实测旧写法在 max offset 时整段文字全在可视区外。
  - `set_done(bool)` 自绘删除线（对齐 `DONE_LABEL_QSS` 的 `line-through`）；`setText` 同步全文本 + tooltip 兜底。
  - `enterEvent`/`leaveEvent` 启停滑动；`leaveEvent` 复位 `offset=0`。
- **显示长度动态性**：因 `meta` 固定、`text` 可压缩，行宽不变时——有提醒时间 → meta 更宽 → 标题更短；无提醒 → meta 更窄 → 标题更长（自动随右侧内容变化）。
- **平台**：纯 Qt（QPainter / QPropertyAnimation / 子类），跨平台无碍。

### 1.2 列表行右侧「提醒时间 + 优先级」圆角胶囊 tag  【新增 TagLabel】
- **文件**：`todo_window.py` —— 新增 `class TagLabel(QLabel)`；`TaskRow._make_tag()` 返回 `TagLabel`；`_format_remind()` 格式化 `yyyy-MM-dd HH:mm`。
- **原始**：用 QSS `border-radius:999px`，被 Qt **完全忽略**（实测 999px 圆角=0，8px 才生效）→ 直角。
- **最终方案**：自绘圆角——`QPainter.drawRoundedRect(rect.adjusted(0,0,-1,-1), radius=8, radius=8)` + 居中绘字；`setSizePolicy(Fixed, Fixed)` + `setContentsMargins(10,3,10,3)` 保证文字不裁切、尺寸不收缩。提醒时间（有提醒才加 tag，无则不显示）与优先级（高/中/低）都用 `TagLabel`，两者圆角一致。
- **平台**：纯 Qt，跨平台无碍。

---

## 2. 添加/编辑页 + 便签 右键菜单统一（CM + I18N）

### 2.1 共享菜单基类 `EditContextMenu` + 全软件 i18n 排查
- **文件**：`app/ui/common.py`（新增 `EditContextMenu`）、`RE`（viewport 右键接管 + 合并双 eventFilter）、`i18n.py`（补 ~40 条词条）。
- **原始**：添加/编辑页内容框右键弹 **Qt 原生英文菜单**（Undo/Redo/…），与便签菜单不一致；大量界面文案未走 `tr()`。
- **最终方案**：
  - `EditContextMenu(QWidget, Qt.Popup)`：顶层弹出（白底 `#ffffff` + `border-radius:8px` + `QGraphicsDropShadowEffect` blur16/offset(0,4)/alpha46），含**原生编辑动作块**（撤销/重做/剪切/复制/粘贴/删除/全选 + 快捷键提示，文案 `tr()`）；子类 `_build_extra(lay)` 追加自定义项。`StickyContextMenu` 与编辑页共用此基类。
  - 隐藏 bug 修复：`RichEditor` 原定义了**两个同名 `eventFilter`**（后者覆盖前者）→ 焦点信号 + Windows 排版快捷键拦截其实是死代码；合并为唯一实现（焦点高亮 / Ctrl+B/I/U/S、Ctrl+L/E/R 快捷键 / 视口右键 / compact 按钮 hover）。
  - i18n：AST 扫描定位 29 处直传中文未 `tr()`，全部补包裹；补词条含富文本工具栏全套、字体/字号/文字颜色/高亮/自定义…/占位/链接输入/缓存/在线/今日已饮用 {n} 杯/触发成功捏/时间到捏… 并带 zh-TW/en 映射；品牌名 `AT小PP` 保持原样。
- **平台**：Qt Popup / QGraphicsDropShadowEffect / 子类，跨平台无碍。

### 2.2 「全选」英文文案 Select All → All
- **文件**：`app/core/i18n.py` 第 72 行：
  - 原：`"全选": ("全選", "Select All")`
  - 现：`"全选": ("全選", "All")`
- 验证：`atpp_validate.py` 英文菜单断言段补 `"All" in _en_texts`。

---

## 3. 便签卡片窗口（S）

### 3.1 点击列表标题崩溃（阻断级回归）
- **文件**：`app/ui/rich_editor.py` —— `RichEditor.__init__` 开头 `self.editor = None`；`eventFilter` 两处 `obj is self.editor` / `obj is self.editor.viewport()` 比较前加 `self.editor is not None` 守卫。
- **根因**：紧凑（便签）模式下 `add_cmd`/`build_color_buttons` 先把 `RichEditor` 自身作为事件过滤器装到工具栏按钮（约 L551/580/585），而 `self.editor`(QTextEdit) 要到约 L675 才赋值。点击列表标题新建便签 → 构造期若事件同步投递到这些按钮 → `eventFilter` 访问尚不存在的 `self.editor` → `AttributeError` 崩溃。
- **修复**：属性恒存在 + 比较安全；构造期竞态不再引发崩溃。

### 3.2 便签拖拽吃力
- **文件**：`app/ui/todo_window.py` —— `StickyNoteWindow` 新增 `self._drag` 状态；`eventFilter` 的 `MouseButtonPress` 分支判定可拖区域并 `_begin_drag`（含 `grabMouse`）；新增 `mouseMoveEvent` / `mouseReleaseEvent` 按全局坐标差 `move()` 并 `releaseMouse()`；`_locked`（置顶=锁定）时禁拖。
- **原始**：拖拽手柄只有顶部 24px 细条（右侧被 3 个 24px 按钮占去大半），抓卡片主体拖不动；用 `windowHandle().startSystemMove()`。
- **最终方案**：拖拽区扩展到**整张卡片空白**（顶部栏空白 + `note` 背景；按钮/标题/正文仍不拦截，避免抢文本编辑）；改用「按下 `grabMouse` + 全局鼠标追踪」的手动拖拽，比 `startSystemMove()` 在 Frameless+置顶+代理旋转控件下更可靠、整张卡片任意空白都能抓。

### 3.3 便签右键菜单「便签背景」英文两行 + 字体一致
- **文件**：`app/ui/todo_window.py` —— `StickyContextMenu._build_extra`。
- **原始**：背景行是单行 `QHBoxLayout`（标签 + 5 个 18px 色块同排）。菜单定宽 `CARD_WIDTH=206`（卡片内宽≈198，背景行内容宽≈174），色块占 5×18+4×6=114px，标签只剩≈54px → 中文「便签背景」够、英文 "Sticky Background" 被截成 "Sticky Bac"。且标签用 `font-size:12px`，比其它项（13px）小一号。
- **最终方案**：背景行改 `QVBoxLayout` 两行——第 1 行标签独占整宽（完整显示），第 2 行 5 个色块左对齐。标签样式去掉 12px 覆盖、统一 `CTX_MENU_TEXT_QSS`（13px），与上方菜单项完全一致。菜单高度由 `show_at()` 的 `adjustSize()` 自动增长。
- **平台**：纯 Qt 布局，跨平台无碍。

### 3.3b 便签右键菜单点「复制任务 / 清空内容」崩溃（阻断级回归，2026-09-20 续）
- **现象**：点这两项必崩 `RuntimeError: wrapped C/C++ object of type StickyContextMenu has been deleted`，堆栈 `common.py` `_trigger` → `self.close()`，外层 lambda 在 `todo_window.py` `_build_extra`。
- **根因：回调被 `_trigger` 包了两层**。`EditContextMenu._row()` 内部已自动 `clicked -> self._trigger(cb)`；而 `_build_extra` 又写成 `self._row(tr(text), "", lambda c=cb: self._trigger(c))` → 一次点击走两遍 `_trigger`：第一遍 `self.close()`（本类带 `WA_DeleteOnClose`，C++ 对象立即销毁），第二遍再 `self.close()` 即访问已销毁对象 → 崩溃。编辑动作块只包一层、`_set_bg` 手写 close+QTimer 也只有一层，故不崩，与「只有这两项崩」吻合。
- **最终方案（两道）**：
  1. 根治 —— `todo_window.py` 改为 `self._row(tr(text), "", cb)`，回调直传，不再重复包装。
  2. 兜底 —— `EditContextMenu._trigger` 与 `context_menu.ActionPopupMenu._trigger` 改为 `try: self.close() except RuntimeError: pass` 后再 `QTimer.singleShot(0, cb)`；对象已销毁时跳过 close 但**动作照常执行**（cb 指向业务窗口方法，与菜单生命周期无关）→ 同类问题既不崩也不丢动作。
  3. 顺带 —— `StickyContextMenu._set_bg` 改走 `self._trigger(...)`，消除手写 close+QTimer 的重复。
- **平台**：纯 Python/Qt 语义，**macOS 同因同解**。⚠️ macOS 上 popup 关闭时机与 Win 略有差异，这层 `try/except` 防护在 Mac 上同样必要（且更可能被 Qt 先行关闭 popup）。
- **通用红线**：`WA_DeleteOnClose` + 「回调链里再次触发自身关闭」= 悬空 wrapper 崩溃。菜单/弹窗类的关闭动作必须只包一层，且容忍对象已销毁。

### 3.4 便签右键菜单架构（本轮前已完成，列此备查）
- 菜单改为「原生编辑块 + 自定义块」（`STICKY_EDIT_ITEMS` / `STICKY_EDIT_SHORTCUTS`）；`_do_edit(act)` 按 `target` 类型作用于 `QTextEdit`/`QLineEdit`（删除：QTextEdit 走 `textCursor().removeSelectedText()`，QLineEdit 走 `del_()`）；顶层 `Qt.Popup` 由 Qt 负责「点外部/Esc 关闭」；i18n 词条含 Undo/Redo/Cut/Copy/Paste/Copy Task/Clear Content/Sticky Background 等。
- **关键根因（勿再误诊）**：`QTextEdit` 右键 `ContextMenu` 事件投递给它的 **`viewport()` 而非 QTextEdit 本身**，过滤器必须装在 viewport 上（见 `StickyNoteWindow._build_note` 的 `self.editor.editor.viewport().installEventFilter(self)`）。

---

## 4. 跨平台（macOS）迁移重点 ⚠️

下列是**非 Qt 原生 / 平台专属**或**需要替换资源**的点，macOS 端口必须处理（其余 Qt 代码可直接沿用）：

1. **字体（最关键）**
   - 多处硬编码 `C:\Windows\Fonts\msyh.ttc`（微软雅黑），包括运行时 `QFontDatabase.addApplicationFont(...)` 与所有 offscreen 测试脚本的字体注册。
   - macOS 无此文件：改用系统中文无衬线（PingFang SC / `.AppleSystemUIFont`）或随包分发字体；所有 `addApplicationFont(r"...msyh.ttc")` 调用及测试注册需替换。
   - 注意：offscreen 默认 fallback 字体极宽（"Sticky Background" 需 204px），真实字体仅需 ~108px——度量类断言**必须先注册真实字体**否则误判「放不下」。

2. **置顶 / 弹窗层级（Windows 专属 API）**
   - `_keep_topmost` 定时器、`promote_popup_topmost`、`SetWindowPos(TOPMOST)` 等为 Windows 专属；macOS 需换 `NSWindow` level（`NSFloatingWindowLevel`），或尽量依赖 Qt 跨平台的 `WindowStaysOnTopHint`（已使用，但「把下拉/日历弹窗顶到最上」的实现需重写）。
   - 弹窗打开期间应停止抢置顶（`popup_open()` 检测 `activePopupWidget()/activeModalWidget()`）。

3. **`startSystemMove()`**
   - Qt 跨平台（macOS 11+ 支持）；但便签拖拽本轮已改为 `grabMouse` 手动拖拽（纯 Qt、跨平台更友好），建议 macOS 直接沿用此实现，无需 `startSystemMove()`。

4. **无边框 + 半透明窗口**
   - `FramelessWindowHint` + `WA_TranslucentBackground`：macOS 上需额外处理窗口阴影/圆角（Qt 对 layered/translucent 行为不同）；`QGraphicsDropShadowEffect` 可用但性能/外观需验证。
   - 便签已**移除代理控件上的 `QGraphicsDropShadowEffect`**（每次重绘都把整卡渲染成 pixmap 再做高斯模糊，代价极高），改用窗口级轻量阴影或自绘。

5. **跨平台可直接沿用**：`QGraphicsView`/`QGraphicsProxyWidget`/`QGraphicsRotation`（卡片旋转）、`ResizeGrip`（缩放）、`grabMouse`/`QPropertyAnimation`/`QPainter`/`ElideLabel`/`TagLabel`、`QColorDialog(DontUseNativeDialog)`（自绘取色弹窗）、`EditContextMenu` 顶层 Popup 架构。

---

## 5. 验证状态

- 新增/复用 offscreen 回归脚本（均在 managed python 3.13.12 venv 跑）：
  - `atpp_verify_fixes.py`：崩溃修复 + "All" —— **8/8 PASS**。
  - `atpp_verify_elide.py`：标题省略号 + 动态长度 + 不遮挡 —— **16/16 PASS**。
  - `atpp_verify_menu_hover.py`：菜单两行 + hover 显示全 —— **11/11 PASS**。
  - `atpp_validate.py`：综合断言（100+ 条）。⚠️ 本沙箱构造 `StickyNoteWindow` 必现 C 级崩溃（exit 127，环境特有，非代码回归），故该脚本在沙箱跑不全；**需在真实机器 `python main.py` 跑**。
- ⚠️ 所有**视觉/交互**（拖拽手感、hover 滑动、菜单弹出位置、卜卜 PeekCard 渲染、字体渲染、卡顿根治程度）仍需用户在源码模式 `python main.py` 实机确认；offscreen 仅验证结构与几何。

---

## 6. 提交 / 打包 待办（用户尚未执行）
- 验收通过后：`git` 提交本时段全部改动；按既有三段打包链路重出安装包（PyInstaller → ISCC → bootstrap），并回归历史修复（UIPI 降权、播放器 i18n、卸载脚本 CRLF）。
