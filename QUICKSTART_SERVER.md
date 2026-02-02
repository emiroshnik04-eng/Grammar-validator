# Быстрый старт - Серверное развертывание

Catalog Validator теперь готов к развертыванию на сервере для использования менеджерами по сети.

---

## Для Windows Server

### Самый простой способ:

1. **Скопируйте проект на сервер**
   ```
   Например: C:\CatalogValidator\
   ```

2. **Создайте файл `.env`** (скопируйте из `.env.example`)
   ```
   OPENAI_API_KEY=sk-ваш-ключ-здесь
   SERVER_HOST=0.0.0.0
   SERVER_PORT=8080
   ```

3. **Запустите сервер**
   ```
   Дважды кликните: start_server.bat
   ```

4. **Узнайте IP адрес сервера**
   ```cmd
   ipconfig
   ```
   Найдите IPv4 Address (например, 192.168.1.100)

5. **Менеджеры открывают в браузере:**
   ```
   http://192.168.1.100:8080
   ```

**Готово!**

---

## Для Linux Server (Ubuntu/Debian)

### Автоматическая установка:

```bash
# Скопируйте проект на сервер в /opt/catalog-validator
cd /opt/catalog-validator

# Запустите установочный скрипт
sudo chmod +x install_linux.sh
sudo ./install_linux.sh
```

Скрипт сделает всё автоматически:
- Создаст виртуальное окружение
- Установит зависимости
- Настроит автозапуск (systemd)
- Запустит сервис

### Управление сервисом:

```bash
sudo systemctl start catalog-validator   # Запустить
sudo systemctl stop catalog-validator    # Остановить
sudo systemctl status catalog-validator  # Проверить статус
sudo systemctl restart catalog-validator # Перезапустить
```

### Просмотр логов:

```bash
sudo journalctl -u catalog-validator -f
```

### Узнать IP адрес:

```bash
hostname -I
```

Менеджеры открывают: `http://IP_АДРЕС:8080`

---

## Настройка Firewall (ВАЖНО!)

### Windows:

```cmd
netsh advfirewall firewall add rule name="Catalog Validator" dir=in action=allow protocol=TCP localport=8080
```

### Linux:

```bash
sudo ufw allow 8080/tcp
sudo ufw reload
```

---

## Проверка работы

1. На сервере откройте: `http://127.0.0.1:8080`
2. С другого компьютера: `http://IP_СЕРВЕРА:8080`

Если не открывается - проверьте firewall!

---

## Полная документация

Подробные инструкции в файле: [DEPLOY_SERVER.md](DEPLOY_SERVER.md)

---

## Что дальше?

- Сервер автоматически перезапускается при ошибках
- Логи сохраняются для диагностики
- Менеджеры работают через браузер без установки
- Все изменения применяются автоматически при перезапуске

**Приятной работы!**
