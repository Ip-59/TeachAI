"""
Тест функции вопросов и ответов TeachAI
"""

from engine import TeachAIEngine


def test_qa_function():
    """Тестирует функцию вопросов и ответов"""
    print("🧪 Тестирование функции вопросов и ответов")
    print("=" * 50)

    # Создаем экземпляр движка
    engine = TeachAIEngine()

    # Инициализируем систему
    if engine.initialize():
        print("✅ Система TeachAI инициализирована")

        # Получаем content_generator
        content_generator = engine.content_generator

        # Тестовый вопрос
        test_question = "почему снег белый?"

        print(f"❓ Тестовый вопрос: {test_question}")

        try:
            # Генерируем ответ
            answer = content_generator.answer_question(
                course="Основы Python",
                section="Основы Python и синтаксис",
                topic="Введение в Python",
                lesson="Основы синтаксиса",
                user_question=test_question,
                lesson_content="Python - это язык программирования высокого уровня...",
                user_name="Тестовый пользователь",
                communication_style="friendly",
            )

            print("✅ Ответ успешно сгенерирован!")
            print(f"📝 Ответ: {answer}")

        except Exception as e:
            print(f"❌ Ошибка при генерации ответа: {str(e)}")

    else:
        print("❌ Ошибка при инициализации TeachAI")


if __name__ == "__main__":
    test_qa_function()
