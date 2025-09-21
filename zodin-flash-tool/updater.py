#!/usr/bin/env python3
"""
Zodin Flash Tool - Sistema de Atualização Automática
Módulo responsável por verificar e aplicar atualizações do Zodin Flash Tool
"""

import os
import sys
import json
import requests
import subprocess
import tempfile
import shutil
import zipfile
import hashlib
from pathlib import Path
from typing import Dict, Optional, Tuple, List
from datetime import datetime, timedelta
import threading
import time

# Importações Qt condicionais
try:
    from PyQt6.QtCore import QThread, pyqtSignal, QTimer, Qt
    from PyQt6.QtWidgets import QMessageBox, QProgressDialog, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit
    QT_AVAILABLE = True
except ImportError:
    # Fallback para quando Qt não está disponível
    QT_AVAILABLE = False
    QThread = object
    pyqtSignal = lambda *args: None
    QTimer = None
    Qt = None


class UpdateInfo:
    """Informações sobre uma atualização disponível"""
    def __init__(self, version: str, download_url: str, changelog: str, 
                 release_date: str, size: int = 0, is_critical: bool = False):
        self.version = version
        self.download_url = download_url
        self.changelog = changelog
        self.release_date = release_date
        self.size = size
        self.is_critical = is_critical


class UpdateChecker(QThread):
    """Thread para verificação de atualizações"""
    update_available = pyqtSignal(object)  # UpdateInfo
    no_update = pyqtSignal()
    error_occurred = pyqtSignal(str)
    
    def __init__(self, current_version: str = "1.0.0"):
        super().__init__()
        self.current_version = current_version
        self.github_api_url = "https://api.github.com/repos/Llucs/ZodinLinux/releases/latest"
        self.check_interval = 24 * 60 * 60  # 24 horas em segundos
    
    def run(self):
        """Executa verificação de atualização"""
        try:
            response = requests.get(self.github_api_url, timeout=10)
            response.raise_for_status()
            
            release_data = response.json()
            latest_version = release_data['tag_name'].lstrip('v')
            
            if self._is_newer_version(latest_version, self.current_version):
                # Encontra o asset do Zodin Flash Tool
                download_url = None
                file_size = 0
                
                for asset in release_data.get('assets', []):
                    if 'zodin-flash-tool' in asset['name'].lower():
                        download_url = asset['download_url']
                        file_size = asset['size']
                        break
                
                if not download_url:
                    # Se não há asset específico, usa o zipball
                    download_url = release_data['zipball_url']
                
                update_info = UpdateInfo(
                    version=latest_version,
                    download_url=download_url,
                    changelog=release_data.get('body', 'Sem informações de changelog'),
                    release_date=release_data['published_at'],
                    size=file_size,
                    is_critical=self._is_critical_update(release_data.get('body', ''))
                )
                
                self.update_available.emit(update_info)
            else:
                self.no_update.emit()
                
        except Exception as e:
            self.error_occurred.emit(f"Erro ao verificar atualizações: {str(e)}")
    
    def _is_newer_version(self, latest: str, current: str) -> bool:
        """Compara versões para determinar se há atualização"""
        try:
            latest_parts = [int(x) for x in latest.split('.')]
            current_parts = [int(x) for x in current.split('.')]
            
            # Normaliza para mesmo tamanho
            max_len = max(len(latest_parts), len(current_parts))
            latest_parts.extend([0] * (max_len - len(latest_parts)))
            current_parts.extend([0] * (max_len - len(current_parts)))
            
            return latest_parts > current_parts
        except:
            return False
    
    def _is_critical_update(self, changelog: str) -> bool:
        """Determina se é uma atualização crítica baseada no changelog"""
        critical_keywords = ['critical', 'security', 'urgent', 'hotfix', 'crítico', 'segurança']
        changelog_lower = changelog.lower()
        return any(keyword in changelog_lower for keyword in critical_keywords)


class UpdateDownloader(QThread):
    """Thread para download de atualizações"""
    progress_updated = pyqtSignal(int)
    download_completed = pyqtSignal(str)  # caminho do arquivo baixado
    download_failed = pyqtSignal(str)
    
    def __init__(self, update_info: UpdateInfo):
        super().__init__()
        self.update_info = update_info
        self.download_path = None
    
    def run(self):
        """Executa o download da atualização"""
        try:
            # Cria diretório temporário
            temp_dir = tempfile.mkdtemp(prefix='zodin_update_')
            filename = f"zodin-flash-tool-{self.update_info.version}.zip"
            self.download_path = os.path.join(temp_dir, filename)
            
            # Download com progresso
            response = requests.get(self.update_info.download_url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(self.download_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if total_size > 0:
                            progress = int((downloaded / total_size) * 100)
                            self.progress_updated.emit(progress)
            
            self.download_completed.emit(self.download_path)
            
        except Exception as e:
            self.download_failed.emit(f"Erro no download: {str(e)}")


class UpdateInstaller:
    """Classe para instalação de atualizações"""
    
    def __init__(self, app_dir: str):
        self.app_dir = Path(app_dir)
        self.backup_dir = self.app_dir.parent / "zodin-backup"
    
    def install_update(self, update_file: str) -> Tuple[bool, str]:
        """Instala a atualização baixada"""
        try:
            # Cria backup da versão atual
            if not self._create_backup():
                return False, "Falha ao criar backup da versão atual"
            
            # Extrai nova versão
            if not self._extract_update(update_file):
                return False, "Falha ao extrair nova versão"
            
            # Verifica integridade
            if not self._verify_installation():
                # Restaura backup em caso de falha
                self._restore_backup()
                return False, "Falha na verificação da nova versão"
            
            # Remove backup antigo se tudo deu certo
            self._cleanup_backup()
            
            return True, "Atualização instalada com sucesso!"
            
        except Exception as e:
            # Restaura backup em caso de erro
            self._restore_backup()
            return False, f"Erro durante instalação: {str(e)}"
    
    def _create_backup(self) -> bool:
        """Cria backup da versão atual"""
        try:
            if self.backup_dir.exists():
                shutil.rmtree(self.backup_dir)
            
            shutil.copytree(self.app_dir, self.backup_dir)
            return True
        except Exception:
            return False
    
    def _extract_update(self, update_file: str) -> bool:
        """Extrai arquivos da atualização"""
        try:
            with zipfile.ZipFile(update_file, 'r') as zip_ref:
                # Extrai para diretório temporário primeiro
                temp_extract = tempfile.mkdtemp(prefix='zodin_extract_')
                zip_ref.extractall(temp_extract)
                
                # Encontra o diretório do zodin-flash-tool
                zodin_dir = None
                for root, dirs, files in os.walk(temp_extract):
                    if 'zodin_flash_tool.py' in files:
                        zodin_dir = root
                        break
                
                if not zodin_dir:
                    return False
                
                # Copia arquivos para o diretório de instalação
                for item in os.listdir(zodin_dir):
                    src = os.path.join(zodin_dir, item)
                    dst = self.app_dir / item
                    
                    if os.path.isfile(src):
                        shutil.copy2(src, dst)
                    elif os.path.isdir(src):
                        if dst.exists():
                            shutil.rmtree(dst)
                        shutil.copytree(src, dst)
                
                # Limpa diretório temporário
                shutil.rmtree(temp_extract)
                return True
                
        except Exception:
            return False
    
    def _verify_installation(self) -> bool:
        """Verifica se a instalação foi bem-sucedida"""
        try:
            # Verifica se arquivos principais existem
            required_files = ['zodin_flash_tool.py', 'samsung_protocol.py']
            for file in required_files:
                if not (self.app_dir / file).exists():
                    return False
            
            # Tenta importar o módulo principal (verificação básica)
            sys.path.insert(0, str(self.app_dir))
            try:
                import zodin_flash_tool
                return True
            except ImportError:
                return False
            finally:
                sys.path.remove(str(self.app_dir))
                
        except Exception:
            return False
    
    def _restore_backup(self) -> bool:
        """Restaura backup em caso de falha"""
        try:
            if not self.backup_dir.exists():
                return False
            
            # Remove versão com falha
            if self.app_dir.exists():
                shutil.rmtree(self.app_dir)
            
            # Restaura backup
            shutil.copytree(self.backup_dir, self.app_dir)
            return True
        except Exception:
            return False
    
    def _cleanup_backup(self):
        """Remove backup após instalação bem-sucedida"""
        try:
            if self.backup_dir.exists():
                shutil.rmtree(self.backup_dir)
        except Exception:
            pass


class UpdateDialog(QDialog):
    """Diálogo para mostrar informações de atualização"""
    
    def __init__(self, update_info: UpdateInfo, parent=None):
        super().__init__(parent)
        self.update_info = update_info
        self.result_action = None
        self.setup_ui()
    
    def setup_ui(self):
        """Configura a interface do diálogo"""
        self.setWindowTitle("🔄 Atualização Disponível - Zodin Flash Tool")
        self.setFixedSize(600, 500)
        
        layout = QVBoxLayout(self)
        
        # Título
        title = QLabel(f"🎉 Nova versão disponível: v{self.update_info.version}")
        title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #6c5ce7;
                margin: 15px;
                text-align: center;
            }
        """)
        layout.addWidget(title)
        
        # Informações da versão
        info_layout = QVBoxLayout()
        
        date_label = QLabel(f"📅 Data de lançamento: {self.update_info.release_date[:10]}")
        date_label.setStyleSheet("font-size: 14px; margin: 5px;")
        info_layout.addWidget(date_label)
        
        if self.update_info.size > 0:
            size_mb = self.update_info.size / (1024 * 1024)
            size_label = QLabel(f"📦 Tamanho: {size_mb:.1f} MB")
            size_label.setStyleSheet("font-size: 14px; margin: 5px;")
            info_layout.addWidget(size_label)
        
        if self.update_info.is_critical:
            critical_label = QLabel("⚠️ ATUALIZAÇÃO CRÍTICA - Recomendada instalação imediata")
            critical_label.setStyleSheet("""
                QLabel {
                    font-size: 14px;
                    font-weight: bold;
                    color: #e74c3c;
                    margin: 5px;
                    padding: 10px;
                    background-color: #ffeaa7;
                    border-radius: 5px;
                }
            """)
            info_layout.addWidget(critical_label)
        
        layout.addLayout(info_layout)
        
        # Changelog
        changelog_label = QLabel("📋 Novidades desta versão:")
        changelog_label.setStyleSheet("font-size: 16px; font-weight: bold; margin: 15px 5px 5px 5px;")
        layout.addWidget(changelog_label)
        
        changelog_text = QTextEdit()
        changelog_text.setPlainText(self.update_info.changelog)
        changelog_text.setReadOnly(True)
        changelog_text.setMaximumHeight(200)
        changelog_text.setStyleSheet("""
            QTextEdit {
                border: 2px solid #ddd;
                border-radius: 8px;
                padding: 10px;
                font-size: 13px;
                background-color: #f8f9fa;
            }
        """)
        layout.addWidget(changelog_text)
        
        # Botões
        buttons_layout = QHBoxLayout()
        
        later_button = QPushButton("⏰ Lembrar Depois")
        later_button.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 20px;
                font-size: 14px;
                font-weight: bold;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        later_button.clicked.connect(lambda: self.set_result('later'))
        
        skip_button = QPushButton("❌ Pular Versão")
        skip_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 20px;
                font-size: 14px;
                font-weight: bold;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        skip_button.clicked.connect(lambda: self.set_result('skip'))
        
        update_button = QPushButton("🚀 Atualizar Agora")
        update_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #6c5ce7, stop:1 #5f3dc4);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 20px;
                font-size: 14px;
                font-weight: bold;
                min-width: 120px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #7d6ef0, stop:1 #6c5ce7);
            }
        """)
        update_button.clicked.connect(lambda: self.set_result('update'))
        
        buttons_layout.addWidget(later_button)
        buttons_layout.addWidget(skip_button)
        buttons_layout.addWidget(update_button)
        
        layout.addLayout(buttons_layout)
    
    def set_result(self, action: str):
        """Define a ação escolhida pelo usuário"""
        self.result_action = action
        self.accept()


class ZodinUpdater:
    """Classe principal do sistema de atualização"""
    
    def __init__(self, parent_widget=None, current_version: str = "1.0.0"):
        self.parent = parent_widget
        self.current_version = current_version
        self.app_dir = self._get_app_directory()
        self.config_dir = Path.home() / ".config" / "zodin-flash-tool"
        self.config_file = self.config_dir / "update_config.json"
        
        # Cria diretório de configuração se não existir
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Carrega configurações
        self.config = self._load_config()
        
        # Componentes
        self.checker = None
        self.downloader = None
        self.installer = UpdateInstaller(str(self.app_dir))
    
    def _get_app_directory(self) -> Path:
        """Obtém o diretório da aplicação"""
        if getattr(sys, 'frozen', False):
            # Aplicação empacotada
            return Path(sys.executable).parent
        else:
            # Executando do código fonte
            return Path(__file__).parent
    
    def _load_config(self) -> Dict:
        """Carrega configurações de atualização"""
        default_config = {
            "auto_check": True,
            "check_interval": 24,  # horas
            "last_check": None,
            "skipped_versions": [],
            "notify_critical_only": False
        }
        
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    # Mescla com configurações padrão
                    default_config.update(config)
            return default_config
        except Exception:
            return default_config
    
    def _save_config(self):
        """Salva configurações de atualização"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception:
            pass
    
    def should_check_for_updates(self) -> bool:
        """Verifica se deve procurar por atualizações"""
        if not self.config["auto_check"]:
            return False
        
        last_check = self.config.get("last_check")
        if not last_check:
            return True
        
        try:
            last_check_date = datetime.fromisoformat(last_check)
            check_interval = timedelta(hours=self.config["check_interval"])
            return datetime.now() - last_check_date > check_interval
        except Exception:
            return True
    
    def check_for_updates(self, manual: bool = False):
        """Inicia verificação de atualizações"""
        if not manual and not self.should_check_for_updates():
            return
        
        self.checker = UpdateChecker(self.current_version)
        self.checker.update_available.connect(self._on_update_available)
        self.checker.no_update.connect(self._on_no_update)
        self.checker.error_occurred.connect(self._on_update_error)
        self.checker.start()
        
        # Atualiza timestamp da última verificação
        self.config["last_check"] = datetime.now().isoformat()
        self._save_config()
    
    def _on_update_available(self, update_info: UpdateInfo):
        """Callback quando atualização está disponível"""
        # Verifica se versão foi pulada
        if update_info.version in self.config["skipped_versions"]:
            return
        
        # Verifica se deve notificar apenas atualizações críticas
        if self.config["notify_critical_only"] and not update_info.is_critical:
            return
        
        # Mostra diálogo de atualização
        dialog = UpdateDialog(update_info, self.parent)
        dialog.exec()
        
        if dialog.result_action == 'update':
            self._start_update_process(update_info)
        elif dialog.result_action == 'skip':
            self.config["skipped_versions"].append(update_info.version)
            self._save_config()
        # 'later' não faz nada, vai verificar novamente no próximo intervalo
    
    def _on_no_update(self):
        """Callback quando não há atualizações"""
        # Pode mostrar notificação se foi verificação manual
        pass
    
    def _on_update_error(self, error_message: str):
        """Callback quando há erro na verificação"""
        if self.parent and QT_AVAILABLE:
            QMessageBox.warning(
                self.parent,
                "Erro na Verificação",
                f"Não foi possível verificar atualizações:\n{error_message}"
            )
        else:
            print(f"❌ Erro na verificação de atualizações: {error_message}")
    
    def _start_update_process(self, update_info: UpdateInfo):
        """Inicia processo de atualização"""
        # Mostra diálogo de progresso
        progress_dialog = QProgressDialog(
            "Baixando atualização...",
            "Cancelar",
            0, 100,
            self.parent
        )
        progress_dialog.setWindowTitle("Atualizando Zodin Flash Tool")
        progress_dialog.setWindowModality(Qt.WindowModal if QT_AVAILABLE else 0)
        progress_dialog.show()
        
        # Inicia download
        self.downloader = UpdateDownloader(update_info)
        self.downloader.progress_updated.connect(progress_dialog.setValue)
        self.downloader.download_completed.connect(
            lambda path: self._on_download_completed(path, progress_dialog)
        )
        self.downloader.download_failed.connect(
            lambda error: self._on_download_failed(error, progress_dialog)
        )
        
        progress_dialog.canceled.connect(self.downloader.terminate)
        self.downloader.start()
    
    def _on_download_completed(self, file_path: str, progress_dialog: QProgressDialog):
        """Callback quando download é concluído"""
        progress_dialog.close()
        
        # Confirma instalação
        if QT_AVAILABLE:
            reply = QMessageBox.question(
                self.parent,
                "Instalar Atualização",
                "Download concluído!\n\n"
                "Deseja instalar a atualização agora?\n"
                "O Zodin Flash Tool será reiniciado após a instalação.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self._install_update(file_path)
        else:
            # Fallback para ambiente sem Qt
            print("Download concluído! Instale manualmente ou use interface gráfica.")
    
    def _on_download_failed(self, error_message: str, progress_dialog: QProgressDialog):
        """Callback quando download falha"""
        progress_dialog.close()
        if QT_AVAILABLE:
            QMessageBox.critical(
                self.parent,
                "Erro no Download",
                f"Falha ao baixar atualização:\n{error_message}"
            )
        else:
            print(f"❌ Falha ao baixar atualização: {error_message}")
    
    def _install_update(self, update_file: str):
        """Instala a atualização"""
        try:
            success, message = self.installer.install_update(update_file)
            
            if success:
                if QT_AVAILABLE:
                    QMessageBox.information(
                        self.parent,
                        "Atualização Concluída",
                        f"{message}\n\n"
                        "O Zodin Flash Tool será reiniciado agora."
                    )
                else:
                    print(f"✅ {message}")
                    print("🔄 Reinicie o Zodin Flash Tool manualmente")
                
                # Reinicia aplicação
                self._restart_application()
            else:
                if QT_AVAILABLE:
                    QMessageBox.critical(
                        self.parent,
                        "Erro na Instalação",
                        f"Falha ao instalar atualização:\n{message}"
                    )
                else:
                    print(f"❌ Falha ao instalar atualização: {message}")
        
        except Exception as e:
            if QT_AVAILABLE:
                QMessageBox.critical(
                    self.parent,
                    "Erro na Instalação",
                    f"Erro inesperado durante instalação:\n{str(e)}"
                )
            else:
                print(f"❌ Erro inesperado durante instalação: {str(e)}")
        
        finally:
            # Remove arquivo temporário
            try:
                os.remove(update_file)
            except Exception:
                pass
    
    def _restart_application(self):
        """Reinicia a aplicação"""
        try:
            # Obtém argumentos da linha de comando
            args = sys.argv[:]
            
            # Adiciona interpretador Python se necessário
            if not getattr(sys, 'frozen', False):
                args.insert(0, sys.executable)
            
            # Reinicia
            os.execv(args[0], args)
        except Exception:
            # Se falhar, apenas fecha a aplicação
            sys.exit(0)
    
    def get_update_settings(self) -> Dict:
        """Retorna configurações atuais de atualização"""
        return self.config.copy()
    
    def update_settings(self, settings: Dict):
        """Atualiza configurações de atualização"""
        self.config.update(settings)
        self._save_config()
    
    def manual_check(self):
        """Força verificação manual de atualizações"""
        self.check_for_updates(manual=True)

