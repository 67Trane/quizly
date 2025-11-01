from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from .functions import process_youtube_quiz
from ..models import Quiz, Question
from rest_framework import status
from .serializers import QuizSerializer
from rest_framework import viewsets


class CreateQuizView(APIView):
    """
    API endpoint for creating a new quiz based on a YouTube video.
    The process involves:
      1. Downloading and transcribing the video audio,
      2. Generating quiz questions via AI,
      3. Saving the resulting quiz and questions in the database.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Accepts a POST request containing a YouTube video URL.
        Returns the created quiz with its generated questions.
        """
        url = request.data.get("url")
        if not url:
            return Response(
                {"detail": "no url found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Process YouTube link to create quiz data (title, description, questions)
            data = process_youtube_quiz(url)
        except Exception as e:
            return Response(
                {"detail": f"process failed: {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Extract core quiz fields
        title = data.get("title")
        description = data.get("description")
        video_url = url
        questions_data = data.get("questions")

        # Create a new quiz entry
        quiz = Quiz.objects.create(
            title=title,
            description=description,
            video_url=video_url,
        )

        # Prepare question objects for bulk insertion
        questions_obj = []
        for q in questions_data:
            questions_obj.append(
                Question(
                    quiz=quiz,
                    question_title=q.get("question_title") or "",
                    question_options=q.get("question_options"),
                    answer=q.get("answer") or "",
                )
            )

        # Perform efficient bulk insert if there are questions
        if questions_obj:
            Question.objects.bulk_create(questions_obj)

        # Serialize the created quiz with related questions
        serializer = QuizSerializer(quiz)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class QuizViewSet(viewsets.ModelViewSet):
    """
    Standard ModelViewSet providing CRUD operations for Quiz objects.
    Includes nested question data via QuizSerializer.
    """

    queryset = Quiz.objects.prefetch_related("questions").all()
    serializer_class = QuizSerializer
    permission_classes = [IsAuthenticated]
