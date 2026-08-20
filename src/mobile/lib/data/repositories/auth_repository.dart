import 'dart:convert';

import '../../core/services/biometric_auth_service.dart';
import '../../core/services/secure_storage_service.dart';
import '../datasources/remote/api_client.dart';
import '../models/user_model.dart';

class TwoFactorRequiredException implements Exception {
  final String tempToken;
  const TwoFactorRequiredException(this.tempToken);
  @override
  String toString() => 'Требуется подтверждение 2FA';
}

class AuthRepository {
  final ApiClient _api;
  final BiometricAuthService _biometric;

  AuthRepository({ApiClient? api, BiometricAuthService? biometric})
      : _api = api ?? ApiClient(),
        _biometric = biometric ?? BiometricAuthService();

  Future<bool> isAuthenticated() async => (await SecureStorageService.getToken())?.isNotEmpty == true;

  Future<UserModel?> getCurrentUser() async {
    final cached = await SecureStorageService.getUserData();
    if (cached != null && cached.isNotEmpty) {
      try {
        return UserModel.fromJson(Map<String, dynamic>.from(jsonDecode(cached) as Map));
      } catch (_) {}
    }
    try {
      final response = await _api.getCurrentUser();
      if (response.data is! Map) return null;
      final user = UserModel.fromJson(Map<String, dynamic>.from(response.data as Map));
      await SecureStorageService.saveUserData(jsonEncode(user.toJson()));
      return user;
    } catch (_) {
      return null;
    }
  }

  Future<UserModel> login(String email, String password) async {
    final response = await _api.login(email, password);
    final data = response.data is Map ? Map<String, dynamic>.from(response.data as Map) : <String, dynamic>{};
    final temp = data['temp_token'] ?? data['two_factor_token'];
    if (data['requires_2fa'] == true && temp != null) {
      throw TwoFactorRequiredException(temp.toString());
    }
    return _storeAuthenticatedResponse(data);
  }

  Future<UserModel> login2fa(String tempToken, String code) async {
    final response = await _api.login2fa(tempToken, code);
    final data = response.data is Map ? Map<String, dynamic>.from(response.data as Map) : <String, dynamic>{};
    return _storeAuthenticatedResponse(data);
  }

  Future<void> register(String name, String email, String password, {String? referralCode}) async {
    await _api.register({
      'name': name,
      'email': email,
      'password': password,
      if (referralCode != null && referralCode.isNotEmpty) 'referral_code': referralCode,
    });
  }

  Future<void> logout() async {
    try {
      await _api.logout();
    } finally {
      await SecureStorageService.clearAll();
    }
  }

  Future<bool> isBiometricAvailable() => _biometric.isAvailable();
  Future<bool> isBiometricEnabled() => SecureStorageService.isBiometricEnabled();

  Future<void> enableBiometric() async {
    await SecureStorageService.setBiometricEnabled(true);
  }

  Future<bool> authenticateWithBiometric() => _biometric.authenticate();

  Future<UserModel> _storeAuthenticatedResponse(Map<String, dynamic> data) async {
    final token = data['access_token'] ?? data['token'];
    final refresh = data['refresh_token'];
    if (token != null) await SecureStorageService.saveToken(token.toString());
    if (refresh != null) await SecureStorageService.saveRefreshToken(refresh.toString());

    final rawUser = data['user'] is Map ? Map<String, dynamic>.from(data['user'] as Map) : data;
    final user = UserModel.fromJson(rawUser);
    await SecureStorageService.saveUserData(jsonEncode(user.toJson()));
    return user;
  }
}
