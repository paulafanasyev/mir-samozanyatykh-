import 'package:flutter/material.dart';

class BankScreen extends StatelessWidget {
  const BankScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Банковские подключения')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Card(
            child: ListTile(
              leading: const Icon(Icons.account_balance, color: Colors.yellow),
              title: const Text('Тинькофф'),
              subtitle: const Text('Подключено'),
              trailing: const Icon(Icons.check_circle, color: Colors.green),
            ),
          ),
          Card(
            child: ListTile(
              leading: const Icon(Icons.account_balance, color: Colors.green),
              title: const Text('СберБанк'),
              subtitle: const Text('Не подключено'),
              trailing: FilledButton.tonal(onPressed: () {}, child: const Text('Подключить')),
            ),
          ),
        ],
      ),
    );
  }
}
