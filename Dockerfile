FROM python:3.11-slim

LABEL maintainer="Alp Package Manager"
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

# Alp home dizinini oluştur ve izinleri ayarla
RUN mkdir -p /root/.alp/cache /root/.alp/logs /root/.alp/installed && \
    chmod -R 755 /root/.alp

# Python'un unbuffered modda çalışması için
ENV PYTHONUNBUFFERED=1

# Sembolik link oluştur (global erişim için)
RUN ln -sf /app/alp_manager.py /usr/local/bin/alp && \
    chmod +x /usr/local/bin/alp

# Varsayılan shell olarak bash kullan
SHELL ["/bin/bash", "-c"]

# Varsayılan komut - shell başlat
CMD ["/bin/bash"]

# Health check - basit bir Python kontrolü
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import sys; sys.exit(0)" || exit 1
