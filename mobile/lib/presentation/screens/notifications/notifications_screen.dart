import 'package:flutter/material.dart';

class NotificationsScreen extends StatelessWidget {
  const NotificationsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Уведомления'),
        actions: [TextButton(onPressed: () {}, child: const Text('Прочитать все'))],
      ),
      body: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: 8,
        itemBuilder: (context, index) => Card(
          child: ListTile(
            leading: Icon(
              [Icons.receipt, Icons.person, Icons.task, Icons.warning, Icons.check_circle, Icons.money, Icons.message, Icons.trending_up][index],
              color: [Colors.blue, Colors.green, Colors.orange, Colors.red, Colors.green, Colors.purple, Colors.blue, Colors.orange][index],
            ),
            title: Text(['Новый счет', 'Новый клиент', 'Задача просрочена', 'Оплата получена', 'Сделка закрыта', 'Налоговый отчёт', 'Сообщение от Светланы', 'Новая сделка'][index]),
            subtitle: Text('${index + 1} час назад'),
            trailing: index < 3 ? Container(width: 8, height: 8, decoration: const BoxDecoration(color: Colors.red, shape: BoxShape.circle)) : null,
          ),
        ),
      ),
    );
  }
}
