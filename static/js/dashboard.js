function toggleTheme() {
    const body = document.body;
    const currentTheme = body.classList.contains('dark-theme') ? 'dark' : 'light';
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

    body.classList.remove(`${currentTheme}-theme`);
    body.classList.add(`${newTheme}-theme`);
    localStorage.setItem('theme', newTheme);

    // Update button icon
    const themeToggle = document.getElementById('theme-toggle');
    themeToggle.innerHTML = newTheme === 'dark' ? '<i class="fas fa-sun"></i>' : '<i class="fas fa-moon"></i>';
}

document.addEventListener('DOMContentLoaded', () => {
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

    // Add this new function to fetch and display AI insights
    function fetchAIInsights() {
        fetch('/api/suggestions')
            .then(response => response.json())
            .then(insights => {
                const insightsGrid = document.getElementById('ai-insights-grid');
                insightsGrid.innerHTML = ''; // Clear existing insights

                insights.forEach((insight, index) => {
                    const card = document.createElement('div');
                    card.className = 'insight-card';

                    const tagClass = index === insights.length - 1 ? 'tag-new' : 'tag-popular';
                    const tagText = index === insights.length - 1 ? 'New' : 'Popular';

                    card.innerHTML = `
                        <div class="insight-icon">
                            <i class="fas ${insight.icon}" style="color: ${getRandomColor()}"></i>
                        </div>
                        <h4 class="insight-title">${insight.title}</h4>
                        <p class="insight-description">${truncateDescription(insight.description, 50)}</p>
                        <div class="insight-action">
                            <button class="try-now-btn">Try</button>
                            <span class="insight-tag ${tagClass}">${tagText}</span>
                        </div>
                    `;

                    insightsGrid.appendChild(card);
                });
            })
            .catch(error => {
                console.error('Error fetching AI insights:', error);
            });
    }

    function truncateDescription(description, maxLength) {
        return description.length > maxLength 
            ? description.substring(0, maxLength - 3) + '...' 
            : description;
    }

    function getRandomColor() {
        const colors = ['#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6', '#1abc9c'];
        return colors[Math.floor(Math.random() * colors.length)];
    }

    // Call the function to fetch and display AI insights
    fetchAIInsights();

    // Add event listener for the refresh button
    const refreshBtn = document.querySelector('.refresh-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', fetchAIInsights);
    }

    // Mood tracking functionality
    const moodForm = document.getElementById('mood-form');
    const moodButtons = moodForm.querySelectorAll('.mood-button');
    const csrfToken = moodForm.querySelector('input[name="csrf_token"]').value;

    moodButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const moodValue = this.value;
            
            fetch('/save_mood', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': csrfToken
                },
                body: `mood=${moodValue}`
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    updateMoodChart();
                    alert('Mood saved successfully!');
                } else {
                    alert('Error saving mood. Please try again.');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred. Please try again.');
            });
        });
    });

    function updateMoodChart() {
        fetch('/get_mood_history')
            .then(response => response.json())
            .then(data => {
                const labels = Object.keys(data);
                const moodScores = Object.values(data);
                
                if (moodChart) {
                    new Chart(moodChart.getContext('2d'), {
                        type: 'line',
                        data: {
                            labels: labels,
                            datasets: [{
                                label: 'Mood',
                                data: moodScores,
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
                }
            });
    }

    // Initial chart update
    updateMoodChart();

    // Add this inside the DOMContentLoaded event listener
    const themeToggle = document.getElementById('theme-toggle');
    const currentTheme = localStorage.getItem('theme') || 'light';
    document.body.classList.add(`${currentTheme}-theme`);
    themeToggle.innerHTML = currentTheme === 'dark' ? '<i class="fas fa-sun"></i>' : '<i class="fas fa-moon"></i>';
    themeToggle.addEventListener('click', toggleTheme);

    // Add this to your existing dashboard.js file
    function updatePetStatus() {
        fetch('/pet_stats')
            .then(response => response.json())
            .then(data => {
                document.getElementById('pet-happiness-bar').style.width = `${data.happiness}%`;
                document.getElementById('pet-energy-bar').style.width = `${data.energy}%`;
                
                let statusMessage = "Your pet is doing great!";
                if (data.happiness < 30 || data.energy < 30) {
                    statusMessage = "Your pet needs some attention!";
                }
                document.getElementById('pet-status-message').textContent = statusMessage;
            })
            .catch(error => console.error('Error fetching pet stats:', error));
    }

    document.getElementById('interact-pet-btn').addEventListener('click', () => {
        window.location.href = '/pet';
    });

    // Call updatePetStatus initially and then every 5 minutes
    updatePetStatus();
    setInterval(updatePetStatus, 5 * 60 * 1000);
});