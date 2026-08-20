import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:hive_flutter/hive_flutter.dart';

import '../../data/datasources/remote/api_client.dart';

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

  Future<void> queueAction(
    String endpoint,
    Map<String, dynamic> data, {
    String method = 'POST',
  }) async {
    if (!_isInitialized) await initialize();
    await _syncBox.add({
      'endpoint': endpoint,
      'data': data,
      'method': method.toUpperCase(),
      'timestamp': DateTime.now().toIso8601String(),
      'retryCount': 0,
    });
  }

  Future<void> syncPending() async {
    if (!_isInitialized) await initialize();

    final connectivity = await Connectivity().checkConnectivity();
    if (connectivity.contains(ConnectivityResult.none)) return;

    final api = ApiClient();
    final keys = _syncBox.keys.toList(growable: false);

    for (final key in keys) {
      final raw = _syncBox.get(key);
      if (raw is! Map) continue;

      final endpoint = raw['endpoint']?.toString();
      if (endpoint == null || endpoint.isEmpty) continue;

      final method = (raw['method']?.toString() ?? 'POST').toUpperCase();
      final data = raw['data'] is Map
          ? Map<String, dynamic>.from(raw['data'] as Map)
          : <String, dynamic>{};

      try {
        await api.dio.request<dynamic>(
          endpoint,
          data: method == 'GET' || method == 'DELETE' ? null : data,
          queryParameters: method == 'GET' ? data : null,
          options: Options(method: method),
        );
        await _syncBox.delete(key);
      } catch (_) {
        final retryCount = (raw['retryCount'] is num)
            ? (raw['retryCount'] as num).toInt()
            : 0;
        await _syncBox.put(key, {
          ...Map<String, dynamic>.from(raw),
          'retryCount': retryCount + 1,
        });
      }
    }
  }

  Future<bool> isOnline() async {
    final connectivity = await Connectivity().checkConnectivity();
    return !connectivity.contains(ConnectivityResult.none);
  }
}
