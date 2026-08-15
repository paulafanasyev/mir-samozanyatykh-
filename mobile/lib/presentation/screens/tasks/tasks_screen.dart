import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

class TasksScreen extends StatelessWidget {
  const TasksScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Задачи')),
      body: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: 5,
        itemBuilder: (context, index) => Card(
          child: ListTile(
            leading: Checkbox(value: index == 2, onChanged: (_) {}),
            title: Text('Задача ${index + 1}'),
            subtitle: Text('Приоритет: ${['Высокий', 'Средний', 'Низкий'][index % 3]}'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => context.push('/tasks/${index + 1}'),
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
