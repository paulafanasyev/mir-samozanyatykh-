import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:shimmer/shimmer.dart';

import '../../../core/theme/app_theme.dart';
import '../../../core/constants/app_constants.dart';
import '../../../data/datasources/remote/api_client.dart';
import '../../providers/auth_provider.dart';
import '../../widgets/common/loading_widget.dart';
import '../../widgets/common/empty_state.dart';
import '../../widgets/common/brand_header.dart';
import '../../widgets/common/svetlana_card.dart';
import '../../widgets/cards/stat_card.dart';
import '../../widgets/cards/action_card.dart';

class ResponseData { final Map<String, dynamic> data; const ResponseData(this.data); }

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authState = ref.watch(authStateProvider);
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;

    return Scaffold(
      appBar: AppBar(
        titleSpacing: 16,
        title: const BrandHeader(),
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
    return FutureBuilder<ResponseData>(
      future: _loadDashboard(),
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const SizedBox(height: 170, child: Center(child: CircularProgressIndicator()));
        }
        if (snapshot.hasError || snapshot.data == null) {
          return const Card(child: ListTile(leading: Icon(Icons.error_outline), title: Text('Не удалось загрузить статистику'), subtitle: Text('Потяните экран вниз для повторной загрузки.')));
        }
        final d = snapshot.data!.data;
        final clients = (d['clients'] as Map?) ?? const {};
        final deals = (d['deals'] as Map?) ?? const {};
        final invoices = (d['invoices'] as Map?) ?? const {};
        return GridView.count(
          shrinkWrap: true, physics: const NeverScrollableScrollPhysics(), crossAxisCount: 2,
          mainAxisSpacing: 12, crossAxisSpacing: 12, childAspectRatio: 1.4,
          children: [
            StatCard(title: 'Счета', value: '${invoices['total'] ?? 0}', subtitle: '${invoices['paid'] ?? 0} оплачено', icon: Icons.receipt, color: colorScheme.primary, onTap: () => context.push('/invoices')),
            StatCard(title: 'Сделки', value: '${deals['total'] ?? 0}', subtitle: '${deals['won'] ?? 0} выиграно', icon: Icons.trending_up, color: AppTheme.accent, onTap: () => context.push('/deals')),
            StatCard(title: 'Клиенты', value: '${clients['total'] ?? 0}', subtitle: '+${clients['new'] ?? 0} за период', icon: Icons.people, color: AppTheme.secondary, onTap: () => context.push('/clients')),
            StatCard(title: 'Задачи', value: '${d['tasks_completed'] ?? 0}', subtitle: 'выполнено за период', icon: Icons.task, color: AppTheme.error, onTap: () => context.push('/tasks')),
          ],
        );
      },
    );
  }

  Future<ResponseData> _loadDashboard() async {
    final response = await ApiClient().getDashboardStats();
    final data = response.data is Map ? Map<String, dynamic>.from(response.data) : <String, dynamic>{};
    return ResponseData(data);
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
    return Card(
      child: ListTile(
        leading: const Icon(Icons.insights_outlined),
        title: const Text('Актуальная статистика'),
        subtitle: const Text('Показатели выше загружаются напрямую из вашего аккаунта.'),
      ),
    );
  }

  Widget _buildSvetlanaWidget(BuildContext context) {
    return const SvetlanaCard();
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
