from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response


class CreateQuizView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        user = request.user

        print("user ist :", user)
        print("request ist: ", request.data.get("url"))

        return Response({
            "id": user.id,
            "title": "Quiz Title",
            "description": "Quiz Description",
            "created_at": "2023-07-29T12:34:56.789Z",
            "updated_at": "2023-07-29T12:34:56.789Z",
            "video_url": "https://www.youtube.com/watch?v=example",
            "questions": [
                {
                    "id": 1,
                    "question_title": "Question 1",
                    "question_options": [
                        "Option A",
                        "Option B",
                        "Option C",
                        "Option D"
                    ],
                    "answer": "Option A",
                    "created_at": "2023-07-29T12:34:56.789Z",
                    "updated_at": "2023-07-29T12:34:56.789Z"
                }
            ]
        })


class QuizListView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        return Response({
            "test": "test2323"
        })