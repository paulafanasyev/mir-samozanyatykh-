import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class AuthService {
  static const _storage = FlutterSecureStorage();
  static const _tokenKey = 'access_token';
  static const _refreshKey = 'refresh_token';
  static const _baseUrl = 'https://mir-samozanyatykh.onrender.com';

  static Future<String?> getToken() async {
    return await _storage.read(key: _tokenKey);
  }

  static Future<void> setToken(String token) async {
    await _storage.write(key: _tokenKey, value: token);
  }

  static Future<void> clear() async {
    await _storage.deleteAll();
  }

  static Future<Map<String, dynamic>?> login(String email, String password) async {
    final res = await http.post(
      Uri.parse('$_baseUrl/api/auth/login'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'email': email, 'password': password}),
    );
    if (res.statusCode == 200) {
      final data = jsonDecode(res.body);
      await setToken(data['access_token']);
      await _storage.write(key: _refreshKey, value: data['refresh_token']);
      return data;
    }
    return null;
  }

  static Future<Map<String, dynamic>?> register(Map<String, String> data) async {
    final res = await http.post(
      Uri.parse('$_baseUrl/api/auth/register'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(data),
    );
    if (res.statusCode == 200) {
      return jsonDecode(res.body);
    }
    return null;
  }

  static Future<Map<String, dynamic>?> me() async {
    final token = await getToken();
    if (token == null) return null;
    final res = await http.get(
      Uri.parse('$_baseUrl/api/auth/me'),
      headers: {'Authorization': 'Bearer $token'},
    );
    if (res.statusCode == 200) return jsonDecode(res.body);
    return null;
  }
}
