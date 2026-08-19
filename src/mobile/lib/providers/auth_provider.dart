import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Whether the current session is authenticated.
final authProvider = StateProvider<bool>((ref) => false);

/// Current user payload. Keep this nullable until authentication succeeds.
final userProvider = StateProvider<Map<String, dynamic>?>((ref) => null);

/// Number of unread notifications/messages shown in the app shell.
final unreadCountProvider = StateProvider<int>((ref) => 0);
