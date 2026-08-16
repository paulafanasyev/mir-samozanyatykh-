import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class AuthService extends ChangeNotifier {
  final _storage = const FlutterSecureStorage();
  final String baseUrl = 'https://mir-samozanyatykh-api.onrender.com';

  bool _isAuthenticated = false;
  bool _isLoading = true;
  Map<String, dynamic>? _user;
  String? _token;

  bool get isAuthenticated => _isAuthenticated;
  bool get isLoading => _isLoading;
  Map<String, dynamic>? get user => _user;

  AuthService() {
    _checkAuth();
  }

  Future<void> _checkAuth() async {
    _token = await _storage.read(key: 'access_token');
    if (_token != null) {
      await _fetchUser();
    }
    _isLoading = false;
    notifyListeners();
  }

  Future<void> _fetchUser() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/api/user/me'),
        headers: {'Authorization': 'Bearer $_token'},
      );
      if (response.statusCode == 200) {
        _user = jsonDecode(response.body);
        _isAuthenticated = true;
      } else {
        await logout();
      }
    } catch (e) {
      await logout();
    }
  }

  Future<bool> login(String email, String password) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/api/auth/login'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'email': email, 'password': password}),
      );
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        _token = data['access_token'];
        await _storage.write(key: 'access_token', value: _token);
        await _fetchUser();
        notifyListeners();
        return true;
      }
      return false;
    } catch (e) {
      return false;
    }
  }

  Future<bool> register(String fullName, String email, String password, {String? phone, String? inn}) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/api/auth/register'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'full_name': fullName,
          'email': email,
          'password': password,
          'phone': phone,
          'inn': inn,
        }),
      );
      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }

  Future<void> logout() async {
    await _storage.delete(key: 'access_token');
    _token = null;
    _user = null;
    _isAuthenticated = false;
    notifyListeners();
  }
}
