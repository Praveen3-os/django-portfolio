from django.contrib import admin
from django.urls import path
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Core Application Pages
    path('', views.home_view, name='home'),
    path('about/', views.about_view, name='about'),
    path('skills/', views.skills_view, name='skills'),
    path('faqs/', views.faqs_view, name='faqs'),
    path('errors/', views.errors_view, name='errors'),
    path('health/', views.health_view, name='health'),
    path('contact/', views.contact_view, name='contact'),

    # API Endpoints
    path('api/chat/', views.api_chat, name='api_chat'),
    path('api/tickets/', views.api_ticket_create, name='api_ticket_create'),
    path('api/feedback/', views.api_feedback, name='api_feedback'),
    path('api/quote/', views.api_quote, name='api_quote'),

    # Simulated Error Triggers & Direct Previews
    path('test-500/', views.test_500_view, name='test_500'),
    path('404/', views.custom_404_view, name='custom_404'),
    path('500/', views.custom_500_view, name='custom_500'),
]

# Custom Error Handlers
handler404 = 'core.views.custom_404_view'
handler500 = 'core.views.custom_500_view'
