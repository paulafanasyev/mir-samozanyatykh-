import 'package:flutter/material.dart';
import '../services/auth_service.dart';
import '../services/api_service.dart';
import 'dart:convert';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  Map<String, dynamic>? _user;
  Map<String, dynamic>? _finance;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    final user = await AuthService.me();
    final financeRes = await ApiService.get('/api/finance');
    setState(() {
      _user = user;
      _finance = financeRes.statusCode == 200 ? jsonDecode(financeRes.body) : null;
      _loading = false;
    });
  }

  Future<void> _logout() async {
    await AuthService.clear();
    if (mounted) Navigator.pushReplacementNamed(context, '/login');
  }

  Widget _statCard(String label, String value, IconData icon, Color color) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(icon, color: color, size: 28),
            const SizedBox(height: 12),
            Text(value, style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
            const SizedBox(height: 4),
            Text(label, style: TextStyle(fontSize: 14, color: Colors.grey[400])),
          ],
        ),
      ),
    );
  }

  Widget _navItem(String title, String route, IconData icon) {
    return ListTile(
      leading: Icon(icon, color: const Color(0xFFF5A623)),
      title: Text(title),
      trailing: const Icon(Icons.chevron_right, color: Colors.grey),
      onTap: () => Navigator.pushNamed(context, route),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const Scaffold(body: Center(child: CircularProgressIndicator(color: Color(0xFFF5A623))));
    }

    final income = _finance?['total_income']?.toString() ?? '0';
    final expense = _finance?['total_expense']?.toString() ?? '0';
    final balance = _finance?['balance']?.toString() ?? '0';

    return Scaffold(
      appBar: AppBar(
        title: const Text('📊 Дашборд'),
        actions: [
          IconButton(
            icon: const Icon(Icons.chat_bubble_outline),
            onPressed: () => Navigator.pushNamed(context, '/svetlana'),
          ),
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: _logout,
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _loadData,
        color: const Color(0xFFF5A623),
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Text(
              'Привет, ${_user?['name'] ?? 'Пользователь'}!',
              style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 4),
            Text(
              'Тариф: ${_user?['subscription']?.toString().toUpperCase() ?? 'START'}',
              style: TextStyle(fontSize: 14, color: Colors.grey[400]),
            ),
            const SizedBox(height: 20),
            GridView.count(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              crossAxisCount: 2,
              mainAxisSpacing: 12,
              crossAxisSpacing: 12,
              childAspectRatio: 1.1,
              children: [
                _statCard('Доходы', '${income}₽', Icons.trending_up, Colors.green),
                _statCard('Расходы', '${expense}₽', Icons.trending_down, Colors.red),
                _statCard('Баланс', '${balance}₽', Icons.account_balance_wallet, const Color(0xFFF5A623)),
                _statCard('Договоры', '1', Icons.description, Colors.blue),
              ],
            ),
            const SizedBox(height: 24),
            const Text('Разделы', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Card(
              child: Column(
                children: [
                  _navItem('Договоры', '/contracts', Icons.description),
                  const Divider(height: 1),
                  _navItem('Финансы', '/finance', Icons.account_balance),
                  const Divider(height: 1),
                  _navItem('Калькулятор НПД', '/calculator', Icons.calculate),
                  const Divider(height: 1),
                  _navItem('CRM', '/crm', Icons.people),
                  const Divider(height: 1),
                  _navItem('Маркетплейс', '/marketplace', Icons.store),
                  const Divider(height: 1),
                  _navItem('Гранты', '/grants', Icons.card_giftcard),
                  const Divider(height: 1),
                  _navItem('Профиль', '/profile', Icons.person),
                ],
              ),
            ),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => Navigator.pushNamed(context, '/svetlana'),
        backgroundColor: const Color(0xFFF5A623),
        child: const Icon(Icons.support_agent, color: Colors.black),
      ),
    );
  }
}
