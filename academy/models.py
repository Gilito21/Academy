from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse


class TimeStampedModel(models.Model):
    """Abstract base model that tracks creation and update times."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Profile(TimeStampedModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    full_name = models.CharField(max_length=255, blank=True)
    bio = models.TextField(blank=True)

    def __str__(self) -> str:
        return self.full_name or self.user.get_username()


class Module(TimeStampedModel):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    image = models.ImageField(upload_to="modules/images/", blank=True, null=True)
    is_recommended = models.BooleanField(default=False)

    class Meta:
        ordering = ["title"]

    def __str__(self) -> str:
        return self.title

    def get_absolute_url(self):
        return reverse("academy:module_detail", args=[self.slug])


class Lesson(TimeStampedModel):
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    video = models.FileField(upload_to="lessons/videos/")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return f"{self.module.title} - {self.title}"


class ModuleAccess(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="module_accesses")
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name="accesses")
    purchased_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "module")

    def __str__(self) -> str:
        return f"{self.user} -> {self.module}"


class Quiz(TimeStampedModel):
    module = models.OneToOneField(Module, on_delete=models.CASCADE, related_name="quiz")
    title = models.CharField(max_length=200)
    passing_score = models.PositiveIntegerField(default=70, help_text="Percentage required to pass")

    def __str__(self) -> str:
        return f"Quiz for {self.module.title}"


class Question(TimeStampedModel):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField()

    def __str__(self) -> str:
        return self.text


class Choice(TimeStampedModel):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="choices")
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.text


class QuizSubmission(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="quiz_submissions")
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="submissions")
    score = models.PositiveIntegerField()
    total_questions = models.PositiveIntegerField()
    passed = models.BooleanField(default=False)

    class Meta:
        unique_together = ("user", "quiz")

    def __str__(self) -> str:
        return f"{self.user} - {self.quiz} ({self.score}/{self.total_questions})"
