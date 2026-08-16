import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/auth_service.dart';

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final _nameController = TextEditingController();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _phoneController = TextEditingController();
  final _innController = TextEditingController();
  bool _isLoading = false;
  String? _error;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            colors: [Color(0xFF667eea), Color(0xFF764ba2)],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
        ),
        child: SafeArea(
          child: Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(24),
              child: Card(
                elevation: 8,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
                child: Padding(
                  padding: const EdgeInsets.all(32),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Text(
                        'Регистрация',
                        style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Color(0xFF667eea)),
                      ),
                      const SizedBox(height: 24),
                      if (_error != null)
                        Container(
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(color: Colors.red.shade50, borderRadius: BorderRadius.circular(8)),
                          child: Text(_error!, style: TextStyle(color: Colors.red.shade700)),
                        ),
                      const SizedBox(height: 16),
                      _buildField('Имя', _nameController, Icons.person),
                      const SizedBox(height: 12),
                      _buildField('Email', _emailController, Icons.email, type: TextInputType.emailAddress),
                      const SizedBox(height: 12),
                      _buildField('Пароль', _passwordController, Icons.lock, obscure: true),
                      const SizedBox(height: 12),
                      _buildField('Телефон', _phoneController, Icons.phone, type: TextInputType.phone),
                      const SizedBox(height: 12),
                      _buildField('ИНН (12 цифр)', _innController, Icons.business, type: TextInputType.number),
                      const SizedBox(height: 24),
                      SizedBox(
                        width: double.infinity,
                        height: 50,
                        child: ElevatedButton(
                          onPressed: _isLoading ? null : _register,
                          style: ElevatedButton.styleFrom(
                            backgroundColor: const Color(0xFF667eea),
                            foregroundColor: Colors.white,
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                          ),
                          child: _isLoading
                              ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                              : const Text('Создать аккаунт', style: TextStyle(fontSize: 16)),
                        ),
                      ),
                      const SizedBox(height: 16),
                      TextButton(
                        onPressed: () => Navigator.pop(context),
                        child: const Text('Уже есть аккаунт? Войти'),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildField(String label, TextEditingController controller, IconData icon, {bool obscure = false, TextInputType? type}) {
    return TextField(
      controller: controller,
      decoration: InputDecoration(
        labelText: label,
        prefixIcon: Icon(icon),
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
      ),
      obscureText: obscure,
      keyboardType: type,
    );
  }

  Future<void> _register() async {
    setState(() { _isLoading = true; _error = null; });
    final success = await context.read<AuthService>().register(
      _nameController.text,
      _emailController.text,
      _passwordController.text,
      phone: _phoneController.text.isEmpty ? null : _phoneController.text,
      inn: _innController.text.isEmpty ? null : _innController.text,
    );
    if (success) {
      await context.read<AuthService>().login(_emailController.text, _passwordController.text);
    } else {
      setState(() { _error = 'Ошибка регистрации. Возможно, email уже используется.'; _isLoading = false; });
    }
  }

  @override
  void dispose() {
    _nameController.dispose();
    _emailController.dispose();
    _passwordController.dispose();
    _phoneController.dispose();
    _innController.dispose();
    super.dispose();
  }
}
