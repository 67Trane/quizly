from django.urls import path
from .views import CreateQuizView, QuizListView

urlpatterns = [
    path("createQuiz/", CreateQuizView.as_view(), name="registration"),
    path("quizzes/", QuizListView.as_view(), name="registration"),
]