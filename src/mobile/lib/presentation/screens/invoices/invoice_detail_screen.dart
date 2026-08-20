import 'package:flutter/material.dart';

import '../../../data/datasources/remote/api_client.dart';

class InvoiceDetailScreen extends StatefulWidget {
  final int invoiceId;
  const InvoiceDetailScreen({super.key, required this.invoiceId});

  @override
  State<InvoiceDetailScreen> createState() => _InvoiceDetailScreenState();
}

class _InvoiceDetailScreenState extends State<InvoiceDetailScreen> {
  Map<String, dynamic>? invoiceData;
  bool isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadInvoice();
  }

  Future<void> _loadInvoice() async {
    try {
      final response = await ApiClient().getInvoice(widget.invoiceId);
      if (!mounted) return;
      final raw = response.data;
      setState(() {
        invoiceData = raw is Map ? Map<String, dynamic>.from(raw) : <String, dynamic>{};
        isLoading = false;
      });
    } catch (_) {
      if (mounted) setState(() => isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Счёт'),
        actions: [
          IconButton(
            icon: const Icon(Icons.share),
            onPressed: () => ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Ссылка на счёт подготовлена.'))),
          ),
          IconButton(
            icon: const Icon(Icons.download),
            onPressed: () => ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Скачивание PDF доступно через web-версию.'))),
          ),
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

  Widget _buildHeader() => Card(
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

  Widget _buildItemsList() {
    final rawItems = invoiceData?['items'];
    final items = rawItems is List ? rawItems : const [];
    return Column(
      children: items.map<Widget>((item) {
        final data = item is Map ? item : const {};
        return ListTile(
          title: Text((data['name'] ?? data['description'] ?? '—').toString()),
          trailing: Text('${data['amount'] ?? data['total'] ?? '—'} ₽'),
        );
      }).toList(),
    );
  }

  Widget _buildTotal() => Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          const Text('ИТОГО:', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
          Text('${invoiceData?['total'] ?? invoiceData?['total_amount'] ?? '—'} ₽', style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
        ],
      );

  Widget _buildPaymentButton() => SizedBox(
        width: double.infinity,
        child: ElevatedButton.icon(
          onPressed: () => ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Ссылка на счёт подготовлена.'))),
          icon: const Icon(Icons.payment),
          label: const Text('Оплатить через ЮKassa'),
        ),
      );
}
