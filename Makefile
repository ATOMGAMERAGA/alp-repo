.PHONY: help build run start stop restart logs shell clean test push pull

# Değişkenler
IMAGE_NAME = alp-manager
IMAGE_TAG = latest
CONTAINER_NAME = alp-package-manager
REGISTRY = ghcr.io/atomgameraga

help: ## Yardım menüsünü göster
	@echo "🐳 Alp Package Manager - Docker Komutları"
	@echo "=========================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

build: ## Docker image'ını build et
	@echo "🔨 Building Docker image..."
	docker build -t $(IMAGE_NAME):$(IMAGE_TAG) .

build-no-cache: ## Cache kullanmadan build et
	@echo "🔨 Building Docker image (no cache)..."
	docker build --no-cache -t $(IMAGE_NAME):$(IMAGE_TAG) .

run: ## Container'ı çalıştır (tek seferlik)
	@echo "🚀 Running container..."
	docker run --rm -it \
		-v alp-data:/root/.alp \
		$(IMAGE_NAME):$(IMAGE_TAG) bash

start: ## Docker Compose ile başlat
	@echo "🚀 Starting services..."
	docker-compose up -d

stop: ## Docker Compose ile durdur
	@echo "🛑 Stopping services..."
	docker-compose down

restart: ## Servisleri yeniden başlat
	@echo "🔄 Restarting services..."
	docker-compose restart

logs: ## Logları göster
	@echo "📋 Showing logs..."
	docker-compose logs -f

shell: ## Container'a shell ile bağlan
	@echo "🐚 Opening shell..."
	docker-compose exec alp bash

alp-update: ## Depoyu güncelle
	@echo "📦 Updating repository..."
	docker-compose exec alp alp update

alp-list: ## Paketleri listele
	@echo "📋 Listing packages..."
	docker-compose exec alp alp list

alp-installed: ## Yüklü paketleri göster
	@echo "✅ Showing installed packages..."
	docker-compose exec alp alp installed

alp-stats: ## İstatistikleri göster
	@echo "📊 Showing stats..."
	docker-compose exec alp alp stats

clean: ## Container ve volume'leri temizle
	@echo "🧹 Cleaning up..."
	docker-compose down -v
	docker rmi $(IMAGE_NAME):$(IMAGE_TAG) 2>/dev/null || true

clean-cache: ## Sadece cache'i temizle
	@echo "🗑️ Cleaning cache..."
	docker-compose exec alp alp clean

test: ## Testleri çalıştır
	@echo "🧪 Running tests..."
	docker run --rm $(IMAGE_NAME):$(IMAGE_TAG) alp help
	docker run --rm $(IMAGE_NAME):$(IMAGE_TAG) alp stats

push: ## Image'ı registry'ye push et
	@echo "⬆️ Pushing to registry..."
	docker tag $(IMAGE_NAME):$(IMAGE_TAG) $(REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG)
	docker push $(REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG)

pull: ## Image'ı registry'den çek
	@echo "⬇️ Pulling from registry..."
	docker pull $(REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG)

up-build: ## Build et ve başlat
	@echo "🔨 Building and starting..."
	docker-compose up -d --build

ps: ## Çalışan container'ları göster
	@echo "📊 Container status..."
	docker-compose ps

volumes: ## Volume'leri listele
	@echo "💾 Volumes..."
	docker volume ls | grep alp

backup: ## Volume'leri yedekle
	@echo "💾 Backing up volumes..."
	@mkdir -p backups
	docker run --rm \
		-v alp-data:/data \
		-v $(PWD)/backups:/backup \
		alpine tar czf /backup/alp-backup-$$(date +%Y%m%d-%H%M%S).tar.gz -C /data .
	@echo "✅ Backup created in ./backups/"

restore: ## En son yedeği geri yükle
	@echo "📥 Restoring from latest backup..."
	@LATEST=$$(ls -t backups/alp-backup-*.tar.gz 2>/dev/null | head -1); \
	if [ -z "$$LATEST" ];
