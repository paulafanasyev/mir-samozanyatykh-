import 'package:hive_flutter/hive_flutter.dart';
import 'package:connectivity_plus/connectivity_plus.dart';

class OfflineSyncService {
  static final OfflineSyncService _instance = OfflineSyncService._internal();
  factory OfflineSyncService() => _instance;
  OfflineSyncService._internal();

  late Box _syncBox;
  bool _isInitialized = false;

  Future<void> initialize() async {
    if (_isInitialized) return;
    await Hive.initFlutter();
    _syncBox = await Hive.openBox('offline_sync');
    _isInitialized = true;
  }

  Future<void> queueAction(String endpoint, Map<String, dynamic> data) async {
    final action = {
      'endpoint': endpoint,
      'data': data,
      'timestamp': DateTime.now().toIso8601String(),
      'retryCount': 0,
    };
    await _syncBox.add(action);
  }

  Future<void> syncPending() async {
    final connectivity = await Connectivity().checkConnectivity();
    if (connectivity == ConnectivityResult.none) return;

    final pending = _syncBox.values.toList();
    for (var action in pending) {
      try {
        await _syncBox.deleteAt(pending.indexOf(action));
      } catch (e) {
        // Retry later
      }
    }
  }

  Future<bool> isOnline() async {
    final connectivity = await Connectivity().checkConnectivity();
    return connectivity != ConnectivityResult.none;
  }
}
