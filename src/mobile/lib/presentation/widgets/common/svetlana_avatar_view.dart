import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';

class SvetlanaAvatarView extends StatefulWidget {
  const SvetlanaAvatarView({super.key, this.height = 180, this.compact = false});
  final double height;
  final bool compact;

  @override
  State<SvetlanaAvatarView> createState() => _SvetlanaAvatarViewState();
}

class _SvetlanaAvatarViewState extends State<SvetlanaAvatarView> {
  late final WebViewController _controller;

  @override
  void initState() {
    super.initState();
    _controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..setNavigationDelegate(NavigationDelegate(
        onNavigationRequest: (request) {
          final uri = Uri.tryParse(request.url);
          // Flutter's bundled asset loader uses the flutter_asset scheme/host.
          // Keep the avatar isolated from external navigation.
          final allowed = uri != null &&
              (uri.scheme == 'file' ||
                  uri.scheme == 'flutter-asset' ||
                  uri.host == 'flutter_asset');
          return allowed ? NavigationDecision.navigate : NavigationDecision.prevent;
        },
      ))
      ..loadFlutterAsset('assets/svetlana/index.html');
  }

  void emotion(String name) {
    const allowed = {'none', 'smile', 'surprise', 'sad', 'angry', 'thinking'};
    final safeName = allowed.contains(name) ? name : 'none';
    _controller.runJavaScript(
      "window.postMessage({type:'svetlana.emotion',name:${jsonEncode(safeName)},duration:2200},'*');",
    );
  }

  @override
  Widget build(BuildContext context) => ClipRRect(
        borderRadius: BorderRadius.circular(widget.compact ? 18 : 24),
        child: SizedBox(
          height: widget.height,
          width: double.infinity,
          child: WebViewWidget(controller: _controller),
        ),
      );
}
