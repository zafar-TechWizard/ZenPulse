document.addEventListener('DOMContentLoaded', () => {
    const petResponse = document.getElementById('pet-response');
    const userInput = document.getElementById('user-message');
    const sendButton = document.querySelector('.user-input button');
    const themeToggle = document.getElementById('theme-toggle');
    const petImage = document.getElementById('pet-image');
    const petHappiness = document.getElementById('pet-happiness');
    const petIntelligence = document.getElementById('pet-intelligence');
    const petEnergy = document.getElementById('pet-energy');

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
                document.getElementById('pet-happiness').textContent = `${data.happiness}%`;
                document.getElementById('pet-intelligence').textContent = `${data.intelligence}%`;
                document.getElementById('pet-energy').textContent = `${data.energy}%`;
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
            if (data.error) {
                console.error(`Error in ${type} interaction:`, data.error);
                petResponse.textContent = "Oops! Something went wrong. Please try again.";
            } else {
                petResponse.textContent = data.response;
                updatePetStats();
            }
        })
        .catch(error => {
            console.error(`Error in ${type} interaction:`, error);
            petResponse.textContent = "Oops! Something went wrong. Please try again.";
        });
    }

    function sendMessage() {
        const userMessage = userInput.value.trim();
        if (userMessage) {
            petInteraction('chat', userMessage);
            userInput.value = '';
        }
    }

    // Call updatePetStats when the page loads
    updatePetStats();

    // Add event listeners
    sendButton.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            sendMessage();
        }
    });

    // Select buttons by their icon classes and add event listeners
    document.querySelector('button i.fa-dumbbell').parentElement.addEventListener('click', () => petInteraction('pet_train'));
    document.querySelector('button i.fa-gamepad').parentElement.addEventListener('click', () => petInteraction('pet_play'));
    document.querySelector('button i.fa-moon').parentElement.addEventListener('click', () => petInteraction('pet_sleep'));
    document.querySelector('button i.fa-smile').parentElement.addEventListener('click', () => petInteraction('pet_mood'));
    document.querySelector('button i.fa-lightbulb').parentElement.addEventListener('click', () => petInteraction('pet_suggest'));

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