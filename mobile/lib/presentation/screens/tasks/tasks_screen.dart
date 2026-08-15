import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:dio/dio.dart';

import '../../core/constants/app_constants.dart';
import '../../core/services/secure_storage_service.dart';
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
      final token = await SecureStorageService.getToken();
      final dio = Dio(BaseOptions(
        baseUrl: AppConstants.apiBaseUrl,
        headers: {'Authorization': 'Bearer $token'},
      ));
      final response = await dio.get('/api/crm/tasks');
      setState(() {
        tasks = response.data['items'] ?? [];
        isLoading = false;
      });
    } catch (e) {
      setState(() => isLoading = false);
    }
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
                  onChanged: (v) {},
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
        onPressed: () {},
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
