import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../data/datasources/remote/api_client.dart';
import 'client_detail_screen.dart';

class ClientsScreen extends ConsumerStatefulWidget {
  const ClientsScreen({super.key});

  @override
  ConsumerState<ClientsScreen> createState() => _ClientsScreenState();
}

class _ClientsScreenState extends ConsumerState<ClientsScreen> {
  List<dynamic> clients = [];
  bool isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadClients();
  }

  Future<void> _loadClients() async {
    try {
      final response = await ApiClient().getClients();
      final data = response.data;
      final items = data is List ? data : (data['items'] ?? data['clients'] ?? []);
      if (!mounted) return;
      setState(() { clients = List<dynamic>.from(items); isLoading = false; });
    } catch (_) {
      if (mounted) setState(() => isLoading = false);
    }
  }

  Future<void> _createClient() async {
    final controller = TextEditingController();
    final created = await showDialog<bool>(context: context, builder: (context) => AlertDialog(
      title: const Text('Новый клиент'),
      content: TextField(controller: controller, autofocus: true, decoration: const InputDecoration(labelText: 'Имя')),
      actions: [TextButton(onPressed: () => Navigator.pop(context), child: const Text('Отмена')), FilledButton(onPressed: () async {
        if (controller.text.trim().isEmpty) return;
        try { await ApiClient().createClient({'name': controller.text.trim()}); if (context.mounted) Navigator.pop(context, true); } catch (_) {}
      }, child: const Text('Создать'))],
    ));
    if (created == true) _loadClients();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Клиенты')),
      body: isLoading
          ? const Center(child: CircularProgressIndicator())
          : ListView.builder(
              itemCount: clients.length,
              itemBuilder: (context, index) {
                final client = clients[index];
                return ListTile(
                  leading: CircleAvatar(child: Text(client['name']?[0] ?? '?')),
                  title: Text(client['name'] ?? 'Без имени'),
                  subtitle: Text(client['email'] ?? ''),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () => Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (_) => ClientDetailScreen(clientId: client['id']),
                    ),
                  ),
                );
              },
            ),
      floatingActionButton: FloatingActionButton(
        onPressed: _createClient,
        child: const Icon(Icons.add),
      ),
    );
  }
}
