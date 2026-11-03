import os
import re
import requests
from django.db.models import Q
from .models import FAQ, ErrorCode, SupportTicket
from .mongo_service import mongo_client

class AIService:
    def __init__(self):
        self.gemini_api_key = os.getenv('GEMINI_API_KEY', '').strip()

    def process_message(self, message: str, session_id: str = 'default', client_ip: str = '127.0.0.1') -> dict:
        text = message.strip()
        lower_text = text.lower()

        # 1. Check if user is asking to create a support ticket directly
        ticket_triggers = ['create ticket', 'raise ticket', 'file ticket', 'open ticket', 'support ticket', 'contact praveen', 'human support']
        if any(trig in lower_text for trig in ticket_triggers):
            ticket = SupportTicket.objects.create(
                user_name="Visitor via AI Chat",
                email="chat-visitor@portfolio.local",
                subject=f"Inquiry: {text[:60]}",
                description=text,
                priority="Normal"
            )
            response_text = (
                f"🎫 <strong>Support Ticket Generated!</strong><br><br>"
                f"Reference Code: <code>{ticket.ticket_code}</code><br>"
                f"Status: <code>{ticket.status}</code><br><br>"
                f"Your request has been logged into our SQL support database. Praveen will review your query shortly. "
                f"You can also check ticket statuses on the Contact page."
            )
            mongo_client.log_chat(session_id, text, response_text, ip=client_ip)
            return {
                'response': response_text,
                'source': 'ticket_engine',
                'ticket_code': ticket.ticket_code,
                'can_create_ticket': False
            }

        # 2. Check for Error Code explanation request
        # Patterns like: "404", "error 500", "code 429", "explain 401", "599"
        error_match = re.search(r'\b(400|401|403|404|429|500|503|599)\b', lower_text)
        if error_match or 'error' in lower_text:
            code_num = None
            if error_match:
                code_num = int(error_match.group(1))
            else:
                for ec in [400, 401, 403, 404, 429, 500, 503, 599]:
                    if str(ec) in lower_text:
                        code_num = ec
                        break

            if code_num:
                try:
                    ec_obj = ErrorCode.objects.get(code=code_num)
                    response_text = (
                        f"⚠️ <strong>Error Code {ec_obj.code} — {ec_obj.name}</strong> ({ec_obj.category})<br><br>"
                        f"<strong>Description:</strong> {ec_obj.description}<br><br>"
                        f"<strong>Potential Cause:</strong> {ec_obj.cause}<br><br>"
                        f"<strong>Recommended Resolution:</strong> {ec_obj.resolution}<br><br>"
                        f"<em>Need more help? Ask me to 'create a support ticket' anytime!</em>"
                    )
                    mongo_client.log_chat(session_id, text, response_text, error_code=code_num, ip=client_ip)
                    return {
                        'response': response_text,
                        'source': 'error_database',
                        'error_code': code_num,
                        'can_create_ticket': True
                    }
                except ErrorCode.DoesNotExist:
                    pass

        # 3. Search SQL FAQ Database
        # Clean query tokens and filter out common stop words
        STOP_WORDS = {'the', 'is', 'at', 'which', 'on', 'and', 'a', 'an', 'in', 'that', 'this', 'to', 'for', 'of', 'or', 'by', 'with', 'from', 'as', 'what', 'how', 'who', 'does', 'can', 'are', 'was'}
        raw_words = re.findall(r'\b[a-z0-9]{3,}\b', lower_text)
        words = [w for w in raw_words if w not in STOP_WORDS]
        faq_candidates = FAQ.objects.all()

        best_faq = None
        best_score = 0

        for faq in faq_candidates:
            score = 0
            q_lower = faq.question.lower()
            a_lower = faq.answer.lower()
            kw_lower = faq.keywords.lower() if faq.keywords else ''

            # Direct substring match
            if len(lower_text) > 6 and (lower_text in q_lower or q_lower in lower_text):
                score += 25

            for word in words:
                pattern = r'\b' + re.escape(word) + r'\b'
                if re.search(pattern, q_lower):
                    score += 6
                if re.search(pattern, kw_lower):
                    score += 5
                if re.search(pattern, a_lower):
                    score += 1

            if score > best_score:
                best_score = score
                best_faq = faq

        # If strong FAQ match found (score threshold of 10)
        if best_faq and best_score >= 10:
            response_text = (
                f"💡 <strong>{best_faq.question}</strong><br><br>"
                f"{best_faq.answer}<br><br>"
                f"<span class='badge-cat'>Category: {best_faq.category}</span>"
            )
            mongo_client.log_chat(session_id, text, response_text, ip=client_ip)
            return {
                'response': response_text,
                'source': 'sql_faq',
                'faq_id': best_faq.id,
                'can_create_ticket': False
            }

        # 4. Try Gemini AI if API key is provided
        if self.gemini_api_key:
            gemini_ans = self._call_gemini(text)
            if gemini_ans:
                mongo_client.log_chat(session_id, text, gemini_ans, ip=client_ip)
                return {
                    'response': gemini_ans,
                    'source': 'gemini_ai',
                    'can_create_ticket': True
                }

        # 5. Fallback: Assistant cannot answer from FAQ data -> Offer/Auto-create support ticket
        ticket = SupportTicket.objects.create(
            user_name="Visitor (Unresolved Query)",
            email="",
            subject=f"AI Unresolved: {text[:50]}",
            description=f"User asked: '{text}'. The AI assistant could not find a sufficient match in the SQL FAQ database.",
            priority="Normal"
        )

        response_text = (
            f"🤖 I couldn't find a direct answer in our SQL FAQ database regarding: <em>\"{text}\"</em>.<br><br>"
            f"To make sure you get the right support, I have automatically created a <strong>Support Ticket</strong> for Praveen:<br>"
            f"• Ticket Code: <code>{ticket.ticket_code}</code><br>"
            f"• Status: <code>Open (Logged in SQL)</code><br><br>"
            f"You can also browse our <strong><a href='/faqs/'>FAQs</a></strong> or check standard <strong><a href='/errors/'>Error Codes</a></strong>."
        )

        mongo_client.log_chat(session_id, text, response_text, ip=client_ip)
        return {
            'response': response_text,
            'source': 'unresolved_ticket_created',
            'ticket_code': ticket.ticket_code,
            'can_create_ticket': False
        }

    def _call_gemini(self, prompt: str) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_api_key}"
        headers = {'Content-Type': 'application/json'}
        system_instruction = (
            "You are the AI Command Assistant for Praveen A's Engineering Portfolio. "
            "Praveen is a Mechatronics Engineering student, Full Stack Developer, and AI Prompt Engineer. "
            "His expertise covers Robotics, IoT, PLC Automation, ProtoSem Fellowship, and Web Development. "
            "Answer clearly and politely. If you cannot answer technical specifics about his personal projects, "
            "kindly instruct the user to file a support ticket or view the FAQ."
        )
        data = {
            "contents": [
                {"role": "user", "parts": [{"text": f"System context: {system_instruction}\nUser question: {prompt}"}]}
            ],
            "generationConfig": {
                "maxOutputTokens": 300,
                "temperature": 0.4
            }
        }
        try:
            res = requests.post(url, headers=headers, json=data, timeout=5)
            if res.status_code == 200:
                result = res.json()
                candidates = result.get('candidates', [])
                if candidates:
                    parts = candidates[0].get('content', {}).get('parts', [])
                    if parts:
                        return parts[0].get('text', '')
        except Exception as e:
            print("Gemini API call failed:", e)
        return ""

ai_assistant = AIService()
