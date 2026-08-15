import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:dio/dio.dart';

import '../../core/constants/app_constants.dart';

class InvoiceDetailScreen extends ConsumerStatefulWidget {
  final int invoiceId;
  const InvoiceDetailScreen({super.key, required this.invoiceId});

  @override
  ConsumerState<InvoiceDetailScreen> createState() => _InvoiceDetailScreenState();
}

class _InvoiceDetailScreenState extends ConsumerState<InvoiceDetailScreen> {
  Map<String, dynamic>? invoiceData;
  bool isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadInvoice();
  }

  Future<void> _loadInvoice() async {
    try {
      final dio = Dio(BaseOptions(baseUrl: AppConstants.apiBaseUrl));
      final response = await dio.get('/api/crm/invoices/${widget.invoiceId}');
      setState(() {
        invoiceData = response.data;
        isLoading = false;
      });
    } catch (e) {
      setState(() => isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Счёт'),
        actions: [
          IconButton(icon: const Icon(Icons.share), onPressed: () {}),
          IconButton(icon: const Icon(Icons.download), onPressed: () {}),
        ],
      ),
      body: isLoading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(
                children: [
                  _buildHeader(),
                  const SizedBox(height: 16),
                  _buildItemsList(),
                  const Divider(height: 32),
                  _buildTotal(),
                  const SizedBox(height: 16),
                  _buildPaymentButton(),
                ],
              ),
            ),
    );
  }

  Widget _buildHeader() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            Text('СЧЁТ №${widget.invoiceId}', style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Text('От: ${invoiceData?['from_date'] ?? '—'}', style: const TextStyle(color: Colors.grey)),
            Text('Клиент: ${invoiceData?['client_name'] ?? '—'}'),
          ],
        ),
      ),
    );
  }

  Widget _buildItemsList() {
    final items = invoiceData?['items'] as List? ?? [];
    return Column(
      children: items.map((item) => ListTile(
        title: Text(item['name'] ?? '—'),
        trailing: Text('${item['amount'] ?? '—'} ₽'),
      )).toList(),
    );
  }

  Widget _buildTotal() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        const Text('ИТОГО:', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
        Text('${invoiceData?['total'] ?? '—'} ₽', style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
      ],
    );
  }

  Widget _buildPaymentButton() {
    return SizedBox(
      width: double.infinity,
      child: ElevatedButton.icon(
        onPressed: () {},
        icon: const Icon(Icons.payment),
        label: const Text('Оплатить через ЮKassa'),
      ),
    );
  }
}
