from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from .functions import process_youtube_quiz
from ..models import Quiz, Question
from rest_framework import status
from .serializers import QuizSerializer


class CreateQuizView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):

        url = request.data.get("url")
        if not url:
            return Response({"detail": "no url found"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            data = process_youtube_quiz(url)
        except Exception as e:
            return Response({"detail": f"process failed: {e}"})

        title = data.get("title")
        description = data.get("description")
        video_url = url
        questions_data = data.get("questions")
        quiz = Quiz.objects.create(
            title=title, description=description, video_url=video_url)

        questions_obj = []
        for q in questions_data:
            questions_obj.append(Question(
                quiz=quiz,
                question_title=q.get("question_title") or "",
                question_options=q.get("question_options"),
                answer=q.get("answer") or "",
            ))

        if questions_obj:
            Question.objects.bulk_create(questions_obj)

        serializer = QuizSerializer(quiz)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class QuizListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({
            "test": "test2323"
        })
