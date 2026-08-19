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
      final items = data is List
          ? data
          : data is Map
              ? (data['items'] ?? data['tasks'] ?? const [])
              : const [];
      if (!mounted) return;
      setState(() {
        tasks = List<dynamic>.from(items is Iterable ? items : const []);
        isLoading = false;
      });
    } catch (_) {
      if (mounted) setState(() => isLoading = false);
    }
  }

  Future<void> _toggleTask(dynamic task, bool? value) async {
    final id = task is Map ? task['id'] : null;
    if (id == null) return;
    try {
      await ApiClient().updateTask(id, {'status': value == true ? 'completed' : 'pending'});
      await _loadTasks();
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Не удалось обновить задачу')));
      }
    }
  }

  Future<void> _openTask(dynamic task) async {
    final id = task is Map ? task['id'] : null;
    if (id is! int) return;
    await Navigator.push(context, MaterialPageRoute(builder: (_) => TaskDetailScreen(taskId: id)));
    if (mounted) _loadTasks();
  }

  Future<void> _createTask() async {
    final controller = TextEditingController();
    final ok = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Новая задача'),
        content: TextField(
          controller: controller,
          autofocus: true,
          textInputAction: TextInputAction.done,
          decoration: const InputDecoration(labelText: 'Название', border: OutlineInputBorder()),
          onSubmitted: (_) => Navigator.pop(dialogContext, controller.text.trim().isNotEmpty),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(dialogContext, false), child: const Text('Отмена')),
          FilledButton(onPressed: () => Navigator.pop(dialogContext, controller.text.trim().isNotEmpty), child: const Text('Создать')),
        ],
      ),
    );
    final title = controller.text.trim();
    controller.dispose();
    if (ok != true || title.isEmpty) return;

    try {
      await ApiClient().createTask({'title': title});
      if (mounted) {
        await _loadTasks();
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Задача создана')));
      }
    } catch (_) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Не удалось создать задачу')));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Задачи')),
      body: isLoading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _loadTasks,
              child: tasks.isEmpty
                  ? ListView(children: const [SizedBox(height: 180), Center(child: Text('Задач пока нет'))])
                  : ListView.separated(
                      padding: const EdgeInsets.symmetric(vertical: 8),
                      itemCount: tasks.length,
                      separatorBuilder: (_, __) => const Divider(height: 1),
                      itemBuilder: (context, index) {
                        final task = tasks[index] as Map?;
                        final id = task?['id'];
                        final completed = task?['is_completed'] == true || task?['status'] == 'completed';
                        return ListTile(
                          onTap: id is int ? () => _openTask(task) : null,
                          leading: Checkbox(value: completed, onChanged: (v) => _toggleTask(task, v)),
                          title: Text(task?['title']?.toString() ?? 'Задача'),
                          subtitle: Text('Дедлайн: ${task?['deadline']?.toString() ?? '—'}'),
                          trailing: _getPriorityIcon(task?['priority']?.toString()),
                        );
                      },
                    ),
            ),
      floatingActionButton: FloatingActionButton(onPressed: _createTask, child: const Icon(Icons.add)),
    );
  }

  Widget _getPriorityIcon(String? priority) {
    switch (priority) {
      case 'high':
        return const Icon(Icons.priority_high, color: Colors.red);
      case 'medium':
        return const Icon(Icons.remove, color: Colors.orange);
      default:
        return const Icon(Icons.arrow_downward, color: Colors.green);
    }
  }
}
