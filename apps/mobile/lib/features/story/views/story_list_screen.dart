import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/services/api_client.dart';
import '../../../core/models/app_models.dart';
import '../../../core/theme/app_theme.dart';
import '../../home/views/home_screen.dart';

// ══════════════════════════════════════════════════════════════════════
// Story List — book-cover cards
// ══════════════════════════════════════════════════════════════════════

class StoryListScreen extends ConsumerStatefulWidget {
  const StoryListScreen({super.key});
  @override
  ConsumerState<StoryListScreen> createState() => _StoryListScreenState();
}

class _StoryListScreenState extends ConsumerState<StoryListScreen> {
  List<StoryData> _stories = [];
  bool _loading = true;
  bool _creating = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final child = ref.read(childProvider);
    if (child == null) return;
    setState(() => _loading = true);
    try {
      final res = await ref.read(apiClientProvider).getStories(child.id);
      setState(() {
        _stories = (res['stories'] as List<dynamic>?)?.map((s) => StoryData.fromJson(s)).toList() ?? [];
        _loading = false;
      });
    } catch (_) {
      setState(() => _loading = false);
    }
  }

  Future<void> _create() async {
    final child = ref.read(childProvider);
    if (child == null) return;
    setState(() => _creating = true);
    try {
      final res = await ref.read(apiClientProvider).createStory(child.id);
      setState(() {
        _stories.insert(0, StoryData.fromJson(res));
        _creating = false;
      });
    } catch (_) {
      setState(() => _creating = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('我的故事书')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _stories.isEmpty
              ? _EmptyLibrary(onCreate: _create, creating: _creating)
              : _StoryGrid(stories: _stories, onCreate: _create, creating: _creating),
    );
  }
}

class _EmptyLibrary extends StatelessWidget {
  final VoidCallback onCreate;
  final bool creating;
  const _EmptyLibrary({required this.onCreate, required this.creating});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(40),
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          Container(
            width: 120, height: 120,
            decoration: BoxDecoration(gradient: const LinearGradient(colors: [Color(0xFFFFB84D), Color(0xFFFF9500)]), borderRadius: BorderRadius.circular(30)),
            child: const Center(child: Text('📚', style: TextStyle(fontSize: 56))),
          ),
          const SizedBox(height: 28),
          Text('你的故事书还是空的', style: Theme.of(context).textTheme.headlineMedium),
          const SizedBox(height: 8),
          Text('AI会根据你的兴趣\n为你创作独一无二的冒险故事', style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: AppTheme.textSecondary), textAlign: TextAlign.center),
          const SizedBox(height: 36),
          SizedBox(
            width: 220,
            child: ElevatedButton.icon(
              onPressed: creating ? null : onCreate,
              icon: creating ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white)) : const Icon(Icons.auto_awesome),
              label: Text(creating ? '创作中...' : '创作第一本故事 🪄'),
            ),
          ),
        ]),
      ),
    );
  }
}

class _StoryGrid extends StatelessWidget {
  final List<StoryData> stories;
  final VoidCallback onCreate;
  final bool creating;
  const _StoryGrid({required this.stories, required this.onCreate, required this.creating});

  static const _coverGradients = [
    [Color(0xFF667eea), Color(0xFF764ba2)],
    [Color(0xFFf093fb), Color(0xFFf5576c)],
    [Color(0xFF4facfe), Color(0xFF00f2fe)],
    [Color(0xFF43e97b), Color(0xFF38f9d7)],
    [Color(0xFFfa709a), Color(0xFFfee140)],
    [Color(0xFFa18cd1), Color(0xFFfbc2eb)],
  ];

  @override
  Widget build(BuildContext context) {
    return RefreshIndicator(
      onRefresh: () async {},
      child: CustomScrollView(
        slivers: [
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 4),
              child: OutlinedButton.icon(
                onPressed: creating ? null : onCreate,
                icon: const Icon(Icons.auto_awesome, size: 18),
                label: Text(creating ? '创作中...' : '创作新故事'),
              ),
            ),
          ),
          SliverPadding(
            padding: const EdgeInsets.all(16),
            sliver: SliverGrid(
              gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(crossAxisCount: 2, mainAxisSpacing: 16, crossAxisSpacing: 16, childAspectRatio: 0.72),
              delegate: SliverChildBuilderDelegate(
                (ctx, i) {
                  final story = stories[i];
                  final gradient = _coverGradients[i % _coverGradients.length];
                  return _StoryCover(story: story, gradient: gradient);
                },
                childCount: stories.length,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _StoryCover extends StatelessWidget {
  final StoryData story;
  final List<Color> gradient;
  const _StoryCover({required this.story, required this.gradient});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () => context.push('/story/play/${story.id}'),
      child: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(colors: gradient, begin: Alignment.topLeft, end: Alignment.bottomRight),
          borderRadius: BorderRadius.circular(20),
          boxShadow: [BoxShadow(color: gradient.last.withValues(alpha: 0.4), blurRadius: 12, offset: const Offset(0, 6))],
        ),
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Spacer(),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
              decoration: BoxDecoration(color: Colors.white.withValues(alpha: 0.25), borderRadius: BorderRadius.circular(8)),
              child: Text(story.theme, style: const TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.w600)),
            ),
            const SizedBox(height: 8),
            Text(story.title, style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.w700, height: 1.3), maxLines: 2, overflow: TextOverflow.ellipsis),
            const SizedBox(height: 8),
            Row(children: [
              const Icon(Icons.menu_book, color: Colors.white70, size: 14),
              const SizedBox(width: 4),
              Text('${story.totalChapters}章', style: const TextStyle(color: Colors.white70, fontSize: 12)),
              const Spacer(),
              if (story.status == 'ready') const Text('继续 ▶', style: TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.w700)),
            ]),
            const SizedBox(height: 12),
            ClipRRect(
              borderRadius: BorderRadius.circular(4),
              child: LinearProgressIndicator(value: story.status == 'completed' ? 1.0 : 0.3, backgroundColor: Colors.white24, color: Colors.white, minHeight: 3),
            ),
          ],
        ),
      ),
    );
  }
}

// ══════════════════════════════════════════════════════════════════════
// Story Play — page-turn reading
// ══════════════════════════════════════════════════════════════════════

class StoryPlayScreen extends ConsumerStatefulWidget {
  final String storyId;
  const StoryPlayScreen({super.key, required this.storyId});
  @override
  ConsumerState<StoryPlayScreen> createState() => _StoryPlayScreenState();
}

class _StoryPlayScreenState extends ConsumerState<StoryPlayScreen> {
  final _pageCtrl = PageController();
  final _scenes = <SceneData>[];
  String _title = '';
  int _currentPage = 0;
  bool _loading = true;
  bool _generating = false;
  bool _finished = false;

  @override
  void dispose() {
    _pageCtrl.dispose();
    super.dispose();
  }

  @override
  void initState() {
    super.initState();
    _loadStory();
  }

  Future<void> _loadStory() async {
    try {
      final api = ref.read(apiClientProvider);
      final res = await api.getStory(widget.storyId);
      final chapters = res['chapters'] as List<dynamic>? ?? [];
      final loaded = <SceneData>[];
      for (final ch in chapters) {
        for (final sc in (ch['scenes'] as List<dynamic>? ?? [])) {
          loaded.add(SceneData.fromJson(sc));
        }
      }
      setState(() {
        _title = res['title'] ?? '';
        _scenes.addAll(loaded);
        _loading = false;
      });
    } catch (_) {
      setState(() => _loading = false);
    }
  }

  Future<void> _generateNext() async {
    setState(() => _generating = true);
    try {
      final api = ref.read(apiClientProvider);
      final ch = (_scenes.length ~/ 3) + 1;
      final si = (_scenes.length % 3) + 1;
      final res = await api.generateScene(widget.storyId, chapter: ch, scene: si);
      setState(() {
        _scenes.add(SceneData.fromJson(res));
        _generating = false;
      });
      _pageCtrl.animateToPage(_scenes.length - 1, duration: const Duration(milliseconds: 500), curve: Curves.easeInOut);
    } catch (_) {
      setState(() => _generating = false);
    }
  }

  Future<void> _makeChoice(String choice) async {
    final child = ref.read(childProvider);
    if (child == null) return;
    setState(() => _generating = true);
    try {
      final res = await ref.read(apiClientProvider).makeChoice(widget.storyId, child.id, choice);
      if (res['finished'] == true) {
        setState(() { _finished = true; _generating = false; });
        return;
      }
      setState(() {
        _scenes.add(SceneData.fromJson(res));
        _generating = false;
      });
      _pageCtrl.animateToPage(_scenes.length - 1, duration: const Duration(milliseconds: 500), curve: Curves.easeInOut);
    } catch (_) {
      setState(() => _generating = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) return Scaffold(appBar: AppBar(title: const Text('加载中...')), body: const Center(child: CircularProgressIndicator()));

    return Scaffold(
      extendBodyBehindAppBar: true,
      appBar: AppBar(
        title: Text(_title, style: const TextStyle(fontSize: 18)),
        backgroundColor: Colors.transparent,
        elevation: 0,
        actions: [
          Text('${_currentPage + 1}/${_scenes.length + (_generating ? 1 : 0)}', style: Theme.of(context).textTheme.bodySmall),
          const SizedBox(width: 16),
        ],
      ),
      body: _finished ? _TheEnd(onBack: () => Navigator.pop(context)) : _scenes.isEmpty ? Center(
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          const Text('📖', style: TextStyle(fontSize: 72)),
          const SizedBox(height: 16),
          Text('准备开始冒险...', style: Theme.of(context).textTheme.headlineMedium),
          const SizedBox(height: 24),
          ElevatedButton.icon(onPressed: _generateNext, icon: const Icon(Icons.play_arrow), label: const Text('开始阅读')),
        ]),
      ) : Column(
        children: [
          Expanded(
            child: PageView.builder(
              controller: _pageCtrl,
              onPageChanged: (i) => setState(() => _currentPage = i),
              itemCount: _scenes.length + (_generating ? 1 : 0),
              itemBuilder: (ctx, i) {
                if (_generating && i == _scenes.length) return const Center(child: CircularProgressIndicator());
                return _PageView(scene: _scenes[i], pageNum: i + 1, total: _scenes.length);
              },
            ),
          ),
          if (_currentPage == _scenes.length - 1 && !_finished)
            _ChoiceBar(choices: _scenes.last.choices, loading: _generating, onChoose: _makeChoice),
        ],
      ),
    );
  }
}

class _PageView extends StatelessWidget {
  final SceneData scene;
  final int pageNum, total;
  const _PageView({required this.scene, required this.pageNum, required this.total});

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(28, 100, 28, 28),
      child: Column(children: [
        Text(scene.text, style: Theme.of(context).textTheme.bodyLarge?.copyWith(height: 1.8, fontSize: 17)),
        if (scene.knowledgePoints.isNotEmpty) ...[
          const SizedBox(height: 28),
          _KnowledgeCard(points: scene.knowledgePoints),
        ],
        const SizedBox(height: 100),
      ]),
    );
  }
}

class _KnowledgeCard extends StatefulWidget {
  final List<KnowledgePointData> points;
  const _KnowledgeCard({required this.points});
  @override
  State<_KnowledgeCard> createState() => _KnowledgeCardState();
}

class _KnowledgeCardState extends State<_KnowledgeCard> with SingleTickerProviderStateMixin {
  bool _revealed = false;
  late final AnimationController _ctrl;
  late final Animation<double> _scale;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(vsync: this, duration: const Duration(milliseconds: 600));
    _scale = CurvedAnimation(parent: _ctrl, curve: Curves.elasticOut);
    Future.delayed(const Duration(milliseconds: 800), () { if (mounted) { setState(() => _revealed = true); _ctrl.forward(); } });
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return ScaleTransition(
      scale: _scale,
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(color: AppTheme.secondaryLight.withValues(alpha: 0.12), borderRadius: BorderRadius.circular(16), border: Border.all(color: AppTheme.secondaryLight.withValues(alpha: 0.3))),
        child: Row(children: [
          AnimatedRotation(turns: _revealed ? 0 : -0.25, duration: const Duration(milliseconds: 600), child: const Text('💡', style: TextStyle(fontSize: 28))),
          const SizedBox(width: 12),
          Expanded(
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text('学到了！', style: Theme.of(context).textTheme.headlineMedium?.copyWith(color: AppTheme.secondary, fontSize: 16)),
              const SizedBox(height: 4),
              ...widget.points.map((k) => Padding(
                padding: const EdgeInsets.only(bottom: 2),
                child: Text('${k.concept}${k.vocabulary != null ? "（${k.vocabulary}）" : ""}', style: Theme.of(context).textTheme.bodySmall),
              )),
            ]),
          ),
        ]),
      ),
    );
  }
}

class _ChoiceBar extends StatelessWidget {
  final List<ChoiceData> choices;
  final bool loading;
  final Function(String) onChoose;
  const _ChoiceBar({required this.choices, required this.loading, required this.onChoose});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 28),
      decoration: BoxDecoration(color: AppTheme.surface, boxShadow: [BoxShadow(color: Colors.black.withValues(alpha: 0.06), blurRadius: 12, offset: const Offset(0, -4))], borderRadius: const BorderRadius.vertical(top: Radius.circular(24))),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [const Text('👉', style: TextStyle(fontSize: 20)), const SizedBox(width: 8), Text('你决定怎么做？', style: Theme.of(context).textTheme.headlineMedium)]),
        const SizedBox(height: 12),
        ...choices.map((c) => Padding(
          padding: const EdgeInsets.only(bottom: 8),
          child: SizedBox(
            width: double.infinity,
            child: OutlinedButton(
              onPressed: loading ? null : () => onChoose(c.text),
              style: OutlinedButton.styleFrom(alignment: Alignment.centerLeft, padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)), backgroundColor: AppTheme.surfaceWarm.withValues(alpha: 0.5)),
              child: Text(c.text, style: const TextStyle(fontSize: 16, height: 1.4)),
            ),
          ),
        )),
      ]),
    );
  }
}

class _TheEnd extends StatelessWidget {
  final VoidCallback onBack;
  const _TheEnd({required this.onBack});
  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(40),
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          const Text('🎉', style: TextStyle(fontSize: 80)),
          const SizedBox(height: 20),
          Text('故事结束！', style: Theme.of(context).textTheme.displayLarge),
          const SizedBox(height: 8),
          Text('你完成了一次精彩的冒险', style: Theme.of(context).textTheme.bodyLarge?.copyWith(color: AppTheme.textSecondary)),
          const SizedBox(height: 32),
          SizedBox(width: 200, child: ElevatedButton(onPressed: onBack, child: const Text('回到书架 📚'))),
        ]),
      ),
    );
  }
}
