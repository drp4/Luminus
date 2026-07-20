import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/services/api_client.dart';
import '../../../core/models/app_models.dart';
import '../../../core/theme/app_theme.dart';
import '../../home/views/home_screen.dart';

class GardenScreen extends ConsumerStatefulWidget {
  const GardenScreen({super.key});
  @override
  ConsumerState<GardenScreen> createState() => _GardenScreenState();
}

class _GardenScreenState extends ConsumerState<GardenScreen> with SingleTickerProviderStateMixin {
  GardenData? _garden;
  bool _loading = true;
  late final AnimationController _sunCtrl;

  @override
  void initState() {
    super.initState();
    _sunCtrl = AnimationController(vsync: this, duration: const Duration(seconds: 4))..repeat();
    _load();
  }

  @override
  void dispose() {
    _sunCtrl.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    final child = ref.read(childProvider);
    if (child == null) { setState(() => _loading = false); return; }
    try {
      final res = await ref.read(apiClientProvider).getGarden(child.id);
      setState(() { _garden = GardenData.fromJson(res); _loading = false; });
    } catch (_) { setState(() => _loading = false); }
  }

  @override
  Widget build(BuildContext context) {
    final child = ref.watch(childProvider);
    if (_loading) return Scaffold(appBar: AppBar(title: const Text('成长花园')), body: const Center(child: CircularProgressIndicator()));
    if (child == null) return Scaffold(appBar: AppBar(title: const Text('成长花园')), body: Center(child: Text('先去首页创建角色吧~', style: Theme.of(context).textTheme.bodyLarge)));

    final garden = _garden;
    return Scaffold(
      appBar: AppBar(title: Text('${child.nickname}的花园')),
      body: RefreshIndicator(
        onRefresh: _load,
        child: ListView(padding: const EdgeInsets.all(20), children: [
          _SkyHeader(sunCtrl: _sunCtrl, gardenLevel: garden?.gardenLevel ?? 1, soilQuality: garden?.soilQuality ?? 0.5, memories: garden?.totalMemories ?? 0),
          const SizedBox(height: 28),
          if (garden == null || garden.plants.isEmpty)
            _EmptyGarden()
          else ...[
            Text('🌱 兴趣植物', style: Theme.of(context).textTheme.headlineMedium),
            const SizedBox(height: 4),
            Text('每颗种子都来自你的一次好奇心', style: Theme.of(context).textTheme.bodySmall),
            const SizedBox(height: 16),
            ...garden.plants.map((p) => _PlantCard(plant: p)),
            const SizedBox(height: 28),
            _GardenStats(garden: garden),
          ],
        ]),
      ),
    );
  }
}

// ── Sky Header ────────────────────────────────────────────────────────

class _SkyHeader extends StatelessWidget {
  final AnimationController sunCtrl;
  final int gardenLevel;
  final double soilQuality;
  final int memories;
  const _SkyHeader({required this.sunCtrl, required this.gardenLevel, required this.soilQuality, required this.memories});

  static const _levels = [
    {'icon': '🌰', 'label': '种子'},
    {'icon': '🌱', 'label': '嫩芽'},
    {'icon': '🌿', 'label': '小树'},
    {'icon': '🪴', 'label': '花园'},
    {'icon': '🌳', 'label': '森林'},
  ];

  @override
  Widget build(BuildContext context) {
    final lv = _levels[gardenLevel - 1];
    return Container(
      padding: const EdgeInsets.all(28),
      decoration: BoxDecoration(
        gradient: const LinearGradient(colors: [Color(0xFFFFF8F0), Color(0xFFFFF0E0), Color(0xFFFFE8D0)], begin: Alignment.topCenter, end: Alignment.bottomCenter),
        borderRadius: BorderRadius.circular(24),
      ),
      child: Column(children: [
        // Animated sun
        AnimatedBuilder(
          animation: sunCtrl,
          builder: (_, __) => Transform.rotate(angle: sunCtrl.value * 0.3, child: const Text('☀️', style: TextStyle(fontSize: 60))),
        ),
        const SizedBox(height: 12),
        Text(lv['icon']!, style: const TextStyle(fontSize: 56)),
        const SizedBox(height: 8),
        Text('花园等级 $gardenLevel — ${lv['label']}', style: Theme.of(context).textTheme.headlineMedium),
        const SizedBox(height: 12),
        ClipRRect(
          borderRadius: BorderRadius.circular(6),
          child: LinearProgressIndicator(value: soilQuality, backgroundColor: AppTheme.surfaceWarm, color: AppTheme.secondary, minHeight: 10),
        ),
        const SizedBox(height: 8),
        Text('$memories 条记忆滋养着这片花园', style: Theme.of(context).textTheme.bodySmall),
      ]),
    );
  }
}

// ── Empty Garden ──────────────────────────────────────────────────────

class _EmptyGarden extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(36),
      decoration: BoxDecoration(color: AppTheme.surfaceWarm, borderRadius: BorderRadius.circular(24)),
      child: Column(children: [
        const Text('🪹', style: TextStyle(fontSize: 56)),
        const SizedBox(height: 16),
        Text('花园还空着呢', style: Theme.of(context).textTheme.headlineMedium),
        const SizedBox(height: 8),
        Text('去右下角的 🦕 伙伴聊聊天吧\n每次对话都会种下一颗种子', style: Theme.of(context).textTheme.bodySmall, textAlign: TextAlign.center),
      ]),
    );
  }
}

// ── Plant Card ────────────────────────────────────────────────────────

class _PlantCard extends StatefulWidget {
  final PlantData plant;
  const _PlantCard({required this.plant});
  @override
  State<_PlantCard> createState() => _PlantCardState();
}

class _PlantCardState extends State<_PlantCard> with SingleTickerProviderStateMixin {
  late final AnimationController _growCtrl;
  late final Animation<double> _growAnim;
  bool _expanded = false;

  @override
  void initState() {
    super.initState();
    _growCtrl = AnimationController(vsync: this, duration: const Duration(milliseconds: 800));
    _growAnim = CurvedAnimation(parent: _growCtrl, curve: Curves.elasticOut);
    Future.delayed(const Duration(milliseconds: 300), () { if (mounted) _growCtrl.forward(); });
  }

  @override
  void dispose() {
    _growCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final p = widget.plant;
    final color = Color(int.parse('FF${p.color.replaceAll('#', '')}', radix: 16));

    return ScaleTransition(
      scale: _growAnim,
      child: Card(
        margin: const EdgeInsets.only(bottom: 12),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        child: InkWell(
          onTap: () => setState(() => _expanded = !_expanded),
          borderRadius: BorderRadius.circular(20),
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 400),
            padding: const EdgeInsets.all(20),
            child: Column(children: [
              Row(children: [
                Container(
                  width: p.size * 0.9, height: p.size * 0.9,
                  decoration: BoxDecoration(gradient: LinearGradient(colors: [color.withValues(alpha: 0.25), color.withValues(alpha: 0.08)]), borderRadius: BorderRadius.circular(18)),
                  child: Center(child: Text(p.emoji, style: TextStyle(fontSize: p.size * 0.5))),
                ),
                const SizedBox(width: 18),
                Expanded(
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Text(p.topic, style: Theme.of(context).textTheme.headlineMedium),
                    const SizedBox(height: 6),
                    Row(children: [
                      _StageBadge(stage: p.stage),
                      const SizedBox(width: 10),
                      _TrendIcon(trend: p.trend),
                    ]),
                  ]),
                ),
                AnimatedRotation(turns: _expanded ? 0.5 : 0, duration: const Duration(milliseconds: 300), child: const Icon(Icons.keyboard_arrow_down, color: AppTheme.textSecondary)),
              ]),
              if (_expanded) ...[
                const SizedBox(height: 16),
                Container(
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(color: AppTheme.surfaceWarm, borderRadius: BorderRadius.circular(12)),
                  child: Row(children: [
                    _StatItem(icon: '💪', label: '强度', value: '${(p.weight * 100).toInt()}%'),
                    const SizedBox(width: 24),
                    _StatItem(icon: '📈', label: '趋势', value: p.trend == 'rising' ? '上升中' : p.trend == 'declining' ? '下降中' : '稳定'),
                    const SizedBox(width: 24),
                    _StatItem(icon: '🌱', label: '阶段', value: _stageName(p.stage)),
                  ]),
                ),
              ],
            ]),
          ),
        ),
      ),
    );
  }

  String _stageName(String s) {
    switch (s) { case 'blooming': return '盛开'; case 'growing': return '成长'; case 'sprout': return '发芽'; default: return '种子'; }
  }
}

class _StageBadge extends StatelessWidget {
  final String stage;
  const _StageBadge({required this.stage});
  @override
  Widget build(BuildContext context) {
    final config = switch (stage) {
      'blooming' => ('🌸 盛开', AppTheme.secondary, AppTheme.secondaryLight),
      'growing' => ('🪴 成长', const Color(0xFF2196F3), const Color(0xFFBBDEFB)),
      'sprout' => ('🌿 发芽', AppTheme.primaryLight, AppTheme.primaryLight.withValues(alpha: 0.3)),
      _ => ('🌱 种子', AppTheme.textSecondary, AppTheme.textSecondary.withValues(alpha: 0.15)),
    };
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(color: config.$3, borderRadius: BorderRadius.circular(10)),
      child: Text(config.$1, style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: config.$2)),
    );
  }
}

class _TrendIcon extends StatelessWidget {
  final String trend;
  const _TrendIcon({required this.trend});
  @override
  Widget build(BuildContext context) {
    switch (trend) {
      case 'rising': return const Row(mainAxisSize: MainAxisSize.min, children: [Icon(Icons.trending_up, color: AppTheme.secondary, size: 18), SizedBox(width: 2), Text('上升', style: TextStyle(fontSize: 12, color: AppTheme.secondary, fontWeight: FontWeight.w600))]);
      case 'declining': return const Row(mainAxisSize: MainAxisSize.min, children: [Icon(Icons.trending_down, color: Colors.grey, size: 18), SizedBox(width: 2), Text('下降', style: TextStyle(fontSize: 12, color: Colors.grey))]);
      default: return const Row(mainAxisSize: MainAxisSize.min, children: [Icon(Icons.trending_flat, color: AppTheme.primary, size: 18), SizedBox(width: 2), Text('稳定', style: TextStyle(fontSize: 12, color: AppTheme.primary, fontWeight: FontWeight.w600))]);
    }
  }
}

class _StatItem extends StatelessWidget {
  final String icon, label, value;
  const _StatItem({required this.icon, required this.label, required this.value});
  @override
  Widget build(BuildContext context) {
    return Column(children: [Text(icon, style: const TextStyle(fontSize: 20)), const SizedBox(height: 4), Text(value, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 14)), Text(label, style: Theme.of(context).textTheme.bodySmall)]);
  }
}

// ── Stats ─────────────────────────────────────────────────────────────

class _GardenStats extends StatelessWidget {
  final GardenData garden;
  const _GardenStats({required this.garden});
  @override
  Widget build(BuildContext context) {
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text('📊 成长数据', style: Theme.of(context).textTheme.headlineMedium),
      const SizedBox(height: 12),
      Row(children: [
        Expanded(child: _MiniStat(icon: '🪴', label: '兴趣植物', value: '${garden.plants.length}')),
        const SizedBox(width: 12),
        Expanded(child: _MiniStat(icon: '🧠', label: '长期记忆', value: '${garden.totalMemories}')),
        const SizedBox(width: 12),
        Expanded(child: _MiniStat(icon: '🌿', label: '土壤质量', value: '${(garden.soilQuality * 100).toInt()}%')),
      ]),
    ]);
  }
}

class _MiniStat extends StatelessWidget {
  final String icon, label, value;
  const _MiniStat({required this.icon, required this.label, required this.value});
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 18),
      decoration: BoxDecoration(color: AppTheme.surfaceWarm, borderRadius: BorderRadius.circular(16)),
      child: Column(children: [
        Text(icon, style: const TextStyle(fontSize: 28)),
        const SizedBox(height: 8),
        Text(value, style: Theme.of(context).textTheme.headlineMedium?.copyWith(fontSize: 22)),
        Text(label, style: Theme.of(context).textTheme.bodySmall),
      ]),
    );
  }
}
