from django.contrib import admin
from .models import StudyPlan

@admin.register(StudyPlan)
class StudyPlanAdmin(admin.ModelAdmin):
    list_display = ('planned_date', 'id_plan', 'id_topic', 'repetition_number', 'is_done')
    list_display_links = ('id_plan',)
    list_filter = ('planned_date', 'is_done', 'repetition_number')
    search_fields = ('id_topic__title',)
    ordering = ('planned_date',)
    list_editable = ('is_done',)
    
    # Фильтр по датам
    date_hierarchy = 'planned_date'