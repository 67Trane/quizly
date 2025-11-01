from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CreateQuizView, QuizViewSet

# Initialize a DRF router for automatic route generation of QuizViewSet
router = DefaultRouter()
router.register(r"quizzes", QuizViewSet, basename="quiz")

"""
Defines URL routes for the Quiz app.
Includes both:
- a custom endpoint for quiz creation (CreateQuizView),
- and RESTful routes for listing, retrieving, updating, and deleting quizzes (QuizViewSet).
"""
urlpatterns = [
    # Custom endpoint to create a quiz from a YouTube video or transcript
    path("createQuiz/", CreateQuizView.as_view(), name="create-quiz"),
    # Include automatically generated CRUD routes from the router
    path("", include(router.urls)),
]
