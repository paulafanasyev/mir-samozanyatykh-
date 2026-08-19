import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../data/datasources/remote/api_client.dart';
import 'task_detail_screen.dart';

class TasksScreen extends ConsumerStatefulWidget {
  const TasksScreen({super.key});

  @override
  ConsumerState<TasksScreen> createState() => _TasksScreenState();
}

class _TasksScreenState extends ConsumerState<TasksScreen> {
  List<dynamic> tasks = [];
  bool isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadTasks();
  }

  Future<void> _loadTasks() async {
    try {
      final response = await ApiClient().getTasks();
      final data = response.data;
      final items = data is List ? data : (data['items'] ?? data['tasks'] ?? []);
      if (!mounted) return;
      setState(() { tasks = List<dynamic>.from(items); isLoading = false; });
    } catch (_) { if (mounted) setState(() => isLoading = false); }
  }

  Future<void> _toggleTask(dynamic task, bool? value) async {
    try {
      await ApiClient().updateTask(task['id'], {'status': value == true ? 'completed' : 'pending'});
      await _loadTasks();
    } catch (_) {}
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Задачи')),
      body: isLoading
          ? const Center(child: CircularProgressIndicator())
          : ListView.builder(
              itemCount: tasks.length,
              itemBuilder: (context, index) {
                final task = tasks[index];
                return CheckboxListTile(
                  value: task['is_completed'] == true,
                  onChanged: (v) => _toggleTask(task, v),
                  title: Text(task['title'] ?? 'Задача'),
                  subtitle: Text('Дедлайн: ${task['deadline'] ?? '—'}'),
                  secondary: _getPriorityIcon(task['priority']),
                  onTap: () => Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (_) => TaskDetailScreen(taskId: task['id']),
                    ),
                  ),
                );
              },
            ),
      floatingActionButton: FloatingActionButton(
        onPressed: () async {
          final c = TextEditingController();
          final ok = await showDialog<bool>(context: context, builder: (context) => AlertDialog(title: const Text('Новая задача'), content: TextField(controller: c, autofocus: true, decoration: const InputDecoration(labelText: 'Название')), actions: [TextButton(onPressed: () => Navigator.pop(context), child: const Text('Отмена')), FilledButton(onPressed: () async { if (c.text.trim().isEmpty) return; try { await ApiClient().createTask({'title': c.text.trim()}); if (context.mounted) Navigator.pop(context, true); } catch (_) {} }, child: const Text('Создать'))]));
          if (ok == true) _loadTasks();
        },
        child: const Icon(Icons.add),
      ),
    );
  }

  Widget _getPriorityIcon(String? priority) {
    switch (priority) {
      case 'high': return const Icon(Icons.priority_high, color: Colors.red);
      case 'medium': return const Icon(Icons.remove, color: Colors.orange);
      default: return const Icon(Icons.arrow_downward, color: Colors.green);
    }
  }
}
