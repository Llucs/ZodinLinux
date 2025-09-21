#!/usr/bin/env python3
"""
Zodin Flash Tool - A Ferramenta Definitiva de Flash Samsung para Linux
Interface gráfica moderna e intuitiva para flash de dispositivos Samsung
"""

import os
import sys
import time
import threading
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

# Adiciona o diretório atual ao path para importações locais
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Configuração do ambiente Qt para suportar ambientes headless
if 'DISPLAY' not in os.environ:
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
else:
    os.environ.setdefault('QT_QPA_PLATFORM', 'xcb')

try:
    from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                                QHBoxLayout, QTabWidget, QLabel, QPushButton, 
                                QProgressBar, QTextEdit, QFileDialog, QMessageBox,
                                QGroupBox, QCheckBox, QSpinBox, QComboBox, QFrame,
                                QSplitter, QListWidget, QListWidgetItem, QGridLayout,
                                QScrollArea, QSizePolicy, QDialog, QProgressDialog,
                                QLineEdit, QGraphicsDropShadowEffect)
    from PyQt6.QtGui import QColor

    from PyQt6.QtCore import (Qt, QThread, pyqtSignal, QTimer, QPropertyAnimation, 
                             QEasingCurve, QRect, QParallelAnimationGroup, 
                             QSequentialAnimationGroup, QAbstractAnimation, QTranslator, QLocale)



except ImportError as e:
    print(f"❌ Erro ao importar PyQt6: {e}")
    print("💡 Instale com: pip install PyQt6")
    sys.exit(1)

try:
    from samsung_protocol import (ZodinFlashEngine, SamsungDevice, SamsungMode, 
                                 FlashProgress, FirmwareParser)
except ImportError as e:
    print(f"❌ Erro ao importar samsung_protocol: {e}")
    print(f"📁 Diretório atual: {current_dir}")
    print(f"🔍 Arquivos disponíveis: {os.listdir(current_dir)}")
    sys.exit(1)

try:
    from updater import ZodinUpdater
except ImportError as e:
    print(f"❌ Erro ao importar updater: {e}")
    print("⚠️ Sistema de atualização desabilitado")
    ZodinUpdater = None


class AnimatedButton(QPushButton):
    """Botão com animações fluidas"""
    def __init__(self, text, primary=False, danger=False, success=False):
        super().__init__(text)
        self.primary = primary
        self.danger = danger
        self.success = success
        self.animation = None
        self.setup_style()
        self.setup_animations()
    
    def setup_style(self):
        if self.danger:
            self.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0.0 #ff6b6b, stop:1 #ee5a52);
                    color: white;
                    border: none;
                    border-radius: 12px;
                    padding: 15px 30px;
                    font-size: 14px;
                    font-weight: bold;
                    min-width: 120px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0.0 #ff7979, stop:1 #fd6c6c);
                }
                QPushButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0.0 #e55656, stop:1 #d63447);
                }
                QPushButton:disabled {
                    background: #bdc3c7;
                    color: #7f8c8d;
                }
            """)
        elif self.success:
            self.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0.0 #00b894, stop:1 #00a085);
                    color: white;
                    border: none;
                    border-radius: 12px;
                    padding: 15px 30px;
                    font-size: 14px;
                    font-weight: bold;
                    min-width: 120px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0.0 #00cec9, stop:1 #00b894);
                }
                QPushButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0.0 #00a085, stop:1 #008f7a);
                }
            """)
        elif self.primary:
            self.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0.0 #6c5ce7, stop:1 #5f3dc4);
                    color: white;
                    border: none;
                    border-radius: 12px;
                    padding: 15px 30px;
                    font-size: 14px;
                    font-weight: bold;
                    min-width: 120px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0.0 #7d6ef0, stop:1 #6c5ce7);
                }
                QPushButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0.0 #5f3dc4, stop:1 #4c3baf);
                }
                QPushButton:disabled {
                    background: #bdc3c7;
                    color: #7f8c8d;
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0.0 #ffffff, stop:1 #f8f9fa);
                    color: #2d3436;
                    border: 2px solid #ddd;
                    border-radius: 12px;
                    padding: 12px 25px;
                    font-size: 13px;
                    font-weight: 500;
                    min-width: 100px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0.0 #f8f9fa, stop:1 #e9ecef);
                    border-color: #6c5ce7;
                }
                QPushButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0.0 #e9ecef, stop:1 #dee2e6);
                }
            """)
    
    def setup_animations(self):
        # Adiciona sombra
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 5)
        self.setGraphicsEffect(shadow)
    
    def enterEvent(self, event):
        """Animação ao passar o mouse"""
        if not self.animation:
            self.animation = QPropertyAnimation(self, b"geometry")
            self.animation.setDuration(200)
            self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Expande ligeiramente
        current_rect = self.geometry()
        new_rect = QRect(current_rect.x() - 2, current_rect.y() - 2,
                        current_rect.width() + 4, current_rect.height() + 4)
        
        self.animation.setStartValue(current_rect)
        self.animation.setEndValue(new_rect)
        self.animation.start()
        
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Animação ao sair o mouse"""
        if self.animation:
            current_rect = self.geometry()
            original_rect = QRect(current_rect.x() + 2, current_rect.y() + 2,
                                current_rect.width() - 4, current_rect.height() - 4)
            
            self.animation.setStartValue(current_rect)
            self.animation.setEndValue(original_rect)
            self.animation.start()
        
        super().leaveEvent(event)


class AnimatedProgressBar(QProgressBar):
    """Barra de progresso com animações"""
    def __init__(self):
        super().__init__()
        self.setup_style()
        self.pulse_animation = None
        self.setup_animations()
    
    def setup_style(self):
        self.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 15px;
                text-align: center;
                font-weight: bold;
                font-size: 14px;
                background-color: #ecf0f1;
                height: 30px;
                color: white;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0.0 #6c5ce7, stop:0.5 #a29bfe, stop:1 #fd79a8);
                border-radius: 13px;
                margin: 2px;
            }
        """)
    
    def setup_animations(self):
        # Animação de pulso quando ativo
        self.pulse_animation = QPropertyAnimation(self, b"value")
        self.pulse_animation.setDuration(1000)
        self.pulse_animation.setEasingCurve(QEasingCurve.Type.InOutSine)
    
    def setValue(self, value):
        """Override para adicionar animação suave"""
        if hasattr(self, '_last_value'):
            # Anima transição suave
            animation = QPropertyAnimation(self, b"value")
            animation.setDuration(300)
            animation.setStartValue(self._last_value)
            animation.setEndValue(value)
            animation.setEasingCurve(QEasingCurve.Type.OutCubic)
            animation.start()
        else:
            super().setValue(value)
        
        self._last_value = value


class GlowingLabel(QLabel):
    """Label com efeito de brilho"""
    def __init__(self, text=""):
        super().__init__(text)
        self.glow_animation = None
        self.setup_glow()
    
    def setup_glow(self):
        # Efeito de brilho
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(20)
        glow.setColor(QColor(108, 92, 231, 150))
        glow.setOffset(0, 0)
        self.setGraphicsEffect(glow)
        
        # Animação de pulso
        self.glow_animation = QPropertyAnimation(glow, b"blurRadius")
        self.glow_animation.setDuration(2000)
        self.glow_animation.setStartValue(15)
        self.glow_animation.setEndValue(25)
        self.glow_animation.setEasingCurve(QEasingCurve.Type.InOutSine)
        self.glow_animation.setLoopCount(-1)  # Loop infinito
        self.glow_animation.start()


class DeviceDetectionThread(QThread):
    """Thread para detecção de dispositivos com animações"""
    device_detected = pyqtSignal(list, bool)  # devices, any_connected
    
    def __init__(self, flash_engine):
        super().__init__()
        self.running = True
        self.flash_engine = flash_engine
    
    def run(self):
        while self.running:
            try:
                devices = self.flash_engine.detect_devices()
                connected = len(devices) > 0
                self.device_detected.emit(devices, connected)
                    
            except Exception as e:
                self.device_detected.emit([], False)
            
            self.msleep(2000)  # Verifica a cada 2 segundos
    
    def stop(self):
        self.running = False


class FlashThread(QThread):
    """Thread para operações de flash"""
    progress_updated = pyqtSignal(object)  # FlashProgress object
    log_updated = pyqtSignal(str)
    flash_completed = pyqtSignal(bool, str)
    
    def __init__(self, flash_engine, firmware_files, options):
        super().__init__()
        self.flash_engine = flash_engine
        self.firmware_files = firmware_files
        self.options = options
    
    def run(self):
        try:
            success = self.flash_engine.flash_firmware_files(self.firmware_files)
            
            if success:
                self.flash_completed.emit(True, "Flash concluído com sucesso! 🎉")
            else:
                self.flash_completed.emit(False, "Operação de flash falhou! ❌")
                
        except Exception as e:
            self.flash_completed.emit(False, f"Erro no flash: {str(e)}")


class ZodinFlashTool(QMainWindow):
    """Classe principal do Zodin Flash Tool"""
    
    def __init__(self):
        super().__init__()
        self.files = {}
        self.checkboxes = {}
        self.is_flashing = False
        self.device_thread = None
        self.flash_thread = None
        self.connected_devices = []
        self.current_device = None

        # Inicializa o tradutor
        self.translator = QTranslator()
        self.current_language = QLocale().name().split("_")[0] # Detecta o idioma do sistema
        self.switch_language(self.current_language)
        
        # Inicializa engine própria
        self.flash_engine = ZodinFlashEngine(
            progress_callback=self.update_flash_progress,
            log_callback=self.log
        )
        
        # Inicializa sistema de atualização
        if ZodinUpdater:
            self.updater = ZodinUpdater(self, "1.1.0")
        else:
            self.updater = None
        
        self.init_ui()
        self.setup_device_detection()
        self.setup_animations()
        
        # Verifica atualizações após 3 segundos (para não atrasar a inicialização)
        if self.updater:
            QTimer.singleShot(3000, self.updater.check_for_updates)
    
    def init_ui(self):
        """Inicializa a interface do usuário"""
        self.setWindowTitle("Zodin Flash Tool v1.0.0 - The Ultimate Samsung Flash Tool")
        self.resize(1600, 1000) # Tamanho inicial da janela
        self.setMinimumSize(1200, 800) # Tamanho mínimo para responsividade
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(25)
        main_layout.setContentsMargins(25, 25, 25, 25)
        
        # Splitter para dividir a interface
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Painel esquerdo
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # Painel direito
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        # Proporções do splitter
        splitter.setSizes([500, 1100])
        
        # Aplica estilo moderno
        self.apply_modern_style(dark_mode=False)

        # Adiciona um menu para alternar o modo escuro
        menu_bar = self.menuBar()
        view_menu = menu_bar.addMenu("Visualização")
        dark_mode_action = view_menu.addAction("Modo Escuro")
        dark_mode_action.setCheckable(True)
        dark_mode_action.toggled.connect(self.toggle_dark_mode)

        # Adiciona um menu para trocar o idioma
        lang_menu = menu_bar.addMenu("Idioma")
        en_action = lang_menu.addAction("English")
        en_action.triggered.connect(lambda: self.switch_language("en"))
        pt_action = lang_menu.addAction("Português")
        pt_action.triggered.connect(lambda: self.switch_language("pt"))

    def toggle_dark_mode(self, checked):
        self.apply_modern_style(dark_mode=checked)

    def switch_language(self, lang_code):
        if lang_code == "en":
            self.translator.load("en", ".")
        elif lang_code == "pt":
            self.translator.load("pt", ".")
        QApplication.instance().installTranslator(self.translator)
        self.retranslateUi()

    def retranslateUi(self):
        # TODO: Implementar a re-tradução de todos os elementos da UI
        self.setWindowTitle(self.tr("Zodin Flash Tool - The Ultimate Samsung Flash Tool"))
        # Exemplo: self.device_status.setText(self.tr("Searching for devices..."))
        # Isso precisará ser feito para todos os textos visíveis na UI


    
    def create_left_panel(self):
        """Cria o painel esquerdo com design moderno"""
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(20)
        
        # Header com logo animado
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0.0 #667eea, stop:1 #764ba2);
                border-radius: 20px;
                margin-bottom: 15px;
            }
        """)
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(30, 30, 30, 30)
        
        # Logo animado
        logo_label = GlowingLabel("ZODIN")
        logo_label.setStyleSheet("""
            QLabel {
                font-size: 42px;
                font-weight: bold;
                color: white;
                margin: 15px;
                text-align: center;
            }
        """)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(logo_label)
        
        subtitle_label = QLabel("Flash Tool v1.0.0")
        subtitle_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                color: rgba(255, 255, 255, 0.9);
                margin-bottom: 15px;
                text-align: center;
            }
        """)
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(subtitle_label)
        
        tagline_label = QLabel("The Ultimate Samsung Flash Tool")
        tagline_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: rgba(255, 255, 255, 0.7);
                font-style: italic;
                text-align: center;
            }
        """)
        tagline_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(tagline_label)
        
        left_layout.addWidget(header_frame)
        
        # Status do dispositivo com animações
        device_group = QGroupBox("🔌 Status do Dispositivo")
        device_layout = QVBoxLayout(device_group)
        
        self.device_status = QLabel("🔍 Procurando dispositivos...")
        self.device_status.setStyleSheet("""
            QLabel {
                padding: 15px;
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 10px;
                font-size: 14px;
                font-weight: bold;
                color: #333;
            }
        """)
        device_layout.addWidget(self.device_status)
        
        # Lista de dispositivos
        self.devices_list = QListWidget()
        self.devices_list.setMaximumHeight(120)
        self.devices_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ccc;
                border-radius: 8px;
                background-color: #ffffff;
                font-size: 13px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 4px;
                margin: 2px;
            }
            QListWidget::item:selected {
                background-color: #6c5ce7;
                color: white;
            }
        """)
        device_layout.addWidget(self.devices_list)
        
        # Botão de refresh
        refresh_btn = AnimatedButton("🔄 Atualizar Dispositivos")
        refresh_btn.clicked.connect(self.refresh_devices)
        device_layout.addWidget(refresh_btn)
        
        left_layout.addWidget(device_group)
        
        # Configurações rápidas
        settings_group = QGroupBox("⚙️ Configurações Rápidas")
        settings_layout = QVBoxLayout(settings_group)
        
        self.auto_reboot_cb = QCheckBox("🔄 Auto Reboot")
        self.auto_reboot_cb.setChecked(True)
        self.auto_reboot_cb.setStyleSheet("font-size: 14px; padding: 5px;")
        
        self.verify_files_cb = QCheckBox("✅ Verificar Integridade")
        self.verify_files_cb.setChecked(True)
        self.verify_files_cb.setStyleSheet("font-size: 14px; padding: 5px;")
        
        self.backup_before_flash_cb = QCheckBox("💾 Backup Antes do Flash")
        self.backup_before_flash_cb.setStyleSheet("font-size: 14px; padding: 5px;")
        
        settings_layout.addWidget(self.auto_reboot_cb)
        settings_layout.addWidget(self.verify_files_cb)
        settings_layout.addWidget(self.backup_before_flash_cb)
        
        left_layout.addWidget(settings_group)
        
        # Log com design moderno
        log_group = QGroupBox("📋 Log de Atividades")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0.0 #2d3436, stop:1 #636e72);
                color: #00ff88;
                border: none;
                border-radius: 12px;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 12px;
                padding: 15px;
                line-height: 1.4;
            }
        """)
        log_layout.addWidget(self.log_text)
        
        # Botões do log
        log_buttons_layout = QHBoxLayout()
        clear_log_btn = AnimatedButton("🧹 Limpar")
        clear_log_btn.clicked.connect(self.clear_log)
        save_log_btn = AnimatedButton("💾 Salvar")
        save_log_btn.clicked.connect(self.save_log)
        
        log_buttons_layout.addWidget(clear_log_btn)
        log_buttons_layout.addWidget(save_log_btn)
        log_layout.addLayout(log_buttons_layout)
        
        left_layout.addWidget(log_group)
        
        return left_widget
    
    def create_right_panel(self):
        """Cria o painel direito com abas modernas"""
        tab_widget = QTabWidget()
        tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 3px solid #6c5ce7;
                border-radius: 15px;
                background-color: white;
                margin-top: 10px;
            }
            QTabBar::tab {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0.0 #f8f9fa, stop:1 #e9ecef);
                border: 2px solid #ddd;
                padding: 15px 25px;
                margin-right: 3px;
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
                font-weight: bold;
                font-size: 14px;
                min-width: 120px;
            }
            QTabBar::tab:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0.0 #6c5ce7, stop:1 #5f3dc4);
                color: white;
                border-bottom-color: #6c5ce7;
            }
            QTabBar::tab:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0.0 #a29bfe, stop:1 #6c5ce7);
                color: white;
            }
        """)
        
        # Aba Flash
        flash_tab = self.create_flash_tab()
        tab_widget.addTab(flash_tab, "🔥 Flash")
        
        # Aba Backup
        backup_tab = self.create_backup_tab()
        tab_widget.addTab(backup_tab, "💾 Backup")
        
        # Aba Download
        download_tab = self.create_download_tab()
        tab_widget.addTab(download_tab, "📥 Download")
        
        # Aba Ferramentas
        tools_tab = self.create_tools_tab()
        tab_widget.addTab(tools_tab, "🔧 Tools")
        
        # Aba Configurações
        settings_tab = self.create_settings_tab()
        tab_widget.addTab(settings_tab, "⚙️ Config")
        
        # Aba Sobre
        about_tab = self.create_about_tab()
        tab_widget.addTab(about_tab, "ℹ️ About")
        
        return tab_widget
    
    def create_flash_tab(self):
        """Cria a aba de flash com design moderno"""
        flash_widget = QWidget()
        flash_layout = QVBoxLayout(flash_widget)
        flash_layout.setSpacing(25)
        
        # Arquivos de firmware
        files_group = QGroupBox("📁 Arquivos de Firmware")
        files_layout = QVBoxLayout(files_group)
        
        file_types = [
            ('BL', 'Bootloader', '🔧'),
            ('AP', 'Android Platform', '📱'),
            ('CP', 'Cellular Processor', '📡'),
            ('CSC', 'Consumer Software Customization', '🌍'),
            ('USERDATA', 'User Data', '👤')
        ]
        
        for file_type, description, icon in file_types:
            file_row = self.create_modern_file_row(file_type, description, icon)
            files_layout.addWidget(file_row)
        
        flash_layout.addWidget(files_group)
        
        # Progresso com animações
        progress_group = QGroupBox("📊 Progresso do Flash")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_bar = AnimatedProgressBar()
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)
        
        self.progress_details = QLabel("")
        self.progress_details.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_details.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #636e72;
                margin: 10px;
            }
        """)
        self.progress_details.setVisible(False)
        progress_layout.addWidget(self.progress_details)
        
        flash_layout.addWidget(progress_group)
        
        # Botões de ação
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        verify_button = AnimatedButton("🔍 Verificar Arquivos")
        verify_button.clicked.connect(self.verify_files)
        
        reset_button = AnimatedButton("🧹 Limpar Tudo")
        reset_button.clicked.connect(self.reset_form)
        
        self.start_button = AnimatedButton("🚀 Iniciar Flash", primary=True)
        self.start_button.clicked.connect(self.start_flash)
        
        buttons_layout.addWidget(verify_button)
        buttons_layout.addWidget(reset_button)
        buttons_layout.addWidget(self.start_button)
        
        flash_layout.addLayout(buttons_layout)
        flash_layout.addStretch()
        
        return flash_widget
    
    def create_modern_file_row(self, file_type, description, icon):
        """Cria uma linha moderna para seleção de arquivo"""
        row_frame = QFrame()
        row_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 2px solid #e9ecef;
                border-radius: 12px;
                margin: 5px;
                padding: 10px;
            }
            QFrame:hover {
                border-color: #6c5ce7;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0.0 #ffffff, stop:1 #f8f9ff);
            }
        """)
        
        row_layout = QHBoxLayout(row_frame)
        row_layout.setContentsMargins(15, 15, 15, 15)
        
        # Checkbox com ícone
        checkbox_layout = QVBoxLayout()
        checkbox = QCheckBox()
        checkbox.setStyleSheet("""
            QCheckBox::indicator {
                width: 25px;
                height: 25px;
                border-radius: 12px;
                border: 3px solid #ddd;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0.0 #6c5ce7, stop:1 #5f3dc4);
                border-color: #6c5ce7;
            }
        """)
        self.checkboxes[file_type] = checkbox
        
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 24px; margin: 5px;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        checkbox_layout.addWidget(checkbox)
        checkbox_layout.addWidget(icon_label)
        row_layout.addLayout(checkbox_layout)
        
        # Informações do arquivo
        info_layout = QVBoxLayout()
        
        type_label = QLabel(f"{file_type}")
        type_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #2d3436;
                margin-bottom: 5px;
            }
        """)
        
        desc_label = QLabel(description)
        desc_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #636e72;
                margin-bottom: 10px;
            }
        """)
        
        file_edit = QLineEdit()
        file_edit.setReadOnly(True)
        file_edit.setPlaceholderText(f"Selecione o arquivo {file_type}...")
        file_edit.setStyleSheet("""
            QLineEdit {
                padding: 12px 15px;
                font-size: 13px;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                background-color: #f8f9fa;
            }
            QLineEdit:focus {
                border-color: #6c5ce7;
                background-color: white;
            }
        """)
        self.files[file_type] = file_edit
        
        info_layout.addWidget(type_label)
        info_layout.addWidget(desc_label)
        info_layout.addWidget(file_edit)
        row_layout.addLayout(info_layout)
        
        # Botões
        buttons_layout = QVBoxLayout()
        
        browse_button = AnimatedButton("📁")
        browse_button.setMaximumWidth(60)
        browse_button.clicked.connect(lambda: self.browse_file(file_type))
        
        info_button = AnimatedButton("ℹ️")
        info_button.setMaximumWidth(60)
        info_button.clicked.connect(lambda: self.show_file_info(file_type))
        
        buttons_layout.addWidget(browse_button)
        buttons_layout.addWidget(info_button)
        row_layout.addLayout(buttons_layout)
        
        return row_frame
    
    def create_backup_tab(self):
        """Cria a aba de backup"""
        backup_widget = QWidget()
        backup_layout = QVBoxLayout(backup_widget)
        
        # Placeholder para funcionalidades de backup
        placeholder = QLabel("🚧 Funcionalidades de Backup em Desenvolvimento 🚧")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("""
            QLabel {
                font-size: 24px;
                color: #636e72;
                margin: 50px;
                padding: 50px;
                border: 3px dashed #ddd;
                border-radius: 20px;
            }
        """)
        backup_layout.addWidget(placeholder)
        
        return backup_widget
    
    def create_download_tab(self):
        """Cria a aba de download"""
        download_widget = QWidget()
        download_layout = QVBoxLayout(download_widget)
        
        # Placeholder para funcionalidades de download
        placeholder = QLabel("🚧 Funcionalidades de Download em Desenvolvimento 🚧")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("""
            QLabel {
                font-size: 24px;
                color: #636e72;
                margin: 50px;
                padding: 50px;
                border: 3px dashed #ddd;
                border-radius: 20px;
            }
        """)
        download_layout.addWidget(placeholder)
        
        return download_widget
    
    def create_settings_tab(self):
        """Cria a aba de configurações"""
        settings_widget = QWidget()
        settings_layout = QVBoxLayout(settings_widget)
        settings_layout.setSpacing(25)
        
        # Configurações de Atualização
        update_group = QGroupBox("🔄 Sistema de Atualização")
        update_layout = QVBoxLayout(update_group)
        
        # Obter configurações atuais
        update_config = self.updater.get_update_settings()
        
        # Auto verificação
        self.auto_check_cb = QCheckBox("🔍 Verificar atualizações automaticamente")
        self.auto_check_cb.setChecked(update_config.get("auto_check", True))
        self.auto_check_cb.setStyleSheet("font-size: 14px; padding: 8px;")
        update_layout.addWidget(self.auto_check_cb)
        
        # Intervalo de verificação
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("⏰ Verificar a cada:"))
        
        self.check_interval_spin = QSpinBox()
        self.check_interval_spin.setRange(1, 168)  # 1 hora a 1 semana
        self.check_interval_spin.setValue(update_config.get("check_interval", 24))
        self.check_interval_spin.setSuffix(" horas")
        self.check_interval_spin.setStyleSheet("""
            QSpinBox {
                padding: 8px;
                font-size: 14px;
                border: 2px solid #ddd;
                border-radius: 8px;
                min-width: 100px;
            }
        """)
        interval_layout.addWidget(self.check_interval_spin)
        interval_layout.addStretch()
        update_layout.addLayout(interval_layout)
        
        # Apenas atualizações críticas
        self.critical_only_cb = QCheckBox("⚠️ Notificar apenas atualizações críticas")
        self.critical_only_cb.setChecked(update_config.get("notify_critical_only", False))
        self.critical_only_cb.setStyleSheet("font-size: 14px; padding: 8px;")
        update_layout.addWidget(self.critical_only_cb)
        
        # Botões de ação
        update_buttons_layout = QHBoxLayout()
        
        check_now_btn = AnimatedButton("🔍 Verificar Agora", primary=True)
        check_now_btn.clicked.connect(self.check_updates_manually)
        
        save_settings_btn = AnimatedButton("💾 Salvar Configurações", success=True)
        save_settings_btn.clicked.connect(self.save_update_settings)
        
        reset_skipped_btn = AnimatedButton("🔄 Resetar Versões Puladas")
        reset_skipped_btn.clicked.connect(self.reset_skipped_versions)
        
        update_buttons_layout.addWidget(check_now_btn)
        update_buttons_layout.addWidget(save_settings_btn)
        update_buttons_layout.addWidget(reset_skipped_btn)
        update_layout.addLayout(update_buttons_layout)
        
        # Informações da última verificação
        last_check = update_config.get("last_check")
        if last_check:
            try:
                from datetime import datetime
                last_check_date = datetime.fromisoformat(last_check)
                last_check_str = last_check_date.strftime("%d/%m/%Y às %H:%M")
            except:
                last_check_str = "Data inválida"
        else:
            last_check_str = "Nunca"
        
        last_check_label = QLabel(f"📅 Última verificação: {last_check_str}")
        last_check_label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                color: #636e72;
                padding: 10px;
                background-color: #f8f9fa;
                border-radius: 8px;
                margin-top: 10px;
            }
        """)
        update_layout.addWidget(last_check_label)
        
        settings_layout.addWidget(update_group)
        
        # Configurações da Interface
        interface_group = QGroupBox("🎨 Interface e Aparência")
        interface_layout = QVBoxLayout(interface_group)
        
        # Animações
        self.animations_cb = QCheckBox("✨ Ativar animações fluidas")
        self.animations_cb.setChecked(True)
        self.animations_cb.setStyleSheet("font-size: 14px; padding: 8px;")
        interface_layout.addWidget(self.animations_cb)
        
        # Tema
        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("🎨 Tema:"))
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["🌟 Automático", "☀️ Claro", "🌙 Escuro"])
        self.theme_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                font-size: 14px;
                border: 2px solid #ddd;
                border-radius: 8px;
                min-width: 150px;
            }
        """)
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        interface_layout.addLayout(theme_layout)
        
        # Idioma
        language_layout = QHBoxLayout()
        language_layout.addWidget(QLabel("🌍 Idioma:"))
        
        self.language_combo = QComboBox()
        self.language_combo.addItems(["🇧🇷 Português", "🇺🇸 English"])
        self.language_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                font-size: 14px;
                border: 2px solid #ddd;
                border-radius: 8px;
                min-width: 150px;
            }
        """)
        language_layout.addWidget(self.language_combo)
        language_layout.addStretch()
        interface_layout.addLayout(language_layout)
        
        settings_layout.addWidget(interface_group)
        
        # Configurações Avançadas
        advanced_group = QGroupBox("🔧 Configurações Avançadas")
        advanced_layout = QVBoxLayout(advanced_group)
        
        # Debug mode
        self.debug_mode_cb = QCheckBox("🐛 Modo Debug (logs detalhados)")
        self.debug_mode_cb.setStyleSheet("font-size: 14px; padding: 8px;")
        advanced_layout.addWidget(self.debug_mode_cb)
        
        # Timeout USB
        timeout_layout = QHBoxLayout()
        timeout_layout.addWidget(QLabel("⏱️ Timeout USB:"))
        
        self.usb_timeout_spin = QSpinBox()
        self.usb_timeout_spin.setRange(1000, 30000)
        self.usb_timeout_spin.setValue(5000)
        self.usb_timeout_spin.setSuffix(" ms")
        self.usb_timeout_spin.setStyleSheet("""
            QSpinBox {
                padding: 8px;
                font-size: 14px;
                border: 2px solid #ddd;
                border-radius: 8px;
                min-width: 100px;
            }
        """)
        timeout_layout.addWidget(self.usb_timeout_spin)
        timeout_layout.addStretch()
        advanced_layout.addLayout(timeout_layout)
        
        # Chunk size
        chunk_layout = QHBoxLayout()
        chunk_layout.addWidget(QLabel("📦 Tamanho do Chunk:"))
        
        self.chunk_size_combo = QComboBox()
        self.chunk_size_combo.addItems([
            "512 KB", "1 MB", "2 MB", "4 MB", "8 MB"
        ])
        self.chunk_size_combo.setCurrentText("1 MB")
        self.chunk_size_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                font-size: 14px;
                border: 2px solid #ddd;
                border-radius: 8px;
                min-width: 100px;
            }
        """)
        chunk_layout.addWidget(self.chunk_size_combo)
        chunk_layout.addStretch()
        advanced_layout.addLayout(chunk_layout)
        
        settings_layout.addWidget(advanced_group)
        
        # Botões gerais
        general_buttons_layout = QHBoxLayout()
        general_buttons_layout.addStretch()
        
        reset_all_btn = AnimatedButton("🔄 Restaurar Padrões", danger=True)
        reset_all_btn.clicked.connect(self.reset_all_settings)
        
        apply_btn = AnimatedButton("✅ Aplicar Todas", primary=True)
        apply_btn.clicked.connect(self.apply_all_settings)
        
        general_buttons_layout.addWidget(reset_all_btn)
        general_buttons_layout.addWidget(apply_btn)
        
        settings_layout.addLayout(general_buttons_layout)
        settings_layout.addStretch()
        
        return settings_widget
    
    def check_updates_manually(self):
        """Verifica atualizações manualmente"""
        self.log("🔍 Verificando atualizações manualmente...")
        self.updater.manual_check()
    
    def save_update_settings(self):
        """Salva configurações de atualização"""
        settings = {
            "auto_check": self.auto_check_cb.isChecked(),
            "check_interval": self.check_interval_spin.value(),
            "notify_critical_only": self.critical_only_cb.isChecked()
        }
        
        self.updater.update_settings(settings)
        self.log("💾 Configurações de atualização salvas")
        
        QMessageBox.information(
            self,
            "Configurações Salvas",
            "✅ Configurações de atualização salvas com sucesso!"
        )
    
    def reset_skipped_versions(self):
        """Reseta versões puladas"""
        settings = self.updater.get_update_settings()
        settings["skipped_versions"] = []
        self.updater.update_settings(settings)
        
        self.log("🔄 Lista de versões puladas foi resetada")
        QMessageBox.information(
            self,
            "Versões Resetadas",
            "🔄 Lista de versões puladas foi resetada.\n"
            "Você será notificado sobre todas as atualizações novamente."
        )
    
    def reset_all_settings(self):
        """Restaura todas as configurações para o padrão"""
        reply = QMessageBox.question(
            self,
            "Restaurar Configurações",
            "⚠️ Tem certeza que deseja restaurar todas as configurações para o padrão?\n\n"
            "Esta ação não pode ser desfeita.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Restaura configurações de atualização
            default_update_settings = {
                "auto_check": True,
                "check_interval": 24,
                "notify_critical_only": False,
                "skipped_versions": []
            }
            self.updater.update_settings(default_update_settings)
            
            # Restaura controles da interface
            self.auto_check_cb.setChecked(True)
            self.check_interval_spin.setValue(24)
            self.critical_only_cb.setChecked(False)
            self.animations_cb.setChecked(True)
            self.theme_combo.setCurrentIndex(0)
            self.language_combo.setCurrentIndex(0)
            self.debug_mode_cb.setChecked(False)
            self.usb_timeout_spin.setValue(5000)
            self.chunk_size_combo.setCurrentText("1 MB")
            
            self.log("🔄 Todas as configurações foram restauradas para o padrão")
            QMessageBox.information(
                self,
                "Configurações Restauradas",
                "✅ Todas as configurações foram restauradas para o padrão!"
            )
    
    def apply_all_settings(self):
        """Aplica todas as configurações"""
        # Salva configurações de atualização
        self.save_update_settings()
        
        # Aplica outras configurações
        self.log("✅ Todas as configurações foram aplicadas")
        QMessageBox.information(
            self,
            "Configurações Aplicadas",
            "✅ Todas as configurações foram aplicadas com sucesso!\n\n"
            "Algumas mudanças podem exigir reinicialização da aplicação."
        )
    
    def create_tools_tab(self):
        """Cria a aba de ferramentas"""
        tools_widget = QWidget()
        tools_layout = QVBoxLayout(tools_widget)
        
        # Placeholder para ferramentas
        placeholder = QLabel("🚧 Ferramentas Avançadas em Desenvolvimento 🚧")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("""
            QLabel {
                font-size: 24px;
                color: #636e72;
                margin: 50px;
                padding: 50px;
                border: 3px dashed #ddd;
                border-radius: 20px;
            }
        """)
        tools_layout.addWidget(placeholder)
        
        return tools_widget
    
    def create_about_tab(self):
        """Cria a aba sobre"""
        about_widget = QWidget()
        about_layout = QVBoxLayout(about_widget)
        
        # Título com animação
        title_frame = QFrame()
        title_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0.0 #667eea, stop:0.5 #764ba2, stop:1 #f093fb);
                border-radius: 20px;
                margin: 20px;
            }
        """)
        title_layout = QVBoxLayout(title_frame)
        title_layout.setContentsMargins(40, 40, 40, 40)
        
        app_title = GlowingLabel("ZODIN FLASH TOOL")
        app_title.setStyleSheet("""
            QLabel {
                font-size: 48px;
                font-weight: bold;
                color: white;
                margin: 20px;
                text-align: center;
            }
        """)
        app_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_layout.addWidget(app_title)
        
        version_label = QLabel("Version 1.0.0 - The Ultimate Samsung Flash Tool")
        version_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                color: rgba(255, 255, 255, 0.9);
                margin-bottom: 20px;
                text-align: center;
            }
        """)
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_layout.addWidget(version_label)
        
        about_layout.addWidget(title_frame)
        
        # Descrição
        description = QLabel("""
        <div style="text-align: center; line-height: 1.8;">
        <h2 style="color: #6c5ce7;">🚀 A Revolução do Flash Samsung no Linux</h2>
        
        <p style="font-size: 16px; margin: 20px 0;">
        O <b>Zodin Flash Tool</b> representa uma nova era nas ferramentas de flash Samsung para Linux. 
        Combinando o conhecimento e as melhores práticas de todas as ferramentas existentes, 
        criamos uma experiência única, moderna e poderosa.
        </p>
        
        <h3 style="color: #00b894;">✨ Características Revolucionárias:</h3>
        <div style="text-align: left; max-width: 600px; margin: 0 auto;">
        <p>🎨 <b>Interface Moderna:</b> Design fluido com animações suaves</p>
        <p>⚡ <b>Protocolo Próprio:</b> Implementação nativa dos protocolos Samsung</p>
        <p>🔧 <b>Detecção Inteligente:</b> Reconhecimento automático de dispositivos</p>
        <p>🛡️ <b>Segurança Avançada:</b> Verificações de integridade integradas</p>
        <p>📊 <b>Progresso Visual:</b> Feedback em tempo real com animações</p>
        <p>🌟 <b>Experiência Única:</b> Fusão do melhor de todas as ferramentas</p>
        </div>
        
        <h3 style="color: #e17055;">💡 Inovação Tecnológica:</h3>
        <p style="font-size: 14px; color: #636e72;">
        Diferente de outras ferramentas que dependem de binários externos, o Zodin implementa 
        seus próprios protocolos de comunicação Samsung, oferecendo controle total e 
        performance otimizada.
        </p>
        
        <p style="margin-top: 30px; font-style: italic; color: #6c5ce7;">
        "Desenvolvido com ❤️ para elevar o padrão das ferramentas Linux"
        </p>
        </div>
        """)
        description.setWordWrap(True)
        description.setStyleSheet("""
            QLabel {
                padding: 30px;
                background-color: white;
                border-radius: 15px;
                border: 2px solid #e9ecef;
            }
        """)
        about_layout.addWidget(description)
        
        about_layout.addStretch()
        
        return about_widget

    def apply_modern_style(self, dark_mode=False):
        """Aplica um estilo moderno e limpo à aplicação"""
        if dark_mode:
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #2c3e50; /* Dark Blue-Grey */
                    color: #ecf0f1; /* Light Grey */
                }
                QTabWidget::pane {
                    border: none;
                    border-top: 3px solid #3498db; /* Blue */
                }
                QTabBar::tab {
                    background: #34495e; /* Darker Blue-Grey */
                    color: #ecf0f1;
                    padding: 15px 30px;
                    font-size: 14px;
                    font-weight: bold;
                    border-top-left-radius: 10px;
                    border-top-right-radius: 10px;
                    min-width: 150px;
                }
                QTabBar::tab:selected {
                    background: #3498db;
                    color: white;
                }
                QTabBar::tab:hover {
                    background: #2980b9; /* Slightly darker blue */
                }
                QGroupBox {
                    font-size: 16px;
                    font-weight: bold;
                    color: #ecf0f1;
                    border: 2px solid #34495e;
                    border-radius: 15px;
                    margin-top: 10px;
                    padding: 20px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    subcontrol-position: top left;
                    padding: 0 10px;
                    background-color: #2c3e50;
                }
                QLabel {
                    font-size: 14px;
                    color: #ecf0f1;
                }
                QTextEdit {
                    background-color: #34495e;
                    border: 2px solid #2980b9;
                    border-radius: 10px;
                    padding: 10px;
                    font-family: 'monospace';
                    font-size: 13px;
                    color: #ecf0f1;
                }
                QListWidget {
                    background-color: #34495e;
                    border: 2px solid #2980b9;
                    border-radius: 10px;
                    padding: 10px;
                }
                QListWidget::item {
                    padding: 12px;
                    border-bottom: 1px solid #2c3e50;
                }
                QListWidget::item:selected {
                    background-color: #3498db;
                    color: white;
                    border-radius: 8px;
                }
                QCheckBox {
                    spacing: 10px;
                    font-size: 14px;
                    color: #ecf0f1;
                }
                QCheckBox::indicator {
                    width: 20px;
                    height: 20px;
                    border: 2px solid #3498db;
                    border-radius: 10px;
                    background-color: #2c3e50;
                }
                QCheckBox::indicator:checked {
                    background-color: #3498db;
                }
            """)
        else:
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #ecf0f1; /* Light Grey Background */
                    color: #2c3e50; /* Dark Blue-Grey */
                }
                QTabWidget::pane {
                    border: none;
                    border-top: 3px solid #3498db; /* Blue */
                }
                QTabBar::tab {
                    background: #bdc3c7; /* Medium Grey */
                    color: #2c3e50;
                    padding: 15px 30px;
                    font-size: 14px;
                    font-weight: bold;
                    border-top-left-radius: 10px;
                    border-top-right-radius: 10px;
                    min-width: 150px;
                }
                QTabBar::tab:selected {
                    background: #3498db;
                    color: white;
                }
                QTabBar::tab:hover {
                    background: #aeb6bf; /* Slightly darker grey */
                }
                QGroupBox {
                    font-size: 16px;
                    font-weight: bold;
                    color: #2c3e50;
                    border: 2px solid #bdc3c7;
                    border-radius: 15px;
                    margin-top: 10px;
                    padding: 20px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    subcontrol-position: top left;
                    padding: 0 10px;
                    background-color: #ecf0f1;
                }
                QLabel {
                    font-size: 14px;
                    color: #2c3e50;
                }
                QTextEdit {
                    background-color: #ffffff;
                    border: 2px solid #bdc3c7;
                    border-radius: 10px;
                    padding: 10px;
                    font-family: 'monospace';
                    font-size: 13px;
                    color: #2c3e50;
                }
                QListWidget {
                    background-color: #ffffff;
                    border: 2px solid #bdc3c7;
                    border-radius: 10px;
                    padding: 10px;
                }
                QListWidget::item {
                    padding: 12px;
                    border-bottom: 1px solid #ecf0f1;
                }
                QListWidget::item:selected {
                    background-color: #3498db;
                    color: white;
                    border-radius: 8px;
                }
                QCheckBox {
                    spacing: 10px;
                    font-size: 14px;
                    color: #2c3e50;
                }
                QCheckBox::indicator {
                    width: 20px;
                    height: 20px;
                    border: 2px solid #3498db;
                    border-radius: 10px;
                    background-color: #ffffff;
                }
                QCheckBox::indicator:checked {
                    background-color: #3498db;
                }
            """)
    
    def setup_device_detection(self):
        """Configura a detecção de dispositivos"""
        self.device_thread = DeviceDetectionThread(self.flash_engine)
        self.device_thread.device_detected.connect(self.update_device_status)
        self.device_thread.start()
    
    def setup_animations(self):
        """Configura animações da interface"""
        # Animação de entrada da janela
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(1000)
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.fade_animation.start()
    
    def update_device_status(self, devices, any_connected):
        """Atualiza o status dos dispositivos com animações"""
        self.connected_devices = devices
        self.devices_list.clear()
        
        if any_connected:
            self.device_status.setText("✅ Dispositivo Samsung Detectado!")
            self.device_status.setStyleSheet("""
                QLabel {
                    padding: 20px;
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0.0 #00b894, stop:1 #00a085);
                    border: none;
                    border-radius: 12px;
                    font-size: 15px;
                    font-weight: bold;
                    color: white;
                }
            """)
            self.start_button.setEnabled(True)

            for device in devices:
                if device.mode == SamsungMode.ADB:
                    item_text = f"📱 {device.model or 'Dispositivo Android'} ({device.serial_number}) - ADB"
                else:
                    item_text = f"📱 {device.model or 'Samsung Device'} ({device.serial_number}) - {device.mode.value.capitalize()}"
                item = QListWidgetItem(item_text)
                self.devices_list.addItem(item)

            # Conecta ao primeiro dispositivo
            if devices and not self.current_device:
                self.current_device = devices[0]
                if self.current_device.mode != SamsungMode.ADB:
                    self.flash_engine.connect_device(self.current_device)
                self.log(f"🔗 Conectado ao dispositivo: {self.current_device.model or 'Samsung Device'} ({self.current_device.mode.value.capitalize()})")
        else:
            self.device_status.setText("🔍 Procurando dispositivos Samsung...")
            self.device_status.setStyleSheet("""
                QLabel {
                    padding: 20px;
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0.0 #ffeaa7, stop:1 #fdcb6e);
                    border: none;
                    border-radius: 12px;
                    font-size: 15px;
                    font-weight: bold;
                    color: #2d3436;
                }
            """)
            self.start_button.setEnabled(False)
            self.current_device = None
            
            # Adiciona mensagem na lista
            item = QListWidgetItem("🔍 Nenhum dispositivo detectado")
            self.devices_list.addItem(item)
    
    def log(self, message):
        """Adiciona mensagem ao log com timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.log_text.append(formatted_message)
        
        # Auto-scroll para o final
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)
    
    def update_flash_progress(self, progress: FlashProgress):
        """Atualiza progresso do flash com animações"""
        if hasattr(self, 'progress_bar'):
            self.progress_bar.setValue(int(progress.percentage))
            
            details = f"📁 {progress.current_file} | 📊 {progress.stage}"
            if progress.total_bytes > 0:
                mb_current = progress.current_bytes / (1024 * 1024)
                mb_total = progress.total_bytes / (1024 * 1024)
                details += f" | 💾 {mb_current:.1f}/{mb_total:.1f} MB"
            
            self.progress_details.setText(details)
    
    def browse_file(self, file_type):
        """Abre diálogo para selecionar arquivo"""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            f"Selecionar arquivo {file_type}",
            "",
            "Arquivos de firmware (*.tar *.md5 *.bin *.img *.tar.md5);;Todos os arquivos (*.*)"
        )
        
        if filename:
            self.files[file_type].setText(filename)
            self.checkboxes[file_type].setChecked(True)
            self.log(f"📁 Selecionado {file_type}: {os.path.basename(filename)}")
            
            # Animação de confirmação
            self.animate_file_selection(file_type)
    
    def animate_file_selection(self, file_type):
        """Anima a seleção de arquivo"""
        file_edit = self.files[file_type]
        
        # Animação de destaque
        original_style = file_edit.styleSheet()
        highlight_style = original_style.replace(
            "border: 2px solid #e9ecef;",
            "border: 3px solid #00b894;"
        )
        
        file_edit.setStyleSheet(highlight_style)
        
        # Volta ao normal após 1 segundo
        QTimer.singleShot(1000, lambda: file_edit.setStyleSheet(original_style))
    
    def show_file_info(self, file_type):
        """Mostra informações do arquivo"""
        file_path = self.files[file_type].text()
        if not file_path:
            QMessageBox.warning(self, "Aviso", f"Nenhum arquivo {file_type} selecionado!")
            return
        
        try:
            file_size = os.path.getsize(file_path)
            file_size_mb = file_size / (1024 * 1024)
            
            # Verifica integridade se solicitado
            integrity_status = "✅ Válido"
            if self.verify_files_cb.isChecked():
                if FirmwareParser.verify_firmware_integrity(file_path):
                    integrity_status = "✅ Integridade Verificada"
                else:
                    integrity_status = "⚠️ Falha na Verificação"
            
            info_text = f"""
            <h3>📁 Informações do Arquivo {file_type}</h3>
            <p><b>Nome:</b> {os.path.basename(file_path)}</p>
            <p><b>Caminho:</b> {file_path}</p>
            <p><b>Tamanho:</b> {file_size_mb:.2f} MB ({file_size:,} bytes)</p>
            <p><b>Tipo:</b> {file_type}</p>
            <p><b>Integridade:</b> {integrity_status}</p>
            """
            
            QMessageBox.information(self, f"Informações - {file_type}", info_text)
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao obter informações: {str(e)}")
    
    def verify_files(self):
        """Verifica integridade dos arquivos selecionados"""
        selected_files = []
        for file_type, file_edit in self.files.items():
            if self.checkboxes[file_type].isChecked() and file_edit.text():
                selected_files.append((file_type, file_edit.text()))
        
        if not selected_files:
            QMessageBox.warning(self, "Aviso", "Nenhum arquivo selecionado!")
            return
        
        self.log("🔍 Iniciando verificação de integridade...")
        
        all_valid = True
        for file_type, file_path in selected_files:
            try:
                if FirmwareParser.verify_firmware_integrity(file_path):
                    self.log(f"✅ {file_type}: Arquivo válido")
                else:
                    self.log(f"❌ {file_type}: Falha na verificação")
                    all_valid = False
            except Exception as e:
                self.log(f"❌ {file_type}: Erro - {str(e)}")
                all_valid = False
        
        if all_valid:
            self.log("✅ Todos os arquivos são válidos!")
            QMessageBox.information(self, "Verificação", "✅ Todos os arquivos são válidos!")
        else:
            self.log("⚠️ Alguns arquivos falharam na verificação")
            QMessageBox.warning(self, "Verificação", "⚠️ Alguns arquivos falharam na verificação")
    
    def reset_form(self):
        """Limpa o formulário com animação"""
        # Animação de limpeza
        for file_edit in self.files.values():
            file_edit.clear()
        
        for checkbox in self.checkboxes.values():
            checkbox.setChecked(False)
        
        self.progress_bar.setVisible(False)
        self.progress_details.setVisible(False)
        
        self.log("🧹 Formulário limpo")
    
    def start_flash(self):
        """Inicia o processo de flash"""
        # Coleta arquivos selecionados
        selected_files = {}
        for file_type, file_edit in self.files.items():
            if self.checkboxes[file_type].isChecked() and file_edit.text():
                selected_files[file_type] = file_edit.text()
        
        if not selected_files:
            QMessageBox.warning(self, "Aviso", "Selecione pelo menos um arquivo!")
            return
        
        if not self.current_device:
            QMessageBox.warning(self, "Aviso", "Nenhum dispositivo conectado!")
            return
        
        # Confirmação com design moderno
        file_list = "<br>".join([f"• <b>{ft}:</b> {os.path.basename(fp)}" for ft, fp in selected_files.items()])
        
        reply = QMessageBox.question(
            self, 
            "🚀 Confirmar Flash",
            f"""
            <h2>⚠️ Confirmação de Flash</h2>
            <p><b>Dispositivo:</b> {self.current_device.model or 'Samsung Device'}</p>
            <p><b>Arquivos selecionados:</b></p>
            {file_list}
            <br>
            <p style="color: red;"><b>⚠️ ATENÇÃO:</b> Esta operação irá sobrescrever o firmware!</p>
            <p>• Pode anular a garantia do dispositivo</p>
            <p>• Mantenha o dispositivo conectado durante todo o processo</p>
            <br>
            <p>Deseja continuar?</p>
            """,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Inicia flash
        self.is_flashing = True
        self.start_button.setEnabled(False)
        self.start_button.setText("🔥 Fazendo Flash...")
        self.progress_bar.setVisible(True)
        self.progress_details.setVisible(True)
        self.progress_bar.setValue(0)
        
        options = {
            'auto_reboot': self.auto_reboot_cb.isChecked(),
            'verify_integrity': self.verify_files_cb.isChecked(),
            'backup_before_flash': self.backup_before_flash_cb.isChecked()
        }
        
        self.flash_thread = FlashThread(self.flash_engine, selected_files, options)
        self.flash_thread.progress_updated.connect(self.update_flash_progress)
        self.flash_thread.log_updated.connect(self.log)
        self.flash_thread.flash_completed.connect(self.flash_completed)
        self.flash_thread.start()
    
    def flash_completed(self, success, message):
        """Callback quando o flash é concluído"""
        self.is_flashing = False
        self.start_button.setEnabled(True)
        self.start_button.setText("🚀 Iniciar Flash")
        
        if success:
            # Animação de sucesso
            QMessageBox.information(self, "🎉 Sucesso", f"<h2>🎉 {message}</h2><p>O flash foi concluído com sucesso!</p>")
            self.log(f"🎉 {message}")
            
            # Reinicia dispositivo se solicitado
            if self.auto_reboot_cb.isChecked():
                self.log("🔄 Reiniciando dispositivo...")
                self.flash_engine.reboot_device()
        else:
            QMessageBox.critical(self, "❌ Erro", f"<h2>❌ Erro no Flash</h2><p>{message}</p>")
            self.log(f"❌ {message}")
    
    def refresh_devices(self):
        """Atualiza lista de dispositivos"""
        self.log("🔄 Atualizando lista de dispositivos...")
        # A detecção é automática via thread
    
    def clear_log(self):
        """Limpa o log"""
        self.log_text.clear()
        self.log("🧹 Log limpo")
    
    def save_log(self):
        """Salva o log em arquivo"""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar log",
            f"zodin_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Arquivos de texto (*.txt);;Todos os arquivos (*.*)"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.toPlainText())
                self.log(f"💾 Log salvo: {filename}")
            except Exception as e:
                self.log(f"❌ Erro ao salvar log: {str(e)}")
    
    def closeEvent(self, event):
        """Evento de fechamento da aplicação"""
        if self.device_thread:
            self.device_thread.stop()
            self.device_thread.wait()
        
        if self.flash_thread and self.flash_thread.isRunning():
            reply = QMessageBox.question(
                self,
                "Flash em Andamento",
                "⚠️ Uma operação de flash está em andamento!\n\n"
                "Interromper pode danificar o dispositivo.\n"
                "Deseja realmente sair?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
        
        # Desconecta dispositivo
        if self.flash_engine:
            self.flash_engine.disconnect()
        
        self.log("👋 Encerrando Zodin Flash Tool...")
        event.accept()


def main():
    """Função principal da aplicação"""
    # Parse argumentos de linha de comando
    parser = argparse.ArgumentParser(
        description="Zodin Flash Tool - A Ferramenta Definitiva de Flash Samsung para Linux",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python3 zodin_flash_tool.py                    # Inicia interface gráfica
  python3 zodin_flash_tool.py --help             # Mostra esta ajuda
  python3 zodin_flash_tool.py --version          # Mostra versão
  python3 zodin_flash_tool.py --check-devices    # Verifica dispositivos conectados
  python3 zodin_flash_tool.py --headless         # Modo sem interface gráfica
        """
    )
    
    parser.add_argument('--version', action='version', version='Zodin Flash Tool v1.1.0')
    parser.add_argument('--check-devices', action='store_true', 
                       help='Verifica dispositivos Samsung conectados')
    parser.add_argument('--headless', action='store_true',
                       help='Executa em modo headless (sem interface gráfica)')
    parser.add_argument('--debug', action='store_true',
                       help='Ativa modo debug com logs detalhados')
    
    args = parser.parse_args()
    
    # Se argumentos específicos foram passados, executa e sai
    if args.check_devices:
        print("🔍 Verificando dispositivos Samsung conectados...")
        try:
            from samsung_protocol import ZodinFlashEngine
            engine = ZodinFlashEngine()
            devices = engine.detect_devices()
            if devices:
                print(f"✅ Encontrados {len(devices)} dispositivo(s):")
                for i, device in enumerate(devices, 1):
                    print(f"  {i}. {device}")
            else:
                print("❌ Nenhum dispositivo Samsung encontrado")
        except Exception as e:
            print(f"❌ Erro ao verificar dispositivos: {e}")
        return
    
    if args.headless:
        print("🖥️ Modo headless não implementado ainda")
        print("💡 Use a interface gráfica: python3 zodin_flash_tool.py")
        return
    
    # Verifica se não está em ambiente headless
    if 'DISPLAY' not in os.environ and not args.headless:
        print("❌ Ambiente sem display detectado")
        print("💡 Use: python3 zodin_flash_tool.py --headless")
        print("💡 Ou configure DISPLAY para usar interface gráfica")
        return
    
    # Inicia aplicação Qt
    app = QApplication(sys.argv)
    app.setApplicationName("Zodin Flash Tool")
    app.setApplicationVersion("1.1.0")
    app.setOrganizationName("Zodin Project")
    
    # Verifica dependências
    try:
        import usb.core
    except ImportError:
        if 'DISPLAY' in os.environ:
            QMessageBox.critical(None, "Dependência Faltando", 
                               "PyUSB não está instalado!\n\n"
                               "Instale com: pip install pyusb\n"
                               "Ou execute o script de instalação.")
        else:
            print("❌ PyUSB não está instalado!")
            print("💡 Instale com: pip install pyusb")
        sys.exit(1)
    
    # Verifica privilégios
    if os.geteuid() != 0:
        print("⚠️  Aviso: Executando sem privilégios de root.")
        print("   Pode ser necessário executar com sudo para acesso USB.")
        print("   Comando: sudo python3 zodin_flash_tool.py")
    
    try:
        # Cria e exibe a janela principal
        window = ZodinFlashTool()
        window.show()
        
        # Log inicial
        window.log("🚀 Zodin Flash Tool v1.1.0 iniciado")
        window.log("✨ A ferramenta definitiva de flash Samsung para Linux")
        window.log("🔧 Implementação própria dos protocolos Samsung")
        
        sys.exit(app.exec())
    except Exception as e:
        print(f"❌ Erro ao iniciar aplicação: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

