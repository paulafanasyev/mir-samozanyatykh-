import 'package:intl/intl.dart';

class Validators {
  Validators._();

  static bool isValidEmail(String value) {
    final email = value.trim();
    return RegExp(r'^[^\s@]+@[^\s@]+\.[^\s@]+$').hasMatch(email);
  }

  static bool isValidPhone(String value) {
    final digits = value.replaceAll(RegExp(r'\D'), '');
    return digits.length >= 10 && digits.length <= 15;
  }

  static bool isValidINN(String value) {
    final inn = value.trim();
    if (!RegExp(r'^\d{10}(?:\d{2})?$').hasMatch(inn)) return false;
    if (inn.length == 10) {
      const weights = [2, 4, 10, 3, 5, 9, 4, 6, 8];
      final sum = List.generate(9, (i) => int.parse(inn[i]) * weights[i]).fold<int>(0, (a, b) => a + b);
      return sum % 11 % 10 == int.parse(inn[9]);
    }
    const w1 = [7, 2, 4, 10, 3, 5, 9, 4, 6, 8];
    const w2 = [3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8];
    final s1 = List.generate(10, (i) => int.parse(inn[i]) * w1[i]).fold<int>(0, (a,b)=>a+b);
    final s2 = List.generate(11, (i) => int.parse(inn[i]) * w2[i]).fold<int>(0, (a,b)=>a+b);
    return s1 % 11 % 10 == int.parse(inn[10]) && s2 % 11 % 10 == int.parse(inn[11]);
  }
}

class Formatters {
  Formatters._();

  static String currency(num value) => NumberFormat('#,##0.##', 'ru_RU').format(value).replaceAll(',', ' ') + ' ₽';
  static String date(DateTime value) => DateFormat('dd.MM.yyyy').format(value);
}
