from django.db import connection

def update_content_types():
    cursor = connection.cursor()
    try:
        # Проверяем, существует ли колонка content_type
        cursor.execute("PRAGMA table_info(app_news)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'content_type' in columns:
            print("Обновление типов контента...")
            
            # Здесь вы можете определить логику для разделения новостей и статей
            # Например, по заголовку, категории или другим признакам
            
            # Пример: все записи с категорией 'article' становятся статьями
            cursor.execute("UPDATE app_news SET content_type = 'article' WHERE category = 'article'")
            
            # Пример: все остальные записи становятся новостями
            cursor.execute("UPDATE app_news SET content_type = 'news' WHERE content_type IS NULL OR content_type = ''")
            
            print("Типы контента успешно обновлены!")
        else:
            print("Колонка content_type не существует в таблице app_news")
    except Exception as e:
        print(f"Ошибка при обновлении типов контента: {e}")
    finally:
        cursor.close()

if __name__ == "__main__":
    update_content_types() 