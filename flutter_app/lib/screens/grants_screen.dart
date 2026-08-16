import 'package:flutter/material.dart';

class GrantsScreen extends StatelessWidget {
  const GrantsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('🎁 Гранты')),
      body: const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.card_giftcard, size: 64, color: Color(0xFFF5A623)),
            SizedBox(height: 16),
            Text('🎁 Гранты', style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
            SizedBox(height: 8),
            Text('В разработке', style: TextStyle(color: Colors.grey)),
          ],
        ),
      ),
    );
  }
}
