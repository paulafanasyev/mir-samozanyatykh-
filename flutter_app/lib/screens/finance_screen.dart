import 'package:flutter/material.dart';
import '../services/api_service.dart';

class FinanceScreen extends StatefulWidget {
  const FinanceScreen({super.key});

  @override
  State<FinanceScreen> createState() => _FinanceScreenState();
}

class _FinanceScreenState extends State<FinanceScreen> {
  final _api = ApiService();
  List<dynamic> _records = [];
  Map<String, dynamic> _summary = {};
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadFinance();
  }

  Future<void> _loadFinance() async {
    try {
      final data = await _api.get('/api/finance');
      setState(() {
        _records = data['records'] ?? [];
        _summary = data['summary'] ?? {};
        _loading = false;
      });
    } catch (e) {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) return const Center(child: CircularProgressIndicator());
    return Column(
      children: [
        Container(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              _buildSummaryCard('Доход', _summary['total_income'] ?? 0, Colors.green),
              const SizedBox(width: 12),
              _buildSummaryCard('Расход', _summary['total_expense'] ?? 0, Colors.red),
              const SizedBox(width: 12),
              _buildSummaryCard('Налог', _summary['total_tax'] ?? 0, Colors.orange),
            ],
          ),
        ),
        Expanded(
          child: _records.isEmpty
              ? const Center(child: Text('Пока нет записей', style: TextStyle(color: Colors.grey)))
              : ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: _records.length,
                  itemBuilder: (context, index) {
                    final r = _records[index];
                    return Card(
                      margin: const EdgeInsets.only(bottom: 8),
                      child: ListTile(
                        leading: Icon(
                          r['type'] == 'income' ? Icons.arrow_downward : Icons.arrow_upward,
                          color: r['type'] == 'income' ? Colors.green : Colors.red,
                        ),
                        title: Text('${r['amount']?.toString() ?? '0'} ₽'),
                        subtitle: Text(r['category'] ?? 'Без категории'),
                        trailing: Text(r['date']?.toString().substring(0, 10) ?? ''),
                      ),
                    );
                  },
                ),
        ),
      ],
    );
  }

  Widget _buildSummaryCard(String title, dynamic amount, Color color) {
    return Expanded(
      child: Card(
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Column(
            children: [
              Text(title, style: TextStyle(color: Colors.grey.shade600, fontSize: 12)),
              const SizedBox(height: 4),
              Text(
                '${amount is num ? amount.toStringAsFixed(0) : amount} ₽',
                style: TextStyle(fontWeight: FontWeight.bold, color: color, fontSize: 16),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
