import time
from django.utils import timezone
from .models import RequestLog

# In-memory buffer of recent requests for immediate telemetry rendering
RECENT_REQUESTS = []

class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        response = self.get_response(request)
        duration_ms = (time.time() - start_time) * 1000.0

        # Extract client IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '127.0.0.1')

        path = request.path
        method = request.method
        status_code = response.status_code
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:250]

        # Ignore static and media files from persistent DB logging to keep DB clean
        if not path.startswith('/static/') and not path.startswith('/favicon.ico'):
            log_entry = {
                'timestamp': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
                'method': method,
                'path': path,
                'status_code': status_code,
                'duration_ms': round(duration_ms, 2),
                'ip': ip,
                'user_agent': user_agent
            }

            RECENT_REQUESTS.insert(0, log_entry)
            if len(RECENT_REQUESTS) > 50:
                RECENT_REQUESTS.pop()

            try:
                RequestLog.objects.create(
                    method=method,
                    path=path[:250],
                    status_code=status_code,
                    duration_ms=round(duration_ms, 2),
                    ip_address=ip,
                    user_agent=user_agent
                )
            except Exception as e:
                # Middleware should never crash the main application request
                pass

        return response
