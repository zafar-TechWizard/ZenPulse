document.addEventListener('DOMContentLoaded', () => {
    // Render mood chart
    const ctx = document.getElementById('moodChart').getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            datasets: [{
                label: 'Mood',
                data: [3, 4, 2, 5, 3, 4, 4],
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 5
                }
            }
        }
    });

    // Add hover effects to feature tiles
    const featureTiles = document.querySelectorAll('.feature-tile');
    featureTiles.forEach(tile => {
        tile.addEventListener('mouseenter', () => {
            tile.style.transform = 'translateY(-5px)';
        });
        tile.addEventListener('mouseleave', () => {
            tile.style.transform = 'translateY(0)';
        });
    });

    // Handle feature button clicks
    const featureButtons = document.querySelectorAll('.feature-button');
    featureButtons.forEach(button => {
        button.addEventListener('click', (e) => {
            const feature = e.target.closest('.feature-tile').querySelector('h3').textContent;
            console.log(`User clicked on ${feature}`);
            // Here you can add code to navigate to the specific feature page
        });
    });

    // Handle recommendation button click
    const recommendationButton = document.querySelector('.recommendation-button');
    if (recommendationButton) {
        recommendationButton.addEventListener('click', () => {
            console.log('User clicked on recommendation');
            // Here you can add code to follow the recommendation
        });
    }

    // Handle quick mood check
    const quickMoodCheck = document.getElementById('quick-mood-check');
    if (quickMoodCheck) {
        quickMoodCheck.addEventListener('click', () => {
            console.log('User clicked quick mood check');
            // Here you can add code to open a mood check modal or navigate to mood check page
        });
    }

    // Handle notifications click
    const notificationsButton = document.getElementById('notifications');
    if (notificationsButton) {
        notificationsButton.addEventListener('click', () => {
            console.log('User clicked notifications');
            // Here you can add code to show notifications panel
        });
    }

    // Handle quick access toolbar clicks
    const quickAccessButtons = document.querySelectorAll('.quick-access-toolbar button');
    quickAccessButtons.forEach(button => {
        button.addEventListener('click', (e) => {
            console.log(`User clicked ${e.target.textContent.trim()}`);
            // Here you can add code to handle each quick access action
        });
    });

    // Theme toggle functionality
    const themeToggle = document.getElementById('theme-toggle');
    const body = document.body;
    const icon = themeToggle.querySelector('i');

    function setTheme(isDark) {
        body.classList.remove('transitioning');
        body.classList.toggle('dark-theme', isDark);
        body.classList.toggle('light-theme', !isDark);
        updateThemeIcon(isDark);
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
    }

    function toggleTheme() {
        body.classList.add('transitioning');
        const isDark = !body.classList.contains('dark-theme');
        setTheme(isDark);
        setTimeout(() => {
            body.classList.remove('transitioning');
        }, 300);
    }

    function updateThemeIcon(isDark) {
        if (isDark) {
            icon.classList.remove('fa-moon');
            icon.classList.add('fa-sun');
        } else {
            icon.classList.remove('fa-sun');
            icon.classList.add('fa-moon');
        }
    }

    themeToggle.addEventListener('click', toggleTheme);

    // Check for saved theme preference or use system preference
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        setTheme(savedTheme === 'dark');
    } else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        setTheme(true);
    }

    // Listen for changes in system color scheme
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
        if (!localStorage.getItem('theme')) {
            setTheme(e.matches);
        }
    });

    // Virtual Psychiatrist Chat
    const chatContent = document.getElementById('chat-content');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-message');
    const chatInfoButton = document.getElementById('chat-info');

    let conversationHistory = [];

    function addMessage(content, isUser = false) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message');
        if (isUser) {
            messageDiv.classList.add('user');
        } else {
            messageDiv.classList.add('assistant');
            const img = document.createElement('img');
            img.src = "{{ url_for('static', filename='images/ai-assistant.gif') }}";
            img.alt = "AI Assistant";
            img.classList.add('assistant-pic');
            messageDiv.appendChild(img);
        }
        const p = document.createElement('p');
        p.textContent = content;
        messageDiv.appendChild(p);
        chatContent.appendChild(messageDiv);
        chatContent.scrollTop = chatContent.scrollHeight;
    }

    async function getAssistantResponse(userMessage) {
        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: userMessage,
                    history: conversationHistory
                }),
            });
            const data = await response.json();
            return data.response;
        } catch (error) {
            console.error('Error:', error);
            return "I'm sorry, I'm having trouble processing your request right now. Please try again later.";
        }
    }

    async function handleUserInput() {
        const userMessage = userInput.value.trim();
        if (userMessage) {
            addMessage(userMessage, true);
            userInput.value = '';
            
            conversationHistory.push({ role: "user", content: userMessage });
            
            const assistantResponse = await getAssistantResponse(userMessage);
            addMessage(assistantResponse);
            
            conversationHistory.push({ role: "assistant", content: assistantResponse });
            
            // Limit conversation history to last 10 messages
            if (conversationHistory.length > 10) {
                conversationHistory = conversationHistory.slice(-10);
            }
        }
    }

    sendButton.addEventListener('click', handleUserInput);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleUserInput();
        }
    });

    chatInfoButton.addEventListener('click', () => {
        alert('This is a virtual psychiatrist chat. Feel free to share your thoughts and feelings. Remember, for serious mental health concerns, please consult with a licensed professional.');
    });

    // Chat tab functionality
    const tabButtons = document.querySelectorAll('.chat .chat-tabs .tab-button');
    const tabContents = document.querySelectorAll('.chat .chat-content .tab-content');

    if (tabButtons.length > 0 && tabContents.length > 0) {
        tabButtons.forEach(button => {
            button.addEventListener('click', () => {
                const tabName = button.getAttribute('data-tab');
                
                // Deactivate all tabs
                tabButtons.forEach(btn => btn.classList.remove('active'));
                tabContents.forEach(content => content.classList.remove('active'));
                
                // Activate the clicked tab
                button.classList.add('active');
                const activeContent = document.getElementById(`${tabName}-content`);
                if (activeContent) {
                    activeContent.classList.add('active');
                }
            });
        });
    }

    // Mood selector functionality
    const moodSelector = document.getElementById('mood-selector');
    if (moodSelector) {
        moodSelector.addEventListener('change', function() {
            // Here you can add code to send the mood data to your backend
            console.log('Mood selected:', moodSelector.value);
        });
    }

    // Quick action buttons
    const startChatBtn = document.getElementById('start-chat');
    if (startChatBtn) {
        startChatBtn.addEventListener('click', function() {
            // Add functionality to start a chat
            console.log('Starting chat...');
        });
    }

    const playMusicBtn = document.getElementById('play-music');
    if (playMusicBtn) {
        playMusicBtn.addEventListener('click', function() {
            // Add functionality to play music
            console.log('Playing music...');
        });
    }

    const writeJournalBtn = document.getElementById('write-journal');
    if (writeJournalBtn) {
        writeJournalBtn.addEventListener('click', function() {
            // Add functionality to open journal
            console.log('Opening journal...');
        });
    }

    // New quote button
    const newQuoteBtn = document.getElementById('new-quote-btn');
    if (newQuoteBtn) {
        newQuoteBtn.addEventListener('click', function() {
            // Here you would typically fetch a new quote from your backend
            const quotes = [
                "Believe you can and you're halfway there.",
                "You are never too old to set another goal or to dream a new dream.",
                "The only way to do great work is to love what you do."
            ];
            const randomQuote = quotes[Math.floor(Math.random() * quotes.length)];
            const dailyQuoteElement = document.querySelector('#daily-quote p');
            if (dailyQuoteElement) {
                dailyQuoteElement.textContent = randomQuote;
            }
        });
    }

    // Mobile menu toggle
    const menuToggle = document.querySelector('.menu-toggle');
    const navContainer = document.querySelector('.nav-container');

    menuToggle.addEventListener('click', () => {
        navContainer.classList.toggle('show');
    });

    // Close menu when clicking outside
    document.addEventListener('click', (event) => {
        const isClickInsideNav = navContainer.contains(event.target) || menuToggle.contains(event.target);
        if (!isClickInsideNav && navContainer.classList.contains('show')) {
            navContainer.classList.remove('show');
        }
    });

    // Close menu when window is resized to larger screen
    window.addEventListener('resize', () => {
        if (window.innerWidth > 992 && navContainer.classList.contains('show')) {
            navContainer.classList.remove('show');
        }
    });

    // ... (rest of the existing code) ...
});