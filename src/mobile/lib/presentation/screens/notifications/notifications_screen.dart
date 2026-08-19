import 'package:flutter/material.dart';
import '../../widgets/common/loading_widget.dart';
import '../../../data/datasources/remote/api_client.dart';

class NotificationsScreen extends StatefulWidget {
  const NotificationsScreen({super.key});
  @override State<NotificationsScreen> createState() => _NotificationsScreenState();
}
class _NotificationsScreenState extends State<NotificationsScreen> {
  final _api = ApiClient();
  List<dynamic> _items = [];
  bool _loading = true;
  String? _error;
  @override void initState() { super.initState(); _load(); }
  Future<void> _load() async { try { final r = await _api.getNotifications(); if (!mounted) return; setState(() { _items = r.data is List ? r.data : (r.data['items'] ?? []); _loading=false; }); } catch(e) { if(mounted) setState((){_error=e.toString();_loading=false;}); } }
  Future<void> _readAll() async { try { await _api.markAllNotificationsRead(); await _load(); } catch (_) {} }
  @override Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Уведомления'), actions:[TextButton(onPressed:_readAll, child:const Text('Прочитать все'))]),
    body: _loading ? const LoadingWidget() : _error != null ? Center(child:Text(_error!)) : RefreshIndicator(
      onRefresh:_load, child: ListView.builder(padding:const EdgeInsets.all(16), itemCount:_items.length,
      itemBuilder:(context,i){ final n=Map<String,dynamic>.from(_items[i] as Map); final id=(n['id'] as num?)?.toInt(); return Card(child:ListTile(
        leading: const Icon(Icons.notifications_outlined), title:Text(n['title']?.toString() ?? 'Уведомление'),
        subtitle:Text(n['message']?.toString() ?? n['body']?.toString() ?? ''),
        trailing:n['is_read']==true ? null : const Icon(Icons.circle,size:10,color:Colors.red),
        onTap:id==null?null:() async { await _api.markNotificationRead(id); await _load(); },
      ));}),
    ),
  );
}
