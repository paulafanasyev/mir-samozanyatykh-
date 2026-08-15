import 'package:hive/hive.dart';
import 'package:local_auth/local_auth.dart';
import 'package:local_auth_android/local_auth_android.dart';
import 'package:local_auth_ios/local_auth_ios.dart';

import '../../core/constants/app_constants.dart';
import '../models/user_model.dart';
import '../datasources/remote/api_client.dart';

class AuthRepository {
  final Box _authBox;
  final LocalAuthentication _localAuth;
  late final ApiClient _apiClient;

  AuthRepository({Box? authBox, LocalAuthentication? localAuth})
      : _authBox = authBox ?? Hive.box(AppConstants.authBox),
        _localAuth = localAuth ?? LocalAuthentication() {
    _apiClient = ApiClient(_authBox);
  }

  ApiClient get apiClient => _apiClient;

  Future<bool> isAuthenticated() async {
    final token = _authBox.get(AppConstants.tokenKey);
    return token != null && token.isNotEmpty;
  }

  Future<UserModel> login(String email, String password) async {
    final response = await _apiClient.login(email, password);
    if (response.statusCode == 200) {
      final data = response.data;
      await _authBox.put(AppConstants.tokenKey, data['access_token']);
      await _authBox.put(AppConstants.refreshTokenKey, data['refresh_token']);
      await _authBox.put(AppConstants.userKey, data['user']);
      return UserModel.fromJson(data['user']);
    }
    throw Exception(response.data['detail'] ?? 'Login failed');
  }

  Future<UserModel> register(String name, String email, String password, {String? referralCode}) async {
    final response = await _apiClient.register(name, email, password, referralCode: referralCode);
    if (response.statusCode == 201 || response.statusCode == 200) {
      final data = response.data;
      await _authBox.put(AppConstants.tokenKey, data['access_token']);
      await _authBox.put(AppConstants.refreshTokenKey, data['refresh_token']);
      await _authBox.put(AppConstants.userKey, data['user']);
      return UserModel.fromJson(data['user']);
    }
    throw Exception(response.data['detail'] ?? 'Registration failed');
  }

  Future<void> logout() async {
    try {
      await _apiClient.logout();
    } catch (_) {}
    await _authBox.delete(AppConstants.tokenKey);
    await _authBox.delete(AppConstants.refreshTokenKey);
    await _authBox.delete(AppConstants.userKey);
    await _authBox.delete('biometric_enabled');
  }

  Future<UserModel?> getCurrentUser() async {
    final userData = _authBox.get(AppConstants.userKey);
    if (userData != null) {
      return UserModel.fromJson(Map<String, dynamic>.from(userData));
    }
    try {
      final response = await _apiClient.getCurrentUser();
      if (response.statusCode == 200) {
        await _authBox.put(AppConstants.userKey, response.data);
        return UserModel.fromJson(response.data);
      }
    } catch (_) {}
    return null;
  }

  Future<bool> isBiometricAvailable() async {
    try {
      final available = await _localAuth.isDeviceSupported();
      final canCheck = await _localAuth.canCheckBiometrics;
      return available && canCheck;
    } catch (_) {
      return false;
    }
  }

  Future<bool> isBiometricEnabled() async {
    return _authBox.get('biometric_enabled') == true;
  }

  Future<void> enableBiometric() async {
    await _authBox.put('biometric_enabled', true);
  }

  Future<bool> authenticateWithBiometric() async {
    try {
      final success = await _localAuth.authenticate(
        localizedReason: 'Подтвердите вход в приложение',
        authMessages: const [
          AndroidAuthMessages(
            signInTitle: 'Биометрическая аутентификация',
            cancelButton: 'Отмена',
            biometricHint: 'Подтвердите свою личность',
            biometricNotRecognized: 'Не распознано, попробуйте снова',
            biometricRequiredTitle: 'Требуется биометрия',
            deviceCredentialsRequiredTitle: 'Требуется разблокировка устройства',
            deviceCredentialsSetupDescription: 'Настройте PIN или пароль',
            goToSettingsButton: 'В настройки',
            goToSettingsDescription: 'Настройте биометрию в настройках устройства',
          ),
          IOSAuthMessages(
            cancelButton: 'Отмена',
            goToSettingsButton: 'В настройки',
            goToSettingsDescription: 'Настройте Face ID или Touch ID',
            lockOut: 'Пожалуйста, повторите попытку позже',
          ),
        ],
        options: const AuthenticationOptions(
          biometricOnly: false,
          stickyAuth: true,
          useErrorDialogs: true,
        ),
      );
      return success;
    } catch (_) {
      return false;
    }
  }
}
