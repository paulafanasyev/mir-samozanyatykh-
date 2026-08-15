# Flutter
-keep class io.flutter.app.** { *; }
-keep class io.flutter.plugin.** { *; }
-keep class io.flutter.util.** { *; }
-keep class io.flutter.view.** { *; }
-keep class io.flutter.** { *; }
-keep class io.flutter.plugins.** { *; }

# Firebase
-keep class com.google.firebase.** { *; }
-keep class com.google.android.gms.** { *; }

# Dio/Retrofit
-keep class com.mirsamozanyatykh.mobile.data.models.** { *; }
-keepclassmembers class * {
    @retrofit2.http.* <methods>;
}

# Local Auth
-keep class androidx.biometric.** { *; }

# WebRTC
-keep class org.webrtc.** { *; }
