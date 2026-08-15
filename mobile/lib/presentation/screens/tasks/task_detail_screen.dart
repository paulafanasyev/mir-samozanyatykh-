import 'package:flutter/material.dart';

class TaskDetailScreen extends StatelessWidget {
  final int taskId;
  const TaskDetailScreen({super.key, required this.taskId});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Задача')),
      body: Center(child: Text('Задача ID: $taskId')),
    );
  }
}
