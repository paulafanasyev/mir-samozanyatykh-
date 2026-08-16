import 'package:flutter/material.dart';

class MarketplaceScreen extends StatelessWidget {
  const MarketplaceScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('🏪 Маркетплейс')),
      body: const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.store, size: 64, color: Color(0xFFF5A623)),
            SizedBox(height: 16),
            Text('🏪 Маркетплейс', style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
            SizedBox(height: 8),
            Text('В разработке', style: TextStyle(color: Colors.grey)),
          ],
        ),
      ),
    );
  }
}
