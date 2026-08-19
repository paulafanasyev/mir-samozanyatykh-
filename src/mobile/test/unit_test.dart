import 'package:flutter_test/flutter_test.dart';
import 'package:mir_samozanyatykh_mobile/core/utils/validators.dart';

void main() {
  group('Validators', () {
    test('Valid email passes', () {
      expect(Validators.isValidEmail('test@example.com'), true);
    });

    test('Invalid email fails', () {
      expect(Validators.isValidEmail('invalid'), false);
    });

    test('Valid phone passes', () {
      expect(Validators.isValidPhone('+79001234567'), true);
    });

    test('Valid INN passes', () {
      expect(Validators.isValidINN('9724016805'), true);
    });
  });

  group('Formatters', () {
    test('Format currency', () {
      expect(Formatters.currency(1000), '1 000 ₽');
    });

    test('Format date', () {
      expect(Formatters.date(DateTime(2026, 8, 16)), '16.08.2026');
    });
  });
}
