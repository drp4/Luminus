import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../../../core/services/api_client.dart';
import '../../../core/models/app_models.dart';
import '../../../core/theme/app_theme.dart';
import '../../chat/views/chat_sheet.dart';

// ── State ────────────────────────────────────────────────────────────

final childProvider = StateProvider<Child?>((ref) => null);
final onboardingStepProvider = StateProvider<int>((ref) => 0);

class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({super.key});
  @override
  ConsumerState<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends ConsumerState<HomeScreen> {
  bool _checking = true;

  @override
  void initState() {
    super.initState();
    _restoreSession();
  }

  Future<void> _restoreSession() async {
    final prefs = await SharedPreferences.getInstance();
    final childId = prefs.getString('child_id');
    if (childId != null) {
      try {
        final api = ref.read(apiClientProvider);
        final profile = await api.getProfile(childId);
        ref.read(childProvider.notifier).state = Child(
          id: childId,
          nickname: profile['nickname'] ?? '',
          age: profile['age'] ?? 9,
          grade: profile['grade'] ?? '',
        );
      } catch (_) {
        await prefs.remove('child_id');
      }
    }
    setState(() => _checking = false);
  }

  @override
  Widget build(BuildContext context) {
    if (_checking) return const Scaffold(body: Center(child: CircularProgressIndicator()));
    final child = ref.watch(childProvider);
    return child != null ? const _MainHome() : const _OnboardingFlow();
  }
}

// ══════════════════════════════════════════════════════════════════════
// Onboarding Flow — 4-step PageView
// ══════════════════════════════════════════════════════════════════════

class _OnboardingFlow extends ConsumerStatefulWidget {
  const _OnboardingFlow();
  @override
  ConsumerState<_OnboardingFlow> createState() => _OnboardingFlowState();
}

class _OnboardingFlowState extends ConsumerState<_OnboardingFlow> {
  final _pageCtrl = PageController();
  final _nameCtrl = TextEditingController();
  int _age = 9;
  String _grade = '3年级';
  String _partner = '小阳';
  bool _creating = false;

  static const _partners = [
    {'name': '小阳', 'emoji': '☀️', 'color': Color(0xFFFF9500), 'desc': '阳光开朗,喜欢运动'},
    {'name': '星星', 'emoji': '⭐', 'color': Color(0xFF9C27B0), 'desc': '好奇宝宝,爱问为什么'},
    {'name': '小海', 'emoji': '🌊', 'color': Color(0xFF2196F3), 'desc': '安静温柔,喜欢听故事'},
    {'name': '芽芽', 'emoji': '🌱', 'color': Color(0xFF34C759), 'desc': '小小艺术家,爱画画唱歌'},
  ];

  static const _ages = [6, 7, 8, 9, 10, 11, 12];
  static const _grades = ['1年级', '2年级', '3年级', '4年级', '5年级', '6年级'];

  @override
  void dispose() {
    _pageCtrl.dispose();
    _nameCtrl.dispose();
    super.dispose();
  }

  Future<void> _finish() async {
    if (_nameCtrl.text.trim().isEmpty) return;
    setState(() => _creating = true);
    try {
      final api = ref.read(apiClientProvider);
      final data = await api.createChild(_nameCtrl.text.trim(), _age, _grade);
      final child = Child.fromJson(data);
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('child_id', child.id);
      ref.read(childProvider.notifier).state = child;
    } finally {
      setState(() => _creating = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final step = ref.watch(onboardingStepProvider);

    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            // Progress dots
            const SizedBox(height: 24),
            Row(mainAxisAlignment: MainAxisAlignment.center, children: List.generate(4, (i) => AnimatedContainer(
              duration: const Duration(milliseconds: 300),
              margin: const EdgeInsets.symmetric(horizontal: 4),
              width: step == i ? 24 : 8, height: 8,
              decoration: BoxDecoration(
                color: step >= i ? AppTheme.primary : AppTheme.primaryLight.withValues(alpha: 0.3),
                borderRadius: BorderRadius.circular(4),
              ),
            ))),
            const SizedBox(height: 8),
            Text('${step + 1} / 4', style: Theme.of(context).textTheme.bodySmall),

            // Pages
            Expanded(
              child: PageView(
                controller: _pageCtrl,
                physics: const NeverScrollableScrollPhysics(),
                onPageChanged: (i) => ref.read(onboardingStepProvider.notifier).state = i,
                children: [
                  _StepPartner(partners: _partners, selected: _partner, onSelect: (p) => setState(() => _partner = p)),
                  _StepName(controller: _nameCtrl, partner: _partner),
                  _StepAge(selectedAge: _age, selectedGrade: _grade, ages: _ages, grades: _grades, onAge: (a) => setState(() { _age = a; _grade = _grades[_ages.indexOf(a)]; }), onGrade: (g) => setState(() { _grade = g; _age = _ages[_grades.indexOf(g)]; })),
                  _StepReady(name: _nameCtrl.text, partner: _partner, age: _age, grade: _grade, creating: _creating, onFinish: _finish),
                ],
              ),
            ),

            // Navigation
            Padding(
              padding: const EdgeInsets.fromLTRB(24, 0, 24, 32),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  if (step > 0)
                    TextButton(onPressed: () { _pageCtrl.previousPage(duration: const Duration(milliseconds: 300), curve: Curves.easeOut); }, child: const Text('上一步'))
                  else
                    const SizedBox(width: 80),
                  if (step < 3)
                    ElevatedButton(
                      onPressed: () { _pageCtrl.nextPage(duration: const Duration(milliseconds: 300), curve: Curves.easeOut); },
                      style: ElevatedButton.styleFrom(minimumSize: const Size(120, 56)),
                      child: const Text('下一步'),
                    ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ── Step 1: Choose Partner ───────────────────────────────────────────

class _StepPartner extends StatelessWidget {
  final List<Map<String, dynamic>> partners;
  final String selected;
  final ValueChanged<String> onSelect;
  const _StepPartner({required this.partners, required this.selected, required this.onSelect});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(32),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text('选一个AI伙伴吧！', style: Theme.of(context).textTheme.displayLarge),
          const SizedBox(height: 8),
          Text('TA会陪你一起成长', style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: AppTheme.textSecondary)),
          const SizedBox(height: 40),
          ...partners.map((p) {
            final isSelected = p['name'] == selected;
            return GestureDetector(
              onTap: () => onSelect(p['name']),
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 300),
                margin: const EdgeInsets.only(bottom: 12),
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: isSelected ? (p['color'] as Color).withValues(alpha: 0.15) : AppTheme.surface,
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(color: isSelected ? (p['color'] as Color) : Colors.transparent, width: 2),
                ),
                child: Row(
                  children: [
                    Container(width: 56, height: 56, decoration: BoxDecoration(color: (p['color'] as Color).withValues(alpha: 0.2), borderRadius: BorderRadius.circular(16)), child: Center(child: Text(p['emoji'] as String, style: const TextStyle(fontSize: 28)))),
                    const SizedBox(width: 16),
                    Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      Text(p['name'] as String, style: Theme.of(context).textTheme.headlineMedium),
                      Text(p['desc'] as String, style: Theme.of(context).textTheme.bodySmall),
                    ])),
                    if (isSelected) Icon(Icons.check_circle, color: p['color'] as Color, size: 28),
                  ],
                ),
              ),
            );
          }),
        ],
      ),
    );
  }
}

// ── Step 2: Name ──────────────────────────────────────────────────────

class _StepName extends StatelessWidget {
  final TextEditingController controller;
  final String partner;
  const _StepName({required this.controller, required this.partner});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(32),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Text('💬', style: TextStyle(fontSize: 64)),
          const SizedBox(height: 16),
          Text('$partner: "嗨！你叫什么名字呀？"', style: Theme.of(context).textTheme.headlineMedium, textAlign: TextAlign.center),
          const SizedBox(height: 32),
          TextField(
            controller: controller,
            textCapitalization: TextCapitalization.words,
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.displayLarge,
            decoration: const InputDecoration(hintText: '你的小名', border: InputBorder.none),
            autofocus: true,
          ),
        ],
      ),
    );
  }
}

// ── Step 3: Age ───────────────────────────────────────────────────────

class _StepAge extends StatelessWidget {
  final int selectedAge;
  final String selectedGrade;
  final List<int> ages;
  final List<String> grades;
  final ValueChanged<int> onAge;
  final ValueChanged<String> onGrade;
  const _StepAge({required this.selectedAge, required this.selectedGrade, required this.ages, required this.grades, required this.onAge, required this.onGrade});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(32),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text('你多大了？', style: Theme.of(context).textTheme.displayLarge),
          const SizedBox(height: 32),
          Wrap(spacing: 12, runSpacing: 12, alignment: WrapAlignment.center, children: ages.map((a) => GestureDetector(
            onTap: () => onAge(a),
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 200),
              width: 72, height: 72,
              decoration: BoxDecoration(
                color: a == selectedAge ? AppTheme.primary : AppTheme.surface,
                borderRadius: BorderRadius.circular(20),
                border: Border.all(color: a == selectedAge ? AppTheme.primary : AppTheme.primaryLight.withValues(alpha: 0.3), width: 2),
              ),
              child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
                Text('$a', style: TextStyle(fontSize: 24, fontWeight: FontWeight.w700, color: a == selectedAge ? Colors.white : AppTheme.textPrimary)),
                Text('岁', style: TextStyle(fontSize: 12, color: a == selectedAge ? Colors.white70 : AppTheme.textSecondary)),
              ]),
            ),
          )).toList()),
          const SizedBox(height: 32),
          Text('${selectedGrade}的小探险家！', style: Theme.of(context).textTheme.headlineMedium),
          DropdownButtonFormField<String>(
            value: selectedGrade,
            items: grades.map((g) => DropdownMenuItem(value: g, child: Text(g))).toList(),
            onChanged: (v) { if (v != null) onGrade(v); },
            decoration: const InputDecoration(prefixIcon: Icon(Icons.school)),
          ),
        ],
      ),
    );
  }
}

// ── Step 4: Ready ─────────────────────────────────────────────────────

class _StepReady extends StatelessWidget {
  final String name;
  final String partner;
  final int age;
  final String grade;
  final bool creating;
  final VoidCallback onFinish;
  const _StepReady({required this.name, required this.partner, required this.age, required this.grade, required this.creating, required this.onFinish});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(32),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Text('🚀', style: TextStyle(fontSize: 80)),
          const SizedBox(height: 24),
          Text('准备就绪！', style: Theme.of(context).textTheme.displayLarge),
          const SizedBox(height: 16),
          Container(
            padding: const EdgeInsets.all(24),
            decoration: BoxDecoration(color: AppTheme.surfaceWarm, borderRadius: BorderRadius.circular(20)),
            child: Column(children: [
              _infoRow('伙伴', partner),
              _infoRow('名字', name),
              _infoRow('年龄', '$age 岁 / $grade'),
            ]),
          ),
          const SizedBox(height: 32),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: creating ? null : onFinish,
              child: creating ? const SizedBox(height: 24, width: 24, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white)) : const Text('开始冒险！🌟'),
            ),
          ),
        ],
      ),
    );
  }

  Widget _infoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
        Text(label, style: const TextStyle(color: AppTheme.textSecondary, fontSize: 15)),
        Text(value, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 16)),
      ]),
    );
  }
}

// ══════════════════════════════════════════════════════════════════════
// Main Home — after onboarding
// ══════════════════════════════════════════════════════════════════════

class _MainHome extends ConsumerWidget {
  const _MainHome();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final child = ref.watch(childProvider)!;
    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            const SizedBox(height: 16),
            Row(children: [
              Text('Hi, ${child.nickname}！👋', style: Theme.of(context).textTheme.displayLarge),
              const Spacer(),
              TextButton.icon(onPressed: () => _logout(ref), icon: const Icon(Icons.exit_to_app, size: 18), label: const Text('换角色')),
            ]),
            const SizedBox(height: 4),
            Text('今天想去哪探险？', style: Theme.of(context).textTheme.headlineMedium?.copyWith(color: AppTheme.textSecondary)),
            const SizedBox(height: 32),
            _PromptCard(emoji: '💬', title: '聊聊天', subtitle: '和你的AI伙伴$child.nickname聊天', color: AppTheme.primary, onTap: () {
              showModalBottomSheet(context: context, isScrollControlled: true, backgroundColor: Colors.transparent, builder: (_) => const ChatSheet());
            }),
            const SizedBox(height: 16),
            _PromptCard(emoji: '📖', title: '看故事', subtitle: '探索属于你的冒险故事', color: AppTheme.secondary, onTap: () => context.go('/story')),
            const SizedBox(height: 16),
            _PromptCard(emoji: '🌱', title: '成长花园', subtitle: '看看你的知识花园吧', color: const Color(0xFF2196F3), onTap: () => context.go('/garden')),
          ]),
        ),
      ),
    );
  }

  void _logout(WidgetRef ref) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('child_id');
    ref.read(childProvider.notifier).state = null;
    ref.read(onboardingStepProvider.notifier).state = 0;
  }
}

class _PromptCard extends StatelessWidget {
  final String emoji, title, subtitle;
  final Color color;
  final VoidCallback onTap;
  const _PromptCard({required this.emoji, required this.title, required this.subtitle, required this.color, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Card(
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Row(children: [
            Container(width: 56, height: 56, decoration: BoxDecoration(color: color.withValues(alpha: 0.15), borderRadius: BorderRadius.circular(16)), child: Center(child: Text(emoji, style: const TextStyle(fontSize: 28)))),
            const SizedBox(width: 16),
            Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(title, style: Theme.of(context).textTheme.headlineMedium),
              const SizedBox(height: 4),
              Text(subtitle, style: Theme.of(context).textTheme.bodySmall),
            ])),
            const Icon(Icons.chevron_right, color: AppTheme.textSecondary),
          ]),
        ),
      ),
    );
  }
}
