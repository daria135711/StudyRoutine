from django.contrib import admin
from .models import Topic

@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    # Исправленные поля
    list_display = (
        'id',               # вместо id_topic
        'title',
        'exam_title',       # вместо id_exam (кастомный метод)
        'priority',
        'is_completed',     # вместо is_complete
        'estimated_time',
        'created_at'
    )
    
    list_display_links = ('id', 'title')
    
    # Исправленные фильтры
    list_filter = ('is_completed', 'priority', 'exam')
    
    # Поиск по полям (всё верно)
    search_fields = ('title', 'description')
    
    # Исправленная сортировка
    ordering = ('-priority', 'title')
    
    # Редактируемые поля
    list_editable = ('is_completed', 'priority')
    
    # Дополнительные полезные настройки
    list_select_related = ('exam',)  # оптимизация запросов
    date_hierarchy = 'created_at'     # навигация по датам
    list_per_page = 25
    
    # Кастомный метод для отображения экзамена
    def exam_title(self, obj):
        return obj.exam.title if obj.exam else '-'
    exam_title.short_description = 'Экзамен'
    exam_title.admin_order_field = 'exam__title'
    
    # Цветная индикация статуса (опционально)
    def colored_status(self, obj):
        from django.utils.html import format_html
        if obj.is_completed:
            return format_html('<span style="color: green; font-weight: bold;">✓ Изучено</span>')
        return format_html('<span style="color: gray;">○ Не изучено</span>')
    colored_status.short_description = 'Статус'
    
    # Действия для нескольких записей
    actions = ['mark_as_completed', 'mark_as_not_completed', 'increase_priority']
    
    def mark_as_completed(self, request, queryset):
        queryset.update(is_completed=True)
    mark_as_completed.short_description = 'Отметить выбранные как "Изучено"'
    
    def mark_as_not_completed(self, request, queryset):
        queryset.update(is_completed=False)
    mark_as_not_completed.short_description = 'Отметить выбранные как "Не изучено"'
    
    def increase_priority(self, request, queryset):
        for topic in queryset:
            topic.priority += 1
            topic.save()
    increase_priority.short_description = 'Увеличить приоритет на 1'
