# 🐳 Alp Package Manager - Docker Kurulum Rehberi

Bu rehber, Alp Package Manager'ı Docker kullanarak nasıl kuracağınızı ve çalıştıracağınızı detaylı bir şekilde açıklar.

## 📋 İçindekiler

1. [Gereksinimler](#gereksinimler)
2. [Hızlı Başlangıç](#hızlı-başlangıç)
3. [Docker ile Kurulum](#docker-ile-kurulum)
4. [Docker Compose ile Kurulum](#docker-compose-ile-kurulum)
5. [Kullanım Örnekleri](#kullanım-örnekleri)
6. [Volume Yönetimi](#volume-yönetimi)
7. [Sorun Giderme](#sorun-giderme)
8. [GitHub Actions CI/CD](#github-actions-cicd)

---

## 🔧 Gereksinimler

- **Docker**: 20.10 veya üzeri
- **Docker Compose**: 2.0 veya üzeri (opsiyonel)
- **İşletim Sistemi**: Linux, macOS, Windows (WSL2)

### Docker Kurulumu

#### Linux (Ubuntu/Debian)
```bash
# Docker'ı kur
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Docker Compose'u kur
sudo apt-get update
sudo apt-get install docker-compose-plugin

# Kullanıcıyı docker grubuna ekle
sudo usermod -aG docker $USER
newgrp docker
```

#### macOS
```bash
# Homebrew ile Docker Desktop'ı kur
brew install --cask docker
```

#### Windows
[Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/) indir ve kur.

---

## ⚡ Hızlı Başlangıç

### Pre-built Image Kullanımı (GitHub Container Registry)

```bash
# Image'ı çek
docker pull ghcr.io/atomgameraga/alp-repo:latest

# Container'ı çalıştır
docker run -it --rm ghcr.io/atomgameraga/alp-repo:latest alp help
```

### Yerel Build

```bash
# Repository'yi klonla
git clone https://github.com/ATOMGAMERAGA/alp-repo.git
cd alp-repo

# Docker image'ını build et
docker build -t alp-manager:latest .

# Container'ı çalıştır
docker run -it --rm alp-manager:latest alp help
```

---

## 🐋 Docker ile Kurulum

### 1. Image Build Etme

```bash
# Repository dizininde
docker build -t alp-manager:latest .

# Build argümanları ile (opsiyonel)
docker build \
  --build-arg PYTHON_VERSION=3.11 \
  -t alp-manager:2.2 \
  .
```

### 2. Container Çalıştırma

#### Tek Komut Çalıştırma
```bash
# Yardım menüsünü göster
docker run --rm alp-manager:latest alp help

# Depoyu güncelle
docker run --rm -v alp-data:/root/.alp alp-manager:latest alp update

# Paket ara
docker run --rm alp-manager:latest alp search python
```

#### İnteraktif Mod
```bash
# İnteraktif shell ile başlat
docker run -it --rm \
  -v alp-data:/root/.alp \
  alp-manager:latest bash

# Container içinde komutlar çalıştır
alp update
alp list
alp install mypackage
```

#### Detached Mode (Arka Planda)
```bash
# Container'ı arka planda çalıştır
docker run -d \
  --name alp-manager \
  -v alp-data:/root/.alp \
  alp-manager:latest tail -f /dev/null

# Container'a bağlan
docker exec -it alp-manager bash

# Container'ı durdur
docker stop alp-manager

# Container'ı kaldır
docker rm alp-manager
```

---

## 🎼 Docker Compose ile Kurulum

### 1. docker-compose.yml Hazırlama

`docker-compose.yml` dosyası zaten hazır. İsterseniz özelleştirebilirsiniz:

```yaml
version: '3.8'

services:
  alp:
    build:
      context: .
      dockerfile: Dockerfile
    image: alp-manager:latest
    container_name: alp-package-manager
    
    volumes:
      - alp-data:/root/.alp
      - alp-packages:/root/.alp/installed
      - alp-cache:/root/.alp/cache
      - alp-logs:/root/.alp/logs
    
    environment:
      - TZ=Europe/Istanbul
      - PYTHONUNBUFFERED=1
      - ALP_AUTO_UPDATE=true
    
    restart: unless-stopped
    stdin_open: true
    tty: true
    
    networks:
      - alp-network

volumes:
  alp-data:
  alp-packages:
  alp-cache:
  alp-logs:

networks:
  alp-network:
```

### 2. Compose ile Çalıştırma

```bash
# Build ve başlat
docker-compose up -d

# Logları izle
docker-compose logs -f

# Container'a bağlan
docker-compose exec alp bash

# Container içinde komut çalıştır
docker-compose exec alp alp update
docker-compose exec alp alp list

# Durdur
docker-compose down

# Volume'ler ile birlikte kaldır
docker-compose down -v
```

---

## 💡 Kullanım Örnekleri

### Paket Yönetimi

```bash
# Depoyu güncelle
docker run --rm -v alp-data:/root/.alp alp-manager:latest alp update

# Paketleri listele
docker run --rm alp-manager:latest alp list

# Paket ara
docker run --rm alp-manager:latest alp search web

# Paket bilgisi
docker run --rm alp-manager:latest alp info mypackage

# Paket yükle
docker run --rm -v alp-data:/root/.alp alp-manager:latest alp install mypackage

# Yüklü paketleri göster
docker run --rm -v alp-data:/root/.alp alp-manager:latest alp installed

# Paket kaldır
docker run --rm -v alp-data:/root/.alp alp-manager:latest alp remove mypackage

# Tüm paketleri güncelle
docker run --rm -v alp-data:/root/.alp alp-manager:latest alp upgrade
```

### Geliştirici Komutları

```bash
# Paket derle (yerel dizinden)
docker run --rm \
  -v $(pwd)/my-package:/workspace \
  -v alp-data:/root/.alp \
  -w /workspace \
  alp-manager:latest alp compile .

# Yerel .alp dosyasını kur
docker run --rm \
  -v $(pwd):/workspace \
  -v alp-data:/root/.alp \
  -w /workspace \
  alp-manager:latest alp install-local mypackage-1.0.0.alp

# Sertifika bilgisi
docker run --rm -v alp-data:/root/.alp alp-manager:latest alp cert-info mypackage
```

### Sistem Komutları

```bash
# İstatistikleri göster
docker run --rm -v alp-data:/root/.alp alp-manager:latest alp stats

# Cache temizle
docker run --rm -v alp-data:/root/.alp alp-manager:latest alp clean

# Alp'i güncelle
docker run --rm -v alp-data:/root/.alp alp-manager:latest alp self-update

# Konfigürasyonu göster
docker run --rm -v alp-data:/root/.alp alp-manager:latest alp config
```

---

## 📦 Volume Yönetimi

### Volume'leri Görüntüleme

```bash
# Tüm volume'leri listele
docker volume ls

# Alp volume'lerini filtrele
docker volume ls | grep alp

# Volume detaylarını göster
docker volume inspect alp-data
```

### Volume'leri Yedekleme

```bash
# Volume'ü tar.gz olarak yedekle
docker run --rm \
  -v alp-data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/alp-backup-$(date +%Y%m%d).tar.gz -C /data .

# Alternatif: Docker cp kullanarak
docker run -d --name alp-temp -v alp-data:/data alpine tail -f /dev/null
docker cp alp-temp:/data ./alp-backup
docker rm -f alp-temp
```

### Volume'leri Geri Yükleme

```bash
# Yedekten geri yükle
docker run --rm \
  -v alp-data:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/alp-backup-20240101.tar.gz -C /data
```

### Volume'leri Temizleme

```bash
# Belirli bir volume'ü sil
docker volume rm alp-cache

# Kullanılmayan tüm volume'leri sil
docker volume prune

# Tüm alp volume'lerini sil
docker volume ls | grep alp | awk '{print $2}' | xargs docker volume rm
```

---

## 🔍 Sorun Giderme

### Container Loglarını İnceleme

```bash
# Docker Compose ile
docker-compose logs alp

# Docker ile
docker logs alp-package-manager

# Canlı log takibi
docker logs -f alp-package-manager
```

### Container İçine Girme

```bash
# İnteraktif shell
docker exec -it alp-package-manager bash

# Root kullanıcısı ile
docker exec -it -u root alp-package-manager bash

# Tek komut çalıştır
docker exec alp-package-manager alp stats
```

### Ağ Sorunları

```bash
# Container'ın network bilgisi
docker inspect alp-package-manager | grep -A 20 NetworkSettings

# Ping testi
docker exec alp-package-manager ping -c 3 google.com

# DNS testi
docker exec alp-package-manager nslookup github.com
```

### Permission Sorunları

```bash
# Volume izinlerini kontrol et
docker exec alp-package-manager ls -la /root/.alp

# İzinleri düzelt
docker exec -u root alp-package-manager chown -R root:root /root/.alp
docker exec -u root alp-package-manager chmod -R 755 /root/.alp
```

### Container Yeniden Başlatma

```bash
# Soft restart
docker restart alp-package-manager

# Hard restart
docker stop alp-package-manager && docker start alp-package-manager

# Docker Compose ile
docker-compose restart alp
```

---

## 🚀 GitHub Actions CI/CD

### Workflow Özellikleri

Repository'de `.github/workflows/docker-build-push.yml` dosyası şunları yapar:

1. **Otomatik Build**: Her push ve PR'da
2. **Multi-platform Build**: linux/amd64, linux/arm64
3. **Container Registry**: GitHub Container Registry (GHCR)
4. **Docker Hub**: (opsiyonel, secrets gerekli)
5. **Güvenlik Tarama**: Docker Scout ile CVE kontrolü
6. **Otomatik Test**: Build sonrası test komutları

### Secrets Yapılandırması

GitHub Repository Settings > Secrets and variables > Actions:

```
DOCKERHUB_USERNAME: your-dockerhub-username
DOCKERHUB_TOKEN: your-dockerhub-token
```

### Workflow Tetikleme

```bash
# Manuel tetikleme (GitHub UI'dan)
Actions > Docker Build and Push > Run workflow

# Tag ile tetikleme
git tag v2.2.0
git push origin v2.2.0

# Branch push ile
git push origin main
```

### Image Kullanımı

```bash
# GitHub Container Registry'den
docker pull ghcr.io/atomgameraga/alp-repo:latest

# Docker Hub'dan (yapılandırıldıysa)
docker pull yourusername/alp-manager:latest

# Belirli tag
docker pull ghcr.io/atomgameraga/alp-repo:v2.2.0
```

---

## 📝 Best Practices

### 1. Volume Kullanımı
```bash
# Her zaman named volume kullan
docker run -v alp-data:/root/.alp ...

# Bind mount yerine volume tercih et
```

### 2. Resource Limits
```bash
# CPU ve memory limitleri
docker run --cpus=2 --memory=1g alp-manager:latest
```

### 3. Security
```bash
# Root olmayan kullanıcı ile çalıştır (production için)
docker run --user 1000:1000 alp-manager:latest

# Read-only root filesystem
docker run --read-only alp-manager:latest
```

### 4. Monitoring
```bash
# Container stats
docker stats alp-package-manager

# Health check
docker inspect --format='{{.State.Health.Status}}' alp-package-manager
```

---

## 🎯 İleri Seviye Kullanım

### Custom Dockerfile

```dockerfile
FROM alp-manager:latest

# Ekstra paketler yükle
RUN apt-get update && apt-get install -y \
    vim \
    htop \
    net-tools

# Özel scriptler ekle
COPY scripts/ /usr/local/bin/

# Başlangıç komutunu değiştir
CMD ["alp", "stats"]
```

### Docker Compose Override

```yaml
# docker-compose.override.yml
version: '3.8'

services:
  alp:
    environment:
      - DEBUG=true
    ports:
      - "8080:8080"
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: alp-manager
spec:
  replicas: 1
  selector:
    matchLabels:
      app: alp
  template:
    metadata:
      labels:
        app: alp
    spec:
      containers:
      - name: alp
        image: ghcr.io/atomgameraga/alp-repo:latest
        volumeMounts:
        - name: alp-data
          mountPath: /root/.alp
      volumes:
      - name: alp-data
        persistentVolumeClaim:
          claimName: alp-pvc
```

---

## 📞 Yardım ve Destek

- **GitHub Issues**: [https://github.com/ATOMGAMERAGA/alp-repo/issues](https://github.com/ATOMGAMERAGA/alp-repo/issues)
- **Docker Hub**: [https://hub.docker.com/r/yourusername/alp-manager](https://hub.docker.com/r/yourusername/alp-manager)
- **GitHub Container Registry**: [https://ghcr.io/atomgameraga/alp-repo](https://ghcr.io/atomgameraga/alp-repo)

---

## 📄 Lisans

Bu proje MIT Lisansı altında lisanslanmıştır.

---

## 🎉 Katkıda Bulunma

Pull request'ler memnuniyetle karşılanır! Büyük değişiklikler için lütfen önce bir issue açın.

```bash
# Fork et
# Branch oluştur
git checkout -b feature/amazing-feature

# Commit et
git commit -m 'feat: Add amazing feature'

# Push et
git push origin feature/amazing-feature

# Pull Request aç
```

---

**Mutlu Kodlamalar! 🚀**
