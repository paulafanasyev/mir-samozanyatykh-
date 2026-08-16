import 'package:flutter/material.dart';
import '../services/api_service.dart';

class GrantsScreen extends StatefulWidget {
  const GrantsScreen({super.key});

  @override
  State<GrantsScreen> createState() => _GrantsScreenState();
}

class _GrantsScreenState extends State<GrantsScreen> {
  final _api = ApiService();
  List<dynamic> _grants = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadGrants();
  }

  Future<void> _loadGrants() async {
    try {
      final data = await _api.get('/api/grants');
      setState(() {
        _grants = data['grants'] ?? [];
        _loading = false;
      });
    } catch (e) {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) return const Center(child: CircularProgressIndicator());
    if (_grants.isEmpty) {
      return const Center(child: Text('Пока нет активных грантов', style: TextStyle(color: Colors.grey)));
    }
    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: _grants.length,
      itemBuilder: (context, index) {
        final g = _grants[index];
        return Card(
          margin: const EdgeInsets.only(bottom: 12),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(g['title'] ?? 'Без названия', style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                const SizedBox(height: 8),
                Text(g['organization'] ?? '', style: TextStyle(color: Colors.grey.shade600)),
                const SizedBox(height: 8),
                Text('Сумма: ${g['amount_min']?.toString() ?? '0'} — ${g['amount_max']?.toString() ?? '0'} ₽'),
                if (g['deadline'] != null)
                  Text('Дедлайн: ${g['deadline'].toString().substring(0, 10)}', style: const TextStyle(color: Colors.red)),
                const SizedBox(height: 8),
                Wrap(
                  spacing: 8,
                  children: [
                    if (g['category'] != null) Chip(label: Text(g['category']), visualDensity: VisualDensity.compact),
                    if (g['region'] != null) Chip(label: Text(g['region']), visualDensity: VisualDensity.compact),
                  ],
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}
