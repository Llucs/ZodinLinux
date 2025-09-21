#!/usr/bin/env python3
"""
Zodin Flash Tool - Samsung Protocol Implementation
Implementação própria dos protocolos Samsung baseada no conhecimento das melhores ferramentas
"""

import usb.core
import usb.util
import struct
import time
import hashlib
import os
import tarfile
import tempfile
from typing import Optional, List, Dict, Tuple, Callable
from dataclasses import dataclass
from enum import Enum
import threading


class SamsungMode(Enum):
    """Modos do dispositivo Samsung"""
    NORMAL = "normal"
    DOWNLOAD = "download"
    RECOVERY = "recovery"
    FASTBOOT = "fastboot"


class PacketType(Enum):
    """Tipos de pacotes do protocolo Samsung"""
    HANDSHAKE = 0x00
    FLASH_SET_TOTAL_BYTES = 0x01
    FLASH_SEND_DATA = 0x02
    DUMP_PART_PIT = 0x03
    DUMP_PART_NAND = 0x04
    END_SESSION = 0x05
    DEVICE_TYPE = 0x06
    PIT_FILE = 0x07
    DUMP_PART_SBOOT = 0x08


@dataclass
class SamsungDevice:
    """Informações do dispositivo Samsung"""
    vendor_id: int = 0x04e8
    product_id: int = 0x6601
    model: str = ""
    bootloader_version: str = ""
    baseband_version: str = ""
    serial_number: str = ""
    chip_id: str = ""
    mode: SamsungMode = SamsungMode.NORMAL


@dataclass
class FlashProgress:
    """Progresso do flash"""
    current_bytes: int = 0
    total_bytes: int = 0
    current_file: str = ""
    stage: str = ""
    percentage: float = 0.0


class SamsungProtocol:
    """Implementação do protocolo Samsung"""
    
    # IDs de dispositivos Samsung conhecidos
    SAMSUNG_DEVICES = {
        0x6601: "Download Mode",
        0x685d: "Download Mode (Newer)",
        0x6860: "Download Mode (S3/S4)",
        0x68c3: "Download Mode (Note)",
        0x685e: "Download Mode (Alternative)"
    }
    
    def __init__(self, progress_callback: Optional[Callable] = None,
                 log_callback: Optional[Callable] = None):
        self.device = None
        self.endpoint_out = None
        self.endpoint_in = None
        self.progress_callback = progress_callback
        self.log_callback = log_callback
        self.session_active = False
        
    def log(self, message: str):
        """Envia mensagem para callback de log"""
        if self.log_callback:
            self.log_callback(message)
    
    def update_progress(self, progress: FlashProgress):
        """Atualiza progresso"""
        if self.progress_callback:
            self.progress_callback(progress)
    
    def detect_devices(self) -> List[SamsungDevice]:
        """Detecta dispositivos Samsung conectados"""
        devices = []
        
        try:
            # Busca por dispositivos Samsung
            samsung_devices = usb.core.find(
                find_all=True,
                idVendor=0x04e8
            )
            
            for dev in samsung_devices:
                if dev.idProduct in self.SAMSUNG_DEVICES:
                    samsung_dev = SamsungDevice(
                        vendor_id=dev.idVendor,
                        product_id=dev.idProduct,
                        mode=SamsungMode.DOWNLOAD
                    )
                    
                    try:
                        # Tenta obter informações do dispositivo
                        samsung_dev.serial_number = usb.util.get_string(dev, dev.iSerialNumber) or ""
                        samsung_dev.model = usb.util.get_string(dev, dev.iProduct) or ""
                    except:
                        pass
                    
                    devices.append(samsung_dev)
                    
        except Exception as e:
            self.log(f"Erro na detecção de dispositivos: {str(e)}")
        
        return devices
    
    def connect_device(self, device: SamsungDevice) -> bool:
        """Conecta ao dispositivo Samsung"""
        try:
            # Encontra o dispositivo USB
            self.device = usb.core.find(
                idVendor=device.vendor_id,
                idProduct=device.product_id
            )
            
            if self.device is None:
                self.log("Dispositivo não encontrado")
                return False
            
            # Configura o dispositivo
            try:
                if self.device.is_kernel_driver_active(0):
                    self.device.detach_kernel_driver(0)
            except:
                pass
            
            # Define configuração
            self.device.set_configuration()
            
            # Encontra endpoints
            cfg = self.device.get_active_configuration()
            intf = cfg[(0, 0)]
            
            self.endpoint_out = usb.util.find_descriptor(
                intf,
                custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT
            )
            
            self.endpoint_in = usb.util.find_descriptor(
                intf,
                custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN
            )
            
            if self.endpoint_out is None or self.endpoint_in is None:
                self.log("Endpoints não encontrados")
                return False
            
            self.log("Dispositivo conectado com sucesso")
            return True
            
        except Exception as e:
            self.log(f"Erro ao conectar dispositivo: {str(e)}")
            return False
    
    def send_packet(self, packet_type: PacketType, data: bytes = b'') -> bool:
        """Envia pacote para o dispositivo"""
        try:
            # Constrói cabeçalho do pacote
            header = struct.pack('<II', packet_type.value, len(data))
            packet = header + data
            
            # Envia pacote
            self.endpoint_out.write(packet)
            return True
            
        except Exception as e:
            self.log(f"Erro ao enviar pacote: {str(e)}")
            return False
    
    def receive_packet(self, timeout: int = 5000) -> Tuple[Optional[PacketType], bytes]:
        """Recebe pacote do dispositivo"""
        try:
            # Recebe cabeçalho
            header_data = self.endpoint_in.read(8, timeout)
            if len(header_data) < 8:
                return None, b''
            
            packet_type_val, data_length = struct.unpack('<II', header_data)
            packet_type = PacketType(packet_type_val)
            
            # Recebe dados se houver
            data = b''
            if data_length > 0:
                data = self.endpoint_in.read(data_length, timeout)
            
            return packet_type, data
            
        except Exception as e:
            self.log(f"Erro ao receber pacote: {str(e)}")
            return None, b''
    
    def handshake(self) -> bool:
        """Realiza handshake com o dispositivo"""
        try:
            self.log("Iniciando handshake...")
            
            # Envia handshake
            if not self.send_packet(PacketType.HANDSHAKE):
                return False
            
            # Recebe resposta
            packet_type, data = self.receive_packet()
            if packet_type != PacketType.HANDSHAKE:
                self.log("Handshake falhou")
                return False
            
            self.session_active = True
            self.log("Handshake realizado com sucesso")
            return True
            
        except Exception as e:
            self.log(f"Erro no handshake: {str(e)}")
            return False
    
    def get_device_info(self) -> Dict[str, str]:
        """Obtém informações detalhadas do dispositivo"""
        info = {}
        
        try:
            if not self.session_active:
                if not self.handshake():
                    return info
            
            # Solicita informações do dispositivo
            if self.send_packet(PacketType.DEVICE_TYPE):
                packet_type, data = self.receive_packet()
                if packet_type == PacketType.DEVICE_TYPE and data:
                    # Parse das informações (formato específico Samsung)
                    if len(data) >= 4:
                        device_type = struct.unpack('<I', data[:4])[0]
                        info['device_type'] = f"0x{device_type:08x}"
                    
                    if len(data) >= 8:
                        bootloader_version = struct.unpack('<I', data[4:8])[0]
                        info['bootloader_version'] = f"0x{bootloader_version:08x}"
            
        except Exception as e:
            self.log(f"Erro ao obter informações do dispositivo: {str(e)}")
        
        return info
    
    def get_pit_data(self) -> Optional[bytes]:
        """Obtém dados da tabela PIT"""
        try:
            if not self.session_active:
                if not self.handshake():
                    return None
            
            self.log("Obtendo dados PIT...")
            
            # Solicita PIT
            if not self.send_packet(PacketType.PIT_FILE):
                return None
            
            # Recebe dados PIT
            packet_type, data = self.receive_packet(timeout=10000)
            if packet_type == PacketType.PIT_FILE:
                self.log(f"PIT recebido: {len(data)} bytes")
                return data
            
            return None
            
        except Exception as e:
            self.log(f"Erro ao obter PIT: {str(e)}")
            return None
    
    def flash_partition(self, partition_name: str, data: bytes, 
                       progress_callback: Optional[Callable] = None) -> bool:
        """Faz flash de uma partição"""
        try:
            if not self.session_active:
                if not self.handshake():
                    return False
            
            self.log(f"Iniciando flash da partição {partition_name}...")
            
            # Define total de bytes
            total_bytes = len(data)
            if not self.send_packet(PacketType.FLASH_SET_TOTAL_BYTES, 
                                  struct.pack('<I', total_bytes)):
                return False
            
            # Recebe confirmação
            packet_type, _ = self.receive_packet()
            if packet_type != PacketType.FLASH_SET_TOTAL_BYTES:
                self.log("Falha ao definir total de bytes")
                return False
            
            # Envia dados em chunks
            chunk_size = 1024 * 1024  # 1MB chunks
            bytes_sent = 0
            
            while bytes_sent < total_bytes:
                chunk_end = min(bytes_sent + chunk_size, total_bytes)
                chunk = data[bytes_sent:chunk_end]
                
                # Envia chunk
                if not self.send_packet(PacketType.FLASH_SEND_DATA, chunk):
                    return False
                
                # Recebe confirmação
                packet_type, _ = self.receive_packet()
                if packet_type != PacketType.FLASH_SEND_DATA:
                    self.log("Falha ao enviar dados")
                    return False
                
                bytes_sent += len(chunk)
                
                # Atualiza progresso
                if progress_callback:
                    progress = FlashProgress(
                        current_bytes=bytes_sent,
                        total_bytes=total_bytes,
                        current_file=partition_name,
                        stage="Enviando dados",
                        percentage=(bytes_sent / total_bytes) * 100
                    )
                    progress_callback(progress)
                
                self.log(f"Progresso: {bytes_sent}/{total_bytes} bytes ({(bytes_sent/total_bytes)*100:.1f}%)")
            
            self.log(f"Flash da partição {partition_name} concluído")
            return True
            
        except Exception as e:
            self.log(f"Erro no flash da partição {partition_name}: {str(e)}")
            return False
    
    def reboot_device(self, mode: SamsungMode = SamsungMode.NORMAL) -> bool:
        """Reinicia o dispositivo"""
        try:
            self.log(f"Reiniciando dispositivo para modo {mode.value}...")
            
            # Envia comando de fim de sessão (que geralmente reinicia)
            if self.send_packet(PacketType.END_SESSION):
                self.session_active = False
                self.log("Comando de reinicialização enviado")
                return True
            
            return False
            
        except Exception as e:
            self.log(f"Erro ao reiniciar dispositivo: {str(e)}")
            return False
    
    def disconnect(self):
        """Desconecta do dispositivo"""
        try:
            if self.session_active:
                self.send_packet(PacketType.END_SESSION)
                self.session_active = False
            
            if self.device:
                usb.util.dispose_resources(self.device)
                self.device = None
            
            self.log("Dispositivo desconectado")
            
        except Exception as e:
            self.log(f"Erro ao desconectar: {str(e)}")


class FirmwareParser:
    """Parser para arquivos de firmware Samsung"""
    
    @staticmethod
    def parse_tar_firmware(tar_path: str) -> Dict[str, bytes]:
        """Extrai e organiza arquivos de firmware de um TAR"""
        firmware_data = {}
        
        try:
            with tarfile.open(tar_path, 'r') as tar:
                for member in tar.getmembers():
                    if member.isfile():
                        file_data = tar.extractfile(member).read()
                        
                        # Determina tipo de partição baseado no nome do arquivo
                        filename = member.name.lower()
                        
                        if 'boot' in filename:
                            firmware_data['BOOT'] = file_data
                        elif 'recovery' in filename:
                            firmware_data['RECOVERY'] = file_data
                        elif 'system' in filename:
                            firmware_data['SYSTEM'] = file_data
                        elif 'userdata' in filename:
                            firmware_data['USERDATA'] = file_data
                        elif 'cache' in filename:
                            firmware_data['CACHE'] = file_data
                        elif 'modem' in filename or 'cp' in filename:
                            firmware_data['MODEM'] = file_data
                        elif 'sboot' in filename or 'bl' in filename:
                            firmware_data['BOOTLOADER'] = file_data
                        else:
                            # Usa nome do arquivo como chave
                            partition_name = os.path.splitext(member.name)[0].upper()
                            firmware_data[partition_name] = file_data
        
        except Exception as e:
            raise Exception(f"Erro ao analisar firmware TAR: {str(e)}")
        
        return firmware_data
    
    @staticmethod
    def verify_firmware_integrity(file_path: str) -> bool:
        """Verifica integridade do firmware"""
        try:
            # Verifica se existe arquivo MD5
            md5_file = file_path + '.md5'
            if os.path.exists(md5_file):
                with open(md5_file, 'r') as f:
                    expected_md5 = f.read().strip().split()[0]
                
                # Calcula MD5 do arquivo
                hasher = hashlib.md5()
                with open(file_path, 'rb') as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        hasher.update(chunk)
                
                calculated_md5 = hasher.hexdigest()
                return calculated_md5.lower() == expected_md5.lower()
            
            # Se não há arquivo MD5, assume que está correto
            return True
            
        except Exception:
            return False


class ZodinFlashEngine:
    """Engine principal do Zodin Flash Tool"""
    
    def __init__(self, progress_callback: Optional[Callable] = None,
                 log_callback: Optional[Callable] = None):
        self.protocol = SamsungProtocol(progress_callback, log_callback)
        self.progress_callback = progress_callback
        self.log_callback = log_callback
        self.connected_device = None
    
    def log(self, message: str):
        """Envia mensagem para callback de log"""
        if self.log_callback:
            self.log_callback(message)
    
    def detect_devices(self) -> List[SamsungDevice]:
        """Detecta dispositivos Samsung"""
        return self.protocol.detect_devices()
    
    def connect_device(self, device: SamsungDevice) -> bool:
        """Conecta a um dispositivo"""
        if self.protocol.connect_device(device):
            self.connected_device = device
            return True
        return False
    
    def get_device_info(self) -> Dict[str, str]:
        """Obtém informações do dispositivo conectado"""
        if not self.connected_device:
            return {}
        
        return self.protocol.get_device_info()
    
    def flash_firmware_files(self, firmware_files: Dict[str, str]) -> bool:
        """Faz flash de múltiplos arquivos de firmware"""
        try:
            if not self.connected_device:
                self.log("Nenhum dispositivo conectado")
                return False
            
            self.log("Iniciando processo de flash...")
            
            # Processa cada arquivo
            for file_type, file_path in firmware_files.items():
                self.log(f"Processando arquivo {file_type}: {os.path.basename(file_path)}")
                
                # Verifica integridade
                if not FirmwareParser.verify_firmware_integrity(file_path):
                    self.log(f"⚠️ Aviso: Falha na verificação de integridade de {file_type}")
                
                # Determina como processar o arquivo
                if file_path.endswith('.tar'):
                    # Arquivo TAR - extrai partições
                    firmware_data = FirmwareParser.parse_tar_firmware(file_path)
                    
                    for partition_name, data in firmware_data.items():
                        if not self.protocol.flash_partition(partition_name, data, self.progress_callback):
                            self.log(f"Falha no flash da partição {partition_name}")
                            return False
                
                else:
                    # Arquivo único
                    with open(file_path, 'rb') as f:
                        data = f.read()
                    
                    partition_name = file_type.upper()
                    if not self.protocol.flash_partition(partition_name, data, self.progress_callback):
                        self.log(f"Falha no flash da partição {partition_name}")
                        return False
            
            self.log("Flash concluído com sucesso!")
            return True
            
        except Exception as e:
            self.log(f"Erro no flash: {str(e)}")
            return False
    
    def reboot_device(self, mode: SamsungMode = SamsungMode.NORMAL) -> bool:
        """Reinicia o dispositivo"""
        return self.protocol.reboot_device(mode)
    
    def get_pit_data(self) -> Optional[bytes]:
        """Obtém dados PIT"""
        return self.protocol.get_pit_data()
    
    def disconnect(self):
        """Desconecta do dispositivo"""
        self.protocol.disconnect()
        self.connected_device = None

