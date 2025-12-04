// Room-based chat application logic

let socket = null;
let currentRoomSlug = null;
let currentUsername = null;
let isConnected = false;
let activeUsers = new Set(); // Usernames currently active in the room
let allUsers = new Set(); // All usernames who have sent messages

const API_BASE = '/api';
const WS_URL = window.location.origin;

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

function initializeApp() {
    // Get room slug from URL hash
    const hash = window.location.hash.substring(1);
    
    if (!hash) {
        // No room in URL, redirect to home
        window.location.href = '/';
        return;
    }

    currentRoomSlug = hash;
    
    // Check if username is already set in sessionStorage
    const storedUsername = sessionStorage.getItem(`username_${currentRoomSlug}`);
    if (storedUsername) {
        currentUsername = storedUsername;
        showChatInterface();
        connectWebSocket();
        loadMessages();
    } else {
        // Show username modal
        showUsernameModal();
    }
    
    // Listen for hash changes (if user navigates to different room)
    window.addEventListener('hashchange', () => {
        const newHash = window.location.hash.substring(1);
        if (newHash && newHash !== currentRoomSlug) {
            // User navigated to different room
            leaveRoom();
            currentRoomSlug = newHash;
            const storedUsername = sessionStorage.getItem(`username_${newHash}`);
            if (storedUsername) {
                currentUsername = storedUsername;
                showChatInterface();
                connectWebSocket();
                loadMessages();
            } else {
                showUsernameModal();
            }
        }
    });
    
    setupEventListeners();
}

function showUsernameModal() {
    const modal = document.getElementById('usernameModal');
    const chatContainer = document.getElementById('chatContainer');
    
    if (modal) modal.style.display = 'flex';
    if (chatContainer) chatContainer.style.display = 'none';
    
    // Focus on username input
    const usernameInput = document.getElementById('usernameInput');
    if (usernameInput) {
        usernameInput.focus();
    }
}

function showChatInterface() {
    const modal = document.getElementById('usernameModal');
    const chatContainer = document.getElementById('chatContainer');
    
    if (modal) modal.style.display = 'none';
    if (chatContainer) {
        chatContainer.style.display = 'flex';
    }
    
    // Update room name display
    const roomNameEl = document.getElementById('roomName');
    if (roomNameEl) {
        roomNameEl.textContent = currentRoomSlug;
    }
    
    // Update current username display
    const currentUsernameEl = document.getElementById('currentUsername');
    if (currentUsernameEl) {
        currentUsernameEl.textContent = `You: ${currentUsername}`;
    }
    
    // Initialize users list
    updateUsersList();
}

function setupEventListeners() {
    // Username modal - generate random username
    const generateUsernameBtn = document.getElementById('generateUsernameBtn');
    if (generateUsernameBtn) {
        generateUsernameBtn.addEventListener('click', () => {
            const randomUsername = generateRandomUsername();
            const usernameInput = document.getElementById('usernameInput');
            if (usernameInput) {
                usernameInput.value = randomUsername;
            }
        });
    }
    
    // Username modal - set username and continue
    const setUsernameBtn = document.getElementById('setUsernameBtn');
    if (setUsernameBtn) {
        setUsernameBtn.addEventListener('click', () => {
            const usernameInput = document.getElementById('usernameInput');
            const errorDiv = document.getElementById('usernameError');
            
            if (!usernameInput) return;
            
            const username = usernameInput.value.trim();
            
            if (!username) {
                if (errorDiv) {
                    errorDiv.textContent = 'Please enter a username';
                }
                return;
            }
            
            if (username.length > 100) {
                if (errorDiv) {
                    errorDiv.textContent = 'Username must be 100 characters or less';
                }
                return;
            }
            
            // Set username
            currentUsername = username;
            sessionStorage.setItem(`username_${currentRoomSlug}`, username);
            
            // Clear error
            if (errorDiv) errorDiv.textContent = '';
            
            // Show chat interface
            showChatInterface();
            
            // Connect to WebSocket and load messages
            connectWebSocket();
            loadMessages();
            
            // Initialize users list
            updateUsersList();
        });
    }
    
    // Allow Enter key in username input
    const usernameInput = document.getElementById('usernameInput');
    if (usernameInput) {
        usernameInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                const setUsernameBtn = document.getElementById('setUsernameBtn');
                if (setUsernameBtn) setUsernameBtn.click();
            }
        });
    }
    
    // Send message button
    const sendBtn = document.getElementById('sendBtn');
    if (sendBtn) {
        sendBtn.addEventListener('click', sendMessage);
    }
    
    // Message input - Enter key to send
    const messageInput = document.getElementById('messageInput');
    if (messageInput) {
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    }
    
    // Clear chat button
    const clearChatBtn = document.getElementById('clearChatBtn');
    if (clearChatBtn) {
        clearChatBtn.addEventListener('click', () => {
            if (confirm('Are you sure you want to clear all messages in this room? This cannot be undone.')) {
                clearAllMessages();
            }
        });
    }
    
    // Leave room button
    const leaveRoomBtn = document.getElementById('leaveRoomBtn');
    if (leaveRoomBtn) {
        leaveRoomBtn.addEventListener('click', () => {
            if (confirm('Leave this room and return to home?')) {
                window.location.href = '/';
            }
        });
    }
}

function generateRandomUsername() {
    const adjectives = ['Cool', 'Swift', 'Bright', 'Calm', 'Bold', 'Quick', 'Smart', 'Wise', 'Brave', 'Kind'];
    const nouns = ['Tiger', 'Eagle', 'Wolf', 'Lion', 'Fox', 'Bear', 'Hawk', 'Shark', 'Dragon', 'Phoenix'];
    const randomNum = Math.floor(Math.random() * 1000);
    const adj = adjectives[Math.floor(Math.random() * adjectives.length)];
    const noun = nouns[Math.floor(Math.random() * nouns.length)];
    return `${adj}${noun}${randomNum}`;
}

function connectWebSocket() {
    if (!currentRoomSlug || !currentUsername) return;
    
    // Check if Socket.IO is available
    if (typeof io === 'undefined') {
        console.warn('Socket.IO not loaded. Real-time features will be disabled.');
        return;
    }
    
    // Disconnect existing connection if any
    if (socket) {
        socket.disconnect();
    }
    
    try {
        socket = io(WS_URL);
        
        socket.on('connect', () => {
            console.log('WebSocket connected');
            isConnected = true;
            
            // Join the room
            socket.emit('join_room', { room_slug: currentRoomSlug, username: currentUsername });
        });
        
        socket.on('connected', (data) => {
            console.log('Socket.IO connected:', data);
        });
        
        socket.on('joined_room', (data) => {
            console.log('Joined room:', data);
            // Notify server of our username when joining
            socket.emit('user_joined', { room_slug: currentRoomSlug, username: currentUsername });
        });
        
        socket.on('user_joined', (data) => {
            if (data.room_slug === currentRoomSlug && data.username) {
                activeUsers.add(data.username);
                updateUsersList();
            }
        });
        
        socket.on('user_left', (data) => {
            if (data.room_slug === currentRoomSlug && data.username) {
                activeUsers.delete(data.username);
                updateUsersList();
            }
        });
        
        socket.on('active_users', (data) => {
            if (data.room_slug === currentRoomSlug && data.users) {
                activeUsers = new Set(data.users);
                updateUsersList();
            }
        });
        
        socket.on('new_message', (data) => {
            // Only handle messages for current room
            if (data.room_slug === currentRoomSlug) {
                // Add username to all users if it's a new message
                if (data.username) {
                    allUsers.add(data.username);
                }
                // Reload messages to get the latest
                loadMessages();
            }
        });
        
        socket.on('messages_cleared', (data) => {
            // Only handle if it's for current room
            if (data.room_slug === currentRoomSlug) {
                // Clear messages display
                const container = document.getElementById('messagesContainer');
                if (container) {
                    container.innerHTML = '';
                }
            }
        });
        
        socket.on('disconnect', () => {
            console.log('WebSocket disconnected');
            isConnected = false;
            // Remove current user from active users
            activeUsers.delete(currentUsername);
            updateUsersList();
        });
        
        socket.on('error', (error) => {
            console.error('WebSocket error:', error);
        });
    } catch (error) {
        console.error('WebSocket connection error:', error);
    }
}

async function loadMessages() {
    if (!currentRoomSlug) return;
    
    try {
        const response = await fetch(`${API_BASE}/rooms/${currentRoomSlug}/messages`);
        
        if (!response.ok) {
            console.error('Failed to load messages:', response.status);
            return;
        }
        
        const data = await response.json();
        renderMessages(data.messages || []);
    } catch (error) {
        console.error('Error loading messages:', error);
    }
}

function renderMessages(messages) {
    const container = document.getElementById('messagesContainer');
    if (!container) return;
    
    // Clear container
    container.innerHTML = '';
    
    // Extract all unique usernames from messages for past users
    const messageUsernames = new Set();
    messages.forEach(msg => {
        if (msg.username) {
            messageUsernames.add(msg.username);
            allUsers.add(msg.username);
        }
    });
    
    // Update users list after extracting from messages
    updateUsersList();
    
    if (messages.length === 0) {
        const emptyDiv = document.createElement('div');
        emptyDiv.className = 'empty-messages';
        emptyDiv.textContent = 'No messages yet. Start the conversation!';
        emptyDiv.style.textAlign = 'center';
        emptyDiv.style.color = '#999';
        emptyDiv.style.padding = '20px';
        container.appendChild(emptyDiv);
        return;
    }
    
    // Render each message
    messages.forEach(msg => {
        const isSent = msg.username === currentUsername;
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isSent ? 'sent' : 'received'}`;
        
        // Message content
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = msg.content;
        
        // Message metadata
        const metaDiv = document.createElement('div');
        metaDiv.className = 'message-meta';
        
        // Username (only show for received messages)
        if (!isSent) {
            const usernameSpan = document.createElement('span');
            usernameSpan.className = 'message-username';
            usernameSpan.textContent = msg.username;
            metaDiv.appendChild(usernameSpan);
        }
        
        // Timestamp
        const timeSpan = document.createElement('span');
        timeSpan.className = 'message-time';
        const msgDate = new Date(msg.created_at);
        const hours = msgDate.getHours();
        const minutes = msgDate.getMinutes().toString().padStart(2, '0');
        const ampm = hours >= 12 ? 'PM' : 'AM';
        const displayHours = hours % 12 || 12;
        timeSpan.textContent = `${displayHours}:${minutes} ${ampm}`;
        metaDiv.appendChild(timeSpan);
        
        messageDiv.appendChild(contentDiv);
        messageDiv.appendChild(metaDiv);

        container.appendChild(messageDiv);
    });

    // Scroll to bottom
    container.scrollTop = container.scrollHeight;
}

async function sendMessage() {
    if (!currentRoomSlug || !currentUsername) return;
    
    const messageInput = document.getElementById('messageInput');
    if (!messageInput) return;
    
    const content = messageInput.value.trim();
    
    if (!content) return;
    
    if (content.length > 10000) {
        alert('Message is too long (max 10000 characters)');
        return;
    }
    
    // Disable input while sending
    messageInput.disabled = true;
    const sendBtn = document.getElementById('sendBtn');
    if (sendBtn) sendBtn.disabled = true;
    
    try {
        const response = await fetch(`${API_BASE}/rooms/${currentRoomSlug}/messages`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username: currentUsername,
                content: content
            })
        });

        if (response.ok) {
            // Clear input
            messageInput.value = '';
            
            // Reload messages to show the new one
            await loadMessages();
        } else {
            const error = await response.json();
            alert(error.error || 'Failed to send message');
        }
    } catch (error) {
        console.error('Error sending message:', error);
        alert('Failed to send message. Please try again.');
    } finally {
        // Re-enable input
        messageInput.disabled = false;
        if (sendBtn) sendBtn.disabled = false;
        messageInput.focus();
    }
}

async function clearAllMessages() {
    if (!currentRoomSlug) return;
    
    try {
        const response = await fetch(`${API_BASE}/rooms/${currentRoomSlug}/messages`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            // Clear messages display
            const container = document.getElementById('messagesContainer');
            if (container) {
                container.innerHTML = '';
            }
        } else {
            const error = await response.json();
            alert(error.error || 'Failed to clear messages');
        }
    } catch (error) {
        console.error('Error clearing messages:', error);
        alert('Failed to clear messages. Please try again.');
    }
}

function updateUsersList() {
    const activeUsersList = document.getElementById('activeUsersList');
    const pastUsersList = document.getElementById('pastUsersList');
    
    if (!activeUsersList || !pastUsersList) return;
    
    // Clear lists
    activeUsersList.innerHTML = '';
    pastUsersList.innerHTML = '';
    
    // Add current user to active users if connected
    if (isConnected && currentUsername) {
        activeUsers.add(currentUsername);
    }
    
    // Get past users (all users who have sent messages but are not active)
    const pastUsers = Array.from(allUsers).filter(username => !activeUsers.has(username));
    
    // Render active users
    if (activeUsers.size === 0) {
        const emptyDiv = document.createElement('div');
        emptyDiv.className = 'user-item-empty';
        emptyDiv.textContent = 'No active users';
        activeUsersList.appendChild(emptyDiv);
    } else {
        Array.from(activeUsers).sort().forEach(username => {
            const userItem = document.createElement('div');
            userItem.className = 'user-item user-item-active';
            
            const indicator = document.createElement('div');
            indicator.className = 'user-status-indicator';
            
            const nameSpan = document.createElement('span');
            nameSpan.className = 'user-name';
            nameSpan.textContent = username === currentUsername ? `${username} (me)` : username;
            
            userItem.appendChild(indicator);
            userItem.appendChild(nameSpan);
            activeUsersList.appendChild(userItem);
        });
    }
    
    // Render past users
    if (pastUsers.length === 0) {
        const emptyDiv = document.createElement('div');
        emptyDiv.className = 'user-item-empty';
        emptyDiv.textContent = 'No past users';
        pastUsersList.appendChild(emptyDiv);
    } else {
        pastUsers.sort().forEach(username => {
            const userItem = document.createElement('div');
            userItem.className = 'user-item user-item-past';
            
            const nameSpan = document.createElement('span');
            nameSpan.className = 'user-name';
            nameSpan.textContent = username;
            
            userItem.appendChild(nameSpan);
            pastUsersList.appendChild(userItem);
        });
    }
}

function leaveRoom() {
    // Notify server that user is leaving
    if (socket && currentRoomSlug && currentUsername) {
        socket.emit('user_left', { room_slug: currentRoomSlug, username: currentUsername });
        socket.emit('leave_room', { room_slug: currentRoomSlug });
        socket.disconnect();
    }
    
    // Remove from active users
    activeUsers.delete(currentUsername);
    updateUsersList();
    
    socket = null;
    isConnected = false;
}
