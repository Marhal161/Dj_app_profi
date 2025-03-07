# Django Project Setup Guide

Этот документ содержит инструкции по настройке и запуску проекта на Django с использованием базы данных SQLite.

## Требования

- Python 3.x
- pip (менеджер пакетов Python)

## Установка

1. **Клонируйте репозиторий:**

   ```sh
   git clone https://github.com/Marhal161/Dj_app_profi.git
   cd chemistry

## 2. Создайте виртуальное окружение и активируйте его:

bash
### Windows

python -m venv venv
venv\Scripts\activate

### Linux/macOS

python3 -m venv venv
source venv/bin/activate

3. Установите зависимости:

bash

pip install -r requirements.txt

4. Примените миграции:

bash
python manage.py migrate

5. Запустите сервер разработки:

bash
python manage.py runserver

6. Откройте браузер и перейдите по адресу:

    http://127.0.0.1:8000/