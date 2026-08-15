import 'package:flutter/material.dart';

class ClientDetailScreen extends StatelessWidget {
  final int clientId;
  const ClientDetailScreen({super.key, required this.clientId});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Клиент')),
      body: Center(child: Text('Клиент ID: $clientId')),
    );
  }
}
