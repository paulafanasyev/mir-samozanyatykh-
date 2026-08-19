import 'package:local_auth/local_auth.dart';
import 'package:local_auth_android/local_auth_android.dart';
import 'package:local_auth_ios/local_auth_ios.dart';

class BiometricAuthService {
  static final BiometricAuthService _instance = BiometricAuthService._internal();
  factory BiometricAuthService() => _instance;
  BiometricAuthService._internal();

  final LocalAuthentication _localAuth = LocalAuthentication();

  Future<bool> isAvailable() async {
    return await _localAuth.isDeviceSupported() && await _localAuth.canCheckBiometrics;
  }

  Future<bool> authenticate() async {
    try {
      return await _localAuth.authenticate(
        localizedReason: 'Подтвердите вход в Мир Самозанятых',
        authMessages: const [
          AndroidAuthMessages(
            signInTitle: 'Биометрическая аутентификация',
            cancelButton: 'Отмена', biometricHint: 'Подтвердите',
          ),
          IOSAuthMessages(cancelButton: 'Отмена'),
        ],
        options: const AuthenticationOptions(stickyAuth: true, biometricOnly: false),
      );
    } catch (e) {
      return false;
    }
  }
}
