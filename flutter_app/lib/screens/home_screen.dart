import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/auth_service.dart';
import '../services/api_service.dart';
import 'contracts_screen.dart';
import 'finance_screen.dart';
import 'crm_screen.dart';
import 'marketplace_screen.dart';
import 'grants_screen.dart';
import 'profile_screen.dart';
import 'svetlana_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _currentIndex = 0;
  final _api = ApiService();
  Map<String, dynamic>? _stats;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadStats();
  }

  Future<void> _loadStats() async {
    try {
      final data = await _api.get('/api/contracts');
      final finance = await _api.get('/api/finance');
      final notifs = await _api.get('/api/notifications?unread_only=true');
      setState(() {
        _stats = {
          'contracts': (data['contracts'] as List?)?.length ?? 0,
          'income': finance['summary']?['total_income'] ?? 0.0,
          'notifications': (notifs['notifications'] as List?)?.length ?? 0,
        };
        _loading = false;
      });
    } catch (e) {
      setState(() => _loading = false);
    }
  }

  final _screens = [
    const _DashboardTab(),
    const ContractsScreen(),
    const FinanceScreen(),
    const CRMScreen(),
    const MarketplaceScreen(),
    const GrantsScreen(),
    const ProfileScreen(),
  ];

  final _items = [
    const BottomNavigationBarItem(icon: Icon(Icons.dashboard), label: 'Главная'),
    const BottomNavigationBarItem(icon: Icon(Icons.description), label: 'Договоры'),
    const BottomNavigationBarItem(icon: Icon(Icons.account_balance_wallet), label: 'Финансы'),
    const BottomNavigationBarItem(icon: Icon(Icons.people), label: 'CRM'),
    const BottomNavigationBarItem(icon: Icon(Icons.shopping_bag), label: 'Маркет'),
    const BottomNavigationBarItem(icon: Icon(Icons.card_giftcard), label: 'Гранты'),
    const BottomNavigationBarItem(icon: Icon(Icons.person), label: 'Профиль'),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Мир Самозанятых', style: TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: const Color(0xFF667eea),
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.chat_bubble),
            onPressed: () => Navigator.push(
              context,
              MaterialPageRoute(builder: (_) => const SvetlanaScreen()),
            ),
          ),
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () => context.read<AuthService>().logout(),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _loadStats,
        child: _screens[_currentIndex],
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _currentIndex,
        onTap: (i) => setState(() => _currentIndex = i),
        type: BottomNavigationBarType.fixed,
        selectedItemColor: const Color(0xFF667eea),
        unselectedItemColor: Colors.grey,
        items: _items,
      ),
    );
  }
}

class _DashboardTab extends StatelessWidget {
  const _DashboardTab();

  @override
  Widget build(BuildContext context) {
    final user = context.watch<AuthService>().user;
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Привет, ${user?['full_name'] ?? 'Пользователь'}!',
            style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          Text(
            'Тариф: ${user?['subscription']?.toUpperCase() ?? 'START'}',
            style: TextStyle(color: Colors.grey.shade600),
          ),
          const SizedBox(height: 24),
          GridView.count(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            crossAxisCount: 2,
            crossAxisSpacing: 12,
            mainAxisSpacing: 12,
            children: [
              _buildStatCard('Договоры', '0', Icons.description, Colors.blue),
              _buildStatCard('Доход', '0 ₽', Icons.trending_up, Colors.green),
              _buildStatCard('Налог НПД', '0 ₽', Icons.account_balance, Colors.orange),
              _buildStatCard('Уведомления', '0', Icons.notifications, Colors.purple),
            ],
          ),
          const SizedBox(height: 24),
          const Text('Быстрые действия', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
          const SizedBox(height: 12),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              _buildActionChip(context, 'Новый договор', Icons.add, 1),
              _buildActionChip(context, 'Запись дохода', Icons.add_chart, 2),
              _buildActionChip(context, 'Новый контакт', Icons.person_add, 3),
              _buildActionChip(context, 'Спросить Светлану', Icons.chat, -1),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildStatCard(String title, String value, IconData icon, Color color) {
    return Card(
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, size: 32, color: color),
            const SizedBox(height: 8),
            Text(value, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
            Text(title, style: TextStyle(color: Colors.grey.shade600, fontSize: 12)),
          ],
        ),
      ),
    );
  }

  Widget _buildActionChip(BuildContext context, String label, IconData icon, int screenIndex) {
    return ActionChip(
      avatar: Icon(icon, size: 18),
      label: Text(label),
      onPressed: () {
        if (screenIndex == -1) {
          Navigator.push(context, MaterialPageRoute(builder: (_) => const SvetlanaScreen()));
        }
      },
    );
  }
}
