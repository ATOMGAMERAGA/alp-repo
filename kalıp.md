# Alp Paket Şablonu

Bu dosya, Alp Package Manager üzerinde yayınlanacak projeler için **README.md** şablonudur.

## Bilgi Alanları

Alp, aşağıdaki bilgileri README.md dosyasından otomatik olarak çıkartır:

### Gerekli Alanlar

```
name = myproject
ver = 1.0.0
des = Projeleriniz için harika bir araç
```

### Opsiyonel Alanlar

```
author = Kullanıcı Adı
license = MIT
category = development
deps = [dep1, dep2, dep3]
```

## Tam Örnek

```markdown
# MyProject

name = myproject
ver = 1.0.0
des = Dosya işlemleri için basit ve hızlı bir CLI aracı
author = John Doe
license = MIT
category = utilities
deps = [python-requests, python-click]

## Açıklama

Bu proje, dosyaları yönetmek için kullanılan bir CLI aracıdır.

### Özellikler
- Dosya yönetimi
- Batch işlemleri
- Loglama

### Kurulum

Alp aracılığıyla:
```bash
alp install myproject
```

### Kullanım

```bash
myproject --help
```

### Lisans

MIT License
```

## Alp Scriptleri

### alp.sh - Kurulum Scripti

Bu script, paket yüklenirken çalıştırılır:

```bash
#!/bin/bash
set -e

echo "Kurulum başlıyor..."

# Bağımlılıkları yükle
sudo apt-get update
sudo apt-get install -y python3 python3-pip

# Projeyi klonla
git clone https://github.com/username/myproject.git /opt/myproject
cd /opt/myproject

# Bağımlılıkları kur
pip3 install -r requirements.txt

# Sistem komutu oluştur
sudo ln -sf /opt/myproject/myproject.py /usr/local/bin/myproject
sudo chmod +x /usr/local/bin/myproject

echo "✅ Kurulum tamamlandı!"
```

### alp_u.sh - Kaldırma Scripti

Bu script, paket kaldırılırken çalıştırılır:

```bash
#!/bin/bash
set -e

echo "Kaldırma başlıyor..."

# Sistem komutunu sil
sudo rm -f /usr/local/bin/myproject

# Proje dizinini sil
sudo rm -rf /opt/myproject

# Bağımlılıkları temizle (isteğe bağlı)
# pip3 uninstall -y myproject-package

echo "✅ Kaldırma tamamlandı!"
```

## Kategori Türleri

- `utilities` - Sistem araçları
- `development` - Geliştirme araçları
- `web` - Web uygulamaları
- `database` - Veritabanı araçları
- `monitoring` - İzleme araçları
- `education` - Eğitim araçları
- `misc` - Diğer

## Bağımlılıklar

Bağımlılıkları şu şekilde belirtin:

```
deps = [python3, git, curl]
```

Alp, bağımlılıkları otomatik olarak çözer ve sırasıyla yükler.

## Versioning

Versiyon numarası Semantic Versioning kullanmalıdır:

- `1.0.0` - Major.Minor.Patch
- `2.1.3` - İyileştirilmiş versioning

## Kontrol Listesi

Projenizi Alp'e gönderirken kontrol edin:

- [ ] README.md dosyasında tüm gerekli alanlar mevcut
- [ ] alp.sh scripti kurulum yapıyor
- [ ] alp_u.sh scripti kaldırma yapıyor
- [ ] Bağımlılıklar doğru belirtilmiş
- [ ] Repository public ve erişilebilir
- [ ] Versiyon numarası belirtilmiş

## Repo.alp Dosyasına Ekleme

Projenizi `repo.alp`'ye eklemek için GitHub URL'sini ekleyin:

```
https://github.com/username/myproject
https://github.com/username/another-project
```

Her satırda bir proje URL'si olmalıdır.
