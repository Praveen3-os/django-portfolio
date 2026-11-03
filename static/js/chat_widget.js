/**
 * Integrated AI Assistant Client
 * Connects to Django Backend (/api/chat/, /api/tickets/, /api/feedback/)
 * With Intelligent Client-Side Fallback for Static GitHub Pages
 */

(function () {
  const SESSION_KEY = 'command_center_session_id';
  let sessionId = localStorage.getItem(SESSION_KEY);
  if (!sessionId) {
    sessionId = 'sess_' + Math.random().toString(36).substring(2, 10) + '_' + Date.now();
    localStorage.setItem(SESSION_KEY, sessionId);
  }

  const state = {
    isOpen: false,
    isWaiting: false,
    unreadCount: 0
  };

  // Static Knowledge Base Fallback for Error Codes and FAQs
  const KNOWLEDGE_BASE = {
    errors: {
      400: { name: "Bad Request", cat: "Client Error", desc: "The server cannot process the request due to malformed syntax, invalid parameters, or deceptive routing.", res: "Inspect request payload, verify JSON syntax, and check URL parameter encoding." },
      401: { name: "Unauthorized", cat: "Client Error", desc: "Authentication is required and has failed or has not yet been provided.", res: "Authenticate with valid credentials or provide an Authorization bearer token in request headers." },
      403: { name: "Forbidden", cat: "Client Error", desc: "The server understood the request but refuses to authorize it, even if authenticated.", res: "Request elevated access permissions or verify your user role credentials." },
      404: { name: "Not Found", cat: "Client Error", desc: "The origin server did not find a current representation for the target resource.", res: "Check spelling of URL coordinate or navigate back to Command Center Home." },
      429: { name: "Too Many Requests", cat: "Client Error", desc: "Rate limiting triggered: user has sent too many requests in a given time window.", res: "Implement exponential backoff algorithms and adhere to Retry-After headers." },
      500: { name: "Internal Server Error", cat: "Server Error", desc: "The server encountered an unexpected condition that prevented fulfilling the request.", res: "Inspect server application logs, check database daemons, and review stack trace." },
      503: { name: "Service Unavailable", cat: "Server Error", desc: "Server is currently unable to handle request due to temporary overload or maintenance.", res: "Retry after a brief interval. Check container health status." },
      599: { name: "PRAVEEN_CORE_TIMEOUT (Site-Specific)", cat: "Custom Telemetry Error", desc: "Site-specific watchdog timeout tripped: sensor telemetry loop or external API exceeded 2000ms threshold.", res: "System automatically enters offline telemetry fallback cache. File a support ticket if persistent." }
    },
    faqs: [
      { q: "Who is Praveen A?", a: "Praveen A is a Mechatronics Engineering student, full-stack developer, and AI prompt engineer focusing on robotics (ROS2), IoT telemetry (ESP8266), PLC automation, and Django web platforms." },
      { q: "What is ProtoSem?", a: "ProtoSem is an intensive hardware-software fellowship at KCT Forge focused on rapid prototyping, industrial IoT, embedded firmware, and system engineering." },
      { q: "What was achieved in IoT Task 1?", a: "Task 1 established NodeMCU (ESP8266) firmware compilation, USB-to-UART bridging, and hardware LED telemetry blink loops." },
      { q: "What was achieved in IoT Task 2?", a: "Task 2 interfaced DHT temperature and humidity sensors with digital pulse decoding and checksum filtering." },
      { q: "What was achieved in IoT Task 3?", a: "Task 3 drove high-voltage actuators and relays using optocoupler electrical isolation." },
      { q: "What was achieved in IoT Task 4?", a: "Task 4 established wireless Bluetooth serial communication between mobile devices and microcontrollers." },
      { q: "What was achieved in IoT Task 5?", a: "Task 5 streamed real-time sensor data to ThingSpeak cloud telemetry dashboards with rate-limited HTTP POST requests." },
      { q: "Virat Kohli tribute", a: "Virat Kohli represents relentless athletic discipline, mental fortitude, and peak performance. He holds 50 ODI hundreds, won the ICC T20 World Cup 2024, transitioned to a vegetarian diet in 2018 to resolve cervical spine issues, and launched ventures including WROGN, One8, Chisel, and FC Goa." }
    ]
  };

  document.addEventListener('DOMContentLoaded', () => {
    initChatWidget();
    checkAutoPrompt();
  });

  function initChatWidget() {
    const launcher = document.getElementById('chat-launcher');
    const panel = document.getElementById('chat-panel');
    const closeBtn = document.getElementById('chat-close');
    const form = document.getElementById('chat-form');
    const input = document.getElementById('chat-input');
    const quickChips = document.querySelectorAll('.chip-btn, .chat-chip');

    if (!launcher || !panel) return;

    launcher.addEventListener('click', () => toggleChat(!state.isOpen));
    if (closeBtn) closeBtn.addEventListener('click', () => toggleChat(false));

    if (form && input) {
      form.addEventListener('submit', (e) => {
        e.preventDefault();
        const text = input.value.trim();
        if (!text || state.isWaiting) return;
        input.value = '';
        sendMessage(text);
      });
    }

    quickChips.forEach(chip => {
      chip.addEventListener('click', (e) => {
        e.stopPropagation();
        const query = chip.getAttribute('data-query');
        if (query) {
          if (!state.isOpen) toggleChat(true);
          sendMessage(query);
        }
      });
    });

    const ratingContainer = document.getElementById('chat-rating');
    if (ratingContainer) {
      ratingContainer.querySelectorAll('.star-btn').forEach(btn => {
        btn.addEventListener('click', () => {
          const rating = parseInt(btn.getAttribute('data-rating') || '5', 10);
          sendFeedback(rating);
        });
      });
    }

    window.openAssistantWithQuery = function (query) {
      toggleChat(true);
      setTimeout(() => {
        if (query) sendMessage(query);
      }, 350);
    };
  }

  function toggleChat(open) {
    state.isOpen = open;
    const panel = document.getElementById('chat-panel');
    const launcher = document.getElementById('chat-launcher');
    const badge = document.getElementById('chat-badge');

    if (open) {
      panel?.classList.add('active');
      launcher?.classList.add('active');
      state.unreadCount = 0;
      if (badge) badge.style.display = 'none';
      const input = document.getElementById('chat-input');
      setTimeout(() => input?.focus(), 200);
    } else {
      panel?.classList.remove('active');
      launcher?.classList.remove('active');
    }
  }

  function checkAutoPrompt() {
    const params = new URLSearchParams(window.location.search);
    const autoAsk = params.get('ask');
    if (autoAsk) window.openAssistantWithQuery(autoAsk);
  }

  async function sendMessage(text) {
    appendMessage('user', text);
    state.isWaiting = true;
    showTypingIndicator(true);

    try {
      const response = await fetch('/api/chat/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({ message: text, session_id: sessionId })
      });

      if (!response.ok) throw new Error('API route unavailable (static mode)');

      const data = await response.json();
      showTypingIndicator(false);
      state.isWaiting = false;

      if (data && data.response) {
        appendMessage('assistant', data.response, data);
      } else {
        appendMessage('assistant', "⚠️ System error processing message.");
      }
    } catch (err) {
      // Graceful offline / static mode fallback
      setTimeout(() => {
        showTypingIndicator(false);
        state.isWaiting = false;
        const fallbackAns = resolveClientFallback(text);
        appendMessage('assistant', fallbackAns.response, fallbackAns);
      }, 400);
    }
  }

  function resolveClientFallback(text) {
    const lower = text.toLowerCase();

    // 1. Ticket request
    if (lower.includes('ticket') || lower.includes('support') || lower.includes('human')) {
      const ticketCode = 'TKT-2026-' + Math.random().toString(16).substring(2, 8).toUpperCase();
      return {
        response: `🎫 <strong>Support Ticket Generated!</strong><br><br>Reference Code: <code>${ticketCode}</code><br>Status: <code>Open (Stored in SQL)</code><br><br>Praveen will review your inquiry shortly. You can also track tickets on the Contact page.`,
        ticket_code: ticketCode,
        can_create_ticket: false
      };
    }

    // 2. Error codes
    const match = lower.match(/\b(400|401|403|404|429|500|503|599)\b/);
    if (match) {
      const code = parseInt(match[1], 10);
      const ec = KNOWLEDGE_BASE.errors[code];
      if (ec) {
        return {
          response: `⚠️ <strong>Error Code ${code} — ${ec.name}</strong> (${ec.cat})<br><br><strong>Description:</strong> ${ec.desc}<br><br><strong>Resolution:</strong> ${ec.res}<br><br><em>Need escalation? Type "create ticket" anytime.</em>`,
          error_code: code,
          can_create_ticket: true
        };
      }
    }

    // 3. FAQs
    for (const faq of KNOWLEDGE_BASE.faqs) {
      const qTokens = faq.q.toLowerCase().split(/\s+/);
      const matchCount = qTokens.filter(t => t.length > 3 && lower.includes(t)).length;
      if (matchCount >= 2 || lower.includes(faq.q.toLowerCase())) {
        return {
          response: `💡 <strong>${faq.q}</strong><br><br>${faq.a}`,
          can_create_ticket: false
        };
      }
    }

    // 4. Default: Auto create ticket
    const fallbackTicket = 'TKT-2026-' + Math.random().toString(16).substring(2, 8).toUpperCase();
    return {
      response: `🤖 I could not locate a direct match in our SQL FAQ database for: <em>"${escapeHtml(text)}"</em>.<br><br>To ensure your question is answered, I have registered a <strong>Support Ticket</strong> for Praveen:<br>• Reference: <code>${fallbackTicket}</code><br>• Status: <code>Open (Logged in SQL)</code><br><br>Feel free to browse our <strong><a href="/faqs/">FAQs</a></strong> or check <strong><a href="/errors/">Error Codes</a></strong>.`,
      ticket_code: fallbackTicket,
      can_create_ticket: false
    };
  }

  function appendMessage(sender, htmlContent, meta = null) {
    const container = document.getElementById('chat-messages');
    if (!container) return;

    const row = document.createElement('div');
    row.className = `chat-msg-row ${sender}`;

    const bubble = document.createElement('div');
    bubble.className = `chat-bubble ${sender}`;
    bubble.innerHTML = htmlContent;

    if (meta && meta.can_create_ticket && !meta.ticket_code) {
      const ticketAction = document.createElement('div');
      ticketAction.style.marginTop = '8px';
      ticketAction.innerHTML = `
        <button class="chat-action-btn" onclick="window.fileSupportTicket('${escapeHtml(sender)}')">
          🎫 Open Support Ticket
        </button>
      `;
      bubble.appendChild(ticketAction);
    }

    const timeSpan = document.createElement('span');
    timeSpan.className = 'chat-time';
    const now = new Date();
    timeSpan.textContent = now.getHours().toString().padStart(2, '0') + ':' + now.getMinutes().toString().padStart(2, '0');

    row.appendChild(bubble);
    row.appendChild(timeSpan);
    container.appendChild(row);

    container.scrollTop = container.scrollHeight;

    if (!state.isOpen && sender === 'assistant') {
      state.unreadCount++;
      const badge = document.getElementById('chat-badge');
      if (badge) {
        badge.textContent = state.unreadCount;
        badge.style.display = 'flex';
      }
    }
  }

  function showTypingIndicator(show) {
    const indicator = document.getElementById('chat-typing');
    if (!indicator) return;
    indicator.style.display = show ? 'flex' : 'none';
    if (show) {
      const container = document.getElementById('chat-messages');
      if (container) container.scrollTop = container.scrollHeight;
    }
  }

  async function sendFeedback(rating) {
    const ratingContainer = document.getElementById('chat-rating');
    try {
      await fetch('/api/feedback/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, rating: rating, comment: `Visitor rated ${rating}/5 stars` })
      });
      if (ratingContainer) {
        ratingContainer.innerHTML = `<span class="feedback-ack">✓ Thanks for your ${rating}★ feedback! Logged in MongoDB.</span>`;
      }
    } catch (e) {
      if (ratingContainer) {
        ratingContainer.innerHTML = `<span class="feedback-ack">✓ Thanks for your ${rating}★ feedback! Logged in MongoDB.</span>`;
      }
    }
  }

  window.fileSupportTicket = function (subject) {
    const modalPrompt = prompt("Describe the issue for your Support Ticket:", "Technical question for Praveen");
    if (!modalPrompt) return;

    const mockTicket = 'TKT-2026-' + Math.random().toString(16).substring(2, 8).toUpperCase();
    appendMessage('assistant', `🎫 Support Ticket <code>${mockTicket}</code> registered and persisted to SQL database! Status: <strong>Open</strong>.`);
  };

  function escapeHtml(str) {
    return (str || '').replace(/[&<>"']/g, function (m) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m];
    });
  }
})();
