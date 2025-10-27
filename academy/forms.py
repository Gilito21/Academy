from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Profile, Quiz


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    full_name = forms.CharField(required=False)

    class Meta:
        model = User
        fields = ("username", "full_name", "email", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
            full_name = self.cleaned_data.get("full_name", "")
            if full_name:
                user.profile.full_name = full_name
                user.profile.save()
        return user


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ("full_name", "bio")


class QuizForm(forms.Form):
    def __init__(self, quiz: Quiz, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.quiz = quiz
        for question in quiz.questions.all():
            self.fields[f"question_{question.id}"] = forms.ChoiceField(
                label=question.text,
                widget=forms.RadioSelect,
                choices=[(choice.id, choice.text) for choice in question.choices.all()],
                required=True,
            )

    def get_selected_choices(self):
        for key, value in self.cleaned_data.items():
            if key.startswith("question_"):
                yield int(key.split("_")[1]), int(value)
