import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../../data/datasources/remote/api_client.dart';
import '../../widgets/common/loading_widget.dart';

class AccountingScreen extends StatefulWidget {
  const AccountingScreen({super.key});
  @override State<AccountingScreen> createState() => _AccountingScreenState();
}
class _AccountingScreenState extends State<AccountingScreen> {
  final _api = ApiClient();
  bool _loading = true;
  String? _error;
  DecimalValue _balance = const DecimalValue(0);

  @override void initState() { super.initState(); _load(); }
  Future<void> _load() async {
    try {
      final r = await _api.getTransactions(page: 1);
      final data = r.data is Map ? Map<String,dynamic>.from(r.data) : {'items': r.data};
      final items = (data['items'] as List? ?? const []);
      double balance = 0;
      for (final raw in items) {
        final m = Map<String,dynamic>.from(raw as Map);
        final amount = double.tryParse(m['amount']?.toString() ?? '') ?? 0;
        balance += m['transaction_type'] == 'expense' ? -amount : amount;
      }
      if (mounted) setState(() { _balance = DecimalValue(balance); _loading = false; });
    } catch (_) { if (mounted) setState(() { _error = 'Не удалось загрузить бухгалтерию'; _loading = false; }); }
  }
  @override Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(appBar: AppBar(title: const Text('Бухгалтерия')), body: _loading ? const LoadingWidget() : _error != null ? Center(child: Text(_error!)) : RefreshIndicator(
      onRefresh: _load, child: ListView(padding: const EdgeInsets.all(16), children: [
        Card(child: Padding(padding: const EdgeInsets.all(16), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text('Баланс загруженных операций', style: theme.textTheme.labelMedium), const SizedBox(height: 4),
          Text('${_balance.value.toStringAsFixed(2)} ₽', style: theme.textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.w700)),
        ]))),
        ListTile(leading: const Icon(Icons.receipt_long, color: Colors.green), title: const Text('Транзакции'), trailing: const Icon(Icons.chevron_right), onTap: () => _showTransactions(context)),
        ListTile(leading: const Icon(Icons.description, color: Colors.blue), title: const Text('Налоговые отчёты'), trailing: const Icon(Icons.chevron_right), onTap: () => context.push('/tax-reports')),
        ListTile(leading: const Icon(Icons.money_off, color: Colors.orange), title: const Text('Вычеты'), trailing: const Icon(Icons.chevron_right), onTap: () => _showDeductions(context)),
      ])));
  }
  Future<void> _showTransactions(BuildContext context) async {
    try {
      final r = await _api.getTransactions(page: 1); final items = r.data is Map ? (r.data['items'] ?? []) : r.data;
      if (!context.mounted) return;
      showModalBottomSheet(context: context, builder: (_) => ListView(children: [for (final raw in (items as List)) ListTile(title: Text((raw['description'] ?? raw['category'] ?? 'Транзакция').toString()), trailing: Text('${raw['amount'] ?? '—'} ₽'))]));
    } catch (_) { if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Не удалось загрузить транзакции'))); }
  }
  Future<void> _showDeductions(BuildContext context) async {
    try { final r = await _api.getTaxDeductions(); if (context.mounted) showModalBottomSheet(context: context, builder: (_) => ListView(children: [for (final raw in (r.data is List ? r.data : (r.data['items'] ?? []))) ListTile(title: Text((raw['description'] ?? raw['type'] ?? 'Вычет').toString()), trailing: Text('${raw['amount'] ?? '—'} ₽'))])); }
    catch (_) { if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Не удалось загрузить вычеты'))); }
  }
}
class DecimalValue { final double value; const DecimalValue(this.value); }
