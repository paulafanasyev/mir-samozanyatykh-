import 'package:flutter/material.dart';
import '../services/api_service.dart';
import 'dart:convert';

class FinanceScreen extends StatefulWidget {
  const FinanceScreen({super.key});

  @override
  State<FinanceScreen> createState() => _FinanceScreenState();
}

class _FinanceScreenState extends State<FinanceScreen> {
  List<dynamic> _items = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final res = await ApiService.get('/api/finance');
    setState(() {
      _items = res.statusCode == 200 ? jsonDecode(res.body)['items'] : [];
      _loading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('💰 Финансы')),
      body: _loading
          ? const Center(child: CircularProgressIndicator(color: Color(0xFFF5A623)))
          : ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: _items.length,
              itemBuilder: (ctx, i) {
                final f = _items[i];
                final isIncome = f['type'] == 'income';
                return Card(
                  child: ListTile(
                    leading: Icon(
                      isIncome ? Icons.arrow_upward : Icons.arrow_downward,
                      color: isIncome ? Colors.green : Colors.red,
                    ),
                    title: Text(f['description'] ?? f['category'] ?? ''),
                    subtitle: Text(f['category'] ?? ''),
                    trailing: Text(
                      '${isIncome ? '+' : '-'}${f['amount']}₽',
                      style: TextStyle(
                        color: isIncome ? Colors.green : Colors.red,
                        fontWeight: FontWeight.bold,
                        fontSize: 16,
                      ),
                    ),
                  ),
                );
              },
            ),
    );
  }
}
