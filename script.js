// ============================================
// WildAtlas - Main JavaScript File
// Inspired by Facts.app
// ============================================

// Global state
let allAnimals = [];

// ============================================
// Initialize on DOM Load
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    console.log('🦁 WildAtlas initializing...');
    
    // Detect which page we're on
    const isHomePage = document.getElementById('grid') !== null;
    const isDetailPage = document.getElementById('animal-name') !== null;
    
    if (isHomePage) {
        console.log('📍 Home page detected');
        initHomePage();
    } else if (isDetailPage) {
        console.log('📍 Detail page detected');
        initDetailPage();
    } else {
        console.log('⚠️ Unknown page type');
    }
});

// ============================================
// Home Page Functions (index.html)
// ============================================
function initHomePage() {
    const grid = document.getElementById('grid');
    const searchInput = document.getElementById('search-input');
    
    // Fetch animal data
    fetchAnimals()
        .then(animals => {
            allAnimals = animals;
            console.log(`✅ Loaded ${animals.length} animals`);
            renderGrid(animals);
        })
        .catch(error => {
            console.error('❌ Error loading animals:', error);
            if (grid) {
                grid.innerHTML = `
                    <div class="error-message" style="grid-column: 1/-1; text-align: center; padding: 60px 20px;">
                        <h2 style="color: #f87171; margin-bottom: 15px;">⚠️ Unable to Load Data</h2>
                        <p style="color: #94a3b8;">${error.message}</p>
                        <p style="color: #64748b; font-size: 0.9rem; margin-top: 20px;">
                            Try refreshing the page (Ctrl+Shift+R or Cmd+Shift+R)
                        </p>
                    </div>
                `;
            }
        });
    
    // Search functionality
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase().trim();
            filterAnimals(query);
        });
    }
}

/**
 * Fetch animals from JSON file
 */
async function fetchAnimals() {
    const response = await fetch('data/animals.json?t=' + Date.now());
    
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: Failed to load animals.json`);
    }
    
    return await response.json();
}

/**
 * Render animal cards on home page
 */
function renderGrid(animals) {
    const grid = document.getElementById('grid');
    if (!grid) return;
    
    grid.innerHTML = '';
    
    if (animals.length === 0) {
        grid.innerHTML = `
            <div class="no-results" style="grid-column: 1/-1; text-align: center; padding: 60px 20px;">
                <h2 style="color: #64748b; margin-bottom: 10px;">No animals found</h2>
                <p style="color: #475569;">Try searching for something else.</p>
            </div>
        `;
        return;
    }
    
    animals.forEach(animal => {
        const card = document.createElement('div');
        card.className = 'card';
        
        const statusClass = getConservationClass(animal.ecology?.conservation_status);
        const statusLabel = animal.ecology?.conservation_status || '';
        const imageUrl = animal.image ? animal.image.trim() : 'https://via.placeholder.com/330x200?text=No+Image';
        const summary = animal.summary || animal.description || 'No description available.';
        
        card.innerHTML = `
            <img src="${imageUrl}" alt="${animal.name}" loading="lazy">
            <div class="card-content">
                <h3>${animal.name}</h3>
                <p class="scientific-name">${animal.scientific_name}</p>
                <p>${truncateText(summary, 100)}</p>
                ${statusLabel ? `<span class="conservation-badge ${statusClass}">${statusLabel}</span>` : ''}
            </div>
        `;
        
        card.addEventListener('click', () => {
            window.location.href = `animal.html?name=${encodeURIComponent(animal.name)}`;
        });
        
        grid.appendChild(card);
    });
}

/**
 * Filter animals by search query
 */
function filterAnimals(query) {
    if (!query) {
        renderGrid(allAnimals);
        return;
    }
    
    const filtered = allAnimals.filter(animal => {
        const nameMatch = animal.name?.toLowerCase().includes(query);
        const scientificMatch = animal.scientific_name?.toLowerCase().includes(query);
        const typeMatch = animal.animal_type?.toLowerCase().includes(query);
        const habitatMatch = animal.ecology?.habitat?.toLowerCase().includes(query);
        const locationMatch = animal.ecology?.locations?.toLowerCase().includes(query);
        
        return nameMatch || scientificMatch || typeMatch || habitatMatch || locationMatch;
    });
    
    renderGrid(filtered);
}

// ============================================
// Detail Page Functions (animal.html)
// ============================================
function initDetailPage() {
    const params = new URLSearchParams(window.location.search);
    const animalName = params.get('name');
    
    if (!animalName) {
        console.warn('⚠️ No animal name in URL, redirecting to home');
        window.location.href = 'index.html';
        return;
    }
    
    console.log(`🔍 Loading data for: ${animalName}`);
    
    fetchAnimals()
        .then(animals => {
            const animal = animals.find(a => 
                a.name.toLowerCase() === decodeURIComponent(animalName).toLowerCase()
            );
            
            if (!animal) {
                console.error('❌ Animal not found:', animalName);
                document.getElementById('animal-name').textContent = 'Animal Not Found';
                document.getElementById('animal-summary').textContent = 
                    'The animal you are looking for could not be found. Please go back and try again.';
                return;
            }
            
            console.log('✅ Animal data loaded:', animal.name);
            populateDetailPage(animal);
        })
        .catch(error => {
            console.error('❌ Error loading animal data:', error);
            document.getElementById('animal-summary').textContent = 
                'Error loading data. Please try refreshing the page.';
        });
}

/**
 * Populate detail page with animal data
 */
function populateDetailPage(animal) {
    // Basic Info
    document.getElementById('animal-name').textContent = animal.name;
    document.getElementById('animal-scientific').textContent = animal.scientific_name;
    document.getElementById('animal-image').src = animal.image ? animal.image.trim() : '';
    document.getElementById('animal-image').alt = animal.name;
    document.getElementById('animal-summary').textContent = animal.summary || animal.description || 'No description available.';
    
    // Conservation Badge
    const badgesContainer = document.getElementById('animal-badges');
    if (badgesContainer && animal.ecology?.conservation_status) {
        const statusClass = getConservationClass(animal.ecology.conservation_status);
        badgesContainer.innerHTML = `
            <span class="status-badge ${statusClass}">${animal.ecology.conservation_status}</span>
        `;
    }
    
    // Taxonomy Table
    const taxonomyTable = document.getElementById('taxonomy-table');
    if (taxonomyTable && animal.classification) {
        const order = ['kingdom', 'phylum', 'class', 'order', 'family', 'genus', 'species'];
        taxonomyTable.innerHTML = order.map(key => {
            if (animal.classification[key]) {
                return `
                    <tr>
                        <th>${capitalizeFirst(key)}</th>
                        <td>${animal.classification[key]}</td>
                    </tr>
                `;
            }
            return '';
        }).join('');
    }
    
    // Physical Stats
    const physicalList = document.getElementById('physical-list');
    if (physicalList) {
        const phys = animal.physical || {};
        physicalList.innerHTML = buildInfoList([
            ['Weight', phys.weight],
            ['Length', phys.length],
            ['Height', phys.height],
            ['Top Speed', phys.top_speed],
            ['Lifespan', phys.lifespan]
        ]);
        
        if (physicalList.innerHTML === '') {
            physicalList.innerHTML = '<li class="no-data">No physical data available</li>';
        }
    }
    
    // Ecology
    const ecologyList = document.getElementById('ecology-list');
    if (ecologyList) {
        const eco = animal.ecology || {};
        ecologyList.innerHTML = buildInfoList([
            ['Diet', eco.diet],
            ['Habitat', eco.habitat],
            ['Locations', eco.locations],
            ['Behavior', eco.group_behavior]
        ]);
        
        if (ecologyList.innerHTML === '') {
            ecologyList.innerHTML = '<li class="no-data">No ecology data available</li>';
        }
    }
    
    // Feature Tags
    const featureTags = document.getElementById('feature-tags');
    if (featureTags) {
        const eco = animal.ecology || {};
        if (eco.distinctive_features && eco.distinctive_features.length > 0) {
            featureTags.innerHTML = eco.distinctive_features
                .map(f => `<span class="feature-tag">${f}</span>`)
                .join('');
        } else {
            featureTags.innerHTML = '<span class="no-data">No distinctive features listed</span>';
        }
    }
    
    // Conservation Status Card
    const conservationStatus = document.getElementById('conservation-status');
    const threatsEl = document.getElementById('conservation-threats');
    if (conservationStatus && animal.ecology?.conservation_status) {
        const statusClass = getConservationClass(animal.ecology.conservation_status);
        conservationStatus.className = `conservation-status ${statusClass}`;
        const statusText = conservationStatus.querySelector('.status-text');
        if (statusText) {
            statusText.textContent = animal.ecology.conservation_status;
        }
    }
    if (threatsEl && animal.ecology?.biggest_threat) {
        threatsEl.textContent = animal.ecology.biggest_threat;
    }
    
    // Reproduction
    const reproList = document.getElementById('reproduction-list');
    if (reproList) {
        const repro = animal.reproduction || {};
        reproList.innerHTML = buildInfoList([
            ['Young Name', repro.name_of_young || animal.young_name],
            ['Group Name', animal.group_name],
            ['Gestation', repro.gestation_period],
            ['Litter Size', repro.average_litter_size]
        ]);
        
        if (reproList.innerHTML === '') {
            reproList.innerHTML = '<li class="no-data">No reproduction data available</li>';
        }
    }
    
    // Quick Facts
    const quickFactsList = document.getElementById('quick-facts-list');
    if (quickFactsList) {
        quickFactsList.innerHTML = buildInfoList([
            ['Animal Type', animal.animal_type],
            ['Diet', animal.ecology?.diet]
        ]);
        
        if (quickFactsList.innerHTML === '') {
            quickFactsList.innerHTML = '<li class="no-data">No quick facts available</li>';
        }
    }
    
    // Data Sources
    const sourcesEl = document.getElementById('data-sources');
    if (sourcesEl) {
        sourcesEl.textContent = animal.sources?.join(', ') || 'Wikipedia, iNaturalist';
    }
}

// ============================================
// Helper Functions
// ============================================

/**
 * Build HTML list from array of [label, value] pairs
 */
function buildInfoList(items) {
    return items
        .filter(([_, value]) => value && value !== 'null' && value !== 'undefined')
        .map(([label, value]) => `
            <li>
                <span class="label">${label}</span>
                <span class="value">${value}</span>
            </li>
        `)
        .join('');
}

/**
 * Get CSS class for conservation status
 */
function getConservationClass(status) {
    if (!status) return '';
    const s = status.toLowerCase();
    if (s.includes('critically')) return 'status-critical';
    if (s.includes('endangered')) return 'status-endangered';
    if (s.includes('vulnerable')) return 'status-vulnerable';
    if (s.includes('least') || s.includes('concern')) return 'status-least-concern';
    return 'status-vulnerable';
}

/**
 * Truncate text to specified length
 */
function truncateText(str, length) {
    if (!str) return '';
    if (str.length <= length) return str;
    return str.slice(0, length) + '...';
}

/**
 * Capitalize first letter of string
 */
function capitalizeFirst(str) {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1);
}

// ============================================
// Console Branding
// ============================================
console.log(`
╔═══════════════════════════════════════╗
║           🦁 WildAtlas 🌍             ║
║   Discover the Animal Kingdom         ║
║   Inspired by Facts.app               ║
╚═══════════════════════════════════════╝
`);
