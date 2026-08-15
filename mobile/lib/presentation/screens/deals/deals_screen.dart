import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

class DealsScreen extends StatelessWidget {
  const DealsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Сделки')),
      body: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: 8,
        itemBuilder: (context, index) => Card(
          child: ListTile(
            leading: const Icon(Icons.trending_up, color: Colors.orange),
            title: Text('Сделка ${index + 1}'),
            subtitle: Text('Стадия: ${['Новая', 'В работе', 'Переговоры', 'Закрыта'][index % 4]}'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => context.push('/deals/${index + 1}'),
          ),
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {},
        child: const Icon(Icons.add),
      ),
    );
  }
}
