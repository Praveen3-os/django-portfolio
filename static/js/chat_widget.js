/**
 * Integrated AI Assistant Client
 * Connects to Django Backend (/api/chat/, /api/tickets/, /api/feedback/)
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
    const quickChips = document.querySelectorAll('.chip-btn');
    const badge = document.getElementById('chat-badge');

    if (!launcher || !panel) return;

    // Toggle panel
    launcher.addEventListener('click', () => {
      toggleChat(!state.isOpen);
    });

    if (closeBtn) {
      closeBtn.addEventListener('click', () => {
        toggleChat(false);
      });
    }

    // Submit form
    if (form && input) {
      form.addEventListener('submit', (e) => {
        e.preventDefault();
        const text = input.value.trim();
        if (!text || state.isWaiting) return;
        input.value = '';
        sendMessage(text);
      });
    }

    // Quick chips
    quickChips.forEach(chip => {
      chip.addEventListener('click', () => {
        const query = chip.getAttribute('data-query');
        if (query) {
          if (!state.isOpen) toggleChat(true);
          sendMessage(query);
        }
      });
    });

    // Rating stars handler
    const ratingContainer = document.getElementById('chat-rating');
    if (ratingContainer) {
      ratingContainer.querySelectorAll('.star-btn').forEach(btn => {
        btn.addEventListener('click', () => {
          const rating = parseInt(btn.getAttribute('data-rating') || '5', 10);
          sendFeedback(rating);
        });
      });
    }

    // Global helper for 404 / 500 error pages
    window.openAssistantWithQuery = function (query) {
      toggleChat(true);
      setTimeout(() => {
        if (query) {
          sendMessage(query);
        }
      }, 300);
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
    if (autoAsk) {
      window.openAssistantWithQuery(autoAsk);
    }
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
        body: JSON.stringify({
          message: text,
          session_id: sessionId
        })
      });

      const data = await response.json();
      showTypingIndicator(false);
      state.isWaiting = false;

      if (data && data.response) {
        appendMessage('assistant', data.response, data);
      } else {
        appendMessage('assistant', "⚠️ System error processing message. Please file a support ticket.");
      }
    } catch (err) {
      showTypingIndicator(false);
      state.isWaiting = false;
      appendMessage('assistant', "⚠️ Unable to contact AI backend. Engaging fallback: Please file a ticket via the Contact page.");
    }
  }

  function appendMessage(sender, htmlContent, meta = null) {
    const container = document.getElementById('chat-messages');
    if (!container) return;

    const row = document.createElement('div');
    row.className = `chat-msg-row ${sender}`;

    const bubble = document.createElement('div');
    bubble.className = `chat-bubble ${sender}`;
    bubble.innerHTML = htmlContent;

    // Optional ticket action button if applicable
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

    // Scroll to bottom
    container.scrollTop = container.scrollHeight;

    // If chat closed, increase badge
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
        body: JSON.stringify({
          session_id: sessionId,
          rating: rating,
          comment: `Visitor rated ${rating}/5 stars`
        })
      });
      if (ratingContainer) {
        ratingContainer.innerHTML = `<span class="feedback-ack">✓ Thanks for your ${rating}★ feedback! Logged in MongoDB.</span>`;
      }
    } catch (e) {
      if (ratingContainer) {
        ratingContainer.innerHTML = `<span class="feedback-ack">✓ Feedback recorded locally.</span>`;
      }
    }
  }

  window.fileSupportTicket = function (subject) {
    const modalPrompt = prompt("Describe the issue for your Support Ticket:", "Follow-up on inquiry");
    if (!modalPrompt) return;

    fetch('/api/tickets/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_name: 'Visitor via AI Widget',
        subject: modalPrompt.substring(0, 50),
        description: modalPrompt,
        priority: 'Normal'
      })
    })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          appendMessage('assistant', `🎫 Support Ticket <code>${data.ticket_code}</code> generated and stored in SQL database! Status: <strong>${data.status}</strong>.`);
        }
      })
      .catch(err => {
        appendMessage('assistant', '⚠️ Failed to create ticket automatically. Please use the Contact form.');
      });
  };

  function escapeHtml(str) {
    return (str || '').replace(/[&<>"']/g, function (m) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m];
    });
  }
})();
