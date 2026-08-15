import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:dio/dio.dart';

import '../../core/constants/app_constants.dart';
import '../../core/services/secure_storage_service.dart';

class TaxReportsScreen extends ConsumerStatefulWidget {
  const TaxReportsScreen({super.key});

  @override
  ConsumerState<TaxReportsScreen> createState() => _TaxReportsScreenState();
}

class _TaxReportsScreenState extends ConsumerState<TaxReportsScreen> {
  Map<String, dynamic>? taxData;
  bool isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadTaxData();
  }

  Future<void> _loadTaxData() async {
    try {
      final token = await SecureStorageService.getToken();
      final dio = Dio(BaseOptions(
        baseUrl: AppConstants.apiBaseUrl,
        headers: {'Authorization': 'Bearer $token'},
      ));
      final response = await dio.get('/api/accounting/tax-reports');
      setState(() {
        taxData = response.data;
        isLoading = false;
      });
    } catch (e) {
      setState(() => isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Налоговые отчеты')),
      body: isLoading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(
                children: [
                  _buildSummaryCard(),
                  const SizedBox(height: 16),
                  _buildMonthlyList(),
                ],
              ),
            ),
    );
  }

  Widget _buildSummaryCard() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            const Text('Сводка', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            _buildInfoRow('Доход', '${taxData?['total_income'] ?? '—'} ₽'),
            _buildInfoRow('Налог НПД', '${taxData?['total_tax'] ?? '—'} ₽'),
            _buildInfoRow('Вычет', '${taxData?['total_deduction'] ?? '—'} ₽'),
          ],
        ),
      ),
    );
  }

  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(color: Colors.grey)),
          Text(value, style: const TextStyle(fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }

  Widget _buildMonthlyList() {
    final months = taxData?['months'] as List? ?? [];
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('По месяцам', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
        const SizedBox(height: 8),
        ...months.map((m) => Card(
          child: ListTile(
            title: Text(m['month'] ?? '—'),
            trailing: Text('${m['tax'] ?? '—'} ₽'),
          ),
        )).toList(),
      ],
    );
  }
}
