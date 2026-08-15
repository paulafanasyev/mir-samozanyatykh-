import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shimmer/shimmer.dart';

import '../../../core/theme/app_theme.dart';
import '../../widgets/common/loading_widget.dart';

class SvetlanaScreen extends ConsumerStatefulWidget {
  const SvetlanaScreen({super.key});

  @override
  ConsumerState<SvetlanaScreen> createState() => _SvetlanaScreenState();
}

class _SvetlanaScreenState extends ConsumerState<SvetlanaScreen> {
  final _messageController = TextEditingController();
  final _scrollController = ScrollController();
  final List<Map<String, dynamic>> _messages = [];
  bool _isTyping = false;

  final List<Map<String, String>> _quickQuestions = [
    {'text': 'Какие налоги платит самозанятый?', 'icon': '💰'},
    {'text': 'Как оформить чек?', 'icon': '🧾'},
    {'text': 'Налоговый вычет 2026', 'icon': '📉'},
    {'text': 'Переход в ИП', 'icon': '🏢'},
    {'text': 'Гранты для самозанятых', 'icon': '🎁'},
    {'text': 'Проверка контрагента', 'icon': '🔍'},
    {'text': 'Больничный для самозанятых', 'icon': '🏥'},
    {'text': 'Международные платежи', 'icon': '🌍'},
  ];

  @override
  void initState() {
    super.initState();
    _messages.add({
      'role': 'assistant',
      'text': 'Здравствуйте! Я Светлана, ваш ИИ-ассистент по вопросам самозанятости и бизнеса.

Я могу помочь с:
• Налогами и отчётностью
• Оформлением документов
• Проверкой контрагентов
• Грантами и поддержкой
• Юридическими вопросами

Чем могу помочь?',
      'time': DateTime.now(),
    });
  }

  @override
  void dispose() {
    _messageController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _sendMessage() {
    final text = _messageController.text.trim();
    if (text.isEmpty) return;

    setState(() {
      _messages.add({'role': 'user', 'text': text, 'time': DateTime.now()});
      _isTyping = true;
      _messageController.clear();
    });

    _scrollToBottom();

    // Simulate AI response
    Future.delayed(const Duration(seconds: 2), () {
      if (!mounted) return;
      setState(() {
        _isTyping = false;
        _messages.add({
          'role': 'assistant',
          'text': _generateResponse(text),
          'time': DateTime.now(),
        });
      });
      _scrollToBottom();
    });
  }

  String _generateResponse(String query) {
    final lower = query.toLowerCase();
    if (lower.contains('налог') || lower.contains('ставк')) {
      return 'В 2026 году ставки НПД:

• 4% — при доходе от физических лиц
• 6% — при доходе от юридических лиц и ИП

Налоговый вычет 10 000 ₽:
• 1% — от физлиц (итого 3%)
• 2% — от юрлиц (итого 4%)

До 2,4 млн ₽ в год — без обязательной отчётности.

⚠️ Это общая информация. Для персональной консультации обратитесь в ФНС.';
    } else if (lower.contains('чек') || lower.contains('квитанц')) {
      return 'Чек самозанятого можно оформить:

1. В мобильном приложении «Мой налог»
2. Через личный кабинет на nalog.ru
3. В нашем приложении — раздел «Счета»

Обязательные поля чека:
• Дата и время
• Наименование услуги/товара
• Сумма
• ИНН покупателя (для юрлиц)

Чек нужно сформировать до получения оплаты или в момент оплаты.';
    } else if (lower.contains('вычет') || lower.contains('вычет')) {
      return 'Налоговый вычет для самозанятых 2026:

📌 Размер: 10 000 ₽ (одноразовый)

📌 Как работает:
• Снижает ставку с 4% → 3% (от физлиц)
• Снижает ставку с 6% → 4% (от юрлиц)

📌 Как получить:
1. Зарегистрироваться в «Мой налог»
2. Вычет применяется автоматически
3. Отслеживайте в приложении

📌 Профессиональный вычет:
• До 20% от дохода
• Требует подтверждения расходов
• Подача декларации 3-НДФЛ';
    }
    return 'Спасибо за вопрос! Я передала его нашему юристу. Обычно ответ приходит в течение 15 минут.

Пока могу предложить посмотреть раздел «База знаний» на сайте или задать уточняющий вопрос.

⚠️ Помните: я предоставляю общую информацию. Для важных решений консультируйтесь с налоговым специалистом или ФНС.';
  }

  void _scrollToBottom() {
    Future.delayed(const Duration(milliseconds: 100), () {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;

    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            Container(
              width: 36,
              height: 36,
              decoration: BoxDecoration(
                color: colorScheme.primaryContainer,
                borderRadius: BorderRadius.circular(10),
              ),
              child: Icon(Icons.smart_toy, color: colorScheme.primary, size: 20),
            ),
            const SizedBox(width: 12),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Светлана', style: theme.textTheme.titleMedium),
                Text(
                  'ИИ-ассистент',
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: colorScheme.onSurfaceVariant,
                  ),
                ),
              ],
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.history),
            onPressed: () {},
          ),
          IconButton(
            icon: const Icon(Icons.more_vert),
            onPressed: () {},
          ),
        ],
      ),
      body: Column(
        children: [
          // Quick questions
          Container(
            height: 48,
            padding: const EdgeInsets.symmetric(horizontal: 12),
            child: ListView.separated(
              scrollDirection: Axis.horizontal,
              itemCount: _quickQuestions.length,
              separatorBuilder: (_, __) => const SizedBox(width: 8),
              itemBuilder: (context, index) {
                final q = _quickQuestions[index];
                return ActionChip(
                  avatar: Text(q['icon']!, style: const TextStyle(fontSize: 14)),
                  label: Text(q['text']!, style: theme.textTheme.bodySmall),
                  onPressed: () {
                    _messageController.text = q['text']!;
                    _sendMessage();
                  },
                );
              },
            ),
          ),
          const Divider(height: 1),

          // Messages
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              padding: const EdgeInsets.all(16),
              itemCount: _messages.length,
              itemBuilder: (context, index) {
                final msg = _messages[index];
                final isUser = msg['role'] == 'user';

                return Align(
                  alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
                  child: Container(
                    margin: const EdgeInsets.only(bottom: 12),
                    padding: const EdgeInsets.all(14),
                    constraints: BoxConstraints(
                      maxWidth: MediaQuery.of(context).size.width * 0.8,
                    ),
                    decoration: BoxDecoration(
                      color: isUser
                          ? colorScheme.primary
                          : colorScheme.surfaceVariant,
                      borderRadius: BorderRadius.only(
                        topLeft: const Radius.circular(16),
                        topRight: const Radius.circular(16),
                        bottomLeft: Radius.circular(isUser ? 16 : 4),
                        bottomRight: Radius.circular(isUser ? 4 : 16),
                      ),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          msg['text'],
                          style: theme.textTheme.bodyMedium?.copyWith(
                            color: isUser ? Colors.white : colorScheme.onSurface,
                            height: 1.5,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          _formatTime(msg['time'] as DateTime),
                          style: theme.textTheme.labelSmall?.copyWith(
                            color: isUser
                                ? Colors.white.withOpacity(0.7)
                                : colorScheme.onSurfaceVariant,
                          ),
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
          ),

          // Typing indicator
          if (_isTyping)
            Padding(
              padding: const EdgeInsets.only(left: 16, bottom: 8),
              child: Align(
                alignment: Alignment.centerLeft,
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                  decoration: BoxDecoration(
                    color: colorScheme.surfaceVariant,
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      SizedBox(
                        width: 40,
                        child: Shimmer.fromColors(
                          baseColor: colorScheme.onSurfaceVariant.withOpacity(0.3),
                          highlightColor: colorScheme.onSurfaceVariant.withOpacity(0.1),
                          child: Row(
                            children: [
                              Container(width: 8, height: 8, decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(4))),
                              const SizedBox(width: 4),
                              Container(width: 8, height: 8, decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(4))),
                              const SizedBox(width: 4),
                              Container(width: 8, height: 8, decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(4))),
                            ],
                          ),
                        ),
                      ),
                      const SizedBox(width: 8),
                      Text('Светлана печатает...', style: theme.textTheme.bodySmall),
                    ],
                  ),
                ),
              ),
            ),

          // Input
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: colorScheme.surface,
              border: Border(
                top: BorderSide(color: colorScheme.outlineVariant),
              ),
            ),
            child: SafeArea(
              child: Row(
                children: [
                  IconButton(
                    icon: Icon(Icons.mic, color: colorScheme.onSurfaceVariant),
                    onPressed: () {},
                  ),
                  Expanded(
                    child: TextField(
                      controller: _messageController,
                      decoration: InputDecoration(
                        hintText: 'Спросите Светлану...',
                        filled: true,
                        fillColor: colorScheme.surfaceVariant,
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(24),
                          borderSide: BorderSide.none,
                        ),
                        contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                      ),
                      textInputAction: TextInputAction.send,
                      onSubmitted: (_) => _sendMessage(),
                      maxLines: null,
                    ),
                  ),
                  const SizedBox(width: 8),
                  IconButton(
                    icon: Icon(Icons.send, color: colorScheme.primary),
                    onPressed: _sendMessage,
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  String _formatTime(DateTime time) {
    return '${time.hour.toString().padLeft(2, '0')}:${time.minute.toString().padLeft(2, '0')}';
  }
}
