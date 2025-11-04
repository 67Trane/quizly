from django.contrib import admin
from django.utils.html import format_html
from django import forms

from .models import Quiz, Question

try:
    from django.contrib.admin.widgets import AdminJSONEditor

    HAS_JSON_EDITOR = True
except Exception:
    HAS_JSON_EDITOR = False


class QuestionInlineForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ["question_title", "question_options", "answer"]

        # Schöner JSON-Editor, wenn verfügbar
        if HAS_JSON_EDITOR:
            widgets = {
                "question_options": AdminJSONEditor,
            }


class QuestionInline(admin.TabularInline):
    model = Question
    form = QuestionInlineForm
    extra = 0
    show_change_link = True
    fields = ("question_title", "question_options", "answer")
    verbose_name = "Frage"
    verbose_name_plural = "Fragen"


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "short_description",
        "video_url_link",
        "question_count",
        "created_at",
    )
    list_display_links = ("id", "title")
    search_fields = (
        "title__icontains",
        "description__icontains",
        "video_url__icontains",
    )
    list_filter = ("created_at",)
    date_hierarchy = "created_at"
    inlines = [QuestionInline]
    readonly_fields = ("created_at", "updated_at")
    actions = ["rebuild_from_video"]

    fieldsets = (
        (None, {"fields": ("title", "description", "video_url")}),
        ("Meta", {"fields": ("created_at", "updated_at")}),
    )

    @admin.display(description="Beschreibung")
    def short_description(self, obj: Quiz):
        if not obj.description:
            return "-"
        return (
            (obj.description[:80] + "…")
            if len(obj.description) > 80
            else obj.description
        )

    @admin.display(description="Video")
    def video_url_link(self, obj: Quiz):
        if not obj.video_url:
            return "-"
        return format_html(
            '<a href="{}" target="_blank" rel="noopener">Link öffnen</a>', obj.video_url
        )

    @admin.display(description="Fragen")
    def question_count(self, obj: Quiz):
        return obj.questions.count()

    @admin.action(description="Quiz aus Video-URL neu generieren (überschreibt Fragen)")
    def rebuild_from_video(self, request, queryset):
        """
        Re-runner: ruft deine bestehende Prozesslogik auf und ersetzt die Fragen.
        ACHTUNG: Überschreibt vorhandene Fragen des/der gewählten Quizze(s).
        """
        from .api.functions import process_youtube_quiz

        updated = 0
        for quiz in queryset:
            try:
                data = process_youtube_quiz(quiz.video_url)
                quiz.title = data.get("title") or quiz.title
                quiz.description = data.get("description") or quiz.description
                quiz.save()

                quiz.questions.all().delete()
                questions_data = data.get("questions") or []
                Question.objects.bulk_create(
                    [
                        Question(
                            quiz=quiz,
                            question_title=q.get("question_title") or "",
                            question_options=q.get("question_options"),
                            answer=q.get("answer") or "",
                        )
                        for q in questions_data
                    ]
                )
                updated += 1
            except Exception as e:
                self.message_user(
                    request, f"Fehler bei Quiz {quiz.id}: {e}", level="error"
                )

        self.message_user(request, f"{updated} Quizze neu generiert.")


class QuestionAdminForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = "__all__"
        if HAS_JSON_EDITOR:
            widgets = {
                "question_options": AdminJSONEditor,
            }


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    form = QuestionAdminForm
    list_display = ("id", "quiz_title", "short_question", "answer")
    list_display_links = ("id", "short_question")
    search_fields = (
        "question_title__icontains",
        "answer__icontains",
        "quiz__title__icontains",
    )
    list_filter = ("quiz",)
    autocomplete_fields = ("quiz",)

    @admin.display(description="Quiz")
    def quiz_title(self, obj: Question):
        return obj.quiz.title

    @admin.display(description="Frage")
    def short_question(self, obj: Question):
        return (
            (obj.question_title[:80] + "…")
            if len(obj.question_title) > 80
            else obj.question_title
        )
