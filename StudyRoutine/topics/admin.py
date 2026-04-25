from django.contrib import admin
from .models import Topic

@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('id_topic', 'title', 'id_exam', 'priority', 'is_complete')
    list_display_links = ('id_topic', 'title')
    list_filter = ('is_complete', 'priority', 'id_exam')
    search_fields = ('title', 'description')
    ordering = ('-priority', 'title')
    
    list_editable = ('is_complete', 'priority')
