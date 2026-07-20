class Child {
  final String id;
  final String nickname;
  final int age;
  final String grade;

  const Child({required this.id, required this.nickname, required this.age, required this.grade});

  factory Child.fromJson(Map<String, dynamic> json) => Child(
    id: json['id'] ?? '',
    nickname: json['nickname'] ?? '',
    age: json['age'] ?? 8,
    grade: json['grade'] ?? '',
  );
}

class GardenData {
  final String childId;
  final String nickname;
  final List<PlantData> plants;
  final double soilQuality;
  final int gardenLevel;
  final int totalMemories;

  const GardenData({
    required this.childId, required this.nickname, required this.plants,
    required this.soilQuality, required this.gardenLevel, required this.totalMemories,
  });

  factory GardenData.fromJson(Map<String, dynamic> json) => GardenData(
    childId: json['child_id'] ?? '',
    nickname: json['nickname'] ?? '',
    plants: (json['plants'] as List<dynamic>?)?.map((p) => PlantData.fromJson(p)).toList() ?? [],
    soilQuality: (json['soil_quality'] ?? 0.5).toDouble(),
    gardenLevel: json['garden_level'] ?? 1,
    totalMemories: json['total_memories'] ?? 0,
  );
}

class PlantData {
  final String topic;
  final double weight;
  final String trend;
  final String stage;
  final String color;

  const PlantData({required this.topic, required this.weight, required this.trend, required this.stage, required this.color});

  factory PlantData.fromJson(Map<String, dynamic> json) => PlantData(
    topic: json['topic'] ?? '',
    weight: (json['weight'] ?? 0.5).toDouble(),
    trend: json['trend'] ?? 'stable',
    stage: json['stage'] ?? 'seed',
    color: json['color'] ?? '#9E9E9E',
  );

  String get emoji {
    switch (stage) {
      case 'blooming': return '🌸';
      case 'growing': return '🪴';
      case 'sprout': return '🌿';
      default: return '🌱';
    }
  }

  double get size {
    switch (stage) {
      case 'blooming': return 80;
      case 'growing': return 64;
      case 'sprout': return 48;
      default: return 32;
    }
  }
}

class StoryData {
  final String id;
  final String title;
  final String theme;
  final String description;
  final String status;
  final int totalChapters;
  final int currentChapter;
  final String? createdAt;

  const StoryData({
    required this.id, required this.title, required this.theme, required this.description,
    required this.status, required this.totalChapters, required this.currentChapter, this.createdAt,
  });

  factory StoryData.fromJson(Map<String, dynamic> json) => StoryData(
    id: json['id'] ?? '',
    title: json['title'] ?? '',
    theme: json['theme'] ?? '',
    description: json['description'] ?? '',
    status: json['status'] ?? '',
    totalChapters: json['total_chapters'] ?? 0,
    currentChapter: json['current_chapter'] ?? 1,
    createdAt: json['created_at'],
  );
}

class SceneData {
  final String id;
  final int order;
  final String text;
  final String imagePrompt;
  final List<ChoiceData> choices;
  final List<KnowledgePointData> knowledgePoints;
  final bool isEndScene;

  const SceneData({
    required this.id, required this.order, required this.text, required this.imagePrompt,
    required this.choices, required this.knowledgePoints, required this.isEndScene,
  });

  factory SceneData.fromJson(Map<String, dynamic> json) => SceneData(
    id: json['id'] ?? '',
    order: json['order'] ?? 0,
    text: json['text'] ?? '',
    imagePrompt: json['image_prompt'] ?? '',
    choices: (json['choices'] as List<dynamic>?)?.map((c) => ChoiceData.fromJson(c)).toList() ?? [],
    knowledgePoints: (json['knowledge_points'] as List<dynamic>?)?.map((k) => KnowledgePointData.fromJson(k)).toList() ?? [],
    isEndScene: json['is_end_scene'] ?? false,
  );
}

class ChoiceData {
  final String text;
  const ChoiceData({required this.text});
  factory ChoiceData.fromJson(Map<String, dynamic> json) => ChoiceData(text: json['text'] ?? '');
}

class KnowledgePointData {
  final String subject;
  final String concept;
  final String? vocabulary;
  const KnowledgePointData({required this.subject, required this.concept, this.vocabulary});
  factory KnowledgePointData.fromJson(Map<String, dynamic> json) => KnowledgePointData(
    subject: json['subject'] ?? '',
    concept: json['concept'] ?? '',
    vocabulary: json['vocabulary'],
  );
}

class ChatMessage {
  final String role; // 'user' or 'assistant'
  final String content;
  final DateTime timestamp;

  const ChatMessage({required this.role, required this.content, required this.timestamp});

  Map<String, dynamic> toApi() => {'role': role, 'content': content};
}
