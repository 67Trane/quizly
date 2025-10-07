from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CreateQuizView, QuizViewSet

router = DefaultRouter()
router.register(r'quizzes', QuizViewSet, basename='quiz')


urlpatterns = [
    path("createQuiz/", CreateQuizView.as_view(), name="create-quiz"),
    path('', include(router.urls)),
]
