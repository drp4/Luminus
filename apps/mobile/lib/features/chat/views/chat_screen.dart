import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/services/api_client.dart';
import '../../../core/models/app_models.dart';
import '../../../core/theme/app_theme.dart';
import '../../home/views/home_screen.dart';

class ChatScreen extends ConsumerStatefulWidget {
  const ChatScreen({super.key});
  @override
  ConsumerState<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends ConsumerState<ChatScreen> {
  final _msgCtrl = TextEditingController();
  final _scrollCtrl = ScrollController();
  final _messages = <ChatMessage>[];
  bool _sending = false;

  @override
  void dispose() {
    _msgCtrl.dispose();
    _scrollCtrl.dispose();
    super.dispose();
  }

  Future<void> _send() async {
    final text = _msgCtrl.text.trim();
    if (text.isEmpty) return;
    final child = ref.read(childProvider);
    if (child == null) return;

    setState(() {
      _messages.add(ChatMessage(role: 'user', content: text, timestamp: DateTime.now()));
      _sending = true;
    });
    _msgCtrl.clear();
    _scrollToBottom();

    try {
      final api = ref.read(apiClientProvider);
      final history = _messages.sublist(0, _messages.length - 1).map((m) => m.toApi()).toList();
      final res = await api.sendMessage(child.id, text, history: history);
      setState(() {
        _messages.add(ChatMessage(role: 'assistant', content: res['message'] ?? '', timestamp: DateTime.now()));
        _sending = false;
      });
      _scrollToBottom();
    } catch (e) {
      setState(() => _sending = false);
    }
  }

  void _scrollToBottom() {
    Future.delayed(const Duration(milliseconds: 100), () {
      if (_scrollCtrl.hasClients) _scrollCtrl.animateTo(_scrollCtrl.position.maxScrollExtent, duration: const Duration(milliseconds: 300), curve: Curves.easeOut);
    });
  }

  @override
  Widget build(BuildContext context) {
    final child = ref.watch(childProvider);
    return Scaffold(
      appBar: AppBar(
        title: Text(child != null ? '和${child.nickname}聊天' : '聊天'),
        leading: IconButton(icon: const Icon(Icons.arrow_back), onPressed: () => Navigator.pop(context)),
      ),
      body: Column(
        children: [
          Expanded(
            child: _messages.isEmpty ? _EmptyChat() : ListView.builder(
              controller: _scrollCtrl,
              padding: const EdgeInsets.all(16),
              itemCount: _messages.length + (_sending ? 1 : 0),
              itemBuilder: (ctx, i) {
                if (_sending && i == _messages.length) return const _TypingBubble();
                return _ChatBubble(message: _messages[i]);
              },
            ),
          ),
          _ChatInput(controller: _msgCtrl, sending: _sending, onSend: _send),
        ],
      ),
    );
  }
}

class _EmptyChat extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Text('💬', style: TextStyle(fontSize: 64)),
          const SizedBox(height: 16),
          Text('开始聊天吧！', style: Theme.of(context).textTheme.headlineMedium),
          const SizedBox(height: 8),
          Text('你的AI伙伴在等你哦', style: Theme.of(context).textTheme.bodySmall),
        ],
      ),
    );
  }
}

class _ChatBubble extends StatelessWidget {
  final ChatMessage message;
  const _ChatBubble({required this.message});

  @override
  Widget build(BuildContext context) {
    final isUser = message.role == 'user';
    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.8),
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
        decoration: BoxDecoration(
          color: isUser ? AppTheme.surface : AppTheme.primaryLight,
          borderRadius: BorderRadius.only(
            topLeft: const Radius.circular(24),
            topRight: const Radius.circular(24),
            bottomLeft: isUser ? const Radius.circular(24) : const Radius.circular(8),
            bottomRight: isUser ? const Radius.circular(8) : const Radius.circular(24),
          ),
        ),
        child: Text(message.content, style: TextStyle(fontSize: 16, height: 1.5, color: isUser ? AppTheme.textPrimary : AppTheme.textOnPrimary)),
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
        padding: EdgeInsets.only(bottom: 12),
        child: Text('...', style: TextStyle(fontSize: 20, color: AppTheme.textSecondary)),
      ),
    );
  }
}

class _ChatInput extends StatelessWidget {
  final TextEditingController controller;
  final bool sending;
  final VoidCallback onSend;
  const _ChatInput({required this.controller, required this.sending, required this.onSend});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
      decoration: const BoxDecoration(color: AppTheme.surface, boxShadow: [BoxShadow(color: Color(0x0A000000), blurRadius: 8, offset: Offset(0, -2))]),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: controller,
              minLines: 1, maxLines: 4,
              textInputAction: TextInputAction.send,
              onSubmitted: (_) => onSend(),
              decoration: const InputDecoration(hintText: '说点什么吧...', contentPadding: EdgeInsets.symmetric(horizontal: 20, vertical: 12)),
            ),
          ),
          const SizedBox(width: 12),
          SizedBox(
            width: 52, height: 52,
            child: ElevatedButton(
              onPressed: sending ? null : onSend,
              style: ElevatedButton.styleFrom(padding: EdgeInsets.zero, shape: const CircleBorder(), minimumSize: const Size(52, 52)),
              child: sending ? const SizedBox(width: 24, height: 24, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white)) : const Icon(Icons.send_rounded, size: 24),
            ),
          ),
        ],
      ),
    );
  }
}
