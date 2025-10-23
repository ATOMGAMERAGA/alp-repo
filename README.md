# Alp Package Manager

Alp, projeleri kolayca paketleyip yüklemenizi, bağımlılıkları yönetmenizi ve sisteminizi sağlıklı tutmanızı sağlayan hafif bir paket yöneticisidir. Sertifika sistemi (cerf.alpc) ile güven ve şeffaflık sunar.

## Özellikler
- Hızlı paket güncelleme ve kurulum (`alp update`, `alp install`)
- Bağımlılık kontrolü ve çözümleme
- Projeleri `.alp` dosyasına derleme (`alp compile`)
- Yerel `.alp` paketlerini kurma (`alp install-local`)
- Sertifika sistemi: `cert-info`, `cert-create`, `cert-scan`
- Sistem sağlık taraması (`alp doctor`) ve istatistikler (`alp stats`)
- Cache temizleme ve kendi kendini güncelleme (`alp clean`, `alp self-update`)

---

## Kurulum

### Linux (Tek Komut)
```bash
sudo curl -fsSL https://raw.githubusercontent.com/ATOMGAMERAGA/alp-repo/main/install.sh | bash
```
- Kurulum, `~/.alp` dizinini hazırlar ve gerekli dosyaları indirir.
- Komut sonrası `alp` komutunu terminalde kullanabilirsiniz.

### Windows (Python ile)
1. Python 3 yüklü olduğundan emin olun.
2. Depoyu indirin veya klonlayın:
   ```powershell
   git clone https://github.com/ATOMGAMERAGA/alp-repo.git
   cd alp-repo
   ```
3. Komutları çalıştırın:
   ```powershell
   python alp_manager.py help
   python alp_manager.py update
   ```
4. İsteğe bağlı alias (PowerShell):
   ```powershell
   Set-Alias alp "python C:\Genel\Code\alp-repo\alp_manager.py"
   # Sonra: alp help
   ```

### Docker (Container)
Docker ile hızlı kurulum ve izole çalışma ortamı.

- Docker Hub: https://hub.docker.com/r/atomgameraga/alp-manager

Çek ve çalıştır:
```bash
docker pull atomgameraga/alp-manager:latest
docker run --rm -it atomgameraga/alp-manager alp help
```

Veri kalıcılığı (named volume):
```bash
docker run --rm \
  -v alp-data:/root/.alp \
  atomgameraga/alp-manager alp update
```

İnteraktif shell:
```bash
docker run -it --rm \
  -v alp-data:/root/.alp \
  atomgameraga/alp-manager bash
# Container içinde:
alp update
alp list
alp install myapp
```

Detaylı kullanım ve Compose: `DOCKER.md`

### Güncelleme
```bash
alp self-update
```
- Son sürümü indirir, syntax kontrolü yapar ve güvenli şekilde günceller.

---

## Hızlı Başlangıç
```bash
alp update              # Depoyu güncelle
alp search web          # Arama yap
alp install myapp       # Paket kur
alp installed           # Yüklü paketleri gör
alp info myapp          # Paket detayları
alp doctor              # Sistem sağlık taraması
alp clean               # Cache temizleme
```

---

## Komutlar

### Paket Yönetimi
- `alp update` — Depoyu güncelle
- `alp install <paket>` — Paket yükle
- `alp remove <paket>` — Paket kaldır
- `alp upgrade [paket]` — Tüm veya tek paket güncelle

### Listeleme ve Bilgi
- `alp list [kategori]` — Tüm/kategoriye göre listele
- `alp installed` — Yüklü paketleri göster
- `alp search <anahtar>` — Paket ara
- `alp info <paket>` — Paket detaylarını göster

### Geliştirici Araçları
- `alp compile <dizin>` — Proje dizinini `.alp` dosyasına derle
- `alp install-local <dosya>` — Yerel `.alp` paketini kur

### Sertifika Sistemi (cerf.alpc)
- `alp cert-info <paket>` — Paket sertifikasını göster
- `alp cert-create <type> <author> <pkg>` — Sertifika dosyası oluştur
  - Etkileşimli mod: `alp cert-create` (türü, yazar ve paket adı sorulur)
  - Tipler: `official`, `dev`, `normal`
- `alp cert-scan <github_url>` — GitHub reposunda `cerf.alpc` taraması yap

### Sistem
- `alp stats` — İstatistikleri göster
- `alp doctor` — Sağlık taraması (kurulum, bağımlılık, cache)
- `alp clean` — Cache’i temizle
- `alp self-update` — Alp’i güncelle
- `alp config` — Yapılandırmayı göster
- `alp help` — Yardım

---

## Sertifika Sistemi: cerf.alpc
Alp, paketlerin güvenilirliğini artırmak için `cerf.alpc` dosyalarını destekler.
- `official` — Resmi Alp sertifikalı paketler
- `dev` — Geliştirici sertifikalı paketler
- `normal` — Normal sertifikalı paketler
- `unsigned` — Sertifikasız paketler (uyarı verir)

`alp update` sırasında repo README ve `cerf.alpc` taranır; listelerde ve `info` çıktısında rozetler gösterilir.

Örnek kullanım:
```bash
alp cert-info myapp
alp cert-create normal "Jane Doe" myapp
alp cert-scan https://github.com/kullanici/proje
```

---

## Paket Geliştirme ve Derleme

### README.md Formatı
Proje kökünde basit meta bilgiler olmalı:
```markdown
# MyProject

name = myproject
ver = 1.0.0
des = Dosya işlemleri için harika bir CLI aracı
author = John Doe
license = MIT
category = utilities
deps = [python3, git]
```
Zorunlu: `name`, `ver`, `des`

### Kurulum Scripti: `alp.sh`
- Proje köküne `alp.sh` ekleyin.
- Paket kurulum/kaldırma adımlarını içerir (Linux uyumlu bash).

### Derleme
```bash
alp compile ./myproject
# Çıktı: myproject-1.0.0.alp
```

### Yerel Paket Kurma
```bash
alp install-local myproject-1.0.0.alp
```

---

## Dizin Yapısı
```
~/.alp/
├── packages.json          # Tüm mevcut paketler
├── installed.json         # Yüklü paketler
├── config.json            # Alp yapılandırması
├── cache/                 # İndirilen dosyaların cache’i
│   └── *.sh               # Kurulum/kaldırma scriptleri
├── logs/                  # İşlem logları
│   └── alp_*.log          # Tarih/saatli loglar
└── installed/             # Yüklü paketler
    └── <paket>/installed.json
```

---

## Sistem Sağlığı ve Sorun Giderme
- `alp doctor` — Bozuk kurulumlar, eksik bağımlılıklar ve cache sorunlarını tarar.
- `alp clean` — Cache’i temizler; disk alanı kazanımı sağlar.
- `alp self-update` — Alp’i güvenli şekilde günceller.

Örnek `alp doctor` çıktısı:
```
🩺 Sistem Sağlık Taraması
────────────────────────────────────────────────────────────────────────────────
✅ Dizin durumu: OK
⚠️ installed.json uyumsuz kayıtlar: 1
   └─ Kayıp paket dizini: myapp
⚠️ Bağımlılık sorunları: 2
   ├─ ggs: eksik -> [python3]
   └─ webtools: eksik -> [curl, git]
⚠️ Cache sorunları: 1
   └─ Yarım indirme: cache/webtools-2.0.0/install.sh.partial
────────────────────────────────────────────────────────────────────────────────
Öneriler:
- Run: alp clean
- Reinstall missing packages: alp install myapp
- Resolve deps: alp install python3 curl git
```

---

## Sık Karşılaşılan Komutlar
- `alp update` — Depoyu güncelle
- `alp install <paket>` — Paket kur
- `alp remove <paket>` — Paket kaldır
- `alp installed` — Yüklü paketleri gör
- `alp doctor` — Sistem taraması
- `alp cert-info <paket>` — Sertifika bilgisi

---

## Katkı ve Geri Bildirim
- Hata/suggestion: GitHub Issues
- Katkı: Pull Request açabilirsiniz
- İletişim ve destek: repo açıklamalarına bakınız

---

## Lisans
Bu proje topluluğa açık şekilde geliştirilmektedir. Lisans bilgisi proje kökünde belirtilir.
