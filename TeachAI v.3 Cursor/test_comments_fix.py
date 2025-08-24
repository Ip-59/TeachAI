#!/usr/bin/env python3
"""
Тест исправления комментариев
Проверяет, что комментарии в коде отображаются правильно без HTML тегов
"""

import ipywidgets as widgets
from IPython.display import display, HTML

def test_comments_fix():
    """Тестирует исправление отображения комментариев"""
    
    print("💬 ТЕСТ ИСПРАВЛЕНИЯ КОММЕНТАРИЕВ")
    print("=" * 50)
    
    # Тестовый HTML контент с комментариями
    test_html = """
    <div class="lesson-content">
        <h1>Тест комментариев в коде</h1>
        
        <p>Вот пример кода с комментариями:</p>
        
        <pre><code>import os
import sys

# Загружаем данные
data = load_dataset()

# Разделяем данные на обучающий и тестовый наборы
X_train, X_test = split_data(data)

# Обучаем модель
model = train_model(X_train)

# Делаем предсказания на тестовом наборе
predictions = model.predict(X_test)

# Выводим результат
print(f"Точность: {accuracy_score(predictions)}")</code></pre>
        
        <p>Inline код: <code># это комментарий</code></p>
        
        <p>Еще один блок кода:</p>
        <pre><code>def example():
    # Инициализация переменных
    x = 10
    y = 20
    
    # Вычисление результата
    result = x + y
    
    # Возврат значения
    return result</code></pre>
    </div>
    """
    
    # CSS стили с исправленными комментариями
    css_styles = """
    <style>
    /* Улучшенные стили для контраста с темно-синими шрифтами */
    .lesson-content {
        color: #1a365d !important;
        font-weight: 400 !important;
    }
    
    .lesson-content pre {
        background-color: #f8f8f8 !important;
        border: 1px solid #ddd !important;
        color: #1a365d !important;
        padding: 15px !important;
        border-radius: 5px !important;
        overflow-x: auto !important;
    }
    
    .lesson-content code {
        color: #1a365d !important;
        font-weight: 700 !important;
        background-color: #f0f0f0 !important;
        padding: 2px 4px !important;
        border-radius: 3px !important;
        border: 1px solid #ccc !important;
    }
    
    .lesson-content pre code {
        background-color: transparent !important;
        color: #1a365d !important;
        padding: 0 !important;
        border: none !important;
    }
    
    .lesson-content h1, .lesson-content h2, .lesson-content h3, .lesson-content h4 {
        color: #1a365d !important;
        font-weight: 600 !important;
        border-bottom: 1px solid #ddd !important;
    }
    
    .lesson-content p, .lesson-content li {
        color: #1a365d !important;
        font-weight: 400 !important;
    }
    
    .lesson-content strong, .lesson-content b {
        color: #1a365d !important;
        font-weight: 600 !important;
    }
    
    .lesson-content em, .lesson-content i {
        color: #1a365d !important;
        font-style: italic !important;
        font-weight: 400 !important;
    }
    
    .lesson-content blockquote {
        border-left: 3px solid #ddd !important;
        background-color: #f9f9f9 !important;
        color: #1a365d !important;
        font-style: italic !important;
        padding: 10px 15px !important;
        margin: 15px 0 !important;
    }
    
    .lesson-content .comment {
        color: #6b7280 !important;
        font-style: italic !important;
        background-color: #f3f4f6 !important;
        padding: 1px 3px !important;
        border-radius: 2px !important;
    }
    </style>
    """
    
    # HTML с добавленными стилями
    html_with_styles = css_styles + test_html
    
    print("📝 Тестовый HTML контент:")
    print(test_html)
    print("\n" + "=" * 50)
    
    print("🎨 Примененные CSS стили:")
    print("- Основной цвет: #1a365d (темно-синий)")
    print("- Комментарии: #6b7280 (серый) с светло-серым фоном")
    print("- Убраны HTML теги из комментариев")
    print("- Сохранен контраст и читаемость")
    print("\n" + "=" * 50)
    
    # Создаем виджет с исправленными стилями
    content_html = widgets.HTML(
        value=html_with_styles,
        layout=widgets.Layout(
            width="100%",
            padding="20px",
            border="1px solid #ddd",
            border_radius="8px",
            margin="10px 0",
            background_color="#ffffff",
        ),
    )
    
    print("🚀 Отображаем результат с исправленными комментариями...")
    display(content_html)
    
    print("\n✅ Тест завершен! Проверьте, что:")
    print("   - Комментарии отображаются серым цветом")
    print("   - Нет HTML тегов <span class=\"comment\"> на экране")
    print("   - Комментарии имеют светло-серый фон")
    print("   - Код читается легко и понятно")
    
    return html_with_styles

if __name__ == "__main__":
    test_comments_fix()
