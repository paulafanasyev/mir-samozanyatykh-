import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../data/models/user_model.dart';
import '../../data/repositories/auth_repository.dart';

class AuthState {
  final String? twoFactorTempToken;
  final bool isAuthenticated;
  final UserModel? user;
  final bool isLoading;
  final String? error;
  final bool biometricEnabled;
  final bool biometricAvailable;

  const AuthState({
    this.isAuthenticated = false,
    this.twoFactorTempToken,
    this.user,
    this.isLoading = false,
    this.error,
    this.biometricEnabled = false,
    this.biometricAvailable = false,
  });

  AuthState copyWith({
    bool? isAuthenticated,
    String? twoFactorTempToken,
    bool clearTwoFactorTempToken = false,
    UserModel? user,
    bool clearUser = false,
    bool? isLoading,
    String? error,
    bool clearError = false,
    bool? biometricEnabled,
    bool? biometricAvailable,
  }) => AuthState(
    isAuthenticated: isAuthenticated ?? this.isAuthenticated,
    twoFactorTempToken: clearTwoFactorTempToken ? null : (twoFactorTempToken ?? this.twoFactorTempToken),
    user: clearUser ? null : (user ?? this.user),
    isLoading: isLoading ?? this.isLoading,
    error: clearError ? null : (error ?? this.error),
    biometricEnabled: biometricEnabled ?? this.biometricEnabled,
    biometricAvailable: biometricAvailable ?? this.biometricAvailable,
  );
}

final authRepositoryProvider = Provider<AuthRepository>((ref) => AuthRepository());
final authStateProvider = StateNotifierProvider<AuthNotifier, AsyncValue<AuthState>>(
  (ref) => AuthNotifier(ref.watch(authRepositoryProvider)),
);

class AuthNotifier extends StateNotifier<AsyncValue<AuthState>> {
  final AuthRepository _repository;
  AuthNotifier(this._repository) : super(const AsyncValue.loading()) { _checkAuth(); }

  Future<void> _checkAuth() async {
    try {
      if (!await _repository.isAuthenticated()) {
        state = const AsyncValue.data(AuthState());
        return;
      }
      final user = await _repository.getCurrentUser();
      state = AsyncValue.data(AuthState(
        isAuthenticated: true,
        user: user,
        biometricAvailable: await _repository.isBiometricAvailable(),
        biometricEnabled: await _repository.isBiometricEnabled(),
      ));
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }

  Future<void> login(String email, String password) async {
    state = const AsyncValue.data(AuthState(isLoading: true));
    try {
      final user = await _repository.login(email, password);
      state = AsyncValue.data(AuthState(
        isAuthenticated: true,
        user: user,
        biometricAvailable: await _repository.isBiometricAvailable(),
      ));
    } catch (e, st) {
      if (e is TwoFactorRequiredException) {
        state = AsyncValue.data(const AuthState(twoFactorTempToken: 'pending'));
        _pendingTwoFactorToken = e.tempToken;
      } else {
        state = AsyncValue.error(e, st);
      }
    }
  }

  String? _pendingTwoFactorToken;

  Future<void> login2fa(String code) async {
    final token = _pendingTwoFactorToken;
    if (token == null || token.isEmpty) throw Exception('Сессия 2FA истекла');
    state = const AsyncValue.data(AuthState(isLoading: true));
    try {
      final user = await _repository.login2fa(token, code);
      _pendingTwoFactorToken = null;
      state = AsyncValue.data(AuthState(isAuthenticated: true, user: user));
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }

  Future<void> register(String name, String email, String password, {String? referralCode}) async {
    state = const AsyncValue.data(AuthState(isLoading: true));
    try {
      await _repository.register(name, email, password, referralCode: referralCode);
      state = const AsyncValue.data(AuthState());
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }

  Future<void> logout() async {
    try { await _repository.logout(); } finally { state = const AsyncValue.data(AuthState()); }
  }

  Future<void> enableBiometric() async {
    await _repository.enableBiometric();
    final current = state.value ?? const AuthState();
    state = AsyncValue.data(current.copyWith(biometricEnabled: true));
  }

  Future<void> authenticateWithBiometric() async {
    try {
      if (await _repository.authenticateWithBiometric()) {
        final user = await _repository.getCurrentUser();
        state = AsyncValue.data((state.value ?? const AuthState()).copyWith(
          isAuthenticated: user != null, user: user,
        ));
      }
    } catch (e, st) { state = AsyncValue.error(e, st); }
  }
}
