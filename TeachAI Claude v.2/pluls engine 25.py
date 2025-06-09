def start(self):
    """
    ДИАГНОСТИКА: Запускает систему TeachAI с отладочными сообщениями.

    Returns:
        UserInterface объект или соответствующий виджет для отображения
    """
    print("🔍 DEBUG start(): Начало метода start()")

    if not self.is_ready:
        print("🔍 DEBUG start(): Система не готова, вызываем initialize()")
        if not self.initialize():
            print("❌ DEBUG start(): initialize() вернул False")
            return None
        print("✅ DEBUG start(): initialize() успешен")

    print("🔍 DEBUG start(): Логируем запуск системы...")
    self.logger.info("Запуск TeachAI...")

    # Логируем запуск системы
    print("🔍 DEBUG start(): Вызываем system_logger.log_activity...")
    self.system_logger.log_activity(
        action_type="system_started",
        details={"is_first_run": self.state_manager.is_first_run()},
    )
    print("✅ DEBUG start(): system_logger.log_activity завершен")

    # Определяем начальное состояние интерфейса
    print("🔍 DEBUG start(): Проверяем is_first_run...")
    is_first_run = self.state_manager.is_first_run()
    print(f"🔍 DEBUG start(): is_first_run = {is_first_run}")

    if is_first_run:
        # Первый запуск - показываем настройку профиля
        print("🔍 DEBUG start(): Первый запуск - показ настройки профиля")
        self.logger.info("Первый запуск - показ настройки профиля")
        self.interface.current_state = InterfaceState.INITIAL_SETUP

        print("🔍 DEBUG start(): Вызываем interface.show_initial_setup()...")
        result = self.interface.show_initial_setup()
        print(f"✅ DEBUG start(): show_initial_setup() вернул: {type(result)}")
        return result
    else:
        # НОВОЕ: Не первый запуск - показываем главное меню
        print("🔍 DEBUG start(): Повторный запуск - показ главного меню")
        self.logger.info("Повторный запуск - показ главного меню")
        self.interface.current_state = InterfaceState.MAIN_MENU

        print("🔍 DEBUG start(): Вызываем interface.show_main_menu()...")
        result = self.interface.show_main_menu()
        print(f"✅ DEBUG start(): show_main_menu() вернул: {type(result)}")
        return result
