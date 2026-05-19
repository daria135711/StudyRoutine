from django.contrib import admin
from .models import StudySession

@admin.register(StudySession)
class StudySessionAdmin(admin.ModelAdmin):
    list_display = ('date', 'id_session', 'id_topic', 'duration_minutes', 'completed')
    list_display_links = ('id_session',)
    list_filter = ('date', 'completed')
    search_fields = ('id_topic__title',)
    ordering = ('-date',)
    list_editable = ('completed',)
    date_hierarchy = 'date'