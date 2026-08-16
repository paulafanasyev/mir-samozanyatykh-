import 'package:http/http.dart' as http;
import 'dart:convert';
import 'auth_service.dart';

class ApiService {
  static const _baseUrl = 'https://mir-samozanyatykh.onrender.com';

  static Future<Map<String, String>> _headers() async {
    final token = await AuthService.getToken();
    return {
      'Content-Type': 'application/json',
      if (token != null) 'Authorization': 'Bearer $token',
    };
  }

  static Future<http.Response> get(String path) async {
    return http.get(Uri.parse('$_baseUrl$path'), headers: await _headers());
  }

  static Future<http.Response> post(String path, Map<String, dynamic> body) async {
    return http.post(
      Uri.parse('$_baseUrl$path'),
      headers: await _headers(),
      body: jsonEncode(body),
    );
  }

  static Future<http.Response> delete(String path) async {
    return http.delete(Uri.parse('$_baseUrl$path'), headers: await _headers());
  }
}
