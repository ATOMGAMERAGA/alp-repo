FROM python:3.11-slim

LABEL maintainer="ALP Package Manager"
LABEL description="Advanced Linux Package Management System"
LABEL version="2.2"

# Sistem paketlerini güncelle ve gerekli araçları yükle
RUN apt-get update && apt-get install -y \
    git \
    wget \
    curl \
    bash \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Çalışma dizinini oluştur
WORKDIR /app

# Alp manager'ı kopyala
COPY alp_manager.py /app/alp_manager.py

# Çalıştırma izinlerini ayarla
RUN chmod +x /app/alp_manager.py

# Alp home dizinini oluştur
RUN mkdir -p /root/.alp/cache /root/.alp/logs /root/.alp/installed

# Sembolik link oluştur (global erişim için)
RUN ln -sf /app/alp_manager.py /usr/local/bin/alp

# Varsayılan komut
CMD ["python3", "/app/alp_manager.py", "help"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 /app/alp_manager.py stats || exit 1
