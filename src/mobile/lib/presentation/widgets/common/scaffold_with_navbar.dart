import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../providers/auth_provider.dart';
import '../../../core/theme/app_theme.dart';

class ScaffoldWithNavbar extends ConsumerStatefulWidget {
  final Widget child;

  const ScaffoldWithNavbar({super.key, required this.child});

  @override
  ConsumerState<ScaffoldWithNavbar> createState() => _ScaffoldWithNavbarState();
}

class _ScaffoldWithNavbarState extends ConsumerState<ScaffoldWithNavbar> {
  int _getCurrentIndex(BuildContext context) {
    final location = GoRouterState.of(context).matchedLocation;
    switch (location) {
      case '/':
        return 0;
      case '/clients':
        return 1;
      case '/deals':
        return 2;
      case '/invoices':
        return 3;
      case '/tasks':
        return 4;
      case '/calendar':
        return 5;
      case '/accounting':
        return 6;
      case '/svetlana':
        return 7;
      case '/profile':
        return 8;
      default:
        return 0;
    }
  }

  void _onItemTapped(int index, BuildContext context) {
    switch (index) {
      case 0:
        context.go('/');
        break;
      case 1:
        context.go('/clients');
        break;
      case 2:
        context.go('/deals');
        break;
      case 3:
        context.go('/invoices');
        break;
      case 4:
        context.go('/tasks');
        break;
      case 5:
        context.go('/calendar');
        break;
      case 6:
        context.go('/accounting');
        break;
      case 7:
        context.go('/svetlana');
        break;
      case 8:
        context.go('/profile');
        break;
    }
  }

  @override
  Widget build(BuildContext context) {
    final currentIndex = _getCurrentIndex(context);
    final authState = ref.watch(authStateProvider);
    final isAdmin = authState.value?.user?.isAdmin ?? false;

    return Scaffold(
      body: widget.child,
      bottomNavigationBar: NavigationBar(
        selectedIndex: currentIndex,
        onDestinationSelected: (index) => _onItemTapped(index, context),
        destinations: [
          const NavigationDestination(
            icon: Icon(Icons.home_outlined),
            selectedIcon: Icon(Icons.home),
            label: 'Главная',
          ),
          const NavigationDestination(
            icon: Icon(Icons.people_outline),
            selectedIcon: Icon(Icons.people),
            label: 'Клиенты',
          ),
          const NavigationDestination(
            icon: Icon(Icons.trending_up_outlined),
            selectedIcon: Icon(Icons.trending_up),
            label: 'Сделки',
          ),
          const NavigationDestination(
            icon: Icon(Icons.receipt_outlined),
            selectedIcon: Icon(Icons.receipt),
            label: 'Счета',
          ),
          const NavigationDestination(
            icon: Icon(Icons.task_outlined),
            selectedIcon: Icon(Icons.task),
            label: 'Задачи',
          ),
          const NavigationDestination(
            icon: Icon(Icons.calendar_today_outlined),
            selectedIcon: Icon(Icons.calendar_today),
            label: 'Календарь',
          ),
          const NavigationDestination(
            icon: Icon(Icons.account_balance_wallet_outlined),
            selectedIcon: Icon(Icons.account_balance_wallet),
            label: 'Финансы',
          ),
          const NavigationDestination(
            icon: Icon(Icons.smart_toy_outlined),
            selectedIcon: Icon(Icons.smart_toy),
            label: 'Светлана',
          ),
          NavigationDestination(
            icon: Badge(
              isLabelVisible: false,
              child: Icon(isAdmin ? Icons.admin_panel_settings_outlined : Icons.person_outline),
            ),
            selectedIcon: Icon(isAdmin ? Icons.admin_panel_settings : Icons.person),
            label: isAdmin ? 'Админ' : 'Профиль',
          ),
        ],
      ),
    );
  }
}
