#!/usr/bin/env python3
"""
Тест исправления inline кода
Проверяет, что inline код выглядит нормально без желтого фона
"""

import ipywidgets as widgets
from IPython.display import display, HTML

def test_inline_code_fix():
    """Тестирует исправление inline кода"""
    
    print("🔧 ТЕСТ ИСПРАВЛЕНИЯ INLINE КОДА")
    print("=" * 50)
    
    # Тестовый HTML контент
    test_html = """
    <div class="lesson-content">
        <h1>Тест inline кода</h1>
        
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
    </div>
    """
    
    # CSS стили (как в исправленном lesson_display.py)
    css_styles = """
    <style>
    /* Улучшенные стили для контраста */
    .lesson-content {
        color: #000000 !important;
        font-weight: 400 !important;
    }
    
    .lesson-content pre {
        background-color: #f8f8f8 !important;
        border: 1px solid #ddd !important;
        color: #000000 !important;
        padding: 15px !important;
        border-radius: 5px !important;
        overflow-x: auto !important;
    }
    
    .lesson-content code {
        color: #000000 !important;
        font-weight: 700 !important;
        background-color: #f0f0f0 !important;
        padding: 2px 4px !important;
        border-radius: 3px !important;
        border: 1px solid #ccc !important;
    }
    
    .lesson-content pre code {
        background-color: transparent !important;
        color: #000000 !important;
        padding: 0 !important;
        border: none !important;
    }
    
    .lesson-content h1, .lesson-content h2, .lesson-content h3, .lesson-content h4 {
        color: #000000 !important;
        font-weight: 600 !important;
        border-bottom: 1px solid #ddd !important;
    }
    
    .lesson-content p, .lesson-content li {
        color: #000000 !important;
        font-weight: 400 !important;
    }
    
    .lesson-content strong, .lesson-content b {
        color: #000000 !important;
        font-weight: 600 !important;
    }
    
    .lesson-content em, .lesson-content i {
        color: #000000 !important;
        font-style: italic !important;
        font-weight: 400 !important;
    }
    
    .lesson-content blockquote {
        border-left: 3px solid #ddd !important;
        background-color: #f9f9f9 !important;
        color: #000000 !important;
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
    
    print("🚀 Отображаем результат с исправленными стилями...")
    display(content_html)
    
    print("\n✅ Тест завершен! Проверьте, что inline код выглядит нормально.")
    
    return html_with_styles

if __name__ == "__main__":
    test_inline_code_fix()
