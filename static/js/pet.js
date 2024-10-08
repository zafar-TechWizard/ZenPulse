document.addEventListener('DOMContentLoaded', () => {
    const petResponse = document.getElementById('pet-response');
    const userInput = document.getElementById('user-message');
    const sendButton = document.getElementById('send-button');
    const suggestionButtons = document.querySelectorAll('.suggestion-btn');
    const typingIndicator = document.querySelector('.typing-indicator');
    const themeToggle = document.getElementById('theme-toggle');
    const petImage = document.getElementById('pet-image');
    const petHappiness = document.getElementById('pet-happiness');
    const petIntelligence = document.getElementById('pet-intelligence');
    const petEnergy = document.getElementById('pet-energy');

    function setGaugeValue(gaugeId, value) {
        const gauge = document.querySelector(`#${gaugeId} .gauge-fill`);
        const gaugeText = document.querySelector(`#${gaugeId} .gauge-text`);
        const circumference = 2 * Math.PI * 45;
        const offset = circumference - (value / 100) * circumference;
        
        gauge.style.strokeDasharray = `${circumference} ${circumference}`;
        gauge.style.strokeDashoffset = offset;
        gaugeText.textContent = `${value}%`;
    }

    function animateGauge(gaugeId, startValue, endValue, duration) {
        const start = performance.now();
        
        function update(time) {
            const elapsed = time - start;
            const progress = Math.min(elapsed / duration, 1);
            const currentValue = startValue + (endValue - startValue) * progress;
            
            setGaugeValue(gaugeId, Math.round(currentValue));
            
            if (progress < 1) {
                requestAnimationFrame(update);
            }
        }
        
        requestAnimationFrame(update);
    }

    function updateStat(statId, value) {
        const progressBar = document.querySelector(`#${statId} .progress`);
        progressBar.style.width = `${value}%`;
    }

    function updatePetStats() {
        fetch('/pet_stats')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                if (data.error) {
                    console.error('Error fetching pet stats:', data.error);
                    return;
                }
                
                updateStat('happiness-stat', data.happiness);
                updateStat('intelligence-stat', data.intelligence);
                updateStat('energy-stat', data.energy);
            })
            .catch(error => {
                console.error('Error fetching pet stats:', error);
                // Optionally, update UI to show error state
            });
    }

    function petInteraction(type, message = '') {
        const url = type === 'chat' ? '/pet_interaction' : `/${type}`;
        const method = type === 'chat' ? 'POST' : 'GET';
        const body = type === 'chat' ? JSON.stringify({ message: message }) : null;

        showTypingIndicator();  // Show typing indicator before fetch

        fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrf_token')
            },
            body: body
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            hideTypingIndicator();  // Hide typing indicator after response
            if (data.error) {
                console.error(`Error in ${type} interaction:`, data.error);
                petResponse.textContent = "Oops! Something went wrong. Please try again.";
            } else {
                petResponse.textContent = data.response;
                updatePetStats();
            }
        })
        .catch(error => {
            hideTypingIndicator();  // Hide typing indicator on error
            console.error(`Error in ${type} interaction:`, error);
            petResponse.textContent = "Oops! Something went wrong. Please try again.";
        });
    }

    function showTypingIndicator() {
        typingIndicator.style.display = 'flex';
        petResponse.style.display = 'none';  // Hide the pet response
    }

    function hideTypingIndicator() {
        typingIndicator.style.display = 'none';
        petResponse.style.display = 'block';  // Show the pet response
    }

    function sendMessage(message) {
        if (message) {
            showTypingIndicator();  // Show typing indicator before sending message
            petInteraction('chat', message);
            userInput.value = '';
        }
    }

    // Call updatePetStats when the page loads
    updatePetStats();

    // Add event listeners
    sendButton.addEventListener('click', () => sendMessage(userInput.value.trim()));
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            sendMessage(userInput.value.trim());
        }
    });

    suggestionButtons.forEach(button => {
        button.addEventListener('click', () => {
            sendMessage(button.textContent);
        });
    });

    // Select buttons by their icon classes and add event listeners
    document.querySelector('button i.fa-gamepad').parentElement.addEventListener('click', () => petInteraction('pet_play'));
    document.querySelector('button i.fa-bed').parentElement.addEventListener('click', () => petInteraction('pet_sleep'));
    document.querySelector('button i.fa-smile').parentElement.addEventListener('click', () => petInteraction('pet_mood'));
    document.querySelector('button i.fa-lightbulb').parentElement.addEventListener('click', () => petInteraction('pet_suggest'));

    // Update this line to select the feed button
    document.querySelector('button i.fa-utensils').parentElement.addEventListener('click', () => petInteraction('pet_feed'));

    themeToggle.addEventListener('change', () => {
        document.body.classList.toggle('dark-theme');
    });

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});