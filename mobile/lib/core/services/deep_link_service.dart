import 'package:flutter/services.dart';
import 'package:uni_links/uni_links.dart';

class DeepLinkService {
  static final DeepLinkService _instance = DeepLinkService._internal();
  factory DeepLinkService() => _instance;
  DeepLinkService._internal();

  Future<void> initialize() async {
    try {
      final initialLink = await getInitialLink();
      if (initialLink != null) _handleLink(initialLink);
    } on PlatformException {}

    linkStream.listen((String? link) {
      if (link != null) _handleLink(link);
    });
  }

  void _handleLink(String link) {
    final uri = Uri.parse(link);
    if (uri.scheme == 'mirsamoz') {
      switch (uri.host) {
        case 'payment':
          print('Payment: ${uri.queryParameters['id']}');
          break;
        case 'contract':
          print('Contract: ${uri.queryParameters['id']}');
          break;
      }
    }
  }
}
