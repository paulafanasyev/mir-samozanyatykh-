import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:freezed_annotation/freezed_annotation.dart';

import '../../data/models/user_model.dart';
import '../../data/repositories/auth_repository.dart';

part 'auth_provider.freezed.dart';

@freezed
class AuthState with _$AuthState {
  const factory AuthState({
    @Default(false) bool isAuthenticated,
    UserModel? user,
    @Default(false) bool isLoading,
    String? error,
    @Default(false) bool biometricEnabled,
    @Default(false) bool biometricAvailable,
  }) = _AuthState;
}

final authRepositoryProvider = Provider<AuthRepository>((ref) {
  return AuthRepository();
});

final authStateProvider = StateNotifierProvider<AuthNotifier, AsyncValue<AuthState>>((ref) {
  return AuthNotifier(ref.watch(authRepositoryProvider));
});

class AuthNotifier extends StateNotifier<AsyncValue<AuthState>> {
  final AuthRepository _repository;

  AuthNotifier(this._repository) : super(const AsyncValue.loading()) {
    _checkAuth();
  }

  Future<void> _checkAuth() async {
    try {
      final isAuth = await _repository.isAuthenticated();
      if (isAuth) {
        final user = await _repository.getCurrentUser();
        state = AsyncValue.data(AuthState(
          isAuthenticated: true,
          user: user,
          biometricAvailable: await _repository.isBiometricAvailable(),
          biometricEnabled: await _repository.isBiometricEnabled(),
        ));
      } else {
        state = const AsyncValue.data(AuthState());
      }
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }

  Future<void> login(String email, String password) async {
    state = const AsyncValue.loading();
    try {
      final user = await _repository.login(email, password);
      state = AsyncValue.data(AuthState(
        isAuthenticated: true,
        user: user,
        biometricAvailable: await _repository.isBiometricAvailable(),
      ));
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }

  Future<void> register(String name, String email, String password, {String? referralCode}) async {
    state = const AsyncValue.loading();
    try {
      final user = await _repository.register(name, email, password, referralCode: referralCode);
      state = AsyncValue.data(AuthState(
        isAuthenticated: true,
        user: user,
      ));
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }

  Future<void> logout() async {
    state = const AsyncValue.loading();
    try {
      await _repository.logout();
      state = const AsyncValue.data(AuthState());
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }

  Future<void> enableBiometric() async {
    await _repository.enableBiometric();
    state = AsyncValue.data(state.value!.copyWith(biometricEnabled: true));
  }

  Future<void> authenticateWithBiometric() async {
    try {
      final success = await _repository.authenticateWithBiometric();
      if (success) {
        final user = await _repository.getCurrentUser();
        state = AsyncValue.data(state.value!.copyWith(
          isAuthenticated: true,
          user: user,
        ));
      }
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }
}
