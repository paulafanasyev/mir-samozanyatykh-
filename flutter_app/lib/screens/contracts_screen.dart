import 'package:flutter/material.dart';
import '../services/api_service.dart';

class ContractsScreen extends StatefulWidget {
  const ContractsScreen({super.key});

  @override
  State<ContractsScreen> createState() => _ContractsScreenState();
}

class _ContractsScreenState extends State<ContractsScreen> {
  final _api = ApiService();
  List<dynamic> _contracts = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadContracts();
  }

  Future<void> _loadContracts() async {
    try {
      final data = await _api.get('/api/contracts');
      setState(() {
        _contracts = data['contracts'] ?? [];
        _loading = false;
      });
    } catch (e) {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) return const Center(child: CircularProgressIndicator());
    if (_contracts.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.description_outlined, size: 64, color: Colors.grey),
            const SizedBox(height: 16),
            const Text('Пока нет договоров', style: TextStyle(color: Colors.grey)),
            const SizedBox(height: 16),
            ElevatedButton.icon(
              onPressed: () => _showCreateDialog(),
              icon: const Icon(Icons.add),
              label: const Text('Создать договор'),
            ),
          ],
        ),
      );
    }
    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: _contracts.length,
      itemBuilder: (context, index) {
        final c = _contracts[index];
        return Card(
          margin: const EdgeInsets.only(bottom: 12),
          child: ListTile(
            leading: const Icon(Icons.description, color: Color(0xFF667eea)),
            title: Text(c['title'] ?? 'Без названия'),
            subtitle: Text('${c['client_name'] ?? ''} • ${c['amount']?.toString() ?? '0'} ₽'),
            trailing: Chip(
              label: Text(c['status'] ?? 'draft', style: const TextStyle(fontSize: 12)),
              backgroundColor: _statusColor(c['status']),
            ),
          ),
        );
      },
    );
  }

  Color _statusColor(String? status) {
    switch (status) {
      case 'signed': return Colors.green.shade100;
      case 'sent': return Colors.blue.shade100;
      case 'completed': return Colors.purple.shade100;
      default: return Colors.orange.shade100;
    }
  }

  void _showCreateDialog() {
    // TODO: Implement create contract dialog
  }
}
