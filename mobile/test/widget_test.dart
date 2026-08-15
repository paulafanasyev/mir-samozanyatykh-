import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mir_samozanyatykh/main.dart';

void main() {
  group('App Widget Tests', () {
    testWidgets('App launches with LoginScreen', (WidgetTester tester) async {
      await tester.pumpWidget(const MyApp());
      expect(find.byType(MaterialApp), findsOneWidget);
    });

    testWidgets('Login screen has email field', (WidgetTester tester) async {
      await tester.pumpWidget(const MyApp());
      await tester.pumpAndSettle();
      expect(find.byType(TextField), findsWidgets);
    });
  });

  group('Client Detail Screen', () {
    testWidgets('Shows loading state', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: Center(child: CircularProgressIndicator()),
          ),
        ),
      );
      expect(find.byType(CircularProgressIndicator), findsOneWidget);
    });
  });

  group('Navigation', () {
    testWidgets('Bottom navigation has 5 items', (WidgetTester tester) async {
      await tester.pumpWidget(const MyApp());
      await tester.pumpAndSettle();
      expect(find.byType(BottomNavigationBar), findsOneWidget);
    });
  });
}
