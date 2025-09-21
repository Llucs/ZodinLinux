#!/usr/bin/env python3
"""
Zodin Flash Tool - Flash Engines Module
Integra múltiplas ferramentas de flash Samsung em uma única interface
"""

import os
import subprocess
import tempfile
import tarfile
import contextlib
import hashlib
import json
import shutil
from pathlib import Path
from abc import ABC, abstractmethod
from typing import List, Dict, Tuple, Optional, Callable
from dataclasses import dataclass
from enum import Enum


class FlashEngine(Enum):
    """Tipos de engines de flash disponíveis"""
    HEIMDALL = "heimdall"
    THOR = "thor"
    ODIN4 = "odin4"
    AUTO = "auto"


@dataclass
class FlashFile:
    """Representa um arquivo de firmware"""
    file_type: str  # BL, AP, CP, CSC, USERDATA
    file_path: str
    partition_name: Optional[str] = None
    size: Optional[int] = None
    checksum: Optional[str] = None


@dataclass
class FlashOptions:
    """Opções de flash"""
    auto_reboot: bool = True
    repartition: bool = False
    nand_erase: bool = False
    bootloader_update: bool = False
    efs_clear: bool = False
    engine: FlashEngine = FlashEngine.AUTO
    device_path: Optional[str] = None


class FlashEngineBase(ABC):
    """Classe base para engines de flash"""
    
    def __init__(self, progress_callback: Optional[Callable] = None, 
                 log_callback: Optional[Callable] = None):
        self.progress_callback = progress_callback
        self.log_callback = log_callback
    
    def log(self, message: str):
        """Envia mensagem para o log"""
        if self.log_callback:
            self.log_callback(message)
    
    def update_progress(self, percentage: int):
        """Atualiza o progresso"""
        if self.progress_callback:
            self.progress_callback(percentage)
    
    @abstractmethod
    def is_available(self) -> bool:
        """Verifica se a engine está disponível no sistema"""
        pass
    
    @abstractmethod
    def detect_device(self) -> Tuple[bool, str]:
        """Detecta dispositivo Samsung em modo download"""
        pass
    
    @abstractmethod
    def get_device_info(self) -> Dict[str, str]:
        """Obtém informações do dispositivo"""
        pass
    
    @abstractmethod
    def flash_firmware(self, files: List[FlashFile], options: FlashOptions) -> bool:
        """Executa o flash do firmware"""
        pass
    
    @abstractmethod
    def get_pit_info(self) -> Dict[str, any]:
        """Obtém informações da tabela de partições (PIT)"""
        pass


class HeimdallEngine(FlashEngineBase):
    """Engine baseada no Heimdall"""
    
    def is_available(self) -> bool:
        try:
            result = subprocess.run(['heimdall', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def detect_device(self) -> Tuple[bool, str]:
        try:
            # Verifica USB Samsung
            lsusb = subprocess.run(['lsusb'], capture_output=True, text=True, timeout=5)
            if not ("Samsung" in lsusb.stdout or "04e8" in lsusb.stdout):
                return False, "Nenhum dispositivo Samsung USB detectado"
            
            # Verifica modo download
            result = subprocess.run(['heimdall', 'detect'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return True, "Dispositivo Samsung - Modo Download"
            else:
                return False, "Samsung USB - Não está em Modo Download"
                
        except Exception as e:
            return False, f"Erro na detecção: {str(e)}"
    
    def get_device_info(self) -> Dict[str, str]:
        info = {}
        try:
            # Tenta obter informações do PIT
            result = subprocess.run(['heimdall', 'print-pit'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                info['pit_available'] = 'Sim'
                # Parse básico do PIT
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'Entry Count:' in line:
                        info['partition_count'] = line.split(':')[1].strip()
                    elif 'Unknown 1:' in line:
                        info['unknown1'] = line.split(':')[1].strip()
            else:
                info['pit_available'] = 'Não'
        except Exception as e:
            info['error'] = str(e)
        
        return info
    
    def get_pit_info(self) -> Dict[str, any]:
        try:
            result = subprocess.run(['heimdall', 'print-pit'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return {'success': True, 'output': result.stdout}
            else:
                return {'success': False, 'error': result.stderr}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def flash_firmware(self, files: List[FlashFile], options: FlashOptions) -> bool:
        try:
            self.log("Iniciando flash com Heimdall...")
            
            # Constrói comando
            cmd = ['heimdall', 'flash']
            
            if options.repartition:
                cmd.append('--repartition')
            
            if not options.auto_reboot:
                cmd.append('--no-reboot')
            
            # Processa arquivos
            for flash_file in files:
                self.log(f"Processando {flash_file.file_type}: {os.path.basename(flash_file.file_path)}")
                
                actual_path = flash_file.file_path
                if actual_path.endswith('.md5'):
                    actual_path = actual_path[:-4]
                
                if actual_path.endswith('.tar'):
                    self._process_tar_file(cmd, actual_path, flash_file.file_type)
                else:
                    self._process_single_file(cmd, actual_path, flash_file.file_type)
            
            cmd.append('--verbose')
            self.log(f"Executando: {' '.join(cmd)}")
            
            # Executa comando
            return self._execute_flash_command(cmd)
            
        except Exception as e:
            self.log(f"Erro no flash Heimdall: {str(e)}")
            return False
    
    def _process_tar_file(self, cmd: List[str], tar_path: str, file_type: str):
        """Processa arquivo TAR"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with tarfile.open(tar_path) as tar:
                tar.extractall(temp_dir)
            
            for file_name in os.listdir(temp_dir):
                full_path = os.path.join(temp_dir, file_name)
                
                # Descomprime LZ4 se necessário
                if file_name.endswith('.lz4'):
                    decompressed = file_name[:-4]
                    decompressed_path = os.path.join(temp_dir, decompressed)
                    try:
                        subprocess.check_call(['lz4', '-d', full_path, decompressed_path])
                        os.remove(full_path)
                        file_name = decompressed
                        full_path = decompressed_path
                        self.log(f"Descomprimido {file_name}")
                    except (FileNotFoundError, subprocess.CalledProcessError) as e:
                        self.log(f"Erro ao descomprimir {file_name}: {str(e)}")
                        continue
                
                if file_name.endswith(('.bin', '.img', '.mbn')):
                    partition = os.path.splitext(file_name)[0].upper()
                    cmd.extend([f'--{partition}', full_path])
                    self.log(f"Adicionado {file_name} à partição {partition}")
    
    def _process_single_file(self, cmd: List[str], file_path: str, file_type: str):
        """Processa arquivo único"""
        if file_path.endswith(('.bin', '.img', '.mbn')):
            partition = os.path.splitext(os.path.basename(file_path))[0].upper()
            cmd.extend([f'--{partition}', file_path])
            self.log(f"Adicionado {os.path.basename(file_path)} à partição {partition}")
    
    def _execute_flash_command(self, cmd: List[str]) -> bool:
        """Executa comando de flash"""
        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                     universal_newlines=True, bufsize=1)
            
            progress = 0
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    line = output.strip()
                    self.log(line)
                    
                    # Simula progresso
                    if any(keyword in line.lower() for keyword in ['uploading', 'sending', 'writing']):
                        progress = min(progress + 5, 95)
                        self.update_progress(progress)
            
            return_code = process.poll()
            if return_code == 0:
                self.update_progress(100)
                return True
            else:
                return False
                
        except Exception as e:
            self.log(f"Erro na execução: {str(e)}")
            return False


class ThorEngine(FlashEngineBase):
    """Engine baseada no Thor"""
    
    def is_available(self) -> bool:
        try:
            result = subprocess.run(['thor', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def detect_device(self) -> Tuple[bool, str]:
        try:
            result = subprocess.run(['thor', '--detect'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and "Device detected" in result.stdout:
                return True, "Dispositivo Samsung - Modo Download (Thor)"
            else:
                return False, "Dispositivo não detectado pelo Thor"
        except Exception as e:
            return False, f"Erro na detecção Thor: {str(e)}"
    
    def get_device_info(self) -> Dict[str, str]:
        info = {}
        try:
            result = subprocess.run(['thor', '--info'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                # Parse das informações do Thor
                lines = result.stdout.split('\n')
                for line in lines:
                    if ':' in line:
                        key, value = line.split(':', 1)
                        info[key.strip()] = value.strip()
        except Exception as e:
            info['error'] = str(e)
        
        return info
    
    def get_pit_info(self) -> Dict[str, any]:
        try:
            result = subprocess.run(['thor', '--print-pit'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return {'success': True, 'output': result.stdout}
            else:
                return {'success': False, 'error': result.stderr}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def flash_firmware(self, files: List[FlashFile], options: FlashOptions) -> bool:
        try:
            self.log("Iniciando flash com Thor...")
            
            # Thor usa arquivos TAR diretamente
            tar_files = []
            for flash_file in files:
                if flash_file.file_path.endswith(('.tar', '.tar.md5')):
                    tar_files.append(flash_file.file_path)
            
            if not tar_files:
                self.log("Thor requer arquivos TAR")
                return False
            
            # Comando Thor
            cmd = ['thor', '--flash']
            
            for tar_file in tar_files:
                cmd.extend(['--file', tar_file])
            
            if options.repartition:
                cmd.append('--repartition')
            
            if not options.auto_reboot:
                cmd.append('--no-reboot')
            
            self.log(f"Executando: {' '.join(cmd)}")
            
            return self._execute_flash_command(cmd)
            
        except Exception as e:
            self.log(f"Erro no flash Thor: {str(e)}")
            return False
    
    def _execute_flash_command(self, cmd: List[str]) -> bool:
        """Executa comando de flash Thor"""
        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                     universal_newlines=True, bufsize=1)
            
            progress = 0
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    line = output.strip()
                    self.log(line)
                    
                    # Parse do progresso do Thor
                    if 'Progress:' in line:
                        try:
                            progress_str = line.split('Progress:')[1].strip().replace('%', '')
                            progress = int(float(progress_str))
                            self.update_progress(progress)
                        except:
                            pass
            
            return_code = process.poll()
            if return_code == 0:
                self.update_progress(100)
                return True
            else:
                return False
                
        except Exception as e:
            self.log(f"Erro na execução Thor: {str(e)}")
            return False


class Odin4Engine(FlashEngineBase):
    """Engine baseada no Odin4"""
    
    def is_available(self) -> bool:
        try:
            result = subprocess.run(['odin4', '-v'], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def detect_device(self) -> Tuple[bool, str]:
        try:
            result = subprocess.run(['odin4', '-l'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and result.stdout.strip():
                return True, "Dispositivo Samsung - Modo Download (Odin4)"
            else:
                return False, "Dispositivo não detectado pelo Odin4"
        except Exception as e:
            return False, f"Erro na detecção Odin4: {str(e)}"
    
    def get_device_info(self) -> Dict[str, str]:
        info = {}
        try:
            # Lista dispositivos
            result = subprocess.run(['odin4', '-l'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                devices = result.stdout.strip().split('\n')
                info['devices'] = str(len(devices))
                if devices:
                    info['device_path'] = devices[0]
        except Exception as e:
            info['error'] = str(e)
        
        return info
    
    def get_pit_info(self) -> Dict[str, any]:
        # Odin4 não tem comando direto para PIT, mas pode ser implementado
        return {'success': False, 'error': 'PIT info não disponível no Odin4'}
    
    def flash_firmware(self, files: List[FlashFile], options: FlashOptions) -> bool:
        try:
            self.log("Iniciando flash com Odin4...")
            
            cmd = ['odin4']
            
            # Mapeia tipos de arquivo para parâmetros Odin4
            file_map = {
                'BL': '-b',
                'AP': '-a', 
                'CP': '-c',
                'CSC': '-s',
                'USERDATA': '-u'
            }
            
            for flash_file in files:
                if flash_file.file_type in file_map:
                    cmd.extend([file_map[flash_file.file_type], flash_file.file_path])
            
            if options.nand_erase:
                cmd.append('-e')
            
            if not options.auto_reboot:
                cmd.append('--no-reboot')
            
            if options.device_path:
                cmd.extend(['-d', options.device_path])
            
            self.log(f"Executando: {' '.join(cmd)}")
            
            return self._execute_flash_command(cmd)
            
        except Exception as e:
            self.log(f"Erro no flash Odin4: {str(e)}")
            return False
    
    def _execute_flash_command(self, cmd: List[str]) -> bool:
        """Executa comando de flash Odin4"""
        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                     universal_newlines=True, bufsize=1)
            
            progress = 0
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    line = output.strip()
                    self.log(line)
                    
                    # Parse do progresso do Odin4
                    if any(keyword in line.lower() for keyword in ['downloading', 'flashing']):
                        progress = min(progress + 10, 95)
                        self.update_progress(progress)
            
            return_code = process.poll()
            if return_code == 0:
                self.update_progress(100)
                return True
            else:
                return False
                
        except Exception as e:
            self.log(f"Erro na execução Odin4: {str(e)}")
            return False


class FlashEngineManager:
    """Gerenciador de engines de flash"""
    
    def __init__(self, progress_callback: Optional[Callable] = None, 
                 log_callback: Optional[Callable] = None):
        self.progress_callback = progress_callback
        self.log_callback = log_callback
        
        # Inicializa engines
        self.engines = {
            FlashEngine.HEIMDALL: HeimdallEngine(progress_callback, log_callback),
            FlashEngine.THOR: ThorEngine(progress_callback, log_callback),
            FlashEngine.ODIN4: Odin4Engine(progress_callback, log_callback)
        }
    
    def get_available_engines(self) -> List[FlashEngine]:
        """Retorna lista de engines disponíveis"""
        available = []
        for engine_type, engine in self.engines.items():
            if engine.is_available():
                available.append(engine_type)
        return available
    
    def get_best_engine(self) -> Optional[FlashEngine]:
        """Retorna a melhor engine disponível"""
        available = self.get_available_engines()
        
        # Prioridade: Thor > Odin4 > Heimdall
        priority = [FlashEngine.THOR, FlashEngine.ODIN4, FlashEngine.HEIMDALL]
        
        for engine in priority:
            if engine in available:
                return engine
        
        return None
    
    def detect_device(self, engine_type: FlashEngine = FlashEngine.AUTO) -> Tuple[bool, str, Optional[FlashEngine]]:
        """Detecta dispositivo usando engine especificada ou automática"""
        if engine_type == FlashEngine.AUTO:
            # Tenta todas as engines disponíveis
            for engine_type in self.get_available_engines():
                engine = self.engines[engine_type]
                detected, message = engine.detect_device()
                if detected:
                    return True, message, engine_type
            return False, "Nenhum dispositivo detectado", None
        else:
            if engine_type in self.engines:
                engine = self.engines[engine_type]
                detected, message = engine.detect_device()
                return detected, message, engine_type if detected else None
            else:
                return False, "Engine não disponível", None
    
    def get_device_info(self, engine_type: FlashEngine) -> Dict[str, str]:
        """Obtém informações do dispositivo"""
        if engine_type in self.engines:
            return self.engines[engine_type].get_device_info()
        return {}
    
    def flash_firmware(self, files: List[FlashFile], options: FlashOptions) -> bool:
        """Executa flash usando engine especificada ou automática"""
        engine_type = options.engine
        
        if engine_type == FlashEngine.AUTO:
            engine_type = self.get_best_engine()
            if not engine_type:
                if self.log_callback:
                    self.log_callback("Nenhuma engine de flash disponível")
                return False
        
        if engine_type in self.engines:
            engine = self.engines[engine_type]
            if self.log_callback:
                self.log_callback(f"Usando engine: {engine_type.value}")
            return engine.flash_firmware(files, options)
        else:
            if self.log_callback:
                self.log_callback(f"Engine {engine_type.value} não disponível")
            return False
    
    def get_pit_info(self, engine_type: FlashEngine) -> Dict[str, any]:
        """Obtém informações PIT"""
        if engine_type in self.engines:
            return self.engines[engine_type].get_pit_info()
        return {'success': False, 'error': 'Engine não disponível'}


def calculate_file_hash(file_path: str, algorithm: str = 'md5') -> str:
    """Calcula hash de um arquivo"""
    hash_obj = hashlib.new(algorithm)
    
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_obj.update(chunk)
    
    return hash_obj.hexdigest()


def verify_firmware_integrity(file_path: str) -> Dict[str, any]:
    """Verifica integridade de arquivo de firmware"""
    result = {'valid': False, 'checksums': {}}
    
    try:
        # Calcula checksums
        result['checksums']['md5'] = calculate_file_hash(file_path, 'md5')
        result['checksums']['sha256'] = calculate_file_hash(file_path, 'sha256')
        
        # Verifica se existe arquivo .md5
        md5_file = file_path + '.md5'
        if os.path.exists(md5_file):
            with open(md5_file, 'r') as f:
                expected_md5 = f.read().strip().split()[0]
                result['expected_md5'] = expected_md5
                result['valid'] = result['checksums']['md5'].lower() == expected_md5.lower()
        else:
            result['valid'] = True  # Assume válido se não há arquivo MD5
        
        result['file_size'] = os.path.getsize(file_path)
        
    except Exception as e:
        result['error'] = str(e)
    
    return result

