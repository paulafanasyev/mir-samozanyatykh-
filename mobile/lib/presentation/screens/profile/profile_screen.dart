import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/theme/app_theme.dart';
import '../../providers/auth_provider.dart';
import '../../widgets/common/loading_widget.dart';
import '../../widgets/common/empty_state.dart';

class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authState = ref.watch(authStateProvider);
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Профиль'),
        actions: [
          IconButton(
            icon: const Icon(Icons.settings_outlined),
            onPressed: () => context.push('/settings'),
          ),
        ],
      ),
      body: authState.when(
        data: (state) => _buildContent(context, ref, state),
        loading: () => const LoadingWidget(),
        error: (error, _) => EmptyState(
          icon: Icons.error_outline,
          title: 'Ошибка',
          message: error.toString(),
        ),
      ),
    );
  }

  Widget _buildContent(BuildContext context, WidgetRef ref, dynamic state) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;
    final user = state.user;

    if (user == null) {
      return const EmptyState(
        icon: Icons.person_off,
        title: 'Пользователь не найден',
      );
    }

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        // Avatar & Name
        Center(
          child: Column(
            children: [
              CircleAvatar(
                radius: 50,
                backgroundColor: colorScheme.primaryContainer,
                backgroundImage: user.avatar != null ? NetworkImage(user.avatar!) : null,
                child: user.avatar == null
                    ? Text(
                        user.name.isNotEmpty ? user.name[0].toUpperCase() : '?',
                        style: theme.textTheme.displaySmall?.copyWith(
                          color: colorScheme.primary,
                        ),
                      )
                    : null,
              ),
              const SizedBox(height: 16),
              Text(
                user.name,
                style: theme.textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w700),
              ),
              const SizedBox(height: 4),
              Text(
                user.email,
                style: theme.textTheme.bodyMedium?.copyWith(color: colorScheme.onSurfaceVariant),
              ),
              const SizedBox(height: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
                decoration: BoxDecoration(
                  color: _getTierColor(user.userTier).withOpacity(0.1),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Text(
                  _getTierName(user.userTier),
                  style: theme.textTheme.labelLarge?.copyWith(
                    color: _getTierColor(user.userTier),
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 32),

        // Stats
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                _buildStat('Счета', '12', Icons.receipt),
                _buildStat('Сделки', '8', Icons.trending_up),
                _buildStat('Клиенты', '24', Icons.people),
                _buildStat('Рефералы', '${user.referralCount}', Icons.group_add),
              ],
            ),
          ),
        ),
        const SizedBox(height: 24),

        // Menu Items
        _buildSectionTitle(context, 'Аккаунт'),
        _buildMenuItem(
          context,
          icon: Icons.person_outline,
          title: 'Редактировать профиль',
          onTap: () => context.push('/edit-profile'),
        ),
        _buildMenuItem(
          context,
          icon: Icons.verified_user_outlined,
          title: 'Верификация',
          subtitle: user.isVerified ? 'Верифицирован' : 'Не верифицирован',
          trailing: user.isVerified
              ? Icon(Icons.check_circle, color: AppTheme.success, size: 20)
              : Icon(Icons.warning_amber, color: AppTheme.warning, size: 20),
          onTap: () {},
        ),
        _buildMenuItem(
          context,
          icon: Icons.lock_outline,
          title: 'Безопасность',
          subtitle: '2FA, биометрия, пароль',
          onTap: () {},
        ),
        const SizedBox(height: 16),

        _buildSectionTitle(context, 'Финансы'),
        _buildMenuItem(
          context,
          icon: Icons.account_balance_wallet_outlined,
          title: 'Бухгалтерия',
          onTap: () => context.push('/accounting'),
        ),
        _buildMenuItem(
          context,
          icon: Icons.account_balance_outlined,
          title: 'Банковские подключения',
          onTap: () => context.push('/bank'),
        ),
        _buildMenuItem(
          context,
          icon: Icons.card_giftcard_outlined,
          title: 'Реферальная программа',
          subtitle: 'Заработано: ${user.referralEarnings.toStringAsFixed(0)} ₽',
          onTap: () => context.push('/referrals'),
        ),
        const SizedBox(height: 16),

        _buildSectionTitle(context, 'Бизнес'),
        _buildMenuItem(
          context,
          icon: Icons.description_outlined,
          title: 'Договоры',
          onTap: () => context.push('/contracts'),
        ),
        _buildMenuItem(
          context,
          icon: Icons.store_outlined,
          title: 'Маркетплейс',
          onTap: () => context.push('/marketplace'),
        ),
        _buildMenuItem(
          context,
          icon: Icons.analytics_outlined,
          title: 'Аналитика',
          onTap: () => context.push('/analytics'),
        ),
        _buildMenuItem(
          context,
          icon: Icons.integration_instructions_outlined,
          title: 'Интеграции и API',
          onTap: () => context.push('/integrations'),
        ),
        const SizedBox(height: 16),

        if (user.isAdmin || user.isModerator) ...[
          _buildSectionTitle(context, 'Администрирование'),
          _buildMenuItem(
            context,
            icon: Icons.admin_panel_settings_outlined,
            title: 'Панель администратора',
            color: AppTheme.primary,
            onTap: () => context.push('/admin'),
          ),
          const SizedBox(height: 16),
        ],

        _buildSectionTitle(context, 'Приложение'),
        _buildMenuItem(
          context,
          icon: Icons.help_outline,
          title: 'Помощь и поддержка',
          onTap: () {},
        ),
        _buildMenuItem(
          context,
          icon: Icons.info_outline,
          title: 'О приложении',
          subtitle: 'Версия 8.6.0 (860)',
          onTap: () {},
        ),
        const SizedBox(height: 16),

        // Logout
        FilledButton.tonal(
          onPressed: () async {
            await ref.read(authStateProvider.notifier).logout();
            if (context.mounted) context.go('/login');
          },
          style: FilledButton.styleFrom(
            backgroundColor: colorScheme.errorContainer,
            foregroundColor: colorScheme.error,
            minimumSize: const Size(double.infinity, 48),
          ),
          child: const Text('Выйти из аккаунта'),
        ),
        const SizedBox(height: 32),
      ],
    );
  }

  Widget _buildStat(String label, String value, IconData icon) {
    return Column(
      children: [
        Icon(icon, size: 20, color: AppTheme.onSurfaceVariant),
        const SizedBox(height: 4),
        Text(value, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16)),
        const SizedBox(height: 2),
        Text(label, style: const TextStyle(fontSize: 12, color: AppTheme.onSurfaceVariant)),
      ],
    );
  }

  Widget _buildSectionTitle(BuildContext context, String title) {
    return Padding(
      padding: const EdgeInsets.only(left: 16, bottom: 8),
      child: Text(
        title,
        style: Theme.of(context).textTheme.labelLarge?.copyWith(
          color: Theme.of(context).colorScheme.primary,
          fontWeight: FontWeight.w700,
        ),
      ),
    );
  }

  Widget _buildMenuItem(
    BuildContext context, {
    required IconData icon,
    required String title,
    String? subtitle,
    Widget? trailing,
    Color? color,
    required VoidCallback onTap,
  }) {
    final theme = Theme.of(context);
    return ListTile(
      leading: Icon(icon, color: color ?? theme.colorScheme.onSurfaceVariant),
      title: Text(title),
      subtitle: subtitle != null ? Text(subtitle, style: theme.textTheme.bodySmall) : null,
      trailing: trailing ?? const Icon(Icons.chevron_right),
      onTap: onTap,
    );
  }

  Color _getTierColor(String tier) {
    switch (tier) {
      case 'pro':
        return AppTheme.accent;
      case 'business':
        return AppTheme.primary;
      case 'enterprise':
        return const Color(0xFF7B1FA2);
      default:
        return AppTheme.onSurfaceVariant;
    }
  }

  String _getTierName(String tier) {
    switch (tier) {
      case 'pro':
        return 'PRO — 300 ₽/мес';
      case 'business':
        return 'BUSINESS — 990 ₽/мес';
      case 'enterprise':
        return 'ENTERPRISE';
      default:
        return 'START — Бесплатно';
    }
  }
}
