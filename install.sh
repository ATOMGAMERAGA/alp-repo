#!/bin/bash

#############################################################################
# Alp Advanced Package Manager - Kurulum ve Kurulum Sonrası Scripti
# Sistem genelinde paket yönetimi ve otomatik güncellemeler
#############################################################################

set -e

# Renklar
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Kurulum parametreleri
INSTALL_DIR="/usr/local/lib/alp"
BIN_DIR="/usr/local/bin"
MAN_DIR="/usr/local/share/man/man1"
SYSTEMD_DIR="/etc/systemd/system"
PYTHON_MIN_VERSION="3.6"

# Durum kodları
SUCCESS=0
ERROR=1
WARNING=2

# ============================================================================
# Yardımcı Fonksiyonlar
# ============================================================================

print_header() {
    echo -e "${BOLD}${CYAN}"
    cat << "EOF"
  ╔═══════════════════════════════════════════════════════════╗
  ║     Alp Advanced Package Manager - Kurulum Scripti        ║
  ║                      v2.0                                 ║
  ╚═══════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
}

log_info() {
    echo -e "${BLUE}ℹ️  ${NC}$1"
}

log_success() {
    echo -e "${GREEN}✅ ${NC}$1"
}

log_warning() {
    echo -e "${YELLOW}⚠️  ${NC}$1"
}

log_error() {
    echo -e "${RED}❌ ${NC}$1" >&2
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "Bu script root tarafından çalıştırılmalı"
        echo "   Çalıştırın: sudo bash install.sh"
        exit $ERROR
    fi
}

check_python() {
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 yüklü değil"
        echo ""
        echo "   Ubuntu/Debian:"
        echo "     sudo apt update && sudo apt install -y python3 python3-pip"
        echo ""
        echo "   Fedora/RHEL:"
        echo "     sudo dnf install -y python3 python3-pip"
        echo ""
        echo "   Arch:"
        echo "     sudo pacman -S python"
        exit $ERROR
    fi
    
    local py_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    log_success "Python3 bulundu: v$py_version"
}

check_dependencies() {
    log_info "Bağımlılıklar kontrol ediliyor..."
    
    local missing_deps=()
    
    if ! command -v curl &> /dev/null; then
        missing_deps+=("curl")
    fi
    
    if ! command -v git &> /dev/null; then
        log_warning "Git yüklü değil (opsiyonel)"
    fi
    
    if [ ${#missing_deps[@]} -gt 0 ]; then
        log_error "Eksik bağımlılıklar: ${missing_deps[@]}"
        echo "   Yüklemek için:"
        echo "     sudo apt install -y ${missing_deps[@]}"
        exit $ERROR
    fi
    
    log_success "Tüm bağımlılıklar yüklü"
}

create_directories() {
    log_info "Dizinler oluşturuluyor..."
    
    mkdir -p "$INSTALL_DIR"
    mkdir -p "$BIN_DIR"
    mkdir -p "$MAN_DIR"
    mkdir -p "$SYSTEMD_DIR"
    
    log_success "Dizinler oluşturuldu"
}

download_manager() {
    log_info "Alp Package Manager indiriliyor..."
    
    local script_url="https://raw.githubusercontent.com/ATOMGAMERAGA/alp-repo/main/alp_manager.py"
    local retries=3
    local count=0
    
    while [ $count -lt $retries ]; do
        if curl -s -L "$script_url" -o "$INSTALL_DIR/alp_manager.py" 2>/dev/null; then
            chmod +x "$INSTALL_DIR/alp_manager.py"
            log_success "Alp Package Manager indirildi"
            return $SUCCESS
        fi
        
        count=$((count + 1))
        if [ $count -lt $retries ]; then
            log_warning "İndirme başarısız, $((retries - count)) deneme kaldı..."
            sleep 2
        fi
    done
    
    log_error "Alp Package Manager indirilemedi"
    return $ERROR
}

create_bin_wrapper() {
    log_info "Sistem komutu oluşturuluyor..."
    
    cat > "$BIN_DIR/alp" << 'WRAPPER_EOF'
#!/bin/bash
exec python3 /usr/local/lib/alp/alp_manager.py "$@"
WRAPPER_EOF
    
    chmod +x "$BIN_DIR/alp"
    log_success "Sistem komutu oluşturuldu: /usr/local/bin/alp"
}

create_man_page() {
    log_info "Man sayfası oluşturuluyor..."
    
    cat > "$MAN_DIR/alp.1.gz" << 'MAN_EOF'
.TH ALP 1
.SH NAME
alp \- Alp Advanced Package Manager
.SH SYNOPSIS
.B alp
.I KOMUT
.IR [ARGÜMANLAR]
.SH DESCRIPTION
Alp, GitHub deposundan paketleri yönetmek için tasarlanmış gelişmiş bir paket yöneticisidir.
Bağımlılık yönetimi, otomatik güncellemeler ve kapsamlı loglama özelliklerini içerir.
.SH COMMANDS
.TP
.B update
Depoyu güncelle ve yeni paketleri bul
.TP
.B install <paket>
Belirtilen paketi yükle (bağımlılıklarıyla)
.TP
.B remove <paket>
Belirtilen paketi kaldır
.TP
.B upgrade [paket]
Paketleri güncelle (tümü veya belirli)
.TP
.B list [kategori]
Mevcut paketleri listele
.TP
.B installed
Yüklü paketleri listele
.TP
.B search <anahtar>
Paket adı veya açıklamasında ara
.TP
.B info <paket>
Paket hakkında detaylı bilgi göster
.TP
.B stats
Alp istatistiklerini göster
.TP
.B clean
Cache'i temizle
.TP
.B config
Ayarları göster
.SH EXAMPLES
.TP
Depoyu güncelle:
.B alp update
.TP
Paket yükle:
.B alp install myproject
.TP
Paket kaldır:
.B alp remove myproject
.TP
Tüm paketleri güncelle:
.B alp upgrade
.TP
Paketleri listele:
.B alp list
.TP
Yüklü paketleri göster:
.B alp installed
.SH FILES
.TP
.B ~/.alp/
Alp veritabanları ve yapılandırması
.TP
.B ~/.alp/packages.json
Kullanılabilir paketler
.TP
.B ~/.alp/installed.json
Yüklü paketler
.TP
.B ~/.alp/config.json
Alp yapılandırması
.TP
.B ~/.alp/logs/
Alp loglama dosyaları
.SH AUTHOR
Alp Package Manager Team
.SH SEE ALSO
apt(8), pacman(8), yum(8)
MAN_EOF
    
    log_success "Man sayfası oluşturuldu"
}

create_systemd_timer() {
    log_info "Systemd timer oluşturuluyor..."
    
    cat > "$SYSTEMD_DIR/alp-update.service" << 'SYSTEMD_SERVICE'
[Unit]
Description=Alp Package Manager Update
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/alp update
StandardOutput=journal
StandardError=journal
SYSTEMD_SERVICE
    
    cat > "$SYSTEMD_DIR/alp-update.timer" << 'SYSTEMD_TIMER'
[Unit]
Description=Alp Package Manager Update Timer
Requires=alp-update.service

[Timer]
OnBootSec=5min
OnUnitActiveSec=1d
AccuracySec=12h

[Install]
WantedBy=timers.target
SYSTEMD_TIMER
    
    log_success "Systemd timer oluşturuldu"
}

setup_shell_completion() {
    log_info "Shell completion oluşturuluyor..."
    
    mkdir -p /etc/bash_completion.d
    
    cat > /etc/bash_completion.d/alp << 'COMPLETION'
_alp_completions() {
    local cur="${COMP_WORDS[COMP_CWORD]}"
    local prev="${COMP_WORDS[COMP_CWORD-1]}"
    
    local commands="update install remove upgrade list installed search info stats clean config self-update help"
    
    if [[ ${COMP_CWORD} -eq 1 ]]; then
        COMPREPLY=($(compgen -W "$commands" -- "$cur"))
    elif [[ "$prev" == "install" || "$prev" == "remove" || "$prev" == "info" || "$prev" == "upgrade" ]]; then
        # Package names
        if [ -f ~/.alp/packages.json ]; then
            local packages=$(python3 -c "import json; print(' '.join(json.load(open(open.expanduser('~/.alp/packages.json'))).keys()))" 2>/dev/null)
            COMPREPLY=($(compgen -W "$packages" -- "$cur"))
        fi
    fi
}

complete -o bashdefault -o default -o nospace -F _alp_completions alp
COMPLETION
    
    log_success "Shell completion oluşturuldu"
}

create_update_script() {
    log_info "Self-update scripti oluşturuluyor..."
    
    cat > "$INSTALL_DIR/alp_update.sh" << 'UPDATE_SCRIPT'
#!/bin/bash

# Alp Self-Update Script
# Alp'in kendisini güncelleme özelliği

set -e

INSTALL_DIR="/usr/local/lib/alp"
MANAGER_URL="https://raw.githubusercontent.com/ATOMGAMERAGA/alp-repo/refs/heads/main/alp_manager.py"
BACKUP_DIR="/tmp/alp_backup_$$"

echo -e "\033[0;36m🔄 Alp Self-Update Başlıyor...${NC}"

# Backup oluştur
echo -e "\033[1;33m→ Backup oluşturuluyor...${NC}"
mkdir -p "$BACKUP_DIR"
cp -r "$INSTALL_DIR" "$BACKUP_DIR/" 2>/dev/null || true

echo -e "\033[0;33m→ Yeni sürüm indiriliyor...${NC}"

# Yeni sürümü indir
if curl -s -L "$MANAGER_URL" -o "$INSTALL_DIR/alp_manager.py.new" 2>/dev/null; then
    chmod +x "$INSTALL_DIR/alp_manager.py.new"
    
    # Syntax kontrolü
    echo -e "\033[0;33m→ Syntax kontrol ediliyor...${NC}"
    if python3 -m py_compile "$INSTALL_DIR/alp_manager.py.new" 2>/dev/null; then
        # Eski sürümü sil, yenisini taşı
        rm -f "$INSTALL_DIR/alp_manager.py"
        mv "$INSTALL_DIR/alp_manager.py.new" "$INSTALL_DIR/alp_manager.py"
        
        # Backup'ı temizle
        rm -rf "$BACKUP_DIR"
        
        echo -e "\033[0;32m✅ Alp başarıyla güncellendi!${NC}"
        echo -e "\033[0;36mℹ️  Yeni sürüm bilgisi:${NC}"
        alp help | head -3
        exit 0
    else
        echo -e "\033[0;31m❌ Yeni sürümde syntax hatası var!${NC}"
        echo -e "\033[1;33m⚠️  Eski sürüme geri dönülüyor...${NC}"
        cp -r "$BACKUP_DIR/alp" "$INSTALL_DIR" 2>/dev/null || true
        rm -rf "$BACKUP_DIR"
        exit 1
    fi
else
    echo -e "\033[0;31m❌ Yeni sürüm indirilemedi!${NC}"
    echo -e "\033[1;33m⚠️  Eski sürüm korundu...${NC}"
    rm -rf "$BACKUP_DIR"
    exit 1
fi
UPDATE_SCRIPT
    
    chmod +x "$INSTALL_DIR/alp_update.sh"
    log_success "Self-update scripti oluşturuldu"
}

create_uninstall_script() {
    log_info "Kaldırma scripti oluşturuluyor..."
    
    cat > "$BIN_DIR/alp-uninstall" << 'UNINSTALL'
#!/bin/bash

echo -e "\033[0;31m🗑️  Alp Package Manager Kaldırılıyor...\033[0m"

# Sistemd timer'ı durdur
sudo systemctl stop alp-update.timer 2>/dev/null || true
sudo systemctl disable alp-update.timer 2>/dev/null || true
sudo rm -f /etc/systemd/system/alp-update.* 2>/dev/null || true

# Dosyaları sil
sudo rm -f /usr/local/bin/alp
sudo rm -f /usr/local/bin/alp-uninstall
sudo rm -f /usr/local/share/man/man1/alp.1.gz
sudo rm -f /etc/bash_completion.d/alp
sudo rm -rf /usr/local/lib/alp

echo -e "\033[0;32m✅ Alp başarıyla kaldırıldı\033[0m"
UNINSTALL
    
    chmod +x "$BIN_DIR/alp-uninstall"
    log_success "Kaldırma scripti oluşturuldu: alp-uninstall"
}

enable_auto_update() {
    log_info "Otomatik güncellemeler etkinleştiriliyor..."
    
    systemctl daemon-reload
    systemctl enable alp-update.timer --now 2>/dev/null || log_warning "Systemd timer etkinleştirilemedi"
    
    log_success "Otomatik güncellemeler etkinleştirildi"
}

test_installation() {
    log_info "Kurulum test ediliyor..."
    
    if ! command -v alp &> /dev/null; then
        log_error "Alp komutu bulunamadı"
        return $ERROR
    fi
    
    # Basit komut çalıştır
    if alp help &> /dev/null; then
        log_success "Kurulum başarılı"
        return $SUCCESS
    else
        log_error "Alp çalıştırılamadı"
        return $ERROR
    fi
}

# ============================================================================
# Ana Kurulum Rutini
# ============================================================================

main() {
    print_header
    
    echo ""
    check_root
    
    echo ""
    log_info "Sistem kontrol ediliyor..."
    check_python
    check_dependencies
    
    echo ""
    create_directories
    
    echo ""
    if ! download_manager; then
        log_error "Kurulum iptal edildi"
        exit $ERROR
    fi
    
    echo ""
    create_bin_wrapper
    create_man_page
    create_systemd_timer
    setup_shell_completion
    create_update_script
    create_uninstall_script
    
    echo ""
    enable_auto_update
    
    echo ""
    if test_installation; then
        echo ""
        echo -e "${BOLD}${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${BOLD}${GREEN}║         Alp Başarıyla Kuruldu! ✅                          ║${NC}"
        echo -e "${BOLD}${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
        echo ""
        echo "   📖 Hızlı Başlangıç:"
        echo ""
        echo "     alp update              # Depoyu güncelle"
        echo "     alp list                # Paketleri listele"
        echo "     alp install <paket>     # Paket yükle"
        echo ""
        echo "   📚 Daha fazla bilgi:"
        echo ""
        echo "     man alp                 # Manual sayfasını aç"
        echo "     alp help                # Yardımı göster"
        echo ""
        echo "   🗑️  Kaldırma:"
        echo ""
        echo "     sudo alp-uninstall"
        echo ""
        echo -e "${CYAN}Otomatik güncellemeler başlatılmıştır (her 24 saat)${NC}"
        echo ""
    else
        log_error "Kurulum başarısız oldu"
        exit $ERROR
    fi
}

# Kurulum başlat
main
