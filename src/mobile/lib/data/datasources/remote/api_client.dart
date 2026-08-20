import 'package:dio/dio.dart';

import '../../../core/constants/app_constants.dart';
import '../../../core/services/secure_storage_service.dart';

class ApiResponse {
  final dynamic data;
  final int? statusCode;
  const ApiResponse(this.data, {this.statusCode});
}

class ApiClient {
  ApiClient._internal() {
    dio = Dio(BaseOptions(
      baseUrl: AppConstants.apiBaseUrl,
      connectTimeout: const Duration(milliseconds: AppConstants.apiTimeout),
      receiveTimeout: const Duration(milliseconds: AppConstants.apiTimeout),
      sendTimeout: const Duration(milliseconds: AppConstants.apiTimeout),
      headers: {'Accept': 'application/json', 'Content-Type': 'application/json'},
    ));
    dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        final token = await SecureStorageService.getToken();
        if (token != null && token.isNotEmpty) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        handler.next(options);
      },
    ));
  }

  static final ApiClient _instance = ApiClient._internal();
  factory ApiClient() => _instance;

  late final Dio dio;

  Future<ApiResponse> _request(Future<Response<dynamic>> Function() request) async {
    final response = await request();
    return ApiResponse(response.data, statusCode: response.statusCode);
  }

  Future<ApiResponse> getDashboardStats() => _request(() => dio.get('/api/dashboard/stats'));
  Future<ApiResponse> getTransactions({int page = 1}) => _request(() => dio.get('/api/transactions', queryParameters: {'page': page}));
  Future<ApiResponse> getTaxDeductions() => _request(() => dio.get('/api/tax/deductions'));
  Future<ApiResponse> getTaxReports() => _request(() => dio.get('/api/tax/reports'));
  Future<ApiResponse> getRevenueAnalytics({int months = 6}) => _request(() => dio.get('/api/analytics/revenue', queryParameters: {'months': months}));

  Future<ApiResponse> getClients() => _request(() => dio.get('/api/clients'));
  Future<ApiResponse> getClient(int id) => _request(() => dio.get('/api/clients/$id'));
  Future<ApiResponse> createClient(Map<String, dynamic> data) => _request(() => dio.post('/api/clients', data: data));
  Future<ApiResponse> deleteClient(int id) => _request(() => dio.delete('/api/clients/$id'));

  Future<ApiResponse> getDeals() => _request(() => dio.get('/api/deals'));
  Future<ApiResponse> getDeal(int id) => _request(() => dio.get('/api/deals/$id'));
  Future<ApiResponse> createDeal(Map<String, dynamic> data) => _request(() => dio.post('/api/deals', data: data));

  Future<ApiResponse> getInvoices() => _request(() => dio.get('/api/invoices'));
  Future<ApiResponse> getInvoice(int id) => _request(() => dio.get('/api/invoices/$id'));
  Future<ApiResponse> createInvoice(Map<String, dynamic> data) => _request(() => dio.post('/api/invoices', data: data));

  Future<ApiResponse> getContracts() => _request(() => dio.get('/api/contracts'));

  Future<ApiResponse> getTasks() => _request(() => dio.get('/api/tasks'));
  Future<ApiResponse> getTask(int id) => _request(() => dio.get('/api/tasks/$id'));
  Future<ApiResponse> createTask(Map<String, dynamic> data) => _request(() => dio.post('/api/tasks', data: data));
  Future<ApiResponse> updateTask(int id, Map<String, dynamic> data) => _request(() => dio.patch('/api/tasks/$id', data: data));

  Future<ApiResponse> getEvents({required DateTime start, required DateTime end}) => _request(() => dio.get('/api/calendar/events', queryParameters: {'start': start.toIso8601String(), 'end': end.toIso8601String()}));
  Future<ApiResponse> createCalendarEvent(Map<String, dynamic> data) => _request(() => dio.post('/api/calendar/events', data: data));

  Future<ApiResponse> getBankStatus() => _request(() => dio.get('/api/banks/status'));
  Future<ApiResponse> connectBank(String bank, String token) => _request(() => dio.post('/api/banks/$bank/connect', data: {'token': token}));

  Future<ApiResponse> getNotifications() => _request(() => dio.get('/api/notifications'));
  Future<ApiResponse> markNotificationRead(int id) => _request(() => dio.post('/api/notifications/$id/read'));
  Future<ApiResponse> markAllNotificationsRead() => _request(() => dio.post('/api/notifications/read-all'));

  Future<ApiResponse> getReferralStats() => _request(() => dio.get('/api/referrals/stats'));
  Future<ApiResponse> getReferralCode() => _request(() => dio.get('/api/referrals/code'));

  Future<ApiResponse> getApiKeys() => _request(() => dio.get('/api/integrations/api-keys'));
  Future<ApiResponse> createApiKey(Map<String, dynamic> data) => _request(() => dio.post('/api/integrations/api-keys', data: data));
  Future<ApiResponse> revokeApiKey(String id) => _request(() => dio.delete('/api/integrations/api-keys/$id'));
  Future<ApiResponse> getWebhooks() => _request(() => dio.get('/api/integrations/webhooks'));

  Future<ApiResponse> checkReceipt(Map<String, dynamic> data) => _request(() => dio.post('/api/receipts/check', data: data));
  Future<ApiResponse> sendMessage(String text) => _request(() => dio.post('/api/svetlana/chat', data: {'message': text}));
  Future<ApiResponse> getCurrentUser() => _request(() => dio.get('/api/users/me'));

  Future<ApiResponse> login(String email, String password) => _request(() => dio.post('/api/auth/login', data: {'email': email, 'password': password}));
  Future<ApiResponse> login2fa(String tempToken, String code) => _request(() => dio.post('/api/auth/2fa', data: {'temp_token': tempToken, 'code': code}));
  Future<ApiResponse> register(Map<String, dynamic> data) => _request(() => dio.post('/api/auth/register', data: data));
  Future<ApiResponse> logout() => _request(() => dio.post('/api/auth/logout'));
}
