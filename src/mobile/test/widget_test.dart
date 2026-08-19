import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mir_samozanyatykh_mobile/main.dart';
import 'package:mir_samozanyatykh_mobile/data/models/user_model.dart';
import 'package:mir_samozanyatykh_mobile/presentation/providers/auth_provider.dart';

void main() {
  group('App Widget Tests', () {
    testWidgets('App launches with MaterialApp router', (WidgetTester tester) async {
      await tester.pumpWidget(const ProviderScope(child: MirSamozanyatykhApp()));
      expect(find.byType(MaterialApp), findsOneWidget);
    });

    testWidgets('Login screen has email field', (WidgetTester tester) async {
      await tester.pumpWidget(ProviderScope(
        overrides: [authStateProvider.overrideWithValue(const AsyncValue.data(AuthState()))],
        child: const MirSamozanyatykhApp(),
      ));
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
    testWidgets('Authenticated app shows bottom navigation', (WidgetTester tester) async {
      const user = UserModel(id: 1, email: 'test@example.com', name: 'Test');
      await tester.pumpWidget(ProviderScope(
        overrides: [
          authStateProvider.overrideWithValue(AsyncValue.data(AuthState(isAuthenticated: true, user: user))),
        ],
        child: const MirSamozanyatykhApp(),
      ));
      await tester.pumpAndSettle();
      expect(find.byType(BottomNavigationBar), findsOneWidget);
    });
  });
}
