import 'package:flutter/material.dart';

class DealDetailScreen extends StatelessWidget {
  final int dealId;
  const DealDetailScreen({super.key, required this.dealId});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Сделка')),
      body: Center(child: Text('Сделка ID: $dealId')),
    );
  }
}
