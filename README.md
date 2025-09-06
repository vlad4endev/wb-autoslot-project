# WB AutoSlot - Автоматический поиск слотов Wildberries

Полнофункциональная система для автоматического поиска и бронирования слотов поставок на Wildberries.

## 🚀 Возможности

- **Автоматический поиск слотов** - Реальный парсинг WB с использованием Playwright
- **Автоматическое бронирование** - Автоматическое бронирование найденных слотов
- **Система задач** - Создание и управление задачами поиска
- **Фоновые воркеры** - Периодический поиск слотов в фоновом режиме
- **Уведомления** - Email и Telegram уведомления о найденных слотах
- **Безопасность** - JWT аутентификация, валидация данных, логирование
- **Docker** - Полная контейнеризация для легкого развертывания

## 🏗️ Архитектура

### Backend (Flask API)
- **Flask** - Web framework
- **SQLAlchemy** - ORM для работы с БД
- **Playwright** - Автоматизация браузера для WB
- **JWT** - Аутентификация
- **Celery** - Фоновые задачи (планируется)

### Frontend (React)
- **React 19** - UI framework
- **Vite** - Build tool
- **Tailwind CSS** - Стилизация
- **Radix UI** - UI компоненты
- **React Router** - Роутинг

## 📦 Установка

### Локальная разработка

1. **Клонируйте репозиторий**
```bash
git clone <repository-url>
cd wb-autoslot-project
```

2. **Настройте Backend**
```bash
cd wb-autoslot-api
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

3. **Настройте Frontend**
```bash
cd wb-autoslot-frontend
npm install -g pnpm
pnpm install
```

4. **Настройте переменные окружения**
```bash
cp env.example .env
# Отредактируйте .env файл
```

5. **Запустите приложение**
```bash
# Backend
cd wb-autoslot-api
python src/main.py

# Frontend (в новом терминале)
cd wb-autoslot-frontend
pnpm dev
```

### Docker

1. **Запустите с Docker Compose**
```bash
docker-compose up -d
```

2. **Или соберите образы отдельно**
```bash
# Backend
docker build -t wb-autoslot-api .

# Frontend
cd wb-autoslot-frontend
docker build -t wb-autoslot-frontend .
```

## 🔧 Конфигурация

### Переменные окружения

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `FLASK_ENV` | Режим Flask | `development` |
| `SECRET_KEY` | Секретный ключ Flask | `dev-secret-key` |
| `JWT_SECRET_KEY` | Секретный ключ JWT | `jwt-secret-string` |
| `DATABASE_URL` | URL базы данных | `sqlite:///app.db` |
| `LOG_LEVEL` | Уровень логирования | `INFO` |
| `NOTIFICATIONS_ENABLED` | Включить уведомления | `false` |
| `EMAIL_SMTP_SERVER` | SMTP сервер | - |
| `TELEGRAM_BOT_TOKEN` | Токен Telegram бота | - |

### Настройка уведомлений

#### Email
```env
NOTIFICATIONS_ENABLED=true
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
EMAIL_FROM=WB AutoSlot <noreply@example.com>
```

#### Telegram
```env
NOTIFICATIONS_ENABLED=true
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id
```

## 📱 Использование

### 1. Регистрация и вход
- Откройте приложение в браузере
- Зарегистрируйтесь с номером телефона
- Войдите в систему

### 2. Настройка аккаунта WB
- Перейдите в раздел "Настройки"
- Добавьте аккаунт Wildberries
- Вставьте cookies для автоматической авторизации

### 3. Создание задачи
- Нажмите "Создать задачу"
- Укажите параметры поиска:
  - Название задачи
  - Период поиска
  - Склад
  - Минимальный коэффициент
  - Тип упаковки
  - WB аккаунт (опционально)
  - Автоматическое бронирование

### 4. Мониторинг
- Просматривайте статус задач в дашборде
- Отслеживайте события в журнале
- Получайте уведомления о найденных слотах

## 🔒 Безопасность

- **JWT аутентификация** - Безопасные токены доступа
- **Валидация данных** - Проверка всех входных данных
- **Логирование** - Детальные логи всех операций
- **Rate limiting** - Защита от спама
- **CORS** - Настройка кросс-доменных запросов

## 📊 Мониторинг

### Логи
- `logs/app.log` - Общие логи приложения
- `logs/error.log` - Логи ошибок
- `logs/wb_service.log` - Логи WB сервиса
- `logs/task_worker.log` - Логи воркера задач

### API Endpoints

#### Аутентификация
- `POST /api/auth/register` - Регистрация
- `POST /api/auth/login` - Вход
- `GET /api/auth/me` - Текущий пользователь

#### Задачи
- `GET /api/tasks` - Список задач
- `POST /api/tasks` - Создать задачу
- `PUT /api/tasks/{id}` - Обновить задачу
- `DELETE /api/tasks/{id}` - Удалить задачу
- `POST /api/tasks/{id}/{action}` - Действия с задачей

#### WB Аккаунты
- `GET /api/wb-accounts` - Список аккаунтов
- `POST /api/wb-accounts` - Добавить аккаунт
- `PUT /api/wb-accounts/{id}` - Обновить аккаунт
- `DELETE /api/wb-accounts/{id}` - Удалить аккаунт

#### Воркер
- `GET /api/worker/status` - Статус воркера
- `POST /api/worker/tasks/{id}/start` - Запустить задачу
- `POST /api/worker/tasks/{id}/stop` - Остановить задачу

## 🚀 Развертывание

### Production

1. **Настройте переменные окружения**
```bash
cp env.example .env
# Отредактируйте .env файл с production настройками
```

2. **Инициализируйте миграции БД**
```bash
cd wb-autoslot-api
python init_migrations.py init
```

3. **Запустите с Docker**
```bash
# Автоматическое развертывание
./deploy.sh production

# Или вручную
docker-compose -f docker-compose.prod.yml up -d
```

4. **Настройте SSL сертификаты**
```bash
# Получите SSL сертификаты
certbot certonly --standalone -d your-domain.com

# Скопируйте сертификаты
cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ssl/cert.pem
cp /etc/letsencrypt/live/your-domain.com/privkey.pem ssl/key.pem

# Раскомментируйте HTTPS блок в nginx.prod.conf
```

5. **Настройте автоматические бэкапы**
```bash
# Запустите планировщик бэкапов
python3 backup_scheduler.py
```

### Мониторинг

- **API документация**: http://localhost:5000/api/docs/
- **Метрики Prometheus**: http://localhost:5000/metrics
- **Health check**: http://localhost:5000/api/health
- **Детальная диагностика**: http://localhost:5000/api/health/detailed

## 🐛 Устранение неполадок

### Частые проблемы

1. **Playwright не работает**
```bash
# Установите зависимости
playwright install chromium
playwright install-deps
```

2. **Ошибки базы данных**
```bash
# Пересоздайте базу данных
rm database/app.db
python src/main.py
```

3. **Проблемы с WB авторизацией**
- Проверьте актуальность cookies
- Убедитесь, что аккаунт WB активен
- Попробуйте обновить cookies

## ✨ Новые возможности v2.1

### 🗄️ Система миграций БД
- **Flask-Migrate** - Автоматические миграции базы данных
- **Скрипт инициализации** - `python init_migrations.py init`
- **Управление версиями** - Отслеживание изменений схемы БД

### 📊 Мониторинг и метрики
- **Prometheus метрики** - `/metrics` endpoint
- **Системные метрики** - CPU, память, диск
- **Метрики приложения** - Запросы, задачи, слоты
- **Health checks** - Kubernetes-ready endpoints

### 💾 Система бэкапов
- **Автоматические бэкапы** - Ежедневные и еженедельные
- **Множественные форматы** - SQLite, PostgreSQL, файлы
- **Сжатие и архивирование** - Экономия места
- **API управления** - `/api/backup/*` endpoints
- **Планировщик** - `backup_scheduler.py`

### 📚 API документация
- **Swagger UI** - `/api/docs/` - Интерактивная документация
- **Flask-RESTX** - Автоматическая генерация документации
- **Модели данных** - Валидация и сериализация
- **Примеры запросов** - Готовые к использованию

### 🔧 Улучшения DevOps
- **Redis в dev** - Кеширование и rate limiting
- **Расширенные тесты** - Unit тесты для новых сервисов
- **Руководство по развертыванию** - `DEPLOYMENT_GUIDE.md`
- **Автоматизация** - Скрипты инициализации и развертывания

## 📈 Планы развития

- [x] **PostgreSQL** - Производственная база данных ✅
- [x] **API документация** - Swagger/OpenAPI ✅
- [x] **Мониторинг** - Prometheus метрики ✅
- [x] **Система бэкапов** - Автоматические бэкапы ✅
- [ ] **Celery + Redis** - Улучшенная система фоновых задач
- [ ] **Микросервисы** - Разделение на отдельные сервисы
- [ ] **Grafana дашборды** - Визуализация метрик
- [ ] **Мобильное приложение** - React Native версия

## 📄 Лицензия

MIT License

## 🤝 Вклад в проект

1. Fork репозитория
2. Создайте feature branch
3. Commit изменения
4. Push в branch
5. Создайте Pull Request

## 📞 Поддержка

- **Issues** - GitHub Issues
- **Discussions** - GitHub Discussions
- **Email** - support@wbauotslot.com

---

**⚠️ Внимание**: Используйте на свой страх и риск. Соблюдайте правила Wildberries и не злоупотребляйте автоматизацией.
