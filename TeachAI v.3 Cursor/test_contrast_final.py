#!/usr/bin/env python3
"""
ФИНАЛЬНЫЙ ТЕСТ КОНТРАСТА ШРИФТОВ
Проверяет максимально агрессивные стили в lesson_display.py
"""

import ipywidgets as widgets
from IPython.display import display, HTML

def test_maximal_contrast():
    """Тестирует максимально агрессивные стили контраста"""
    
    print("🚨 ФИНАЛЬНЫЙ ТЕСТ МАКСИМАЛЬНОГО КОНТРАСТА")
    print("=" * 60)
    
    # Тестовый HTML контент с классом lesson-content
    test_html = """
    <div class="lesson-content">
        <h1>Тестовый заголовок H1</h1>
        <h2>Подзаголовок H2</h2>
        <h3>Подзаголовок H3</h3>
        
        <p>Это обычный текст с <strong>жирным выделением</strong> и <em>курсивом</em>.</p>
        
        <p>Вот пример inline кода: <code>переменная = значение</code></p>
        
        <p>И блок кода:</p>
        <pre><code>def test_function():
    print("Hello, World!")
    return True</code></pre>
        
        <ul>
            <li>Элемент списка 1</li>
            <li>Элемент списка 2</li>
            <li>Элемент списка 3</li>
        </ul>
        
        <ol>
            <li>Нумерованный элемент 1</li>
            <li>Нумерованный элемент 2</li>
            <li>Нумерованный элемент 3</li>
        </ol>
        
        <blockquote>
            Это цитата с максимальным контрастом
        </blockquote>
    </div>
    """
    
    # Дополнительные CSS стили (как в lesson_display.py)
    additional_css = """
    <style>
    /* МАКСИМАЛЬНО АГРЕССИВНЫЕ СТИЛИ ДЛЯ КОНТРАСТА */
    .lesson-content * {
        color: #000000 !important;
        font-weight: 900 !important;
        text-shadow: 0 0 2px rgba(0,0,0,1) !important;
    }
    
    .lesson-content pre * {
        color: #ffffff !important;
        background-color: #000000 !important;
        font-weight: 900 !important;
        text-shadow: 0 0 3px rgba(255,255,255,1) !important;
    }
    
    .lesson-content code {
        color: #000000 !important;
        font-weight: 900 !important;
        text-shadow: 0 0 3px rgba(0,0,0,1) !important;
        background-color: #ffff00 !important;
        padding: 2px 4px !important;
        border-radius: 3px !important;
    }
    
    .lesson-content pre {
        background-color: #000000 !important;
        border: 3px solid #ffffff !important;
        color: #ffffff !important;
    }
    
    .lesson-content h1, .lesson-content h2, .lesson-content h3, .lesson-content h4 {
        color: #000000 !important;
        font-weight: 900 !important;
        text-shadow: 0 0 4px rgba(0,0,0,1) !important;
        border-bottom: 3px solid #000000 !important;
    }
    
    .lesson-content p, .lesson-content li, .lesson-content strong, .lesson-content b, .lesson-content em, .lesson-content i {
        color: #000000 !important;
        font-weight: 900 !important;
        text-shadow: 0 0 2px rgba(0,0,0,1) !important;
    }
    
    .lesson-content blockquote {
        border-left: 5px solid #000000 !important;
        background-color: #ffffff !important;
        color: #000000 !important;
        font-weight: 900 !important;
        border: 3px solid #000000 !important;
        padding: 15px !important;
        margin: 20px 0 !important;
    }
    </style>
    """
    
    # HTML с добавленными стилями
    html_with_styles = additional_css + test_html
    
    print("📝 Тестовый HTML контент:")
    print(test_html)
    print("\n" + "=" * 60)
    
    # Создаем виджет с максимально агрессивными стилями
    content_html = widgets.HTML(
        value=html_with_styles,
        layout=widgets.Layout(
            width="100%",
            padding="20px",
            border="3px solid #000000",
            border_radius="10px",
            margin="10px 0",
            background_color="#ffffff",
        ),
    )
    
    print("🚀 Отображаем результат с максимальным контрастом...")
    display(content_html)
    
    # Также показываем как обычный HTML для сравнения
    print("\n📱 Альтернативное отображение:")
    display(HTML(html_with_styles))
    
    print("\n✅ Тест завершен! Проверьте контраст шрифтов выше.")
    
    return html_with_styles

if __name__ == "__main__":
    test_maximal_contrast()
