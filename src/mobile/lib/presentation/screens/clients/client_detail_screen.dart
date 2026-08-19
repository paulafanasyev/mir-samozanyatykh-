import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../data/datasources/remote/api_client.dart';

class ClientDetailScreen extends ConsumerStatefulWidget {
  final int clientId;
  const ClientDetailScreen({super.key, required this.clientId});

  @override
  ConsumerState<ClientDetailScreen> createState() => _ClientDetailScreenState();
}

class _ClientDetailScreenState extends ConsumerState<ClientDetailScreen> {
  Map<String, dynamic>? clientData;
  bool isLoading = true;
  String? error;

  @override
  void initState() {
    super.initState();
    _loadClient();
  }

  Future<void> _loadClient() async {
    try {
      final response = await ApiClient().getClient(widget.clientId);
      if (!mounted) return;
      setState(() { clientData = Map<String,dynamic>.from(response.data); isLoading = false; });
    } catch (e) { if (mounted) setState(() { error = e.toString(); isLoading = false; }); }
  }

  Future<void> _deleteClient() async {
    final ok = await showDialog<bool>(context: context, builder: (context) => AlertDialog(title: const Text('Удалить клиента?'), content: const Text('Это действие нельзя отменить.'), actions: [TextButton(onPressed: () => Navigator.pop(context), child: const Text('Отмена')), FilledButton(onPressed: () => Navigator.pop(context, true), child: const Text('Удалить'))]));
    if (ok == true) { try { await ApiClient().deleteClient(widget.clientId); if (mounted) Navigator.pop(context, true); } catch (_) {} }
  }

  Future<void> _showContact(String title, String value) async {
    await showDialog<void>(context: context, builder: (context) => AlertDialog(title: Text(title), content: SelectableText(value.isEmpty ? 'Не указано' : value), actions: [TextButton(onPressed: () => Navigator.pop(context), child: const Text('Закрыть'))]));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Клиент'),
        actions: [
          IconButton(
            icon: const Icon(Icons.edit),
            onPressed: () => _showContact('Редактирование', 'Используйте веб-интерфейс для расширенного редактирования клиента.'),
          ),
          IconButton(
            icon: const Icon(Icons.delete),
            onPressed: _deleteClient,
          ),
        ],
      ),
      body: isLoading
          ? const Center(child: CircularProgressIndicator())
          : error != null
              ? Center(child: Text('Ошибка: $error'))
              : SingleChildScrollView(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      _buildInfoCard('Имя', clientData?['name'] ?? '—'),
                      _buildInfoCard('Email', clientData?['email'] ?? '—'),
                      _buildInfoCard('Телефон', clientData?['phone'] ?? '—'),
                      _buildInfoCard('Компания', clientData?['company'] ?? '—'),
                      _buildInfoCard('ИНН', clientData?['inn'] ?? '—'),
                      _buildInfoCard('Статус', clientData?['status'] ?? '—'),
                      const SizedBox(height: 16),
                      _buildActionsSection(),
                    ],
                  ),
                ),
    );
  }

  Widget _buildInfoCard(String label, String value) {
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ListTile(
        title: Text(label, style: const TextStyle(fontSize: 12, color: Colors.grey)),
        subtitle: Text(value, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w500)),
      ),
    );
  }

  Widget _buildActionsSection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('Действия', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
        const SizedBox(height: 8),
        Wrap(
          spacing: 8,
          children: [
            ActionChip(
              avatar: const Icon(Icons.phone),
              label: const Text('Позвонить'),
              onPressed: () => _showContact('Телефон', clientData?['phone']?.toString() ?? ''),
            ),
            ActionChip(
              avatar: const Icon(Icons.email),
              label: const Text('Email'),
              onPressed: () => _showContact('Email', clientData?['email']?.toString() ?? ''),
            ),
            ActionChip(
              avatar: const Icon(Icons.description),
              label: const Text('Договор'),
              onPressed: () => _showContact('Договор', 'Создание договора доступно через раздел Договоры.'),
            ),
          ],
        ),
      ],
    );
  }
}
