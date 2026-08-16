import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/auth_service.dart';
import '../services/api_service.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  final _api = ApiService();
  Map<String, dynamic>? _achievements;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadAchievements();
  }

  Future<void> _loadAchievements() async {
    try {
      final data = await _api.get('/api/achievements');
      setState(() {
        _achievements = data;
        _loading = false;
      });
    } catch (e) {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final user = context.watch<AuthService>().user;
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        children: [
          CircleAvatar(
            radius: 50,
            backgroundColor: const Color(0xFF667eea),
            child: Text(
              (user?['full_name'] ?? 'U')[0].toUpperCase(),
              style: const TextStyle(fontSize: 36, color: Colors.white, fontWeight: FontWeight.bold),
            ),
          ),
          const SizedBox(height: 16),
          Text(user?['full_name'] ?? 'Пользователь', style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
          Text(user?['email'] ?? '', style: TextStyle(color: Colors.grey.shade600)),
          const SizedBox(height: 8),
          Chip(
            label: Text(user?['subscription']?.toUpperCase() ?? 'START'),
            backgroundColor: const Color(0xFF667eea).withOpacity(0.1),
            labelStyle: const TextStyle(color: Color(0xFF667eea), fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 24),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                children: [
                  _buildInfoRow(Icons.phone, 'Телефон', user?['phone'] ?? 'Не указан'),
                  _buildInfoRow(Icons.business, 'ИНН', user?['inn'] ?? 'Не указан'),
                  _buildInfoRow(Icons.verified, 'Верификация', user?['is_verified'] == true ? 'Подтверждена' : 'Не подтверждена'),
                ],
              ),
            ),
          ),
          const SizedBox(height: 24),
          if (_achievements != null) ...[
            const Text('🏆 Достижения', style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
            const SizedBox(height: 12),
            Text('Всего очков: ${_achievements!['total_points'] ?? 0}', style: const TextStyle(color: Color(0xFF667eea), fontWeight: FontWeight.bold)),
            const SizedBox(height: 12),
            if ((_achievements!['earned'] as List?)?.isNotEmpty == true)
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: (_achievements!['earned'] as List).map((a) => Chip(
                  avatar: Text(a['icon'] ?? '⭐'),
                  label: Text(a['name'] ?? ''),
                  backgroundColor: Colors.amber.shade100,
                )).toList(),
              ),
          ],
          const SizedBox(height: 24),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton.icon(
              onPressed: () => context.read<AuthService>().logout(),
              icon: const Icon(Icons.logout),
              label: const Text('Выйти'),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.red.shade400,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 16),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInfoRow(IconData icon, String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        children: [
          Icon(icon, size: 20, color: Colors.grey.shade600),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(label, style: TextStyle(fontSize: 12, color: Colors.grey.shade600)),
                Text(value, style: const TextStyle(fontWeight: FontWeight.w500)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
