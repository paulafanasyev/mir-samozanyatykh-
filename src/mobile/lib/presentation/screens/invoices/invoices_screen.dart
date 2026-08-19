import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../data/datasources/remote/api_client.dart';
import 'invoice_detail_screen.dart';

class InvoicesScreen extends ConsumerStatefulWidget {
  const InvoicesScreen({super.key});

  @override
  ConsumerState<InvoicesScreen> createState() => _InvoicesScreenState();
}

class _InvoicesScreenState extends ConsumerState<InvoicesScreen> {
  List<dynamic> invoices = [];
  List<dynamic> clients = [];
  bool isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadInvoices();
  }

  Future<void> _loadInvoices() async {
    try { final api=ApiClient(); final r=await api.getInvoices(); final c=await api.getClients(); final d=r.data; final items=d is List?d:(d['invoices']??d['items']??[]); if(mounted)setState((){invoices=List<dynamic>.from(items);clients=List<dynamic>.from(c.data is List ? c.data : []);isLoading=false;}); } catch(_){if(mounted)setState(()=>isLoading=false);}
  }
  Future<void> _createInvoice() async {
    if (clients.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Сначала создайте клиента')));
      return;
    }
    final description = TextEditingController();
    final price = TextEditingController();
    int? clientId = clients.first['id'] as int?;
    final ok = await showDialog<bool>(
      context: context,
      builder: (context) => StatefulBuilder(builder: (context, setDialogState) => AlertDialog(
        title: const Text('Новый счёт'),
        content: Column(mainAxisSize: MainAxisSize.min, children: [
          DropdownButtonFormField<int>(
            value: clientId,
            items: clients.map<DropdownMenuItem<int>>((c) => DropdownMenuItem<int>(value: c['id'] as int, child: Text('${c['name'] ?? 'Клиент'}'))).toList(),
            onChanged: (v) => setDialogState(() => clientId = v),
            decoration: const InputDecoration(labelText: 'Клиент'),
          ),
          TextField(controller: description, decoration: const InputDecoration(labelText: 'Описание услуги')),
          TextField(controller: price, keyboardType: const TextInputType.numberWithOptions(decimal: true), decoration: const InputDecoration(labelText: 'Цена, ₽')),
        ]),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Отмена')),
          FilledButton(onPressed: () async {
            final amount = double.tryParse(price.text.replaceAll(',', '.'));
            if (clientId == null || description.text.trim().isEmpty || amount == null || amount <= 0) return;
            try {
              await ApiClient().createInvoice({
                'client_id': clientId,
                'items': [{'description': description.text.trim(), 'quantity': 1, 'unit_price': amount}],
              });
              if (context.mounted) Navigator.pop(context, true);
            } catch (_) {
              if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Не удалось создать счёт')));
            }
          }, child: const Text('Создать')),
        ],
      )),
    );
    description.dispose();
    price.dispose();
    if (ok == true) _loadInvoices();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Счета')),
      body: isLoading
          ? const Center(child: CircularProgressIndicator())
          : ListView.builder(
              itemCount: invoices.length,
              itemBuilder: (context, index) {
                final inv = invoices[index];
                return ListTile(
                  leading: const Icon(Icons.receipt),
                  title: Text('Счёт №${inv['id']}'),
                  subtitle: Text('${inv['total_amount'] ?? '—'} ₽'),
                  trailing: inv['is_paid'] == true
                      ? const Icon(Icons.check_circle, color: Colors.green)
                      : const Icon(Icons.pending, color: Colors.orange),
                  onTap: () => Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (_) => InvoiceDetailScreen(invoiceId: inv['id']),
                    ),
                  ),
                );
              },
            ),
      floatingActionButton: FloatingActionButton(
        onPressed: _createInvoice,
        child: const Icon(Icons.add),
      ),
    );
  }
}
