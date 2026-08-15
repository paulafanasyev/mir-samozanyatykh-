import 'package:flutter/material.dart';

class InvoiceDetailScreen extends StatelessWidget {
  final int invoiceId;
  const InvoiceDetailScreen({super.key, required this.invoiceId});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Счёт')),
      body: Center(child: Text('Счёт ID: $invoiceId')),
    );
  }
}
