import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/services/api_client.dart';
import '../../../core/models/app_models.dart';
import '../../../core/theme/app_theme.dart';
import '../../home/views/home_screen.dart';

/// Bottom sheet chat — slides up from partner button
class ChatSheet extends ConsumerStatefulWidget {
  const ChatSheet({super.key});
  @override
  ConsumerState<ChatSheet> createState() => _ChatSheetState();
}

class _ChatSheetState extends ConsumerState<ChatSheet> {
  final _msgCtrl = TextEditingController();
  final _scrollCtrl = ScrollController();
  final _messages = <ChatMessage>[];
  bool _sending = false;
  bool _teacherMode = false;

  static const _suggestions = [
    {'emoji': '🦕', 'text': '恐龙是怎么灭绝的？'},
    {'emoji': '🚀', 'text': '人可以去火星吗？'},
    {'emoji': '🌊', 'text': '海里最大的动物是什么？'},
    {'emoji': '🌈', 'text': '彩虹是怎么形成的？'},
    {'emoji': '🦋', 'text': '毛毛虫怎么变成蝴蝶？'},
    {'emoji': '⭐', 'text': '星星为什么会发光？'},
  ];

  @override
  void dispose() {
    _msgCtrl.dispose();
    _scrollCtrl.dispose();
    super.dispose();
  }

  Future<void> _send([String? preset]) async {
    final text = (preset ?? _msgCtrl.text).trim();
    if (text.isEmpty) return;
    final child = ref.read(childProvider);
    if (child == null) return;

    setState(() {
      _messages.add(ChatMessage(role: 'user', content: text, timestamp: DateTime.now()));
      _sending = true;
    });
    _msgCtrl.clear();
    _scrollDown();

    try {
      final api = ref.read(apiClientProvider);
      final history = _messages.sublist(0, _messages.length - 1).map((m) => m.toApi()).toList();
      final res = await api.sendMessage(child.id, text, history: history);
      final reply = res['message'] ?? '';
      setState(() {
        _messages.add(ChatMessage(role: 'assistant', content: reply, timestamp: DateTime.now()));
        _sending = false;
        _teacherMode = _detectTeacher(reply);
      });
      _scrollDown();
    } catch (_) {
      setState(() => _sending = false);
    }
  }

  bool _detectTeacher(String text) {
    return text.contains('？') || text.contains('想想') || text.contains('你觉得');
  }

  void _scrollDown() {
    Future.delayed(const Duration(milliseconds: 100), () {
      if (_scrollCtrl.hasClients) _scrollCtrl.animateTo(_scrollCtrl.position.maxScrollExtent, duration: const Duration(milliseconds: 300), curve: Curves.easeOut);
    });
  }

  List<Map<String, String>> get _filteredSuggestions {
    if (_messages.isEmpty) return _suggestions;
    // Show shortened list after conversation starts
    return _suggestions.sublist(0, 3);
  }

  @override
  Widget build(BuildContext context) {
    return DraggableScrollableSheet(
      initialChildSize: 0.7,
      minChildSize: 0.35,
      maxChildSize: 0.92,
      expand: false,
      builder: (ctx, scrollCtrl) => Container(
        decoration: const BoxDecoration(
          color: AppTheme.background,
          borderRadius: BorderRadius.vertical(top: Radius.circular(28)),
        ),
        child: Column(
          children: [
            // Drag handle + mode indicator
            Container(
              padding: const EdgeInsets.fromLTRB(20, 12, 20, 0),
              child: Column(
                children: [
                  Container(width: 40, height: 4, decoration: BoxDecoration(color: Colors.grey.shade300, borderRadius: BorderRadius.circular(2))),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
                        decoration: BoxDecoration(
                          color: _teacherMode ? const Color(0xFF2196F3).withValues(alpha: 0.1) : AppTheme.primaryLight.withValues(alpha: 0.15),
                          borderRadius: BorderRadius.circular(20),
                        ),
                        child: Row(mainAxisSize: MainAxisSize.min, children: [
                          Text(_teacherMode ? '🔍' : '💬', style: const TextStyle(fontSize: 14)),
                          const SizedBox(width: 4),
                          Text(_teacherMode ? '探索中' : '聊天中', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: _teacherMode ? const Color(0xFF2196F3) : AppTheme.primary)),
                        ]),
                      ),
                      const Spacer(),
                      IconButton(icon: const Icon(Icons.close, size: 22), onPressed: () => Navigator.pop(context)),
                    ],
                  ),
                ],
              ),
            ),

            // Messages
            Expanded(
              child: _messages.isEmpty
                  ? _EmptySuggestions(suggestions: _filteredSuggestions, onTap: _send)
                  : ListView.builder(
                      controller: _scrollCtrl,
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                      itemCount: _messages.length + (_sending ? 1 : 0),
                      itemBuilder: (ctx, i) {
                        if (_sending && i == _messages.length) return const _TypingBubble();
                        return _Bubble(message: _messages[i]);
                      },
                    ),
            ),

            // Input bar
            _InputBar(controller: _msgCtrl, sending: _sending, onSend: () => _send(), suggestions: _filteredSuggestions, onSuggestion: _send),
          ],
        ),
      ),
    );
  }
}

// ── Empty state with topic suggestions ────────────────────────────────

class _EmptySuggestions extends StatelessWidget {
  final List<Map<String, String>> suggestions;
  final Function(String) onTap;
  const _EmptySuggestions({required this.suggestions, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const SizedBox(height: 8),
          Container(
            width: 80,
            height: 80,
            decoration: BoxDecoration(
              gradient: const LinearGradient(colors: [Color(0xFFFFB84D), Color(0xFFFF9500)]),
              shape: BoxShape.circle,
            ),
            child: const Center(child: Text('🦕', style: TextStyle(fontSize: 40))),
          ),
          const SizedBox(height: 20),
          Text('想聊点什么呢？', style: Theme.of(context).textTheme.headlineMedium),
          const SizedBox(height: 8),
          Text('选一个话题开始吧', style: Theme.of(context).textTheme.bodySmall),
          const SizedBox(height: 24),
          for (final s in suggestions)
            Padding(
              padding: const EdgeInsets.only(bottom: 10),
              child: SizedBox(
                width: double.infinity,
                child: OutlinedButton(
                  onPressed: () => onTap(s['text']!),
                  style: OutlinedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                    side: BorderSide(color: AppTheme.primaryLight.withValues(alpha: 0.3)),
                  ),
                  child: Align(
                    alignment: Alignment.centerLeft,
                    child: Text('${s['emoji']}  ${s['text']}', style: const TextStyle(fontSize: 16)),
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }
}

// ── Chat bubble ────────────────────────────────────────────────────────

class _Bubble extends StatelessWidget {
  final ChatMessage message;
  const _Bubble({required this.message});

  @override
  Widget build(BuildContext context) {
    final isUser = message.role == 'user';
    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.78),
        margin: const EdgeInsets.only(bottom: 10),
        padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 12),
        decoration: BoxDecoration(
          gradient: isUser ? null : const LinearGradient(colors: [Color(0xFFFFB84D), Color(0xFFFFA01A)]),
          color: isUser ? AppTheme.surface : null,
          borderRadius: BorderRadius.only(
            topLeft: const Radius.circular(22),
            topRight: const Radius.circular(22),
            bottomLeft: isUser ? const Radius.circular(22) : const Radius.circular(6),
            bottomRight: isUser ? const Radius.circular(6) : const Radius.circular(22),
          ),
          boxShadow: [BoxShadow(color: Colors.black.withValues(alpha: isUser ? 0.04 : 0.12), blurRadius: 8, offset: const Offset(0, 2))],
        ),
        child: Text(message.content, style: TextStyle(fontSize: 16, height: 1.5, color: isUser ? AppTheme.textPrimary : Colors.white)),
      ),
    );
  }
}

class _TypingBubble extends StatelessWidget {
  const _TypingBubble();
  @override
  Widget build(BuildContext context) {
    return const Align(
      alignment: Alignment.centerLeft,
      child: Padding(
        padding: EdgeInsets.only(bottom: 10, left: 4),
        child: Text('💭 ...', style: TextStyle(fontSize: 20)),
      ),
    );
  }
}

// ── Input bar ──────────────────────────────────────────────────────────

class _InputBar extends StatefulWidget {
  final TextEditingController controller;
  final bool sending;
  final VoidCallback onSend;
  final List<Map<String, String>> suggestions;
  final Function(String) onSuggestion;
  const _InputBar({required this.controller, required this.sending, required this.onSend, required this.suggestions, required this.onSuggestion});
  @override
  State<_InputBar> createState() => _InputBarState();
}

class _InputBarState extends State<_InputBar> {
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
      decoration: BoxDecoration(color: AppTheme.surface, boxShadow: [BoxShadow(color: Colors.black.withValues(alpha: 0.04), blurRadius: 8, offset: const Offset(0, -2))]),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Quick suggestion chips
          if (widget.suggestions.isNotEmpty)
            SizedBox(
              height: 36,
              child: ListView.separated(
                scrollDirection: Axis.horizontal,
                itemCount: widget.suggestions.length,
                separatorBuilder: (_, __) => const SizedBox(width: 8),
                itemBuilder: (_, i) => GestureDetector(
                  onTap: () => widget.onSuggestion(widget.suggestions[i]['text']!),
                  child: Chip(
                    avatar: Text(widget.suggestions[i]['emoji']!, style: const TextStyle(fontSize: 14)),
                    label: Text(widget.suggestions[i]['text']!, style: const TextStyle(fontSize: 13)),
                    backgroundColor: AppTheme.surfaceWarm,
                    side: BorderSide.none,
                    padding: EdgeInsets.zero,
                    materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                  ),
                ),
              ),
            ),
          const SizedBox(height: 8),
          // Text field + send
          Row(children: [
            Expanded(
              child: TextField(
                controller: widget.controller,
                minLines: 1, maxLines: 3,
                textInputAction: TextInputAction.send,
                onSubmitted: (_) => widget.onSend(),
                decoration: InputDecoration(
                  hintText: '说点什么吧...',
                  contentPadding: const EdgeInsets.symmetric(horizontal: 18, vertical: 10),
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(24), borderSide: BorderSide.none),
                  filled: true,
                  fillColor: AppTheme.surfaceWarm,
                ),
              ),
            ),
            const SizedBox(width: 10),
            GestureDetector(
              onTap: widget.sending ? null : widget.onSend,
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 200),
                width: 48, height: 48,
                decoration: BoxDecoration(
                  gradient: widget.sending ? null : const LinearGradient(colors: [Color(0xFFFFB84D), Color(0xFFFF9500)]),
                  color: widget.sending ? Colors.grey.shade300 : null,
                  shape: BoxShape.circle,
                ),
                child: Center(
                  child: widget.sending
                      ? const SizedBox(width: 22, height: 22, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.grey))
                      : const Icon(Icons.send_rounded, color: Colors.white, size: 22),
                ),
              ),
            ),
          ]),
        ],
      ),
    );
  }
}
