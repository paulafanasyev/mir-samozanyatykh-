import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:logger/logger.dart';
import 'package:hive/hive.dart';

import '../../core/constants/app_constants.dart';

final logger = Logger();

class ApiClient {
  late final Dio _dio;
  final Box _authBox;

  ApiClient(this._authBox) {
    _dio = Dio(BaseOptions(
      baseUrl: kDebugMode ? AppConstants.devBaseUrl : AppConstants.baseUrl,
      connectTimeout: const Duration(milliseconds: AppConstants.apiTimeout),
      receiveTimeout: const Duration(milliseconds: AppConstants.apiTimeout),
      sendTimeout: const Duration(milliseconds: AppConstants.apiTimeout),
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-Client-Version': AppConstants.appVersion,
        'X-Platform': 'flutter',
      },
      validateStatus: (status) => status != null && status < 500,
    ));

    _setupInterceptors();
  }

  void _setupInterceptors() {
    // Request interceptor - add auth token
    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        final token = _authBox.get(AppConstants.tokenKey);
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        logger.d('→ ${options.method} ${options.path}');
        return handler.next(options);
      },
      onResponse: (response, handler) {
        logger.d('← ${response.statusCode} ${response.requestOptions.path}');
        return handler.next(response);
      },
      onError: (error, handler) async {
        logger.e('✗ ${error.response?.statusCode} ${error.requestOptions.path}: ${error.message}');

        // Handle 401 - try refresh token
        if (error.response?.statusCode == 401) {
          final refreshed = await _refreshToken();
          if (refreshed) {
            final token = _authBox.get(AppConstants.tokenKey);
            error.requestOptions.headers['Authorization'] = 'Bearer $token';
            return handler.resolve(await _dio.fetch(error.requestOptions));
          }
        }

        return handler.next(error);
      },
    ));

    // Retry interceptor
    _dio.interceptors.add(
      InterceptorsWrapper(
        onError: (error, handler) async {
          if (error.requestOptions.extra['retry_count'] == null) {
            error.requestOptions.extra['retry_count'] = 0;
          }
          final retryCount = error.requestOptions.extra['retry_count'] as int;

          if (retryCount < AppConstants.apiMaxRetries &&
              (error.type == DioExceptionType.connectionTimeout ||
               error.type == DioExceptionType.receiveTimeout ||
               error.type == DioExceptionType.connectionError)) {
            error.requestOptions.extra['retry_count'] = retryCount + 1;
            await Future.delayed(Duration(seconds: retryCount + 1));
            return handler.resolve(await _dio.fetch(error.requestOptions));
          }
          return handler.next(error);
        },
      ),
    );

    // Logging interceptor in debug
    if (kDebugMode) {
      _dio.interceptors.add(LogInterceptor(
        requestBody: true,
        responseBody: true,
        logPrint: (o) => logger.d(o.toString()),
      ));
    }
  }

  Future<bool> _refreshToken() async {
    try {
      final refreshToken = _authBox.get(AppConstants.refreshTokenKey);
      if (refreshToken == null) return false;

      final response = await _dio.post(
        '/api/auth/refresh',
        data: {'refresh_token': refreshToken},
        options: Options(skipAuth: true),
      );

      if (response.statusCode == 200) {
        await _authBox.put(AppConstants.tokenKey, response.data['access_token']);
        await _authBox.put(AppConstants.refreshTokenKey, response.data['refresh_token']);
        return true;
      }
    } catch (e) {
      logger.e('Token refresh failed: $e');
    }
    return false;
  }

  Dio get dio => _dio;

  // Auth
  Future<Response> login(String email, String password) =>
      _dio.post('/api/auth/login', data: {'email': email, 'password': password});

  Future<Response> register(String name, String email, String password, {String? referralCode}) =>
      _dio.post('/api/auth/register', data: {
        'name': name,
        'email': email,
        'password': password,
        if (referralCode != null) 'referral_code': referralCode,
      });

  Future<Response> logout() => _dio.post('/api/auth/logout');

  Future<Response> getCurrentUser() => _dio.get('/api/users/me');

  // Clients
  Future<Response> getClients({int page = 1, String? search}) =>
      _dio.get('/api/crm/clients', queryParameters: {'page': page, 'search': search});

  Future<Response> getClient(int id) => _dio.get('/api/crm/clients/$id');

  Future<Response> createClient(Map<String, dynamic> data) =>
      _dio.post('/api/crm/clients', data: data);

  Future<Response> updateClient(int id, Map<String, dynamic> data) =>
      _dio.put('/api/crm/clients/$id', data: data);

  Future<Response> deleteClient(int id) => _dio.delete('/api/crm/clients/$id');

  // Deals
  Future<Response> getDeals({int page = 1, String? status}) =>
      _dio.get('/api/crm/deals', queryParameters: {'page': page, 'status': status});

  Future<Response> getDeal(int id) => _dio.get('/api/crm/deals/$id');

  Future<Response> createDeal(Map<String, dynamic> data) =>
      _dio.post('/api/crm/deals', data: data);

  Future<Response> updateDeal(int id, Map<String, dynamic> data) =>
      _dio.put('/api/crm/deals/$id', data: data);

  Future<Response> moveDeal(int id, String stage) =>
      _dio.patch('/api/crm/deals/$id/move', data: {'stage': stage});

  // Invoices
  Future<Response> getInvoices({int page = 1, String? status}) =>
      _dio.get('/api/sales/invoices', queryParameters: {'page': page, 'status': status});

  Future<Response> getInvoice(int id) => _dio.get('/api/sales/invoices/$id');

  Future<Response> createInvoice(Map<String, dynamic> data) =>
      _dio.post('/api/sales/invoices', data: data);

  Future<Response> getInvoicePdf(int id) =>
      _dio.get('/api/sales/invoices/$id/pdf', options: Options(responseType: ResponseType.bytes));

  // Tasks
  Future<Response> getTasks({int page = 1, String? status, String? priority}) =>
      _dio.get('/api/tasks', queryParameters: {'page': page, 'status': status, 'priority': priority});

  Future<Response> getTask(int id) => _dio.get('/api/tasks/$id');

  Future<Response> createTask(Map<String, dynamic> data) =>
      _dio.post('/api/tasks', data: data);

  Future<Response> updateTask(int id, Map<String, dynamic> data) =>
      _dio.put('/api/tasks/$id', data: data);

  Future<Response> deleteTask(int id) => _dio.delete('/api/tasks/$id');

  // Calendar
  Future<Response> getEvents({required DateTime start, required DateTime end}) =>
      _dio.get('/api/calendar/events', queryParameters: {
        'start': start.toIso8601String(),
        'end': end.toIso8601String(),
      });

  Future<Response> createEvent(Map<String, dynamic> data) =>
      _dio.post('/api/calendar/events', data: data);

  // Accounting
  Future<Response> getTransactions({int page = 1, String? category}) =>
      _dio.get('/api/accounting/transactions', queryParameters: {'page': page, 'category': category});

  Future<Response> getTaxReports() => _dio.get('/api/accounting/tax-reports');

  Future<Response> getTaxDeductions() => _dio.get('/api/accounting/deductions');

  Future<Response> createTransaction(Map<String, dynamic> data) =>
      _dio.post('/api/accounting/transactions', data: data);

  // Svetlana (AI)
  Future<Response> sendMessage(String message, {String? context}) =>
      _dio.post('/api/svetlana/chat', data: {
        'message': message,
        if (context != null) 'context': context,
      });

  Future<Response> getSvetlanaHistory() => _dio.get('/api/svetlana/history');

  // Notifications
  Future<Response> getNotifications({int page = 1}) =>
      _dio.get('/api/notifications', queryParameters: {'page': page});

  Future<Response> markNotificationRead(int id) =>
      _dio.patch('/api/notifications/$id/read');

  Future<Response> getUnreadCount() => _dio.get('/api/notifications/unread-count');

  // Referrals
  Future<Response> getReferralStats() => _dio.get('/api/referrals/stats');

  Future<Response> getReferralCode() => _dio.get('/api/referrals/code');

  // Bank
  Future<Response> getBankConnections() => _dio.get('/api/bank/connections');

  Future<Response> connectBank(String bankName, String token) =>
      _dio.post('/api/bank/connect', data: {'bank_name': bankName, 'token': token});

  Future<Response> getBankTransactions({int page = 1}) =>
      _dio.get('/api/bank/transactions', queryParameters: {'page': page});

  // Receipt check
  Future<Response> checkReceipt(String qrData) =>
      _dio.post('/api/fns/receipt-check', data: {'qr_data': qrData});

  // Admin
  Future<Response> getAdminStats() => _dio.get('/api/admin/stats');

  Future<Response> getAdminUsers({int page = 1, String? search}) =>
      _dio.get('/api/admin/users', queryParameters: {'page': page, 'search': search});

  // Analytics
  Future<Response> getDashboardStats() => _dio.get('/api/analytics/dashboard');

  Future<Response> getRevenueAnalytics({required DateTime start, required DateTime end}) =>
      _dio.get('/api/analytics/revenue', queryParameters: {
        'start': start.toIso8601String(),
        'end': end.toIso8601String(),
      });

  // Export
  Future<Response> exportData(String type, String format) =>
      _dio.get('/api/export/$type', queryParameters: {'format': format},
          options: Options(responseType: ResponseType.bytes));

  // Webhooks
  Future<Response> getWebhooks() => _dio.get('/api/webhooks');

  Future<Response> createWebhook(Map<String, dynamic> data) =>
      _dio.post('/api/webhooks', data: data);

  // API Keys
  Future<Response> getApiKeys() => _dio.get('/api/api-keys');

  Future<Response> createApiKey(Map<String, dynamic> data) =>
      _dio.post('/api/api-keys', data: data);

  Future<Response> revokeApiKey(String id) => _dio.delete('/api/api-keys/$id');
}

// Extension for skipping auth on specific requests
extension OptionsExtension on Options {
  bool get skipAuth => extra?['skip_auth'] == true;
  set skipAuth(bool value) => extra = {...?extra, 'skip_auth': value};
}
