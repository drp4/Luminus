import 'package:dio/dio.dart';

import 'package:flutter_riverpod/flutter_riverpod.dart';

class ApiClient {
  static const String baseUrl = 'http://localhost:8000/api/v1';

  late final Dio _dio;

  ApiClient() {
    _dio = Dio(BaseOptions(
      baseUrl: baseUrl,
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 60),
      headers: {'Content-Type': 'application/json'},
    ));
  }

  // ── Children ──────────────────────────────────────────────────────

  Future<Map<String, dynamic>> createChild(String nickname, int age, String grade) async {
    final res = await _dio.post('/children', data: {'nickname': nickname, 'age': age, 'grade': grade});
    return res.data;
  }

  // ── Chat ──────────────────────────────────────────────────────────

  Future<Map<String, dynamic>> sendMessage(String childId, String message, {List<Map<String, dynamic>>? history}) async {
    final res = await _dio.post('/chat', data: {
      'child_id': childId,
      'message': message,
      'history': history ?? [],
    });
    return res.data;
  }

  // ── Profile ───────────────────────────────────────────────────────

  Future<Map<String, dynamic>> getProfile(String childId) async {
    final res = await _dio.get('/children/$childId/profile');
    return res.data;
  }

  Future<Map<String, dynamic>> getGarden(String childId) async {
    final res = await _dio.get('/children/$childId/garden');
    return res.data;
  }

  // ── Story ─────────────────────────────────────────────────────────

  Future<Map<String, dynamic>> createStory(String childId) async {
    final res = await _dio.post('/stories', data: {'child_id': childId});
    return res.data;
  }

  Future<Map<String, dynamic>> getStories(String childId) async {
    final res = await _dio.get('/stories', queryParameters: {'child_id': childId});
    return res.data;
  }

  Future<Map<String, dynamic>> getStory(String storyId) async {
    final res = await _dio.get('/stories/$storyId');
    return res.data;
  }

  Future<Map<String, dynamic>> generateScene(String storyId, {int chapter = 1, int scene = 1}) async {
    final res = await _dio.post('/stories/$storyId/scene', queryParameters: {
      'chapter_order': chapter,
      'scene_index': scene,
    });
    return res.data;
  }

  Future<Map<String, dynamic>> makeChoice(String storyId, String childId, String choice) async {
    final res = await _dio.post('/stories/$storyId/choose', data: {
      'child_id': childId,
      'choice_text': choice,
    });
    return res.data;
  }
}

final apiClientProvider = Provider<ApiClient>((ref) => ApiClient());
