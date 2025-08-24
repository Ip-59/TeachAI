#!/usr/bin/env python3
"""
Скрипт для запуска TeachAI в режиме отладки
"""

import os
import sys
import logging
from pathlib import Path

# Добавляем текущую директорию в путь
sys.path.insert(0, os.getcwd())

def setup_debug_logging():
    """Настраивает подробное логирование для отладки"""
    # Создаем директорию для логов
    Path("logs").mkdir(exist_ok=True)
    
    # Настраиваем логирование
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/debug_teachai.log', mode='w', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    # Устанавливаем уровень логирования для всех модулей
    logging.getLogger().setLevel(logging.DEBUG)
    
    # Специально для OpenAI API (чтобы видеть запросы)
    logging.getLogger('openai').setLevel(logging.DEBUG)
    logging.getLogger('httpx').setLevel(logging.DEBUG)
    logging.getLogger('httpcore').setLevel(logging.DEBUG)
    
    return logging.getLogger(__name__)

def run_teachai_debug():
    """Запускает TeachAI в режиме отладки"""
    logger = setup_debug_logging()
    
    logger.info("🚀 ЗАПУСК TEACHAI В РЕЖИМЕ ОТЛАДКИ")
    logger.info("=" * 60)
    
    try:
        # Импортируем движок
        from engine import TeachAIEngine
        
        logger.info("Создаем экземпляр TeachAIEngine...")
        engine = TeachAIEngine()
        
        logger.info("Инициализируем систему...")
        if engine.initialize():
            logger.info("✅ Система успешно инициализирована")
            
            logger.info("Запускаем интерфейс...")
            interface_element = engine.start()
            
            if interface_element:
                logger.info("✅ Интерфейс создан успешно!")
                logger.info("🎯 TeachAI готов к работе!")
                
                # Возвращаем интерфейс для использования в Jupyter
                return interface_element
            else:
                logger.error("❌ Интерфейс не был создан")
                return None
        else:
            logger.error("❌ Ошибка при инициализации системы TeachAI")
            return None
            
    except Exception as e:
        logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None

def main():
    """Основная функция для запуска в консольном режиме"""
    print("🔍 ЗАПУСК TEACHAI В РЕЖИМЕ ОТЛАДКИ")
    print("=" * 60)
    
    interface = run_teachai_debug()
    
    if interface:
        print("\n✅ TeachAI запущен успешно!")
        print("📋 Логи сохранены в: logs/debug_teachai.log")
        print("🎯 Система готова к тестированию контрольных заданий!")
    else:
        print("\n❌ Ошибка при запуске TeachAI")
        print("📋 Проверьте логи в: logs/debug_teachai.log")

if __name__ == "__main__":
    main()