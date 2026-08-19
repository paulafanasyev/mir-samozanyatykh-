import 'package:flutter/material.dart';
import '../../../data/datasources/remote/api_client.dart';

class ReceiptCheckScreen extends StatefulWidget { const ReceiptCheckScreen({super.key}); @override State<ReceiptCheckScreen> createState()=>_ReceiptCheckScreenState(); }
class _ReceiptCheckScreenState extends State<ReceiptCheckScreen>{
 final _controller=TextEditingController(); bool _loading=false; String? _result;
 Future<void> _check() async { final raw=_controller.text.trim(); if(raw.isEmpty){ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Введите данные чека')));return;} setState(()=>_loading=true); try { final response=await ApiClient().checkReceipt({'qr_code':raw}); setState(()=>_result=response.data.toString()); } catch(e){setState(()=>_result='Ошибка проверки: $e');} finally{if(mounted)setState(()=>_loading=false);}}
 @override void dispose(){_controller.dispose();super.dispose();}
 @override Widget build(BuildContext context)=>Scaffold(appBar:AppBar(title:const Text('Проверка чека ФНС')),body:Padding(padding:const EdgeInsets.all(16),child:Column(crossAxisAlignment:CrossAxisAlignment.stretch,children:[TextField(controller:_controller,decoration:const InputDecoration(labelText:'QR-код чека или данные',hintText:'t=20260101T0000&s=100.00&fn=...',prefixIcon:Icon(Icons.qr_code)),maxLines:3),const SizedBox(height:16),FilledButton.icon(onPressed:_loading?null:()=>ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Для сканирования используйте ввод QR-строки из приложения камеры.'))),icon:const Icon(Icons.qr_code_scanner),label:const Text('Сканировать QR-код')),const SizedBox(height:16),FilledButton(onPressed:_loading?null:_check,child:_loading?const CircularProgressIndicator():const Text('Проверить чек')),if(_result!=null) ...[const SizedBox(height:16),Expanded(child:SingleChildScrollView(child:Text(_result!)))]])));
}
