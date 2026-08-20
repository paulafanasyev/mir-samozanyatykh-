import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class AppTheme {
  AppTheme._();

  static const Color primary = Color(0xFFF97316);
  static const Color primaryDark = Color(0xFFEA580C);
  static const Color primaryLight = Color(0xFFFFB45F);
  static const Color secondary = Color(0xFF16A34A);
  static const Color accent = Color(0xFFF6B73C);
  static const Color accentLight = Color(0xFFFFC95E);
  static const Color error = Color(0xFFE53935);
  static const Color warning = Color(0xFFFFA000);
  static const Color success = Color(0xFF43A047);
  static const Color info = Color(0xFF1E88E5);
  static const Color background = Color(0xFFF7F7F5);
  static const Color surface = Color(0xFFFFFFFF);
  static const Color surfaceVariant = Color(0xFFF7F3EE);
  static const Color onSurface = Color(0xFF171A22);
  static const Color onSurfaceVariant = Color(0xFF64748B);
  static const Color outline = Color(0xFFE2E8F0);
  static const Color outlineVariant = Color(0xFFF0F1F3);
  static const Color darkBackground = Color(0xFF0D1016);
  static const Color darkSurface = Color(0xFF151922);
  static const Color darkSurfaceVariant = Color(0xFF1D232E);
  static const Color darkOnSurface = Color(0xFFF8FAFC);
  static const Color darkOnSurfaceVariant = Color(0xFF94A3B8);

  static ThemeData get lightTheme => _theme(Brightness.light);
  static ThemeData get darkTheme => _theme(Brightness.dark);

  static ThemeData _theme(Brightness brightness) {
    final dark = brightness == Brightness.dark;
    final scheme = dark
        ? const ColorScheme.dark(
            primary: accentLight,
            onPrimary: Colors.black,
            primaryContainer: Color(0xFF7C2D12),
            onPrimaryContainer: Color(0xFFFFEDD5),
            secondary: Color(0xFF4ADE80),
            onSecondary: Colors.black,
            secondaryContainer: Color(0xFF1B5E20),
            onSecondaryContainer: Color(0xFFE8F5E9),
            tertiary: accentLight,
            onTertiary: Colors.black,
            error: Color(0xFFEF5350),
            onError: Colors.black,
            surface: darkSurface,
            onSurface: darkOnSurface,
            surfaceContainerHighest: darkSurfaceVariant,
            onSurfaceVariant: darkOnSurfaceVariant,
            outline: Color(0xFF343B48),
            outlineVariant: Color(0xFF272D39),
          )
        : const ColorScheme.light(
            primary: primary,
            onPrimary: Colors.white,
            primaryContainer: Color(0xFFFFE7D1),
            onPrimaryContainer: Color(0xFF9A3412),
            secondary: secondary,
            onSecondary: Colors.white,
            secondaryContainer: Color(0xFFDCFCE7),
            onSecondaryContainer: Color(0xFF1B5E20),
            tertiary: accent,
            onTertiary: Colors.white,
            tertiaryContainer: Color(0xFFFFF7E8),
            onTertiaryContainer: Color(0xFF9A3412),
            error: error,
            onError: Colors.white,
            errorContainer: Color(0xFFFFEBEE),
            onErrorContainer: Color(0xFFB71C1C),
            surface: surface,
            onSurface: onSurface,
            surfaceContainerHighest: surfaceVariant,
            onSurfaceVariant: onSurfaceVariant,
            outline: outline,
            outlineVariant: outlineVariant,
          );

    final textColor = dark ? darkOnSurface : onSurface;
    return ThemeData(
      useMaterial3: true,
      brightness: brightness,
      colorScheme: scheme,
      scaffoldBackgroundColor: dark ? darkBackground : background,
      textTheme: GoogleFonts.interTextTheme().apply(bodyColor: textColor, displayColor: textColor),
      appBarTheme: AppBarTheme(
        elevation: 0,
        scrolledUnderElevation: 1,
        centerTitle: true,
        backgroundColor: dark ? darkSurface : surface,
        foregroundColor: textColor,
      ),
      cardTheme: CardThemeData(
        elevation: 0,
        color: dark ? darkSurface : surface,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: BorderSide(color: dark ? const Color(0xFF343B48) : outlineVariant),
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          elevation: 0,
          backgroundColor: scheme.primary,
          foregroundColor: scheme.onPrimary,
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: scheme.primary,
          side: BorderSide(color: scheme.outline),
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: dark ? darkSurfaceVariant : surfaceVariant,
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
        enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
        focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide(color: scheme.primary, width: 2)),
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      ),
      floatingActionButtonTheme: FloatingActionButtonThemeData(
        backgroundColor: scheme.primary,
        foregroundColor: scheme.onPrimary,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      ),
      bottomNavigationBarTheme: BottomNavigationBarThemeData(
        backgroundColor: dark ? darkSurface : surface,
        selectedItemColor: scheme.primary,
        unselectedItemColor: scheme.onSurfaceVariant,
        type: BottomNavigationBarType.fixed,
      ),
      dividerTheme: DividerThemeData(color: scheme.outlineVariant, thickness: 1, space: 1),
    );
  }
}
