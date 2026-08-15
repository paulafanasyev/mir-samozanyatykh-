import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:dio/dio.dart';

import '../../core/constants/app_constants.dart';

class DealDetailScreen extends ConsumerStatefulWidget {
  final int dealId;
  const DealDetailScreen({super.key, required this.dealId});

  @override
  ConsumerState<DealDetailScreen> createState() => _DealDetailScreenState();
}

class _DealDetailScreenState extends ConsumerState<DealDetailScreen> {
  Map<String, dynamic>? dealData;
  bool isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadDeal();
  }

  Future<void> _loadDeal() async {
    try {
      final dio = Dio(BaseOptions(baseUrl: AppConstants.apiBaseUrl));
      final response = await dio.get('/api/crm/deals/${widget.dealId}');
      setState(() {
        dealData = response.data;
        isLoading = false;
      });
    } catch (e) {
      setState(() => isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Сделка')),
      body: isLoading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _buildStatusBadge(dealData?['status'] ?? 'new'),
                  const SizedBox(height: 16),
                  _buildInfoCard('Название', dealData?['title'] ?? 'Сделка #${widget.dealId}'),
                  _buildInfoCard('Сумма', '${dealData?['amount'] ?? '—'} ₽'),
                  _buildInfoCard('Клиент', dealData?['client_name'] ?? '—'),
                  _buildInfoCard('Описание', dealData?['description'] ?? '—'),
                  const SizedBox(height: 16),
                  _buildTimeline(),
                ],
              ),
            ),
    );
  }

  Widget _buildStatusBadge(String status) {
    final colors = {
      'new': Colors.blue,
      'in_progress': Colors.orange,
      'won': Colors.green,
      'lost': Colors.red,
    };
    return Chip(
      backgroundColor: (colors[status] ?? Colors.grey).withOpacity(0.2),
      label: Text(
        status.toUpperCase(),
        style: TextStyle(color: colors[status] ?? Colors.grey, fontWeight: FontWeight.bold),
      ),
    );
  }

  Widget _buildInfoCard(String label, String value) {
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ListTile(
        title: Text(label, style: const TextStyle(fontSize: 12, color: Colors.grey)),
        subtitle: Text(value, style: const TextStyle(fontSize: 16)),
      ),
    );
  }

  Widget _buildTimeline() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('История', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
        const SizedBox(height: 8),
        ListTile(
          leading: const Icon(Icons.circle, color: Colors.green, size: 12),
          title: const Text('Сделка создана'),
          subtitle: Text(dealData?['created_at'] ?? '—'),
        ),
      ],
    );
  }
}
