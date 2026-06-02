// App State Management
let moviesState = [];      // Holds all 250 scraped movies
let filteredMovies = [];   // Holds currently searched/filtered movies
let currentSort = {
    column: 'Rank',
    direction: 'asc'       // 'asc' or 'desc'
};
let currentPage = 1;
const pageSize = 25;

// DOM Elements
const btnScrape = document.getElementById('btn-scrape');
const scrapeLoader = document.getElementById('scrape-loader');
const btnDownload = document.getElementById('btn-download');
const searchInput = document.getElementById('search-input');
const resultsCount = document.getElementById('results-count');
const movieTbody = document.getElementById('movie-tbody');
const paginationPanel = document.getElementById('pagination-panel');
const paginationNumbers = document.getElementById('pagination-numbers');
const btnPrev = document.getElementById('btn-prev');
const btnNext = document.getElementById('btn-next');
const statsStatus = document.getElementById('stats-status');

// Dashboard Stats Nodes
const valTotal = document.getElementById('val-total');
const valHighest = document.getElementById('val-highest');
const valAverage = document.getElementById('val-average');
const valOldest = document.getElementById('val-oldest');

// Notification Elements
const notification = document.getElementById('notification');
const notificationIcon = document.getElementById('notification-icon');
const notificationMessage = document.getElementById('notification-message');
const notificationClose = document.getElementById('notification-close');

// Initialize App
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
});

// Setup Event Listeners
function setupEventListeners() {
    // Scrape button click
    btnScrape.addEventListener('click', handleScrape);
    
    // Search input field typing
    searchInput.addEventListener('input', handleSearch);
    
    // Column header sorting
    const headers = document.querySelectorAll('.movie-table th.sortable');
    headers.forEach(header => {
        header.addEventListener('click', () => {
            const column = header.getAttribute('data-sort');
            handleSort(column);
        });
    });
    
    // Pagination controls
    btnPrev.addEventListener('click', () => navigatePage(currentPage - 1));
    btnNext.addEventListener('click', () => navigatePage(currentPage + 1));
    
    // Notification close trigger
    notificationClose.addEventListener('click', hideNotification);
}

// Scrape Handler (AJAX)
async function handleScrape() {
    // 1. Update UI to Loading State
    btnScrape.disabled = true;
    scrapeLoader.classList.remove('hidden');
    btnScrape.querySelector('.btn-text').textContent = 'Scraping IMDb...';
    statsStatus.textContent = 'Scraping...';
    statsStatus.classList.remove('active');
    
    // Disable inputs while scraping
    searchInput.disabled = true;
    searchInput.value = '';
    
    // Show info toast
    showNotification(
        'info', 
        '⚡ Selenium WebDriver started in Headless Mode. Scraping IMDb Top 250... Please wait!'
    );
    
    try {
        // 2. Fetch data from Flask endpoint
        const response = await fetch('/scrape', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        
        if (result.status === 'success') {
            // 3. Store data in state
            moviesState = result.data;
            filteredMovies = [...moviesState];
            
            // 4. Update Dashboard Stats Cards
            updateDashboard(result.stats);
            
            // 5. Reset Table State & Enable Controls
            currentSort = { column: 'Rank', direction: 'asc' };
            currentPage = 1;
            
            searchInput.disabled = false;
            btnDownload.classList.remove('disabled-link');
            btnDownload.removeAttribute('tabindex');
            
            // Render UI
            updateSortHeadersUI();
            renderTable();
            renderPagination();
            
            // Success alert
            showNotification(
                'success', 
                `🎉 Success! Scraped ${result.stats.total_movies} movies. CSV file generated.`
            );
        } else {
            throw new Error(result.message || 'Scraping failed.');
        }
    } catch (error) {
        console.error('Error during scraping:', error);
        statsStatus.textContent = 'Error';
        
        showNotification(
            'error', 
            `❌ Scraping Failed: ${error.message || 'Check Flask server console logs for details.'}`
        );
    } finally {
        // 6. Reset Primary Button UI State
        btnScrape.disabled = false;
        scrapeLoader.classList.add('hidden');
        btnScrape.querySelector('.btn-text').textContent = 'Scrape Movies';
    }
}

// Update Dashboard Statistics Cards
function updateDashboard(stats) {
    // Trigger smooth fade/update
    animateValue(valTotal, 0, stats.total_movies, 800);
    animateValue(valAverage, 0, stats.average_rating, 800, true);
    
    valHighest.textContent = stats.highest_rated;
    valHighest.title = stats.highest_rated; // tooltip
    
    valOldest.textContent = stats.oldest_movie;
    valOldest.title = stats.oldest_movie; // tooltip
    
    statsStatus.textContent = 'Live';
    statsStatus.classList.add('active');
}

// Stats counter-up animation helper
function animateValue(obj, start, end, duration, isFloat = false) {
    let startTimestamp = null;
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        const currentVal = progress * (end - start) + start;
        
        if (isFloat) {
            obj.innerHTML = currentVal.toFixed(2);
        } else {
            obj.innerHTML = Math.floor(currentVal);
        }
        
        if (progress < 1) {
            window.requestAnimationFrame(step);
        }
    };
    window.requestAnimationFrame(step);
}

// Search / Filtering Handler
function handleSearch(e) {
    const query = e.target.value.toLowerCase().trim();
    
    if (query === '') {
        filteredMovies = [...moviesState];
    } else {
        filteredMovies = moviesState.filter(movie => {
            const title = movie['Movie Title'].toLowerCase();
            return title.includes(query);
        });
    }
    
    currentPage = 1; // Reset to page 1 on new search
    
    // Sort again based on current column sorting since data subsets changed
    sortData();
    
    renderTable();
    renderPagination();
}

// Sorting Handler
function handleSort(column) {
    if (moviesState.length === 0) return;
    
    // Toggle direction or change column
    if (currentSort.column === column) {
        currentSort.direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
    } else {
        currentSort.column = column;
        currentSort.direction = 'asc';
    }
    
    updateSortHeadersUI();
    sortData();
    renderTable();
    renderPagination();
}

// Perform actual sorting on filteredMovies list
function sortData() {
    const col = currentSort.column;
    const dir = currentSort.direction === 'asc' ? 1 : -1;
    
    filteredMovies.sort((a, b) => {
        let valA = a[col];
        let valB = b[col];
        
        // Handle sorting types
        if (col === 'Movie Title') {
            return dir * valA.localeCompare(valB, 'en', { sensitivity: 'base' });
        } else {
            // Numeric comparison for Rank, Release Year, IMDb Rating
            return dir * (parseFloat(valA) - parseFloat(valB));
        }
    });
}

// Update the direction icons on the table headers
function updateSortHeadersUI() {
    const headers = document.querySelectorAll('.movie-table th.sortable');
    headers.forEach(header => {
        const col = header.getAttribute('data-sort');
        const indicator = header.querySelector('.sort-indicator');
        
        if (col === currentSort.column) {
            header.classList.add('active');
            indicator.textContent = currentSort.direction === 'asc' ? '▲' : '▼';
        } else {
            header.classList.remove('active');
            indicator.textContent = '';
        }
    });
}

// Render Table Rows for Current Page
function renderTable() {
    movieTbody.innerHTML = '';
    
    const totalCount = filteredMovies.length;
    resultsCount.textContent = `Showing ${totalCount === 0 ? 0 : (currentPage - 1) * pageSize + 1} - ${Math.min(currentPage * pageSize, totalCount)} of ${totalCount} movies`;
    
    if (totalCount === 0) {
        movieTbody.innerHTML = `
            <tr class="empty-state-row">
                <td colspan="4" class="text-center">
                    <div class="empty-state">
                        <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                            <circle cx="12" cy="12" r="10"/>
                            <line x1="12" y1="8" x2="12" y2="12"/>
                            <line x1="12" y1="16" x2="12.01" y2="16"/>
                        </svg>
                        <p>No matching movies found for your search.</p>
                    </div>
                </td>
            </tr>
        `;
        return;
    }
    
    // Slice data for pagination
    const startIndex = (currentPage - 1) * pageSize;
    const pageData = filteredMovies.slice(startIndex, startIndex + pageSize);
    
    pageData.forEach(movie => {
        const row = document.createElement('tr');
        
        // Highlight row depending on high score/stats (just visually appealing touch)
        let ratingBadgeClass = '';
        if (movie['IMDb Rating'] >= 9.0) ratingBadgeClass = 'text-gold';
        
        row.innerHTML = `
            <td class="font-semibold text-muted">#${movie['Rank']}</td>
            <td class="movie-title-cell">${escapeHtml(movie['Movie Title'])}</td>
            <td class="text-center font-medium">${movie['Release Year']}</td>
            <td class="text-center">
                <div class="rating-cell">
                    <svg class="star-rating-icon" viewBox="0 0 24 24" fill="currentColor">
                        <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
                    </svg>
                    <span class="rating-value font-bold ${ratingBadgeClass}">${movie['IMDb Rating'].toFixed(1)}</span>
                </div>
            </td>
        `;
        movieTbody.appendChild(row);
    });
}

// Render Pagination Numbers
function renderPagination() {
    const totalCount = filteredMovies.length;
    const totalPages = Math.ceil(totalCount / pageSize);
    
    paginationNumbers.innerHTML = '';
    
    if (totalPages <= 1) {
        paginationPanel.classList.add('hidden');
        return;
    }
    
    paginationPanel.classList.remove('hidden');
    
    // Configure Prev/Next buttons active status
    btnPrev.disabled = currentPage === 1;
    btnNext.disabled = currentPage === totalPages;
    
    // Generate page buttons array
    let pages = [];
    if (totalPages <= 6) {
        for (let i = 1; i <= totalPages; i++) pages.push(i);
    } else {
        // Complex slider with ellipsis
        if (currentPage <= 3) {
            pages = [1, 2, 3, 4, '...', totalPages];
        } else if (currentPage >= totalPages - 2) {
            pages = [1, '...', totalPages - 3, totalPages - 2, totalPages - 1, totalPages];
        } else {
            pages = [1, '...', currentPage - 1, currentPage, currentPage + 1, '...', totalPages];
        }
    }
    
    // Create elements
    pages.forEach(p => {
        const btn = document.createElement('button');
        if (p === '...') {
            btn.className = 'page-num dots';
            btn.textContent = '...';
        } else {
            btn.className = `page-num ${p === currentPage ? 'active' : ''}`;
            btn.textContent = p;
            btn.addEventListener('click', () => navigatePage(p));
        }
        paginationNumbers.appendChild(btn);
    });
}

// Page Navigation
function navigatePage(pageNum) {
    const totalPages = Math.ceil(filteredMovies.length / pageSize);
    if (pageNum < 1 || pageNum > totalPages) return;
    
    currentPage = pageNum;
    renderTable();
    renderPagination();
    
    // Scroll smoothly to table top
    document.querySelector('.data-section').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// Show Toast Alerts
let notificationTimeout;
function showNotification(type, message) {
    clearTimeout(notificationTimeout);
    
    // Set notification types classes
    notification.className = `notification ${type}`;
    notificationMessage.textContent = message;
    
    // Add custom SVG icon based on type
    if (type === 'success') {
        notificationIcon.innerHTML = `
            <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <polyline points="20 6 9 17 4 12"/>
            </svg>
        `;
    } else if (type === 'error') {
        notificationIcon.innerHTML = `
            <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <circle cx="12" cy="12" r="10"/>
                <line x1="12" y1="8" x2="12" y2="12"/>
                <line x1="12" y1="16" x2="12.01" y2="16"/>
            </svg>
        `;
    } else { // info
        notificationIcon.innerHTML = `
            <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <circle cx="12" cy="12" r="10"/>
                <line x1="12" y1="16" x2="12" y2="12"/>
                <line x1="12" y1="8" x2="12.01" y2="8"/>
            </svg>
        `;
    }
    
    notification.classList.remove('hidden');
    
    // Auto hide after 8 seconds
    notificationTimeout = setTimeout(hideNotification, 8000);
}

function hideNotification() {
    notification.classList.add('hidden');
}

// XSS Sanitizer Helper
function escapeHtml(str) {
    const div = document.createElement('div');
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
}
