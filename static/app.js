// --- STATE ---
let activeChatUserId = null;

// --- DOM READY ---
document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initHeaderInteractions();
    initChatActions();
    loadNotifications();
    loadEvents();
});

// --- NAVIGATION ---
function initNavigation() {
    const navItems = document.querySelectorAll('.bottom-nav .nav-item');
    const views = document.querySelectorAll('.main-content .view');

    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const targetViewId = item.getAttribute('data-target');
            if (!targetViewId) return;

            navItems.forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');

            views.forEach(view => {
                view.classList.toggle('active', view.id === targetViewId);
            });
        });
    });
}

// --- HEADER / ROLE MODAL ---
function initHeaderInteractions() {
    const currentRole = document.getElementById('currentRole');
    const roleModal = document.getElementById('roleModal');

    if (currentRole && roleModal) {
        currentRole.addEventListener('click', (e) => {
            e.stopPropagation();
            roleModal.classList.add('show');
        });

        document.addEventListener('click', () => {
            roleModal.classList.remove('show');
        });

        roleModal.addEventListener('click', (e) => {
            if (e.target === roleModal) {
                roleModal.classList.remove('show');
            }
        });
    }

    const broadcastBtn = document.getElementById('broadcastBtn');
    if (broadcastBtn) {
        broadcastBtn.addEventListener('click', async () => {
            const title = document.getElementById('broadcastTitle').value.trim();
            const content = document.getElementById('broadcastContent').value.trim();
            const priority = document.getElementById('broadcastPriority').value;

            if (!title || !content) return;

            await fetch('/notifications/broadcast', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title, content, priority })
            });

            document.getElementById('broadcastTitle').value = '';
            document.getElementById('broadcastContent').value = '';
            loadNotifications();
        });
    }
}

// --- CHAT OVERLAY ---
function openChat(userId, teacherName) {
    activeChatUserId = userId;
    const chatScreen = document.getElementById('chatScreen');
    const activeChatName = document.getElementById('activeChatName');

    if (chatScreen && activeChatName) {
        activeChatName.textContent = teacherName;
        chatScreen.classList.add('open');
        loadChatHistory();
    }
}
window.openChat = openChat;

function closeChat() {
    const chatScreen = document.getElementById('chatScreen');
    if (chatScreen) {
        chatScreen.classList.remove('open');
    }
}
window.closeChat = closeChat;

// --- CHAT ACTIONS ---
function initChatActions() {
    const attachBtn = document.getElementById('attachBtn');
    const attachmentMenu = document.getElementById('attachmentMenu');
    const sendBtn = document.getElementById('sendBtn');
    const messageInput = document.getElementById('messageInput');
    const chatMessages = document.getElementById('chatMessages');

    if (attachBtn && attachmentMenu) {
        attachBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            attachmentMenu.classList.toggle('show');
        });

        document.addEventListener('click', () => {
            attachmentMenu.classList.remove('show');
        });
    }

    async function handleSendMessage() {
        const text = messageInput.value.trim();
        if (!text || !activeChatUserId) return;

        await fetch('/messages/send', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                receiver_id: activeChatUserId,
                content: text
            })
        });

        messageInput.value = '';
        loadChatHistory();
    }

    if (sendBtn && messageInput && chatMessages) {
        sendBtn.addEventListener('click', handleSendMessage);
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') handleSendMessage();
        });
    }
}

async function loadChatHistory() {
    if (!activeChatUserId) return;
    const chatMessages = document.getElementById('chatMessages');
    chatMessages.innerHTML = '';

    const res = await fetch(`/messages/history/${activeChatUserId}`);
    const data = await res.json();

    data.forEach(msg => {
        const isSent = msg.sender === CURRENT_USER_ID;
        const wrapper = document.createElement('div');
        wrapper.className = `message ${isSent ? 'sent' : 'received'}`;

        const content = document.createElement('div');
        content.className = 'message-content';
        content.textContent = msg.content;

        const time = document.createElement('span');
        time.className = 'message-time';
        time.textContent = msg.timestamp;

        content.appendChild(time);
        wrapper.appendChild(content);
        chatMessages.appendChild(wrapper);
    });

    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function simulateAttach(type) {
    alert(`Simulating ${type} selection.`);
}
window.simulateAttach = simulateAttach;

// --- NOTIFICATIONS ---
async function loadNotifications() {
    const listContainer = document.getElementById('notificationList');
    if (!listContainer) return;

    const res = await fetch('/notifications/list');
    const data = await res.json();

    listContainer.innerHTML = '';
    data.forEach(notif => {
        const item = document.createElement('div');
        item.className = 'glass-panel';
        item.style.padding = '16px';
        item.style.borderRadius = '16px';
        item.style.marginBottom = '12px';

        item.innerHTML = `
            <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
                <h3 style="font-size:14px; font-weight:600;">${notif.title}</h3>
                <span style="font-size:11px; color:var(--text-muted);">${notif.timestamp}</span>
            </div>
            <p style="font-size:13px; line-height:1.4;">${notif.content}</p>
        `;
        listContainer.appendChild(item);
    });
}

// --- EVENTS / CALENDAR ---
async function loadEvents() {
    const res = await fetch('/events/list');
    const events = await res.json();
    window._events = events;
    renderCalendar();
}

function initCalendarControls() {
    const prevMonthBtn = document.getElementById('prevMonth');
    const nextMonthBtn = document.getElementById('nextMonth');
    const addEventBtn = document.getElementById('addEventBtn');

    let calendarDate = new Date();

    function render() {
        renderCalendar(calendarDate);
    }

    if (prevMonthBtn && nextMonthBtn) {
        prevMonthBtn.addEventListener('click', () => {
            calendarDate.setMonth(calendarDate.getMonth() - 1);
            render();
        });

        nextMonthBtn.addEventListener('click', () => {
            calendarDate.setMonth(calendarDate.getMonth() + 1);
            render();
        });
    }

    if (addEventBtn) {
        addEventBtn.addEventListener('click', async () => {
            const titleInput = document.getElementById('eventTitle');
            const dateInput = document.getElementById('eventDate');

            const title = titleInput.value.trim();
            const date = dateInput.value;

            if (!title || !date) return;

            await fetch('/events/add', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title, date })
            });

            titleInput.value = '';
            dateInput.value = '';
            loadEvents();
        });
    }

    render();
}

function renderCalendar(calendarDate = new Date()) {
    const monthYearHeader = document.getElementById('monthYear');
    const calendarGrid = document.getElementById('calendarGrid');
    const eventListEl = document.getElementById('eventList');
    const events = window._events || [];

    const year = calendarDate.getFullYear();
    const month = calendarDate.getMonth();

    const monthNames = ["January","February","March","April","May","June","July","August","September","October","November","December"];
    monthYearHeader.textContent = `${monthNames[month]} ${year}`;

    calendarGrid.innerHTML = '';

    const firstDayIndex = new Date(year, month, 1).getDay();
    const totalDays = new Date(year, month + 1, 0).getDate();

    for (let i = 0; i < firstDayIndex; i++) {
        calendarGrid.appendChild(document.createElement('div'));
    }

    for (let day = 1; day <= totalDays; day++) {
        const dayCell = document.createElement('div');
        dayCell.className = 'calendar-day-cell';
        dayCell.style.padding = '8px 0';
        dayCell.style.fontSize = '14px';
        dayCell.style.textAlign = 'center';
        dayCell.textContent = day;

        const currentStringDate = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
        const dailyEvents = events.filter(e => e.date === currentStringDate);

        if (dailyEvents.length > 0) {
            dayCell.style.background = 'rgba(79, 70, 229, 0.1)';
            dayCell.style.color = 'var(--primary)';
            dayCell.style.fontWeight = '700';
            dayCell.style.borderRadius = '50%';
        }

        calendarGrid.appendChild(dayCell);
    }

    if (eventListEl) {
        eventListEl.innerHTML = '';
        const relevantEvents = events
            .filter(e => new Date(e.date).getMonth() === month && new Date(e.date).getFullYear() === year)
            .sort((a, b) => new Date(a.date) - new Date(b.date));

        if (relevantEvents.length === 0) {
            eventListEl.innerHTML = `<p style="color:var(--text-muted); font-size:13px; padding:10px;">No events scheduled for this month.</p>`;
        } else {
            relevantEvents.forEach(ev => {
                const dayNum = ev.date.split('-')[2];
                const card = `
                    <div class="glass-panel" style="padding:14px; border-radius:14px; display:flex; align-items:center; gap:12px; margin-bottom: 8px;">
                        <div style="background:var(--primary); color:white; font-weight:700; border-radius:10px; width:40px; height:40px; display:flex; align-items:center; justify-content:center; font-size:14px;">
                            ${dayNum}
                        </div>
                        <div>
                            <h4 style="font-size:14px; margin-bottom:2px;">${ev.title}</h4>
                            <p style="font-size:12px; color:var(--text-muted);">${ev.date}</p>
                        </div>
                    </div>
                `;
                eventListEl.insertAdjacentHTML('beforeend', card);
            });
        }
    }
}

// Initialize calendar controls after DOM load
document.addEventListener('DOMContentLoaded', initCalendarControls);
