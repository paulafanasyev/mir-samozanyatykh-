import 'package:flutter/material.dart';
import 'screens/login_screen.dart';
import 'screens/dashboard_screen.dart';
import 'screens/contracts_screen.dart';
import 'screens/finance_screen.dart';
import 'screens/calculator_screen.dart';
import 'screens/crm_screen.dart';
import 'screens/marketplace_screen.dart';
import 'screens/grants_screen.dart';
import 'screens/profile_screen.dart';
import 'screens/svetlana_screen.dart';
import 'services/auth_service.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const MirApp());
}

class MirApp extends StatelessWidget {
  const MirApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'МИР Самозанятых',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFFF5A623),
          brightness: Brightness.dark,
        ),
        fontFamily: 'Inter',
        scaffoldBackgroundColor: const Color(0xFF0F0F0F),
        cardTheme: CardTheme(
          color: const Color(0xFF1A1A1A),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        ),
        appBarTheme: const AppBarTheme(
          backgroundColor: Color(0xFF0F0F0F),
          elevation: 0,
          centerTitle: true,
        ),
      ),
      home: const AuthWrapper(),
      routes: {
        '/login': (ctx) => const LoginScreen(),
        '/dashboard': (ctx) => const DashboardScreen(),
        '/contracts': (ctx) => const ContractsScreen(),
        '/finance': (ctx) => const FinanceScreen(),
        '/calculator': (ctx) => const CalculatorScreen(),
        '/crm': (ctx) => const CrmScreen(),
        '/marketplace': (ctx) => const MarketplaceScreen(),
        '/grants': (ctx) => const GrantsScreen(),
        '/profile': (ctx) => const ProfileScreen(),
        '/svetlana': (ctx) => const SvetlanaScreen(),
      },
    );
  }
}

class AuthWrapper extends StatefulWidget {
  const AuthWrapper({super.key});

  @override
  State<AuthWrapper> createState() => _AuthWrapperState();
}

class _AuthWrapperState extends State<AuthWrapper> {
  bool _loading = true;
  bool _authenticated = false;

  @override
  void initState() {
    super.initState();
    _checkAuth();
  }

  Future<void> _checkAuth() async {
    final token = await AuthService.getToken();
    setState(() {
      _authenticated = token != null;
      _loading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator(color: Color(0xFFF5A623))),
      );
    }
    return _authenticated ? const DashboardScreen() : const LoginScreen();
  }
}
