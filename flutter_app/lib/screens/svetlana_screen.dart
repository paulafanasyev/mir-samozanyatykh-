import 'package:flutter/material.dart';
import '../services/api_service.dart';
import 'dart:convert';

class SvetlanaScreen extends StatefulWidget {
  const SvetlanaScreen({super.key});

  @override
  State<SvetlanaScreen> createState() => _SvetlanaScreenState();
}

class _SvetlanaScreenState extends State<SvetlanaScreen> {
  final _ctrl = TextEditingController();
  final List<Map<String, dynamic>> _messages = [];
  bool _typing = false;

  @override
  void initState() {
    super.initState();
    _messages.add({
      'text': 'Здравствуйте! Я Светлана, ваш ИИ-ассистент. Чем могу помочь?',
      'isUser': false,
      'time': DateTime.now(),
    });
  }

  Future<void> _send() async {
    final text = _ctrl.text.trim();
    if (text.isEmpty) return;

    setState(() {
      _messages.add({'text': text, 'isUser': true, 'time': DateTime.now()});
      _typing = true;
      _ctrl.clear();
    });

    final res = await ApiService.post('/api/svetlana/chat', {'message': text});
    setState(() {
      _typing = false;
      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        _messages.add({'text': data['response'], 'isUser': false, 'time': DateTime.now()});
      } else {
        _messages.add({'text': 'Извините, произошла ошибка.', 'isUser': false, 'time': DateTime.now()});
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('💡 Светлана')),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: _messages.length,
              itemBuilder: (ctx, i) {
                final msg = _messages[i];
                final isUser = msg['isUser'] as bool;
                return Align(
                  alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
                  child: Container(
                    margin: const EdgeInsets.only(bottom: 12),
                    padding: const EdgeInsets.all(14),
                    constraints: BoxConstraints(maxWidth: MediaQuery.of(ctx).size.width * 0.75),
                    decoration: BoxDecoration(
                      color: isUser ? const Color(0xFFF5A623).withOpacity(0.2) : const Color(0xFF242424),
                      borderRadius: BorderRadius.circular(16).copyWith(
                        bottomRight: isUser ? const Radius.circular(4) : null,
                        bottomLeft: !isUser ? const Radius.circular(4) : null,
                      ),
                    ),
                    child: Text(msg['text'], style: const TextStyle(fontSize: 15)),
                  ),
                );
              },
            ),
          ),
          if (_typing)
            const Padding(
              padding: EdgeInsets.only(left: 16, bottom: 8),
              child: Align(
                alignment: Alignment.centerLeft,
                child: Text('Светлана печатает...', style: TextStyle(color: Colors.grey, fontSize: 12)),
              ),
            ),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: const Color(0xFF1A1A1A),
              border: Border(top: BorderSide(color: Colors.grey[800]!)),
            ),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _ctrl,
                    decoration: InputDecoration(
                      hintText: 'Задайте вопрос...',
                      filled: true,
                      fillColor: const Color(0xFF242424),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(24),
                        borderSide: BorderSide.none,
                      ),
                      contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
                    ),
                    onSubmitted: (_) => _send(),
                  ),
                ),
                const SizedBox(width: 8),
                CircleAvatar(
                  backgroundColor: const Color(0xFFF5A623),
                  child: IconButton(
                    icon: const Icon(Icons.send, color: Colors.black, size: 20),
                    onPressed: _send,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
