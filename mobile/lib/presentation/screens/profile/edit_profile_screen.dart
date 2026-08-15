import 'package:flutter/material.dart';

class EditProfileScreen extends StatelessWidget {
  const EditProfileScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Редактировать профиль')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            const CircleAvatar(radius: 50, child: Icon(Icons.person, size: 50)),
            const SizedBox(height: 24),
            const TextField(decoration: InputDecoration(labelText: 'Имя')),
            const SizedBox(height: 16),
            const TextField(decoration: InputDecoration(labelText: 'Email')),
            const SizedBox(height: 16),
            const TextField(decoration: InputDecoration(labelText: 'Телефон')),
            const SizedBox(height: 16),
            const TextField(decoration: InputDecoration(labelText: 'ИНН')),
            const SizedBox(height: 24),
            FilledButton(onPressed: () {}, child: const Text('Сохранить')),
          ],
        ),
      ),
    );
  }
}
