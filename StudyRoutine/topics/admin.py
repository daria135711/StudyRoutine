from django.contrib import admin
from .models import Topic

@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    # Первое поле в list_display не должно быть ссылкой, если есть list_editable (Django).
    list_display = ('title', 'id_topic', 'id_exam', 'priority', 'is_complete')
    list_display_links = ('title',)
    list_filter = ('is_complete', 'priority', 'id_exam')
    search_fields = ('title', 'description')
    ordering = ('-priority', 'title')
    
    list_editable = ('is_complete', 'priority')
