import 'package:flutter/material.dart';
import '../services/api_service.dart';

class CRMScreen extends StatefulWidget {
  const CRMScreen({super.key});

  @override
  State<CRMScreen> createState() => _CRMScreenState();
}

class _CRMScreenState extends State<CRMScreen> {
  final _api = ApiService();
  List<dynamic> _contacts = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadContacts();
  }

  Future<void> _loadContacts() async {
    try {
      final data = await _api.get('/api/crm/contacts');
      setState(() {
        _contacts = data['contacts'] ?? [];
        _loading = false;
      });
    } catch (e) {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) return const Center(child: CircularProgressIndicator());
    if (_contacts.isEmpty) {
      return const Center(child: Text('Пока нет контактов', style: TextStyle(color: Colors.grey)));
    }
    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: _contacts.length,
      itemBuilder: (context, index) {
        final c = _contacts[index];
        return Card(
          margin: const EdgeInsets.only(bottom: 8),
          child: ListTile(
            leading: const CircleAvatar(child: Icon(Icons.person)),
            title: Text(c['name'] ?? 'Без имени'),
            subtitle: Text('${c['company'] ?? ''} • ${c['status'] ?? ''}'),
            trailing: IconButton(icon: const Icon(Icons.phone), onPressed: () {}),
          ),
        );
      },
    );
  }
}
