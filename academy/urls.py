from django.urls import path

from .views import (
    HomeView,
    dashboard,
    edit_profile,
    lesson_detail,
    module_detail,
    purchase_module,
    register,
    take_quiz,
)

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("dashboard/", dashboard, name="dashboard"),
    path("register/", register, name="register"),
    path("profile/", edit_profile, name="profile"),
    path("modules/<slug:slug>/", module_detail, name="module_detail"),
    path("modules/<slug:slug>/lessons/<int:lesson_id>/", lesson_detail, name="lesson_detail"),
    path("modules/<slug:slug>/purchase/", purchase_module, name="purchase_module"),
    path("modules/<slug:slug>/quiz/", take_quiz, name="take_quiz"),
]
