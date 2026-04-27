from django.shortcuts import render

def dashboard(request):
    return render(request, 'dashboard.html')

def exams_list(request):
    return render(request, 'exams/list.html')

def exam_detail(request, exam_id):
    return render(request, 'exams/detail.html', {'exam_id': exam_id})

def stats(request):
    return render(request, 'stats.html')