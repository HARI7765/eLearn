from django.urls import path
from . import views

urlpatterns = [
    # Home and informational pages
    path('', views.index, name='index'),  # Homepage with search and categories
    path('about/', views.about_view, name='about'),  # About page
    path('contact/', views.contact_view, name='contact'),  # Contact form page

    # Course-related pages
    path('courses/', views.course_list_view, name='course_list'),  # List all courses with search
    path('course/<int:course_id>/', views.course_detail_view, name='course_detail'),  # Course detail with enrollment
    path('course/<int:course_id>/enroll/', views.enroll_course, name='enroll_course'),  # Enroll in a course
    path('enrolled-courses/', views.enrolled_courses_view, name='enrolled_courses'),  # List enrolled courses

    # User-related pages
    path('signup/', views.signup, name='signup'),  # User registration
    path('login/', views.login_view, name='login'),  # User login
    path('logout/', views.logout, name='logout'),  # User logout
    path('accounts/profile/', views.profile_view, name='profile'),  # User profile management
    path('progress/', views.progress_view, name='progress'),  # User progress tracking

    # Admin-related pages
    path('admin-dashboard/', views.admin_dashboard_view, name='admin_dashboard'),  # Admin dashboard
    path('admin/add-course/', views.add_course_view, name='add_course'),  # Add new course
    path('admin/edit-course/<int:course_id>/', views.edit_course_view, name='edit_course'),  # Edit existing course
    path('admin/delete-course/<int:course_id>/', views.delete_course_view, name='delete_course'),  # Delete course

    # Error pages
     # Login required error
    path('admin-required/', views.admin_required, name='admin_required'),  # Admin access required error
]