from django.contrib import admin
from .models import StudySession

@admin.register(StudySession)
class StudySessionAdmin(admin.ModelAdmin):
    # Обновлённый список полей
    list_display = (
        'id',                       # стандартный pk
        'user',                     # кто занимался
        'topic_title',              # тема (через кастомный метод)
        'start_time',               # вместо date
        'duration_minutes',
        'session_length',           # вычисляемая длительность
        'has_notes'                 # индикатор наличия заметок
    )
    
    # Фильтры по актуальным полям
    list_filter = ('start_time', 'topic', 'user')
    
    # Поиск по пользователю, теме, заметкам
    search_fields = ('user__username', 'topic__title', 'notes')
    
    # Сортировка (уже есть в модели, но можно переопределить)
    ordering = ('-start_time',)
    
    # Редактируемые поля (duration_minutes удобно редактировать)
    list_editable = ('duration_minutes',)
    
    # Иерархия по дате
    date_hierarchy = 'start_time'
    
    # Оптимизация запросов
    list_select_related = ('user', 'topic')
    
    # Группировка полей в форме редактирования
    fieldsets = (
        ('Основное', {
            'fields': ('user', 'topic', 'start_time', 'end_time', 'duration_minutes')
        }),
        ('Дополнительно', {
            'fields': ('notes',),
            'classes': ('wide',)
        })
    )
    
    # Только для чтения
    readonly_fields = ('start_time',)
    
    # Кастомные методы
    def topic_title(self, obj):
        return obj.topic.title if obj.topic else '(без темы)'
    topic_title.short_description = 'Тема'
    topic_title.admin_order_field = 'topic__title'
    
    def session_length(self, obj):
        """Вычисляет длительность, если не указана"""
        if obj.duration_minutes:
            return f"{obj.duration_minutes} мин"
        elif obj.start_time and obj.end_time:
            delta = obj.end_time - obj.start_time
            minutes = int(delta.total_seconds() / 60)
            return f"{minutes} мин (вычислено)"
        return "-"
    session_length.short_description = 'Длительность'
    
    def has_notes(self, obj):
        return bool(obj.notes)
    has_notes.boolean = True
    has_notes.short_description = 'Заметки'
    
    # Действия для нескольких записей
    actions = ['add_10_minutes', 'clear_notes']
    
    def add_10_minutes(self, request, queryset):
        for session in queryset:
            session.duration_minutes += 10
            session.save()
    add_10_minutes.short_description = 'Добавить 10 минут к выбранным'
    
    def clear_notes(self, request, queryset):
        queryset.update(notes='')
    clear_notes.short_description = 'Очистить заметки'