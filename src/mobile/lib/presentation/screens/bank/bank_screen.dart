import 'package:flutter/material.dart';
import '../../../data/datasources/remote/api_client.dart';
import '../../widgets/common/loading_widget.dart';

class BankScreen extends StatefulWidget { const BankScreen({super.key}); @override State<BankScreen> createState()=>_BankScreenState(); }
class _BankScreenState extends State<BankScreen> {
  final _api = ApiClient();
  Map<String,dynamic> _status = {};
  bool _loading=true;
  @override void initState(){super.initState();_load();}
  Future<void> _load() async { try { final r=await _api.getBankStatus(); if(mounted)setState(()=>_status=Map<String,dynamic>.from(r.data)); } catch (_) {} finally { if(mounted)setState(()=>_loading=false); } }
  Future<void> _connect(String bank) async {
    final controller=TextEditingController();
    final token=await showDialog<String>(context:context,builder:(_)=>AlertDialog(title:Text('Подключить $bank'),content:TextField(controller:controller,obscureText:true,decoration:const InputDecoration(labelText:'API токен')),actions:[TextButton(onPressed:()=>Navigator.pop(context),child:const Text('Отмена')),FilledButton(onPressed:()=>Navigator.pop(context,controller.text.trim()),child:const Text('Подключить'))]));
    controller.dispose(); if(token==null||token.isEmpty)return;
    setState(()=>_loading=true);
    try { await _api.connectBank(bank, token); if(mounted) { ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Банк подключён'))); await _load(); } }
    catch(_){ if(mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Не удалось подключить банк'))); }
    finally { if(mounted)setState(()=>_loading=false); }
  }
  @override Widget build(BuildContext context){
    final names={'tinkoff':'Тинькофф','sber':'СберБанк','vtb':'ВТБ','raiff':'Райффайзен','alfa':'Альфа-Банк'};
    return Scaffold(appBar:AppBar(title:const Text('Банковские подключения')),body:_loading?const LoadingWidget():RefreshIndicator(onRefresh:_load,child:ListView(padding:const EdgeInsets.all(16),children:[
      for(final entry in names.entries) _bankCard(entry.key,entry.value),
      const SizedBox(height:12),
      const Text('Статус и доступность берутся с сервера. Недоступные интеграции не предлагаются как активные.'),
    ])));
  }
  Widget _bankCard(String key,String name){
    final data=Map<String,dynamic>.from(_status[key] is Map?_status[key]:{});
    final status=data['status']?.toString()??'unknown'; final connected=data['connected']==true; final available=status=='available'||connected;
    return Card(child:ListTile(leading:const Icon(Icons.account_balance),title:Text(name),subtitle:Text(connected?'Подключён':status=='available'?'Доступно подключение':status=='coming_soon'?'Скоро будет доступно':'Интеграция недоступна'),trailing: connected?const Icon(Icons.check_circle):available?FilledButton.tonal(onPressed:()=>_connect(key),child:const Text('Подключить')):const Icon(Icons.lock_outline)));
  }
}
