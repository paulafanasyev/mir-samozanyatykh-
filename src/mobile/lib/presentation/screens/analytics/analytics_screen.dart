import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import '../../../data/datasources/remote/api_client.dart';

class AnalyticsScreen extends StatefulWidget {
  const AnalyticsScreen({super.key});
  @override
  State<AnalyticsScreen> createState() => _AnalyticsScreenState();
}

class _AnalyticsScreenState extends State<AnalyticsScreen> {
  final _api = ApiClient();
  bool _loading = true;
  String? _error;
  Map<String, dynamic> _dashboard = {};
  List<dynamic> _chart = [];

  @override
  void initState() { super.initState(); _load(); }

  Future<void> _load() async {
    setState(() { _loading = true; _error = null; });
    try {
      final results = await Future.wait([_api.getDashboardStats(), _api.getRevenueAnalytics(months: 6)]);
      final dashboard = results[0].data;
      final chart = results[1].data;
      if (!mounted) return;
      setState(() {
        _dashboard = dashboard is Map<String, dynamic> ? dashboard : {};
        _chart = chart is Map && chart['chart_data'] is List ? chart['chart_data'] as List : [];
        _loading = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() { _loading = false; _error = 'Не удалось загрузить аналитику'; });
    }
  }

  @override
  Widget build(BuildContext context) {
    final revenue = (_dashboard['revenue'] as num?)?.toDouble() ?? 0;
    final deals = _dashboard['deals'] is Map ? (_dashboard['deals']['won'] as num?)?.toInt() ?? 0 : 0;
    final clients = _dashboard['clients'] is Map ? (_dashboard['clients']['total'] as num?)?.toInt() ?? 0 : 0;
    final spots = _chart.asMap().entries.map((e) => FlSpot(e.key.toDouble(), ((e.value['revenue'] as num?)?.toDouble() ?? 0))).toList();
    return Scaffold(
      appBar: AppBar(title: const Text('Аналитика')),
      body: RefreshIndicator(
        onRefresh: _load,
        child: ListView(padding: const EdgeInsets.all(16), children: [
          if (_loading) const LinearProgressIndicator(),
          if (_error != null) Padding(padding: const EdgeInsets.all(16), child: Text(_error!)),
          Text('Выручка', style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 16),
          SizedBox(height: 200, child: spots.isEmpty ? const Center(child: Text('Нет данных за период')) : LineChart(LineChartData(
            gridData: const FlGridData(show: false),
            titlesData: const FlTitlesData(show: false),
            borderData: FlBorderData(show: false),
            lineBarsData: [LineChartBarData(spots: spots, isCurved: true, barWidth: 3, belowBarData: BarAreaData(show: true))],
          ))),
          const SizedBox(height: 24),
          Row(children: [
            Expanded(child: _buildStatCard(context, 'Выручка', '${revenue.toStringAsFixed(2)} ₽')),
            const SizedBox(width: 12),
            Expanded(child: _buildStatCard(context, 'Закрыто сделок', deals.toString())),
          ]),
          const SizedBox(height: 12),
          _buildStatCard(context, 'Клиентов всего', clients.toString()),
        ]),
      ),
    );
  }

  Widget _buildStatCard(BuildContext context, String title, String value) => Card(child: Padding(padding: const EdgeInsets.all(16), child: Column(children: [Text(value, style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w700)), const SizedBox(height: 4), Text(title, style: Theme.of(context).textTheme.bodySmall)])));
}
