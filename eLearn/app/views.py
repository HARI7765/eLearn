from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.contrib.auth.models import User
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from django.core.mail import send_mail
from django.conf import settings
from functools import wraps
from django.utils import timezone
from datetime import datetime, timedelta
from django.http import HttpResponse
from .models import Category, Course, Lesson, Progress, Contact
from .forms import CourseForm


# -------------------- Custom Decorators --------------------

def custom_login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            request.session['next_url'] = request.get_full_path()
            return render(request, 'oops_login_required.html', {
                'message': 'Oops! You need to login to access this page.',
                'redirect_url': request.get_full_path(),
                'page_title': 'Login Required'
            })
        return view_func(request, *args, **kwargs)
    return wrapper

def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        elif not request.user.is_superuser:
            return render(request, 'admin_required.html', {
                'message': 'You need admin privileges to access this page.'
            })
        return view_func(request, *args, **kwargs)
    return wrapper

# -------------------- Views --------------------

def index(request, id=None):
    course_id = id
    query = request.GET.get('q')
    courses = Course.objects.all()
    if query:
        courses = courses.filter(Q(title__icontains=query) | Q(description__icontains=query))
    categories = Category.objects.prefetch_related('courses').all()
    return render(request, 'main/index.html', {
        'course_id': course_id,
        'courses': courses,
        'categories': categories,
        'query': query
    })

def about_view(request):
    return render(request, 'main/about.html')

@custom_login_required
def progress_view(request):
    progress_items = Progress.objects.filter(user=request.user)
    total_lessons = Lesson.objects.filter(course__in=progress_items.values('course')).count()
    completed_lessons = progress_items.filter(completed=True).count()
    completion_rate = (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0
    return render(request, 'progress.html', {
        'progress_items': progress_items,
        'total_lessons': total_lessons,
        'completed_lessons': completed_lessons,
        'completion_rate': round(completion_rate, 2)
    })

@custom_login_required
def enrolled_courses_view(request):
    enrolled_courses = Course.objects.filter(progress__user=request.user).distinct()
    return render(request, 'enrolled_courses.html', {'enrolled_courses': enrolled_courses})

def course_detail_view(request, id):
    course = get_object_or_404(Course, id=id)
    lessons = Lesson.objects.filter(course=course)
    enrolled = False
    if request.user.is_authenticated:
        enrolled = Progress.objects.filter(user=request.user, course=course).exists()
    if request.method == 'POST' and request.user.is_authenticated:
        lesson_id = request.POST.get('lesson_id')
        if lesson_id:
            lesson = get_object_or_404(Lesson, id=lesson_id, course=course)
            progress, _ = Progress.objects.get_or_create(user=request.user, lesson=lesson, course=course)
            progress.completed = not progress.completed
            progress.completed_at = timezone.now() if progress.completed else None
            progress.save()
            messages.success(request, f"Lesson '{lesson.title}' marked as {'completed' if progress.completed else 'incomplete'}.")
        else:
            for lesson in lessons:
                Progress.objects.get_or_create(user=request.user, lesson=lesson, course=course)
            messages.success(request, f"You have enrolled in '{course.title}'!")
        return redirect('course_detail', id=course.id)
    return render(request, 'course_detail.html', {
        'course': course,
        'lessons': lessons,
        'enrolled': enrolled
    })

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            next_url = request.session.pop('next_url', None)
            return redirect(next_url or 'index')
    else:
        form = UserCreationForm()
    return render(request, 'signup.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('index')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        if user:
            login(request, user)
            request.session['username'] = username
            next_url = request.session.pop('next_url', None)
            return redirect(next_url or ('admin_dashboard' if user.is_superuser else 'index'))
        messages.error(request, "Invalid credentials.")
    return render(request, 'login/signin.html')

@admin_required
def admin_dashboard_view(request):
    courses = Course.objects.all()
    total_enrollments = Progress.objects.values('course').distinct().count()
    total_users = User.objects.count()
    return render(request, 'admin/admin_dashboard.html', {
        'total_enrollments': total_enrollments,
        'total_users': total_users,
        'courses': courses,
    })

def signup(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirmpassword = request.POST.get('confirmpassword')
        if not username or not email or not password or not confirmpassword:
            messages.error(request, 'All fields are required.')
        elif confirmpassword != password:
            messages.error(request, "Passwords do not match.")
        elif User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
        elif User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            login(request, user)
            messages.success(request, "Account created successfully!")
            next_url = request.session.pop('next_url', None)
            return redirect(next_url or 'login')
    return render(request, "login/signup.html")

@admin_required
def add_course_view(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        image = request.FILES.get('image')
        description = request.POST.get('description')
        category_id = request.POST.get('category')
        category = get_object_or_404(Category, id=category_id)
        Course.objects.create(title=title, image=image, description=description, category=category)
        messages.success(request, f"Course '{title}' added successfully!")
        return redirect('admin_dashboard')
    categories = Category.objects.all()
    return render(request, 'courses/add_course.html', {'categories': categories})

@admin_required
@require_http_methods(["GET", "POST"])
def edit_course_view(request, id):
    course = get_object_or_404(Course, id=id)
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, f"Course '{course.title}' updated successfully.")
            return redirect('admin_dashboard')
    else:
        form = CourseForm(instance=course)
    categories = Category.objects.all()
    return render(request, 'courses/edit_course.html', {
        'form': form,
        'course': course,
        'categories': categories
    })

def course_list_view(request):
    courses = Course.objects.all()
    return render(request, 'courses/course_list.html', {'courses': courses})

@admin_required
def delete_course_view(request, id):
    course = get_object_or_404(Course, id=id)
    if request.method == 'POST':
        course.delete()
        messages.success(request, f"Course '{course.title}' deleted successfully.")
        return redirect('admin_dashboard')
    return render(request, 'courses/delete_course.html', {'course': course})

def logout_view(request):
    if request.method == 'POST':
        logout(request)
        messages.success(request, "You have been logged out successfully.")
        return redirect('login')
    return render(request, 'logout_confirm.html')

@custom_login_required
def profile_view(request):
    progress = Progress.objects.filter(user=request.user)
    return render(request, 'user/profile.html', {
        'username': request.user.username,
        'email': request.user.email,
        'progress': progress,
    })

def contact_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        Contact.objects.create(name=name, email=email, message=message)
        try:
            send_mail(
                subject=f'New Contact Form Submission from {name}',
                message=f"Name: {name}\nEmail: {email}\nMessage: {message}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=['test1project11@gmail.com'],
                fail_silently=False,
            )
            messages.success(request, "Your message has been sent successfully!")
        except Exception as e:
            messages.error(request, f"Email not sent. Error: {e}")
    return render(request, 'contacts/contact.html')

@custom_login_required
def enroll_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    lessons = Lesson.objects.filter(course=course)
    for lesson in lessons:
        Progress.objects.get_or_create(user=request.user, lesson=lesson, course=course)
    messages.success(request, f"You have enrolled in '{course.title}'!")
    return redirect('course_detail', id=course.id)
