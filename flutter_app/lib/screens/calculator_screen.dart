import 'package:flutter/material.dart';
import '../services/api_service.dart';
import 'dart:convert';

class CalculatorScreen extends StatefulWidget {
  const CalculatorScreen({super.key});

  @override
  State<CalculatorScreen> createState() => _CalculatorScreenState();
}

class _CalculatorScreenState extends State<CalculatorScreen> {
  final _ctrl = TextEditingController();
  Map<String, dynamic>? _result;

  Future<void> _calc() async {
    final amount = double.tryParse(_ctrl.text) ?? 0;
    final res = await ApiService.post('/api/calculator/npd', {'amount': amount, 'region': 'default'});
    if (res.statusCode == 200) {
      setState(() => _result = jsonDecode(res.body));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('🧮 Калькулятор НПД')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            TextField(
              controller: _ctrl,
              decoration: InputDecoration(
                labelText: 'Сумма дохода (₽)',
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                filled: true,
                fillColor: const Color(0xFF1A1A1A),
              ),
              keyboardType: TextInputType.number,
            ),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: _calc,
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFFF5A623),
                foregroundColor: Colors.black,
                padding: const EdgeInsets.symmetric(vertical: 16),
              ),
              child: const Text('Рассчитать', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
            ),
            const SizedBox(height: 24),
            if (_result != null)
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(20),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      _resRow('Сумма', '${_result!['amount']}₽'),
                      _resRow('Ставка', '${(_result!['rate'] * 100).toInt()}%'),
                      _resRow('Налог', '${_result!['tax']}₽'),
                      _resRow('На руки', '${_result!['net']}₽', isTotal: true),
                    ],
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }

  Widget _resRow(String label, String value, {bool isTotal = false}) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: TextStyle(fontSize: 16, color: Colors.grey[400])),
          Text(
            value,
            style: TextStyle(
              fontSize: isTotal ? 20 : 16,
              fontWeight: isTotal ? FontWeight.bold : FontWeight.normal,
              color: isTotal ? const Color(0xFFF5A623) : null,
            ),
          ),
        ],
      ),
    );
  }
}
