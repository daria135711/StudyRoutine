from django.urls import path
from .views import ExamListView, ExamDetailView, ExamCreateView, ExamUpdateView, ExamDeleteView

app_name = 'exams'

urlpatterns = [
    path('', ExamListView.as_view(), name='list'),
    path('<int:pk>/', ExamDetailView.as_view(), name='detail'),
    path('new/', ExamCreateView.as_view(), name='create'),
    path('<int:pk>/update/', ExamUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', ExamDeleteView.as_view(), name='delete'),
]