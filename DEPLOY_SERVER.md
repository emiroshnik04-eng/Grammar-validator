# Развертывание Catalog Validator на сервере

Инструкция по установке и настройке Catalog Validator для использования менеджерами по сети.

---

## Содержание

1. [Требования](#требования)
2. [Вариант 1: Windows Server](#вариант-1-windows-server)
3. [Вариант 2: Linux Server (Ubuntu/Debian)](#вариант-2-linux-server-ubuntudebian)
4. [Настройка firewall](#настройка-firewall)
5. [Доступ для менеджеров](#доступ-для-менеджеров)
6. [Обслуживание](#обслуживание)

---

## Требования

### Общие требования:

- **Python 3.8+**
- **4 ГБ RAM** (минимум)
- **10 ГБ свободного места** на диске
- **Интернет-соединение** (для OpenAI API)
- **OpenAI API ключ** (обязательно!)

### Сетевые требования:

- Доступный порт **8080** (или другой по выбору)
- Статический IP адрес в локальной сети (рекомендуется)

---

## Вариант 1: Windows Server

### Шаг 1: Подготовка сервера

1. **Установите Python 3.8+**
   - Скачайте с https://www.python.org/downloads/
   - При установке отметьте "Add Python to PATH"

2. **Проверьте установку:**
   ```cmd
   python --version
   ```

### Шаг 2: Копирование файлов

1. Скопируйте всю папку проекта на сервер, например:
   ```
   C:\CatalogValidator\
   ```

2. Откройте командную строку и перейдите в папку:
   ```cmd
   cd C:\CatalogValidator
   ```

### Шаг 3: Установка зависимостей

```cmd
pip install -r requirements.txt
```

### Шаг 4: Настройка переменных окружения

1. Создайте файл `.env` в папке проекта:
   ```
   OPENAI_API_KEY=sk-ваш-ключ-здесь
   SERVER_HOST=0.0.0.0
   SERVER_PORT=8080
   ```

2. Получите OpenAI API ключ на https://platform.openai.com/api-keys

### Шаг 5: Запуск сервера

**Вариант A: Ручной запуск (для тестирования)**

Дважды кликните на `start_server.bat` или выполните:
```cmd
start_server.bat
```

**Вариант B: Запуск как Windows Service (для постоянной работы)**

1. Установите `nssm` (Non-Sucking Service Manager):
   - Скачайте с https://nssm.cc/download
   - Распакуйте в `C:\nssm`

2. Откройте командную строку от имени администратора:
   ```cmd
   cd C:\nssm\win64
   nssm install CatalogValidator
   ```

3. В открывшемся окне настройте:
   - **Path:** `C:\Python312\python.exe` (путь к Python)
   - **Startup directory:** `C:\CatalogValidator`
   - **Arguments:** `web_app.py`

4. На вкладке "Environment" добавьте:
   ```
   OPENAI_API_KEY=sk-ваш-ключ
   SERVER_HOST=0.0.0.0
   SERVER_PORT=8080
   ```

5. Запустите сервис:
   ```cmd
   nssm start CatalogValidator
   ```

### Шаг 6: Узнайте IP адрес сервера

```cmd
ipconfig
```

Найдите строку `IPv4 Address` (например, `192.168.1.100`)

---

## Вариант 2: Linux Server (Ubuntu/Debian)

### Шаг 1: Подготовка сервера

```bash
# Обновление системы
sudo apt-get update
sudo apt-get upgrade -y

# Установка Python и зависимостей
sudo apt-get install -y python3 python3-pip python3-venv git
```

### Шаг 2: Копирование файлов

```bash
# Скопируйте файлы проекта на сервер
# Например, через scp или git:
cd /opt
sudo git clone https://ваш-репозиторий.git catalog-validator
# или скопируйте файлы вручную
```

### Шаг 3: Автоматическая установка

```bash
cd /opt/catalog-validator
sudo chmod +x install_linux.sh
sudo ./install_linux.sh
```

Скрипт автоматически:
- Создаст виртуальное окружение
- Установит зависимости
- Настроит systemd service
- Настроит автозапуск

### Шаг 4: Ручная установка (альтернатива)

Если автоматическая установка не сработала:

```bash
# Создание виртуального окружения
cd /opt/catalog-validator
python3 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt

# Создание .env файла
nano .env
```

Добавьте в `.env`:
```
OPENAI_API_KEY=sk-ваш-ключ
SERVER_HOST=0.0.0.0
SERVER_PORT=8080
```

```bash
# Копирование systemd service
sudo cp catalog-validator.service /etc/systemd/system/
sudo nano /etc/systemd/system/catalog-validator.service
# Измените API ключ в файле

# Создание директорий для логов
sudo mkdir -p /var/log/catalog-validator
sudo chown www-data:www-data /var/log/catalog-validator

# Настройка прав
sudo chown -R www-data:www-data /opt/catalog-validator

# Запуск сервиса
sudo systemctl daemon-reload
sudo systemctl enable catalog-validator
sudo systemctl start catalog-validator
```

### Шаг 5: Проверка статуса

```bash
sudo systemctl status catalog-validator
sudo journalctl -u catalog-validator -f
```

### Шаг 6: Узнайте IP адрес

```bash
hostname -I
```

---

## Настройка Firewall

### Windows:

1. Откройте "Брандмауэр Windows в режиме повышенной безопасности"
2. Создайте правило для входящих подключений:
   - Порт: **8080**
   - Протокол: **TCP**
   - Разрешить подключение

Или через командную строку:
```cmd
netsh advfirewall firewall add rule name="Catalog Validator" dir=in action=allow protocol=TCP localport=8080
```

### Linux (Ubuntu/Debian):

```bash
sudo ufw allow 8080/tcp
sudo ufw reload
```

### Linux (CentOS/RHEL):

```bash
sudo firewall-cmd --permanent --add-port=8080/tcp
sudo firewall-cmd --reload
```

---

## Доступ для менеджеров

После настройки сервера менеджеры смогут открыть в браузере:

```
http://IP_СЕРВЕРА:8080
```

Например:
```
http://192.168.1.100:8080
```

### Создание удобной ссылки:

Для удобства можно:

1. **Настроить DNS** в локальной сети:
   ```
   http://catalog.company.local:8080
   ```

2. **Использовать имя компьютера** (Windows):
   ```
   http://SERVER-NAME:8080
   ```

3. **Создать закладку в браузерах** менеджеров

---

## Обслуживание

### Просмотр логов:

**Windows:**
```cmd
type catalog_validator.log
```

**Linux:**
```bash
sudo journalctl -u catalog-validator -f
tail -f /var/log/catalog-validator/error.log
```

### Перезапуск сервиса:

**Windows Service (через nssm):**
```cmd
nssm restart CatalogValidator
```

**Windows (ручной запуск):**
- Закройте окно консоли
- Запустите `start_server.bat` снова

**Linux:**
```bash
sudo systemctl restart catalog-validator
```

### Остановка сервиса:

**Windows:**
```cmd
nssm stop CatalogValidator
```

**Linux:**
```bash
sudo systemctl stop catalog-validator
```

### Обновление кода:

1. Остановите сервис
2. Скопируйте новые файлы
3. Перезапустите сервис

**Linux:**
```bash
sudo systemctl stop catalog-validator
cd /opt/catalog-validator
# Обновите файлы (git pull или копирование)
sudo systemctl start catalog-validator
```

### Мониторинг:

Проверьте что сервис работает:

**Windows:**
```cmd
netstat -ano | findstr :8080
```

**Linux:**
```bash
sudo netstat -tlnp | grep :8080
```

---

## Решение проблем

### Порт уже занят:

```bash
# Linux: найти процесс
sudo lsof -i :8080
sudo kill <PID>

# Windows: найти процесс
netstat -ano | findstr :8080
taskkill /PID <PID> /F
```

### Не запускается сервис:

1. Проверьте логи
2. Убедитесь что установлен OpenAI API ключ
3. Проверьте что установлены все зависимости:
   ```bash
   pip install -r requirements.txt
   ```

### Менеджеры не могут подключиться:

1. Проверьте firewall
2. Убедитесь что сервер запущен с `SERVER_HOST=0.0.0.0`
3. Проверьте что менеджеры в той же сети
4. Попробуйте подключиться локально: http://127.0.0.1:8080

---

## Безопасность

### Рекомендации:

1. **Используйте HTTPS** (настройте Nginx/Apache с SSL)
2. **Добавьте авторизацию** (раскомментируйте в `config.py`)
3. **Ограничьте доступ** по IP в firewall
4. **Регулярно обновляйте** зависимости:
   ```bash
   pip install --upgrade -r requirements.txt
   ```

5. **Храните OpenAI API ключ в секрете**
6. **Настройте резервное копирование** файлов

---

## Дополнительно: Настройка Nginx (опционально)

Для production рекомендуется использовать Nginx как reverse proxy:

```bash
sudo apt-get install nginx

# Создайте конфигурацию
sudo nano /etc/nginx/sites-available/catalog-validator
```

Содержимое файла:
```nginx
server {
    listen 80;
    server_name catalog.company.local;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Активируйте конфигурацию
sudo ln -s /etc/nginx/sites-available/catalog-validator /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

Теперь доступ по: `http://catalog.company.local` (без порта)

---

**Готово! Теперь менеджеры могут работать с инструментом через браузер.**
