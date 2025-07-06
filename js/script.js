document.addEventListener('DOMContentLoaded', () => {
    const searchButton = document.getElementById('search-button');
    const searchInput = document.getElementById('search-input');
    const resultsContainer = document.getElementById('results-container');
    const audioPlayer = document.getElementById('audio-player');
    const playerBar = document.getElementById('player-bar');
    const nowPlayingCover = document.getElementById('now-playing-cover');
    const nowPlayingInfo = document.getElementById('now-playing-info');
    const initialMessage = document.getElementById('initial-message');

    let isSearching = false;

    const showLoader = () => {
        resultsContainer.innerHTML = '<div class="loader"></div>';
        if(initialMessage) initialMessage.style.display = 'none';
    };

    const hideLoader = () => {
        const loader = resultsContainer.querySelector('.loader');
        if (loader) {
            loader.remove();
        }
    };

    const searchMusic = async (query) => {
        if (isSearching) return;
        isSearching = true;
        searchButton.disabled = true;
        searchButton.textContent = 'Qidirilmoqda...';
        showLoader();

        try {
            const apiUrl = `/api/search?q=${encodeURIComponent(query)}`;
            
            const response = await fetch(apiUrl);
            if (!response.ok) {
                throw new Error(`Network response was not ok: ${response.statusText}`);
            }

            const data = await response.json();
            if (data.error) {
                throw new Error(`API error: ${data.error}`);
            }
            
            displayResults(data.data || []);

        } catch (error) {
            resultsContainer.innerHTML = `<p class="error-message">Qidiruvda xatolik yuz berdi. Server ishlayotganiga ishonch hosil qiling yoki keyinroq qayta urinib ko'ring.</p>`;
            console.error('Search error:', error);
        } finally {
            isSearching = false;
            searchButton.disabled = false;
            searchButton.textContent = 'Qidirish';
        }
    };

    const displayResults = (tracks) => {
        hideLoader();
        resultsContainer.innerHTML = '';
        if (tracks.length === 0) {
            resultsContainer.innerHTML = '<p>Hech narsa topilmadi. Boshqa so\'rovni sinab ko\'ring.</p>';
            return;
        }

        tracks.forEach(track => {
            if (!track || !track.album || !track.artist) return;

            const trackElement = document.createElement('div');
            trackElement.classList.add('track');
            trackElement.dataset.previewUrl = track.preview;
            
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
                } else {
                    // Maybe show a small, non-disruptive notification
                    trackElement.classList.add('no-preview');
                    setTimeout(() => trackElement.classList.remove('no-preview'), 2000);
                }
            });
            resultsContainer.appendChild(trackElement);
        });
    };

    const handleSearch = () => {
        const query = searchInput.value.trim();
        if (query) {
            searchMusic(query);
        } else {
            // Maybe show a small notification instead of an alert
            searchInput.focus();
            searchInput.placeholder = "Iltimos, qidirish uchun biror nima yozing.";
        }
    };

    searchButton.addEventListener('click', handleSearch);
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleSearch();
        }
    });

    // Set initial message
    if(initialMessage) {
        resultsContainer.innerHTML = '';
        initialMessage.style.display = 'block';
    }
});
