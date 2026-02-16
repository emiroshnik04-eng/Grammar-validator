# Запрос к DevOps на деплой Catalog Validator

## 📋 Описание

Веб-приложение для валидации грамматики и согласования в каталогах товаров (русский язык).

**Текущая версия:** https://catalog-validator.onrender.com (на бесплатном хостинге)
**Нужно:** Развернуть на корпоративном Kubernetes кластере

---

## 🔗 Репозиторий

```
https://gitlab.lalafo.com.ua/ekaterina.miroshnik/catalog-grammar-validator
```

---

## ✅ Готовность к деплою

- ✅ Dockerfile готов и протестирован
- ✅ Kubernetes манифесты готовы (папка `kubernetes/`)
- ✅ GitLab CI/CD pipeline настроен (`.gitlab-ci.yml`)
- ✅ Документация: `KUBERNETES_DEPLOY.md`
- ✅ Health checks настроены
- ✅ Resource limits определены

---

## 🎯 Требования

### Технические:
- **Язык:** Python 3.11+
- **Фреймворк:** FastAPI
- **Порт:** 8080
- **Replicas:** 2 (для надёжности)
- **Memory:** 512Mi-2Gi
- **CPU:** 250m-1000m

### Зависимости:
- pymorphy3 (морфологический анализ)
- LanguageTool (проверка грамматики)
- OpenAI API (LLM для семантического анализа)

---

## 🔐 Секреты

Нужно создать Kubernetes Secret:

```bash
kubectl create secret generic catalog-validator-secrets \
  --from-literal=openai-api-key="API_KEY_ЗДЕСЬ" \
  -n default
```

API ключ можно взять из `.env` файла в репозитории или у меня.

---

## 🌐 DNS

**Желаемый домен:**
```
catalog-validator.yallasvc.net
```

**Требуется:**
- Ingress с SSL/TLS (cert-manager)
- A-запись на Load Balancer IP

---

## 📦 Деплой (3 команды)

```bash
# 1. Клонировать репозиторий
git clone https://gitlab.lalafo.com.ua/ekaterina.miroshnik/catalog-grammar-validator.git
cd catalog-grammar-validator

# 2. Создать secret (ВАЖНО!)
kubectl create secret generic catalog-validator-secrets \
  --from-literal=openai-api-key="YOUR_API_KEY" \
  -n default

# 3. Применить манифесты
kubectl apply -f kubernetes/
```

**Проверка:**
```bash
kubectl get pods -l app=catalog-validator
kubectl get ingress catalog-validator
```

---

## 🚀 GitLab CI/CD (опционально)

Для автоматического деплоя при `git push`:

1. Настроить GitLab Runner с доступом к K8s
2. Добавить переменные в GitLab CI/CD Settings:
   - `KUBE_CONTEXT`
   - `KUBE_NAMESPACE`
   - `CI_REGISTRY_USER`
   - `CI_REGISTRY_PASSWORD`

После настройки: `git push` → автоматический деплой за 2-3 минуты.

---

## 📊 Мониторинг

**Health check endpoint:**
```
GET https://catalog-validator.yallasvc.net/api/health
```

**Ожидаемый ответ:**
```json
{
  "status": "healthy",
  "llm_configured": true,
  "version": "1.0.0"
}
```

**Логи:**
```bash
kubectl logs -l app=catalog-validator -n default --tail=100
```

---

## 🎯 Ожидаемый результат

После деплоя:
- ✅ Приложение доступно по https://catalog-validator.yallasvc.net
- ✅ SSL/TLS сертификат работает
- ✅ Health check возвращает 200 OK
- ✅ Веб-интерфейс открывается
- ✅ Загрузка CSV работает
- ✅ 2 pod'а в статусе Running

---

## 📖 Документация

**Полная документация для DevOps:**
- `KUBERNETES_DEPLOY.md` - пошаговый гайд (60+ страниц)
- `DOCKER_QUICKSTART.md` - быстрый старт
- `kubernetes/` - все манифесты
- `.gitlab-ci.yml` - CI/CD конфигурация

---

## 🆘 Поддержка

**Контакты:**
- Ekaterina Miroshnik
- GitLab: @ekaterina.miroshnik

**Помощь:**
Могу помочь с любыми вопросами по деплою, настройке, отладке.

---

## ⏱️ Оценка времени

- Деплой: 10-15 минут
- Настройка CI/CD: 15-20 минут (опционально)
- Настройка DNS: 5 минут

**Итого:** ~30 минут для полной настройки

---

## ✅ Чеклист для DevOps

- [ ] Клонирован репозиторий
- [ ] Secret с API ключом создан
- [ ] Манифесты применены
- [ ] Pods запущены (2 реплики)
- [ ] Service создан
- [ ] Ingress настроен
- [ ] DNS настроен
- [ ] SSL сертификат получен
- [ ] Health check работает (200 OK)
- [ ] Веб-интерфейс открывается
- [ ] Тестовая загрузка CSV работает
- [ ] GitLab Runner настроен (опционально)
- [ ] Мониторинг настроен

---

**Готово к деплою! 🚀**

Все вопросы - пишите!
