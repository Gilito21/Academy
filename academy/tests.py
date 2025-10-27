import os
import shutil
import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from .models import Choice, Lesson, Module, ModuleAccess, Question, Quiz, QuizSubmission


def create_test_video():
    return SimpleUploadedFile("lesson.mp4", b"fake-video", content_type="video/mp4")


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class AcademyViewsTests(TestCase):
    def setUp(self):
        self.client: Client = Client()
        self.user = User.objects.create_user(username="student", password="password123", email="student@example.com")
        self.module = Module.objects.create(title="Test Module", slug="test-module", description="Module description", price=19.99)
        self.lesson = Lesson.objects.create(
            module=self.module,
            title="Lesson 1",
            description="Lesson description",
            video=create_test_video(),
            order=1,
        )
        self.quiz = Quiz.objects.create(module=self.module, title="Module Quiz", passing_score=70)
        self.question = Question.objects.create(quiz=self.quiz, text="What is 2+2?")
        self.correct_choice = Choice.objects.create(question=self.question, text="4", is_correct=True)
        self.wrong_choice = Choice.objects.create(question=self.question, text="5", is_correct=False)

    @classmethod
    def tearDownClass(cls):
        media_root = cls._overridden_settings["MEDIA_ROOT"]
        super().tearDownClass()
        if os.path.isdir(media_root):
            shutil.rmtree(media_root)

    def test_home_page_accessible(self):
        response = self.client.get(reverse("academy:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Close The Gap Academy")

    def test_module_purchase_creates_access(self):
        self.client.login(username="student", password="password123")
        response = self.client.get(reverse("academy:purchase_module", args=[self.module.slug]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(ModuleAccess.objects.filter(user=self.user, module=self.module).exists())

    def test_quiz_submission_scores_correctly(self):
        self.client.login(username="student", password="password123")
        ModuleAccess.objects.create(user=self.user, module=self.module)
        response = self.client.post(
            reverse("academy:take_quiz", args=[self.module.slug]),
            data={f"question_{self.question.id}": str(self.correct_choice.id)},
        )
        self.assertEqual(response.status_code, 302)
        submission = QuizSubmission.objects.get(user=self.user, quiz=self.quiz)
        self.assertEqual(submission.score, 100)
        self.assertTrue(submission.passed)
