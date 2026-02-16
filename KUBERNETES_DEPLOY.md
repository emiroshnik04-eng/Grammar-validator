# Развертывание Catalog Validator на Kubernetes

## 📋 Содержание
1. [Быстрый старт](#быстрый-старт)
2. [Локальное тестирование Docker](#локальное-тестирование)
3. [Деплой на Kubernetes](#деплой-на-kubernetes)
4. [GitLab CI/CD автодеплой](#gitlab-cicd)
5. [Проверка работоспособности](#проверка)
6. [Troubleshooting](#troubleshooting)

---

## 🚀 Быстрый старт

### Для DevOps команды:

```bash
# 1. Клонировать репозиторий
git clone https://gitlab.lalafo.com.ua/ekaterina.miroshnik/catalog-grammar-validator.git
cd catalog-grammar-validator

# 2. Создать secret с API ключом
kubectl create secret generic catalog-validator-secrets \
  --from-literal=openai-api-key="YOUR_OPENAI_API_KEY" \
  -n default

# 3. Применить манифесты
kubectl apply -f kubernetes/

# 4. Проверить статус
kubectl get pods -l app=catalog-validator
kubectl get ingress catalog-validator

# 5. Готово! Открыть в браузере:
# https://catalog-validator.yallasvc.net
```

---

## 🐳 Локальное тестирование Docker

### Шаг 1: Сборка образа

```bash
cd d:\TestProject
docker build -t catalog-validator:test .
```

**Что происходит:**
- Загружается Python 3.11
- Устанавливаются все зависимости из requirements.txt
- Копируется весь код приложения
- Настраивается порт 8080

**Время сборки:** ~3-5 минут (первый раз)

---

### Шаг 2: Запуск контейнера

```bash
docker run -d \
  --name catalog-validator-test \
  -p 8080:8080 \
  -e OPENAI_API_KEY="ваш_ключ_здесь" \
  catalog-validator:test
```

**Параметры:**
- `-d` - запуск в фоне
- `-p 8080:8080` - проброс порта
- `-e` - переменные окружения
- `--name` - имя контейнера

---

### Шаг 3: Проверка

Откройте в браузере:
```
http://localhost:8080
```

Вы увидите тот же веб-интерфейс что и на Render! ✅

**Проверка логов:**
```bash
docker logs catalog-validator-test
```

**Проверка здоровья:**
```bash
curl http://localhost:8080/api/health
```

Должен вернуть:
```json
{
  "status": "healthy",
  "llm_configured": true,
  "version": "1.0.0"
}
```

---

### Шаг 4: Остановка и очистка

```bash
# Остановить
docker stop catalog-validator-test

# Удалить контейнер
docker rm catalog-validator-test

# Удалить образ
docker rmi catalog-validator:test
```

---

## ☸️ Деплой на Kubernetes

### Предварительные требования:

1. ✅ Доступ к Kubernetes кластеру
2. ✅ kubectl настроен и подключён
3. ✅ Namespace создан (или используется `default`)
4. ✅ Ingress Controller установлен (nginx)
5. ✅ Docker Registry доступен (GitLab Registry)

---

### Шаг 1: Создание Secret с API ключом

**Вариант A: Через kubectl**

```bash
kubectl create secret generic catalog-validator-secrets \
  --from-literal=openai-api-key="sk-svcacct-HpoESy0-..." \
  -n default
```

**Вариант B: Через YAML**

```bash
# Отредактируйте kubernetes/deployment.yaml
# Замените ЗАМЕНИТЕ_НА_ВАШ_КЛЮЧ на реальный ключ
kubectl apply -f kubernetes/deployment.yaml
```

**Проверка:**
```bash
kubectl get secret catalog-validator-secrets -n default
```

---

### Шаг 2: Сборка и Push Docker образа

**Если GitLab CI/CD не настроен, соберите вручную:**

```bash
# Логин в GitLab Registry
docker login registry.gitlab.lalafo.com.ua

# Сборка
docker build -t registry.gitlab.lalafo.com.ua/ekaterina.miroshnik/catalog-grammar-validator:latest .

# Push
docker push registry.gitlab.lalafo.com.ua/ekaterina.miroshnik/catalog-grammar-validator:latest
```

---

### Шаг 3: Применение манифестов

```bash
# Применить все манифесты
kubectl apply -f kubernetes/

# Или по отдельности:
kubectl apply -f kubernetes/deployment.yaml
kubectl apply -f kubernetes/service.yaml
kubectl apply -f kubernetes/ingress.yaml
```

**Что создаётся:**
- ✅ Deployment с 2 репликами
- ✅ Service (ClusterIP на порту 80)
- ✅ Ingress для внешнего доступа
- ✅ Secret с API ключом

---

### Шаг 4: Проверка деплоя

**Проверить pods:**
```bash
kubectl get pods -l app=catalog-validator -n default

# Должно быть:
# NAME                                  READY   STATUS    RESTARTS   AGE
# catalog-validator-xxxx-yyyy           1/1     Running   0          2m
# catalog-validator-xxxx-zzzz           1/1     Running   0          2m
```

**Проверить service:**
```bash
kubectl get svc catalog-validator -n default

# Должно быть:
# NAME                TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)   AGE
# catalog-validator   ClusterIP   10.96.xxx.xxx   <none>        80/TCP    2m
```

**Проверить ingress:**
```bash
kubectl get ingress catalog-validator -n default

# Должно быть:
# NAME                HOSTS                              ADDRESS         PORTS     AGE
# catalog-validator   catalog-validator.yallasvc.net    x.x.x.x         80, 443   2m
```

**Проверить логи:**
```bash
kubectl logs -l app=catalog-validator -n default --tail=50
```

---

### Шаг 5: Настройка DNS

**Попросите сетевого администратора добавить A-запись:**

```
catalog-validator.yallasvc.net  →  IP_ADDRESS_OF_INGRESS
```

**Узнать IP Ingress:**
```bash
kubectl get ingress catalog-validator -n default -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
```

---

### Шаг 6: Проверка доступности

**Откройте в браузере:**
```
https://catalog-validator.yallasvc.net
```

**Или через curl:**
```bash
curl https://catalog-validator.yallasvc.net/api/health
```

**Должен вернуть:**
```json
{
  "status": "healthy",
  "llm_configured": true
}
```

✅ **Готово! Приложение работает!**

---

## 🤖 GitLab CI/CD

### Настройка автоматического деплоя

#### Шаг 1: Настройка GitLab Runner

**Проверьте есть ли Runner:**
```bash
# В GitLab UI:
Settings → CI/CD → Runners
```

Должен быть **активный Runner** с тегами `docker`, `kubernetes`.

#### Шаг 2: Настройка переменных

**В GitLab UI:**
```
Settings → CI/CD → Variables
```

**Добавьте переменные:**

| Variable | Value | Protected | Masked |
|----------|-------|-----------|--------|
| `CI_REGISTRY_USER` | ваш_gitlab_username | ✅ | ❌ |
| `CI_REGISTRY_PASSWORD` | ваш_gitlab_token | ✅ | ✅ |
| `KUBE_CONTEXT` | default | ✅ | ❌ |
| `KUBE_NAMESPACE` | default | ❌ | ❌ |

#### Шаг 3: Настройка Kubernetes доступа

**Создайте ServiceAccount для GitLab:**

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: gitlab-deployer
  namespace: default
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: gitlab-deployer
  namespace: default
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: edit
subjects:
- kind: ServiceAccount
  name: gitlab-deployer
  namespace: default
```

**Получите токен:**
```bash
kubectl create token gitlab-deployer -n default --duration=999999h
```

**Добавьте в GitLab:**
```
Settings → CI/CD → Variables
```
- Name: `KUBE_TOKEN`
- Value: полученный_токен
- Protected: ✅
- Masked: ✅

#### Шаг 4: Тестовый деплой

**Сделайте любое изменение в коде и push:**
```bash
git add .
git commit -m "Test CI/CD pipeline"
git push origin main
```

**В GitLab UI:**
```
CI/CD → Pipelines
```

Вы увидите запущенный pipeline с этапами:
1. ✅ test - проверка синтаксиса
2. ✅ build - сборка Docker образа
3. ⏸️ deploy - ждёт ручного запуска

**Нажмите "Play" на этапе deploy**

Через 2-3 минуты приложение обновится на сервере!

---

## ✅ Проверка работоспособности

### Health Check

```bash
curl https://catalog-validator.yallasvc.net/api/health
```

### Загрузка CSV

```bash
curl -X POST https://catalog-validator.yallasvc.net/api/validate \
  -F "file=@test_catalog.csv"
```

### Проверка категории

```bash
curl -X POST https://catalog-validator.yallasvc.net/api/analyze-category \
  -H "Content-Type: application/json" \
  -d '{"name": "Игрушка", "path": "Детские товары / Игрушка"}'
```

---

## 🔧 Troubleshooting

### Проблема: Pod не запускается

**Симптомы:**
```bash
kubectl get pods
# STATUS: CrashLoopBackOff или Error
```

**Решение:**
```bash
# Проверить логи
kubectl logs -l app=catalog-validator --tail=100

# Проверить describe
kubectl describe pod <pod-name>

# Частые причины:
# 1. Отсутствует OPENAI_API_KEY
# 2. Неправильный Docker образ
# 3. Ошибка в коде
```

---

### Проблема: 502 Bad Gateway

**Симптомы:** Браузер показывает 502 при открытии сайта

**Решение:**
```bash
# Проверить что pods работают
kubectl get pods -l app=catalog-validator

# Проверить service
kubectl get svc catalog-validator

# Проверить ingress
kubectl describe ingress catalog-validator

# Проверить что порты правильные
kubectl get svc catalog-validator -o yaml | grep port
```

---

### Проблема: Долго грузится (медленно)

**Симптомы:** Первый запрос долгий (30-60 сек)

**Причина:** LanguageTool скачивается при первом запуске

**Решение:** Нормально! Последующие запросы будут быстрыми.

Или добавьте initContainer для предзагрузки:
```yaml
initContainers:
- name: download-languagetool
  image: registry.gitlab.lalafo.com.ua/ekaterina.miroshnik/catalog-grammar-validator:latest
  command: ['python', '-c', 'import language_tool_python; language_tool_python.LanguageTool("ru")']
```

---

### Проблема: Недостаточно памяти

**Симптомы:**
```bash
kubectl get pods
# STATUS: OOMKilled
```

**Решение:** Увеличить лимиты в deployment.yaml:
```yaml
resources:
  limits:
    memory: "4Gi"  # Было 2Gi
```

---

## 📚 Дополнительные ресурсы

### Полезные команды

```bash
# Рестарт deployment
kubectl rollout restart deployment/catalog-validator -n default

# Откат к предыдущей версии
kubectl rollout undo deployment/catalog-validator -n default

# Масштабирование
kubectl scale deployment/catalog-validator --replicas=3 -n default

# Логи в реальном времени
kubectl logs -f -l app=catalog-validator -n default

# Выполнить команду в pod
kubectl exec -it <pod-name> -n default -- /bin/bash
```

### Мониторинг

```bash
# Использование ресурсов
kubectl top pods -l app=catalog-validator -n default

# Events
kubectl get events -n default --sort-by='.lastTimestamp' | grep catalog
```

---

## 🎯 Итоговый чеклист

- [ ] Docker образ собран и загружен в registry
- [ ] Secret с OPENAI_API_KEY создан
- [ ] Deployment применён (2 реплики работают)
- [ ] Service создан
- [ ] Ingress настроен
- [ ] DNS запись добавлена
- [ ] Health check возвращает 200 OK
- [ ] Веб-интерфейс открывается в браузере
- [ ] Загрузка CSV работает
- [ ] GitLab CI/CD настроен (опционально)
- [ ] Документация передана команде

✅ **Готово! Приложение работает на Kubernetes!**

---

## 📞 Контакты

- **Репозиторий:** https://gitlab.lalafo.com.ua/ekaterina.miroshnik/catalog-grammar-validator
- **Production URL:** https://catalog-validator.yallasvc.net
- **Render (старый):** https://catalog-validator.onrender.com
