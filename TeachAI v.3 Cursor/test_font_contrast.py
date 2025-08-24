#!/usr/bin/env python3
"""
Тестовый файл для проверки контраста шрифтов
"""

from content_formatter_final import ContentFormatterFinal
import ipywidgets as widgets
from IPython.display import display, HTML

def test_font_contrast():
    """Тестирует контраст шрифтов в ContentFormatterFinal"""
    
    print("🔍 ТЕСТИРОВАНИЕ КОНТРАСТА ШРИФТОВ")
    print("=" * 50)
    
    # Создаем экземпляр ContentFormatterFinal
    formatter = ContentFormatterFinal()
    
    # Тестовый контент с разными элементами
    test_content = """
# Тестовый заголовок H1

## Подзаголовок H2

### Подзаголовок H3

Это обычный текст с **жирным выделением** и *курсивом*.

Вот пример inline кода: `переменная = значение`

И блок кода:

```python
def test_function():
    print("Hello, World!")
    return True
```

- Элемент списка 1
- Элемент списка 2
- Элемент списка 3

1. Нумерованный элемент 1
2. Нумерованный элемент 2
3. Нумерованный элемент 3
"""
    
    print("📝 Исходный контент:")
    print(test_content)
    print("\n" + "=" * 50)
    
    # Форматируем контент
    formatted_content = formatter.format_lesson_content(test_content, "Тест контраста")
    
    print("🎨 Отформатированный HTML:")
    print(formatted_content)
    print("\n" + "=" * 50)
    
    # Создаем виджет для отображения
    html_widget = widgets.HTML(
        value=formatted_content,
        layout=widgets.Layout(
            width="100%",
            padding="20px",
            border="2px solid #ff0000",  # Красная рамка для видимости
            border_radius="10px",
            margin="10px 0",
        ),
    )
    
    print("🚀 Отображаем результат в Jupyter...")
    display(html_widget)
    
    # Также показываем как обычный HTML
    print("\n📱 Альтернативное отображение:")
    display(HTML(formatted_content))
    
    return formatted_content

if __name__ == "__main__":
    test_font_contrast()
