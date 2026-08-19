import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme/app_theme.dart';

class SettingsScreen extends ConsumerStatefulWidget {
  const SettingsScreen({super.key});

  @override
  ConsumerState<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends ConsumerState<SettingsScreen> {
  bool _darkMode = false;
  bool _notifications = true;
  bool _biometric = false;
  bool _analytics = true;
  bool _autoSync = true;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const Text('Настройки')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _buildSectionTitle(context, 'Внешний вид'),
          SwitchListTile(
            secondary: const Icon(Icons.dark_mode_outlined),
            title: const Text('Тёмная тема'),
            subtitle: const Text('Использовать тёмную тему оформления'),
            value: _darkMode,
            onChanged: (v) => setState(() => _darkMode = v),
          ),
          const SizedBox(height: 16),

          _buildSectionTitle(context, 'Уведомления'),
          SwitchListTile(
            secondary: const Icon(Icons.notifications_outlined),
            title: const Text('Push-уведомления'),
            subtitle: const Text('Счета, задачи, напоминания'),
            value: _notifications,
            onChanged: (v) => setState(() => _notifications = v),
          ),
          SwitchListTile(
            secondary: const Icon(Icons.email_outlined),
            title: const Text('Email-уведомления'),
            subtitle: const Text('Еженедельные отчёты, новости'),
            value: true,
            onChanged: (_) {},
          ),
          const SizedBox(height: 16),

          _buildSectionTitle(context, 'Безопасность'),
          SwitchListTile(
            secondary: const Icon(Icons.fingerprint),
            title: const Text('Биометрическая аутентификация'),
            subtitle: const Text('Face ID / Touch ID / Отпечаток'),
            value: _biometric,
            onChanged: (v) => setState(() => _biometric = v),
          ),
          ListTile(
            leading: const Icon(Icons.password_outlined),
            title: const Text('Изменить пароль'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Откройте веб-версию для управления этим параметром.'))),
          ),
          ListTile(
            leading: const Icon(Icons.phonelink_lock_outlined),
            title: const Text('Двухфакторная аутентификация'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Откройте веб-версию для управления этим параметром.'))),
          ),
          const SizedBox(height: 16),

          _buildSectionTitle(context, 'Данные'),
          SwitchListTile(
            secondary: const Icon(Icons.sync_outlined),
            title: const Text('Автоматическая синхронизация'),
            subtitle: const Text('Синхронизировать данные при подключении к сети'),
            value: _autoSync,
            onChanged: (v) => setState(() => _autoSync = v),
          ),
          SwitchListTile(
            secondary: const Icon(Icons.analytics_outlined),
            title: const Text('Аналитика и диагностика'),
            subtitle: const Text('Помогает улучшать приложение'),
            value: _analytics,
            onChanged: (v) => setState(() => _analytics = v),
          ),
          ListTile(
            leading: Icon(Icons.delete_outline, color: AppTheme.error),
            title: Text('Очистить кэш', style: TextStyle(color: AppTheme.error)),
            onTap: () {
              showDialog(
                context: context,
                builder: (context) => AlertDialog(
                  title: const Text('Очистить кэш?'),
                  content: const Text('Все временные данные будут удалены. Это не затронет ваши основные данные.'),
                  actions: [
                    TextButton(onPressed: () => Navigator.pop(context), child: const Text('Отмена')),
                    FilledButton(
                      onPressed: () {
                        Navigator.pop(context);
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(content: Text('Кэш очищен')),
                        );
                      },
                      child: const Text('Очистить'),
                    ),
                  ],
                ),
              );
            },
          ),
          const SizedBox(height: 16),

          _buildSectionTitle(context, 'О приложении'),
          ListTile(
            leading: const Icon(Icons.description_outlined),
            title: const Text('Условия использования'),
            trailing: const Icon(Icons.open_in_new, size: 18),
            onTap: () => ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Откройте веб-версию для управления этим параметром.'))),
          ),
          ListTile(
            leading: const Icon(Icons.privacy_tip_outlined),
            title: const Text('Политика конфиденциальности'),
            trailing: const Icon(Icons.open_in_new, size: 18),
            onTap: () => ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Откройте веб-версию для управления этим параметром.'))),
          ),
          ListTile(
            leading: const Icon(Icons.info_outline),
            title: const Text('Версия'),
            subtitle: const Text('8.4.38 (build 861)'),
          ),
        ],
      ),
    );
  }

  Widget _buildSectionTitle(BuildContext context, String title) {
    return Padding(
      padding: const EdgeInsets.only(left: 16, bottom: 8, top: 8),
      child: Text(
        title,
        style: Theme.of(context).textTheme.labelLarge?.copyWith(
          color: Theme.of(context).colorScheme.primary,
          fontWeight: FontWeight.w700,
        ),
      ),
    );
  }
}
