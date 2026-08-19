import 'package:flutter/material.dart';
import 'package:table_calendar/table_calendar.dart';
import '../../../data/datasources/remote/api_client.dart';
import '../../widgets/common/loading_widget.dart';

class CalendarScreen extends StatefulWidget {
  const CalendarScreen({super.key});
  @override State<CalendarScreen> createState() => _CalendarScreenState();
}

class _CalendarScreenState extends State<CalendarScreen> {
  final _api = ApiClient();
  CalendarFormat _calendarFormat = CalendarFormat.month;
  DateTime _focusedDay = DateTime.now();
  DateTime? _selectedDay;
  List<dynamic> _events = [];
  bool _loading = true;
  String? _error;

  @override void initState() { super.initState(); _selectedDay = DateTime.now(); _load(); }

  Future<void> _load() async {
    setState(() { _loading = true; _error = null; });
    try {
      final start = DateTime(_focusedDay.year, _focusedDay.month, 1);
      final end = DateTime(_focusedDay.year, _focusedDay.month + 1, 1);
      final r = await _api.getEvents(start: start, end: end);
      if (!mounted) return;
      setState(() { _events = r.data is List ? r.data : (r.data['events'] ?? []); _loading = false; });
    } catch (e) {
      if (mounted) setState(() { _error = 'Не удалось загрузить календарь'; _loading = false; });
    }
  }

  Future<void> _addEvent() async {
    final controller = TextEditingController();
    final title = await showDialog<String>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Новое событие'),
        content: TextField(controller: controller, maxLength: 255, decoration: const InputDecoration(labelText: 'Название')),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Отмена')),
          FilledButton(onPressed: () => Navigator.pop(context, controller.text.trim()), child: const Text('Создать')),
        ],
      ),
    );
    controller.dispose();
    if (title == null || title.isEmpty || !mounted) return;
    final start = _selectedDay ?? DateTime.now();
    try {
      await _api.createCalendarEvent({
        'title': title,
        'event_type': 'meeting',
        'start_time': start.toIso8601String(),
        'all_day': true,
        'reminder_minutes': 15,
      });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Событие создано')));
        await _load();
      }
    } catch (_) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Не удалось создать событие')));
    }
  }

  @override Widget build(BuildContext context) {
    final selected = _selectedDay;
    final dayEvents = selected == null ? <dynamic>[] : _events.where((e) {
      final raw = e is Map ? e['start_time']?.toString() : null;
      final dt = raw == null ? null : DateTime.tryParse(raw);
      return dt != null && isSameDay(dt, selected);
    }).toList();
    return Scaffold(
      appBar: AppBar(title: const Text('Календарь')),
      body: Column(children: [
        TableCalendar(
          firstDay: DateTime.utc(2024, 1, 1), lastDay: DateTime.utc(2035, 12, 31),
          focusedDay: _focusedDay, calendarFormat: _calendarFormat,
          selectedDayPredicate: (day) => isSameDay(_selectedDay, day),
          onDaySelected: (d, f) => setState(() { _selectedDay = d; _focusedDay = f; }),
          onPageChanged: (d) { _focusedDay = d; _load(); },
          onFormatChanged: (f) => setState(() => _calendarFormat = f),
        ),
        const Divider(),
        Expanded(child: _loading ? const LoadingWidget() : _error != null ? Center(child: Text(_error!)) : dayEvents.isEmpty
          ? const Center(child: Text('На выбранный день событий нет'))
          : ListView.builder(padding: const EdgeInsets.all(16), itemCount: dayEvents.length, itemBuilder: (_, i) {
              final e = Map<String, dynamic>.from(dayEvents[i] as Map);
              return ListTile(leading: const Icon(Icons.event), title: Text(e['title']?.toString() ?? 'Событие'), subtitle: Text(e['event_type']?.toString() ?? ''));
            })),
      ]),
      floatingActionButton: FloatingActionButton(onPressed: _loading ? null : _addEvent, child: const Icon(Icons.add)),
    );
  }
}
