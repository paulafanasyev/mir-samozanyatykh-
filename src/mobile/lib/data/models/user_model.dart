class UserModel {
  final int id;
  final String name;
  final String email;
  final String? avatar;
  final String userTier;
  final int referralCount;
  final double referralEarnings;
  final bool isVerified;
  final bool isAdmin;
  final bool isModerator;
  final String? phone;
  final String? inn;

  const UserModel({
    required this.id,
    required this.name,
    required this.email,
    this.avatar,
    this.userTier = 'start',
    this.referralCount = 0,
    this.referralEarnings = 0,
    this.isVerified = false,
    this.isAdmin = false,
    this.isModerator = false,
    this.phone,
    this.inn,
  });

  factory UserModel.fromJson(Map<String, dynamic> json) {
    final idValue = json['id'];
    return UserModel(
      id: idValue is num ? idValue.toInt() : int.tryParse('$idValue') ?? 0,
      name: (json['name'] ?? json['full_name'] ?? json['username'] ?? 'Пользователь').toString(),
      email: (json['email'] ?? '').toString(),
      avatar: (json['avatar'] ?? json['avatar_url'])?.toString(),
      userTier: (json['user_tier'] ?? json['tier'] ?? 'start').toString(),
      referralCount: (json['referral_count'] as num?)?.toInt() ?? 0,
      referralEarnings: (json['referral_earnings'] as num?)?.toDouble() ?? 0,
      isVerified: json['is_verified'] == true || json['verified'] == true,
      isAdmin: json['is_admin'] == true || json['role'] == 'admin',
      isModerator: json['is_moderator'] == true || json['role'] == 'moderator',
      phone: json['phone']?.toString(),
      inn: json['inn']?.toString(),
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'name': name,
        'email': email,
        if (avatar != null) 'avatar': avatar,
        'user_tier': userTier,
        'referral_count': referralCount,
        'referral_earnings': referralEarnings,
        'is_verified': isVerified,
        'is_admin': isAdmin,
        'is_moderator': isModerator,
        if (phone != null) 'phone': phone,
        if (inn != null) 'inn': inn,
      };
}
