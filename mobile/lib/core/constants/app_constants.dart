class AppConstants {
  AppConstants._();

  static const String appName = 'Мир Самозанятых';
  static const String appVersion = '8.6.0';
  static const String buildNumber = '860';

  // API
  static const String baseUrl = 'https://api.mir-samozanyatykh.ru';
  static const String devBaseUrl = 'https://dev.mir-samozanyatykh.ru';
  static const int apiTimeout = 30000;
  static const int apiMaxRetries = 3;

  // Storage
  static const String cacheBox = 'cache';
  static const String settingsBox = 'settings';
  static const String authBox = 'auth';
  static const String tokenKey = 'access_token';
  static const String refreshTokenKey = 'refresh_token';
  static const String userKey = 'user_data';

  // Features
  static const int maxOfflineDays = 7;
  static const int itemsPerPage = 20;
  static const int maxImageSize = 5 * 1024 * 1024; // 5MB
  static const int maxFileSize = 10 * 1024 * 1024; // 10MB

  // Biometrics
  static const int biometricTimeout = 300; // 5 minutes

  // Notifications
  static const String notificationChannelId = 'high_importance_channel';
  static const String notificationChannelName = 'Важные уведомления';

  // Deep links
  static const String appScheme = 'mirsamozanyatykh';

  // Analytics
  static const String analyticsCategoryAuth = 'auth';
  static const String analyticsCategoryBusiness = 'business';
  static const String analyticsCategoryFinance = 'finance';
}
