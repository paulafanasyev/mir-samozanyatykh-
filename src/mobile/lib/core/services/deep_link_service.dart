import 'package:app_links/app_links.dart';

class DeepLinkService {
  static final DeepLinkService _instance = DeepLinkService._internal();
  factory DeepLinkService() => _instance;
  DeepLinkService._internal();

  final AppLinks _appLinks = AppLinks();

  Future<void> initialize() async {
    try {
      final initialLink = await _appLinks.getInitialLink();
      if (initialLink != null) _handleLink(initialLink);
    } catch (_) {
      // Ignore malformed or unavailable initial links.
    }

    _appLinks.uriLinkStream.listen(_handleLink);
  }

  void _handleLink(Uri uri) {
    if (uri.scheme != 'mirsamoz') return;

    switch (uri.host) {
      case 'payment':
        // Handle payment deep link without logging identifiers.
        break;
      case 'contract':
        // Handle contract deep link without logging identifiers.
        break;
    }
  }
}
