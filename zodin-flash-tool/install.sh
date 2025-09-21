#!/bin/bash

# Zodin Flash Tool - Installation Script
# Version: 1.1.4
# The Ultimate Samsung Flash Tool for Linux

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ASCII Art Logo
print_logo() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                                                              ║"
    echo "║    ███████╗ ██████╗ ██████╗ ██╗███╗   ██╗                   ║"
    echo "║    ╚══███╔╝██╔═══██╗██╔══██╗██║████╗  ██║                   ║"
    echo "║      ███╔╝ ██║   ██║██║  ██║██║██╔██╗ ██║                   ║"
    echo "║     ███╔╝  ██║   ██║██║  ██║██║██║╚██╗██║                   ║"
    echo "║    ███████╗╚██████╔╝██████╔╝██║██║ ╚████║                   ║"
    echo "║    ╚══════╝ ╚═════╝ ╚═════╝ ╚═╝╚═╝  ╚═══╝                   ║"
    echo "║                                                              ║"
    echo "║              FLASH TOOL v1.1.4                              ║"
    echo "║        The Ultimate Samsung Flash Tool for Linux            ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Print colored messages
print_info() {
    echo -e "${CYAN}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        print_error "Please do not run this script as root."
        print_info "Run as normal user. The script will ask for sudo when needed."
        exit 1
    fi
}

# Detect Linux distribution
detect_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        DISTRO=$ID
        VERSION=$VERSION_ID
        
        # Handle distributions based on others
        case $ID in
            zorin)
                # Zorin OS is based on Ubuntu
                DISTRO="ubuntu"
                ;;
            pop)
                # Pop!_OS is based on Ubuntu
                DISTRO="ubuntu"
                ;;
            linuxmint)
                # Linux Mint is based on Ubuntu
                DISTRO="ubuntu"
                ;;
            elementary)
                # Elementary OS is based on Ubuntu
                DISTRO="ubuntu"
                ;;
        esac
    else
        print_error "Cannot detect Linux distribution"
        exit 1
    fi
    
    print_info "Detected distribution: $PRETTY_NAME"
}

# Install dependencies based on distribution
install_dependencies() {
    print_step "Installing system dependencies..."
    
    case $DISTRO in
        ubuntu|debian|linuxmint|pop)
            print_info "Installing dependencies for Debian/Ubuntu based system..."
            sudo apt update
            sudo apt install -y python3 python3-pip python3-venv python3-dev \
                               libusb-1.0-0-dev libudev-dev pkg-config \
                               heimdall-flash lz4 usbutils git curl wget \
                               build-essential libxcb-xinerama0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-render-util0 libxcb-shm0 libxcb-sync1 libxcb-xfixes0 libxcb-xkb1 libxkbcommon-x11-0 libxcb-cursor0
            ;;
        fedora|centos|rhel)
            print_info "Installing dependencies for Red Hat based system..."
            sudo dnf install -y python3 python3-pip python3-devel \
                               libusb1-devel systemd-devel pkgconfig \
                               heimdall lz4 usbutils git curl wget \
                               gcc gcc-c++ make
            ;;
        arch|manjaro)
            print_info "Installing dependencies for Arch based system..."
            sudo pacman -S --needed python python-pip python-virtualenv \
                                   libusb systemd lz4 usbutils git curl wget \
                                   base-devel heimdall
            ;;
        opensuse*)
            print_info "Installing dependencies for openSUSE..."
            sudo zypper install -y python3 python3-pip python3-devel \
                                   libusb-1_0-devel systemd-devel pkg-config \
                                   lz4 usbutils git curl wget \
                                   gcc gcc-c++ make
            ;;
        *)
            print_warning "Unsupported distribution: $DISTRO"
            print_info "Please install dependencies manually:"
            print_info "- Python 3.8+"
            print_info "- PyQt6"
            print_info "- heimdall-flash"
            print_info "- lz4"
            print_info "- libusb development files"
            ;;
    esac
}

# Install Python dependencies
install_python_deps() {
    print_step "Installing Python dependencies..."
    
    # Create virtual environment
    python3 -m venv ~/.zodin-venv
    source ~/.zodin-venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install required packages (including pyusb that was missing!)
    pip install PyQt6 pyusb requests beautifulsoup4 lxml
    
    print_success "Python dependencies installed in virtual environment"
}

# Download additional flash tools
download_flash_tools() {
    print_step "Downloading additional flash tools..."
    
    TOOLS_DIR="$HOME/.local/share/zodin-flash-tool/tools"
    mkdir -p "$TOOLS_DIR"
    
    # Download Thor (if available)
    print_info "Checking for Thor flash utility..."
    if command -v dotnet >/dev/null 2>&1; then
        print_info "Dotnet runtime found, Thor support available"
    else
        print_warning "Dotnet runtime not found, Thor will not be available"
        print_info "To install dotnet: https://docs.microsoft.com/en-us/dotnet/core/install/linux"
    fi
    
    # Download Odin4 (if available)
    print_info "Checking for Odin4..."
    if [ ! -f "$TOOLS_DIR/odin4" ]; then
        print_info "Odin4 not found in tools directory"
        print_info "You can manually download Odin4 from official sources"
    fi
}

# Setup udev rules for Samsung devices
setup_udev_rules() {
    print_step "Setting up udev rules for Samsung devices..."
    
    UDEV_RULES="/etc/udev/rules.d/99-samsung-zodin.rules"
    
    sudo tee "$UDEV_RULES" > /dev/null << 'EOF'
# Samsung devices for Zodin Flash Tool
SUBSYSTEM=="usb", ATTR{idVendor}=="04e8", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="04e8", ATTR{idProduct}=="6601", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="04e8", ATTR{idProduct}=="685d", MODE="0666", GROUP="plugdev"

# Additional Samsung device IDs
SUBSYSTEM=="usb", ATTR{idVendor}=="04e8", ATTR{idProduct}=="6860", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="04e8", ATTR{idProduct}=="68c3", MODE="0666", GROUP="plugdev"
EOF

    # Add user to plugdev group
    sudo usermod -a -G plugdev "$USER"
    
    # Reload udev rules
    sudo udevadm control --reload-rules
    sudo udevadm trigger
    
    print_success "udev rules installed for Samsung USB devices"
    print_warning "You may need to log out and log back in for group changes to take effect"
}

# Install Zodin Flash Tool
install_zodin() {
    print_step "Installing Zodin Flash Tool..."
    
    APP_DIR="$HOME/.local/share/zodin-flash-tool"
    BIN_DIR="$HOME/.local/bin"
    DESKTOP_DIR="$HOME/.local/share/applications"
    ICON_DIR="$HOME/.local/share/icons"
    
    # Create directories
    mkdir -p "$APP_DIR" "$BIN_DIR" "$DESKTOP_DIR" "$ICON_DIR"
    
    # Copy ALL application files (this was the main problem!)
    print_info "Copying application files..."
    cp zodin_flash_tool.py "$APP_DIR/"
    cp samsung_protocol.py "$APP_DIR/"
    cp updater.py "$APP_DIR/"
    cp flash_engines.py "$APP_DIR/"
    cp requirements.txt "$APP_DIR/"
    
    # Copy tools directory if it exists
    if [ -d "tools" ]; then
        cp -r tools "$APP_DIR/"
    fi
    
    # Create launcher script with proper error handling for sudo and venv
    cat > "$BIN_DIR/zodin-flash-tool" << EOF
#!/bin/bash
# Zodin Flash Tool Launcher v1.1.2

APP_DIR="$APP_DIR"
VENV_DIR="$HOME/.zodin-venv"
PYTHON_EXEC="\$VENV_DIR/bin/python3"
MAIN_SCRIPT="\$APP_DIR/zodin_flash_tool.py"

# Check if virtual environment exists
if [ ! -d "\$VENV_DIR" ]; then
    echo "❌ Ambiente virtual não encontrado. Por favor, reinstale o Zodin Flash Tool."
    exit 1
fi

# Check if main script exists
if [ ! -f "\$MAIN_SCRIPT" ]; then
    echo "❌ Zodin Flash Tool não encontrado. Por favor, reinstale."
    exit 1
fi

# If running with sudo, ensure the correct python from venv is used
if [ "\$(id -u)" -eq 0 ]; then
    # Running as root, use the python from the user's venv
    # This requires the user's HOME directory to be correctly set
    # and the venv to be accessible by root (which it is by default)
    echo "⚠️  Executando como root. Usando ambiente virtual do usuário: \$VENV_DIR"
    exec sudo -E \$PYTHON_EXEC \$MAIN_SCRIPT "\$@"
else
    # Running as normal user, activate venv and run
    source "\$VENV_DIR/bin/activate"
    exec \$PYTHON_EXEC \$MAIN_SCRIPT "\$@"
fi
EOF
    chmod +x "$BIN_DIR/zodin-flash-tool"
    
    # Create desktop entry
    cat > "$DESKTOP_DIR/zodin-flash-tool.desktop" << EOF
[Desktop Entry]
Name=Zodin Flash Tool
Comment=The Ultimate Samsung Flash Tool for Linux
Exec=zodin-flash-tool
Terminal=false
Type=Application
Categories=System;Utility;
Icon=zodin-flash-tool
StartupNotify=true
Keywords=samsung;flash;firmware;android;
EOF
    
    # Create simple icon (text-based)
    cat > "$ICON_DIR/zodin-flash-tool.svg" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<svg width="64" height="64" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
  <rect width="64" height="64" rx="8" fill="#007bff"/>
  <text x="32" y="40" font-family="Arial, sans-serif" font-size="20" font-weight="bold" text-anchor="middle" fill="white">Z</text>
</svg>
EOF
    
    print_success "Zodin Flash Tool installed successfully!"
    print_info "All modules copied: zodin_flash_tool.py, samsung_protocol.py, updater.py, flash_engines.py"
}

# Add to PATH
setup_path() {
    print_step "Setting up PATH..."
    
    # Check if already in PATH
    if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
        # Add to bashrc
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
        
        # Add to zshrc if it exists
        if [ -f "$HOME/.zshrc" ]; then
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.zshrc"
        fi
        
        print_success "Added $HOME/.local/bin to PATH"
        print_info "Please run 'source ~/.bashrc' or restart your terminal"
    else
        print_info "PATH already configured"
    fi
}

# Create uninstall script
create_uninstaller() {
    print_step "Creating uninstaller..."
    
    cat > "$HOME/.local/bin/zodin-uninstall" << 'EOF'
#!/bin/bash
# Zodin Flash Tool Uninstaller

echo "Uninstalling Zodin Flash Tool..."

# Remove application files
rm -rf "$HOME/.local/share/zodin-flash-tool"
rm -f "$HOME/.local/bin/zodin-flash-tool"
rm -f "$HOME/.local/bin/zodin-uninstall"
rm -f "$HOME/.local/share/applications/zodin-flash-tool.desktop"
rm -f "$HOME/.local/share/icons/zodin-flash-tool.svg"

# Remove virtual environment
rm -rf "$HOME/.zodin-venv"

# Remove udev rules (requires sudo)
sudo rm -f "/etc/udev/rules.d/99-samsung-zodin.rules"
sudo udevadm control --reload-rules

echo "Zodin Flash Tool uninstalled successfully!"
echo "Note: System dependencies were not removed."
EOF
    
    chmod +x "$HOME/.local/bin/zodin-uninstall"
    print_success "Uninstaller created: zodin-uninstall"
}

# Print final instructions
print_final_instructions() {
    echo
    print_success "🎉 Zodin Flash Tool v1.1.4 installation completed!"
    echo
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║                     INSTALLATION COMPLETE                   ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo
    print_info "You can run Zodin Flash Tool in the following ways:"
    echo -e "  ${GREEN}1.${NC} Command line: ${YELLOW}zodin-flash-tool${NC}"
    echo -e "  ${GREEN}2.${NC} Desktop: Look for 'Zodin Flash Tool' in your applications menu"
    echo -e "  ${GREEN}3.${NC} Direct: ${YELLOW}python3 $HOME/.local/share/zodin-flash-tool/zodin_flash_tool.py${NC}"
    echo
    print_info "Additional commands:"
    echo -e "  ${GREEN}•${NC} Uninstall: ${YELLOW}zodin-uninstall${NC}"
    echo
    print_warning "Important notes:"
    echo -e "  ${RED}•${NC} Para acesso USB, execute: ${YELLOW}sudo zodin-flash-tool${NC}"
    echo -e "  ${RED}•${NC} Reinicie seu terminal ou execute \'source ~/.bashrc\' para usar o comando na linha"
    echo -e "  ${RED}•${NC} Faça logout e login novamente para que as permissões USB tenham efeito"
    echo
    print_info "For support and updates, visit: https://github.com/Llucs/ZodinLinux"
    echo
    echo -e "${GREEN}Happy flashing! 🚀${NC}"
}

# Main installation function
main() {
    print_logo
    
    print_info "Starting Zodin Flash Tool installation..."
    echo
    
    check_root
    detect_distro
    install_dependencies
    install_python_deps
    download_flash_tools
    setup_udev_rules
    install_zodin
    setup_path
    create_uninstaller
    
    print_final_instructions
}

# Run main function
main "$@"

