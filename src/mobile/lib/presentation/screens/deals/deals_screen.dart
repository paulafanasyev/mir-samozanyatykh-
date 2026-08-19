import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../data/datasources/remote/api_client.dart';
import 'deal_detail_screen.dart';

class DealsScreen extends ConsumerStatefulWidget {
  const DealsScreen({super.key});

  @override
  ConsumerState<DealsScreen> createState() => _DealsScreenState();
}

class _DealsScreenState extends ConsumerState<DealsScreen> {
  List<dynamic> deals = [];
  List<dynamic> clients = [];
  bool isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadDeals();
  }

  Future<void> _loadDeals() async {
    try { final api=ApiClient(); final r=await api.getDeals(); final c=await api.getClients(); final d=r.data; final items=d is List?d:(d['items']??d['deals']??[]); if(mounted)setState((){deals=List<dynamic>.from(items);clients=List<dynamic>.from(c.data is List ? c.data : []);isLoading=false;}); } catch(_){if(mounted)setState(()=>isLoading=false);}
  }
  Future<void> _createDeal() async {
    if (clients.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Сначала создайте клиента')));
      return;
    }
    final title = TextEditingController();
    int? clientId = clients.first['id'] as int?;
    final ok = await showDialog<bool>(context: context, builder: (context) => StatefulBuilder(builder: (context, setDialogState) => AlertDialog(
      title: const Text('Новая сделка'),
      content: Column(mainAxisSize: MainAxisSize.min, children: [
        TextField(controller: title, decoration: const InputDecoration(labelText: 'Название')),
        DropdownButtonFormField<int>(value: clientId, items: clients.map<DropdownMenuItem<int>>((c) => DropdownMenuItem(value: c['id'] as int, child: Text('${c['name'] ?? 'Клиент'}'))).toList(), onChanged: (v) => setDialogState(() => clientId = v), decoration: const InputDecoration(labelText: 'Клиент')),
      ]),
      actions: [TextButton(onPressed: () => Navigator.pop(context), child: const Text('Отмена')), FilledButton(onPressed: () async { if (title.text.trim().isEmpty || clientId == null) return; try { await ApiClient().createDeal({'title': title.text.trim(), 'client_id': clientId, 'amount': 0}); if (context.mounted) Navigator.pop(context, true); } catch (_) { if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Не удалось создать сделку'))); } }, child: const Text('Создать'))],
    )));
    title.dispose();
    if (ok == true) _loadDeals();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Сделки')),
      body: isLoading
          ? const Center(child: CircularProgressIndicator())
          : ListView.builder(
              itemCount: deals.length,
              itemBuilder: (context, index) {
                final deal = deals[index];
                return Card(
                  child: ListTile(
                    title: Text(deal['title'] ?? 'Сделка'),
                    subtitle: Text('${deal['amount'] ?? '—'} ₽'),
                    trailing: Chip(
                      label: Text(deal['status'] ?? 'new'),
                      backgroundColor: _getStatusColor(deal['status']),
                    ),
                    onTap: () => Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (_) => DealDetailScreen(dealId: deal['id']),
                      ),
                    ),
                  ),
                );
              },
            ),
      floatingActionButton: FloatingActionButton(
        onPressed: _createDeal,
        child: const Icon(Icons.add),
      ),
    );
  }

  Color? _getStatusColor(String? status) {
    switch (status) {
      case 'won': return Colors.green[100];
      case 'lost': return Colors.red[100];
      case 'in_progress': return Colors.orange[100];
      default: return Colors.grey[100];
    }
  }
}
