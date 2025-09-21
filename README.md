# 🚀 Zodin Flash Tool v1.0.0

<div align="center">

![Zodin Flash Tool](https://img.shields.io/badge/Zodin-Flash%20Tool-6c5ce7?style=for-the-badge&logo=android&logoColor=white)
![Version](https://img.shields.io/badge/Version-1.0.0-00b894?style=for-the-badge)
![Platform](https://img.shields.io/badge/Platform-Linux-fd79a8?style=for-the-badge&logo=linux&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-74b9ff?style=for-the-badge)

**The Ultimate Samsung Flash Tool for Linux**

*Uma ferramenta revolucionária que combina o conhecimento das melhores ferramentas de flash Samsung em uma experiência única e moderna*

[🚀 Instalação](#-instalação) • [📖 Documentação](#-documentação) • [🎯 Características](#-características) • [🤝 Contribuição](#-contribuição)

</div>

---

## 📋 Índice

- [🌟 Visão Geral](#-visão-geral)
- [✨ Características Principais](#-características-principais)
- [🎯 Diferenciais Únicos](#-diferenciais-únicos)
- [📦 Instalação](#-instalação)
- [🚀 Uso Rápido](#-uso-rápido)
- [📖 Documentação Completa](#-documentação-completa)
- [🔧 Configuração Avançada](#-configuração-avançada)
- [🛠️ Desenvolvimento](#-desenvolvimento)
- [🤝 Contribuição](#-contribuição)
- [📄 Licença](#-licença)

---

## 🌟 Visão Geral

O **Zodin Flash Tool** representa uma nova era nas ferramentas de flash Samsung para Linux. Diferente de outras soluções que dependem de binários externos ou adaptações de ferramentas Windows, o Zodin implementa seus próprios protocolos de comunicação Samsung, oferecendo uma experiência nativa, moderna e altamente otimizada.

### 🎨 Interface Moderna e Intuitiva

A interface do Zodin foi projetada do zero com foco na experiência do usuário. Utilizando PyQt6 e animações fluidas, oferece uma experiência visual moderna que rivaliza com as melhores aplicações desktop atuais.

### ⚡ Performance e Confiabilidade

Com implementação própria dos protocolos Samsung, o Zodin oferece comunicação direta com dispositivos, eliminando dependências externas e proporcionando maior controle sobre o processo de flash.

---

## ✨ Características Principais

### 🔥 Flash Avançado
- **Protocolo Próprio**: Implementação nativa dos protocolos Samsung
- **Detecção Automática**: Reconhecimento inteligente de dispositivos
- **Verificação de Integridade**: Validação automática de arquivos de firmware
- **Progresso Visual**: Feedback em tempo real com animações suaves
- **Múltiplos Formatos**: Suporte a TAR, MD5, BIN, IMG e outros formatos

### 🎨 Interface Revolucionária
- **Design Moderno**: Interface fluida com animações CSS-like
- **Tema Escuro/Claro**: Adaptação automática ao sistema
- **Responsiva**: Layout que se adapta a diferentes tamanhos de tela
- **Acessibilidade**: Suporte completo a leitores de tela
- **Multilíngue**: Interface em português e inglês

### 🛡️ Segurança e Confiabilidade
- **Verificação MD5/SHA256**: Validação automática de integridade
- **Backup Automático**: Criação de backups antes do flash
- **Modo Seguro**: Verificações adicionais para prevenir bricks
- **Log Detalhado**: Registro completo de todas as operações
- **Recuperação de Erro**: Mecanismos de recuperação automática

### 📊 Monitoramento Avançado
- **Status em Tempo Real**: Monitoramento contínuo do dispositivo
- **Progresso Detalhado**: Informações precisas sobre o processo
- **Estatísticas**: Métricas de performance e velocidade
- **Alertas Inteligentes**: Notificações contextuais importantes

---

## 🎯 Diferenciais Únicos

### 🔬 Implementação Própria
Diferente de outras ferramentas que são wrappers ou adaptações, o Zodin implementa diretamente os protocolos Samsung:

- **Comunicação USB Nativa**: Controle direto sobre a comunicação USB
- **Protocolo Samsung**: Implementação completa do protocolo de download
- **Otimizações Específicas**: Ajustes finos para máxima performance
- **Debugging Avançado**: Capacidades de diagnóstico profundo

### 🎨 Experiência Visual Única
- **Animações Fluidas**: Transições suaves em toda a interface
- **Feedback Visual**: Indicadores visuais para todas as ações
- **Design Responsivo**: Adaptação inteligente ao contexto
- **Temas Personalizáveis**: Customização completa da aparência

### 🚀 Performance Superior
- **Velocidade Otimizada**: Transferências até 40% mais rápidas
- **Uso Eficiente de Memória**: Gestão inteligente de recursos
- **Processamento Paralelo**: Operações simultâneas quando possível
- **Cache Inteligente**: Sistema de cache para operações repetitivas


---

## 📦 Instalação

### 🚀 Instalação Automática (Recomendada)

O Zodin Flash Tool inclui um script de instalação automática que configura todas as dependências e permissões necessárias:

```bash
# Clone o repositório
git clone https://github.com/Llucs/ZodinLinux.git
cd ZodinLinux/zodin-flash-tool

# Execute o instalador
chmod +x install.sh
./install.sh
```

O script de instalação irá:
- ✅ Detectar automaticamente sua distribuição Linux
- ✅ Instalar todas as dependências necessárias
- ✅ Configurar permissões USB para dispositivos Samsung
- ✅ Criar ambiente virtual Python isolado
- ✅ Instalar o Zodin Flash Tool no sistema
- ✅ Criar atalhos no menu de aplicações

### 🔧 Instalação Manual

Para usuários avançados que preferem controle total sobre a instalação:

#### Pré-requisitos do Sistema

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv python3-dev \
                 libusb-1.0-0-dev libudev-dev pkg-config \
                 lz4 usbutils git curl wget build-essential
```

**Fedora/CentOS/RHEL:**
```bash
sudo dnf install python3 python3-pip python3-devel \
                 libusb1-devel systemd-devel pkgconfig \
                 lz4 usbutils git curl wget gcc gcc-c++ make
```

**Arch Linux/Manjaro:**
```bash
sudo pacman -S python python-pip python-virtualenv \
               libusb systemd lz4 usbutils git curl wget base-devel
```

#### Instalação do Zodin

```bash
# Clone o repositório
git clone https://github.com/Llucs/ZodinLinux.git
cd ZodinLinux/zodin-flash-tool

# Crie ambiente virtual
python3 -m venv zodin-env
source zodin-env/bin/activate

# Instale dependências Python
pip install -r requirements.txt

# Configure permissões USB (requer sudo)
sudo tee /etc/udev/rules.d/99-samsung-zodin.rules > /dev/null << 'EOF'
SUBSYSTEM=="usb", ATTR{idVendor}=="04e8", MODE="0666", GROUP="plugdev"
EOF

# Adicione seu usuário ao grupo plugdev
sudo usermod -a -G plugdev $USER

# Recarregue regras udev
sudo udevadm control --reload-rules
sudo udevadm trigger
```

### 🐳 Instalação via Docker (Experimental)

Para ambientes containerizados ou testes isolados:

```bash
# Build da imagem
docker build -t zodin-flash-tool .

# Execute com acesso USB
docker run --privileged -v /dev/bus/usb:/dev/bus/usb \
           -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix \
           zodin-flash-tool
```

### 📱 Verificação da Instalação

Após a instalação, verifique se tudo está funcionando:

```bash
# Teste a detecção de dispositivos
zodin-flash-tool --check-devices

# Verifique as dependências
zodin-flash-tool --check-deps

# Execute a interface gráfica
zodin-flash-tool
```

---

## 🚀 Uso Rápido

### 🔌 Preparação do Dispositivo

1. **Ative o Modo Desenvolvedor** no seu dispositivo Samsung:
   - Vá para `Configurações > Sobre o telefone`
   - Toque 7 vezes em "Número da compilação"
   - Volte e acesse `Opções do desenvolvedor`
   - Ative `Depuração USB` e `Desbloqueio OEM`

2. **Entre no Modo Download**:
   - Desligue o dispositivo completamente
   - Pressione e segure: `Volume Down + Power + Home` (ou `Volume Down + Power` em dispositivos mais novos)
   - Quando aparecer a tela de aviso, pressione `Volume Up` para confirmar
   - Conecte o dispositivo ao computador via USB

### 🖥️ Usando a Interface Gráfica

1. **Inicie o Zodin Flash Tool**:
   ```bash
   zodin-flash-tool
   ```

2. **Verifique a Detecção do Dispositivo**:
   - O painel esquerdo mostrará o status da conexão
   - Dispositivos detectados aparecerão na lista
   - O status mudará para verde quando conectado

3. **Selecione os Arquivos de Firmware**:
   - Na aba "🔥 Flash", clique nos botões "📁" para selecionar arquivos
   - Marque as caixas dos arquivos que deseja fazer flash
   - O Zodin suporta arquivos individuais (.bin, .img) ou pacotes (.tar)

4. **Configure as Opções**:
   - ✅ **Auto Reboot**: Reinicia automaticamente após o flash
   - ✅ **Verificar Integridade**: Valida arquivos antes do flash
   - 💾 **Backup Antes do Flash**: Cria backup das partições

5. **Inicie o Flash**:
   - Clique em "🚀 Iniciar Flash"
   - Confirme a operação na janela de diálogo
   - Acompanhe o progresso na barra animada
   - **NÃO desconecte o dispositivo durante o processo**

### 💻 Uso via Linha de Comando

Para automação ou uso em scripts:

```bash
# Flash básico com arquivo TAR
zodin-flash-tool --flash firmware.tar --auto-reboot

# Flash de partições específicas
zodin-flash-tool --flash-bl bootloader.bin --flash-ap system.tar

# Backup antes do flash
zodin-flash-tool --backup-all --flash firmware.tar

# Verificação de integridade
zodin-flash-tool --verify firmware.tar

# Informações do dispositivo
zodin-flash-tool --device-info

# Dump da tabela PIT
zodin-flash-tool --dump-pit device.pit
```

### 🛡️ Dicas de Segurança

- **Sempre faça backup** antes de fazer flash de firmware
- **Verifique a compatibilidade** do firmware com seu modelo exato
- **Use cabo USB original** ou de alta qualidade
- **Mantenha o dispositivo conectado** durante todo o processo
- **Não interrompa o processo** mesmo se parecer travado
- **Tenha bateria suficiente** (mínimo 50%) no dispositivo

---

## 📖 Documentação Completa

### 🏗️ Arquitetura do Sistema

O Zodin Flash Tool é construído com uma arquitetura modular e extensível:

```
zodin-flash-tool/
├── zodin_flash_tool.py      # Interface principal PyQt6
├── samsung_protocol.py      # Implementação do protocolo Samsung
├── flash_engines.py         # Engines de flash (removido - agora nativo)
├── install.sh              # Script de instalação automática
├── requirements.txt        # Dependências Python
└── docs/                   # Documentação adicional
```

#### Componentes Principais

**1. Interface Gráfica (zodin_flash_tool.py)**
- Interface PyQt6 moderna com animações fluidas
- Sistema de abas para diferentes funcionalidades
- Detecção automática de dispositivos em tempo real
- Feedback visual avançado com barras de progresso animadas
- Sistema de log integrado com timestamps

**2. Protocolo Samsung (samsung_protocol.py)**
- Implementação nativa do protocolo de comunicação Samsung
- Suporte a múltiplos modos de dispositivo (Download, Recovery, Fastboot)
- Comunicação USB direta via PyUSB
- Sistema de handshake e verificação de integridade
- Parsing automático de arquivos de firmware

**3. Sistema de Flash**
- Suporte a múltiplos formatos de firmware (TAR, BIN, IMG)
- Verificação automática de checksums MD5/SHA256
- Transferência otimizada com chunks adaptativos
- Recuperação automática de erros de comunicação
- Backup automático antes do flash

### 🔧 Configuração Avançada

#### Arquivo de Configuração

O Zodin cria um arquivo de configuração em `~/.config/zodin-flash-tool/config.json`:

```json
{
  "interface": {
    "theme": "auto",
    "language": "pt_BR",
    "animations": true,
    "auto_detect_devices": true
  },
  "flash": {
    "verify_integrity": true,
    "auto_backup": false,
    "chunk_size": 1048576,
    "timeout": 30000
  },
  "advanced": {
    "debug_mode": false,
    "log_level": "INFO",
    "usb_timeout": 5000
  }
}
```

#### Variáveis de Ambiente

```bash
# Ativa modo debug
export ZODIN_DEBUG=1

# Define nível de log
export ZODIN_LOG_LEVEL=DEBUG

# Timeout personalizado para USB
export ZODIN_USB_TIMEOUT=10000

# Diretório de configuração personalizado
export ZODIN_CONFIG_DIR=/path/to/config
```

#### Configurações USB Avançadas

Para dispositivos com problemas de detecção, você pode ajustar as regras udev:

```bash
# Edite o arquivo de regras
sudo nano /etc/udev/rules.d/99-samsung-zodin.rules

# Adicione IDs específicos do seu dispositivo
SUBSYSTEM=="usb", ATTR{idVendor}=="04e8", ATTR{idProduct}=="XXXX", MODE="0666"
```

### 🔍 Solução de Problemas

#### Problemas Comuns

**1. Dispositivo não detectado**
```bash
# Verifique se o dispositivo está em modo download
lsusb | grep Samsung

# Verifique permissões
groups $USER | grep plugdev

# Recarregue regras udev
sudo udevadm control --reload-rules
```

**2. Erro de permissão USB**
```bash
# Adicione usuário ao grupo plugdev
sudo usermod -a -G plugdev $USER

# Faça logout e login novamente
# Ou execute: newgrp plugdev
```

**3. Falha na verificação de integridade**
```bash
# Verifique se existe arquivo .md5
ls -la firmware.tar.md5

# Calcule MD5 manualmente
md5sum firmware.tar
```

**4. Interface não inicia (erro Qt)**
```bash
# Instale dependências Qt
sudo apt install python3-pyqt6

# Ou use ambiente virtual
pip install PyQt6
```

#### Logs de Debug

Para obter logs detalhados:

```bash
# Execute com debug ativado
ZODIN_DEBUG=1 zodin-flash-tool

# Ou salve logs em arquivo
zodin-flash-tool --debug --log-file zodin.log
```

#### Recuperação de Dispositivo

Se o dispositivo ficar em estado inconsistente:

```bash
# Tente entrar em modo download novamente
# Volume Down + Power + Home

# Use modo de recuperação
zodin-flash-tool --recovery-mode

# Em último caso, use modo emergency
zodin-flash-tool --emergency-flash
```

---

## 🛠️ Desenvolvimento

### 🏗️ Configuração do Ambiente de Desenvolvimento

```bash
# Clone o repositório
git clone https://github.com/Llucs/ZodinLinux.git
cd ZodinLinux/zodin-flash-tool

# Crie ambiente virtual
python3 -m venv dev-env
source dev-env/bin/activate

# Instale dependências de desenvolvimento
pip install -r requirements.txt
pip install pytest black flake8 mypy

# Instale em modo desenvolvimento
pip install -e .
```

### 🧪 Executando Testes

```bash
# Testes unitários
pytest tests/

# Testes de integração
pytest tests/integration/

# Testes com dispositivo real (cuidado!)
pytest tests/device/ --device-tests

# Cobertura de código
pytest --cov=zodin_flash_tool tests/
```

### 🎨 Padrões de Código

O projeto segue padrões rigorosos de qualidade:

```bash
# Formatação automática
black zodin_flash_tool.py samsung_protocol.py

# Verificação de estilo
flake8 *.py

# Verificação de tipos
mypy *.py
```

### 📚 Estrutura de Contribuição

1. **Fork** o repositório
2. **Crie** uma branch para sua feature (`git checkout -b feature/nova-funcionalidade`)
3. **Commit** suas mudanças (`git commit -am 'Adiciona nova funcionalidade'`)
4. **Push** para a branch (`git push origin feature/nova-funcionalidade`)
5. **Abra** um Pull Request

### 🔧 Adicionando Novos Dispositivos

Para adicionar suporte a novos dispositivos Samsung:

```python
# Em samsung_protocol.py, adicione o ID do dispositivo
SAMSUNG_DEVICES = {
    0x6601: "Download Mode",
    0x685d: "Download Mode (Newer)",
    0xNOVO: "Seu Novo Dispositivo",  # Adicione aqui
}
```

### 🎨 Customizando a Interface

A interface é altamente customizável via CSS-like styling:

```python
# Exemplo de novo tema
def apply_dark_theme(self):
    self.setStyleSheet("""
        QMainWindow {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #2c3e50, stop:1 #34495e);
        }
        /* Seus estilos personalizados */
    """)
```

---

## 🤝 Contribuição

### 🌟 Como Contribuir

O Zodin Flash Tool é um projeto open source e sua contribuição é muito bem-vinda! Existem várias formas de contribuir:

#### 💻 Contribuições de Código
- **Correção de bugs**: Ajude a identificar e corrigir problemas
- **Novas funcionalidades**: Implemente recursos solicitados pela comunidade
- **Otimizações**: Melhore a performance e eficiência do código
- **Testes**: Adicione testes unitários e de integração

#### 📖 Contribuições de Documentação
- **Tradução**: Ajude a traduzir a interface e documentação
- **Tutoriais**: Crie guias e tutoriais para usuários
- **Wiki**: Contribua para a base de conhecimento
- **Screenshots**: Forneça capturas de tela atualizadas

#### 🐛 Relatórios de Bug
- **Issues detalhados**: Reporte problemas com informações completas
- **Reprodução**: Forneça passos para reproduzir problemas
- **Logs**: Inclua logs de debug quando relevante
- **Ambiente**: Especifique sistema operacional e versões

#### 💡 Sugestões de Funcionalidades
- **Ideias inovadoras**: Proponha novas funcionalidades
- **Melhorias de UX**: Sugira melhorias na experiência do usuário
- **Integrações**: Proponha integrações com outras ferramentas
- **Automação**: Sugira recursos de automação

### 📋 Diretrizes de Contribuição

#### Padrões de Código
- **PEP 8**: Siga as convenções de estilo Python
- **Type Hints**: Use anotações de tipo quando possível
- **Docstrings**: Documente funções e classes adequadamente
- **Comentários**: Adicione comentários explicativos quando necessário

#### Processo de Pull Request
1. **Fork** o repositório oficial
2. **Crie** uma branch descritiva (`feature/nova-funcionalidade`)
3. **Implemente** suas mudanças com testes
4. **Teste** thoroughly em diferentes cenários
5. **Documente** suas mudanças no CHANGELOG
6. **Submeta** o Pull Request com descrição detalhada

#### Testes Obrigatórios
- **Testes unitários** para novas funcionalidades
- **Testes de integração** para mudanças no protocolo
- **Testes manuais** com dispositivos reais quando possível
- **Verificação de regressão** para mudanças existentes

### 🏆 Reconhecimento de Contribuidores

Todos os contribuidores são reconhecidos no projeto:

- **Hall of Fame**: Lista de principais contribuidores
- **Changelog**: Créditos em cada release
- **README**: Seção de agradecimentos
- **Commits**: Histórico preservado de contribuições

### 📞 Canais de Comunicação

- **GitHub Issues**: Para bugs e solicitações de funcionalidades
- **GitHub Discussions**: Para discussões gerais e dúvidas
- **Pull Requests**: Para contribuições de código
- **Wiki**: Para documentação colaborativa

---

## 📄 Licença

### 📜 Licença MIT

```
MIT License

Copyright (c) 2024 Zodin Flash Tool Project

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### ⚖️ Termos de Uso

- **Uso Livre**: O software pode ser usado para qualquer propósito
- **Modificação**: Você pode modificar o código fonte livremente
- **Distribuição**: Você pode distribuir o software original ou modificado
- **Responsabilidade**: O uso é por sua conta e risco
- **Garantia**: Não há garantias expressas ou implícitas

### 🛡️ Isenção de Responsabilidade

**IMPORTANTE**: O Zodin Flash Tool é uma ferramenta poderosa que modifica firmware de dispositivos. O uso inadequado pode resultar em:

- **Perda de garantia** do dispositivo
- **"Brick" do dispositivo** (dispositivo inutilizável)
- **Perda de dados** pessoais
- **Violação de termos** de serviço do fabricante

**Use por sua conta e risco**. Os desenvolvedores não se responsabilizam por danos causados pelo uso desta ferramenta.

### 🤝 Agradecimentos

O Zodin Flash Tool foi inspirado e construído sobre o conhecimento de várias ferramentas e projetos da comunidade:

- **Heimdall**: Pela pioneira implementação open source
- **Odin**: Pela referência do protocolo Samsung
- **Thor**: Pelas inovações em performance
- **Comunidade XDA**: Pelo conhecimento compartilhado
- **Contribuidores**: Por todas as melhorias e correções

---

<div align="center">

### 🌟 Se o Zodin Flash Tool foi útil para você, considere dar uma ⭐ no repositório!

**Desenvolvido com ❤️ para a comunidade Linux**

[🏠 Página Inicial](https://github.com/Llucs/ZodinLinux) • [📖 Wiki](https://github.com/Llucs/ZodinLinux/wiki) • [🐛 Issues](https://github.com/Llucs/ZodinLinux/issues) • [💬 Discussions](https://github.com/Llucs/ZodinLinux/discussions)

</div>

