# 🚀 Руководство по развертыванию WB AutoSlot

## 📋 Содержание

1. [Требования к системе](#требования-к-системе)
2. [Быстрый старт](#быстрый-старт)
3. [Конфигурация](#конфигурация)
4. [Развертывание в production](#развертывание-в-production)
5. [Мониторинг и логирование](#мониторинг-и-логирование)
6. [Бэкапы](#бэкапы)
7. [Безопасность](#безопасность)
8. [Устранение неполадок](#устранение-неполадок)

---

## 🖥️ Требования к системе

### Минимальные требования
- **CPU**: 2 ядра
- **RAM**: 4 GB
- **Диск**: 20 GB свободного места
- **ОС**: Linux (Ubuntu 20.04+), macOS, Windows 10+

### Рекомендуемые требования
- **CPU**: 4+ ядер
- **RAM**: 8+ GB
- **Диск**: 50+ GB SSD
- **ОС**: Ubuntu 22.04 LTS

### Программное обеспечение
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Git**: 2.0+

---

## ⚡ Быстрый старт

### 1. Клонирование репозитория
```bash
git clone <repository-url>
cd wb-autoslot-project
```

### 2. Настройка переменных окружения
```bash
cp env.example .env
# Отредактируйте .env файл с вашими настройками
```

### 3. Запуск в development режиме
```bash
# Автоматический запуск
./start.sh

# Или вручную
docker-compose up -d
```

### 4. Проверка работоспособности
```bash
# Проверка API
curl http://localhost:5000/api/health

# Проверка frontend
curl http://localhost:3000
```

---

## ⚙️ Конфигурация

### Переменные окружения

#### Основные настройки
```env
# Режим Flask
FLASK_ENV=production

# Секретные ключи (ОБЯЗАТЕЛЬНО измените в production!)
SECRET_KEY=your-super-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here

# База данных
DATABASE_URL=postgresql://user:password@postgres:5432/wbautoslot

# Redis
REDIS_URL=redis://redis:6379/0
```

#### Настройки уведомлений
```env
# Email уведомления
NOTIFICATIONS_ENABLED=true
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
EMAIL_FROM=WB AutoSlot <noreply@yourdomain.com>

# Telegram уведомления
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id
```

#### Настройки мониторинга
```env
# Prometheus метрики
PROMETHEUS_ENABLED=true
METRICS_ENABLED=true

# Бэкапы
BACKUP_ENABLED=true
BACKUP_RETENTION_DAYS=30
```

### Конфигурация Nginx

#### SSL сертификаты
```bash
# Создайте директорию для SSL
mkdir -p ssl

# Получите SSL сертификаты (Let's Encrypt)
certbot certonly --standalone -d yourdomain.com

# Скопируйте сертификаты
cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ssl/cert.pem
cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ssl/key.pem
```

#### Настройка домена
Отредактируйте `nginx.prod.conf`:
```nginx
server_name yourdomain.com;
```

---

## 🏭 Развертывание в production

### 1. Подготовка сервера

#### Установка Docker
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Установка Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### Настройка файрвола
```bash
# UFW
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

### 2. Развертывание приложения

#### Клонирование и настройка
```bash
git clone <repository-url>
cd wb-autoslot-project

# Настройка переменных
cp env.example .env
nano .env  # Отредактируйте настройки
```

#### Запуск production окружения
```bash
# Использование скрипта развертывания
./deploy.sh production

# Или вручную
docker-compose -f docker-compose.prod.yml up -d
```

#### Проверка развертывания
```bash
# Статус сервисов
docker-compose -f docker-compose.prod.yml ps

# Логи
docker-compose -f docker-compose.prod.yml logs -f

# Проверка здоровья
curl https://yourdomain.com/api/health
```

### 3. Настройка автоматического обновления

#### Создание cron задачи
```bash
# Редактирование crontab
crontab -e

# Добавление задачи для обновления каждые 6 часов
0 */6 * * * cd /path/to/wb-autoslot-project && git pull && docker-compose -f docker-compose.prod.yml up -d
```

#### Создание systemd сервиса
```bash
# Создание сервиса
sudo nano /etc/systemd/system/wb-autoslot.service
```

```ini
[Unit]
Description=WB AutoSlot Service
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/path/to/wb-autoslot-project
ExecStart=/usr/local/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/local/bin/docker-compose -f docker-compose.prod.yml down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

```bash
# Активация сервиса
sudo systemctl enable wb-autoslot.service
sudo systemctl start wb-autoslot.service
```

---

## 📊 Мониторинг и логирование

### Prometheus метрики

#### Доступ к метрикам
```bash
# Просмотр метрик
curl http://localhost:5000/metrics
```

#### Основные метрики
- `http_requests_total` - Общее количество HTTP запросов
- `http_request_duration_seconds` - Время выполнения запросов
- `active_tasks_total` - Количество активных задач
- `slots_found_total` - Количество найденных слотов
- `system_cpu_percent` - Использование CPU
- `system_memory_percent` - Использование памяти

### Логирование

#### Просмотр логов
```bash
# Все сервисы
docker-compose logs -f

# Конкретный сервис
docker-compose logs -f wb-autoslot-api

# Последние 100 строк
docker-compose logs --tail=100 wb-autoslot-api
```

#### Ротация логов
```bash
# Настройка logrotate
sudo nano /etc/logrotate.d/wb-autoslot
```

```
/path/to/wb-autoslot-project/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 root root
    postrotate
        docker-compose restart wb-autoslot-api
    endscript
}
```

### Health checks

#### Kubernetes готовность
```bash
# Readiness check
curl http://localhost:5000/api/health/ready

# Liveness check
curl http://localhost:5000/api/health/live
```

---

## 💾 Бэкапы

### Автоматические бэкапы

#### Настройка расписания
```bash
# Запуск планировщика бэкапов
python3 backup_scheduler.py
```

#### Ручное создание бэкапа
```bash
# Через API
curl -X POST http://localhost:5000/api/backup/create \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type": "full"}'

# Через Docker
docker-compose exec wb-autoslot-api python3 -c "
from src.services.backup_service import backup_service
from src.config import config
from flask import Flask
app = Flask(__name__)
app.config.from_object(config['production'])
backup_service.init_app(app)
with app.app_context():
    result = backup_service.create_full_backup('manual')
    print(result)
"
```

### Восстановление из бэкапа

#### Список бэкапов
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:5000/api/backup/list
```

#### Восстановление
```bash
curl -X POST http://localhost:5000/api/backup/restore \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "backup_path": "/path/to/backup.tar.gz",
    "confirm": true
  }'
```

### Настройка внешнего хранилища

#### AWS S3
```bash
# Установка AWS CLI
pip install awscli

# Настройка
aws configure

# Загрузка бэкапа
aws s3 cp backup.tar.gz s3://your-bucket/backups/
```

#### Google Cloud Storage
```bash
# Установка gsutil
pip install gsutil

# Загрузка бэкапа
gsutil cp backup.tar.gz gs://your-bucket/backups/
```

---

## 🔒 Безопасность

### SSL/TLS

#### Let's Encrypt
```bash
# Установка certbot
sudo apt install certbot

# Получение сертификата
sudo certbot certonly --standalone -d yourdomain.com

# Автоматическое обновление
echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -
```

### Брандмауэр

#### UFW настройка
```bash
# Базовые правила
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Разрешенные порты
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS

# Активация
sudo ufw enable
```

### Обновления безопасности

#### Автоматические обновления
```bash
# Настройка автоматических обновлений
sudo dpkg-reconfigure unattended-upgrades

# Проверка статуса
sudo unattended-upgrades --dry-run
```

### Мониторинг безопасности

#### Fail2ban
```bash
# Установка
sudo apt install fail2ban

# Настройка
sudo nano /etc/fail2ban/jail.local
```

```ini
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = ssh
logpath = /var/log/auth.log
maxretry = 3
```

---

## 🛠️ Устранение неполадок

### Частые проблемы

#### 1. Сервис не запускается
```bash
# Проверка логов
docker-compose logs wb-autoslot-api

# Проверка конфигурации
docker-compose config

# Перезапуск
docker-compose restart wb-autoslot-api
```

#### 2. Проблемы с базой данных
```bash
# Проверка подключения
docker-compose exec postgres psql -U postgres -d wbautoslot -c "SELECT 1;"

# Восстановление из бэкапа
docker-compose exec postgres psql -U postgres -d wbautoslot < backup.sql
```

#### 3. Проблемы с Redis
```bash
# Проверка Redis
docker-compose exec redis redis-cli ping

# Очистка кеша
docker-compose exec redis redis-cli FLUSHALL
```

#### 4. Проблемы с Playwright
```bash
# Переустановка браузеров
docker-compose exec wb-autoslot-api playwright install chromium
docker-compose exec wb-autoslot-api playwright install-deps
```

### Диагностика

#### Проверка ресурсов
```bash
# Использование ресурсов
docker stats

# Дисковое пространство
df -h

# Память
free -h
```

#### Проверка сети
```bash
# Проверка портов
netstat -tlnp | grep :5000
netstat -tlnp | grep :3000

# Проверка DNS
nslookup yourdomain.com
```

#### Проверка логов
```bash
# Системные логи
sudo journalctl -u docker.service

# Логи приложения
tail -f logs/app.log
tail -f logs/error.log
```

### Восстановление

#### Полное восстановление
```bash
# Остановка сервисов
docker-compose down

# Очистка данных
docker system prune -a

# Восстановление из бэкапа
# (см. раздел Бэкапы)

# Запуск
docker-compose up -d
```

---

## 📞 Поддержка

### Полезные команды

#### Управление сервисами
```bash
# Статус
docker-compose ps

# Логи
docker-compose logs -f

# Перезапуск
docker-compose restart

# Обновление
docker-compose pull
docker-compose up -d
```

#### Мониторинг
```bash
# Health check
curl http://localhost:5000/api/health

# Метрики
curl http://localhost:5000/metrics

# Статус воркера
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:5000/api/worker/status
```

### Контакты

- **GitHub Issues**: [Создать issue](https://github.com/your-repo/issues)
- **Email**: support@wbauotslot.com
- **Документация**: [API Docs](http://localhost:5000/api/docs/)

---

**🎉 Поздравляем! Ваше приложение WB AutoSlot успешно развернуто и готово к работе!**
