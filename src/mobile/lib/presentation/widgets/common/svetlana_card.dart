import 'package:flutter/material.dart';

class SvetlanaCard extends StatelessWidget {
  const SvetlanaCard({super.key, this.onTap});
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      borderRadius: BorderRadius.circular(22),
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          gradient: const LinearGradient(colors: [Color(0xFFFFF7ED), Color(0xFFFFFBEB)]),
          borderRadius: BorderRadius.circular(22),
          border: Border.all(color: const Color(0xFFFED7AA)),
        ),
        child: Row(children: [
          Container(width: 54, height: 54, clipBehavior: Clip.antiAlias, decoration: BoxDecoration(color: const Color(0xFF171A22), borderRadius: BorderRadius.circular(16)), child: Image.asset('assets/images/svetlana-face.png', fit: BoxFit.cover)),
          const SizedBox(width: 12),
          const Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('Светлана', style: TextStyle(fontWeight: FontWeight.w800)),
            SizedBox(height: 2),
            Text('Ваш ИИ-ассистент · онлайн', style: TextStyle(fontSize: 12, color: Color(0xFF64748B))),
            SizedBox(height: 5),
            Text('Спросите о чеках, клиентах или документах', style: TextStyle(fontSize: 12)),
          ])),
          const Icon(Icons.arrow_forward_ios_rounded, size: 16, color: Color(0xFFF97316)),
        ]),
      ),
    );
  }
}
