import 'package:flutter/material.dart';

class IntegrationsScreen extends StatelessWidget {
  const IntegrationsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Интеграции и API')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _buildSection(context, 'API ключи', [
            ListTile(
              leading: const Icon(Icons.key, color: Colors.blue),
              title: const Text('Управление API ключами'),
              trailing: const Icon(Icons.chevron_right),
              onTap: () {},
            ),
          ]),
          _buildSection(context, 'Вебхуки', [
            ListTile(
              leading: const Icon(Icons.webhook, color: Colors.purple),
              title: const Text('Настройка вебхуков'),
              trailing: const Icon(Icons.chevron_right),
              onTap: () {},
            ),
          ]),
          _buildSection(context, 'Экспорт', [
            ListTile(
              leading: const Icon(Icons.download, color: Colors.green),
              title: const Text('Экспорт данных'),
              trailing: const Icon(Icons.chevron_right),
              onTap: () {},
            ),
          ]),
        ],
      ),
    );
  }

  Widget _buildSection(BuildContext context, String title, List<Widget> children) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.only(left: 16, top: 16, bottom: 8),
          child: Text(title, style: Theme.of(context).textTheme.labelLarge?.copyWith(color: Theme.of(context).colorScheme.primary, fontWeight: FontWeight.w700)),
        ),
        Card(child: Column(children: children)),
      ],
    );
  }
}
