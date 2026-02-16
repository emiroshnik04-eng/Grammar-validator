# 🐳 Docker Quick Start - Для разработчика

## ⚡ За 5 минут

### Тест локально:

```bash
# 1. Соберите образ
docker build -t catalog-validator .

# 2. Запустите
docker run -p 8080:8080 -e OPENAI_API_KEY="ваш_ключ" catalog-validator

# 3. Откройте http://localhost:8080
```

✅ **Работает? Отлично!**

---

## 🏢 Деплой в компании

### Для DevOps:

```bash
# 1. Клонируйте
git clone https://gitlab.lalafo.com.ua/ekaterina.miroshnik/catalog-grammar-validator.git

# 2. Создайте secret
kubectl create secret generic catalog-validator-secrets \
  --from-literal=openai-api-key="API_KEY" -n default

# 3. Деплой
kubectl apply -f kubernetes/

# 4. Проверка
kubectl get pods -l app=catalog-validator
```

**Готово!** Приложение на https://catalog-validator.yallasvc.net

---

## 🤖 Автодеплой

После настройки GitLab CI/CD:

```bash
git add .
git commit -m "My changes"
git push origin main
```

🤖 **Робот задеплоит за вас через 2-3 минуты!**

---

## 📖 Подробная документация

См. [KUBERNETES_DEPLOY.md](KUBERNETES_DEPLOY.md)
