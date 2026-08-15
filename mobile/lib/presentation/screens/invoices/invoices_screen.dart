import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

class InvoicesScreen extends StatelessWidget {
  const InvoicesScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Счета')),
      body: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: 12,
        itemBuilder: (context, index) => Card(
          child: ListTile(
            leading: const Icon(Icons.receipt, color: Colors.blue),
            title: Text('Счёт #${1000 + index}'),
            subtitle: Text('${(index + 1) * 5000} ₽ • ${['Оплачен', 'Ожидает', 'Просрочен'][index % 3]}'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => context.push('/invoices/${index + 1}'),
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
