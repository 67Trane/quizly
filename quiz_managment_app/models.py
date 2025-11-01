from django.db import models


class Quiz(models.Model):
    """
    Represents a quiz generated from a YouTube video or transcript.
    Stores metadata such as title, description, and video URL.
    """

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    video_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        """Return a human-readable representation of the quiz."""
        return self.title


class Question(models.Model):
    """
    Represents a single question belonging to a quiz.
    Each question includes:
      - the question text,
      - four answer options (stored as JSON),
      - and one correct answer.
    """

    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name="questions",
    )
    question_title = models.TextField()
    question_options = models.JSONField()
    answer = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        """Return a readable representation including quiz and question title."""
        return f"{self.quiz.title}: {self.question_title[:50]}"
