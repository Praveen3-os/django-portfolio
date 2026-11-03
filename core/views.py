import json
import time
from datetime import datetime
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from .models import FAQ, ErrorCode, SupportTicket, RequestLog
from .mongo_service import mongo_client
from .ai_service import ai_assistant
from .third_party_api import fetch_third_party_quote
from .middleware import RECENT_REQUESTS

SERVER_START_TIME = time.time()

def get_client_ip(request):
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '127.0.0.1')

# Page 1: Home / Command Center
def home_view(request):
    total_faqs = FAQ.objects.count()
    total_errors = ErrorCode.objects.count()
    total_tickets = SupportTicket.objects.count()
    mongo_status = mongo_client.get_status()

    context = {
        'page_title': 'Command Center // Home',
        'active_page': 'home',
        'total_faqs': total_faqs,
        'total_errors': total_errors,
        'total_tickets': total_tickets,
        'mongo_status': mongo_status,
    }
    return render(request, 'index.html', context)

# Page 2: About & Fellowship
def about_view(request):
    context = {
        'page_title': 'About // Mechatronics & ProtoSem',
        'active_page': 'about',
    }
    return render(request, 'about.html', context)

# Technical Skills
def skills_view(request):
    context = {
        'page_title': 'Skills & Engineering Stack',
        'active_page': 'skills',
    }
    return render(request, 'skills.html', context)

# Page 3: FAQs (Minimum 10 FAQs stored in SQL and displayed here)
def faqs_view(request):
    query = request.GET.get('q', '').strip()
    category = request.GET.get('category', '').strip()

    faqs = FAQ.objects.all()
    if category and category != 'All':
        faqs = faqs.filter(category=category)
    if query:
        faqs = faqs.filter(
            Q(question__icontains=query) |
            Q(answer__icontains=query) |
            Q(keywords__icontains=query)
        )

    categories = ['All'] + list(FAQ.objects.values_list('category', flat=True).distinct())

    context = {
        'page_title': 'Knowledge Base & SQL FAQs',
        'active_page': 'faqs',
        'faqs': faqs,
        'categories': categories,
        'selected_category': category or 'All',
        'search_query': query,
        'total_count': faqs.count(),
    }
    return render(request, 'faqs.html', context)

# Error Codes Explorer (Minimum 8 Error Codes stored in SQL)
def errors_view(request):
    error_codes = ErrorCode.objects.all().order_by('code')
    context = {
        'page_title': 'HTTP Error Codes Registry',
        'active_page': 'errors',
        'error_codes': error_codes,
        'total_codes': error_codes.count(),
    }
    return render(request, 'errors.html', context)

# Health Check & Request Logging Telemetry
def health_view(request):
    uptime_sec = int(time.time() - SERVER_START_TIME)
    hours, rem = divmod(uptime_sec, 3600)
    mins, secs = divmod(rem, 60)
    uptime_str = f"{hours}h {mins}m {secs}s"

    sql_stats = {
        'faqs': FAQ.objects.count(),
        'error_codes': ErrorCode.objects.count(),
        'tickets': SupportTicket.objects.count(),
        'request_logs': RequestLog.objects.count(),
    }

    mongo_status = mongo_client.get_status()

    # Test third-party API
    third_party_data = fetch_third_party_quote(timeout_sec=2.0)

    # Use in-memory recent requests or query DB
    recent_logs = RECENT_REQUESTS[:20] if RECENT_REQUESTS else list(
        RequestLog.objects.all()[:20].values('timestamp', 'method', 'path', 'status_code', 'duration_ms', 'ip_address')
    )

    context = {
        'page_title': 'Telemetry & System Health',
        'active_page': 'health',
        'uptime_str': uptime_str,
        'sql_stats': sql_stats,
        'mongo_status': mongo_status,
        'third_party': third_party_data,
        'recent_logs': recent_logs,
    }
    return render(request, 'health.html', context)

# Contact & Support Tickets Page
def contact_view(request):
    if request.method == 'POST':
        name = request.POST.get('user_name', 'Anonymous')
        email = request.POST.get('email', '')
        subject = request.POST.get('subject', 'General Inquiry')
        desc = request.POST.get('description', '')
        priority = request.POST.get('priority', 'Normal')

        if subject and desc:
            ticket = SupportTicket.objects.create(
                user_name=name,
                email=email,
                subject=subject,
                description=desc,
                priority=priority
            )
            return redirect(f"/contact/?ticket_created={ticket.ticket_code}")

    recent_tickets = SupportTicket.objects.all()[:15]
    ticket_created = request.GET.get('ticket_created')

    context = {
        'page_title': 'Contact & Support Dispatch',
        'active_page': 'contact',
        'recent_tickets': recent_tickets,
        'ticket_created': ticket_created,
    }
    return render(request, 'contact.html', context)

# --------------------------------------------------------------------------
# API ENDPOINTS
# --------------------------------------------------------------------------

@csrf_exempt
@require_http_methods(["POST"])
def api_chat(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
        message = data.get('message', '').strip()
        session_id = data.get('session_id', 'visitor-session')
    except Exception:
        message = request.POST.get('message', '').strip()
        session_id = request.POST.get('session_id', 'visitor-session')

    if not message:
        return JsonResponse({'error': 'Message cannot be empty', 'status': 400}, status=400)

    client_ip = get_client_ip(request)
    result = ai_assistant.process_message(message, session_id=session_id, client_ip=client_ip)
    return JsonResponse(result)

@csrf_exempt
@require_http_methods(["POST"])
def api_ticket_create(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    user_name = data.get('user_name', 'Anonymous')
    email = data.get('email', '')
    subject = data.get('subject', 'Support Request')
    description = data.get('description', '')
    priority = data.get('priority', 'Normal')

    if not description:
        return JsonResponse({'error': 'Description is required'}, status=400)

    ticket = SupportTicket.objects.create(
        user_name=user_name,
        email=email,
        subject=subject,
        description=description,
        priority=priority
    )

    return JsonResponse({
        'success': True,
        'ticket_code': ticket.ticket_code,
        'status': ticket.status,
        'created_at': ticket.created_at.strftime('%Y-%m-%d %H:%M:%S')
    })

@csrf_exempt
@require_http_methods(["POST"])
def api_feedback(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    session_id = data.get('session_id', 'default')
    rating = data.get('rating', 5)
    comment = data.get('comment', '')
    client_ip = get_client_ip(request)

    mongo_client.log_feedback(session_id, rating, comment, ip=client_ip)
    return JsonResponse({'success': True, 'message': 'Feedback successfully recorded in MongoDB'})

def api_quote(request):
    data = fetch_third_party_quote(timeout_sec=2.0)
    return JsonResponse(data)

# Test intentional 500 error
def test_500_view(request):
    raise Exception("Simulated Internal Server Error (500) for assessment testing.")

# Custom 404 Handler
def custom_404_view(request, exception=None):
    context = {
        'page_title': '404 - Target Not Found',
        'path': request.path,
        'error_code': 404
    }
    return render(request, '404.html', context, status=404)

# Custom 500 Handler
def custom_500_view(request):
    context = {
        'page_title': '500 - Server Malfunction',
        'error_code': 500
    }
    return render(request, '500.html', context, status=500)
