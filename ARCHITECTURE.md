# APTIRECALL — Architecture & Planning Document

> AI-Powered Aptitude Learning, Solving & Recall Platform

---

## 1. VISION & CORE PRINCIPLES

AptiRecall is NOT a chatbot wrapper. It is a structured learning + verification + recall platform combining:
- Verified mathematical solving
- Concept/shortcut teaching
- Adaptive spaced recall
- Unseen-question OCR pipeline

The processing pipeline for every question follows:

```
UNDERSTAND → CLASSIFY → SOLVE → VERIFY → EXPLAIN → RECALL → PRACTICE
```

Key architectural principles:
1. **Separation of concerns**: AI layer is never the sole source of truth for math.
2. **Deterministic verification**: All answers pass through SymPy/equation validation.
3. **Modular topics**: New topics are added as data, not code changes.
4. **Progressive disclosure**: UI reveals solutions only through an educational flow.

---

## 2. FINAL SYSTEM ARCHITECTURE

### 2.1 High-Level Components

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                           │
│  ┌──────────────────────┐      ┌──────────────────────────┐   │
│  │   React Web App      │      │  React Native (Expo)     │   │
│  │   (Vite + TypeScript)│      │  Android App             │   │
│  └──────────┬───────────┘      └──────────┬───────────────┘   │
│             │   REST API (JSON)           │                     │
└─────────────┼─────────────────────────────┼────────────────────┘
              │                             │
┌─────────────┼─────────────────────────────┼────────────────────┐
│             ▼                             ▼                    │
│    ┌──────────────────────────────────────────────┐           │
│    │          API GATEWAY / Nginx                 │           │
│    └──────────────────────┬───────────────────────┘           │
│                           │                                    │
│    ┌──────────────────────▼───────────────────────┐           │
│    │        Django REST Framework Backend         │           │
│    │  ┌─────────┐ ┌──────────┐ ┌──────────────┐  │           │
│    │  │ Auth    │ │ Topics   │ │ AI/OCR       │  │           │
│    │  │ Module  │ │ Module   │ │ Module       │  │           │
│    │  └─────────┘ └──────────┘ └──────────────┘  │           │
│    │  ┌─────────┐ ┌──────────┐ ┌──────────────┐  │           │
│    │  │ Solve   │ │ Recall   │ │ Practice     │  │           │
│    │  │ Module  │ │ Module   │ │ Module       │  │           │
│    │  └─────────┘ └──────────┘ └──────────────┘  │           │
│    └──────────────────────┬───────────────────────┘           │
│                           │                                    │
│    ┌──────────────────────▼───────────────────────┐           │
│    │              PostgreSQL                       │           │
│    └──────────────────────────────────────────────┘           │
│                                                               │
│    ┌──────────────────────────────────────────────┐           │
│    │   AI Services (separate process / worker)     │           │
│    │   ┌──────────────┐  ┌────────────────────┐  │           │
│    │   │ LLM Service  │  │ OCR / Vision        │  │           │
│    │   │ (Ollama /    │  │ (Tesseract /        │  │           │
│    │   │  OpenAI)     │  │  PaddleOCR)         │  │           │
│    │   └──────────────┘  └────────────────────┘  │           │
│    │   ┌──────────────┐  ┌────────────────────┐  │           │
│    │   │ Math Solver  │  │ TTS Service        │  │           │
│    │   │ (SymPy)      │  │ (gTTS / edge-tts)  │  │           │
│    │   └──────────────┘  └────────────────────┘  │           │
│    └──────────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Technology Choices (Final)

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Backend | Python 3.11 + Django 5 + DRF | Robust, mature, excellent AI/ML ecosystem |
| Database | PostgreSQL 15+ | Full JSON support, reliable, scalable |
| Auth | JWT (SimpleJWT) | Stateless, works for web and mobile |
| Frontend | React 18 + Vite + TypeScript | Fast, type-safe, good DX |
| Mobile | React Native + Expo | Shared business logic, single codebase |
| AI/LLM | Ollama (local) or OpenAI-compatible API | Structured JSON output, fallback capable |
| OCR | Tesseract / PaddleOCR | Offline-capable, good accuracy for math text |
| Math | SymPy | Deterministic symbolic/numeric solving |
| TTS | edge-tts (offline) or gTTS | Free, no API key required initially |
| Task Queue | Celery + Redis | Async processing for OCR, voice, heavy AI |
| File Storage | Local filesystem / S3-compatible | Images, audio, exports |
| Testing | pytest + pytest-django + React Testing Library | Industry standard |

---

## 3. FOLDER STRUCTURE

```
aptirecall/
├── README.md
├── ARCHITECTURE.md
├── .env.example
├── requirements.txt
├── docker-compose.yml
├── pytest.ini
├── manage.py
│
├── backend/                          # Django project root
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   ├── production.py
│   │   └── test.py
│   ├── __init__.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
│   ├── apps/                          # Django apps (modules)
│   │   ├── __init__.py
│   │   │
│   │   ├── users/                     # Authentication & profiles
│   │   │   ├── __init__.py
│   │   │   ├── models.py
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   ├── urls.py
│   │   │   ├── permissions.py
│   │   │   ├── admin.py
│   │   │   ├── services/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── auth_service.py
│   │   │   │   └── token_service.py
│   │   │   └── tests/
│   │   │       ├── __init__.py
│   │   │       ├── test_models.py
│   │   │       ├── test_auth.py
│   │   │       └── test_serializers.py
│   │   │
│   │   ├── topics/                    # Topic/subtopic/problem-type management
│   │   │   ├── __init__.py
│   │   │   ├── models.py
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   ├── urls.py
│   │   │   ├── admin.py
│   │   │   ├── services/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── topic_service.py
│   │   │   │   └── classification_service.py
│   │   │   └── tests/
│   │   │
│   │   ├── questions/                 # Question bank & learning flow
│   │   │   ├── __init__.py
│   │   │   ├── models.py
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   ├── urls.py
│   │   │   ├── admin.py
│   │   │   ├── services/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── question_service.py
│   │   │   │   └── learning_flow.py
│   │   │   └── tests/
│   │   │
│   │   ├── solve/                     # Solving + verification engine
│   │   │   ├── __init__.py
│   │   │   ├── models.py
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   ├── urls.py
│   │   │   ├── admin.py
│   │   │   ├── services/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── solver_service.py
│   │   │   │   ├── verification_engine.py
│   │   │   │   └── explanation_service.py
│   │   │   └── tests/
│   │   │       ├── test_solver.py
│   │   │       ├── test_verification.py
│   │   │       └── test_explanation.py
│   │   │
│   │   ├── upload/                    # Image upload + OCR pipeline
│   │   │   ├── __init__.py
│   │   │   ├── models.py
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   ├── urls.py
│   │   │   ├── admin.py
│   │   │   ├── services/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── image_service.py
│   │   │   │   ├── ocr_service.py
│   │   │   │   ├── question_extractor.py
│   │   │   │   └── preprocessing.py
│   │   │   └── tests/
│   │   │
│   │   ├── recall/                    # AptiRecall Adaptive Recall Algorithm
│   │   │   ├── __init__.py
│   │   │   ├── models.py
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   ├── urls.py
│   │   │   ├── admin.py
│   │   │   ├── services/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── recall_algorithm.py
│   │   │   │   ├── weakness_detector.py
│   │   │   │   └── scheduler.py
│   │   │   └── tests/
│   │   │       ├── test_recall_algorithm.py
│   │   │       └── test_weakness_detector.py
│   │   │
│   │   ├── practice/                  # Personalized practice generation
│   │   │   ├── __init__.py
│   │   │   ├── models.py
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   ├── urls.py
│   │   │   ├── admin.py
│   │   │   ├── services/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── practice_generator.py
│   │   │   │   └── similar_question_generator.py
│   │   │   └── tests/
│   │   │
│   │   ├── progress/                  # Dashboard & analytics
│   │   │   ├── __init__.py
│   │   │   ├── models.py
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   ├── urls.py
│   │   │   ├── admin.py
│   │   │   ├── services/
│   │   │   │   ├── __init__.py
│   │   │   │   └── analytics_service.py
│   │   │   └── tests/
│   │   │
│   │   ├── voice/                     # Text-to-Speech
│   │   │   ├── __init__.py
│   │   │   ├── models.py
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   ├── urls.py
│   │   │   ├── admin.py
│   │   │   ├── services/
│   │   │   │   ├── __init__.py
│   │   │   │   └── tts_service.py
│   │   │   └── tests/
│   │   │
│   │   └── admin_panel/               # Enhanced admin features
│   │       ├── __init__.py
│   │       ├── models.py
│   │       ├── serializers.py
│   │       ├── views.py
│   │       ├── urls.py
│   │       ├── admin.py
│   │       └── tests/
│   │
│   ├── core/                          # Shared utilities
│   │   ├── __init__.py
│   │   ├── exceptions.py
│   │   ├── constants.py
│   │   ├── enums.py
│   │   ├── pagination.py
│   │   ├── permissions.py
│   │   ├── utils.py
│   │   └── mixins.py
│   │
│   ├── ai_services/                   # AI service wrappers
│   │   ├── __init__.py
│   │   ├── llm_client.py
│   │   ├── prompt_templates.py
│   │   ├── structured_output.py
│   │   └── math_solver.py
│   │
│   ├── celery.py                      # Celery app config
│   └── wsgi.py
│
├── frontend/                          # React web application
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   │
│   ├── public/
│   │   ├── favicon.ico
│   │   └── assets/
│   │
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── index.css
│   │   │
│   │   ├── components/
│   │   │   ├── ui/                   # Reusable UI primitives
│   │   │   │   ├── Button.tsx
│   │   │   │   ├── Card.tsx
│   │   │   │   ├── Input.tsx
│   │   │   │   ├── Modal.tsx
│   │   │   │   ├── Spinner.tsx
│   │   │   │   └── ...
│   │   │   ├── layout/
│   │   │   │   ├── Header.tsx
│   │   │   │   ├── Sidebar.tsx
│   │   │   │   ├── Footer.tsx
│   │   │   │   └── MobileNav.tsx
│   │   │   └── features/
│   │   │       ├── QuestionFlow.tsx
│   │   │       ├── ImageUploader.tsx
│   │   │       ├── SolutionView.tsx
│   │   │       └── ...
│   │   │
│   │   ├── pages/                    # Route-level pages
│   │   │   ├── Splash.tsx
│   │   │   ├── Onboarding.tsx
│   │   │   ├── Login.tsx
│   │   │   ├── Register.tsx
│   │   │   ├── HomeDashboard.tsx
│   │   │   ├── Topics.tsx
│   │   │   ├── TopicDetails.tsx
│   │   │   ├── Question.tsx
│   │   │   ├── Solution.tsx
│   │   │   ├── Shortcut.tsx
│   │   │   ├── AskAptiRecall.tsx
│   │   │   ├── ImagePreview.tsx
│   │   │   ├── ExtractedQuestionConfirm.tsx
│   │   │   ├── Progress.tsx
│   │   │   ├── WeakTopics.tsx
│   │   │   ├── Profile.tsx
│   │   │   ├── Settings.tsx
│   │   │   └── admin/
│   │   │       ├── AdminDashboard.tsx
│   │   │       ├── TopicManagement.tsx
│   │   │       ├── QuestionManagement.tsx
│   │   │       └── ...
│   │   │
│   │   ├── hooks/
│   │   │   ├── useAuth.ts
│   │   │   ├── useQuestions.ts
│   │   │   ├── useSolve.ts
│   │   │   ├── useRecall.ts
│   │   │   └── ...
│   │   │
│   │   ├── services/
│   │   │   ├── api.ts
│   │   │   ├── auth.ts
│   │   │   ├── questions.ts
│   │   │   ├── solve.ts
│   │   │   ├── upload.ts
│   │   │   ├── tts.ts
│   │   │   └── ...
│   │   │
│   │   ├── store/                    # Zustand / Redux state
│   │   │   ├── authStore.ts
│   │   │   ├── questionStore.ts
│   │   │   └── ...
│   │   │
│   │   ├── types/
│   │   │   ├── api.ts
│   │   │   ├── user.ts
│   │   │   ├── question.ts
│   │   │   └── ...
│   │   │
│   │   └── utils/
│   │       ├── constants.ts
│   │       ├── helpers.ts
│   │       └── validators.ts
│   │
│   └── tests/
│       ├── components/
│       ├── pages/
│       └── services/
│
├── mobile/                            # React Native (Expo) app
│   ├── app.json
│   ├── app.config.ts
│   ├── package.json
│   ├── tsconfig.json
│   ├── babel.config.js
│   │
│   ├── assets/
│   │   ├── icon.png
│   │   ├── splash.png
│   │   └── adaptive-icon.png
│   │
│   ├── src/
│   │   ├── App.tsx
│   │   ├── navigation/
│   │   │   ├── AppNavigator.tsx
│   │   │   ├── AuthNavigator.tsx
│   │   │   └── TabNavigator.tsx
│   │   ├── screens/
│   │   │   ├── SplashScreen.tsx
│   │   │   ├── LoginScreen.tsx
│   │   │   ├── HomeScreen.tsx
│   │   │   ├── TopicsScreen.tsx
│   │   │   ├── QuestionScreen.tsx
│   │   │   ├── AskScreen.tsx
│   │   │   ├── CameraScreen.tsx
│   │   │   ├── ProgressScreen.tsx
│   │   │   └── ...
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── store/
│   │   └── utils/
│   │
│   └── __tests__/
│
├── shared/                            # Shared code between web and mobile
│   ├── types/
│   │   ├── user.ts
│   │   ├── question.ts
│   │   └── api.ts
│   ├── constants/
│   │   ├── topics.ts
│   │   ├── problemTypes.ts
│   │   └── difficulty.ts
│   └── utils/
│       ├── math.ts
│       └── validators.ts
│
├── docs/                              # Project documentation
│   ├── 01_problem_statement.md
│   ├── 02_requirements.md
│   ├── 03_architecture.md
│   ├── 04_database_design.md
│   ├── 05_api_documentation.md
│   ├── 06_ai_pipeline.md
│   ├── 07_ocr_pipeline.md
│   ├── 08_verification_architecture.md
│   ├── 09_recall_algorithm.md
│   ├── 10_testing.md
│   ├── 11_deployment.md
│   └── 12_user_manual.md
│
├── tests/                             # Cross-cutting integration tests
│   ├── conftest.py
│   ├── test_api.py
│   └── test_e2e.py
│
├── scripts/                           # Utility scripts
│   ├── seed_topics.py
│   ├── seed_questions.py
│   ├── generate_docs.py
│   └── deploy.sh
│
└── media/                             # Uploaded files (gitignored)
    ├── uploads/
    ├── audio/
    └── exports/
```

---

## 4. DATABASE DESIGN (ER SCHEMA)

### 4.1 Entity Relationship Overview

```
User ──< UserAttempt >── Question
User ──< RecallRecord >── Topic
User ──< RecallRecord >── ProblemType
User ──< UploadedQuestion

Topic ──< Subtopic
Topic ──< Formula
Topic ──< Question >── ProblemType
Question ──< SolutionStep
Question ──< Shortcut
Question ──< UserAttempt
Question ──< GeneratedQuestion

ProblemType ──< Question
```

### 4.2 Core Models (Django ORM)

```python
# apps/users/models.py
class User(AbstractUser):
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    level = models.CharField(max_length=20, default="beginner")
    streak_days = models.PositiveIntegerField(default=0)
    last_active = models.DateField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    total_questions_attempted = models.PositiveIntegerField(default=0)
    total_questions_solved = models.PositiveIntegerField(default=0)
    overall_accuracy = models.FloatField(default=0.0)
    preferred_language = models.CharField(max_length=10, default="en")
```

```python
# apps/topics/models.py
class Topic(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "name"]

class Subtopic(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="subtopics")
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ["topic", "name"]
        ordering = ["order"]

class ProblemType(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="problem_types")
    subtopic = models.ForeignKey(Subtopic, on_delete=models.CASCADE, null=True, blank=True, related_name="problem_types")
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    keywords = models.JSONField(default=list, blank=True)
    solving_strategy = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ["topic", "name"]
        ordering = ["name"]

class Formula(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="formulas")
    problem_type = models.ForeignKey(ProblemType, on_delete=models.CASCADE, null=True, blank=True, related_name="formulas")
    name = models.CharField(max_length=200)
    formula_latex = models.TextField()
    description = models.TextField(blank=True)
    variables = models.JSONField(default=list, blank=True)
    example_usage = models.TextField(blank=True)
```

```python
# apps/questions/models.py
class Question(models.Model):
    DIFFICULTY_CHOICES = [
        ("easy", "Easy"),
        ("medium", "Medium"),
        ("hard", "Hard"),
    ]

    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="questions")
    problem_type = models.ForeignKey(ProblemType, on_delete=models.CASCADE, related_name="questions")
    subtopic = models.ForeignKey(Subtopic, on_delete=models.CASCADE, null=True, blank=True, related_name="questions")
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES)
    question_text = models.TextField()
    question_latex = models.TextField(blank=True)
    options = models.JSONField(default=list, blank=True)  # For MCQ
    correct_answer = models.TextField()
    correct_answer_latex = models.TextField(blank=True)
    explanation_concept = models.TextField()
    explanation_steps = models.JSONField(default=list)  # Step-by-step
    explanation_approach = models.TextField()
    explanation_shortcut = models.TextField(blank=True)
    hints = models.JSONField(default=list, blank=True)
    tags = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

class SolutionStep(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="solution_steps")
    step_number = models.PositiveIntegerField()
    title = models.CharField(max_length=200)
    description = models.TextField()
    latex = models.TextField(blank=True)

    class Meta:
        unique_together = ["question", "step_number"]
        ordering = ["step_number"]

class Shortcut(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="shortcuts")
    title = models.CharField(max_length=200)
    description = models.TextField()
    formula = models.TextField(blank=True)
    example = models.TextField(blank=True)

class UploadedQuestion(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="uploaded_questions")
    image = models.ImageField(upload_to="uploads/questions/")
    extracted_text = models.TextField(blank=True)
    detected_topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True, blank=True)
    detected_problem_type = models.ForeignKey(ProblemType, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    solution = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

```python
# apps/solve/models.py
class UserAttempt(models.Model):
    ATTEMPT_STATUS = [
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("abandoned", "Abandoned"),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="attempts")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="attempts")
    uploaded_question = models.ForeignKey(UploadedQuestion, on_delete=models.CASCADE, null=True, blank=True, related_name="attempts")
    status = models.CharField(max_length=20, choices=ATTEMPT_STATUS, default="in_progress")
    user_answer = models.TextField(blank=True)
    is_correct = models.BooleanField(null=True, blank=True)
    hints_used = models.PositiveIntegerField(default=0)
    attempts_count = models.PositiveIntegerField(default=1)
    time_taken_seconds = models.PositiveIntegerField(null=True, blank=True)
    viewed_solution = models.BooleanField(default=False)
    viewed_shortcut = models.BooleanField(default=False)
    viewed_concept = models.BooleanField(default=False)
    solution_feedback = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

class VerificationRecord(models.Model):
    attempt = models.ForeignKey(UserAttempt, on_delete=models.CASCADE, related_name="verification_records")
    method = models.CharField(max_length=50)  # e.g. "algebraic", "substitution", "reverse"
    input_data = models.JSONField()
    expected_result = models.TextField()
    actual_result = models.TextField()
    is_verified = models.BooleanField()
    verification_details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

```python
# apps/recall/models.py
class RecallRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="recall_records")
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="recall_records")
    problem_type = models.ForeignKey(ProblemType, on_delete=models.CASCADE, null=True, blank=True, related_name="recall_records")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, null=True, blank=True, related_name="recall_records")
    recall_score = models.FloatField(default=0.0)  # 0.0 to 1.0
    accuracy_score = models.FloatField(default=0.0)
    practice_count = models.PositiveIntegerField(default=0)
    last_practiced = models.DateTimeField(null=True, blank=True)
    next_practice_at = models.DateTimeField(null=True, blank=True)
    difficulty_at_practice = models.CharField(max_length=10, blank=True)
    is_weak = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["user", "topic", "problem_type", "question"]
```

```python
# apps/voice/models.py
class VoiceExplanation(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="voice_explanations")
    attempt = models.ForeignKey(UserAttempt, on_delete=models.CASCADE, null=True, blank=True, related_name="voice_explanations")
    audio_file = models.FileField(upload_to="audio/explanations/")
    text_content = models.TextField()
    language = models.CharField(max_length=10, default="en")
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

### 4.3 Indexes & Constraints

Key indexes for performance:
- `UserAttempt(user, question)` — fast attempt lookups
- `RecallRecord(user, next_practice_at)` — efficient scheduling query
- `Question(topic, problem_type, difficulty, is_active)` — filtered practice queries
- `UploadedQuestion(user, status, created_at)` — user upload history

---

## 5. REST API PLAN

### 5.1 Authentication Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | /api/auth/register/ | No | Register new user |
| POST | /api/auth/login/ | No | Obtain JWT tokens |
| POST | /api/auth/refresh/ | No | Refresh access token |
| POST | /api/auth/logout/ | Yes | Blacklist refresh token |
| GET | /api/auth/profile/ | Yes | Get current user profile |
| PATCH | /api/auth/profile/ | Yes | Update profile |

### 5.2 Topic Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | /api/topics/ | Yes | List all topics |
| GET | /api/topics/{id}/ | Yes | Topic details with subtopics |
| GET | /api/topics/{id}/problem-types/ | Yes | Problem types for topic |
| GET | /api/topics/{id}/formulas/ | Yes | Formulas for topic |

### 5.3 Question Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | /api/questions/ | Yes | List questions (filterable) |
| GET | /api/questions/{id}/ | Yes | Question detail |
| GET | /api/questions/{id}/solution/ | Yes | Full solution |
| GET | /api/questions/{id}/shortcut/ | Yes | Shortcut method |
| POST | /api/questions/{id}/attempt/ | Yes | Submit an attempt |
| GET | /api/questions/{id}/similar/ | Yes | Similar practice questions |
| POST | /api/questions/{id}/hint/ | Yes | Get next hint |

### 5.4 Solve Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | /api/solve/text/ | Yes | Solve from text input |
| POST | /api/solve/verify/ | Yes | Verify an answer |
| GET | /api/solve/history/ | Yes | User's solving history |

### 5.5 Upload / OCR Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | /api/upload/image/ | Yes | Upload image for OCR |
| GET | /api/upload/{id}/status/ | Yes | Check processing status |
| GET | /api/upload/{id}/result/ | Yes | Get extracted questions |
| POST | /api/upload/{id}/confirm/ | Yes | Confirm which question to solve |
| POST | /api/ocr/extract/ | Yes | Extract text from image (sync) |

### 5.6 Recall Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | /api/recall/schedule/ | Yes | Get today's recall queue |
| POST | /api/recall/submit/ | Yes | Submit recall answer |
| GET | /api/recall/weak-topics/ | Yes | Weak topics summary |
| GET | /api/recall/analytics/ | Yes | Recall analytics |

### 5.7 Practice Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | /api/practice/next/ | Yes | Get next practice question |
| POST | /api/practice/{id}/submit/ | Yes | Submit practice answer |
| GET | /api/practice/history/ | Yes | Practice history |

### 5.8 Progress Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | /api/progress/dashboard/ | Yes | Dashboard summary |
| GET | /api/progress/accuracy/ | Yes | Accuracy over time |
| GET | /api/progress/topics/ | Yes | Topic-wise breakdown |
| GET | /api/progress/mistakes/ | Yes | Recent mistakes |

### 5.9 Voice Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | /api/voice/generate/ | Yes | Generate TTS for text |
| GET | /api/voice/{id}/ | Yes | Get audio file |
| POST | /api/voice/{id}/regenerate/ | Yes | Regenerate with different voice |

### 5.10 Admin Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | /api/admin/dashboard/ | Admin | Admin overview |
| POST | /api/admin/topics/ | Admin | Create topic |
| PUT | /api/admin/topics/{id}/ | Admin | Update topic |
| POST | /api/admin/questions/ | Admin | Create question |
| PUT | /api/admin/questions/{id}/ | Admin | Update question |
| POST | /api/admin/questions/bulk-import/ | Admin | Bulk import questions |
| GET | /api/admin/users/ | Admin | List users |
| GET | /api/admin/performance/ | Admin | System-wide analytics |

### 5.11 Response Standards

All responses follow this structure:

**Success:**
```json
{
  "success": true,
  "data": { ... },
  "meta": { "page": 1, "total_pages": 5, "total_count": 100 }
}
```

**Error:**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": { "field": ["error message"] }
  }
}
```

---

## 6. MODULE BREAKDOWN

### 6.1 Users Module
**Responsibility:** Authentication, authorization, profile management.

Key files:
- `apps/users/models.py` — User, UserProfile
- `apps/users/serializers.py` — Registration, login, profile serializers
- `apps/users/views.py` — Auth endpoints
- `apps/users/permissions.py` — IsOwner, IsAdmin
- `apps/users/services/auth_service.py` — Registration, login business logic

### 6.2 Topics Module
**Responsibility:** Topic hierarchy management (Topic → Subtopic → ProblemType).

Key files:
- `apps/topics/models.py` — Topic, Subtopic, ProblemType, Formula
- `apps/topics/services/classification_service.py` — LLM-based topic/problem-type classification

### 6.3 Questions Module
**Responsibility:** Question bank, learning flow (Question → Hint → Concept → Approach → Shortcut → Solution).

Key files:
- `apps/questions/models.py` — Question, SolutionStep, Shortcut, UploadedQuestion
- `apps/questions/services/learning_flow.py` — Educational flow orchestration
- `apps/questions/services/question_service.py` — Question CRUD, filtering, similar questions

### 6.4 Solve Module
**Responsibility:** Deterministic solving, independent verification, explanation generation.

Key files:
- `apps/solve/services/solver_service.py` — Route to appropriate solver strategy
- `apps/solve/services/verification_engine.py` — Multi-method verification (algebraic, reverse, substitution)
- `apps/solve/services/explanation_service.py` — AI explanation generation (steps, shortcuts)

### 6.5 Upload Module
**Responsibility:** Image handling, preprocessing, OCR, question extraction, confirmation.

Key files:
- `apps/upload/services/preprocessing.py` — Image enhancement for OCR
- `apps/upload/services/ocr_service.py` — Tesseract/PaddleOCR integration
- `apps/upload/services/question_extractor.py` — LLM-based question structuring from OCR text
- `apps/upload/services/image_service.py` — Upload validation, storage

### 6.6 Recall Module
**Responsibility:** AptiRecall Adaptive Recall Algorithm — tracking, scheduling, weakness detection.

Key files:
- `apps/recall/services/recall_algorithm.py` — Core algorithm implementation
- `apps/recall/services/weakness_detector.py` — Weak topic/problem-type analysis
- `apps/recall/services/scheduler.py` — Generate daily practice queue

### 6.7 Practice Module
**Responsibility:** Personalized practice question generation/selection.

Key files:
- `apps/practice/services/practice_generator.py` — Select/generate questions based on recall state
- `apps/practice/services/similar_question_generator.py` — LLM-based similar question generation

### 6.8 Progress Module
**Responsibility:** Dashboard, analytics, reporting.

Key files:
- `apps/progress/services/analytics_service.py` — Compute accuracy, streaks, recommendations

### 6.9 Voice Module
**Responsibility:** Text-to-Speech generation and delivery.

Key files:
- `apps/voice/services/tts_service.py` — TTS wrapper (edge-tts primary, gTTS fallback)

---

## 7. CORE ALGORITHM — APTIRECALL ADAPTIVE RECALL

### 7.1 Concept

AptiRecall Adaptive Recall Algorithm (AARA) estimates a learner's recall strength for each (topic, problem_type) combination and schedules practice accordingly.

### 7.2 Inputs Per Attempt

For each attempt record:
- `accuracy` (0.0–1.0)
- `solving_time` (seconds)
- `hints_used` (count)
- `attempts_count` (count)
- `viewed_solution` (boolean)
- `viewed_shortcut` (boolean)
- `is_correct` (boolean)
- `difficulty` (easy/medium/hard)
- `recency` (days since last practice)

### 7.3 Scoring Formula

```
base_score = accuracy * 0.5
time_penalty = max(0, (solving_time - expected_time) / expected_time) * 0.15
hint_penalty = (hints_used / max_hints) * 0.15
attempt_penalty = (attempts_count - 1) * 0.05
solution_penalty = 0.1 if viewed_solution else 0.0
shortcut_penalty = 0.05 if viewed_shortcut else 0.0

recall_score = base_score
            - time_penalty
            - hint_penalty
            - attempt_penalty
            - solution_penalty
            - shortcut_penalty

recall_score = clamp(recall_score, 0.0, 1.0)
```

### 7.4 Strength Classification

```
if recall_score >= 0.75:
    strength = "strong"
elif recall_score >= 0.45:
    strength = "moderate"
else:
    strength = "weak"
```

### 7.5 Scheduling (Spaced Repetition Inspired)

```
if strength == "strong":
    next_interval = 7 days + random(0, 2 days)
elif strength == "moderate":
    next_interval = 3 days + random(0, 1 day)
else:  # weak
    next_interval = 1 day + random(0, 12 hours)

next_practice_at = now + next_interval
```

### 7.6 Weakness Detection

A (topic, problem_type) pair is flagged as weak if:
- Average recall score across last 5 attempts < 0.4
- OR more than 2 consecutive incorrect attempts
- OR accuracy < 50% with > 3 attempts

### 7.7 Pseudocode

```python
def update_recall(user, attempt):
    record, _ = RecallRecord.objects.get_or_create(
        user=user,
        topic=attempt.question.topic,
        problem_type=attempt.question.problem_type,
    )
    
    score = compute_recall_score(attempt)
    record.recall_score = exponential_moving_average(record.recall_score, score)
    record.accuracy_score = update_accuracy(record.accuracy_score, attempt.is_correct)
    record.practice_count += 1
    record.last_practiced = now()
    record.next_practice_at = compute_next_schedule(record.recall_score)
    record.is_weak = detect_weakness(record)
    record.save()

def get_daily_queue(user):
    return RecallRecord.objects.filter(
        user=user,
        next_practice_at__lte=now()
    ).order_by("is_weak", "recall_score")
```

---

## 8. AI PIPELINE ARCHITECTURE

### 8.1 LLM Integration Pattern

All LLM calls go through a single service layer:

```python
# ai_services/llm_client.py
class LLMClient:
    def __init__(self):
        self.provider = get_provider()  # Ollama or OpenAI
        self.model = settings.AI_MODEL
    
    def structured_call(self, prompt: str, schema: dict) -> dict:
        """Call LLM with structured output enforcement."""
        response = self.provider.chat(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            format="json",  # Enforce JSON
            response_schema=schema,
        )
        return json.loads(response)
```

### 8.2 Prompt Templates (Structured)

```python
# ai_services/prompt_templates.py
TOPIC_CLASSIFIER_PROMPT = """
Classify the following aptitude question into a topic and problem type.

Available topics: {topics}
Available problem types per topic: {problem_types}

Question: {question_text}

Return JSON:
{{
  "topic": "topic_slug",
  "problem_type": "problem_type_slug",
  "confidence": 0.0-1.0
}}
"""

SOLVER_STRATEGY_PROMPT = """
Given the following aptitude question, select the appropriate solving strategy.

Question: {question_text}
Topic: {topic}
Problem type: {problem_type}

Available strategies: {strategies}

Return JSON:
{{
  "strategy": "strategy_name",
  "variables": ["list of variables"],
  "formulas": ["list of relevant formulas"],
  "approach": "brief approach description"
}}
"""

EXPLANATION_PROMPT = """
Generate a step-by-step explanation for the solved question.

Question: {question_text}
Solution steps: {solution_steps}

Return JSON:
{{
  "concept": "concept explanation",
  "approach": "how to approach similar questions",
  "steps": [
    {{"step": 1, "title": "...", "description": "..."}}
  ]
}}
"""

SIMILAR_QUESTION_PROMPT = """
Generate a similar practice question with different numerical values.

Original question: {question_text}
Topic: {topic}
Problem type: {problem_type}
Difficulty: {difficulty}

Return JSON:
{{
  "question_text": "...",
  "options": [...],
  "correct_answer": "...",
  "explanation_concept": "...",
  "hints": ["..."]
}}
"""
```

### 8.3 Math Solver Integration

```python
# ai_services/math_solver.py
class MathSolver:
    def solve(self, expression: str, problem_type: str) -> dict:
        """Deterministic solver using SymPy."""
        if problem_type == "percentage":
            return self._solve_percentage(expression)
        elif problem_type == "profit_loss":
            return self._solve_profit_loss(expression)
        # ... more strategies
        
    def verify(self, question: str, computed_answer: str) -> VerificationResult:
        """Independent verification."""
        # Re-solve using a different method
        # Check algebraic consistency
        # Validate units
        pass
```

---

## 9. OCR PIPELINE

### 9.1 Flow

```
Image Upload
    ↓
Validate (size, type, dimensions)
    ↓
Preprocess
    ├── Resize (if too large)
    ├── Grayscale
    ├── Denoise (optional)
    └── Binarize (adaptive threshold)
    ↓
OCR Engine
    ├── Tesseract (primary, offline)
    └── PaddleOCR (fallback, better for math)
    ↓
Post-process OCR text
    ├── Fix common OCR errors
    ├── Normalize numbers/symbols
    └── Detect multiple questions
    ↓
LLM Question Extraction
    ├── Structure raw text into clean question
    ├── Extract numbers, variables, options
    └── Detect question boundaries (if multiple)
    ↓
Return structured questions for user confirmation
```

### 9.2 Key Services

```python
# apps/upload/services/preprocessing.py
class ImagePreprocessor:
    def preprocess(self, image_path: str) -> str:
        img = cv2.imread(image_path)
        img = self._resize_if_needed(img)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        processed = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        return processed

# apps/upload/services/ocr_service.py
class OCRService:
    def extract_text(self, image) -> str:
        # Primary: Tesseract
        text = pytesseract.image_to_string(image, config="--psm 6")
        if not text.strip():
            # Fallback: PaddleOCR
            text = self._paddle_ocr(image)
        return text

# apps/upload/services/question_extractor.py
class QuestionExtractor:
    def extract(self, raw_text: str) -> list[dict]:
        prompt = EXTRACTION_PROMPT.format(raw_text=raw_text)
        result = llm_client.structured_call(prompt, EXTRACTION_SCHEMA)
        return result["questions"]
```

---

## 10. VERIFICATION ARCHITECTURE

### 10.1 Multi-Method Verification

For every solved question, run at least 2 independent verification methods:

| Method | Description | Applicable To |
|--------|-------------|---------------|
| Algebraic | Substitute answer back into original equation | All algebra |
| Reverse Calculation | Start from answer, work backwards | Percentage, profit/loss, SI/CI |
| Substitution | Plug answer into constraints | Equations, ratios |
| Option Validation | Test each MCQ option against conditions | All MCQ |
| Unit Consistency | Check units match | Time/speed/distance, mixtures |
| Boundary Check | Answer within logical bounds | Probability, ages |

### 10.2 Verification Flow

```python
class VerificationEngine:
    def verify(self, question, computed_answer, strategy) -> VerificationResult:
        methods = self._select_methods(question.problem_type)
        results = []
        
        for method in methods:
            try:
                result = method.verify(question, computed_answer)
                results.append(result)
            except SolverError:
                results.append(VerificationResult(
                    method=method.name,
                    is_verified=False,
                    error="Solver failed"
                ))
        
        passed = sum(1 for r in results if r.is_verified)
        total = len(results)
        confidence = passed / total if total > 0 else 0.0
        
        return VerificationResult(
            is_verified=confidence >= 0.5,
            confidence=confidence,
            details=results
        )
```

---

## 11. DEVELOPMENT PHASES (16 Phases)

### Phase 1: Architecture + Project Setup
- Create folder structure
- Initialize Django project with settings modules
- Setup PostgreSQL, Redis
- Configure Celery
- Initialize React (Vite) and React Native (Expo)
- Setup environment variables
- Configure linting, formatting, pre-commit

**Deliverable:** Scaffolded full project, all dev servers runnable.

### Phase 2: Database + Django REST API
- Define all models in respective apps
- Create migrations
- Setup Django admin
- Implement serializers for all models
- Create basic CRUD views
- Setup URL routing
- Add pagination, filtering, search

**Deliverable:** Full CRUD API for all models via DRF.

### Phase 3: Authentication
- JWT registration/login/logout
- Token refresh
- Protected routes
- Permission classes (IsOwner, IsAdmin)
- Profile management
- Password reset flow

**Deliverable:** Secure authenticated API.

### Phase 4: Topic/Question Learning System
- Seed initial topics, subtopics, problem types
- Topic listing, detail views
- Question listing with filters
- Learning flow: Question → Hint → Concept → Approach → Shortcut → Solution
- Admin: topic/question CRUD

**Deliverable:** Functional topic browsing and question learning flow.

### Phase 5: Question Solution + Explanation
- Solver service routing
- Step-by-step solution generation
- Concept explanation
- Approach explanation
- Shortcut generation
- Hint system

**Deliverable:** Complete educational solution experience.

### Phase 6: Mathematical Verification Engine
- SymPy-based solvers for each problem type
- Verification engine implementation
- Multi-method verification
- Verification record storage
- "Needs Verification" state handling

**Deliverable:** Verified answers with confidence scores.

### Phase 7: Ask AptiRecall (Image/OCR Pipeline)
- Image upload endpoint
- Image preprocessing
- Tesseract OCR integration
- LLM-based question extraction
- User confirmation flow
- Multi-question detection and selection

**Deliverable:** Working "Ask AptiRecall" image pipeline.

### Phase 8: AI Classification and Explanation
- Topic classification via LLM
- Problem type classification
- Solving strategy selection
- Similar question generation
- Explanation quality tuning

**Deliverable:** AI-powered classification and content generation.

### Phase 9: Voice Explanation
- TTS service (edge-tts)
- Audio generation on demand
- Audio delivery API
- Language support
- Mobile audio playback

**Deliverable:** Voice explanation for questions.

### Phase 10: AptiRecall Adaptive Recall Algorithm
- RecallRecord model
- Recall score computation
- Weakness detection
- Scheduling algorithm
- Daily queue generation
- Recall submission flow

**Deliverable:** Working adaptive recall system.

### Phase 11: Personalized Practice
- Practice queue generation
- Similar question selection
- Difficulty progression
- Practice history
- Performance-based recommendations

**Deliverable:** Personalized practice experience.

### Phase 12: React Web UI
- Setup React + Vite + TypeScript + Tailwind
- Implement all 23 screens
- Auth flow
- Question flow with progressive disclosure
- Ask AptiRecall web interface
- Dashboard, progress, weak topics
- Admin panel UI

**Deliverable:** Complete responsive web application.

### Phase 13: React Native Android UI
- Setup Expo project
- Implement core screens
- Camera integration (Expo Camera)
- Image upload (Expo Image Picker)
- Audio playback
- Push notifications (optional)
- Navigation (Expo Router or React Navigation)

**Deliverable:** Downloadable Android APK via Expo.

### Phase 14: Integration Testing
- End-to-end API tests
- Frontend integration tests
- OCR accuracy testing
- Math solver correctness testing
- Recall algorithm unit tests
- Cross-platform consistency tests

**Deliverable:** Passing test suite.

### Phase 15: Deployment and Android APK
- Docker compose for production
- Environment configuration
- Database migrations
- Static file serving
- EAS Build for Android APK
- Documentation updates

**Deliverable:** Deployed web app + distributable Android APK.

### Phase 16: Expo Demonstration Preparation
- Demo data seeding
- UI polish
- Loading states
- Error handling
- Demo script preparation
- Final documentation

**Deliverable:** Demo-ready application.

---

## 12. SECURITY & ENVIRONMENT

### 12.1 Environment Variables

```env
# .env.example
DEBUG=True
SECRET_KEY=change-me-in-production
DATABASE_URL=postgres://user:pass@localhost:5432/aptirecall
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1

# AI
AI_PROVIDER=ollama  # or openai
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
OPENAI_API_KEY=

# OCR
TESSERACT_CMD=C:\\Program Files\\Tesseract-OCR\\tesseract.exe
PADDLE_OCR_LANG=en

# TTS
TTS_PROVIDER=edge-tts
TTS_VOICE=en-US-JennyNeural

# File Upload
MAX_UPLOAD_SIZE=10485760  # 10MB
ALLOWED_EXTENSIONS=jpg,jpeg,png,pdf

# JWT
JWT_SECRET_KEY=
JWT_ACCESS_TOKEN_LIFETIME=3600
JWT_REFRESH_TOKEN_LIFETIME=604800

# Frontend
VITE_API_URL=http://localhost:8000/api
```

### 12.2 Security Measures

- Password hashing via Django's `set_password`
- JWT with short expiry + refresh token rotation
- File upload validation (size, type, magic bytes)
- CORS configuration (strict origins in production)
- Rate limiting (Django Ratelimit or Nginx)
- SQL injection prevention (ORM)
- XSS prevention (React auto-escaping + CSP headers)
- HTTPS enforcement in production
- Secrets in environment variables only

---

## 13. TESTING STRATEGY

### 13.1 Test Categories

| Category | Tool | Scope |
|----------|------|-------|
| Unit Tests | pytest | Business logic, services, algorithms |
| API Tests | pytest + DRF test client | Endpoint correctness, auth, validation |
| Math Tests | pytest | SymPy solver correctness with known values |
| OCR Tests | pytest + sample images | OCR accuracy on known images |
| Recall Tests | pytest | Algorithm behavior with synthetic data |
| Frontend | React Testing Library | Component behavior |
| Integration | pytest + testcontainers | End-to-end API flows |

### 13.2 Math Test Example

```python
# apps/solve/tests/test_solver.py
import pytest
from apps.solve.services.solver_service import SolverService

@pytest.mark.parametrize("question,expected", [
    ("What is 20% of 150?", "30"),
    ("A man buys an article for Rs.100 and sells for Rs.120. Profit%?", "20%"),
    ("Find LCM of 12 and 18", "36"),
])
def test_percentage_solver(question, expected):
    result = SolverService.solve(question)
    assert result.answer == expected
    assert result.is_verified is True
```

---

## 14. DEPLOYMENT ARCHITECTURE

### 14.1 Production Stack

```
Internet
    ↓
Nginx (reverse proxy + static files + SSL)
    ↓
Gunicorn / Uvicorn (Django ASGI)
    ↓
Celery Worker (async tasks)
    ↓
PostgreSQL (RDS or managed)
    ↓
Redis (ElastiCache or managed)
    ↓
S3-compatible storage (for media)
```

### 14.2 Docker Setup

```yaml
# docker-compose.yml (services: django, celery, redis, postgres, nginx)
```

### 14.3 Android Distribution

- Build via EAS Build (Expo Application Services)
- Generate APK/AAB
- Distribute via:
  - Direct APK download (website)
  - Google Play Store (optional)
  - Firebase App Distribution (for testing)

---

## 15. DOCUMENTATION PLAN

| Document | Content |
|----------|---------|
| 01_problem_statement.md | Problem, existing solutions, gap |
| 02_requirements.md | Functional & non-functional requirements |
| 03_architecture.md | This document |
| 04_database_design.md | ER diagrams, table descriptions |
| 05_api_documentation.md | All endpoints with examples |
| 06_ai_pipeline.md | LLM prompts, flow diagrams |
| 07_ocr_pipeline.md | OCR flow, preprocessing details |
| 08_verification_architecture.md | Verification methods, pseudocode |
| 09_recall_algorithm.md | AARA detailed explanation, pseudocode |
| 10_testing.md | Test plan, test cases, results |
| 11_deployment.md | Setup instructions, deployment steps |
| 12_user_manual.md | Screenshots, usage guide |

---

## 16. ARCHITECTURAL DECISIONS

| Decision | Rationale |
|----------|-----------|
| Django + DRF over FastAPI | Mature admin, built-in auth, large ecosystem, team familiarity |
| PostgreSQL over MongoDB | Strong consistency, JSON support, complex queries, relational integrity |
| Ollama over OpenAI-only | Free local inference, no API costs, offline capability, structured output |
| SymPy for math | Deterministic, open-source, handles symbolic algebra |
| Celery + Redis | Standard Python async task queue, proven at scale |
| React + Expo over Flutter | JavaScript/TypeScript across all platforms, shared logic possible |
| Tesseract over cloud OCR | Free, offline, no per-request cost |
| edge-tts over paid TTS | Free, no API key, good quality, offline capability |
| Separate AI service layer | Enables swapping LLM providers without touching business logic |

---

## 17. RISKS & MITIGATIONS

| Risk | Mitigation |
|------|-----------|
| LLM gives wrong math answer | Mandatory SymPy verification; reject unverified answers |
| OCR fails on complex math | Multi-engine fallback; user confirmation step |
| LLM hallucinates topics | Confidence threshold; fallback to keyword matching |
| Large image uploads slow API | Async Celery processing; return task ID immediately |
| Math solver coverage gaps | Fallback to "Needs Verification" state; log for improvement |
| Mobile build complexity | Use Expo managed workflow; avoid native modules initially |
| Performance with many users | PostgreSQL indexing; Redis caching; CDN for media |

---

## 18. NEXT STEPS

**Awaiting approval before implementing Phase 1.**

If approved, Phase 1 will:
1. Initialize the exact folder structure above
2. Create Django project with modular apps
3. Initialize React Vite project
4. Initialize Expo project
5. Setup docker-compose.yml
6. Create environment configuration
7. Verify all development servers start successfully

---

*Document Version: 1.0*
*Prepared by: Lead Software Architect*
*Date: 2026-10-02*
