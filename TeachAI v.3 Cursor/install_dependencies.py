#!/usr/bin/env python3
"""
Скрипт для автоматической установки зависимостей TeachAI.
Устанавливает все необходимые библиотеки для корректной работы системы.
"""

import subprocess
import sys
import os

def install_package(package):
    """Устанавливает пакет с помощью pip."""
    try:
        print(f"📦 Устанавливаю {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ {package} успешно установлен!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка при установке {package}: {str(e)}")
        return False

def check_package(package):
    """Проверяет, установлен ли пакет."""
    try:
        __import__(package)
        return True
    except ImportError:
        return False

def main():
    """Основная функция установки зависимостей."""
    print("🚀 УСТАНОВКА ЗАВИСИМОСТЕЙ TEACHAI")
    print("=" * 50)
    
    # Список основных зависимостей
    dependencies = [
        "openai>=1.95.1",
        "ipywidgets>=8.1.7", 
        "jupyter>=1.1.0",
        "ipython>=9.4.0",
        "python-dotenv>=1.1.1",
        "pandas>=2.3.1",
        "numpy>=2.3.1",
        "scikit-learn>=1.5.0",
        "scipy>=1.14.0",
        "matplotlib>=3.10.3",
        "seaborn>=0.13.2",
        "markdown>=3.5.2",
        "pygments>=2.17.2"
    ]
    
    # Список пакетов для проверки импорта
    import_names = [
        "openai",
        "ipywidgets",
        "jupyter", 
        "IPython",
        "dotenv",
        "pandas",
        "numpy",
        "sklearn",
        "scipy",
        "matplotlib",
        "seaborn",
        "markdown",
        "pygments"
    ]
    
    print("🔍 Проверяю уже установленные пакеты...")
    
    # Проверяем, какие пакеты уже установлены
    installed = []
    missing = []
    
    for package, import_name in zip(dependencies, import_names):
        if check_package(import_name):
            print(f"✅ {package} уже установлен")
            installed.append(package)
        else:
            print(f"❌ {package} отсутствует")
            missing.append(package)
    
    print(f"\n📊 Статистика: {len(installed)} установлено, {len(missing)} отсутствует")
    
    if not missing:
        print("\n🎉 Все зависимости уже установлены!")
        return
    
    print(f"\n📥 Устанавливаю недостающие пакеты ({len(missing)} шт.)...")
    
    # Устанавливаем недостающие пакеты
    success_count = 0
    for package in missing:
        if install_package(package):
            success_count += 1
        print()  # Пустая строка для читаемости
    
    print("=" * 50)
    print(f"📈 РЕЗУЛЬТАТ УСТАНОВКИ:")
    print(f"✅ Успешно установлено: {success_count}")
    print(f"❌ Ошибок: {len(missing) - success_count}")
    
    if success_count == len(missing):
        print("\n🎉 Все зависимости успешно установлены!")
        print("Теперь TeachAI готов к работе!")
    else:
        print(f"\n⚠️ Установлено {success_count} из {len(missing)} пакетов.")
        print("Проверьте ошибки выше и попробуйте установить недостающие пакеты вручную.")
    
    print("\n💡 Для запуска TeachAI используйте:")
    print("   python run_teachai.py")
    print("   или")
    print("   jupyter notebook TeachAI_clean.ipynb")

if __name__ == "__main__":
    main() 