import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:shimmer/shimmer.dart';

import '../../../core/theme/app_theme.dart';
import '../../../core/constants/app_constants.dart';
import '../../providers/auth_provider.dart';
import '../../widgets/common/loading_widget.dart';
import '../../widgets/common/empty_state.dart';
import '../../widgets/cards/stat_card.dart';
import '../../widgets/cards/action_card.dart';

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authState = ref.watch(authStateProvider);
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Мир Самозанятых'),
        actions: [
          IconButton(
            icon: Badge(
              isLabelVisible: true,
              smallSize: 8,
              child: Icon(Icons.notifications_outlined, color: colorScheme.onSurface),
            ),
            onPressed: () => context.push('/notifications'),
          ),
          const SizedBox(width: 8),
        ],
      ),
      body: authState.when(
        data: (state) => _buildContent(context, ref, state),
        loading: () => const LoadingWidget(),
        error: (error, _) => EmptyState(
          icon: Icons.error_outline,
          title: 'Ошибка загрузки',
          message: error.toString(),
          actionLabel: 'Повторить',
          onAction: () => ref.invalidate(authStateProvider),
        ),
      ),
    );
  }

  Widget _buildContent(BuildContext context, WidgetRef ref, dynamic state) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;
    final user = state.user;

    return RefreshIndicator(
      onRefresh: () async => ref.invalidate(authStateProvider),
      child: CustomScrollView(
        slivers: [
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Welcome
                  Text(
                    'Добро пожаловать,',
                    style: theme.textTheme.bodyLarge?.copyWith(
                      color: colorScheme.onSurfaceVariant,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    user?.name ?? 'Пользователь',
                    style: theme.textTheme.headlineMedium?.copyWith(
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                    decoration: BoxDecoration(
                      color: _getTierColor(user?.userTier ?? 'start').withOpacity(0.1),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Text(
                      _getTierName(user?.userTier ?? 'start'),
                      style: theme.textTheme.labelMedium?.copyWith(
                        color: _getTierColor(user?.userTier ?? 'start'),
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                  const SizedBox(height: 24),

                  // Stats Grid
                  _buildStatsGrid(context),
                  const SizedBox(height: 24),

                  // Quick Actions
                  Text(
                    'Быстрые действия',
                    style: theme.textTheme.titleLarge,
                  ),
                  const SizedBox(height: 12),
                  _buildQuickActions(context),
                  const SizedBox(height: 24),

                  // Recent Activity
                  Text(
                    'Последняя активность',
                    style: theme.textTheme.titleLarge,
                  ),
                  const SizedBox(height: 12),
                  _buildRecentActivity(context),
                  const SizedBox(height: 24),

                  // Svetlana Widget
                  _buildSvetlanaWidget(context),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStatsGrid(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;

    return GridView.count(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      crossAxisCount: 2,
      mainAxisSpacing: 12,
      crossAxisSpacing: 12,
      childAspectRatio: 1.4,
      children: [
        StatCard(
          title: 'Счета',
          value: '12',
          subtitle: '3 на оплате',
          icon: Icons.receipt,
          color: colorScheme.primary,
          onTap: () => context.push('/invoices'),
        ),
        StatCard(
          title: 'Сделки',
          value: '8',
          subtitle: '2 в работе',
          icon: Icons.trending_up,
          color: AppTheme.accent,
          onTap: () => context.push('/deals'),
        ),
        StatCard(
          title: 'Клиенты',
          value: '24',
          subtitle: '+3 за месяц',
          icon: Icons.people,
          color: AppTheme.secondary,
          onTap: () => context.push('/clients'),
        ),
        StatCard(
          title: 'Задачи',
          value: '5',
          subtitle: '1 просрочена',
          icon: Icons.task,
          color: AppTheme.error,
          onTap: () => context.push('/tasks'),
        ),
      ],
    );
  }

  Widget _buildQuickActions(BuildContext context) {
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: [
        ActionChip(
          avatar: const Icon(Icons.add, size: 18),
          label: const Text('Новый счет'),
          onPressed: () => context.push('/invoices'),
        ),
        ActionChip(
          avatar: const Icon(Icons.person_add, size: 18),
          label: const Text('Клиент'),
          onPressed: () => context.push('/clients'),
        ),
        ActionChip(
          avatar: const Icon(Icons.task_alt, size: 18),
          label: const Text('Задача'),
          onPressed: () => context.push('/tasks'),
        ),
        ActionChip(
          avatar: const Icon(Icons.qr_code_scanner, size: 18),
          label: const Text('Чек ФНС'),
          onPressed: () => context.push('/receipt-check'),
        ),
        ActionChip(
          avatar: const Icon(Icons.chat, size: 18),
          label: const Text('Светлана'),
          onPressed: () => context.push('/svetlana'),
        ),
      ],
    );
  }

  Widget _buildRecentActivity(BuildContext context) {
    final activities = [
      {'title': 'Счет #1245 создан', 'time': '2 мин назад', 'icon': Icons.receipt, 'color': AppTheme.primary},
      {'title': 'Клиент "ООО Ромашка" добавлен', 'time': '15 мин назад', 'icon': Icons.person_add, 'color': AppTheme.secondary},
      {'title': 'Задача "Отправить КП" выполнена', 'time': '1 ч назад', 'icon': Icons.check_circle, 'color': AppTheme.success},
      {'title': 'Сделка "Разработка сайта" выиграна', 'time': '3 ч назад', 'icon': Icons.emoji_events, 'color': AppTheme.accent},
    ];

    return Column(
      children: activities.map((activity) => ListTile(
        leading: CircleAvatar(
          backgroundColor: (activity['color'] as Color).withOpacity(0.1),
          child: Icon(activity['icon'] as IconData, color: activity['color'] as Color, size: 20),
        ),
        title: Text(activity['title'] as String, style: Theme.of(context).textTheme.bodyMedium),
        subtitle: Text(activity['time'] as String, style: Theme.of(context).textTheme.bodySmall),
        dense: true,
      )).toList(),
    );
  }

  Widget _buildSvetlanaWidget(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;

    return Card(
      child: InkWell(
        onTap: () => context.push('/svetlana'),
        borderRadius: BorderRadius.circular(16),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              Container(
                width: 48,
                height: 48,
                decoration: BoxDecoration(
                  color: colorScheme.primaryContainer,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(Icons.smart_toy, color: colorScheme.primary),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Светлана', style: theme.textTheme.titleMedium),
                    const SizedBox(height: 2),
                    Text(
                      'Ваш ИИ-ассистент по налогам и бизнесу',
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: colorScheme.onSurfaceVariant,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ),
              ),
              Icon(Icons.arrow_forward_ios, size: 16, color: colorScheme.onSurfaceVariant),
            ],
          ),
        ),
      ),
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
        return 'PRO';
      case 'business':
        return 'BUSINESS';
      case 'enterprise':
        return 'ENTERPRISE';
      default:
        return 'START';
    }
  }
}
