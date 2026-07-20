import 'package:flutter/material.dart';

/// DESIGN.md 设计 token 对应的 Flutter Theme
class AppTheme {
  AppTheme._();

  // ── Colors (from DESIGN.md tokens) ──────────────────────────────────
  static const Color primary = Color(0xFFFF9500);
  static const Color primaryLight = Color(0xFFFFB84D);
  static const Color primaryDark = Color(0xFFCC7700);
  static const Color secondary = Color(0xFF34C759);
  static const Color secondaryLight = Color(0xFF6BD98A);
  static const Color accent = Color(0xFF007AFF);
  static const Color background = Color(0xFFFFF8F0);
  static const Color surface = Color(0xFFFFFFFF);
  static const Color surfaceWarm = Color(0xFFFFF5E6);
  static const Color textPrimary = Color(0xFF2C1810);
  static const Color textSecondary = Color(0xFF8B7355);
  static const Color textOnPrimary = Color(0xFFFFFFFF);

  // Theme colors
  static const List<Color> topicColors = [
    Color(0xFF8BC34A), // dino
    Color(0xFF2196F3), // ocean
    Color(0xFF9C27B0), // space
    Color(0xFFFFD60A), // sunshine
    Color(0xFF4CAF50), // forest
    Color(0xFFE91E63), // pink
    Color(0xFF87CEEB), // sky
    Color(0xFFC9A0DC), // lavender
  ];

  // ── Theme ───────────────────────────────────────────────────────────
  static final ThemeData light = ThemeData(
    useMaterial3: true,
    colorScheme: ColorScheme.fromSeed(
      seedColor: primary,
      primary: primary,
      secondary: secondary,
      surface: surface,
      brightness: Brightness.light,
    ),
    scaffoldBackgroundColor: background,

    // Typography
    textTheme: const TextTheme(
      displayLarge: TextStyle(fontSize: 32, fontWeight: FontWeight.w700, height: 1.2, color: textPrimary),
      headlineMedium: TextStyle(fontSize: 22, fontWeight: FontWeight.w700, height: 1.3, color: textPrimary),
      bodyLarge: TextStyle(fontSize: 18, fontWeight: FontWeight.w500, height: 1.5, color: textPrimary),
      bodyMedium: TextStyle(fontSize: 16, fontWeight: FontWeight.w400, height: 1.6, color: textPrimary),
      bodySmall: TextStyle(fontSize: 13, fontWeight: FontWeight.w400, height: 1.4, color: textSecondary),
      labelLarge: TextStyle(fontSize: 18, fontWeight: FontWeight.w700, height: 1.2, color: textOnPrimary),
    ),

    // Buttons
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: primary,
        foregroundColor: textOnPrimary,
        minimumSize: const Size(double.infinity, 56),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(32)),
        elevation: 2,
        shadowColor: primary.withValues(alpha: 0.3),
        textStyle: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700),
        padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
      ),
    ),

    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        foregroundColor: primary,
        minimumSize: const Size(double.infinity, 56),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(32)),
        side: const BorderSide(color: primary, width: 2),
        textStyle: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700),
      ),
    ),

    // Cards
    cardTheme: CardThemeData(
      color: surface,
      elevation: 1,
      shadowColor: Colors.black.withValues(alpha: 0.08),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
    ),

    // Input
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: surface,
      contentPadding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(32),
        borderSide: const BorderSide(color: primaryLight),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(32),
        borderSide: const BorderSide(color: Color(0xFFE8D5C4)),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(32),
        borderSide: const BorderSide(color: primary, width: 2),
      ),
    ),

    // AppBar
    appBarTheme: const AppBarTheme(
      backgroundColor: surface,
      foregroundColor: textPrimary,
      elevation: 0,
      centerTitle: true,
      titleTextStyle: TextStyle(fontSize: 20, fontWeight: FontWeight.w700, color: textPrimary),
    ),

    // Bottom navigation
    bottomNavigationBarTheme: const BottomNavigationBarThemeData(
      backgroundColor: surface,
      selectedItemColor: primary,
      unselectedItemColor: textSecondary,
      type: BottomNavigationBarType.fixed,
      elevation: 2,
      selectedLabelStyle: TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
      unselectedLabelStyle: TextStyle(fontSize: 12),
    ),
  );
}
