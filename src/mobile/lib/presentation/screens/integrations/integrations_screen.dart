import 'package:flutter/material.dart';
import '../../../data/datasources/remote/api_client.dart';

class IntegrationsScreen extends StatefulWidget {
  const IntegrationsScreen({super.key});

  @override
  State<IntegrationsScreen> createState() => _IntegrationsScreenState();
}

class _IntegrationsScreenState extends State<IntegrationsScreen> {
  final _api = ApiClient();
  bool _loading = true;
  String? _error;
  List<dynamic> _keys = [];
  List<dynamic> _webhooks = [];

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() { _loading = true; _error = null; });
    try {
      final results = await Future.wait([_api.getApiKeys(), _api.getWebhooks()]);
      final keys = results[0].data;
      final hooks = results[1].data;
      if (!mounted) return;
      setState(() {
        _keys = keys is List ? keys : [];
        _webhooks = hooks is Map && hooks['webhooks'] is List ? hooks['webhooks'] : [];
        _loading = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() { _loading = false; _error = 'Не удалось загрузить интеграции'; });
    }
  }

  Future<void> _createKey() async {
    try {
      final response = await _api.createApiKey({'name': 'Mobile key', 'scopes': ['read']});
      final key = response.data is Map ? response.data['key']?.toString() : null;
      if (!mounted) return;
      await _load();
      if (key != null) {
        await showDialog<void>(context: context, builder: (_) => AlertDialog(
          title: const Text('API-ключ создан'),
          content: SelectableText(key),
          actions: [TextButton(onPressed: () => Navigator.pop(context), child: const Text('Закрыть'))],
        ));
      }
    } catch (_) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Не удалось создать API-ключ')));
    }
  }

  Future<void> _revokeKey(String id) async {
    try {
      await _api.revokeApiKey(id);
      await _load();
    } catch (_) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Не удалось отозвать API-ключ')));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Интеграции и API')),
      body: RefreshIndicator(
        onRefresh: _load,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            if (_loading) const LinearProgressIndicator(),
            if (_error != null) Padding(padding: const EdgeInsets.all(16), child: Text(_error!)),
            _section('API ключи', [
              if (_keys.isEmpty) const ListTile(title: Text('Активных ключей нет')),
              ..._keys.map((k) => ListTile(
                leading: const Icon(Icons.key),
                title: Text((k is Map ? k['name'] : null)?.toString() ?? 'API-ключ'),
                subtitle: Text((k is Map ? k['key_prefix'] : null)?.toString() ?? ''),
                trailing: IconButton(icon: const Icon(Icons.delete_outline), onPressed: () => _revokeKey(k['id'].toString())),
              )),
              ListTile(leading: const Icon(Icons.add), title: const Text('Создать API-ключ'), onTap: _createKey),
            ]),
            _section('Вебхуки', [
              if (_webhooks.isEmpty) const ListTile(title: Text('Вебхуков нет')),
              ..._webhooks.map((w) => ListTile(
                leading: const Icon(Icons.webhook),
                title: Text((w is Map ? w['url'] : null)?.toString() ?? ''),
                subtitle: Text((w is Map ? w['is_active'] : false) == true ? 'Активен' : 'Отключён'),
              )),
            ]),
            _section('Экспорт', [
              const ListTile(
                leading: Icon(Icons.download),
                title: Text('Экспорт'),
                subtitle: Text('Экспорт доступен через API и web-панель.'),
              ),
            ]),
          ],
        ),
      ),
    );
  }

  Widget _section(String title, List<Widget> children) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Padding(padding: const EdgeInsets.only(left: 8, top: 16, bottom: 8), child: Text(title, style: Theme.of(context).textTheme.titleMedium)),
      Card(child: Column(children: children)),
    ],
  );
}
