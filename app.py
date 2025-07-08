<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Music Bot</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap" rel="stylesheet">
    <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🎵</text></svg>">
    <style>
        :root {
            --primary-color: #1DB954;
            --primary-color-hover: #1ed760;
            --background-color: #121212;
            --card-color: #181818;
            --card-hover-color: #282828;
            --text-color: #FFFFFF;
            --text-secondary-color: #B3B3B3;
            --border-color: #282828;
            --border-focus-color: var(--primary-color);
            --player-bar-height: 80px;
        }

        *, *::before, *::after {
            box-sizing: border-box;
        }

        body {
            font-family: 'Poppins', sans-serif;
            background-color: var(--background-color);
            color: var(--text-color);
            margin: 0;
            padding: 0;
            display: flex;
            flex-direction: column;
            min-height: 100vh;
        }

        header {
            background-color: rgba(0,0,0,0.7);
            backdrop-filter: blur(10px);
            padding: 1.5rem;
            text-align: center;
            border-bottom: 1px solid var(--border-color);
            position: sticky;
            top: 0;
            z-index: 100;
        }

        h1 {
            margin: 0;
            font-weight: 700;
            color: var(--primary-color);
            letter-spacing: 1px;
        }

        .search-type-container {
            display: flex;
            justify-content: center;
            margin-bottom: 20px;
        }

        .search-type-btn {
            background-color: #333;
            color: #fff;
            border: 1px solid #555;
            padding: 10px 20px;
            margin: 0 5px;
            border-radius: 20px;
            cursor: pointer;
            transition: background-color 0.3s, color 0.3s;
        }

        .search-type-btn:hover {
            background-color: #444;
        }

        .search-type-btn.active {
            background-color: #1DB954;
            color: #fff;
            border-color: #1DB954;
        }

        main {
            flex-grow: 1;
            padding: 2rem;
            padding-bottom: calc(var(--player-bar-height) + 2rem);
        }

        .search-container {
            display: flex;
            justify-content: center;
            margin-bottom: 3rem;
            position: relative;
        }

        #search-input {
            width: 60%;
            max-width: 500px;
            padding: 0.8rem 1.2rem;
            border: 1px solid var(--border-color);
            background-color: var(--card-hover-color);
            color: var(--text-color);
            border-radius: 50px 0 0 50px;
            font-size: 1rem;
            outline: none;
            transition: border-color 0.3s, box-shadow 0.3s;
        }
        #search-input:focus {
            border-color: var(--border-focus-color);
            box-shadow: 0 0 0 3px rgba(29, 185, 84, 0.3);
        }

        #search-button {
            padding: 0.8rem 1.5rem;
            border: none;
            background-color: var(--primary-color);
            color: white;
            cursor: pointer;
            border-radius: 0 50px 50px 0;
            font-size: 1rem;
            font-weight: 600;
            transition: background-color 0.3s;
        }
        #search-button:hover, #search-button:focus {
            background-color: var(--primary-color-hover);
        }

        #results-container {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 1.5rem;
            min-height: 200px;
            position: relative;
        }

        #initial-message {
            color: var(--text-secondary-color);
            text-align: center;
            width: 100%;
            position: absolute;
            top: 50px;
        }

        .track {
            background-color: var(--card-color);
            border-radius: 8px;
            overflow: hidden;
            cursor: pointer;
            transition: transform 0.2s ease-in-out, background-color 0.3s;
            position: relative;
        }

        .track:hover {
            background-color: var(--card-hover-color);
            transform: translateY(-5px);
        }

        .track:hover .play-icon-overlay {
            opacity: 1;
        }

        .track-image-container {
            position: relative;
        }

        .track img {
            width: 100%;
            display: block;
            aspect-ratio: 1 / 1;
            object-fit: cover;
        }

        .play-icon-overlay {
            position: absolute;
            top: 0; left: 0; right: 0; bottom: 0;
            background-color: rgba(0,0,0,0.5);
            display: flex;
            justify-content: center;
            align-items: center;
            opacity: 0;
            transition: opacity 0.3s;
        }

        .track-info {
            padding: 1rem;
        }

        .track-info h3 {
            font-size: 1rem;
            margin: 0 0 0.25rem 0;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .track-info p {
            font-size: 0.8rem;
            margin: 0;
            color: var(--text-secondary-color);
        }

        .loader {
            border: 5px solid #f3f3f3;
            border-top: 5px solid var(--primary-color);
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
            position: absolute;
            left: 50%;
            top: 50px;
            transform: translateX(-50%);
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .error {
            color: #ff4d4d;
            text-align: center;
            width: 100%;
        }

        footer {
            text-align: center;
            padding: 1rem;
            font-size: 0.8rem;
            color: var(--text-secondary-color);
            border-top: 1px solid var(--border-color);
        }

        #player-bar {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            height: var(--player-bar-height);
            background-color: #181818;
            border-top: 1px solid #282828;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 1.5rem;
            transform: translateY(100%);
            transition: transform 0.3s ease-in-out;
        }

        #player-bar.visible {
            transform: translateY(0);
        }

        #player-bar.error #now-playing-info h4 {
            color: #ff4d4d;
        }

        #now-playing {
            display: flex;
            align-items: center;
            gap: 1rem;
            flex-grow: 1;
            min-width: 0;
        }

        #now-playing-cover {
            width: 56px;
            height: 56px;
            border-radius: 4px;
            object-fit: cover;
        }

        #now-playing-info h4, #now-playing-info p {
            margin: 0;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        #audio-player {
            max-width: 500px;
            width: 40%;
        }
    </style>
</head>
<body>
<header>
    <h1>Kino & Music</h1>
</header>
<main>
    <div class="search-type-container">
        <button id="music-btn" class="search-type-btn active">Musiqa</button>
        <button id="movie-btn" class="search-type-btn">Kino</button>
    </div>
    <div class="search-container">
        <input type="text" id="search-input" placeholder="Qo'shiq yoki ijrochini qidiring..." aria-label="Qidirish">
        <button id="search-button">Qidirish</button>
    </div>
    <div id="results-container">
        <p id="initial-message">Sevimli musiqangizni topish uchun qidiruvni boshlang.</p>
    </div>
</main>

<div id="player-bar">
    <div id="now-playing">
        <img id="now-playing-cover" src="https://via.placeholder.com/56" alt="Album cover">
        <div id="now-playing-info">
            <h4>Qo'shiqni tanlang</h4>
            <p>Ijrochi noma'lum</p>
        </div>
    </div>
    <audio id="audio-player" controls></audio>
</div>

<script>
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

        musicBtn.addEventListener('click', () => {
            searchType = 'music';
            musicBtn.classList.add('active');
            movieBtn.classList.remove('active');
            searchInput.placeholder = "Qo'shiq yoki ijrochini qidiring...";
            resultsContainer.innerHTML = '';
            if(initialMessage) initialMessage.style.display = 'block';
        });

        movieBtn.addEventListener('click', () => {
            searchType = 'movie';
            movieBtn.classList.add('active');
            musicBtn.classList.remove('active');
            searchInput.placeholder = 'Film nomini qidiring...';
            resultsContainer.innerHTML = '';
            if(initialMessage) initialMessage.style.display = 'block';
            playerBar.classList.remove('visible');
        });

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

        function playTrack(url, title, artist, imageUrl) {
            nowPlayingInfo.innerHTML = `<h4>Yuklanmoqda...</h4><p>${title}</p>`;
            playerBar.classList.remove('error');
            playerBar.classList.add('visible');
            nowPlayingCover.src = imageUrl;
            audioPlayer.src = '';
            audioPlayer.pause();

            fetch(`/api/download_audio?url=${encodeURIComponent(url)}`)
                .then(response => {
                    if (!response.ok) {
                        return response.json().then(err => { throw new Error(err.error || 'Yuklashda xatolik yuz berdi.') });
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.error) {
                        throw new Error(data.error);
                    }
                    audioPlayer.src = data.audio_path;
                    audioPlayer.play();
                    nowPlayingInfo.innerHTML = `<h4>${title}</h4><p>${artist}</p>`;
                })
                .catch(error => {
                    console.error('Trekni tinglashda xatolik:', error);
                    nowPlayingInfo.innerHTML = `<h4>Xatolik</h4><p>${error.message}</p>`;
                    playerBar.classList.add('error');
                });
        }

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
                        playTrack(track.preview, track.title, track.artist.name, imageUrl);
                    }
                });
                resultsContainer.appendChild(trackElement);
            });
        };

        const displayMovieResults = (movies) => {
            resultsContainer.innerHTML = '';
            playerBar.classList.remove('visible');

            if (!movies || movies.length === 0) {
                resultsContainer.innerHTML = '<p>Hech narsa topilmadi. Boshqa so\'rovni sinab ko\'ring.</p>';
                return;
            }

            movies.forEach(movie => {
                if (!movie) return;

                const movieElement = document.createElement('div');
                movieElement.classList.add('track');

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

        if(initialMessage) {
            resultsContainer.innerHTML = '';
            initialMessage.style.display = 'block';
        }
    });
</script>
</body>
</html>
