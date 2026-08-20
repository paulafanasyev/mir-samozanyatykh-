import 'package:flutter/material.dart';

import '../../../data/datasources/remote/api_client.dart';
import '../../widgets/common/loading_widget.dart';

class ContractsScreen extends StatefulWidget {
  const ContractsScreen({super.key});

  @override
  State<ContractsScreen> createState() => _ContractsScreenState();
}

class _ContractsScreenState extends State<ContractsScreen> {
  final _api = ApiClient();
  List<dynamic> contracts = [];
  bool isLoading = true;
  String? error;

  @override
  void initState() {
    super.initState();
    _loadContracts();
  }

  Future<void> _loadContracts() async {
    try {
      final response = await _api.getContracts();
      final data = response.data;
      final items = data is List
          ? data
          : data is Map
              ? (data['items'] ?? data['contracts'] ?? const [])
              : const [];
      if (!mounted) return;
      setState(() {
        contracts = List<dynamic>.from(items is Iterable ? items : const []);
        isLoading = false;
        error = null;
      });
    } catch (_) {
      if (mounted) setState(() { isLoading = false; error = 'Не удалось загрузить договоры'; });
    }
  }

  void _showContract(BuildContext context, dynamic raw) {
    final contract = raw is Map ? Map<String, dynamic>.from(raw) : <String, dynamic>{};
    showDialog<void>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: Text(contract['title']?.toString() ?? 'Договор'),
        content: Text('Статус: ${contract['status'] ?? '—'}\nID: ${contract['id'] ?? '—'}'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(dialogContext), child: const Text('Закрыть')),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Договоры')),
      body: isLoading
          ? const LoadingWidget()
          : error != null
              ? Center(child: Text(error!))
              : RefreshIndicator(
                  onRefresh: _loadContracts,
                  child: contracts.isEmpty
                      ? ListView(children: const [SizedBox(height: 180), Center(child: Text('Договоров пока нет'))])
                      : ListView.separated(
                          itemCount: contracts.length,
                          separatorBuilder: (_, __) => const Divider(height: 1),
                          itemBuilder: (context, index) {
                            final c = contracts[index] is Map ? contracts[index] as Map : const {};
                            return ListTile(
                              leading: const Icon(Icons.description),
                              title: Text((c['title'] ?? 'Договор').toString()),
                              subtitle: Text('Статус: ${(c['status'] ?? '—').toString()}'),
                              trailing: const Icon(Icons.chevron_right),
                              onTap: () => _showContract(context, c),
                            );
                          },
                        ),
                ),
    );
  }
}
