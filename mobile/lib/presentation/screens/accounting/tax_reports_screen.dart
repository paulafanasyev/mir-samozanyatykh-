import 'package:flutter/material.dart';

class TaxReportsScreen extends StatelessWidget {
  const TaxReportsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Налоговые отчёты')),
      body: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: 6,
        itemBuilder: (context, index) => Card(
          child: ListTile(
            leading: const Icon(Icons.description, color: Colors.blue),
            title: Text('Отчёт за ${['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь'][index]} 2026'),
            subtitle: const Text('Статус: Подан'),
            trailing: const Icon(Icons.download),
          ),
        ),
      ),
    );
  }
}
