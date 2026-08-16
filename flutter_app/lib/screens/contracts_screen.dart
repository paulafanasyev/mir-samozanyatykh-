import 'package:flutter/material.dart';
import '../services/api_service.dart';
import 'dart:convert';

class ContractsScreen extends StatefulWidget {
  const ContractsScreen({super.key});

  @override
  State<ContractsScreen> createState() => _ContractsScreenState();
}

class _ContractsScreenState extends State<ContractsScreen> {
  List<dynamic> _items = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final res = await ApiService.get('/api/contracts');
    setState(() {
      _items = res.statusCode == 200 ? jsonDecode(res.body)['items'] : [];
      _loading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('📝 Договоры')),
      body: _loading
          ? const Center(child: CircularProgressIndicator(color: Color(0xFFF5A623)))
          : _items.isEmpty
              ? const Center(child: Text('Нет договоров'))
              : ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: _items.length,
                  itemBuilder: (ctx, i) {
                    final c = _items[i];
                    return Card(
                      child: ListTile(
                        title: Text(c['title'] ?? ''),
                        subtitle: Text('${c['client_name']} • ${c['amount']}₽'),
                        trailing: Chip(
                          label: Text(c['status'] ?? 'draft', style: const TextStyle(fontSize: 12)),
                          backgroundColor: c['status'] == 'active' ? Colors.green.withOpacity(0.2) : Colors.orange.withOpacity(0.2),
                        ),
                      ),
                    );
                  },
                ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {},
        backgroundColor: const Color(0xFFF5A623),
        child: const Icon(Icons.add, color: Colors.black),
      ),
    );
  }
}
