document.addEventListener('DOMContentLoaded', () => {
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const themeToggle = document.getElementById('theme-toggle');
    const promptButtons = document.querySelectorAll('.prompt-button');
    const clearChatButton = document.getElementById('clear-chat');

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
            return "I'm sorry, I'm having trouble processing your request right now. Please try again later. ${userMessage}";
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

    clearChatButton.addEventListener('click', function() {
        if (confirm('Are you sure you want to clear the entire chat history? This action cannot be undone.')) {
            // Add ripple effect to messages before clearing
            const messages = document.querySelectorAll('.message');
            
            // Reverse the messages array to animate from bottom to top
            Array.from(messages).reverse().forEach((message, index) => {
                setTimeout(() => {
                    message.classList.add('clearing');
                    // Add subtle shake effect to remaining messages
                    const remainingMessages = Array.from(messages).slice(index + 1);
                    remainingMessages.forEach(msg => {
                        msg.style.transform = 'translateX(-2px)';
                        setTimeout(() => {
                            msg.style.transform = 'translateX(0)';
                        }, 50);
                    });
                }, index * 150); // Increased delay for smoother animation
            });

            fetch('/clear_chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
                },
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Wait for all animations to complete
                    setTimeout(() => {
                        const chatMessages = document.getElementById('chat-messages');
                        chatMessages.style.opacity = '0';
                        setTimeout(() => {
                            chatMessages.innerHTML = '';
                            chatMessages.style.opacity = '1';
                        }, 300);
                    }, messages.length * 150 + 800);
                } else {
                    alert('Failed to clear chat history. Please try again.');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while clearing chat history.');
            });
        }
    });
});
