from django.db import connection

def add_content_type_field():
    cursor = connection.cursor()
    try:
        # Проверяем, существует ли уже колонка
        cursor.execute("PRAGMA table_info(app_news)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'content_type' not in columns:
            print("Добавление поля content_type в таблицу app_news...")
            cursor.execute("ALTER TABLE app_news ADD COLUMN content_type VARCHAR(10) DEFAULT 'news'")
            print("Поле content_type успешно добавлено!")
        else:
            print("Поле content_type уже существует в таблице app_news")
    except Exception as e:
        print(f"Ошибка при добавлении поля: {e}")
    finally:
        cursor.close()

if __name__ == "__main__":
    add_content_type_field() 