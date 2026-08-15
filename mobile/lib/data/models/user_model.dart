import 'package:freezed_annotation/freezed_annotation.dart';

part 'user_model.freezed.dart';
part 'user_model.g.dart';

@freezed
class UserModel with _$UserModel {
  const factory UserModel({
    required int id,
    required String email,
    required String name,
    String? phone,
    String? inn,
    String? avatar,
    @Default('start') String userTier,
    @Default(false) bool isAdmin,
    @Default(false) bool isModerator,
    @Default(false) bool isVerified,
    @Default(0) int referralCount,
    @Default(0.0) double referralEarnings,
    String? referralCode,
    DateTime? createdAt,
    DateTime? updatedAt,
    DateTime? subscriptionExpiresAt,
  }) = _UserModel;

  factory UserModel.fromJson(Map<String, dynamic> json) =>
      _$UserModelFromJson(json);
}
