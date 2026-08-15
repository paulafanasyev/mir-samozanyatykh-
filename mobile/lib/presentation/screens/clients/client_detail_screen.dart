import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:dio/dio.dart';

import '../../core/constants/app_constants.dart';

class ClientDetailScreen extends ConsumerStatefulWidget {
  final int clientId;
  const ClientDetailScreen({super.key, required this.clientId});

  @override
  ConsumerState<ClientDetailScreen> createState() => _ClientDetailScreenState();
}

class _ClientDetailScreenState extends ConsumerState<ClientDetailScreen> {
  Map<String, dynamic>? clientData;
  bool isLoading = true;
  String? error;

  @override
  void initState() {
    super.initState();
    _loadClient();
  }

  Future<void> _loadClient() async {
    try {
      final dio = Dio(BaseOptions(
        baseUrl: AppConstants.apiBaseUrl,
        headers: {'Authorization': 'Bearer ${await _getToken()}'},
      ));
      final response = await dio.get('/api/crm/clients/${widget.clientId}');
      setState(() {
        clientData = response.data;
        isLoading = false;
      });
    } catch (e) {
      setState(() {
        error = e.toString();
        isLoading = false;
      });
    }
  }

  Future<String> _getToken() async {
    // TODO: Get from secure storage
    return '';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Клиент'),
        actions: [
          IconButton(
            icon: const Icon(Icons.edit),
            onPressed: () {},
          ),
          IconButton(
            icon: const Icon(Icons.delete),
            onPressed: () {},
          ),
        ],
      ),
      body: isLoading
          ? const Center(child: CircularProgressIndicator())
          : error != null
              ? Center(child: Text('Ошибка: $error'))
              : SingleChildScrollView(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      _buildInfoCard('Имя', clientData?['name'] ?? '—'),
                      _buildInfoCard('Email', clientData?['email'] ?? '—'),
                      _buildInfoCard('Телефон', clientData?['phone'] ?? '—'),
                      _buildInfoCard('Компания', clientData?['company'] ?? '—'),
                      _buildInfoCard('ИНН', clientData?['inn'] ?? '—'),
                      _buildInfoCard('Статус', clientData?['status'] ?? '—'),
                      const SizedBox(height: 16),
                      _buildActionsSection(),
                    ],
                  ),
                ),
    );
  }

  Widget _buildInfoCard(String label, String value) {
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ListTile(
        title: Text(label, style: const TextStyle(fontSize: 12, color: Colors.grey)),
        subtitle: Text(value, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w500)),
      ),
    );
  }

  Widget _buildActionsSection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('Действия', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
        const SizedBox(height: 8),
        Wrap(
          spacing: 8,
          children: [
            ActionChip(
              avatar: const Icon(Icons.phone),
              label: const Text('Позвонить'),
              onPressed: () {},
            ),
            ActionChip(
              avatar: const Icon(Icons.email),
              label: const Text('Email'),
              onPressed: () {},
            ),
            ActionChip(
              avatar: const Icon(Icons.description),
              label: const Text('Договор'),
              onPressed: () {},
            ),
          ],
        ),
      ],
    );
  }
}
