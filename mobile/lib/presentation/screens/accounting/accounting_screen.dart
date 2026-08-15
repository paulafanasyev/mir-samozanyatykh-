import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

class AccountingScreen extends StatelessWidget {
  const AccountingScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(title: const Text('Бухгалтерия')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Баланс', style: theme.textTheme.labelMedium),
                  const SizedBox(height: 4),
                  Text('125 000 ₽', style: theme.textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.w700)),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          ListTile(
            leading: const Icon(Icons.receipt_long, color: Colors.green),
            title: const Text('Транзакции'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () {},
          ),
          ListTile(
            leading: const Icon(Icons.description, color: Colors.blue),
            title: const Text('Налоговые отчёты'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => context.push('/tax-reports'),
          ),
          ListTile(
            leading: const Icon(Icons.money_off, color: Colors.orange),
            title: const Text('Вычеты'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () {},
          ),
        ],
      ),
    );
  }
}
