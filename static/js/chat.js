document.addEventListener('DOMContentLoaded', () => {
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const themeToggle = document.getElementById('theme-toggle');
    const promptButtons = document.querySelectorAll('.prompt-button');

    let conversationHistory = [];

    function addMessage(content, isUser = false) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message');
        messageDiv.classList.add(isUser ? 'user' : 'assistant');

        const avatarImg = document.createElement('img');
        avatarImg.src = isUser ? "/static/images/profile.png" : "/static/images/ai-assistant.gif";
        avatarImg.alt = isUser ? "User" : "AI Assistant";
        avatarImg.classList.add('message-avatar');

        const messageContent = document.createElement('div');
        messageContent.classList.add('message-content');

        const messageBubble = document.createElement('div');
        messageBubble.classList.add('message-bubble');
        messageBubble.textContent = content;

        messageContent.appendChild(messageBubble);
        messageDiv.appendChild(avatarImg);
        messageDiv.appendChild(messageContent);

        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Add this function to handle errors
    function handleError(error) {
        console.error("Error:", error);
        addMessage("I'm sorry, I encountered an error. Please try again later.", "assistant");
    }

    // Update the sendMessage function
    async function sendMessage() {
        const message = userInput.value.trim();
        if (message) {
            addMessage(message, true);
            userInput.value = '';

            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken()
                    },
                    body: JSON.stringify({
                        message: message,
                        history: conversationHistory
                    })
                });

                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }

                const data = await response.json();
                addMessage(data.response);
                displaySentimentInfo(data.sentiment, data.dominant_emotion);

                conversationHistory.push({ role: "user", content: message });
                conversationHistory.push({ role: "assistant", content: data.response });

            } catch (error) {
                console.error('Error:', error);
                addMessage("I'm sorry, I encountered an error. Please try again later.", false);
            }
        }
    }

    // Add this function to display sentiment and emotion
    function displaySentimentInfo(sentiment, emotion) {
        const sentimentInfo = document.createElement('div');
        sentimentInfo.classList.add('sentiment-info');
        sentimentInfo.innerHTML = `Sentiment: ${sentiment}, Emotion: ${emotion || 'Neutral'}`;
        chatMessages.appendChild(sentimentInfo);
    }

    // Make sure you have this function to get the CSRF token
    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
    }

    async function getAssistantResponse(userMessage) {
        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrf_token')
                },
                body: JSON.stringify({
                    message: userMessage
                }),
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(`HTTP error! status: ${response.status}, message: ${errorData.error || 'Unknown error'}`);
            }
            
            const data = await response.json();
            return data.response;
        } catch (error) {
            console.error('Error:', error);
            return "I'm sorry, I'm having trouble processing your request right now. Please try again later. ${userMessage}", userMessage;
        }
    }

    async function handleUserInput(message = null) {
        const userMessage = message || userInput.value.trim();
        if (userMessage) {
            addMessage(userMessage, true);
            userInput.value = '';
            
            conversationHistory.push({ role: "user", content: userMessage });
            
            const assistantResponse = await getAssistantResponse(userMessage);
            addMessage(assistantResponse);
            
            conversationHistory.push({ role: "assistant", content: assistantResponse });
            
            if (conversationHistory.length > 10) {
                conversationHistory = conversationHistory.slice(-10);
            }
        }
    }

    sendButton.addEventListener('click', () => handleUserInput());
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleUserInput();
        }
    });

    promptButtons.forEach(button => {
        button.addEventListener('click', () => handleUserInput(button.textContent));
    });

    themeToggle.addEventListener('change', () => {
        document.body.classList.toggle('dark-theme');
    });

    // Initial greeting message
    addMessage("Hello! I'm your virtual psychiatrist. How are you feeling today?");
});
