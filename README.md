## Foodgram

Проект доступен по адресу https://foodgrampracticum.ddns.net
Логин для доступа в админку: admin_admin@example.com
пароль: password

Foodgram — это онлайн-сервис, где пользователи могут публиковать рецепты, смотреть рецепты других пользователей. добавлять рецепты в избранное и список покупок, подписываться на понравившихся авторов.

Проект соответствует спецификации OpenAPI и полностью готов к развёртыванию в Docker.

---

## Технологии

- **Python 3.12**
- **Django 4.2 + Django REST Framework**
- **PostgreSQL**
- **Docker + Docker Compose**
- **Gunicorn + Nginx**
- **Token Authentication**

## Как развернуть проект

1. Установить docker и docker-compose:
```
sudo apt update
sudo apt install curl
curl -fSL https://get.docker.com -o get-docker.sh
sudo sh ./get-docker.sh
sudo apt install docker-compose-plugin
```
2. Клонировать репозиторий и перейти в него в командной строке:

```
git clone https://github.com/matkunova/foodgram.git
cd foodgram
```
3. Создать файл .env со следующим содержимым:
```
POSTGRES_USER=foodgram_user
POSTGRES_PASSWORD=mysecretpassword
POSTGRES_DB=foodgram
DB_HOST=db
DB_PORT=5432
```
4. Запустить контейнеры:
```
sudo docker compose up --build
```

## После запуска:

База данных инициализируется
Применяются миграции
Загружаются ингредиенты
Собираются статические файлы
Запускается Gunicorn и Nginx

## Документация API и примеры запросов
Доступны по адресу https://foodgrampracticum.ddns.net/api/docs/
