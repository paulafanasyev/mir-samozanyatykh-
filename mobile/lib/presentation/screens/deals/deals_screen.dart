import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:dio/dio.dart';

import '../../core/constants/app_constants.dart';
import '../../core/services/secure_storage_service.dart';
import 'deal_detail_screen.dart';

class DealsScreen extends ConsumerStatefulWidget {
  const DealsScreen({super.key});

  @override
  ConsumerState<DealsScreen> createState() => _DealsScreenState();
}

class _DealsScreenState extends ConsumerState<DealsScreen> {
  List<dynamic> deals = [];
  bool isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadDeals();
  }

  Future<void> _loadDeals() async {
    try {
      final token = await SecureStorageService.getToken();
      final dio = Dio(BaseOptions(
        baseUrl: AppConstants.apiBaseUrl,
        headers: {'Authorization': 'Bearer $token'},
      ));
      final response = await dio.get('/api/crm/deals');
      setState(() {
        deals = response.data['items'] ?? [];
        isLoading = false;
      });
    } catch (e) {
      setState(() => isLoading = false);
    }
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
        onPressed: () {},
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
