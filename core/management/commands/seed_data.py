from django.core.management.base import BaseCommand
from core.models import FAQ, ErrorCode

class Command(BaseCommand):
    help = "Seeds database with required 10+ FAQs and 8 Error Codes"

    def handle(self, *args, **options):
        self.stdout.write("Seeding FAQs...")
        faqs = [
            {
                "category": "Profile & Background",
                "question": "Who is Praveen A and what are his core engineering disciplines?",
                "answer": "Praveen A is a Mechatronics Engineering student, Full Stack Developer, and AI Prompt Engineer. He focuses on the convergence of robotics, PLC automation, IoT telemetry, embedded systems, and modern web software architectures.",
                "keywords": "praveen, mechatronics, profile, disciplines, background, engineering"
            },
            {
                "category": "Profile & Background",
                "question": "What is Praveen's personality type and engineering approach?",
                "answer": "Praveen is identified as an INFJ-T (Advocate) on the 16 Personalities framework. His approach combines rigorous systems thinking and analytical precision with collaborative empathy and continuous innovation.",
                "keywords": "personality, infj, advocate, approach, style, philosophy"
            },
            {
                "category": "ProtoSem Fellowship",
                "question": "What is the ProtoSem Fellowship at KCT Forge?",
                "answer": "ProtoSem is an intensive fellowship program based at KCT Forge. It immerses engineering students in rapid prototyping, hardware-software integration, system design, failure mode analysis, and bringing industrial-grade concepts to life.",
                "keywords": "protosem, kct forge, fellowship, prototyping, hardware"
            },
            {
                "category": "IoT Sessions",
                "question": "What was achieved in IoT Practical Task 1?",
                "answer": "Task 1 focused on Microcontroller Firmware & Telemetry Setup using the NodeMCU (ESP8266) development board, establishing Wi-Fi connectivity, flashing firmware, and hardware LED telemetry control.",
                "keywords": "iot, task 1, nodemcu, esp8266, firmware, wifi"
            },
            {
                "category": "IoT Sessions",
                "question": "How was environmental sensing handled in IoT Task 2?",
                "answer": "Task 2 interfaced DHT temperature and humidity sensors with the microcontroller, calibrated raw analog/digital signals, and verified reliable data sampling loops.",
                "keywords": "iot, task 2, dht, temperature, humidity, sensor"
            },
            {
                "category": "IoT Sessions",
                "question": "What was demonstrated in IoT Task 3 regarding actuators?",
                "answer": "Task 3 explored physical actuator and relay module driving, controlling high-load circuits from low-voltage microcontroller digital output pins safely.",
                "keywords": "iot, task 3, actuators, relays, motor, control"
            },
            {
                "category": "IoT Sessions",
                "question": "What wireless communication was implemented in IoT Task 4?",
                "answer": "Task 4 established wireless Bluetooth Serial Communication between mobile devices and microcontrollers for bidirectional command control.",
                "keywords": "iot, task 4, bluetooth, serial, wireless, mobile"
            },
            {
                "category": "IoT Sessions",
                "question": "How was cloud telemetry streaming configured in IoT Task 5?",
                "answer": "Task 5 streamed real-time sensor telemetry to ThingSpeak cloud dashboards, implementing API key authorization and historical field visualization.",
                "keywords": "iot, task 5, thingspeak, cloud, telemetry, api, charts"
            },
            {
                "category": "AI Assistant & System",
                "question": "How does this Command Center AI Assistant work?",
                "answer": "The AI assistant integrates retrieval-augmented search over SQL FAQ tables, explains 8 standard/custom HTTP error codes, logs chat analytics to MongoDB, and automatically generates SQL support tickets when inquiries require escalation.",
                "keywords": "ai assistant, gemini, rag, support ticket, telemetry, architecture"
            },
            {
                "category": "AI Assistant & System",
                "question": "How are support tickets handled when the AI cannot answer?",
                "answer": "When an inquiry cannot be answered with high confidence from the FAQ database, the assistant automatically issues a support ticket with a unique TKT reference code and stores it in the SQL database for review.",
                "keywords": "support ticket, tickets, help, escalation, unresolved"
            },
            {
                "category": "Technical Skills",
                "question": "What programming languages and frameworks does Praveen master?",
                "answer": "Praveen is proficient in Python (Django, Flask), JavaScript (Node.js, Express, React), C/C++ for embedded firmware, SQL databases, MongoDB, PLC Ladder Logic, and Docker containerization.",
                "keywords": "skills, python, django, javascript, c, plc, sql, mongodb"
            },
            {
                "category": "Technical Skills",
                "question": "What robotics and hardware platforms has Praveen worked with?",
                "answer": "Praveen has hands-on experience with ROS2 (Robot Operating System), Arduino, ESP32, NodeMCU, STM32, pneumatic automation, industrial servo actuators, and sensor bus protocols (I2C, SPI, UART).",
                "keywords": "robotics, ros2, arduino, esp32, stm32, hardware, pneumatic"
            },
            {
                "category": "Inspiration & Tribute",
                "question": "Why does this platform feature a special tribute to Virat Kohli?",
                "answer": "Virat Kohli represents the pinnacle of athletic discipline, resilience, and high-performance focus—core tenets that Praveen translates into robotics, systems engineering, and continuous learning. The platform showcases a photographic tribute, career highlights, and business milestones.",
                "keywords": "virat kohli, tribute, inspiration, cricket, king kohli, hero"
            },
            {
                "category": "Inspiration & Tribute",
                "question": "What dietary and fitness regimen did Virat Kohli adopt to sustain peak performance?",
                "answer": "In 2018, Kohli adopted a vegetarian diet (clarifying he is not vegan as he consumes dairy) to combat high uric acid levels and cervical spine issues affecting his finger mobility and batting performance, exemplifying health discipline.",
                "keywords": "virat diet, vegetarian, fitness, health, uric acid, workout, spine"
            },
            {
                "category": "Inspiration & Tribute",
                "question": "What commercial ventures and lifestyle brands has Virat Kohli launched?",
                "answer": "Kohli co-owns FC Goa (Indian Super League), UAE Royals (IPTL), and Bengaluru Yodhas (PWL). He launched fashion brand WROGN with Universal Sportsbiz, Chisel fitness centers, One8 with Puma, and fine dining restaurants Nueva and One8 Commune.",
                "keywords": "virat business, wrogn, one8, fc goa, chisel, nueva, one8 commune, puma"
            }
        ]

        for item in faqs:
            FAQ.objects.update_or_create(
                question=item["question"],
                defaults={
                    "category": item["category"],
                    "answer": item["answer"],
                    "keywords": item["keywords"]
                }
            )
        self.stdout.write(self.style.SUCCESS(f"Successfully seeded {len(faqs)} FAQs in SQL."))

        self.stdout.write("Seeding Error Codes (8 codes)...")
        error_codes = [
            {
                "code": 400,
                "name": "Bad Request",
                "category": "Client Error",
                "description": "The server cannot process the request due to malformed request syntax, invalid parameters, or deceptive routing.",
                "cause": "Malformed JSON payload, missing required URL query parameters, or mismatched header data.",
                "resolution": "Inspect your request body, verify field types against the API schema, and ensure headers include Content-Type: application/json."
            },
            {
                "code": 401,
                "name": "Unauthorized",
                "category": "Client Error",
                "description": "Authentication is required and has failed or has not yet been provided.",
                "cause": "Missing Authorization header, expired JWT token, or incorrect API credential key.",
                "resolution": "Authenticate with valid credentials or include a bearer token in your HTTP request headers."
            },
            {
                "code": 403,
                "name": "Forbidden",
                "category": "Client Error",
                "description": "The server understood the request but refuses to authorize it even if authenticated.",
                "cause": "Insufficient role privileges, restricted administrative path access, or IP blacklisting.",
                "resolution": "Request elevated permissions from an administrator or ensure you are accessing endpoints permitted by your user role."
            },
            {
                "code": 404,
                "name": "Not Found",
                "category": "Client Error",
                "description": "The origin server did not find a current representation for the target resource.",
                "cause": "Incorrect URL route, deleted database record ID, or an outdated bookmark link.",
                "resolution": "Verify the URL path spelling or navigate back to the Home page using the command menu."
            },
            {
                "code": 429,
                "name": "Too Many Requests",
                "category": "Client Error",
                "description": "The user has sent too many requests in a given amount of time (Rate Limiting).",
                "cause": "Exceeding the API throttling quota or aggressive polling loops.",
                "resolution": "Implement exponential backoff retry algorithms and adhere to the Retry-After header interval."
            },
            {
                "code": 500,
                "name": "Internal Server Error",
                "category": "Server Error",
                "description": "The server encountered an unexpected condition that prevented it from fulfilling the request.",
                "cause": "Unhandled runtime exception, database connection failure, or backend null reference.",
                "resolution": "Check the server application logs for tracebacks, inspect environment variable configurations, and verify database daemon uptime."
            },
            {
                "code": 503,
                "name": "Service Unavailable",
                "category": "Server Error",
                "description": "The server is currently unable to handle the request due to temporary overload or scheduled maintenance.",
                "cause": "Server resource exhaustion (CPU/RAM), third-party upstream gateway downtime, or container restarts.",
                "resolution": "Retry after a brief delay. Verify container health checks and scaling thresholds."
            },
            {
                "code": 599,
                "name": "PRAVEEN_CORE_TIMEOUT (Site-Specific)",
                "category": "Custom Telemetry Error",
                "description": "Proprietary site-specific code indicating a telemetry watchdog timeout when reading hardware sensor loops or upstream microservices beyond 2000ms threshold.",
                "cause": "NodeMCU/ESP8266 telemetry packet dropped, third-party API timeout exceeded, or hardware actuator bus latency.",
                "resolution": "The system automatically engages offline cached telemetry mode. If the condition persists, file a support ticket with the AI assistant."
            }
        ]

        for item in error_codes:
            ErrorCode.objects.update_or_create(
                code=item["code"],
                defaults={
                    "name": item["name"],
                    "category": item["category"],
                    "description": item["description"],
                    "cause": item["cause"],
                    "resolution": item["resolution"]
                }
            )
        self.stdout.write(self.style.SUCCESS(f"Successfully seeded {len(error_codes)} Error Codes in SQL."))
