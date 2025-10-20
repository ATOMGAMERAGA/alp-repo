#!/usr/bin/env python3
"""
Alp Package Manager - Advanced Linux Package Management System
GitHub entegrasyonu, bağımlılık yönetimi, otomatik güncellemeler ve daha fazlası
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

class Logger:
    """Gelişmiş loglama sistemi"""
    def __init__(self):
        ALP_LOGS.mkdir(parents=True, exist_ok=True)
        self.log_file = ALP_LOGS / f"alp_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    def log(self, level: str, message: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        with open(self.log_file, 'a') as f:
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
    
    def compile_package(self, directory: str) -> bool:
        """Paket dizinini .alp dosyasına derle"""
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
            print("main = myapp.py  (opsiyonel)")
            return False
        
        package_name = metadata['name']
        version = metadata['version']
        output_file = Path.cwd() / f"{package_name}-{version}.alp"
        
        print(f"{Colors.BOLD}{Colors.CYAN}📦 Paket derleniyor: {package_name} v{version}{Colors.ENDC}")
        
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
                "format_version": "1.1",
                "metadata": metadata,
                "files": {
                    "install_script": install_script,
                    "uninstall_script": uninstall_script,
                    "readme": readme_content
                },
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
            print(f"{Colors.GREEN}✓{Colors.ENDC} Dosya: {output_file}")
            print(f"{Colors.GREEN}✓{Colors.ENDC} Boyut: {file_size:.2f} KB")
            print(f"{Colors.GREEN}✓{Colors.ENDC} Checksum: {checksum[:16]}...")
            if main_file_name:
                print(f"{Colors.GREEN}✓{Colors.ENDC} Ana dosya: {main_file_name}")
            print(f"\n{Colors.BOLD}Kurulum:{Colors.ENDC} alp install-local {output_file}")
            
            return True
            
        except Exception as e:
            logger.log("ERROR", f"Paket derlenemedi: {e}")
            return False
    
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
            if format_version not in ["1.0", "1.1"]:
                logger.log("ERROR", "Desteklenmeyen paket formatı")
                return False
            
            metadata = alp_package["metadata"]
            package_name = metadata["name"]
            version = metadata.get("version", "unknown")
            
            # Zaten yüklü mü kontrol et
            if package_name in self.installed:
                logger.log("WARNING", f"Paket zaten yüklü: {package_name}")
                response = input(f"Yeniden yüklemek ister misiniz? (e/h): ")
                if response.lower() != 'e':
                    return False
                self.remove(package_name)
            
            print(f"{Colors.BOLD}{Colors.BLUE}📥 Yükleniyor: {package_name} ({version}){Colors.ENDC}")
            
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
                    'checksum': alp_package.get("checksum", "")
                }
                
                with open(pkg_dir / "installed.json", 'w') as f:
                    json.dump(install_info, f, indent=2)
                
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
            
            print(f"{status} {Colors.BOLD}{name}{Colors.ENDC:24} ({ver:8}) {Colors.CYAN}[{cat}]{Colors.ENDC}")
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
            
            print(f"{Colors.GREEN}✓{Colors.ENDC} {Colors.BOLD}{name}{Colors.ENDC:24} {ver:8} ({size:.2f}MB)")
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
        
        print(f"\n{Colors.BOLD}{Colors.CYAN}📊 Alp İstatistikleri:{Colors.ENDC}")
        print(f"{Colors.BOLD}{'-' * 80}{Colors.ENDC}")
        print(f"  {Colors.BOLD}Toplam Paket:{Colors.ENDC} {len(self.packages)}")
        print(f"  {Colors.BOLD}Yüklü Paket:{Colors.ENDC} {len(self.installed)}")
        print(f"  {Colors.BOLD}Kullanılan Alan:{Colors.ENDC} {total_size / 1024 / 1024:.2f} MB")
        print(f"  {Colors.BOLD}Alp Dizini:{Colors.ENDC} {ALP_HOME}")
        print(f"  {Colors.BOLD}Son Güncelleme:{Colors.ENDC} {datetime.fromtimestamp(PACKAGES_DB.stat().st_mtime) if PACKAGES_DB.exists() else 'Hiç'}")
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
{Colors.BOLD}Alp Package Manager v2.1{Colors.ENDC}
{Colors.YELLOW}Advanced Linux Package Management System{Colors.ENDC}
""")

def main():
    if len(sys.argv) < 2:
        print_banner()
        print(f"""{Colors.BOLD}Kullanım: alp <komut> [argümanlar]{Colors.ENDC}

{Colors.BOLD}Paket Yönetimi:{Colors.ENDC}
  {Colors.CYAN}update{Colors.ENDC}                  Depoyu güncelle
  {Colors.CYAN}install <paket>{Colors.ENDC}         Paket yükle
  {Colors.CYAN}remove <paket>{Colors.ENDC}          Paket kaldır
  {Colors.CYAN}upgrade [paket]{Colors.ENDC}         Paket güncelle (tümü veya belirli)
  
{Colors.BOLD}Paket İşlemleri:{Colors.ENDC}
  {Colors.CYAN}list{Colors.ENDC}                    Tüm paketleri listele
  {Colors.CYAN}list <kategori>{Colors.ENDC}        Kategoriye göre listele
  {Colors.CYAN}installed{Colors.ENDC}              Yüklü paketleri listele
  {Colors.CYAN}search <anahtar>{Colors.ENDC}       Paket ara
  {Colors.CYAN}info <paket>{Colors.ENDC}           Paket detaylarını göster
  
{Colors.BOLD}Geliştirici Araçları:{Colors.ENDC}
  {Colors.CYAN}compile <dizin>{Colors.ENDC}        Paket dizinini .alp dosyasına derle
  {Colors.CYAN}install-local <dosya>{Colors.ENDC}  Yerel .alp dosyasını kur
  
{Colors.BOLD}Sistem:{Colors.ENDC}
  {Colors.CYAN}stats{Colors.ENDC}                  İstatistikleri göster
  {Colors.CYAN}clean{Colors.ENDC}                  Cache'i temizle
  {Colors.CYAN}self-update{Colors.ENDC}            Alp'i güncelle
  {Colors.CYAN}config{Colors.ENDC}                 Ayarları göster
  {Colors.CYAN}help{Colors.ENDC}                   Bu yardımı göster

{Colors.BOLD}Örnekler:{Colors.ENDC}
  alp update
  alp install myapp
  alp compile ./myapp-project
  alp install-local myapp-1.0.0.alp
  alp remove myapp
  alp upgrade
  alp search web
        """)
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
        elif cmd == "stats":
            mgr.stats()
        elif cmd == "clean":
            mgr.clean_cache()
        elif cmd == "self-update":
            mgr.self_update()
        elif cmd == "config":
            print(json.dumps(mgr.config.config, indent=2))
        elif cmd == "help":
            main()
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
