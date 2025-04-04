// Music player state
let currentMood = null;
let isPlaying = false;
let currentTrack = null;
let audioPlayer = new Audio();
let isShuffled = false;
let repeatMode = 'none'; // none, one, all
let currentPlaylist = [];
let currentTrackIndex = -1;

// Mood-based playlist recommendations
const moodPlaylists = {
    calm: [
        { id: 'calm1', title: 'Peaceful Piano', artist: 'Various Artists', duration: '3:45', image: '/static/images/peaceful-piano.jpg', audio: '/static/audio/peaceful-piano.mp3' },
        { id: 'calm2', title: 'Gentle Meditation', artist: 'Zen Masters', duration: '5:20', image: '/static/images/meditation.jpg', audio: '/static/audio/gentle-meditation.mp3' },
        { id: 'calm3', title: 'Ocean Waves', artist: 'Nature Sounds', duration: '4:30', image: '/static/images/ocean.jpg', audio: '/static/audio/ocean-waves.mp3' }
    ],
    happy: [
        { id: 'happy1', title: 'Uplifting Beats', artist: 'Joy Division', duration: '4:15', image: '/static/images/uplifting.jpg', audio: '/static/audio/uplifting-beats.mp3' },
        { id: 'happy2', title: 'Positive Vibes', artist: 'Happy Band', duration: '3:30', image: '/static/images/positive.jpg', audio: '/static/audio/positive-vibes.mp3' },
        { id: 'happy3', title: 'Sunny Day', artist: 'The Smiles', duration: '3:45', image: '/static/images/sunny.jpg', audio: '/static/audio/sunny-day.mp3' }
    ],
    focused: [
        { id: 'focus1', title: 'Deep Focus', artist: 'Mind Masters', duration: '4:00', image: '/static/images/deep-focus.jpg', audio: '/static/audio/deep-focus.mp3' },
        { id: 'focus2', title: 'Study Session', artist: 'Brain Wave', duration: '5:00', image: '/static/images/study.jpg', audio: '/static/audio/study-session.mp3' },
        { id: 'focus3', title: 'Concentration', artist: 'Alpha Waves', duration: '4:45', image: '/static/images/concentration.jpg', audio: '/static/audio/concentration.mp3' }
    ],
    energetic: [
        { id: 'energy1', title: 'Morning Boost', artist: 'Energy Plus', duration: '3:45', image: '/static/images/morning.jpg', audio: '/static/audio/morning-boost.mp3' },
        { id: 'energy2', title: 'Workout Mix', artist: 'Fitness Crew', duration: '4:30', image: '/static/images/workout.jpg', audio: '/static/audio/workout-mix.mp3' },
        { id: 'energy3', title: 'Power Up', artist: 'High Energy', duration: '3:15', image: '/static/images/power.jpg', audio: '/static/audio/power-up.mp3' }
    ],
    relaxed: [
        { id: 'relax1', title: 'Evening Calm', artist: 'Chill Masters', duration: '5:15', image: '/static/images/evening.jpg', audio: '/static/audio/evening-calm.mp3' },
        { id: 'relax2', title: 'Sleep Time', artist: 'Dream Team', duration: '6:00', image: '/static/images/sleep.jpg', audio: '/static/audio/sleep-time.mp3' },
        { id: 'relax3', title: 'Gentle Rain', artist: 'Nature Sounds', duration: '5:30', image: '/static/images/rain.jpg', audio: '/static/audio/gentle-rain.mp3' }
    ]
};

// Load recommendations based on current mood
async function loadMoodBasedRecommendations() {
    try {
        const response = await fetch('/api/music/recommendations');
        const data = await response.json();
        
        if (data.tracks) {
            currentMood = data.mood;
            currentPlaylist = data.tracks;
            updateMoodRecommendations(data.mood);
            
            // Update mood button UI
            document.querySelectorAll('.mood-btn').forEach(btn => {
                btn.classList.toggle('active', btn.dataset.mood === data.mood);
            });
        }
    } catch (error) {
        console.error('Error loading recommendations:', error);
    }
}

// Update player UI with track info
function updatePlayerUI(track) {
    if (!track) return;
    
    const playerInfo = document.querySelector('.player-info');
    if (playerInfo) {
        playerInfo.innerHTML = `
            <img src="${track.image || '/static/images/default-album.jpg'}" alt="${track.title}" class="now-playing-img">
            <div class="track-info">
                <h3>${track.title}</h3>
                <p>${track.artist}</p>
            </div>
            <button class="favorite-btn ${track.favorite ? 'active' : ''}" onclick="toggleFavorite('${track.id}', '${track.mood}')">
                <i class="fas fa-heart"></i>
            </button>
        `;
    }
}

// Toggle favorite status
async function toggleFavorite(trackId, mood) {
    try {
        const response = await fetch('/api/music/favorite', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ track_id: trackId, mood: mood })
        });
        
        const data = await response.json();
        if (data.favorite !== undefined) {
            const favoriteBtn = document.querySelector('.favorite-btn');
            favoriteBtn.classList.toggle('active', data.favorite);
        }
    } catch (error) {
        console.error('Error toggling favorite:', error);
    }
}

// Initialize player
document.addEventListener('DOMContentLoaded', () => {
    setupMoodButtons();
    setupPlayerControls();
    setupVolumeControl();
    setupThemeToggle();
    loadMoodBasedRecommendations();
    
    // Set up audio player event listeners
    audioPlayer.addEventListener('timeupdate', updateProgress);
    audioPlayer.addEventListener('ended', handleTrackEnd);
    audioPlayer.addEventListener('loadedmetadata', () => {
        document.getElementById('duration').textContent = formatTime(audioPlayer.duration);
    });
});

// Setup mood selection
function setupMoodButtons() {
    document.querySelectorAll('.mood-btn').forEach(button => {
        button.addEventListener('click', () => {
            const mood = button.dataset.mood;
            currentMood = mood;
            updateMoodRecommendations(mood);
            
            // Visual feedback
            document.querySelectorAll('.mood-btn').forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            
            // Save user preference
            saveUserPreferences();
        });
    });
}

// Update recommendations based on mood
function updateMoodRecommendations(mood) {
    const recommendationsContainer = document.getElementById('mood-recommendations');
    recommendationsContainer.innerHTML = '';

    moodPlaylists[mood].forEach(track => {
        const trackCard = createTrackCard(track);
        recommendationsContainer.appendChild(trackCard);
    });
}

// Create track card element
function createTrackCard(track) {
    const card = document.createElement('div');
    card.className = 'track-card';
    card.innerHTML = `
        <img src="${track.image}" alt="${track.title}">
        <h4>${track.title}</h4>
        <p>${track.artist}</p>
    `;
    card.addEventListener('click', () => playTrack(track));
    return card;
}

// Player controls setup
function setupPlayerControls() {
    const playPauseBtn = document.getElementById('play-pause');
    const prevBtn = document.getElementById('prev-track');
    const nextBtn = document.getElementById('next-track');
    const shuffleBtn = document.getElementById('shuffle');
    const repeatBtn = document.getElementById('repeat');
    const progressBar = document.querySelector('.progress-bar');

    playPauseBtn.addEventListener('click', togglePlayPause);
    prevBtn.addEventListener('click', playPreviousTrack);
    nextBtn.addEventListener('click', playNextTrack);
    shuffleBtn.addEventListener('click', toggleShuffle);
    repeatBtn.addEventListener('click', toggleRepeat);
    progressBar.addEventListener('click', seekTrack);
}

// Play track
function playTrack(track) {
    if (currentTrack?.id === track.id && isPlaying) {
        togglePlayPause();
        return;
    }

    currentTrack = track;
    audioPlayer.src = track.audio;
    audioPlayer.play();
    isPlaying = true;
    updatePlayerUI();
    
    // Update current playlist if not already set
    if (!currentPlaylist.includes(track)) {
        currentPlaylist = moodPlaylists[currentMood];
        currentTrackIndex = currentPlaylist.findIndex(t => t.id === track.id);
    }
}

// Toggle play/pause
function togglePlayPause() {
    if (!currentTrack) return;
    
    if (isPlaying) {
        audioPlayer.pause();
    } else {
        audioPlayer.play();
    }
    isPlaying = !isPlaying;
    updatePlayerUI();
}

// Update player UI
function updatePlayerUI() {
    const playPauseBtn = document.getElementById('play-pause');
    const trackTitle = document.getElementById('track-title');
    const trackArtist = document.getElementById('track-artist');
    const trackArtwork = document.getElementById('track-artwork');
    const shuffleBtn = document.getElementById('shuffle');
    const repeatBtn = document.getElementById('repeat');

    // Update play/pause button
    playPauseBtn.innerHTML = `<i class="fas fa-${isPlaying ? 'pause' : 'play'}"></i>`;
    
    // Update track info
    if (currentTrack) {
        trackTitle.textContent = currentTrack.title;
        trackArtist.textContent = currentTrack.artist;
        trackArtwork.src = currentTrack.image;
        trackArtwork.classList.toggle('playing', isPlaying);
    }

    // Update shuffle and repeat buttons
    shuffleBtn.classList.toggle('active', isShuffled);
    repeatBtn.classList.toggle('active', repeatMode !== 'none');
    repeatBtn.innerHTML = `<i class="fas fa-${repeatMode === 'one' ? 'repeat-1' : 'redo'}"></i>`;
}

// Update progress bar
function updateProgress() {
    const progressBar = document.querySelector('.progress');
    const currentTimeEl = document.getElementById('current-time');
    
    const progress = (audioPlayer.currentTime / audioPlayer.duration) * 100;
    progressBar.style.width = `${progress}%`;
    currentTimeEl.textContent = formatTime(audioPlayer.currentTime);
}

// Format time for display
function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

// Seek track
function seekTrack(e) {
    const progressBar = document.querySelector('.progress-bar');
    const rect = progressBar.getBoundingClientRect();
    const pos = (e.clientX - rect.left) / rect.width;
    audioPlayer.currentTime = pos * audioPlayer.duration;
}

// Handle track end
function handleTrackEnd() {
    if (repeatMode === 'one') {
        audioPlayer.play();
    } else if (repeatMode === 'all' || isShuffled) {
        playNextTrack();
    } else {
        isPlaying = false;
        updatePlayerUI();
    }
}

// Play previous track
function playPreviousTrack() {
    if (!currentPlaylist.length) return;
    
    if (audioPlayer.currentTime > 3) {
        audioPlayer.currentTime = 0;
        return;
    }

    currentTrackIndex = (currentTrackIndex - 1 + currentPlaylist.length) % currentPlaylist.length;
    playTrack(currentPlaylist[currentTrackIndex]);
}

// Play next track
function playNextTrack() {
    if (!currentPlaylist.length) return;
    
    if (isShuffled) {
        const nextIndex = Math.floor(Math.random() * currentPlaylist.length);
        currentTrackIndex = nextIndex;
    } else {
        currentTrackIndex = (currentTrackIndex + 1) % currentPlaylist.length;
    }
    
    playTrack(currentPlaylist[currentTrackIndex]);
}

// Toggle shuffle
function toggleShuffle() {
    isShuffled = !isShuffled;
    document.getElementById('shuffle').classList.toggle('active');
}

// Toggle repeat
function toggleRepeat() {
    const modes = ['none', 'all', 'one'];
    const currentIndex = modes.indexOf(repeatMode);
    repeatMode = modes[(currentIndex + 1) % modes.length];
    updatePlayerUI();
}

// Volume control setup
function setupVolumeControl() {
    const volumeSlider = document.getElementById('volume');
    const volumeIcon = document.querySelector('.volume-control i');
    
    volumeSlider.addEventListener('input', (e) => {
        const volume = e.target.value / 100;
        audioPlayer.volume = volume;
        updateVolumeIcon(volume);
    });

    volumeIcon.addEventListener('click', toggleMute);
}

// Update volume icon
function updateVolumeIcon(volume) {
    const volumeIcon = document.querySelector('.volume-control i');
    volumeIcon.className = 'fas ' + (
        volume === 0 ? 'fa-volume-mute' :
        volume < 0.3 ? 'fa-volume-off' :
        volume < 0.7 ? 'fa-volume-down' :
        'fa-volume-up'
    );
}

// Toggle mute
function toggleMute() {
    const volumeSlider = document.getElementById('volume');
    const wasMuted = audioPlayer.volume === 0;
    
    if (wasMuted) {
        audioPlayer.volume = volumeSlider.value / 100;
    } else {
        audioPlayer.volume = 0;
    }
    
    updateVolumeIcon(audioPlayer.volume);
}

// Theme toggle setup
function setupThemeToggle() {
    const themeToggle = document.getElementById('theme-toggle');
    
    themeToggle.addEventListener('change', () => {
        document.body.classList.toggle('dark-mode');
        saveUserPreferences();
    });
}

// Load meditation tracks
function loadMeditationTracks() {
    const container = document.getElementById('meditation-tracks');
    const tracks = [
        { id: 'med1', title: 'Deep Breathing', artist: 'Meditation Guide', duration: '10:00', image: '/static/images/breathing.jpg', audio: '/static/audio/deep-breathing.mp3' },
        { id: 'med2', title: 'Body Scan', artist: 'Mindfulness Coach', duration: '15:00', image: '/static/images/body-scan.jpg', audio: '/static/audio/body-scan.mp3' },
        { id: 'med3', title: 'Loving Kindness', artist: 'Wellness Guide', duration: '12:00', image: '/static/images/kindness.jpg', audio: '/static/audio/loving-kindness.mp3' }
    ];

    tracks.forEach(track => {
        container.appendChild(createTrackCard(track));
    });
}

// Load focus tracks
function loadFocusTracks() {
    const container = document.getElementById('focus-tracks');
    const tracks = [
        { id: 'focus1', title: 'Alpha Waves', artist: 'Brain Sync', duration: '30:00', image: '/static/images/alpha-waves.jpg', audio: '/static/audio/alpha-waves.mp3' },
        { id: 'focus2', title: 'White Noise', artist: 'Focus Lab', duration: '60:00', image: '/static/images/white-noise.jpg', audio: '/static/audio/white-noise.mp3' },
        { id: 'focus3', title: 'Study Beats', artist: 'Lo-Fi Collective', duration: '45:00', image: '/static/images/study-beats.jpg', audio: '/static/audio/study-beats.mp3' }
    ];

    tracks.forEach(track => {
        container.appendChild(createTrackCard(track));
    });
}

// Save user preferences
function saveUserPreferences() {
    const preferences = {
        mood: currentMood,
        volume: audioPlayer.volume,
        darkMode: document.body.classList.contains('dark-mode')
    };

    fetch('/api/music/preferences', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
        },
        body: JSON.stringify(preferences)
    })
    .catch(error => console.error('Error saving preferences:', error));
}