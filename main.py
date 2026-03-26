"""
Главный модуль TeachAI, точка входа в программу.
Запускает инициализацию и экземпляр системы.
"""

import os
import logging
from pathlib import Path


def setup_logging():
    """Настройка базового логгирования."""
    # Создаем директорию для логов, если она не существует
    Path("logs").mkdir(exist_ok=True)

    # Настраиваем формат логов
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler("logs/teachai.log", mode="a"),
            logging.StreamHandler(),
        ],
    )


def main():
    """Основная функция программы."""
    # Настраиваем логирование
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("Запуск TeachAI...")

    try:
        # Импортируем основной класс системы
        from engine import TeachAIEngine

        # Создаем экземпляр системы
        engine = TeachAIEngine()

        # Инициализируем систему
        if engine.initialize():
            logger.info("Система TeachAI успешно инициализирована")

            # Запускаем интерфейс
            interface = engine.start()

            if interface:
                logger.info("Интерфейс TeachAI успешно запущен")
                return interface
            else:
                logger.error("Ошибка при запуске интерфейса TeachAI")
        else:
            logger.error("Ошибка при инициализации системы TeachAI")

    except Exception as e:
        logger.error(f"Критическая ошибка при запуске TeachAI: {str(e)}")
        raise


if __name__ == "__main__":
    # Запускаем основную функцию
    main()
