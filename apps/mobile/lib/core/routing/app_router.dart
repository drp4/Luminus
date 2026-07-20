import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../features/home/views/home_screen.dart';
import '../../features/story/views/story_list_screen.dart';
import '../../features/garden/views/garden_screen.dart';
import '../../features/chat/views/chat_sheet.dart';

final _rootNavigatorKey = GlobalKey<NavigatorState>();

final appRouter = GoRouter(
  navigatorKey: _rootNavigatorKey,
  initialLocation: '/home',
  routes: [
    ShellRoute(
      builder: (context, state, child) => AppShell(child: child),
      routes: [
        GoRoute(path: '/home', pageBuilder: (ctx, state) => const NoTransitionPage(child: HomeScreen())),
        GoRoute(path: '/story', pageBuilder: (ctx, state) => const NoTransitionPage(child: StoryListScreen())),
        GoRoute(path: '/garden', pageBuilder: (ctx, state) => const NoTransitionPage(child: GardenScreen())),
      ],
    ),
    GoRoute(
      path: '/story/play/:storyId',
      parentNavigatorKey: _rootNavigatorKey,
      builder: (ctx, state) => StoryPlayScreen(storyId: state.pathParameters['storyId']!),
    ),
  ],
);

/// Root shell with bottom nav + floating partner button
class AppShell extends StatefulWidget {
  final Widget child;
  const AppShell({super.key, required this.child});
  @override
  State<AppShell> createState() => _AppShellState();
}

class _AppShellState extends State<AppShell> with SingleTickerProviderStateMixin {
  late final AnimationController _bounceCtrl;

  @override
  void initState() {
    super.initState();
    _bounceCtrl = AnimationController(vsync: this, duration: const Duration(seconds: 2))..repeat(reverse: true);
  }

  @override
  void dispose() {
    _bounceCtrl.dispose();
    super.dispose();
  }

  int _currentIndex() {
    final loc = GoRouterState.of(context).uri.path;
    if (loc.startsWith('/story')) return 1;
    if (loc.startsWith('/garden')) return 2;
    return 0;
  }

  void _openChat() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => const ChatSheet(),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Stack(
        children: [
          widget.child,
          Positioned(
            right: 20,
            bottom: 8,
            child: AnimatedBuilder(
              animation: _bounceCtrl,
              builder: (_, __) => Transform.translate(
                offset: Offset(0, -3 * _bounceCtrl.value),
                child: GestureDetector(
                  onTap: _openChat,
                  child: Container(
                    width: 60, height: 60,
                    decoration: BoxDecoration(
                      gradient: const LinearGradient(colors: [Color(0xFFFFB84D), Color(0xFFFF9500)]),
                      shape: BoxShape.circle,
                      boxShadow: [BoxShadow(color: const Color(0xFFFF9500).withValues(alpha: 0.4), blurRadius: 16, offset: const Offset(0, 4))],
                    ),
                    child: const Center(child: Text('🦕', style: TextStyle(fontSize: 32))),
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
      bottomNavigationBar: SizedBox(
        height: 72,
        child: BottomNavigationBar(
          currentIndex: _currentIndex(),
          onTap: (i) {
            switch (i) {
              case 0: context.go('/home');
              case 1: context.go('/story');
              case 2: context.go('/garden');
            }
          },
          iconSize: 28,
          items: const [
            BottomNavigationBarItem(icon: Icon(Icons.explore_rounded), label: '探索'),
            BottomNavigationBarItem(icon: Icon(Icons.auto_stories_rounded), label: '故事'),
            BottomNavigationBarItem(icon: Icon(Icons.psychology_rounded), label: '花园'),
          ],
        ),
      ),
    );
  }
}
