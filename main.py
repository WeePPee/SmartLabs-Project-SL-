import sys
import os
import json
import shutil
import base64
import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton,
                             QHBoxLayout, QFileDialog, QMessageBox, QStackedWidget, QLabel,
                             QListWidget, QListWidgetItem, QLineEdit, QCheckBox, QMenu, QInputDialog,
                             QAbstractItemView, QDialog, QSlider, QColorDialog, QFormLayout, QTextEdit,
                             QRadioButton, QFrame, QScrollArea)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings, QWebEngineProfile
from PyQt6.QtCore import Qt, QSize, QTimer, QUrl, QSettings
from PyQt6.QtGui import QFont, QPixmap, QColor

# ══════════════════════════════════════════════════════════════════
#  РЕДАКТОР ФОРМУЛ С LIVE PREVIEW
# ══════════════════════════════════════════════════════════════════
class FormulaEditorDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Редактор формул LaTeX")
        self.setMinimumSize(500, 450)
        self.result_latex = ""

        layout = QVBoxLayout(self)
        info = QLabel("Введите код LaTeX. Формула автоматически появится в предпросмотре.")
        info.setStyleSheet("color: #666; font-size: 13px; margin-bottom: 5px;")
        layout.addWidget(info)

        type_layout = QHBoxLayout()
        self.rb_inline = QRadioButton("В тексте \\( ... \\)")
        self.rb_block = QRadioButton("Блоком $$ ... $$")
        self.rb_block.setChecked(True)
        self.rb_inline.toggled.connect(self.update_preview)
        self.rb_block.toggled.connect(self.update_preview)
        type_layout.addWidget(self.rb_inline)
        type_layout.addWidget(self.rb_block)
        type_layout.addStretch()
        layout.addLayout(type_layout)

        layout.addWidget(QLabel("Код LaTeX:"))
        self.editor = QTextEdit()
        self.editor.setPlaceholderText("Например: \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}")
        self.editor.setFont(QFont("Courier New", 14))
        self.editor.setFixedHeight(100)
        self.editor.textChanged.connect(self.update_preview)
        layout.addWidget(self.editor)

        layout.addWidget(QLabel("Предпросмотр:"))
        self.preview = QWebEngineView()
        self.preview.setFixedHeight(120)
        
        preview_html = """
        <!DOCTYPE html><html><head>
        <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
        <script>
        window.MathJax = { tex: { inlineMath: [['\\\\(', '\\\\)']], displayMath: [['$$', '$$']] } };
        function renderTex(tex) {
            document.getElementById('out').innerHTML = tex;
            if (window.MathJax && MathJax.typesetClear) {
                MathJax.typesetClear();
                MathJax.typesetPromise();
            }
        }
        </script>
        <style>
            body { margin: 0; padding: 10px; font-family: sans-serif; background: #fafafa; color: #333; 
                   display: flex; justify-content: center; align-items: center; height: 100vh; box-sizing: border-box; overflow: hidden; border: 1px solid #ddd; border-radius: 6px;}
            #out { font-size: 110%; }
        </style>
        </head><body><div id="out"><i style="color:#aaa;">Здесь появится формула...</i></div></body></html>
        """
        self.preview.setHtml(preview_html)
        layout.addWidget(self.preview)

        buttons = QHBoxLayout()
        btn_cancel = QPushButton("Отмена")
        btn_cancel.clicked.connect(self.reject)
        btn_ok = QPushButton("Вставить")
        btn_ok.setStyleSheet("background-color: #005fb8; color: white; font-weight: bold; padding: 8px 15px;")
        btn_ok.clicked.connect(self.accept_formula)
        buttons.addStretch()
        buttons.addWidget(btn_cancel)
        buttons.addWidget(btn_ok)
        layout.addLayout(buttons)

    def update_preview(self):
        tex = self.editor.toPlainText().strip()
        if not tex:
            self.preview.page().runJavaScript("renderTex('<i style=\"color:#aaa;\">Здесь появится формула...</i>');")
            return
        preview_tex = f"$$ {tex} $$" if self.rb_block.isChecked() else f"\\( {tex} \\)"
        if tex.startswith("\\(") or tex.startswith("$$"): 
            preview_tex = tex
        safe_tex = preview_tex.replace('\\', '\\\\').replace('"', '\\"').replace("'", "\\'")
        self.preview.page().runJavaScript(f"renderTex('{safe_tex}');")

    def accept_formula(self):
        raw = self.editor.toPlainText().strip()
        if raw:
            self.result_latex = raw if (raw.startswith("\\(") or raw.startswith("$$")) else (f"$$ {raw} $$" if self.rb_block.isChecked() else f"\\( {raw} \\)")
            self.accept()
        else:
            QMessageBox.warning(self, "Пусто", "Введите код формулы!")

# ══════════════════════════════════════════════════════════════════
#  ИСПРАВЛЕННЫЙ WIRE SETTINGS DIALOG (БЕЗ ЗАКРЫТИЯ)
# ══════════════════════════════════════════════════════════════════
class WireSettingsDialog(QDialog):
    def __init__(self, current_width, current_opacity, current_color, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки провода")
        self.setMinimumWidth(350)
        self.container = QWidget(self)
        self.container.setStyleSheet("""
            QWidget { background-color: #ffffff; color: #333; font-family: Arial; font-size: 14px; border: 1px solid #ccc; border-radius: 8px; }
            QPushButton { border: none; font-weight: bold; }
        """)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.container)
        form = QFormLayout(self.container)
        form.setContentsMargins(20, 20, 20, 20)
        form.setSpacing(15)
        
        self.width_slider = QSlider(Qt.Orientation.Horizontal)
        self.width_slider.setRange(1, 20)
        self.width_slider.setValue(int(current_width))
        self.width_slider.setStyleSheet("border: none;")
        self.width_val = QLabel(f"{int(current_width)} px")
        self.width_val.setStyleSheet("border: none; font-weight: bold;")
        self.width_slider.valueChanged.connect(lambda v: self.width_val.setText(f"{v} px"))
        w_l = QHBoxLayout()
        w_l.addWidget(self.width_slider)
        w_l.addWidget(self.width_val)
        form.addRow("Ширина:", w_l)

        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(10, 100)
        self.opacity_slider.setValue(int(float(current_opacity) * 100))
        self.opacity_slider.setStyleSheet("border: none;")
        self.opacity_val = QLabel(f"{int(float(current_opacity) * 100)} %")
        self.opacity_val.setStyleSheet("border: none; font-weight: bold;")
        self.opacity_slider.valueChanged.connect(lambda v: self.opacity_val.setText(f"{v} %"))
        o_l = QHBoxLayout()
        o_l.addWidget(self.opacity_slider)
        o_layout = o_l
        o_layout.addWidget(self.opacity_val)
        form.addRow("Непрозрачность:", o_layout)

        self.color_btn = QPushButton(" Выбрать цвет ")
        self.selected_color = current_color
        self.color_btn.setStyleSheet(f"background-color: {current_color}; color: white; border-radius: 6px; padding: 8px; border: 1px solid #aaa;")
        self.color_btn.clicked.connect(self.choose_color)
        form.addRow("Цвет:", self.color_btn)

        btn_layout = QHBoxLayout()
        self.btn_delete = QPushButton("Удалить 🗑️")
        self.btn_delete.setStyleSheet("background-color: #ff4c4c; color: white; border-radius: 6px; padding: 10px;")
        self.btn_delete.clicked.connect(self.accept_delete)
        self.btn_save = QPushButton("Сохранить")
        self.btn_save.setStyleSheet("background-color: #005fb8; color: white; border-radius: 6px; padding: 10px;")
        self.btn_save.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_delete)
        btn_layout.addSpacing(20)
        btn_layout.addWidget(self.btn_save)
        form.addRow("", btn_layout)
        self.action = "save"

    def choose_color(self):
        c = QColorDialog.getColor(QColor(self.selected_color), self, "Выберите цвет провода")
        if c.isValid(): 
            self.selected_color = c.name()
            self.color_btn.setStyleSheet(f"background-color: {self.selected_color}; color: white; border-radius: 6px; padding: 8px; border: 1px solid #aaa;")

    def accept_delete(self):
        self.action = "delete"
        self.accept()

# ══════════════════════════════════════════════════════════════════
#  КОМПОНЕНТЫ И ГЛАВНЫЙ КЛАСС
# ══════════════════════════════════════════════════════════════════
class ComponentItemWidget(QWidget):
    def __init__(self, path, name, list_item, app_window):
        super().__init__()
        self.path = path
        self.name = name
        self.list_item = list_item
        self.app_window = app_window

        self.setFixedSize(100, 110)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 15, 5, 5)
        layout.setSpacing(5)

        self.icon_label = QLabel()
        pixmap = QPixmap(path).scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.icon_label.setPixmap(pixmap)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self.name_label = QLabel(name)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setWordWrap(True)
        self.name_label.setStyleSheet("font-size: 12px; background: transparent;")
        self.name_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        layout.addWidget(self.icon_label)
        layout.addWidget(self.name_label)

        self.btn_delete = QPushButton("✖", self)
        self.btn_delete.setFixedSize(20, 20)
        self.btn_delete.move(80, 5)
        self.btn_delete.setStyleSheet("background-color: #ff4c4c; color: white; border-radius: 10px; font-size: 10px; font-weight: bold; border: none;")
        self.btn_delete.clicked.connect(self.delete_req)
        self.btn_delete.hide()

    def enterEvent(self, event):
        self.btn_delete.show()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.btn_delete.hide()
        super().leaveEvent(event)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        rename_action = menu.addAction("✏️ Переименовать")
        action = menu.exec(self.mapToGlobal(event.pos()))
        if action == rename_action:
            self.app_window.rename_custom_component(self)

    def delete_req(self):
        self.app_window.delete_custom_component(self, self.list_item)

class DraggableComponentList(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)

    def mimeData(self, items):
        mime_data = super().mimeData(items)
        if not items: return mime_data
        path = items[0].data(Qt.ItemDataRole.UserRole)
        if path and os.path.exists(path):
            mime_data.setUrls([QUrl.fromLocalFile(path)])
            try:
                with open(path, "rb") as f:
                    b64_data = base64.b64encode(f.read()).decode('utf-8')
                ext = os.path.splitext(path)[1][1:].lower()
                if ext == "jpg": ext = "jpeg"
                html = f'<img src="data:image/{ext};base64,{b64_data}" alt="component" />'
                mime_data.setHtml(html)
            except Exception as e:
                pass
        return mime_data

class ToastWidget(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("background-color: rgba(30, 30, 30, 0.9); color: #ffffff; padding: 15px 25px; border-radius: 8px; font-size: 15px; font-weight: bold; border: 1px solid #555;")
        self.hide()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.hide)

    def show_message(self, text, duration=3500):
        self.setText(text)
        self.adjustSize()
        if self.parent():
            x = (self.parent().width() - self.width()) // 2
            y = self.parent().height() - self.height() - 80
            self.move(x, y)
        self.show()
        self.raise_()
        self.timer.start(duration)

    def mousePressEvent(self, event):
        self.hide()

class CustomWebPage(QWebEnginePage):
    def __init__(self, app_instance, parent=None):
        super().__init__(parent)
        self.app = app_instance

    def javaScriptConsoleMessage(self, level, msg, line, source):
        if msg.startswith("SMARTLAB_ACTION:"):
            parts = msg.split(":")
            action = parts[1]
            args = parts[2:]
            QTimer.singleShot(0, lambda: self.app.handle_js_action(action, args))
        else:
            super().javaScriptConsoleMessage(level, msg, line, source)

class SmartLabApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SmartLab Assistant")
        self.resize(1400, 900)
        self.showMaximized()
        self.dark_mode = False
        self.protect_step = True
        self.protect_slide = True
        self.wire_mode_active = False

        font = QFont("Arial", 10)
        self.setFont(font)
        self.toast = ToastWidget(self)
        self.settings = QSettings("SmartLab", "SmartLabApp")

        if hasattr(sys, '_MEIPASS'):
            current_dir = sys._MEIPASS
        else:
            current_dir = os.path.dirname(os.path.abspath(__file__))

        self.assets_dir = os.path.join(current_dir, "assets")
        self.comp_dir = os.path.join(self.assets_dir, "components")
        self.html_path = os.path.join(self.assets_dir, "editor.html")
        os.makedirs(self.comp_dir, exist_ok=True)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- НАВИГАЦИЯ ---
        self.nav_panel = QWidget()
        self.nav_panel.setObjectName("NavPanel")
        nav_layout = QHBoxLayout(self.nav_panel)
        nav_layout.setContentsMargins(10, 8, 10, 0)
        nav_layout.setSpacing(5)

        self.tabs = [QPushButton(n) for n in ["Файл", "Главная", "Компоненты", "Консоль (AI)", "Настройки", "Справочник"]]
        self.tabs[0].setObjectName("FileBtn")
        for idx, btn in enumerate(self.tabs):
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, i=idx: self.switch_tab(i))
            nav_layout.addWidget(btn)

        nav_layout.addStretch()
        main_layout.addWidget(self.nav_panel)

        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setObjectName("Stack")
        main_layout.addWidget(self.stacked_widget)

        # --- [0] ФАЙЛ ---
        self.page_file = QWidget()
        self.page_file.setObjectName("BgPage")
        file_layout = QHBoxLayout(self.page_file)
        file_layout.setContentsMargins(0, 0, 0, 0)

        file_sidebar = QWidget()
        file_sidebar.setFixedWidth(280)
        file_sidebar.setObjectName("Sidebar")
        sidebar_layout = QVBoxLayout(file_sidebar)
        sidebar_layout.setContentsMargins(0, 20, 0, 0)
        sidebar_layout.setSpacing(5)

        btn_back = QPushButton("←   Назад")
        btn_back.setObjectName("SideBtn")
        btn_back.clicked.connect(lambda: self.switch_tab(1))
        sidebar_layout.addWidget(btn_back)
        sidebar_layout.addSpacing(30)

        for text, func in [("📄   Создать новую", None), ("📂   Открыть...", self.open_lab), ("💾   Сохранить", self.save_lab)]:
            btn = QPushButton(text)
            btn.setObjectName("SideBtn")
            if func: btn.clicked.connect(func)
            sidebar_layout.addWidget(btn)
        sidebar_layout.addStretch()

        file_content = QWidget()
        file_content.setObjectName("BgPage")
        content_layout = QVBoxLayout(file_content)
        content_layout.setContentsMargins(60, 50, 60, 50)

        lbl_greeting = QLabel("Добрый вечер")
        lbl_greeting.setFont(QFont("Arial", 32, QFont.Weight.Medium))
        lbl_recent = QLabel("Последние документы")
        lbl_recent.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        lbl_recent.setStyleSheet("margin-top: 40px; margin-bottom: 10px; color: #666;")

        self.recent_list = QListWidget()
        for doc in ["Лабораторная_по_физике.slabs", "Основы_схемотехники.slabs"]:
            self.recent_list.addItem(doc)

        content_layout.addWidget(lbl_greeting)
        content_layout.addWidget(lbl_recent)
        content_layout.addWidget(self.recent_list)
        content_layout.addStretch()

        file_layout.addWidget(file_sidebar)
        file_layout.addWidget(file_content)
        self.stacked_widget.addWidget(self.page_file)

        # --- [1] ЕДИНОЕ ПРОСТРАНСТВО (РЕДАКТОР) ---
        self.page_editor_workspace = QWidget()
        workspace_layout = QVBoxLayout(self.page_editor_workspace)
        workspace_layout.setContentsMargins(0, 0, 0, 0)
        workspace_layout.setSpacing(0)

        self.components_ribbon = QWidget()
        self.components_ribbon.setObjectName("ComponentsRibbon")
        self.components_ribbon.setFixedHeight(135)
        self.components_ribbon.hide()

        ribbon_layout = QHBoxLayout(self.components_ribbon)
        ribbon_layout.setContentsMargins(20, 15, 20, 15)
        ribbon_layout.setSpacing(25)

        left_tools = QWidget()
        left_tools.setFixedWidth(160)
        lt_layout = QVBoxLayout(left_tools)
        lt_layout.setContentsMargins(0, 0, 0, 0)
        lt_layout.setSpacing(8)

        self.btn_wire = QPushButton("〰️  Провод (Выкл)")
        self.btn_wire.setObjectName("ToolBtn")
        self.btn_wire.clicked.connect(self.toggle_wire_mode)
        lt_layout.addWidget(self.btn_wire)
        lt_layout.addStretch()

        self.comp_grid = DraggableComponentList()
        self.comp_grid.setObjectName("CompGrid")
        self.comp_grid.setViewMode(QListWidget.ViewMode.IconMode)
        self.comp_grid.setFlow(QListWidget.Flow.TopToBottom)
        self.comp_grid.setWrapping(True)
        self.comp_grid.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.comp_grid.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.comp_grid.setIconSize(QSize(48, 48))
        self.comp_grid.setSpacing(8)

        right_tools = QWidget()
        right_tools.setFixedWidth(150)
        rt_layout = QVBoxLayout(right_tools)
        rt_layout.setContentsMargins(0, 0, 0, 0)
        rt_layout.setSpacing(10)

        self.search_comp = QLineEdit()
        self.search_comp.setObjectName("SearchInput")
        self.search_comp.setPlaceholderText("🔍 Поиск...")
        self.search_comp.setFixedHeight(40)

        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(5)

        self.btn_add_comp = QPushButton("➕ Добав.")
        self.btn_add_comp.setObjectName("ActionBtn")
        self.btn_add_comp.setFixedHeight(40)
        self.btn_add_comp.clicked.connect(self.add_custom_component_dialog)

        self.btn_paste_comp = QPushButton("📋🔽")
        self.btn_paste_comp.setObjectName("ActionBtn")
        self.btn_paste_comp.setFixedSize(45, 40)
        self.btn_paste_comp.setToolTip("Сохранить картинку из буфера обмена")
        self.btn_paste_comp.clicked.connect(self.add_from_clipboard)

        btn_layout.addWidget(self.btn_add_comp)
        btn_layout.addWidget(self.btn_paste_comp)

        rt_layout.addWidget(self.search_comp)
        rt_layout.addLayout(btn_layout)
        rt_layout.addStretch()

        ribbon_layout.addWidget(left_tools)
        ribbon_layout.addWidget(self.comp_grid)
        ribbon_layout.addWidget(right_tools)

        self.browser = QWebEngineView()
        self.custom_page = CustomWebPage(self, self.browser)
        self.browser.setPage(self.custom_page)
        
        QWebEngineProfile.defaultProfile().clearHttpCache()
        settings = self.browser.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        
        if os.path.exists(self.html_path):
            with open(self.html_path, "r", encoding="utf-8") as f:
                html_content = f.read()
            self.browser.setHtml(html_content, QUrl.fromLocalFile(self.assets_dir + os.sep))
        else:
            QMessageBox.critical(self, "Ошибка", f"Файл не найден: {self.html_path}\nУбедитесь, что editor.html лежит в папке assets!")

        workspace_layout.addWidget(self.components_ribbon)
        workspace_layout.addWidget(self.browser)
        self.stacked_widget.addWidget(self.page_editor_workspace)

        # ══════════════════════════════════════════════════════════════════
        #  [2] КОНСОЛЬ AI
        # ══════════════════════════════════════════════════════════════════
        self.page_console = QWidget()
        self.page_console.setObjectName("BgPage")
        console_layout = QVBoxLayout(self.page_console)
        console_layout.setContentsMargins(60, 40, 60, 40)
        console_layout.setSpacing(15)

        lbl_console = QLabel("AI Консоль (Генератор структуры)")
        lbl_console.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        console_layout.addWidget(lbl_console)
        
        desc = QLabel("Скопируйте JSON-код, сгенерированный нейросетью, и вставьте его в поле ниже. Программа автоматически соберет все шаги и форматирование.")
        desc.setStyleSheet("color: #666; font-size: 14px;")
        desc.setWordWrap(True)
        console_layout.addWidget(desc)

        self.console_input = QTextEdit()
        self.console_input.setPlaceholderText('{\n  "title": "Название лабы",\n  "goal": "Цель работы...",\n  "steps": [\n    {"title": "Шаг 1", "desc": "Соберите схему..."}\n  ]\n}')
        self.console_input.setFont(QFont("Courier New", 11))
        self.console_input.setStyleSheet("border: 1px solid #ccc; border-radius: 8px; padding: 10px; background-color: #fff;")
        console_layout.addWidget(self.console_input)

        c_btn_layout = QHBoxLayout()
        self.btn_gen_overwrite = QPushButton("⚠️ Перезаписать документ полностью")
        self.btn_gen_overwrite.setObjectName("ActionBtn")
        self.btn_gen_overwrite.setStyleSheet("background-color: #d32f2f;")
        self.btn_gen_overwrite.setFixedHeight(45)
        self.btn_gen_overwrite.clicked.connect(lambda: self.process_ai_json('overwrite'))
        
        self.btn_gen_insert = QPushButton("📥 Вставить с текущего места")
        self.btn_gen_insert.setObjectName("ActionBtn")
        self.btn_gen_insert.setFixedHeight(45)
        self.btn_gen_insert.clicked.connect(lambda: self.process_ai_json('insert'))
        
        c_btn_layout.addWidget(self.btn_gen_overwrite)
        c_btn_layout.addWidget(self.btn_gen_insert)
        console_layout.addLayout(c_btn_layout)

        self.stacked_widget.addWidget(self.page_console)

        # --- [3] НАСТРОЙКИ ---
        self.page_settings = QWidget()
        self.page_settings.setObjectName("BgPage")
        layout_settings = QVBoxLayout(self.page_settings)
        layout_settings.setContentsMargins(60, 50, 60, 50)
        layout_settings.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        lbl_theme = QLabel("Тема оформления:")
        lbl_theme.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        self.btn_theme = QPushButton("🌙 Переключить на темную тему")
        self.btn_theme.setObjectName("ActionBtn")
        self.btn_theme.setFixedSize(300, 45)
        self.btn_theme.clicked.connect(self.toggle_theme)

        layout_settings.addWidget(lbl_theme)
        layout_settings.addSpacing(15)
        layout_settings.addWidget(self.btn_theme)
        layout_settings.addSpacing(50)

        lbl_editor = QLabel("Безопасность редактора:")
        lbl_editor.setFont(QFont("Arial", 18, QFont.Weight.Bold))

        self.cb_protect_step = QCheckBox("Защита от случайного удаления полностью всего шага")
        self.cb_protect_step.setChecked(True)
        self.cb_protect_step.setObjectName("SettingsCheckbox")
        self.cb_protect_step.stateChanged.connect(self.update_protections)

        self.cb_protect_slide = QCheckBox("Защита от случайного удаления текущего действия")
        self.cb_protect_slide.setChecked(True)
        self.cb_protect_slide.setObjectName("SettingsCheckbox")
        self.cb_protect_slide.stateChanged.connect(self.update_protections)

        layout_settings.addWidget(lbl_editor)
        layout_settings.addSpacing(15)
        layout_settings.addWidget(self.cb_protect_step)
        layout_settings.addSpacing(10)
        layout_settings.addWidget(self.cb_protect_slide)

        self.stacked_widget.addWidget(self.page_settings)

        # ══════════════════════════════════════════════════════════════════
        #  [4] ИНТЕРАКТИВНЫЙ СПРАВОЧНИК
        # ══════════════════════════════════════════════════════════════════
        self.page_guide = QWidget()
        self.page_guide.setObjectName("BgPage")
        gl_layout = QHBoxLayout(self.page_guide)
        gl_layout.setContentsMargins(0, 0, 0, 0)
        
        self.guide_menu = QListWidget()
        self.guide_menu.setFixedWidth(280)
        self.guide_menu.setObjectName("Sidebar")
        self.guide_menu.addItems([
            "🏠 Быстрый старт (Оглавление)",
            "🤖 AI Консоль: Как писать промпт",
            "📐 Формулы и LaTeX",
            "🎨 Схемотехника и провода",
            "📦 Работа с каруселью шагов"
        ])
        
        self.guide_pages = QStackedWidget()
        gl_layout.addWidget(self.guide_menu)
        gl_layout.addWidget(self.guide_pages)
        
        guide_data = [
            ("Оглавление", "<h1>Справочник SmartLab Assistant</h1><p>Выберите раздел слева, чтобы узнать больше о функциях программы.</p><h3>Краткое содержание:</h3><ul><li><b>AI Консоль:</b> Как превратить методичку в готовую структуру за секунды.</li><li><b>Формулы:</b> Использование LaTeX для профессиональных расчетов.</li><li><b>Схемы:</b> Инструкция по рисованию связей и добавлению компонентов.</li><li><b>Шаги:</b> Как управлять блоками действий и менять их местами.</li></ul>"),
            ("AI Консоль", "<h2>🤖 Работа с AI Консолью</h2><p>Для автоматической сборки лабы скопируйте и отправьте этот промпт нейросети вместе с текстом вашей методички:</p><div style='background:#f4f4f4; padding:15px; border-radius:8px; font-family:monospace; border-left: 5px solid #005fb8;'><b>ПРОМПТ:</b><br><br>Проанализируй текст этой лабораторной работы и сформируй структуру для программы в формате JSON.<br>Ответ должен содержать ТОЛЬКО JSON-код, без лишних слов.<br><br>Структура JSON должна быть такой:<br>{<br>  \"title\": \"Название работы\",<br>  \"goal\": \"Цель работы...\",<br>  \"steps\": [<br>    { \"title\": \"Шаг 1\", \"desc\": \"Описание действия...\" },<br>    { \"title\": \"Шаг 2\", \"desc\": \"Описание действия...\" }<br>  ]<br>}</div><p>Затем вставьте полученный код в Консоль и нажмите 'Перезаписать' или 'Вставить'.</p>"),
            ("Формулы", "<h2>📐 Математика и LaTeX</h2><p>Программа поддерживает автоматический рендеринг LaTeX через MathJax.</p><ul><li><b>Встроенные:</b> \\( E=mc^2 \\) (для текста в строке).</li><li><b>Блочные:</b> $$ P=U \\cdot I $$ (для выделенных формул по центру).</li></ul><p>Используйте кнопку <b>f(x)</b> в редакторе для быстрого ввода с предпросмотром.</p>"),
            ("Схемы", "<h2>🎨 Рисование схем</h2><p>1. Перетащите компоненты из ленты сверху прямо на лист.<br>2. Включите режим <b>〰️ Провод</b>.<br>3. Зажмите левую кнопку мыши, чтобы начать линию, и отпустите на узле завершения.<br>4. Нажмите <b>правой кнопкой на провод</b>, чтобы изменить его цвет или удалить.</p>"),
            ("Карусель", "<h2>📦 Управление шагами</h2><p>Каждое 'Действие' — это независимый слайд карусели.</p><ul><li><b>Добавление:</b> Кнопка '+' на нижней панели.</li><li><b>Удаление:</b> Кнопка 'X' над номером слайда удаляет текущее действие, кнопка 'Удалить полностью' удаляет всю карусель.</li><li><b>Порядок:</b> Просто перетащите номер слайда мышкой на новое место.</li></ul>")
        ]
        
        for title, html in guide_data:
            page = QWidget()
            p_lay = QVBoxLayout(page)
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.Shape.NoFrame)
            lbl = QLabel(html)
            lbl.setWordWrap(True)
            lbl.setAlignment(Qt.AlignmentFlag.AlignTop)
            lbl.setOpenExternalLinks(True)
            lbl.setContentsMargins(30, 20, 30, 20)
            scroll.setWidget(lbl)
            p_lay.addWidget(scroll)
            self.guide_pages.addWidget(page)
            
        self.guide_menu.currentRowChanged.connect(self.guide_pages.setCurrentIndex)
        self.stacked_widget.addWidget(self.page_guide)

        self.switch_tab(1)
        self.apply_theme()
        self.load_saved_components()

    def process_ai_json(self, mode):
        text = self.console_input.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Пусто", "Сначала вставьте JSON-код в консоль.")
            return

        try:
            data = json.loads(text)
            safe_json = json.dumps(data)
            
            if mode == 'overwrite':
                reply = QMessageBox.question(self, "Перезапись", "Текущий документ будет полностью стерт. Продолжить?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.No:
                    return

            self.browser.page().runJavaScript(f"if(window.buildLabFromJSON) window.buildLabFromJSON({safe_json}, '{mode}');")
            self.toast.show_message("Структура успешно сгенерирована!")
            self.switch_tab(1)
            
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "Ошибка JSON", f"Нейросеть прислала некорректный JSON. Проверьте код на наличие лишних символов.\n\nДетали:\n{str(e)}")

    def toggle_wire_mode(self):
        self.wire_mode_active = not self.wire_mode_active
        if self.wire_mode_active:
            self.btn_wire.setText("〰️  Провод (Вкл)")
            self.btn_wire.setStyleSheet("background-color: #005fb8; color: white; border: none;")
            self.browser.page().runJavaScript("if (window.setTool) window.setTool('wire');")
        else:
            self.btn_wire.setText("〰️  Провод (Выкл)")
            self.btn_wire.setStyleSheet("") 
            self.browser.page().runJavaScript("if (window.setTool) window.setTool(null);")

    def handle_js_action(self, action, args):
        if action == "open_formula_editor":
            dialog = FormulaEditorDialog(self)
            if dialog.exec():
                safe_latex = dialog.result_latex.replace("\\", "\\\\")
                self.browser.page().runJavaScript(f"tinymce.activeEditor.insertContent('{safe_latex}');")

        elif action == "placeholder_click":
            if self.components_ribbon.isVisible():
                self.toast.show_message("⚠️ Зажмите элемент мышкой и перетащите его прямо сюда!")
            else:
                self.switch_tab(2)

        elif action == "edit_wire":
            wire_id = args[0]
            current_width = args[1]
            current_opacity = args[2]
            current_color = args[3]
            
            dialog = WireSettingsDialog(current_width, current_opacity, current_color, self)
            if dialog.exec():
                if dialog.action == "delete":
                    self.browser.page().runJavaScript(f"window.updateWire('{wire_id}', null, null, null, true);")
                    self.toast.show_message("Провод удален!")
                else:
                    new_w = dialog.width_slider.value()
                    new_o = dialog.opacity_slider.value() / 100.0
                    new_c = dialog.selected_color
                    self.browser.page().runJavaScript(f"window.updateWire('{wire_id}', '{new_w}', '{new_o}', '{new_c}', false);")
                    self.toast.show_message("Настройки сохранены!")

        elif action == "delete_step":
            carousel_id = args[0]
            if self.protect_step:
                if not self.show_confirm("Вы уверены, что хотите удалить полностью весь этот шаг со всеми действиями?", "step"): return
            self.browser.page().runJavaScript(f"if (window.deleteStep) window.deleteStep('{carousel_id}');")

        elif action == "delete_slide":
            carousel_id = args[0]
            active_idx = int(args[1])
            if self.protect_slide:
                if not self.show_confirm("Вы уверены, что хотите удалить текущее действие?", "slide"): return
            self.browser.page().runJavaScript(f"if (window.deleteSlide) window.deleteSlide('{carousel_id}', {active_idx});")

        elif action == "alert":
            msg = ":".join(args)
            self.toast.show_message(f"⚠️ {msg}")

    def show_confirm(self, msg, type_):
        box = QMessageBox(self)
        box.setWindowTitle("Подтверждение удаления")
        box.setText(msg)
        box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        box.setDefaultButton(QMessageBox.StandardButton.No)

        cb = QCheckBox("Запрашивать подтверждение по умолчанию?")
        cb.setChecked(True) 
        cb.setToolTip("Если убрать галочку, элементы будут удаляться без защиты.\nВключить обратно можно в 'Настройках'.")
        box.setCheckBox(cb)
        reply = box.exec()

        if not cb.isChecked():
            if type_ == "step": self.cb_protect_step.setChecked(False)
            elif type_ == "slide": self.cb_protect_slide.setChecked(False)

        return reply == QMessageBox.StandardButton.Yes

    def add_from_clipboard(self):
        clipboard = QApplication.clipboard()
        mime = clipboard.mimeData()

        if mime.hasImage():
            image = clipboard.image()
            if image.isNull():
                self.toast.show_message("⚠️ Ошибка чтения изображения из буфера!")
                return
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            new_name = f"Скрин_{timestamp}"
            dest_path = os.path.join(self.comp_dir, f"{new_name}.png")

            try:
                image.save(dest_path, "PNG")
                self._create_component_widget(dest_path)
                self.toast.show_message(f"Элемент «{new_name}» добавлен из буфера!")
            except Exception as e:
                self.toast.show_message(f"Ошибка сохранения: {e}")
        else:
            self.toast.show_message("⚠️ В буфере обмена нет картинки!")

    def load_saved_components(self):
        self.comp_grid.clear()
        for filename in os.listdir(self.comp_dir):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                path = os.path.join(self.comp_dir, filename)
                self._create_component_widget(path)

    def add_custom_component_dialog(self):
        file_paths, _ = QFileDialog.getOpenFileNames(self, "Выберите картинку", "", "Изображения (*.png *.jpg *.jpeg)")
        for path in file_paths:
            filename = os.path.basename(path)
            dest_path = os.path.join(self.comp_dir, filename)
            if path != dest_path: shutil.copy(path, dest_path)
            self._create_component_widget(dest_path)

    def _create_component_widget(self, path):
        clean_name = os.path.splitext(os.path.basename(path))[0]
        item = QListWidgetItem(self.comp_grid)
        item.setSizeHint(QSize(110, 120))
        item.setData(Qt.ItemDataRole.UserRole, path)
        widget = ComponentItemWidget(path, clean_name, item, self)
        self.comp_grid.setItemWidget(item, widget)

    def delete_custom_component(self, comp_widget, list_item):
        reply = QMessageBox.question(
            self, 'Подтверждение удаления', f'Вы уверены, что хотите удалить элемент "{comp_widget.name}" из базы?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                os.remove(comp_widget.path)
                row = self.comp_grid.row(list_item)
                self.comp_grid.takeItem(row)
                self.toast.show_message(f"Элемент «{comp_widget.name}» удален")
            except Exception as e:
                self.toast.show_message(f"Ошибка: {e}")

    def rename_custom_component(self, comp_widget):
        new_name, ok = QInputDialog.getText(self, 'Переименование', 'Введите новое название:', text=comp_widget.name)
        if ok and new_name.strip():
            new_name = new_name.strip()
            ext = os.path.splitext(comp_widget.path)[1]
            new_path = os.path.join(self.comp_dir, f"{new_name}{ext}")

            if os.path.exists(new_path) and new_path != comp_widget.path:
                QMessageBox.warning(self, "Ошибка", "Элемент с таким именем уже существует!")
                return
            try:
                os.rename(comp_widget.path, new_path)
                comp_widget.path = new_path
                comp_widget.name = new_name
                comp_widget.name_label.setText(new_name)
                comp_widget.list_item.setData(Qt.ItemDataRole.UserRole, new_path)
                self.toast.show_message(f"Успешно переименовано в «{new_name}»")
            except Exception as e:
                self.toast.show_message(f"Ошибка переименования: {e}")

    def switch_tab(self, index):
        if index == 3: # Вкладка консоли
            if not self.settings.value("console_visited", False, type=bool):
                QMessageBox.information(self, "Добро пожаловать в AI Консоль", 
                    "Это инструмент для автоматической генерации лабораторных работ через ИИ.\n\n"
                    "Пожалуйста, загляните во вкладку 'Справочник', чтобы узнать, как правильно составлять "
                    "запросы (промпты) для ChatGPT или Claude.\n\n"
                    "(Это сообщение показывается только один раз)")
                self.settings.setValue("console_visited", True)

        for i, btn in enumerate(self.tabs): btn.setChecked(i == index)
        self.nav_panel.setVisible(index != 0)
        
        if index == 1:
            self.stacked_widget.setCurrentWidget(self.page_editor_workspace)
            self.components_ribbon.hide()
            self.browser.page().runJavaScript("if(window.showEditorToolbar) window.showEditorToolbar(true);")
        elif index == 2:
            self.stacked_widget.setCurrentWidget(self.page_editor_workspace)
            self.components_ribbon.show()
            self.browser.page().runJavaScript("if(window.showEditorToolbar) window.showEditorToolbar(false);")
        elif index == 0: self.stacked_widget.setCurrentWidget(self.page_file)
        elif index == 3: self.stacked_widget.setCurrentWidget(self.page_console)
        elif index == 4: self.stacked_widget.setCurrentWidget(self.page_settings)
        elif index == 5: self.stacked_widget.setCurrentWidget(self.page_guide)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'toast') and self.toast.isVisible():
            x = (self.width() - self.toast.width()) // 2
            y = self.height() - self.toast.height() - 80
            self.toast.move(x, y)

    def update_protections(self):
        self.protect_step = self.cb_protect_step.isChecked()
        self.protect_slide = self.cb_protect_slide.isChecked()

    def save_lab(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить", "", "SmartLab (*.slabs *.html)")
        if file_path: self.browser.page().runJavaScript("tinymce.activeEditor.getContent();", lambda html: self._write_file(file_path, html))

    def _write_file(self, path, content):
        try:
            with open(path, "w", encoding="utf-8") as f: f.write(content)
            self.toast.show_message("Методичка успешно сохранена!")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def open_lab(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Открыть", "", "SmartLab (*.slabs *.html)")
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f: content = f.read()
                safe_content = json.dumps(content)
                self.browser.page().runJavaScript(f"if(window.setEditorContent) window.setEditorContent({safe_content});")
                self.switch_tab(1)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось открыть:\n{e}")

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.browser.page().runJavaScript(f"if(window.toggleDarkMode) window.toggleDarkMode({str(self.dark_mode).lower()});")
        self.apply_theme()

    def apply_theme(self):
        if self.dark_mode:
            self.btn_theme.setText("☀️ Переключить на светлую тему")
            self.setStyleSheet("""
                QMainWindow, QStackedWidget#Stack { background-color: #18181b; }
                QWidget#BgPage { background-color: #18181b; color: #e0e0e0; }
                QWidget#NavPanel { background-color: #1e1e1e; border-bottom: 1px solid #333; }
                QWidget#Sidebar { background-color: #141416; border-right: 1px solid #2d2d30; }
                QLabel { color: #e0e0e0; background: transparent; }
                QWidget#NavPanel QPushButton { min-width: 120px; border: none; padding: 10px 16px; font-size: 14px; background-color: transparent; border-radius: 8px 8px 0 0; color: #999;}
                QWidget#NavPanel QPushButton:hover { color: #fff; background-color: #252526; }
                QWidget#NavPanel QPushButton:checked { color: #4daafc; font-weight: bold; background-color: #18181b; border-bottom: 3px solid #4daafc;}
                QWidget#NavPanel QPushButton#FileBtn { min-width: 80px; background-color: #005fb8; color: white; margin: 2px 5px 0 10px; border-radius: 6px; border-bottom: none;}
                QWidget#NavPanel QPushButton#FileBtn:hover { background-color: #004c99; }
                QPushButton#SideBtn { text-align: left; padding: 14px 24px; font-size: 15px; color: #ccc; border-radius: 8px; margin: 0 15px;}
                QPushButton#SideBtn:hover { background-color: #2d2d30; color: #fff; }
                QPushButton#ActionBtn { background-color: #005fb8; color: white; font-weight: bold; border-radius: 6px; font-size: 14px; border: none;}
                QPushButton#ActionBtn:hover { background-color: #004c99; }
                QWidget#ComponentsRibbon { background-color: #1e1e1e; border-bottom: 1px solid #333; }
                QPushButton#ToolBtn { background-color: #252526; color: #ccc; padding: 8px 15px; border-radius: 6px; font-size: 14px; text-align: left; border: 1px solid #333;}
                QPushButton#ToolBtn:hover { background-color: #2d2d30; border-color: #4daafc; color: #fff;}
                QLineEdit#SearchInput { background-color: #252526; color: #fff; padding: 5px 15px; border-radius: 6px; border: 1px solid #333; font-size: 14px;}
                QLineEdit#SearchInput:focus { border-color: #4daafc; }
                QListWidget { background-color: transparent; color: #ccc; border: none; font-size: 13px;}
                QListWidget::item { padding: 0; border-radius: 8px; margin-bottom: 4px; }
                QListWidget::item:hover { background-color: #2d2d30;}
                QListWidget#CompGrid { background-color: transparent; }
                QListWidget#CompGrid::item { border: 1px solid #333; border-radius: 6px; background-color: #252526;}
                QListWidget#CompGrid::item:hover { border-color: #4daafc; background-color: #2d2d30;}
                QCheckBox#SettingsCheckbox { font-size: 15px; color: #e0e0e0; padding: 5px; }
                QCheckBox#SettingsCheckbox::indicator { width: 20px; height: 20px; border-radius: 4px; border: 1px solid #555; background-color: #252526; }
                QCheckBox#SettingsCheckbox::indicator:checked { background-color: #4daafc; border: 1px solid #4daafc; }
                QListWidget#CompGrid::horizontalScrollBar { background: #1e1e1e; height: 10px; }
                QListWidget#CompGrid::handle:horizontal { background: #444; border-radius: 5px; }
                QListWidget#CompGrid::handle:horizontal:hover { background: #555; }
            """)
        else:
            self.btn_theme.setText("🌙 Переключить на темную тему")
            self.setStyleSheet("""
                QMainWindow, QStackedWidget#Stack { background-color: #f0f2f5; }
                QWidget#BgPage { background-color: white; color: #1a1a1a; }
                QWidget#NavPanel { background-color: #ffffff; border-bottom: 1px solid #e1e4e8; }
                QWidget#Sidebar { background-color: #f8fafc; border-right: 1px solid #e1e4e8; }
                QLabel { color: #1a1a1a; background: transparent; }
                QWidget#NavPanel QPushButton { min-width: 120px; border: none; padding: 10px 16px; font-size: 14px; background-color: transparent; border-radius: 8px 8px 0 0; color: #5c6c7c;}
                QWidget#NavPanel QPushButton:hover { color: #1a1a1a; background-color: #f0f2f5; }
                QWidget#NavPanel QPushButton:checked { color: #005fb8; font-weight: bold; background-color: #f0f2f5; border-bottom: 3px solid #005fb8;}
                QWidget#NavPanel QPushButton#FileBtn { min-width: 80px; background-color: #005fb8; color: white; margin: 2px 5px 0 10px; border-radius: 6px; border-bottom: none;}
                QWidget#NavPanel QPushButton#FileBtn:hover { background-color: #004c99; }
                QPushButton#SideBtn { text-align: left; padding: 14px 24px; font-size: 15px; color: #444; border-radius: 8px; margin: 0 15px;}
                QPushButton#SideBtn:hover { background-color: #e1e4e8; color: #000; }
                QPushButton#ActionBtn { background-color: #005fb8; color: white; font-weight: bold; border-radius: 6px; font-size: 14px; border: none;}
                QPushButton#ActionBtn:hover { background-color: #004c99; }
                QWidget#ComponentsRibbon { background-color: #ffffff; border-bottom: 1px solid #e1e4e8; box-shadow: 0 4px 6px rgba(0,0,0,0.05);}
                QPushButton#ToolBtn { background-color: #ffffff; color: #333; padding: 8px 15px; border-radius: 6px; font-size: 14px; text-align: left; border: 1px solid #d0d7de;}
                QPushButton#ToolBtn:hover { background-color: #f0f2f5; border-color: #005fb8;}
                QLineEdit#SearchInput { background-color: #ffffff; color: #333; padding: 5px 15px; border-radius: 6px; border: 1px solid #d0d7de; font-size: 14px;}
                QLineEdit#SearchInput:focus { border-color: #005fb8; outline: none; }
                QListWidget { background-color: transparent; color: #333; border: none; font-size: 13px;}
                QListWidget::item { padding: 0; border-radius: 8px; margin-bottom: 4px; }
                QListWidget::item:hover { background-color: #f0f2f5; }
                QListWidget#CompGrid { background-color: transparent; }
                QListWidget#CompGrid::item { border: 1px solid #d0d7de; border-radius: 6px; background-color: #ffffff;}
                QListWidget#CompGrid::item:hover { border-color: #005fb8; background-color: #f8fafc;}
                QCheckBox#SettingsCheckbox { font-size: 15px; color: #333; padding: 5px; }
                QCheckBox#SettingsCheckbox::indicator { width: 20px; height: 20px; border-radius: 4px; border: 1px solid #ccc; background-color: #fff; }
                QCheckBox#SettingsCheckbox::indicator:checked { background-color: #005fb8; border: 1px solid #005fb8; }
                QListWidget#CompGrid::horizontalScrollBar { background: #f0f2f5; height: 10px; }
                QListWidget#CompGrid::handle:horizontal { background: #c1c1c1; border-radius: 5px; }
                QListWidget#CompGrid::handle:horizontal:hover { background: #a8a8a8; }
            """)

    def closeEvent(self, event):
        reply = QMessageBox.question(
            self, 'Подтверждение выхода', 'У вас могут быть несохраненные данные.\nВы уверены, что хотите закрыть?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = SmartLabApp()
    window.show()
    sys.exit(app.exec())