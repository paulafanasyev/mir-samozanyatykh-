import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:mir_samozanyatykh_mobile/main.dart';

void main() {
  testWidgets('App launches', (WidgetTester tester) async {
    await tester.pumpWidget(const ProviderScope(child: MirSamozanyatykhApp()));
    expect(find.byType(MaterialApp), findsOneWidget);
  });

  testWidgets('Basic Material UI renders', (WidgetTester tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(body: Center(child: Text('Мир Самозанятых'))),
      ),
    );
    expect(find.text('Мир Самозанятых'), findsOneWidget);
  });

  testWidgets('Loading indicator renders', (WidgetTester tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(body: Center(child: CircularProgressIndicator())),
      ),
    );
    expect(find.byType(CircularProgressIndicator), findsOneWidget);
  });
}
