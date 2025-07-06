document.addEventListener('DOMContentLoaded', () => {
    // Element references
    const musicBtn = document.getElementById('music-btn');
    const movieBtn = document.getElementById('movie-btn');
    const searchButton = document.getElementById('search-button');
    const searchInput = document.getElementById('search-input');
    const resultsContainer = document.getElementById('results-container');
    const audioPlayer = document.getElementById('audio-player');
    const playerBar = document.getElementById('player-bar');
    const nowPlayingCover = document.getElementById('now-playing-cover');
    const nowPlayingInfo = document.getElementById('now-playing-info');
    const initialMessage = document.getElementById('initial-message');

    // State
    let searchType = 'music'; // 'music' or 'movie'

    // --- Event Listeners ---

    // Search type selection
    musicBtn.addEventListener('click', () => {
        searchType = 'music';
        musicBtn.classList.add('active');
        movieBtn.classList.remove('active');
        searchInput.placeholder = "Qo'shiq yoki ijrochini qidiring...";
        resultsContainer.innerHTML = ''; // Clear results
        if(initialMessage) initialMessage.style.display = 'block';
    });

    movieBtn.addEventListener('click', () => {
        searchType = 'movie';
        movieBtn.classList.add('active');
        musicBtn.classList.remove('active');
        searchInput.placeholder = 'Film nomini qidiring...';
        resultsContainer.innerHTML = ''; // Clear results
        if(initialMessage) initialMessage.style.display = 'block';
        playerBar.classList.remove('visible'); // Hide music player
    });

    // Search execution
    searchButton.addEventListener('click', () => performSearch());
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            performSearch();
        }
    });

    // --- Core Functions ---

    const performSearch = async () => {
        const query = searchInput.value.trim();
        if (!query) {
            searchInput.focus();
            return;
        }

        resultsContainer.innerHTML = '<div class="loader"></div>';
        if(initialMessage) initialMessage.style.display = 'none';

        const endpoint = searchType === 'music' ? '/api/search' : '/api/search_movie';
        const apiUrl = `${endpoint}?q=${encodeURIComponent(query)}`;

        try {
            const response = await fetch(apiUrl);
            if (!response.ok) {
                throw new Error(`Server xatosi: ${response.status}`);
            }
            const results = await response.json();
            
            if (searchType === 'music') {
                displayMusicResults(results.data || []);
            } else {
                displayMovieResults(results.data || []);
            }
        } catch (error) {
            console.error('Qidiruvda xato:', error);
            resultsContainer.innerHTML = '<p class="error">Natijalarni yuklashda xatolik yuz berdi.</p>';
        }
    };

    const displayMusicResults = (tracks) => {
        resultsContainer.innerHTML = '';
        if (tracks.length === 0) {
            resultsContainer.innerHTML = '<p>Hech narsa topilmadi. Boshqa so\'rovni sinab ko\'ring.</p>';
            return;
        }

        tracks.forEach(track => {
            if (!track || !track.album || !track.artist) return;

            const trackElement = document.createElement('div');
            trackElement.classList.add('track');
            
            const imageUrl = track.album.cover_medium || 'https://via.placeholder.com/250';

            trackElement.innerHTML = `
                <div class="track-image-container">
                    <img src="${imageUrl}" alt="${track.title}" loading="lazy">
                    <div class="play-icon-overlay">
                        <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="white"><path d="M8 5v14l11-7z"/></svg>
                    </div>
                </div>
                <div class="track-info">
                    <h3>${track.title}</h3>
                    <p>${track.artist.name}</p>
                </div>
            `;

            trackElement.addEventListener('click', () => {
                if (track.preview) {
                    audioPlayer.src = track.preview;
                    audioPlayer.play();
                    playerBar.classList.add('visible');
                    nowPlayingCover.src = imageUrl;
                    nowPlayingInfo.innerHTML = `<h4>${track.title}</h4><p>${track.artist.name}</p>`;
                }
            });
            resultsContainer.appendChild(trackElement);
        });
    };

    const displayMovieResults = (movies) => {
        resultsContainer.innerHTML = '';
        playerBar.classList.remove('visible'); // Hide music player

        if (!movies || movies.length === 0) {
            resultsContainer.innerHTML = '<p>Hech narsa topilmadi. Boshqa so\'rovni sinab ko\'ring.</p>';
            return;
        }

        movies.forEach(movie => {
            if (!movie) return;

            const movieElement = document.createElement('div');
            movieElement.classList.add('track'); // Reuse styles

            const imageUrl = movie.poster_path ? `https://image.tmdb.org/t/p/w500${movie.poster_path}` : 'https://via.placeholder.com/250x375.png?text=Rasm+yo\'q';

            movieElement.innerHTML = `
                <div class="track-image-container">
                    <img src="${imageUrl}" alt="${movie.title}" loading="lazy">
                </div>
                <div class="track-info">
                    <h3>${movie.title}</h3>
                    <p>${movie.release_date ? movie.release_date.split('-')[0] : 'Noma\'lum'} | ⭐ ${movie.vote_average.toFixed(1)}</p>
                </div>
            `;
            resultsContainer.appendChild(movieElement);
        });
    };

    // Set initial message
    if(initialMessage) {
        resultsContainer.innerHTML = '';
        initialMessage.style.display = 'block';
    }
});
