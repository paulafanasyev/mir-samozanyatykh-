import 'package:flutter/material.dart';

class BrandHeader extends StatelessWidget {
  const BrandHeader({super.key, this.showSvetlana = true});
  final bool showSvetlana;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Row(
      children: [
        Image.asset('assets/images/logo-mir-samozanyatykh.png', width: 42, height: 42, fit: BoxFit.contain),
        const SizedBox(width: 10),
        const Expanded(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('Мир Самозанятых', style: TextStyle(fontSize: 17, fontWeight: FontWeight.w800)),
            Text('рабочее пространство', style: TextStyle(fontSize: 10, color: Colors.grey)),
          ]),
        ),
        if (showSvetlana)
          Container(
            width: 38, height: 38,
            decoration: BoxDecoration(color: scheme.surface, borderRadius: BorderRadius.circular(12), border: Border.all(color: scheme.outlineVariant)),
            clipBehavior: Clip.antiAlias,
            child: Image.asset('assets/images/svetlana-face.png', fit: BoxFit.cover),
          ),
      ],
    );
  }
}
