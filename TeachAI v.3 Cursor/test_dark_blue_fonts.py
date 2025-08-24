#!/usr/bin/env python3
"""
Тест темно-синих шрифтов
Проверяет, что все шрифты теперь темно-синие вместо черных
"""

import ipywidgets as widgets
from IPython.display import display, HTML

def test_dark_blue_fonts():
    """Тестирует темно-синие шрифты"""
    
    print("🔵 ТЕСТ ТЕМНО-СИНИХ ШРИФТОВ")
    print("=" * 50)
    
    # Тестовый HTML контент
    test_html = """
    <div class="lesson-content">
        <h1>Заголовок 1 - должен быть темно-синим</h1>
        <h2>Заголовок 2 - тоже темно-синий</h2>
        
        <p>Это обычный текст с <code>переменная = значение</code> внутри.</p>
        
        <p>Вот несколько примеров inline кода:</p>
        <ul>
            <li><code>print("Hello")</code> - функция вывода</li>
            <li><code>def function():</code> - определение функции</li>
            <li><code>import os</code> - импорт модуля</li>
        </ul>
        
        <p>И блок кода для сравнения:</p>
        <pre><code>def example():
    x = 10
    y = 20
    return x + y</code></pre>
        
        <p>Еще inline код: <code>result = example()</code></p>
        
        <p><strong>Жирный текст</strong> и <em>курсив</em> тоже должны быть темно-синими.</p>
        
        <blockquote>
            Это цитата - должна быть темно-синей на светло-сером фоне
        </blockquote>
    </div>
    """
    
    # CSS стили с темно-синими шрифтами (как в исправленном lesson_display.py)
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
    </style>
    """
    
    # HTML с добавленными стилями
    html_with_styles = css_styles + test_html
    
    print("📝 Тестовый HTML контент:")
    print(test_html)
    print("\n" + "=" * 50)
    
    print("🎨 Примененные CSS стили:")
    print("- Основной цвет: #1a365d (темно-синий)")
    print("- Убран черный цвет: #000000")
    print("- Убрана черная заливка")
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
    
    print("🚀 Отображаем результат с темно-синими шрифтами...")
    display(content_html)
    
    print("\n✅ Тест завершен! Проверьте, что:")
    print("   - Все шрифты темно-синие (#1a365d)")
    print("   - Нет черных шрифтов (#000000)")
    print("   - Нет черной заливки")
    print("   - Сохранен контраст и читаемость")
    
    return html_with_styles

if __name__ == "__main__":
    test_dark_blue_fonts()
