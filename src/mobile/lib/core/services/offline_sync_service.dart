import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:hive_flutter/hive_flutter.dart';

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
    if (!_isInitialized) await initialize();
    await _syncBox.add({
      'endpoint': endpoint,
      'data': data,
      'timestamp': DateTime.now().toIso8601String(),
      'retryCount': 0,
    });
  }

  Future<void> syncPending() async {
    if (!_isInitialized) await initialize();

    final connectivity = await Connectivity().checkConnectivity();
    if (connectivity.contains(ConnectivityResult.none)) return;

    // Keep the queued records until the actual network operation succeeds.
    // The previous implementation deleted every record without sending it.
    // This service only owns the queue; callers are responsible for executing
    // the request and deleting the corresponding key after success.
  }

  Future<bool> isOnline() async {
    final connectivity = await Connectivity().checkConnectivity();
    return !connectivity.contains(ConnectivityResult.none);
  }
}
