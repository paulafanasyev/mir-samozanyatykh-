import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../../../data/datasources/remote/api_client.dart';

class ReferralsScreen extends StatefulWidget {
  const ReferralsScreen({super.key});
  @override
  State<ReferralsScreen> createState() => _ReferralsScreenState();
}

class _ReferralsScreenState extends State<ReferralsScreen> {
  final _api = ApiClient();
  Map<String, dynamic> _stats = {};
  String _code = '';
  bool _loading = true;

  @override
  void initState() { super.initState(); _load(); }

  Future<void> _load() async {
    try {
      final results = await Future.wait([_api.getReferralStats(), _api.getReferralCode()]);
      final stats = Map<String, dynamic>.from(results[0].data as Map);
      final code = Map<String, dynamic>.from(results[1].data as Map);
      if (mounted) setState(() { _stats = stats; _code = code['code']?.toString() ?? ''; _loading = false; });
    } catch (_) {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) return const Scaffold(body: Center(child: CircularProgressIndicator()));
    final invited = _stats['referral_count'] ?? _stats['invited'] ?? 0;
    final earned = _stats['earnings'] ?? _stats['referral_earnings'] ?? 0;
    return Scaffold(
      appBar: AppBar(title: const Text('Реферальная программа')),
      body: RefreshIndicator(
        onRefresh: _load,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Card(child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(children: [
                const Text('Ваш реферальный код'),
                const SizedBox(height: 8),
                Row(mainAxisAlignment: MainAxisAlignment.center, children: [
                  Text(_code.isEmpty ? '—' : _code, style: Theme.of(context).textTheme.titleLarge),
                  IconButton(
                    onPressed: _code.isEmpty ? null : () => Clipboard.setData(ClipboardData(text: _code)),
                    icon: const Icon(Icons.copy),
                  ),
                ]),
              ]),
            )),
            const SizedBox(height: 20),
            Row(children: [
              Expanded(child: Card(child: ListTile(title: Text('$invited'), subtitle: const Text('Приглашено')))),
              const SizedBox(width: 12),
              Expanded(child: Card(child: ListTile(title: Text('$earned ₽'), subtitle: const Text('Заработано')))),
            ]),
          ],
        ),
      ),
    );
  }
}
