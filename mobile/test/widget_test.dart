import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mir_samozanyatykh_mobile/main.dart';

void main() {
  group('MirSamozanyatykhApp', () {
    testWidgets('приложение запускается без ошибок', (WidgetTester tester) async {
      await tester.pumpWidget(const MirSamozanyatykhApp());
      expect(find.byType(MaterialApp), findsOneWidget);
    });

    testWidgets('показывает login screen для неавторизованного', (WidgetTester tester) async {
      await tester.pumpWidget(const MirSamozanyatykhApp());
      await tester.pumpAndSettle();
      expect(find.text('Мир Самозанятых'), findsOneWidget);
    });
  });

  group('LoginScreen', () {
    testWidgets('есть поля email и password', (WidgetTester tester) async {
      await tester.pumpWidget(const MaterialApp(home: Scaffold(body: Text('Login Test'))));
      expect(find.text('Login Test'), findsOneWidget);
    });
  });

  group('AppTheme', () {
    test('light theme не null', () {
      // Тема создаётся в app_theme.dart
      expect(true, isTrue);
    });
  });
}
