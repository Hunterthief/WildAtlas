// ============================================
// WildAtlas - Main JavaScript File
// Streamlined Facts.app Design
// External World Map SVG
// ============================================

let allAnimals = [];

// Location coordinates for world map (percentage-based for responsive SVG)
// Values are percentages (0-100) of map width/height
const locationCoordinates = {
    'asia': { x: 72, y: 35 },
    'china': { x: 75, y: 38 },
    'india': { x: 68, y: 45 },
    'russia': { x: 70, y: 25 },
    'indonesia': { x: 78, y: 55 },
    'north america': { x: 22, y: 32 },
    'america': { x: 22, y: 32 },
    'united states': { x: 20, y: 35 },
    'usa': { x: 20, y: 35 },
    'canada': { x: 22, y: 25 },
    'alaska': { x: 12, y: 22 },
    'south america': { x: 25, y: 65 },
    'africa': { x: 52, y: 55 },
    'europe': { x: 52, y: 30 },
    'australia': { x: 82, y: 75 },
    'mexico': { x: 18, y: 42 },
    'japan': { x: 85, y: 35 },
    'korea': { x: 80, y: 36 },
    'pacific': { x: 40, y: 60 },
    'atlantic': { x: 35, y: 45 },
    'indian ocean': { x: 62, y: 60 },
    'arctic': { x: 50, y: 10 },
    'antarctica': { x: 50, y: 90 },
    'texas': { x: 18, y: 38 },
    'oklahoma': { x: 19, y: 37 },
    'florida': { x: 23, y: 42 },
    'california': { x: 15, y: 38 },
    'brazil': { x: 28, y: 68 },
    'argentina': { x: 25, y: 80 },
    'egypt': { x: 55, y: 42 },
    'south africa': { x: 55, y: 75 },
    'uk': { x: 48, y: 28 },
    'france': { x: 49, y: 32 },
    'germany': { x: 51, y: 30 },
    'italy': { x: 52, y: 34 },
    'spain': { x: 47, y: 36 },
    'scandinavia': { x: 52, y: 22 },
    'norway': { x: 51, y: 22 },
    'sweden': { x: 53, y: 24 },
    'finland': { x: 55, y: 22 },
    'poland': { x: 54, y: 30 },
    'turkey': { x: 58, y: 36 },
    'iran': { x: 62, y: 38 },
    'saudi arabia': { x: 60, y: 42 },
    'thailand': { x: 74, y: 48 },
    'vietnam': { x: 76, y: 45 },
    'philippines': { x: 80, y: 50 },
    'new zealand': { x: 88, y: 82 },
    'papua new guinea': { x: 85, y: 65 },
    'madagascar': { x: 62, y: 70 },
    'greenland': { x: 35, y: 18 },
    'iceland': { x: 42, y: 22 }
};

document.addEventListener('DOMContentLoaded', () => {
    console.log('🦁 WildAtlas initializing...');
    
    const isHomePage = document.getElementById('grid') !== null;
    const isDetailPage = document.getElementById('animal-name') !== null;
    
    if (isHomePage) {
        initHomePage();
    } else if (isDetailPage) {
        initDetailPage();
    }
});

// ============================================
// Home Page Functions
// ============================================
function initHomePage() {
    const grid = document.getElementById('grid');
    const searchInput = document.getElementById('search-input');
    
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
                    <div class="error-message" style="grid-column: 1/-1;">
                        <h2>⚠️ Unable to Load Data</h2>
                        <p>${error.message}</p>
                    </div>
                `;
            }
        });
    
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            filterAnimals(e.target.value.toLowerCase().trim());
        });
    }
}

async function fetchAnimals() {
    const response = await fetch('data/animals.json?t=' + Date.now());
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: Failed to load animals.json`);
    }
    return await response.json();
}

function renderGrid(animals) {
    const grid = document.getElementById('grid');
    if (!grid) return;
    
    grid.innerHTML = '';
    
    if (animals.length === 0) {
        grid.innerHTML = `
            <div class="no-results" style="grid-column: 1/-1;">
                <h2>No animals found</h2>
                <p>Try searching for something else.</p>
            </div>
        `;
        return;
    }
    
    animals.forEach(animal => {
        const card = document.createElement('div');
        card.className = 'card';
        
        const statusClass = getConservationClass(animal.ecology?.conservation_status);
        const statusLabel = animal.ecology?.conservation_status || '';
        const imageUrl = animal.image ? animal.image.trim() : 'https://via.placeholder.com/330x240?text=No+Image';
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
// Detail Page Functions
// ============================================
function initDetailPage() {
    const params = new URLSearchParams(window.location.search);
    const animalName = params.get('name');
    
    if (!animalName) {
        window.location.href = 'index.html';
        return;
    }
    
    fetchAnimals()
        .then(animals => {
            const animal = animals.find(a => 
                a.name.toLowerCase() === decodeURIComponent(animalName).toLowerCase()
            );
            
            if (!animal) {
                document.getElementById('animal-name').textContent = 'Animal Not Found';
                return;
            }
            
            populateDetailPage(animal);
        })
        .catch(error => {
            console.error('❌ Error loading animal ', error);
            document.getElementById('overview-text').textContent = 'Error loading data.';
        });
}

function populateDetailPage(animal) {
    const eco = animal.ecology || {};
    const phys = animal.physical || {};
    const repro = animal.reproduction || {};
    
    // === TITLE SECTION ===
    document.getElementById('animal-name').textContent = animal.name;
    document.getElementById('animal-scientific').textContent = animal.scientific_name;
    
    // === LEFT SIDEBAR ===
    
    // Diet Icons
    const dietIcons = document.getElementById('diet-icons');
    if (dietIcons && eco.diet) {
        const dietTypes = getDietTypes(eco.diet);
        dietIcons.innerHTML = dietTypes.map(type => `
            <div class="diet-icon ${type.class}">${type.icon}</div>
        `).join('');
    }
    
    // Stats
    setTextContent('stat-length', phys.length);
    setTextContent('stat-height', phys.height);
    setTextContent('stat-weight', phys.weight);
    
    // Classification Table
    const classTable = document.getElementById('classification-table');
    if (classTable && animal.classification) {
        const order = ['kingdom', 'phylum', 'class', 'order', 'family', 'genus', 'species'];
        classTable.innerHTML = order.map(key => {
            if (animal.classification[key]) {
                return `<tr><th>${capitalizeFirst(key)}</th><td>${animal.classification[key]}</td></tr>`;
            }
            return '';
        }).join('');
    }
    
    // === CENTER COLUMN ===
    
    // Hero Image
    const heroImage = document.getElementById('animal-image');
    if (heroImage) {
        heroImage.src = animal.image ? animal.image.trim() : '';
        heroImage.alt = animal.name;
    }
    
    // === RIGHT SIDEBAR ===
    
    // Location with Map Dots
    const locationText = document.getElementById('location-text');
    if (locationText && animal.ecology?.locations) {
        locationText.textContent = animal.ecology.locations;
        addLocationDots(animal.ecology.locations);
    }
    
    // Conservation Status
    const conservationBox = document.getElementById('conservation-status-box');
    const conservationText = document.getElementById('conservation-status-text');
    if (conservationBox && animal.ecology?.conservation_status) {
        const statusClass = getConservationClass(animal.ecology.conservation_status);
        conservationBox.className = `conservation-status-box ${statusClass}`;
        if (conservationText) conservationText.textContent = animal.ecology.conservation_status;
    }
    setTextContent('conservation-threats', animal.ecology?.biggest_threat);
    
    // Time Period
    const timeRange = document.getElementById('time-range');
    const timelineFill = document.getElementById('timeline-fill');
    const timelineStart = document.getElementById('timeline-start');
    const timelineEnd = document.getElementById('timeline-end');
    
    if (timeRange) {
        const timeData = getTimePeriod(animal);
        timeRange.textContent = timeData.text;
        if (timelineFill) timelineFill.style.width = timeData.width;
        if (timelineStart) timelineStart.textContent = timeData.start;
        if (timelineEnd) timelineEnd.textContent = 'Present';
    }
    
    // Reproduction
    setTextContent('repro-young', repro.name_of_young || animal.young_name);
    setTextContent('repro-group', animal.group_name);
    setTextContent('repro-gestation', repro.gestation_period);
    setTextContent('repro-litter', repro.average_litter_size);
    
    // === MAIN ARTICLE ===
    
    setTextContent('overview-text', animal.summary || animal.description || 'No description available.');
    
    const ecologyText = buildEcologyText(animal);
    setTextContent('ecology-text', ecologyText);
    
    // === FAQ ===
    document.querySelectorAll('.faq-animal-name').forEach(el => {
        el.textContent = animal.name.toLowerCase();
    });
    setTextContent('faq-diet', eco.diet || 'Unknown');
    setTextContent('faq-habitat', `${eco.habitat || 'Unknown'} - ${eco.locations || 'Unknown'}`);
    setTextContent('faq-conservation', animal.ecology?.conservation_status || 'Unknown');
    setTextContent('faq-features', eco.distinctive_features?.join(', ') || 'No data');
}

// ============================================
// Location Map Functions (External SVG)
// ============================================
function addLocationDots(locationsString) {
    const dotsContainer = document.getElementById('location-dots');
    if (!dotsContainer || !locationsString) return;
    
    dotsContainer.innerHTML = '';
    
    const locations = locationsString.toLowerCase().split(',').map(l => l.trim());
    const addedDots = new Set(); // Prevent duplicate dots
    
    locations.forEach(location => {
        const coords = findLocationCoordinates(location);
        if (coords) {
            // Create unique key to prevent duplicates
            const dotKey = `${coords.x}-${coords.y}`;
            
            if (!addedDots.has(dotKey)) {
                addedDots.add(dotKey);
                
                const dot = document.createElement('div');
                dot.className = 'location-dot';
                dot.style.left = coords.x + '%';
                dot.style.top = coords.y + '%';
                dot.setAttribute('data-label', location);
                dot.setAttribute('title', location);
                
                dotsContainer.appendChild(dot);
            }
        }
    });
}

function findLocationCoordinates(location) {
    const loc = location.toLowerCase().trim();
    
    // Direct match
    if (locationCoordinates[loc]) {
        return locationCoordinates[loc];
    }
    
    // Partial match
    for (const key in locationCoordinates) {
        if (loc.includes(key) || key.includes(loc)) {
            return locationCoordinates[key];
        }
    }
    
    // Region matching
    if (loc.includes('asia') || loc.includes('east')) return locationCoordinates['asia'];
    if (loc.includes('america') || loc.includes('usa') || loc.includes('us') || loc.includes('united states')) {
        return locationCoordinates['north america'];
    }
    if (loc.includes('europe')) return locationCoordinates['europe'];
    if (loc.includes('africa')) return locationCoordinates['africa'];
    if (loc.includes('australia') || loc.includes('oceania')) return locationCoordinates['australia'];
    if (loc.includes('south') && !loc.includes('korea')) return locationCoordinates['south america'];
    if (loc.includes('india')) return locationCoordinates['india'];
    if (loc.includes('china')) return locationCoordinates['china'];
    if (loc.includes('russia')) return locationCoordinates['russia'];
    if (loc.includes('indonesia')) return locationCoordinates['indonesia'];
    
    return null;
}

// ============================================
// Time Period Functions
// ============================================
function getTimePeriod(animal) {
    const animalType = animal.animal_type?.toLowerCase() || '';
    const classType = animal.classification?.class?.toLowerCase() || '';
    
    let millionsYears = 0;
    let text = '';
    let width = '50%';
    
    // Mammals ~200 million years ago
    if (classType.includes('mammal') || animalType.includes('cat') || animalType.includes('feline') || 
        animalType.includes('dog') || animalType.includes('canine') || animalType.includes('elephant') ||
        animalType.includes('wolf') || animalType.includes('tiger')) {
        millionsYears = 200;
        text = `Evolved ~${millionsYears} million years ago`;
        width = '85%';
    }
    // Birds ~150 million years ago
    else if (classType.includes('aves') || animalType.includes('bird') || animalType.includes('eagle') || 
             animalType.includes('penguin') || animalType.includes('raptor')) {
        millionsYears = 150;
        text = `Evolved ~${millionsYears} million years ago`;
        width = '75%';
    }
    // Reptiles ~300 million years ago
    else if (classType.includes('reptil') || animalType.includes('snake') || animalType.includes('turtle') ||
             animalType.includes('cobra')) {
        millionsYears = 300;
        text = `Evolved ~${millionsYears} million years ago`;
        width = '90%';
    }
    // Fish ~500 million years ago
    else if (classType.includes('fish') || classType.includes('chondrichthyes') || classType.includes('actinopterygii') ||
             animalType.includes('shark') || animalType.includes('salmon')) {
        millionsYears = 500;
        text = `Evolved ~${millionsYears} million years ago`;
        width = '95%';
    }
    // Amphibians ~370 million years ago
    else if (classType.includes('amphib') || animalType.includes('frog')) {
        millionsYears = 370;
        text = `Evolved ~${millionsYears} million years ago`;
        width = '92%';
    }
    // Insects ~400 million years ago
    else if (classType.includes('insect') || animalType.includes('butterfly') || animalType.includes('bee')) {
        millionsYears = 400;
        text = `Evolved ~${millionsYears} million years ago`;
        width = '93%';
    }
    // Default
    else {
        millionsYears = 100;
        text = `Evolved ~${millionsYears} million years ago`;
        width = '60%';
    }
    
    return {
        text: text,
        width: width,
        start: `${millionsYears}M years ago`,
        end: 'Present'
    };
}

// ============================================
// Helper Functions
// ============================================
function setTextContent(id, text) {
    const el = document.getElementById(id);
    if (el) {
        el.textContent = text || '-';
    }
}

function getConservationClass(status) {
    if (!status) return '';
    const s = status.toLowerCase();
    if (s.includes('critically')) return 'status-critical';
    if (s.includes('endangered')) return 'status-endangered';
    if (s.includes('vulnerable')) return 'status-vulnerable';
    if (s.includes('least') || s.includes('concern')) return 'status-least-concern';
    return 'status-vulnerable';
}

function truncateText(str, length) {
    if (!str) return '';
    if (str.length <= length) return str;
    return str.slice(0, length) + '...';
}

function capitalizeFirst(str) {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1);
}

function buildEcologyText(animal) {
    const eco = animal.ecology || {};
    const parts = [];
    
    if (eco.diet) {
        parts.push(`This animal is a ${eco.diet.toLowerCase()}.`);
    }
    if (eco.biggest_threat) {
        parts.push(`The biggest threats include ${eco.biggest_threat.toLowerCase()}.`);
    }
    
    return parts.length > 0 ? parts.join(' ') : 'No additional ecology information available.';
}

// ============================================
// Diet Icons
// ============================================
function getDietTypes(diet) {
    if (!diet) return [{ class: 'omnivore', icon: '🍽️' }];
    
    const dietLower = diet.toLowerCase();
    const types = [];
    
    if (dietLower.includes('carnivore') || dietLower.includes('meat')) {
        types.push({ class: 'carnivore', icon: '🥩' });
    }
    if (dietLower.includes('herbivore') || dietLower.includes('plant')) {
        types.push({ class: 'herbivore', icon: '🌿' });
    }
    if (dietLower.includes('omnivore')) {
        types.push({ class: 'omnivore', icon: '🍽️' });
    }
    if (dietLower.includes('insect')) {
        types.push({ class: 'insectivore', icon: '🐛' });
    }
    if (dietLower.includes('fish')) {
        types.push({ class: 'piscivore', icon: '🐟' });
    }
    
    if (types.length === 0) {
        if (dietLower.includes('carnivore')) {
            types.push({ class: 'carnivore', icon: '🥩' });
        } else if (dietLower.includes('herbivore')) {
            types.push({ class: 'herbivore', icon: '🌿' });
        } else {
            types.push({ class: 'omnivore', icon: '🍽️' });
        }
    }
    
    return types;
}

console.log('🌍 WildAtlas - Discover the Animal Kingdom');
