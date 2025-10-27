from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import ListView

from .forms import ProfileForm, QuizForm, UserRegistrationForm
from .models import Choice, Lesson, Module, ModuleAccess, Quiz, QuizSubmission


class HomeView(ListView):
    model = Module
    template_name = "academy/home.html"
    context_object_name = "modules"

    def get_queryset(self):
        return (
            Module.objects.prefetch_related("lessons")
            .all()
            .order_by("-is_recommended", "title")
        )


@login_required
def dashboard(request: HttpRequest) -> HttpResponse:
    purchased_modules = (
        Module.objects.filter(accesses__user=request.user)
        .distinct()
        .prefetch_related("lessons")
    )
    quiz_results = QuizSubmission.objects.filter(user=request.user).select_related("quiz", "quiz__module")
    return render(
        request,
        "academy/dashboard.html",
        {"modules": purchased_modules, "quiz_results": quiz_results},
    )


def module_detail(request: HttpRequest, slug: str) -> HttpResponse:
    module = get_object_or_404(Module.objects.prefetch_related("lessons"), slug=slug)
    has_access = False
    if request.user.is_authenticated:
        has_access = ModuleAccess.objects.filter(user=request.user, module=module).exists()
    quiz = getattr(module, "quiz", None)
    return render(
        request,
        "academy/module_detail.html",
        {"module": module, "has_access": has_access, "quiz": quiz},
    )


@login_required
def lesson_detail(request: HttpRequest, slug: str, lesson_id: int) -> HttpResponse:
    module = get_object_or_404(Module, slug=slug)
    access_granted = ModuleAccess.objects.filter(user=request.user, module=module).exists()
    if not access_granted:
        messages.error(request, "You need to purchase this module before viewing the lessons.")
        return redirect(module.get_absolute_url())
    lesson = get_object_or_404(Lesson, module=module, id=lesson_id)
    return render(
        request,
        "academy/lesson_detail.html",
        {"module": module, "lesson": lesson},
    )


@login_required
def purchase_module(request: HttpRequest, slug: str) -> HttpResponse:
    module = get_object_or_404(Module, slug=slug)
    ModuleAccess.objects.get_or_create(user=request.user, module=module)
    messages.success(request, f"You now have access to {module.title}.")
    return redirect(module.get_absolute_url())


@login_required
def take_quiz(request: HttpRequest, slug: str) -> HttpResponse:
    module = get_object_or_404(Module, slug=slug)
    quiz = get_object_or_404(Quiz, module=module)
    access_granted = ModuleAccess.objects.filter(user=request.user, module=module).exists()
    if not access_granted:
        messages.error(request, "Purchase the module before attempting the quiz.")
        return redirect(module.get_absolute_url())

    submission = QuizSubmission.objects.filter(user=request.user, quiz=quiz).first()
    form = QuizForm(quiz, request.POST or None)

    if request.method == "POST" and form.is_valid():
        total_questions = quiz.questions.count()
        correct_answers = 0
        for question_id, choice_id in form.get_selected_choices():
            choice = get_object_or_404(Choice, id=choice_id, question_id=question_id)
            if choice.is_correct:
                correct_answers += 1
        score = int((correct_answers / total_questions) * 100) if total_questions else 0
        passed = score >= quiz.passing_score
        submission, _ = QuizSubmission.objects.update_or_create(
            user=request.user,
            quiz=quiz,
            defaults={
                "score": score,
                "total_questions": total_questions,
                "passed": passed,
            },
        )
        if passed:
            messages.success(request, "Congratulations! You passed the module quiz.")
        else:
            messages.warning(request, "You did not pass the quiz. Review the lessons and try again.")
        return redirect("academy:take_quiz", slug=module.slug)

    return render(
        request,
        "academy/quiz.html",
        {
            "module": module,
            "quiz": quiz,
            "form": form,
            "submission": submission,
        },
    )


def register(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("academy:dashboard")

    form = UserRegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        raw_password = form.cleaned_data.get("password1")
        authenticated_user = authenticate(username=user.username, password=raw_password)
        if authenticated_user:
            login(request, authenticated_user)
            messages.success(request, "Welcome to Close The Gap Academy!")
            return redirect("academy:dashboard")
        messages.info(request, "Registration successful. Please log in.")
        return redirect("login")

    return render(request, "academy/register.html", {"form": form})


@login_required
def edit_profile(request: HttpRequest) -> HttpResponse:
    profile = request.user.profile
    form = ProfileForm(request.POST or None, instance=profile)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Profile updated successfully.")
        return redirect("academy:dashboard")
    return render(request, "academy/profile.html", {"form": form})
