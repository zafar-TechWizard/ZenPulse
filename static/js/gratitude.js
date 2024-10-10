document.addEventListener('DOMContentLoaded', function() {
    const gratitudeForm = document.getElementById('gratitudeForm');
    if (gratitudeForm) {
        gratitudeForm.addEventListener('submit', function(e) {
            e.preventDefault();
            var title = document.getElementById('titleInput').value;
            var content = document.getElementById('contentInput').value;
            var mood = document.getElementById('mood').value;
            var csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

            if (!title) {
                fetch('/gratitude', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'X-CSRFToken': csrfToken
                    },
                    body: new URLSearchParams({
                        'content': content,
                        'mood': mood
                    })
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.json();
                })
                .then(data => {
                    document.getElementById('titleInput').value = data.title;
                    alert('AI-generated title: "' + data.title + '". You can edit it if you want.');
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('An error occurred while generating the title. Please try again.');
                });
            } else {
                this.submit();
            }
        });
    }
});