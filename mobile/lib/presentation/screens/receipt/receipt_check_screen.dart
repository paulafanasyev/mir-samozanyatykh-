import 'package:flutter/material.dart';

class ReceiptCheckScreen extends StatelessWidget {
  const ReceiptCheckScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Проверка чека ФНС')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const TextField(
              decoration: InputDecoration(
                labelText: 'QR-код чека или данные',
                hintText: 't=20260101T0000&s=100.00&fn=...',
                prefixIcon: Icon(Icons.qr_code),
              ),
              maxLines: 3,
            ),
            const SizedBox(height: 16),
            FilledButton.icon(
              onPressed: () {},
              icon: const Icon(Icons.qr_code_scanner),
              label: const Text('Сканировать QR-код'),
            ),
            const SizedBox(height: 16),
            FilledButton(
              onPressed: () {},
              child: const Text('Проверить чек'),
            ),
          ],
        ),
      ),
    );
  }
}
