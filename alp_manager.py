#!/usr/bin/env python3
"""
Alp Package Manager - Advanced Linux Package Management System
GitHub entegrasyonu, bağımlılık yönetimi, otomatik güncellemeler ve sertifika sistemi
"""

import os
import sys
import json
import subprocess
import urllib.request
import urllib.error
import re
import shutil
import hashlib
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import tarfile
import tempfile
import base64
import secrets

# Renkli çıktı için ANSI kodları
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

REPO_URL = "https://github.com/ATOMGAMERAGA/alp-repo/raw/refs/heads/main/repo.alp"
ALP_HOME = Path.home() / ".alp"
ALP_CACHE = ALP_HOME / "cache"
ALP_LOGS = ALP_HOME / "logs"
PACKAGES_DB = ALP_HOME / "packages.json"
INSTALLED_DB = ALP_HOME / "installed.json"
CONFIG_FILE = ALP_HOME / "config.json"
INSTALLED_DIR = ALP_HOME / "installed"
CERTIFICATES_DB = ALP_HOME / "certificates.json"

# Official Sertifika için şifreli anahtar (SHA-256)
OFFICIAL_CERT_KEY = "cefa8faf107f512c2382150e70953e5839d882698709d6accc1ad49651732c95"  # "password" kelimesinin SHA-256 hash'i

class Logger:
    """Gelişmiş loglama sistemi"""
    def __init__(self):
        ALP_LOGS.mkdir(parents=True, exist_ok=True)
        self.log_file = ALP_LOGS / f"alp_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    def log(self, level: str, message: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry + "\n")
        if level == "ERROR":
            print(f"{Colors.RED}❌ {message}{Colors.ENDC}")
        elif level == "WARNING":
            print(f"{Colors.YELLOW}⚠️  {message}{Colors.ENDC}")
        elif level == "INFO":
            print(f"{Colors.CYAN}ℹ️  {message}{Colors.ENDC}")
        elif level == "SUCCESS":
            print(f"{Colors.GREEN}✅ {message}{Colors.ENDC}")

logger = Logger()

class CertificateManager:
    """Paket sertifika yönetim sistemi"""
    
    def __init__(self):
        self.certificates = self.load_certificates()
    
    def load_certificates(self) -> Dict:
        """Sertifika veritabanını yükle"""
        if CERTIFICATES_DB.exists():
            try:
                with open(CERTIFICATES_DB, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_certificates(self):
        """Sertifika veritabanını kaydet"""
        CERTIFICATES_DB.parent.mkdir(parents=True, exist_ok=True)
        with open(CERTIFICATES_DB, 'w') as f:
            json.dump(self.certificates, f, indent=2, ensure_ascii=False)
    
    def generate_certificate(self, package_name: str, author: str, cert_type: str = "custom") -> Dict:
        """Yeni bir sertifika oluştur"""
        cert_id = secrets.token_hex(16)
        timestamp = datetime.now().isoformat()
        
        # Sertifika verisi
        cert_data = {
            "cert_id": cert_id,
            "package_name": package_name,
            "author": author,
            "type": cert_type,  # "custom" veya "official"
            "issued_at": timestamp,
            "signature": self._generate_signature(package_name, author, timestamp)
        }
        
        return cert_data
    
    def _generate_signature(self, package_name: str, author: str, timestamp: str) -> str:
        """Sertifika imzası oluştur"""
        data = f"{package_name}|{author}|{timestamp}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    def verify_certificate(self, cert_data: Dict) -> Tuple[bool, str]:
        """Sertifika doğrulama"""
        if not cert_data:
            return False, "Sertifika bulunamadı"
        
        # İmza doğrulama
        expected_sig = self._generate_signature(
            cert_data.get("package_name", ""),
            cert_data.get("author", ""),
            cert_data.get("issued_at", "")
        )
        
        if cert_data.get("signature") != expected_sig:
            return False, "Sertifika imzası geçersiz"
        
        # Sertifika tipine göre doğrulama
        if cert_data.get("type") == "official":
            return True, "Official Alp Sertifikalı Paket ✓"
        else:
            return True, f"Sertifikalı Paket - {cert_data.get('author')} tarafından imzalanmış ✓"
    
    def register_certificate(self, package_name: str, cert_data: Dict):
        """Sertifikayı kaydet"""
        self.certificates[package_name] = cert_data
        self.save_certificates()
    
    def get_certificate(self, package_name: str) -> Optional[Dict]:
        """Paket sertifikasını getir"""
        return self.certificates.get(package_name)
    
    def show_certificate_info(self, package_name: str):
        """Sertifika bilgilerini göster"""
        cert = self.get_certificate(package_name)
        
        if not cert:
            print(f"{Colors.RED}⚠️  Bu paket sertifikalı değil!{Colors.ENDC}")
            print(f"{Colors.YELLOW}   Paketin nereden geldiği belirsiz ve güvenli olmayabilir.{Colors.ENDC}")
            return
        
        is_valid, message = self.verify_certificate(cert)
        
        if not is_valid:
            print(f"{Colors.RED}⚠️  Sertifika geçersiz: {message}{Colors.ENDC}")
            return
        
        print(f"\n{Colors.BOLD}{Colors.GREEN}🔒 Sertifika Bilgileri{Colors.ENDC}")
        print(f"{Colors.BOLD}{'-' * 60}{Colors.ENDC}")
        
        if cert.get("type") == "official":
            print(f"{Colors.GREEN}  🏆 Official Alp Certified Package{Colors.ENDC}")
            print(f"{Colors.CYAN}  Bu paket resmi olarak Alp tarafından onaylanmıştır{Colors.ENDC}")
        else:
            print(f"{Colors.CYAN}  ✓ Sertifikalı Paket{Colors.ENDC}")
        
        print(f"\n  {Colors.BOLD}Sertifika ID:{Colors.ENDC} {cert.get('cert_id')}")
        print(f"  {Colors.BOLD}Paket Adı:{Colors.ENDC} {cert.get('package_name')}")
        print(f"  {Colors.BOLD}Yazar:{Colors.ENDC} {cert.get('author')}")
        print(f"  {Colors.BOLD}Düzenlenme Tarihi:{Colors.ENDC} {cert.get('issued_at')[:10]}")
        print(f"  {Colors.BOLD}İmza:{Colors.ENDC} {cert.get('signature')[:32]}...")
        print(f"\n{Colors.GREEN}  ✓ Sertifika doğrulandı: {message}{Colors.ENDC}")
        print(f"{Colors.BOLD}{'-' * 60}{Colors.ENDC}\n")

    def generate_alpc_file(self, package_name: str, author: str, cert_type: str) -> Dict:
        """cerf.alpc içeriğini üret (official/dev/normal)"""
        ts = datetime.now().isoformat()
        token = secrets.token_hex(16)
        cert_type = cert_type.lower()
        if cert_type not in ["official", "dev", "normal"]:
            cert_type = "normal"
        data = {
            "format": "alpc-1.0",
            "magic": "ALP-CERF",
            "package": package_name,
            "author": author,
            "type": cert_type,
            "issued_at": ts,
            "token": token,
        }
        data["signature"] = self._generate_alpc_signature(
            data["package"], data["author"], data["type"], data["issued_at"], data["token"]
        )
        return data

    def _generate_alpc_signature(self, package_name: str, author: str, cert_type: str, issued_at: str, token: str) -> str:
        """cerf.alpc imzası"""
        raw = f"{package_name}|{author}|{cert_type}|{issued_at}|{token}|ALP-CERF"
        return hashlib.sha256(raw.encode()).hexdigest()

    def verify_alpc(self, alpc: Dict) -> Tuple[bool, str]:
        """cerf.alpc doğrulaması"""
        required = ["format", "magic", "package", "author", "type", "issued_at", "token", "signature"]
        if not all(k in alpc for k in required):
            return False, "Eksik alanlar"
        if alpc.get("magic") != "ALP-CERF":
            return False, "Geçersiz magic"
        sig = self._generate_alpc_signature(
            alpc.get("package", ""),
            alpc.get("author", ""),
            alpc.get("type", ""),
            alpc.get("issued_at", ""),
            alpc.get("token", "")
        )
        if sig != alpc.get("signature"):
            return False, "İmza uyuşmuyor"
        t = alpc.get("type")
        if t == "official":
            return True, "Official Alp Sertifikası"
        elif t == "dev":
            return True, "Geliştirici Sertifikası"
        else:
            return True, "Normal Sertifika"

class Config:
    """Yapılandırma yönetimi"""
    DEFAULT_CONFIG = {
        "auto_update": True,
        "update_interval": 3600,
        "cache_size": 1000,
        "verify_packages": True,
        "parallel_install": False,
        "check_dependencies": True,
        "keep_cache": False
    }
    
    def __init__(self):
        self.config = self.load()
    
    def load(self):
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except:
                return self.DEFAULT_CONFIG.copy()
        return self.DEFAULT_CONFIG.copy()
    
    def save(self):
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def get(self, key, default=None):
        return self.config.get(key, default)
    
    def set(self, key, value):
        self.config[key] = value
        self.save()

class PackageManager:
    def __init__(self):
        self.config = Config()
        self.cert_manager = CertificateManager()
        self.setup_home()
        self.packages = {}
        self.installed = {}
        self.load_databases()
    
    def setup_home(self):
        """Alp dizin yapısını oluştur"""
        ALP_HOME.mkdir(parents=True, exist_ok=True)
        ALP_CACHE.mkdir(parents=True, exist_ok=True)
        ALP_LOGS.mkdir(parents=True, exist_ok=True)
        INSTALLED_DIR.mkdir(parents=True, exist_ok=True)
        logger.log("INFO", "Dizin yapısı oluşturuldu")
        
    def fetch_url(self, url: str, timeout: int = 30) -> Optional[str]:
        """URL'den içerik indir"""
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Alp-PackageManager/1.0'
            })
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return response.read().decode('utf-8')
        except urllib.error.URLError as e:
            logger.log("ERROR", f"URL indirilemedi: {url} - {e}")
            return None
        except Exception as e:
            logger.log("ERROR", f"Bağlantı hatası: {e}")
            return None
    
    def download_file(self, url: str, filepath: Path) -> bool:
        """Dosya indir ve cache'e kaydet"""
        try:
            filepath.parent.mkdir(parents=True, exist_ok=True)
            urllib.request.urlretrieve(url, filepath)
            logger.log("INFO", f"Dosya indirildi: {filepath.name}")
            return True
        except Exception as e:
            logger.log("ERROR", f"Dosya indirilemedi: {e}")
            return False
    
    def calculate_checksum(self, filepath: Path) -> str:
        """Dosya checksum'ı hesapla"""
        sha256 = hashlib.sha256()
        with open(filepath, 'rb') as f:
            sha256.update(f.read())
        return sha256.hexdigest()
    
    def parse_readme(self, github_url: str) -> Optional[Dict]:
        """GitHub URL'sinden README.md'yi indir ve parse et"""
        github_url = github_url.rstrip('/')
        
        if '/tree/main' in github_url:
            github_url = github_url.replace('/tree/main', '')
        
        readme_url = github_url.replace("github.com", "raw.githubusercontent.com") + "/refs/heads/main/README.md"
        
        content = self.fetch_url(readme_url)
        if not content:
            readme_url_master = github_url.replace("github.com", "raw.githubusercontent.com") + "/refs/heads/master/README.md"
            content = self.fetch_url(readme_url_master)
            if not content:
                logger.log("WARNING", f"README.md bulunamadı: {github_url}")
                return None
        
        return self.extract_metadata(content)
    
    def extract_metadata(self, content: str) -> Dict:
        """README.md'den metadata çıkar"""
        metadata = {}
        
        patterns = {
            'name': r'name\s*=\s*([^\n\s]+)',
            'description': r'des\s*=\s*(.+?)(?:\n|$)',
            'version': r'ver\s*=\s*([^\n\s]+)',
            'author': r'author\s*=\s*([^\n\s]+)',
            'license': r'license\s*=\s*([^\n\s]+)',
            'dependencies': r'deps\s*=\s*\[(.+?)\]',
            'category': r'category\s*=\s*([^\n\s]+)',
            'main': r'main\s*=\s*([^\n\s]+)',
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, content)
            if match:
                value = match.group(1).strip()
                if key == 'dependencies':
                    metadata[key] = [d.strip() for d in value.split(',')]
                else:
                    metadata[key] = value
        
        return metadata

    def parse_cert_alpc(self, github_url: str) -> Optional[Dict]:
        """GitHub repo kökünden cerf.alpc dosyasını indir ve doğrula"""
        base = github_url.rstrip('/')
        if '/tree/main' in base:
            base = base.replace('/tree/main', '')
        raw_main = base.replace('github.com', 'raw.githubusercontent.com') + '/refs/heads/main/cerf.alpc'
        raw_master = base.replace('github.com', 'raw.githubusercontent.com') + '/refs/heads/master/cerf.alpc'
        content = self.fetch_url(raw_main) or self.fetch_url(raw_master)
        if not content:
            return None
        try:
            alpc = json.loads(content)
        except Exception:
            logger.log("WARNING", f"cerf.alpc geçersiz JSON: {github_url}")
            return None
        is_valid, msg = self.cert_manager.verify_alpc(alpc)
        return {
            'cert_type': alpc.get('type'),
            'cert_author': alpc.get('author'),
            'cert_valid': is_valid,
            'cert_message': msg
        }
    
    def compile_package(self, directory: str, add_certificate: bool = True) -> bool:
        """Paket dizinini .alp dosyasına derle ve sertifikala"""
        dir_path = Path(directory)
        
        if not dir_path.exists() or not dir_path.is_dir():
            logger.log("ERROR", f"Dizin bulunamadı: {directory}")
            return False
        
        # Gerekli dosyaları kontrol et
        alp_sh = dir_path / "alp.sh"
        alp_u_sh = dir_path / "alp_u.sh"
        readme = dir_path / "README.md"
        
        missing_files = []
        if not alp_sh.exists():
            missing_files.append("alp.sh")
        if not alp_u_sh.exists():
            missing_files.append("alp_u.sh")
        if not readme.exists():
            missing_files.append("README.md")
        
        if missing_files:
            logger.log("ERROR", f"Eksik dosyalar: {', '.join(missing_files)}")
            return False
        
        # README'den metadata çıkar
        with open(readme, 'r', encoding='utf-8') as f:
            readme_content = f.read()
        
        metadata = self.extract_metadata(readme_content)
        
        if 'name' not in metadata or 'version' not in metadata:
            logger.log("ERROR", "README.md'de 'name' ve 'ver' alanları zorunludur!")
            print(f"{Colors.YELLOW}Örnek README.md formatı:{Colors.ENDC}")
            print("name = myapp")
            print("ver = 1.0.0")
            print("des = Uygulama açıklaması")
            print("author = Sizin İsminiz")
            print("main = myapp.py  (opsiyonel)")
            return False
        
        package_name = metadata['name']
        version = metadata['version']
        author = metadata.get('author', 'Unknown')
        output_file = Path.cwd() / f"{package_name}-{version}.alp"
        
        print(f"{Colors.BOLD}{Colors.CYAN}📦 Paket derleniyor: {package_name} v{version}{Colors.ENDC}")
        
        # Sertifika işlemleri
        certificate = None
        if add_certificate:
            print(f"\n{Colors.BOLD}{Colors.YELLOW}🔒 Sertifika Sistemi{Colors.ENDC}")
            print(f"{Colors.CYAN}Bu paketin sertifikalanmasını ister misiniz?{Colors.ENDC}")
            print(f"{Colors.YELLOW}Sertifikasız paketler kurulurken uyarı verir ve nereden geldiği belli olmaz.{Colors.ENDC}")
            
            cert_choice = input(f"\n1) Özel Sertifika (Kendi isminizle)\n2) Official Alp Sertifikası (Şifre gerekli)\n3) Sertifikasız\n\nSeçiminiz (1/2/3): ").strip()
            
            if cert_choice == "1":
                author_name = input(f"İmzalayan kişinin adı [{author}]: ").strip() or author
                certificate = self.cert_manager.generate_certificate(package_name, author_name, "custom")
                print(f"{Colors.GREEN}✓ Özel sertifika oluşturuldu{Colors.ENDC}")
            
            elif cert_choice == "2":
                password = input("Official sertifika şifresini girin: ").strip()
                password_hash = hashlib.sha256(password.encode()).hexdigest()
                
                if password_hash == OFFICIAL_CERT_KEY:
                    certificate = self.cert_manager.generate_certificate(package_name, "Alp Official", "official")
                    print(f"{Colors.GREEN}✓ Official Alp sertifikası oluşturuldu 🏆{Colors.ENDC}")
                else:
                    print(f"{Colors.RED}✗ Hatalı şifre! Sertifikasız devam ediliyor.{Colors.ENDC}")
        
        # Dosyaları oku ve base64 encode et
        try:
            with open(alp_sh, 'rb') as f:
                install_script = base64.b64encode(f.read()).decode('utf-8')
            
            with open(alp_u_sh, 'rb') as f:
                uninstall_script = base64.b64encode(f.read()).decode('utf-8')
            
            # Ana dosyayı kontrol et (opsiyonel)
            main_file_content = None
            main_file_name = None
            if 'main' in metadata:
                main_file = dir_path / metadata['main']
                if main_file.exists():
                    with open(main_file, 'rb') as f:
                        main_file_content = base64.b64encode(f.read()).decode('utf-8')
                    main_file_name = metadata['main']
                    print(f"{Colors.GREEN}✓{Colors.ENDC} Ana dosya bulundu: {main_file_name}")
                else:
                    logger.log("WARNING", f"Ana dosya bulunamadı: {metadata['main']}")
            
            # .alp paketi oluştur (JSON formatı)
            alp_package = {
                "format_version": "1.2",
                "metadata": metadata,
                "files": {
                    "install_script": install_script,
                    "uninstall_script": uninstall_script,
                    "readme": readme_content
                },
                "certificate": certificate,
                "compiled_at": datetime.now().isoformat(),
                "checksum": ""
            }
            
            # Ana dosya varsa ekle
            if main_file_content and main_file_name:
                alp_package["files"]["main_file"] = main_file_content
                alp_package["files"]["main_file_name"] = main_file_name
            
            # JSON'u string'e çevir
            package_json = json.dumps(alp_package, indent=2, ensure_ascii=False)
            
            # Checksum hesapla
            checksum = hashlib.sha256(package_json.encode()).hexdigest()
            alp_package["checksum"] = checksum
            
            # Dosyaya yaz
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(alp_package, f, indent=2, ensure_ascii=False)
            
            file_size = output_file.stat().st_size / 1024
            
            logger.log("SUCCESS", f"Paket oluşturuldu: {output_file.name}")
            print(f"\n{Colors.GREEN}✓{Colors.ENDC} Dosya: {output_file}")
            print(f"{Colors.GREEN}✓{Colors.ENDC} Boyut: {file_size:.2f} KB")
            print(f"{Colors.GREEN}✓{Colors.ENDC} Checksum: {checksum[:16]}...")
            
            if certificate:
                if certificate.get("type") == "official":
                    print(f"{Colors.GREEN}✓{Colors.ENDC} Sertifika: {Colors.BOLD}Official Alp Certified 🏆{Colors.ENDC}")
                else:
                    print(f"{Colors.GREEN}✓{Colors.ENDC} Sertifika: Özel ({certificate.get('author')})")
            else:
                print(f"{Colors.YELLOW}⚠{Colors.ENDC}  Sertifika: Yok (Kurulumda uyarı verilecek)")
            
            if main_file_name:
                print(f"{Colors.GREEN}✓{Colors.ENDC} Ana dosya: {main_file_name}")
            print(f"\n{Colors.BOLD}Kurulum:{Colors.ENDC} alp install-local {output_file}")
            
            return True
            
        except Exception as e:
            logger.log("ERROR", f"Paket derlenemedi: {e}")
            return False
    
    def create_alpc(self, package_name: str, author: str, cert_type: str) -> bool:
        """Mevcut dizinde cerf.alpc oluştur"""
        cert_type = cert_type.lower()
        if cert_type == 'official':
            pwd = input("Official sertifika şifresi: ").strip()
            if hashlib.sha256(pwd.encode()).hexdigest() != OFFICIAL_CERT_KEY:
                print(f"{Colors.RED}✗ Hatalı şifre!{Colors.ENDC}")
                return False
            author = "Alp Official"
        data = self.cert_manager.generate_alpc_file(package_name, author, cert_type)
        out = Path.cwd() / 'cerf.alpc'
        try:
            with open(out, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.log("SUCCESS", f"cerf.alpc oluşturuldu: {out}")
            icon = "🏆" if data.get('type') == 'official' else ("🔧" if data.get('type') == 'dev' else "👤")
            print(f"{Colors.GREEN}✓{Colors.ENDC} Tür: {data.get('type')} {icon}")
            print(f"{Colors.GREEN}✓{Colors.ENDC} Yazar: {data.get('author')}")
            print(f"{Colors.GREEN}✓{Colors.ENDC} İmza: {data.get('signature')[:16]}...")
            return True
        except Exception as e:
            logger.log("ERROR", f"cerf.alpc yazılamadı: {e}")
            return False

    def scan_alpc_repo(self, github_url: str) -> bool:
        """GitHub repo için cerf.alpc taraması ve çıktı"""
        info = self.parse_cert_alpc(github_url)
        if not info:
            print(f"{Colors.YELLOW}⚠️  cerf.alpc bulunamadı ya da erişilemedi{Colors.ENDC}")
            return False
        icon = "🏆" if info.get('cert_type') == 'official' else ("🔧" if info.get('cert_type') == 'dev' else "👤")
        status = f"{Colors.GREEN}✓ Geçerli{Colors.ENDC}" if info.get('cert_valid') else f"{Colors.RED}✗ Geçersiz{Colors.ENDC}"
        print(f"\n{Colors.BOLD}{Colors.CYAN}🔎 Sertifika Taraması{Colors.ENDC}")
        print(f"{Colors.BOLD}{'-' * 60}{Colors.ENDC}")
        print(f"  Tür: {info.get('cert_type')} {icon}")
        print(f"  Yazar: {info.get('cert_author')}")
        print(f"  Durum: {status} - {info.get('cert_message')}")
        print(f"{Colors.BOLD}{'-' * 60}{Colors.ENDC}\n")
        return info.get('cert_valid', False)

    def install_local_package(self, alp_file: str) -> bool:
        """Yerel .alp dosyasını kur"""
        alp_path = Path(alp_file)
        
        if not alp_path.exists():
            logger.log("ERROR", f".alp dosyası bulunamadı: {alp_file}")
            return False
        
        if not alp_path.suffix == '.alp':
            logger.log("ERROR", "Dosya uzantısı .alp olmalıdır")
            return False
        
        try:
            # .alp dosyasını oku
            with open(alp_path, 'r', encoding='utf-8') as f:
                alp_package = json.load(f)
            
            # Format kontrolü
            format_version = alp_package.get("format_version", "1.0")
            if format_version not in ["1.0", "1.1", "1.2"]:
                logger.log("ERROR", "Desteklenmeyen paket formatı")
                return False
            
            metadata = alp_package["metadata"]
            package_name = metadata["name"]
            version = metadata.get("version", "unknown")
            
            # Sertifika kontrolü
            certificate = alp_package.get("certificate")
            
            print(f"{Colors.BOLD}{Colors.BLUE}📥 Yükleniyor: {package_name} ({version}){Colors.ENDC}\n")
            
            if certificate:
                is_valid, message = self.cert_manager.verify_certificate(certificate)
                if is_valid:
                    if certificate.get("type") == "official":
                        print(f"{Colors.GREEN}🏆 Official Alp Certified Package{Colors.ENDC}")
                    else:
                        print(f"{Colors.GREEN}🔒 Sertifikalı Paket - {certificate.get('author')}{Colors.ENDC}")
                    print(f"{Colors.CYAN}   {message}{Colors.ENDC}\n")
                else:
                    print(f"{Colors.RED}⚠️  Sertifika doğrulaması başarısız: {message}{Colors.ENDC}")
                    response = input("Yine de devam etmek istiyor musunuz? (e/h): ")
                    if response.lower() != 'e':
                        return False
            else:
                print(f"{Colors.YELLOW}⚠️  Bu paket sertifikalı değil!{Colors.ENDC}")
                print(f"{Colors.YELLOW}   Paketin nereden geldiği belirsiz ve güvenli olmayabilir.{Colors.ENDC}")
                response = input(f"{Colors.YELLOW}   Yine de kurmak istiyor musunuz? (e/h): {Colors.ENDC}")
                if response.lower() != 'e':
                    return False
                print()
            
            # Zaten yüklü mü kontrol et
            if package_name in self.installed:
                logger.log("WARNING", f"Paket zaten yüklü: {package_name}")
                response = input(f"Yeniden yüklemek ister misiniz? (e/h): ")
                if response.lower() != 'e':
                    return False
                self.remove(package_name)
            
            # Geçici dizin oluştur
            temp_dir = ALP_CACHE / f"install_{package_name}"
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            # Scriptleri decode et ve kaydet
            install_script = temp_dir / "alp.sh"
            uninstall_script = temp_dir / "alp_u.sh"
            
            install_data = base64.b64decode(alp_package["files"]["install_script"])
            uninstall_data = base64.b64decode(alp_package["files"]["uninstall_script"])
            
            with open(install_script, 'wb') as f:
                f.write(install_data)
            
            with open(uninstall_script, 'wb') as f:
                f.write(uninstall_data)
            
            # Ana dosyayı çıkar (varsa)
            main_file_path = None
            if "main_file" in alp_package["files"] and "main_file_name" in alp_package["files"]:
                main_file_name = alp_package["files"]["main_file_name"]
                main_file_data = base64.b64decode(alp_package["files"]["main_file"])
                main_file_path = temp_dir / main_file_name
                
                with open(main_file_path, 'wb') as f:
                    f.write(main_file_data)
                
                # Dosya uzantısına göre izinleri ayarla
                if main_file_name.endswith('.sh') or main_file_name.endswith('.py'):
                    os.chmod(main_file_path, 0o755)
                
                print(f"{Colors.GREEN}✓{Colors.ENDC} Ana dosya çıkarıldı: {main_file_name}")
            
            # İzinleri ayarla
            os.chmod(install_script, 0o755)
            os.chmod(uninstall_script, 0o755)
            
            # Ana dosya yolunu environment variable olarak belirt
            env = os.environ.copy()
            if main_file_path:
                env['ALP_MAIN_FILE'] = str(main_file_path)
                env['ALP_MAIN_NAME'] = main_file_path.name
            
            # Kurulum scriptini çalıştır
            print(f"{Colors.YELLOW}→ Kurulum scripti çalıştırılıyor...{Colors.ENDC}")
            result = subprocess.run(
                [str(install_script)],
                capture_output=True,
                text=True,
                timeout=300,
                env=env
            )
            
            if result.returncode == 0:
                # Paket dizinini oluştur
                pkg_dir = INSTALLED_DIR / package_name
                pkg_dir.mkdir(parents=True, exist_ok=True)
                
                # Uninstall scriptini kopyala
                shutil.copy2(uninstall_script, pkg_dir / "alp_u.sh")
                
                # Ana dosyayı kopyala (varsa)
                if main_file_path and main_file_path.exists():
                    shutil.copy2(main_file_path, pkg_dir / main_file_path.name)
                
                # README'yi kaydet
                with open(pkg_dir / "README.md", 'w', encoding='utf-8') as f:
                    f.write(alp_package["files"]["readme"])
                
                # Metadata kaydet
                install_info = {
                    **metadata,
                    'installed_at': datetime.now().isoformat(),
                    'source': 'local',
                    'alp_file': str(alp_path.absolute()),
                    'checksum': alp_package.get("checksum", ""),
                    'certified': certificate is not None,
                    'cert_type': certificate.get("type") if certificate else None
                }
                
                with open(pkg_dir / "installed.json", 'w') as f:
                    json.dump(install_info, f, indent=2)
                
                # Sertifikayı kaydet
                if certificate:
                    self.cert_manager.register_certificate(package_name, certificate)
                
                # Veritabanını güncelle
                self.installed[package_name] = install_info
                self.save_installed()
                
                # Geçici dosyaları temizle
                shutil.rmtree(temp_dir, ignore_errors=True)
                
                logger.log("SUCCESS", f"{package_name} başarıyla yüklendi")
                
                # Ana dosya kurulduysa bilgi ver
                if 'main' in metadata:
                    print(f"\n{Colors.CYAN}ℹ️  Ana program: {metadata['main']}{Colors.ENDC}")
                    if metadata['main'].endswith('.py'):
                        print(f"{Colors.YELLOW}   Çalıştırmak için: python3 {metadata['main']}{Colors.ENDC}")
                    elif metadata['main'].endswith('.sh'):
                        print(f"{Colors.YELLOW}   Çalıştırmak için: ./{metadata['main']}{Colors.ENDC}")
                
                return True
            else:
                logger.log("ERROR", f"Kurulum başarısız: {result.stderr}")
                shutil.rmtree(temp_dir, ignore_errors=True)
                return False
                
        except json.JSONDecodeError:
            logger.log("ERROR", "Geçersiz .alp dosya formatı")
            return False
        except Exception as e:
            logger.log("ERROR", f"Kurulum hatası: {e}")
            return False
    
    def update_repo(self, force: bool = False) -> bool:
        """Depoyu güncelle"""
        if not force and INSTALLED_DB.exists():
            stat = INSTALLED_DB.stat()
            if time.time() - stat.st_mtime < self.config.get("update_interval"):
                logger.log("INFO", "Depo zaten güncellidir")
                return True
        
        print(f"{Colors.BOLD}{Colors.CYAN}📦 Depo güncelleniyor...{Colors.ENDC}")
        repo_content = self.fetch_url(REPO_URL)
        if not repo_content:
            logger.log("ERROR", "Depo güncellenemedi")
            return False
        
        self.packages = {}
        valid_count = 0
        
        for line in repo_content.strip().split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                metadata = self.parse_readme(line)
                if metadata and 'name' in metadata:
                    metadata['url'] = line
                    metadata['added_date'] = datetime.now().isoformat()
                    # cerf.alpc tara
                    cert_info = self.parse_cert_alpc(line)
                    if cert_info:
                        metadata.update(cert_info)
                    self.packages[metadata['name']] = metadata
                    valid_count += 1
        
        self.save_packages()
        logger.log("SUCCESS", f"Depo güncellendi: {valid_count} paket bulundu")
        return True
    
    def check_dependencies(self, package_name: str) -> Tuple[bool, List[str]]:
        """Bağımlılıkları kontrol et"""
        if package_name not in self.packages:
            return False, []
        
        pkg = self.packages[package_name]
        deps = pkg.get('dependencies', [])
        missing = []
        
        for dep in deps:
            if dep not in self.installed:
                missing.append(dep)
        
        return len(missing) == 0, missing
    
    def resolve_dependencies(self, package_name: str) -> List[str]:
        """Bağımlılıkları çöz ve kurulum sırasını belirle"""
        install_order = []
        visited = set()
        
        def dfs(pkg_name):
            if pkg_name in visited:
                return
            visited.add(pkg_name)
            
            if pkg_name in self.packages:
                deps = self.packages[pkg_name].get('dependencies', [])
                for dep in deps:
                    dfs(dep)
            
            install_order.append(pkg_name)
        
        dfs(package_name)
        return install_order
    
    def install(self, package_name: str, install_deps: bool = True) -> bool:
        """Paket yükle"""
        if package_name in self.installed:
            logger.log("WARNING", f"Paket zaten yüklü: {package_name}")
            return True
        
        if package_name not in self.packages:
            logger.log("ERROR", f"Paket bulunamadı: {package_name}")
            self.search(package_name)
            return False
        
        if install_deps:
            install_order = self.resolve_dependencies(package_name)
            for pkg in install_order[:-1]:
                if pkg not in self.installed:
                    print(f"{Colors.YELLOW}→ Bağımlılık yükleniyor: {pkg}{Colors.ENDC}")
                    if not self.install(pkg, install_deps=False):
                        logger.log("ERROR", f"Bağımlılık yüklenemedi: {pkg}")
                        return False
        
        pkg = self.packages[package_name]
        print(f"{Colors.BOLD}{Colors.BLUE}📥 Yükleniyor: {package_name} ({pkg.get('version', 'v?')}){Colors.ENDC}")
        
        pkg_dir = INSTALLED_DIR / package_name
        pkg_dir.mkdir(parents=True, exist_ok=True)
        
        base_url = pkg['url'].rstrip('/')
        if '/tree/main' in base_url:
            base_url = base_url.replace('/tree/main', '')
        
        raw_url = base_url.replace('github.com', 'raw.githubusercontent.com') + '/refs/heads/main/alp.sh'
        script_path = ALP_CACHE / f"{package_name}_install.sh"
        
        logger.log("INFO", f"Kurulum scripti indiriliyor: {raw_url}")
        
        if not self.download_file(raw_url, script_path):
            logger.log("ERROR", f"Kurulum scripti indirilemedi: {package_name}")
            return False
        
        try:
            os.chmod(script_path, 0o755)
            result = subprocess.run(
                [str(script_path)],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                install_info = {
                    **pkg,
                    'installed_at': datetime.now().isoformat(),
                    'checksum': self.calculate_checksum(script_path)
                }
                with open(pkg_dir / "installed.json", 'w') as f:
                    json.dump(install_info, f, indent=2)
                
                self.installed[package_name] = install_info
                self.save_installed()
                logger.log("SUCCESS", f"{package_name} başarıyla yüklendi")
                return True
            else:
                logger.log("ERROR", f"Kurulum başarısız: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            logger.log("ERROR", f"Kurulum zaman aşımı: {package_name}")
            return False
        except Exception as e:
            logger.log("ERROR", f"Kurulum hatası: {e}")
            return False
    
    def remove(self, package_name: str, remove_deps: bool = False) -> bool:
        """Paket kaldır"""
        pkg_dir = INSTALLED_DIR / package_name
        
        if not pkg_dir.exists():
            logger.log("ERROR", f"Paket yüklü değil: {package_name}")
            return False
        
        print(f"{Colors.BOLD}{Colors.RED}🗑️  Kaldırılıyor: {package_name}{Colors.ENDC}")
        
        if package_name in self.packages:
            pkg = self.packages[package_name]
            
            base_url = pkg['url'].rstrip('/')
            if '/tree/main' in base_url:
                base_url = base_url.replace('/tree/main', '')
            
            raw_url = base_url.replace('github.com', 'raw.githubusercontent.com') + '/refs/heads/main/alp_u.sh'
            uninstall_path = ALP_CACHE / f"{package_name}_uninstall.sh"
            
            if self.download_file(raw_url, uninstall_path):
                try:
                    os.chmod(uninstall_path, 0o755)
                    result = subprocess.run(
                        [str(uninstall_path)],
                        capture_output=True,
                        text=True,
                        timeout=300
                    )
                    if result.returncode != 0:
                        logger.log("WARNING", f"Kaldırma scripti hata verdi: {result.stderr}")
                except Exception as e:
                    logger.log("WARNING", f"Kaldırma scripti çalıştırılamadı: {e}")
        
        shutil.rmtree(pkg_dir, ignore_errors=True)
        
        if package_name in self.installed:
            del self.installed[package_name]
            self.save_installed()
        
        logger.log("SUCCESS", f"{package_name} kaldırıldı")
        return True
    
    def upgrade(self, package_name: Optional[str] = None) -> bool:
        """Paket güncelle"""
        if package_name:
            if package_name not in self.installed:
                logger.log("ERROR", f"Paket yüklü değil: {package_name}")
                return False
            packages_to_upgrade = [package_name]
        else:
            packages_to_upgrade = list(self.installed.keys())
        
        print(f"{Colors.BOLD}{Colors.YELLOW}🔄 Güncellemeler kontrol ediliyor...{Colors.ENDC}")
        
        updated_count = 0
        for pkg_name in packages_to_upgrade:
            if pkg_name not in self.packages:
                continue
            
            installed_ver = self.installed[pkg_name].get('version', '0')
            available_ver = self.packages[pkg_name].get('version', '0')
            
            if self.compare_versions(available_ver, installed_ver) > 0:
                print(f"{Colors.YELLOW}→ Güncelleniyor: {pkg_name} {installed_ver} → {available_ver}{Colors.ENDC}")
                if self.remove(pkg_name) and self.install(pkg_name):
                    updated_count += 1
        
        logger.log("SUCCESS", f"{updated_count} paket güncellendi")
        return True
    
    def compare_versions(self, v1: str, v2: str) -> int:
        """Versiyon karşılaştırması (-1: v1<v2, 0: eşit, 1: v1>v2)"""
        def normalize(v):
            return [int(x) for x in re.sub(r'(\.0+)*$', '', v).split(".")]
        try:
            v1_parts = normalize(v1)
            v2_parts = normalize(v2)
            if v1_parts > v2_parts:
                return 1
            elif v1_parts < v2_parts:
                return -1
            return 0
        except:
            return 0
    
    def list_packages(self, category: Optional[str] = None) -> None:
        """Paketleri listele"""
        if not self.packages:
            logger.log("ERROR", "Paket bulunamadı. 'alp update' çalıştırın")
            return
        
        packages_to_show = self.packages
        if category:
            packages_to_show = {k: v for k, v in self.packages.items() 
                               if v.get('category') == category}
        
        print(f"\n{Colors.BOLD}{Colors.CYAN}📦 Mevcut Paketler:{Colors.ENDC}")
        print(f"{Colors.BOLD}{'-' * 80}{Colors.ENDC}")
        
        for name, pkg in sorted(packages_to_show.items()):
            ver = pkg.get('version', '?')
            des = pkg.get('description', 'Açıklama yok')[:50]
            cat = pkg.get('category', 'misc')
            status = "✅" if (INSTALLED_DIR / name).exists() else "⭕"
            # Sertifika rozetleri
            cert_icon = ""
            if pkg.get('cert_type') and pkg.get('cert_valid'):
                if pkg['cert_type'] == 'official':
                    cert_icon = f" {Colors.GREEN}🏆{Colors.ENDC}"
                elif pkg['cert_type'] == 'dev':
                    cert_icon = f" {Colors.CYAN}🔧{Colors.ENDC}"
                elif pkg['cert_type'] == 'normal':
                    cert_icon = f" {Colors.CYAN}👤{Colors.ENDC}"
            
            print(f"{status} {Colors.BOLD}{name}{Colors.ENDC:24} ({ver:8}) {Colors.CYAN}[{cat}]{Colors.ENDC}{cert_icon}")
            print(f"   └─ {des}...")
        
        print(f"{Colors.BOLD}{'-' * 80}{Colors.ENDC}")
        installed_count = len([k for k in self.packages.keys() if (INSTALLED_DIR / k).exists()])
        print(f"{Colors.GREEN}✅ Yüklü: {installed_count}/{len(packages_to_show)}{Colors.ENDC}\n")
    
    def list_installed(self) -> None:
        """Yüklü paketleri listele"""
        if not self.installed:
            logger.log("INFO", "Hiçbir paket yüklü değil")
            return
        
        print(f"\n{Colors.BOLD}{Colors.GREEN}✅ Yüklü Paketler:{Colors.ENDC}")
        print(f"{Colors.BOLD}{'-' * 80}{Colors.ENDC}")
        
        for name, info in sorted(self.installed.items()):
            ver = info.get('version', '?')
            installed_at = info.get('installed_at', '?')
            size = sum(f.stat().st_size for f in (INSTALLED_DIR / name).rglob('*') if f.is_file()) / 1024 / 1024
            
            # Sertifika durumu
            cert_icon = ""
            if info.get('certified'):
                if info.get('cert_type') == 'official':
                    cert_icon = f" {Colors.GREEN}🏆{Colors.ENDC}"
                else:
                    cert_icon = f" {Colors.CYAN}🔒{Colors.ENDC}"
            
            print(f"{Colors.GREEN}✓{Colors.ENDC} {Colors.BOLD}{name}{Colors.ENDC:24} {ver:8} ({size:.2f}MB){cert_icon}")
            print(f"   └─ Yükleme tarihi: {installed_at[:10]}")
        
        print(f"{Colors.BOLD}{'-' * 80}{Colors.ENDC}\n")
    
    def search(self, keyword: str) -> None:
        """Paket ara"""
        results = {name: pkg for name, pkg in self.packages.items() 
                   if keyword.lower() in name.lower() or 
                   keyword.lower() in pkg.get('description', '').lower()}
        
        if not results:
            logger.log("ERROR", f"'{keyword}' ile eşleşen paket bulunamadı")
            return
        
        print(f"\n{Colors.BOLD}{Colors.CYAN}🔍 '{keyword}' için arama sonuçları:{Colors.ENDC}")
        print(f"{Colors.BOLD}{'-' * 80}{Colors.ENDC}")
        
        for name, pkg in sorted(results.items()):
            ver = pkg.get('version', '?')
            des = pkg.get('description', 'Açıklama yok')[:60]
            status = "✅" if (INSTALLED_DIR / name).exists() else "⭕"
            
            print(f"{status} {Colors.BOLD}{name}{Colors.ENDC:24} {ver:8} - {des}")
        
        print(f"{Colors.BOLD}{'-' * 80}{Colors.ENDC}\n")
    
    def show_info(self, package_name: str) -> None:
        """Paket detaylarını göster"""
        if package_name not in self.packages:
            logger.log("ERROR", f"Paket bulunamadı: {package_name}")
            return
        
        pkg = self.packages[package_name]
        is_installed = (INSTALLED_DIR / package_name).exists()
        
        print(f"\n{Colors.BOLD}{Colors.CYAN}📋 {package_name}{Colors.ENDC}")
        print(f"{Colors.BOLD}{'-' * 80}{Colors.ENDC}")
        print(f"  {Colors.BOLD}Sürüm:{Colors.ENDC} {pkg.get('version', '?')}")
        status = f"{Colors.GREEN}Yüklü{Colors.ENDC}" if is_installed else f"{Colors.RED}Yüklü Değil{Colors.ENDC}"
        print(f"  {Colors.BOLD}Durum:{Colors.ENDC} {status}")
        print(f"  {Colors.BOLD}Açıklama:{Colors.ENDC} {pkg.get('description', '?')}")
        print(f"  {Colors.BOLD}Yazar:{Colors.ENDC} {pkg.get('author', '?')}")
        print(f"  {Colors.BOLD}Lisans:{Colors.ENDC} {pkg.get('license', 'MIT')}")
        print(f"  {Colors.BOLD}Kategori:{Colors.ENDC} {pkg.get('category', 'misc')}")
        print(f"  {Colors.BOLD}URL:{Colors.ENDC} {pkg['url']}")
        
        if pkg.get('main'):
            print(f"  {Colors.BOLD}Ana Dosya:{Colors.ENDC} {pkg['main']}")
        
        if pkg.get('dependencies'):
            print(f"  {Colors.BOLD}Bağımlılıklar:{Colors.ENDC}")
            for dep in pkg['dependencies']:
                status = f"{Colors.GREEN}✓{Colors.ENDC}" if dep in self.installed else f"{Colors.RED}✗{Colors.ENDC}"
                print(f"    {status} {dep}")
        
        # Repo sertifikası (cerf.alpc)
        if pkg.get('cert_type'):
            icon = "🏆" if pkg.get('cert_type') == 'official' else ("🔧" if pkg.get('cert_type') == 'dev' else "👤")
            validity = f"{Colors.GREEN}Geçerli{Colors.ENDC}" if pkg.get('cert_valid') else f"{Colors.RED}Geçersiz{Colors.ENDC}"
            print(f"  {Colors.BOLD}Repo Sertifikası:{Colors.ENDC} {pkg.get('cert_type')} {icon} - {validity}")
            if pkg.get('cert_author'):
                print(f"  {Colors.BOLD}Sertifika Sahibi:{Colors.ENDC} {pkg.get('cert_author')}")
        
        # Yüklü paket sertifikası
        if is_installed:
            cert = self.cert_manager.get_certificate(package_name)
            if cert:
                if cert.get("type") == "official":
                    print(f"  {Colors.BOLD}Sertifika:{Colors.ENDC} {Colors.GREEN}Official Alp Certified 🏆{Colors.ENDC}")
                else:
                    print(f"  {Colors.BOLD}Sertifika:{Colors.ENDC} {Colors.CYAN}Özel ({cert.get('author')}) 🔒{Colors.ENDC}")
            else:
                print(f"  {Colors.BOLD}Sertifika:{Colors.ENDC} {Colors.YELLOW}Yok ⚠️{Colors.ENDC}")
        
        print(f"{Colors.BOLD}{'-' * 80}{Colors.ENDC}\n")
    
    def clean_cache(self) -> None:
        """Cache'i temizle"""
        if ALP_CACHE.exists():
            shutil.rmtree(ALP_CACHE)
            ALP_CACHE.mkdir()
            logger.log("SUCCESS", "Cache temizlendi")
    
    def stats(self) -> None:
        """İstatistikleri göster"""
        total_size = 0
        for pkg_dir in INSTALLED_DIR.glob("*"):
            if pkg_dir.is_dir():
                total_size += sum(f.stat().st_size for f in pkg_dir.rglob("*") if f.is_file())
        
        # Sertifika istatistikleri
        certified_count = sum(1 for info in self.installed.values() if info.get('certified'))
        official_count = sum(1 for info in self.installed.values() if info.get('cert_type') == 'official')
        
        print(f"\n{Colors.BOLD}{Colors.CYAN}📊 Alp İstatistikleri:{Colors.ENDC}")
        print(f"{Colors.BOLD}{'-' * 80}{Colors.ENDC}")
        print(f"  {Colors.BOLD}Toplam Paket:{Colors.ENDC} {len(self.packages)}")
        print(f"  {Colors.BOLD}Yüklü Paket:{Colors.ENDC} {len(self.installed)}")
        print(f"  {Colors.BOLD}Sertifikalı Paket:{Colors.ENDC} {certified_count} ({Colors.GREEN}🏆 Official: {official_count}{Colors.ENDC})")
        print(f"  {Colors.BOLD}Kullanılan Alan:{Colors.ENDC} {total_size / 1024 / 1024:.2f} MB")
        print(f"  {Colors.BOLD}Alp Dizini:{Colors.ENDC} {ALP_HOME}")
        print(f"  {Colors.BOLD}Son Güncelleme:{Colors.ENDC} {datetime.fromtimestamp(PACKAGES_DB.stat().st_mtime) if PACKAGES_DB.exists() else 'Hiç'}")
        print(f"{Colors.BOLD}{'-' * 80}{Colors.ENDC}\n")
    
    def doctor(self) -> None:
        """Sistem sağlığını kontrol et: bozuk kurulumlar, eksik bağımlılıklar, cache sorunları"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}🏥 Alp Doktor:{Colors.ENDC}")
        print(f"{Colors.BOLD}{'-' * 80}{Colors.ENDC}")
        issues_dirs = []
        issues_db = []
        issues_installs = []
        issues_deps = []
        issues_cache = []

        # Dizin kontrolleri
        for path, name in [(ALP_HOME, 'ALP_HOME'), (ALP_CACHE, 'ALP_CACHE'), (ALP_LOGS, 'ALP_LOGS'), (INSTALLED_DIR, 'INSTALLED_DIR')]:
            if not path.exists():
                issues_dirs.append(f"Eksik dizin: {name} ({path})")
            elif not path.is_dir():
                issues_dirs.append(f"Dizin değil: {name} ({path})")

        # Veritabanı kontrolleri
        if not PACKAGES_DB.exists():
            issues_db.append("Paket veritabanı yok. 'alp update' çalıştırın.")
        else:
            try:
                with open(PACKAGES_DB, 'r') as f:
                    json.load(f)
            except Exception as e:
                issues_db.append(f"packages.json okunamadı: {e}")

        if not INSTALLED_DB.exists():
            issues_db.append("Yüklü paket veritabanı yok (hiç kurulum yapılmamış olabilir).")
        else:
            try:
                with open(INSTALLED_DB, 'r') as f:
                    json.load(f)
            except Exception as e:
                issues_db.append(f"installed.json okunamadı: {e}")

        # Kurulum tutarlılık kontrolleri
        installed_dirs = [d for d in INSTALLED_DIR.glob('*') if d.is_dir()]
        for d in installed_dirs:
            name = d.name
            if name not in self.installed:
                issues_installs.append(f"Kayıtsız kurulum klasörü bulundu: {name}")
            inst_file = d / 'installed.json'
            if not inst_file.exists():
                issues_installs.append(f"Eksik installed.json: {name}")
            else:
                try:
                    with open(inst_file, 'r') as f:
                        data = json.load(f)
                    if data.get('name') and data.get('name') != name:
                        issues_installs.append(f"Ad uyuşmazlığı: klasör={name}, json={data.get('name')}")
                except Exception as e:
                    issues_installs.append(f"installed.json bozuk: {name} ({e})")

        for name in list(self.installed.keys()):
            if not (INSTALLED_DIR / name).exists():
                issues_installs.append(f"Kayıt var ama klasör yok: {name}")

        # Bağımlılık kontrolleri (yalnızca yüklü paketler için)
        for name in list(self.installed.keys()):
            deps = self.packages.get(name, {}).get('dependencies', [])
            for dep in deps:
                if dep not in self.installed:
                    issues_deps.append(f"{name} eksik bağımlılık: {dep}")

        # Cache kontrolleri
        total_cache_size = 0
        zero_files = []
        stale_scripts = 0
        if ALP_CACHE.exists():
            for f in ALP_CACHE.rglob('*'):
                if f.is_file():
                    size = f.stat().st_size
                    total_cache_size += size
                    if size == 0:
                        zero_files.append(str(f))
            for f in ALP_CACHE.glob('*_install.sh'):
                pkgname = f.name.replace('_install.sh', '')
                if pkgname not in self.packages and pkgname not in self.installed:
                    stale_scripts += 1
        cache_limit_mb = self.config.get('cache_size', 1000)
        cache_size_mb = total_cache_size / 1024 / 1024
        if cache_size_mb > cache_limit_mb:
            issues_cache.append(f"Cache boyutu limit aşıldı: {cache_size_mb:.2f}MB > {cache_limit_mb}MB")
        if zero_files:
            issues_cache.append(f"Cache içinde sıfır bayt dosyalar: {len(zero_files)} adet")
        if stale_scripts:
            issues_cache.append(f"Artık kurulum scriptleri: {stale_scripts} adet")

        # Çıktı
        def section(title, items):
            print(f"  {Colors.BOLD}{title}:{Colors.ENDC}")
            if not items:
                print(f"    {Colors.GREEN}✓ Temiz{Colors.ENDC}")
            else:
                for it in items[:10]:
                    print(f"    {Colors.YELLOW}•{Colors.ENDC} {it}")
                extra = len(items) - min(len(items), 10)
                if extra > 0:
                    print(f"    (+{extra} daha)")
            print("")

        section("Dizinler", issues_dirs)
        section("Veritabanları", issues_db)
        section("Kurulumlar", issues_installs)
        section("Bağımlılıklar", issues_deps)
        section("Cache", issues_cache)

        # Öneriler
        suggestions = []
        if issues_db or not PACKAGES_DB.exists():
            suggestions.append("alp update")
        if issues_cache:
            suggestions.append("alp clean")
        if issues_deps:
            missing_set = sorted({x.split(':')[-1].strip() for x in issues_deps})
            if missing_set:
                suggestions.append(f"alp install {' '.join(missing_set[:3])}")
        if suggestions:
            print(f"  {Colors.BOLD}Öneriler:{Colors.ENDC}")
            for s in suggestions:
                print(f"    {Colors.CYAN}→ {s}{Colors.ENDC}")
        print(f"{Colors.BOLD}{'-' * 80}{Colors.ENDC}\n")
    
    def self_update(self) -> None:
        """Alp'in kendisini güncelle"""
        print(f"{Colors.BOLD}{Colors.CYAN}🔄 Alp Self-Update Başlıyor...{Colors.ENDC}\n")
        
        MANAGER_URL = "https://raw.githubusercontent.com/ATOMGAMERAGA/alp-repo/refs/heads/main/alp_manager.py"
        INSTALL_DIR = Path("/usr/local/lib/alp")
        
        try:
            print(f"{Colors.YELLOW}→ Yeni sürüm indiriliyor...{Colors.ENDC}")
            new_manager = INSTALL_DIR / "alp_manager.py.new"
            
            if not self.download_file(MANAGER_URL, new_manager):
                logger.log("ERROR", "Yeni sürüm indirilemedi")
                return
            
            print(f"{Colors.YELLOW}→ Syntax kontrol ediliyor...{Colors.ENDC}")
            result = subprocess.run(
                ["python3", "-m", "py_compile", str(new_manager)],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.log("ERROR", f"Yeni sürümde syntax hatası: {result.stderr}")
                new_manager.unlink()
                return
            
            print(f"{Colors.YELLOW}→ Güncellemesi uygulanıyor...{Colors.ENDC}")
            old_manager = INSTALL_DIR / "alp_manager.py"
            old_manager.unlink()
            new_manager.rename(old_manager)
            old_manager.chmod(0o755)
            
            logger.log("SUCCESS", "Alp başarıyla güncellendi!")
            print(f"\n{Colors.GREEN}✅ Yeni sürüm aktif. Komutu yeniden çalıştırın.{Colors.ENDC}\n")
            
        except Exception as e:
            logger.log("ERROR", f"Self-update hatası: {e}")
    
    def save_packages(self) -> None:
        """Paketleri veritabanına kaydet"""
        PACKAGES_DB.parent.mkdir(parents=True, exist_ok=True)
        with open(PACKAGES_DB, 'w') as f:
            json.dump(self.packages, f, indent=2, ensure_ascii=False)
    
    def save_installed(self) -> None:
        """Yüklü paketleri veritabanına kaydet"""
        INSTALLED_DB.parent.mkdir(parents=True, exist_ok=True)
        with open(INSTALLED_DB, 'w') as f:
            json.dump(self.installed, f, indent=2, ensure_ascii=False)
    
    def load_databases(self) -> None:
        """Veritabanlarını yükle"""
        if PACKAGES_DB.exists():
            try:
                with open(PACKAGES_DB, 'r') as f:
                    self.packages = json.load(f)
            except:
                self.packages = {}
        
        if INSTALLED_DB.exists():
            try:
                with open(INSTALLED_DB, 'r') as f:
                    self.installed = json.load(f)
            except:
                self.installed = {}

def print_banner():
    print(f"""
{Colors.BOLD}{Colors.CYAN}
 █████╗ ██╗     ██████╗ 
██╔══██╗██║     ██╔══██╗
███████║██║     ██████╔╝
██╔══██║██║     ██╔═══╝ 
██║  ██║███████╗██║     
╚═╝  ╚═╝╚══════╝╚═╝     
{Colors.ENDC}
{Colors.BOLD}Alp Package Manager v2.2{Colors.ENDC}
{Colors.YELLOW}Advanced Linux Package Management System{Colors.ENDC}
{Colors.GREEN}🔒 Certificate System Enabled{Colors.ENDC}
""")

# Yardım metnini merkezi hâle getir

def print_help():
    print_banner()
    print(f"""{Colors.BOLD}Kullanım: alp <komut> [argümanlar]{Colors.ENDC}
 
{Colors.BOLD}Paket Yönetimi:{Colors.ENDC}
  {Colors.CYAN}update{Colors.ENDC}                  Depoyu güncelle
  {Colors.CYAN}install <paket>{Colors.ENDC}         Paket yükle
  {Colors.CYAN}remove <paket>{Colors.ENDC}          Paket kaldır
  {Colors.CYAN}upgrade [paket]{Colors.ENDC}         Paket güncelle (tümü veya belirli)
  
{Colors.BOLD}Paket İşlemleri:
  {Colors.CYAN}list{Colors.ENDC}                    Tüm paketleri listele
  {Colors.CYAN}list <kategori>{Colors.ENDC}        Kategoriye göre listele
  {Colors.CYAN}installed{Colors.ENDC}              Yüklü paketleri listele
  {Colors.CYAN}search <anahtar>{Colors.ENDC}       Paket ara
  {Colors.CYAN}info <paket>{Colors.ENDC}           Paket detaylarını göster
  
{Colors.BOLD}Geliştirici Araçları:
  {Colors.CYAN}compile <dizin>{Colors.ENDC}        Paket dizinini .alp dosyasına derle
  {Colors.CYAN}install-local <dosya>{Colors.ENDC}  Yerel .alp dosyasını kur
  
{Colors.BOLD}Sertifika Sistemi:
  {Colors.CYAN}cert-info <paket>{Colors.ENDC}      Paket sertifikasını göster
  {Colors.CYAN}cert-create <type> <author> <pkg>{Colors.ENDC}  cerf.alpc oluştur (official/dev/normal)
  {Colors.CYAN}cert-scan <github_url>{Colors.ENDC}  GitHub reposunda cerf.alpc taraması yap
  {Colors.GREEN}🏆 Official{Colors.ENDC}             Resmi Alp sertifikalı paketler
  {Colors.CYAN}🔧 Dev{Colors.ENDC}                  Geliştirici sertifikalı paketler
  {Colors.CYAN}👤 Normal{Colors.ENDC}               Normal sertifikalı paketler
  {Colors.YELLOW}⚠️  Unsigned{Colors.ENDC}            Sertifikasız paketler (Uyarı verir)
  
{Colors.BOLD}Sistem:
  {Colors.CYAN}stats{Colors.ENDC}                  İstatistikleri göster
  {Colors.CYAN}doctor{Colors.ENDC}                 Sağlık taraması (kurulum, bağımlılık, cache)
  {Colors.CYAN}clean{Colors.ENDC}                  Cache'i temizle
  {Colors.CYAN}self-update{Colors.ENDC}            Alp'i güncelle
  {Colors.CYAN}config{Colors.ENDC}                 Ayarları göster
  {Colors.CYAN}help{Colors.ENDC}                   Bu yardımı göster
 
{Colors.BOLD}Örnekler:
  alp update
  alp install myapp
  alp compile ./myapp-project    {Colors.YELLOW}# Sertifikalama seçeneği ile{Colors.ENDC}
  alp install-local myapp-1.0.0.alp
  alp cert-info myapp            {Colors.YELLOW}# Sertifika bilgilerini görüntüle{Colors.ENDC}
  alp remove myapp
  alp upgrade
  alp search web
        """)
 

def main():
    # Argüman yoksa yardım göster ve çık
    if len(sys.argv) < 2:
        print_help()
        return
    
    mgr = PackageManager()
    cmd = sys.argv[1].lower()
    
    try:
        if cmd == "update":
            mgr.update_repo(force=True)
        elif cmd == "install" and len(sys.argv) > 2:
            mgr.install(sys.argv[2])
        elif cmd == "remove" and len(sys.argv) > 2:
            mgr.remove(sys.argv[2])
        elif cmd == "upgrade":
            mgr.upgrade(sys.argv[2] if len(sys.argv) > 2 else None)
        elif cmd == "list":
            category = sys.argv[2] if len(sys.argv) > 2 else None
            mgr.list_packages(category)
        elif cmd == "installed":
            mgr.list_installed()
        elif cmd == "search" and len(sys.argv) > 2:
            mgr.search(sys.argv[2])
        elif cmd == "info" and len(sys.argv) > 2:
            mgr.show_info(sys.argv[2])
        elif cmd == "compile" and len(sys.argv) > 2:
            mgr.compile_package(sys.argv[2])
        elif cmd == "install-local" and len(sys.argv) > 2:
            mgr.install_local_package(sys.argv[2])
        elif cmd == "cert-info" and len(sys.argv) > 2:
            mgr.cert_manager.show_certificate_info(sys.argv[2])
        elif cmd == "cert-create":
            # alp cert-create <type> <author> <package>
            if len(sys.argv) > 4:
                mgr.create_alpc(sys.argv[4], sys.argv[3], sys.argv[2])
            else:
                print(f"{Colors.YELLOW}ℹ️  Kullanım: alp cert-create <type> <author> <package>{Colors.ENDC}")
                print(f"{Colors.CYAN}Etkileşimli mod başlatılıyor...{Colors.ENDC}")
                ctype = input("Sertifika türü (official/dev/normal): ").strip().lower() or "normal"
                author = input("Yazar/İmzalayan: ").strip() or "Unknown"
                pkg = input("Paket adı: ").strip()
                if pkg:
                    mgr.create_alpc(pkg, author, ctype)
                else:
                    logger.log("ERROR", "Paket adı zorunludur")
        elif cmd == "cert-scan":
            if len(sys.argv) > 2:
                mgr.scan_alpc_repo(sys.argv[2])
            else:
                print(f"{Colors.YELLOW}ℹ️  Kullanım: alp cert-scan <github_url>{Colors.ENDC}")
        elif cmd == "stats":
            mgr.stats()
        elif cmd == "doctor":
            mgr.doctor()
        elif cmd == "clean":
            mgr.clean_cache()
        elif cmd == "self-update":
            mgr.self_update()
        elif cmd == "config":
            print(json.dumps(mgr.config.config, indent=2))
        elif cmd == "help":
            print_help()
        else:
            logger.log("ERROR", f"Bilinmeyen komut: {cmd}")
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️  İşlem iptal edildi{Colors.ENDC}")
        sys.exit(130)
    except Exception as e:
        logger.log("ERROR", f"Beklenmeyen hata: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

