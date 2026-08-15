import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:dio/dio.dart';

import '../../core/constants/app_constants.dart';

class TaskDetailScreen extends ConsumerStatefulWidget {
  final int taskId;
  const TaskDetailScreen({super.key, required this.taskId});

  @override
  ConsumerState<TaskDetailScreen> createState() => _TaskDetailScreenState();
}

class _TaskDetailScreenState extends ConsumerState<TaskDetailScreen> {
  Map<String, dynamic>? taskData;
  bool isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadTask();
  }

  Future<void> _loadTask() async {
    try {
      final dio = Dio(BaseOptions(baseUrl: AppConstants.apiBaseUrl));
      final response = await dio.get('/api/crm/tasks/${widget.taskId}');
      setState(() {
        taskData = response.data;
        isLoading = false;
      });
    } catch (e) {
      setState(() => isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Задача'),
        actions: [
          IconButton(
            icon: const Icon(Icons.check_circle),
            onPressed: () {},
          ),
        ],
      ),
      body: isLoading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _buildPriorityBadge(taskData?['priority'] ?? 'medium'),
                  const SizedBox(height: 16),
                  _buildInfoCard('Название', taskData?['title'] ?? 'Задача #${widget.taskId}'),
                  _buildInfoCard('Описание', taskData?['description'] ?? '—'),
                  _buildInfoCard('Дедлайн', taskData?['deadline'] ?? '—'),
                  _buildInfoCard('Назначена', taskData?['assigned_to'] ?? '—'),
                  const SizedBox(height: 16),
                  _buildSubtasks(),
                ],
              ),
            ),
    );
  }

  Widget _buildPriorityBadge(String priority) {
    final colors = {
      'low': Colors.green,
      'medium': Colors.orange,
      'high': Colors.red,
    };
    return Chip(
      backgroundColor: (colors[priority] ?? Colors.grey).withOpacity(0.2),
      label: Text(
        priority.toUpperCase(),
        style: TextStyle(color: colors[priority] ?? Colors.grey),
      ),
    );
  }

  Widget _buildInfoCard(String label, String value) {
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ListTile(
        title: Text(label, style: const TextStyle(fontSize: 12, color: Colors.grey)),
        subtitle: Text(value, style: const TextStyle(fontSize: 16)),
      ),
    );
  }

  Widget _buildSubtasks() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('Подзадачи', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
        const SizedBox(height: 8),
        CheckboxListTile(
          value: false,
          onChanged: (v) {},
          title: const Text('Позвонить клиенту'),
        ),
        CheckboxListTile(
          value: false,
          onChanged: (v) {},
          title: const Text('Отправить документы'),
        ),
      ],
    );
  }
}
