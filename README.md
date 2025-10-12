# 🚀 Alp Package Manager

**Alp**, GitHub deposundan paketleri yönetmek için tasarlanmış, **gelişmiş**, **hafif** ve **güvenilir** bir Linux paket yöneticisidir. `apt`, `dnf`, `pacman` gibi sistem paket yöneticilerine benzer şekilde çalışır, ancak doğrudan GitHub depolarından paket yönetimi sağlar.

## ✨ Özellikler

- 📦 **GitHub İntegrasyonu** - Projelerinizi doğrudan GitHub'dan yönetin
- 🔗 **Bağımlılık Yönetimi** - Otomatik bağımlılık çözümü ve kurulumu
- 🔄 **Otomatik Güncellemeler** - Systemd timer ile 24 saatte bir güncelleme kontrolü
- 🛡️ **Güvenli Kurulum** - Syntax kontrol, backup ve geri dönüş desteği
- 📊 **Loglama Sistemi** - Tüm işlemler `~/.alp/logs/` dizininde kaydedilir
- ⚡ **Self-Update** - Alp'in kendisini güncelleme özelliği
- 🎯 **Kategorilendirme** - Paketleri kategorilere göre filtreleme
- 💾 **Cache Yönetimi** - Hızlı indirme ve disk alanı yönetimi
- 🔍 **Arama Fonksiyonu** - Paket adı ve açıklamasına göre arama
- 📈 **İstatistikler** - Sistem ve paket istatistikleri

---

## 📥 Kurulum

### Linux (Ubuntu/Debian)

```bash
curl -fsSL https://raw.githubusercontent.com/ATOMGAMERAGA/alp-repo/refs/heads/main/install.sh | sudo bash
```

**Veya adım adım:**

```bash
# Script'i indir
curl -O https://raw.githubusercontent.com/ATOMGAMERAGA/alp-repo/refs/heads/main/install.sh

# Kurulumu çalıştır
sudo bash install.sh

# Script'i sil (opsiyonel)
rm install.sh
```

### Linux (Fedora/RHEL)

```bash
curl -fsSL https://raw.githubusercontent.com/ATOMGAMERAGA/alp-repo/refs/heads/main/install.sh | sudo bash
```

Bağımlılıklar otomatik olarak kurulacaktır.

### Linux (Arch Linux)

```bash
curl -fsSL https://raw.githubusercontent.com/ATOMGAMERAGA/alp-repo/refs/heads/main/install.sh | sudo bash
```

### Sorun Giderme

Eğer curl çalışmazsa wget kullanın:

```bash
wget -qO- https://raw.githubusercontent.com/ATOMGAMERAGA/alp-repo/refs/heads/main/install.sh | sudo bash
```

---

## 🎯 Hızlı Başlangıç

```bash
# Depoyu güncelle
alp update

# Tüm paketleri listele
alp list

# Belirli bir paketi arama
alp search web

# Paket yükle
alp install myproject

# Paket kaldır
alp remove myproject

# Yüklü paketleri göster
alp installed

# Paket detaylarını göster
alp info myproject

# Tüm paketleri güncelle
alp upgrade

# Belirli paketi güncelle
alp upgrade myproject
```

---

## 📚 Komutlar

### Paket Yönetimi

#### `alp update`
Depoyu güncelle ve yeni paketleri bul. İlk kullanımda mutlaka çalıştırılmalıdır.

```bash
alp update
```

**Çıktı:**
```
ℹ️  Dizin yapısı oluşturuldu
📦 Depo güncelleniyor...
✅ Depo güncellendi: 15 paket bulundu
```

---

#### `alp install <paket>`
Belirtilen paketi yükle. Bağımlılıkları otomatik olarak çözer ve kurar.

```bash
alp install ggs
alp install myproject
```

**Özellikler:**
- ✅ Bağımlılıkları otomatik yükler
- ✅ Syntax kontrol yapar
- ✅ Hata durumunda geri yükler (backup)
- ✅ Ayrıntılı loglama

---

#### `alp remove <paket>`
Belirtilen paketi ve ilişkili dosyalarını kaldır.

```bash
alp remove ggs
```

**Uyarı:** Bu işlem geri alınamaz. Lütfen dikkatli olun.

---

#### `alp upgrade [paket]`
Paketleri güncelle. Paket adı belirtilmezse tüm paketler güncellenir.

```bash
# Belirli paketi güncelle
alp upgrade myproject

# Tüm paketleri güncelle
alp upgrade
```

---

### Paket İşlemleri

#### `alp list [kategori]`
Tüm paketleri veya belirli bir kategoriye göre listele.

```bash
# Tüm paketler
alp list

# Kategoriye göre filtrele
alp list development
alp list web
alp list utilities
```

**Kategoriler:**
- `utilities` - Sistem araçları
- `development` - Geliştirme araçları
- `web` - Web uygulamaları
- `database` - Veritabanı araçları
- `monitoring` - İzleme araçları
- `education` - Eğitim araçları
- `misc` - Diğer

---

#### `alp installed`
Yüklü paketlerin listesini göster. Her paket için sürüm, kurulum tarihi ve kullanılan disk alanı gösterilir.

```bash
alp installed
```

**Çıktı:**
```
✅ Yüklü Paketler:
────────────────────────────────────────────────────────────────────────────────
✓ ggs                      1.0.0    (45.32MB)
   └─ Yükleme tarihi: 2025-01-15
✓ myproject                2.1.0    (23.15MB)
   └─ Yükleme tarihi: 2025-01-14
────────────────────────────────────────────────────────────────────────────────
```

---

#### `alp search <anahtar>`
Paket adı veya açıklamasında arama yap.

```bash
alp search web
alp search python
alp search database
```

---

#### `alp info <paket>`
Paket hakkında detaylı bilgi göster.

```bash
alp info ggs
```

**Gösterilenler:**
- 📌 Paket adı ve sürüm
- 📝 Açıklama
- 👤 Yazar
- 📜 Lisans
- 🏷️ Kategori
- 🔗 GitHub URL
- 📦 Bağımlılıklar

---

### Sistem İşlemleri

#### `alp stats`
Alp istatistiklerini göster.

```bash
alp stats
```

**Gösterilenler:**
- 📦 Toplam paket sayısı
- ✅ Yüklü paket sayısı
- 💾 Kullanılan disk alanı
- 📚 Alp dizin konumu
- 📅 Son güncelleme tarihi

---

#### `alp clean`
İndirilen dosyaların cache'ini temizle. Disk alanı tasarrufu sağlar.

```bash
alp clean
```

---

#### `alp self-update`
Alp'in kendisini güncelle. Yeni sürüm indirdikten sonra syntax kontrol yaparak güncelleme yapar.

```bash
alp self-update
```

**Özellikler:**
- ✅ Yeni sürüm syntax kontrol
- ✅ Otomatik backup ve geri yükleme
- ✅ Ayrıntılı loglama

---

#### `alp config`
Alp yapılandırma dosyasını göster.

```bash
alp config
```

**Yapılandırma Seçenekleri:**
```json
{
  "auto_update": true,
  "update_interval": 3600,
  "cache_size": 1000,
  "verify_packages": true,
  "parallel_install": false,
  "check_dependencies": true,
  "keep_cache": false
}
```

---

#### `alp help`
Yardımı göster.

```bash
alp help
```

---

## 📂 Dizin Yapısı

```
~/.alp/
├── packages.json          # Tüm mevcut paketler
├── installed.json         # Yüklü paketler
├── config.json            # Alp yapılandırması
├── cache/                 # İndirilen dosyaların cache'i
│   └── *.sh              # Kurulum/kaldırma scriptleri
├── logs/                  # İşlem logları
│   └── alp_*.log         # Tarih ve saat bilgili loglar
└── installed/             # Yüklü paketler
    ├── ggs/
    │   └── installed.json
    └── myproject/
        └── installed.json
```

---

## 📝 Proje Paketi Oluşturma

### README.md Formatı

Projenizin kökünde `README.md` dosyasında şu bilgiler olmalıdır:

```markdown
# MyProject

name = myproject
ver = 1.0.0
des = Dosya işlemleri için harika bir CLI aracı
author = John Doe
license = MIT
category = utilities
deps = [python3, git]

## Açıklama
Projenizin açıklaması buraya gelir...
```

**Zorunlu Alanlar:**
- `name` - Paket adı (boşluksuz, küçük harfler)
- `ver` - Sürüm numarası (semantic versioning)
- `des` - Kısa açıklama

**Opsiyonel Alanlar:**
- `author` - Geliştirici adı
- `license` - Lisans türü (MIT, GPL, Apache vb.)
- `category` - Kategori
- `deps` - Bağımlılıklar (virgülle ayrılmış)

---

### alp.sh - Kurulum Scripti

Projenizin kökünde `alp.sh` dosyasını oluşturun:

```bash
#!/bin/bash
set -e

PROJECT_NAME="myproject"
PROJECT_DIR="/opt/$PROJECT_NAME"
REPO_URL="https://github.com/username/myproject.git"

echo "📦 $PROJECT_NAME Kurulumu Başlıyor..."

# Sistem bağımlılıkları
sudo apt-get update
sudo apt-get install -y python3 python3-pip git

# Proje dizini
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

# Repoyu klonla
git clone "$REPO_URL" .

# Python bağımlılıkları
if [ -f requirements.txt ]; then
    pip3 install -r requirements.txt
fi

# Sistem komutu oluştur
sudo ln -sf "$PROJECT_DIR/myproject.py" /usr/local/bin/myproject
sudo chmod +x /usr/local/bin/myproject

echo "✅ Kurulum tamamlandı!"
```

---

### alp_u.sh - Kaldırma Scripti

Projenizin kökünde `alp_u.sh` dosyasını oluşturun:

```bash
#!/bin/bash
set -e

PROJECT_NAME="myproject"
PROJECT_DIR="/opt/$PROJECT_NAME"

echo "🗑️  $PROJECT_NAME Kaldırılıyor..."

# Sistem komutunu sil
sudo rm -f /usr/local/bin/$PROJECT_NAME

# Proje dizinini sil
sudo rm -rf "$PROJECT_DIR"

echo "✅ Kaldırma tamamlandı!"
```

---

### repo.alp'ye Ekleme

`repo.alp` dosyasına GitHub URL'nizi ekleyin:

```
https://github.com/ATOMGAMERAGA/alp-repo
https://github.com/username/myproject
https://github.com/username/another-project
```

**Not:** Her satırda bir proje URL'si olmalıdır.

---

## 🔧 Yapılandırma

Alp yapılandırmasını `~/.alp/config.json` dosyasından düzenleyebilirsiniz:

```json
{
  "auto_update": true,
  "update_interval": 3600,
  "cache_size": 1000,
  "verify_packages": true,
  "parallel_install": false,
  "check_dependencies": true,
  "keep_cache": false
}
```

**Seçenekler:**
- `auto_update` - Otomatik güncelleme etkinleştirilsin mi?
- `update_interval` - Güncelleme kontrolü aralığı (saniye cinsinden)
- `cache_size` - Cache boyutu limiti (MB)
- `verify_packages` - Paketler doğrulanabilsin mi?
- `parallel_install` - Paralel kurulum etkinleştirilsin mi?
- `check_dependencies` - Bağımlılıklar kontrol edilsin mi?
- `keep_cache` - Cache koruma edilsin mi?

---

## 🔄 Otomatik Güncellemeler

Alp otomatik olarak 24 saatte bir depoyu günceller. Systemd timer tarafından yönetilir:

```bash
# Timer'ı kontrol et
sudo systemctl status alp-update.timer

# Timer'ı başlat
sudo systemctl start alp-update.timer

# Timer'ı durdur
sudo systemctl stop alp-update.timer

# Timer'ı devre dışı bırak
sudo systemctl disable alp-update.timer
```

---

## 📖 Man Sayfası

Alp hakkında detaylı bilgi almak için:

```bash
man alp
```

---

## 🗑️ Kaldırma

Alp'i sisteminizden kaldırmak için:

```bash
sudo alp-uninstall
```

Bu komut:
- ✅ Alp komutunu kaldırır
- ✅ Systemd timer'ını durdurur
- ✅ Man sayfasını siler
- ✅ Tüm system dosyalarını siler

**Not:** `~/.alp/` dizini korunur, dilerseniz manuel olarak silebilirsiniz.

---

## 🐛 Sorun Giderme

### Sorun: "Python3 yüklü değil"

```bash
# Ubuntu/Debian
sudo apt install python3

# Fedora/RHEL
sudo dnf install python3

# Arch
sudo pacman -S python
```

### Sorun: "Paket bulunamadı"

```bash
# Depoyu güncelle
alp update

# Yeniden ara
alp search paket-adi
```

### Sorun: "Kurulum scripti indirilemedi"

```bash
# Internet bağlantınızı kontrol edin
ping github.com

# Curl/wget testini yapın
curl -I https://github.com
```

### Sorun: "Syntax hatası"

```bash
# Alp'i güncelle
alp self-update

# Veya manuel güncelleme
sudo python3 -m py_compile /usr/local/lib/alp/alp_manager.py
```

---

## 📊 Loglar

Tüm işlemler `~/.alp/logs/` dizininde kaydedilir:

```bash
# Son logları göster
cat ~/.alp/logs/alp_*.log

# Logları izle
tail -f ~/.alp/logs/alp_*.log
```

---

## 📋 Lisans

Alp MIT Lisansı altında dağıtılır. Detaylar için LICENSE dosyasına bakın.

---

## 👤 İçerik ve Katkı

Alp'e katkıda bulunmak istiyorsanız, GitHub deposundan pull request açabilirsiniz.

---

## 📞 Destek

Sorun veya öneriniz varsa:

1. GitHub Issues'da bildirin
2. Logları kontrol edin: `~/.alp/logs/`
3. `alp help` komutunu çalıştırın

---

**Alp Package Manager** - GitHub'dan Paket Yönetimi İçin Gelişmiş Bir Çözüm 🚀
