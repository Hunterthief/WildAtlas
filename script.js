// Location coordinates for world map (percentage-based for responsive SVG)
const locationCoordinates = {
    'asia': { x: 75, y: 40 },
    'china': { x: 78, y: 42 },
    'india': { x: 72, y: 50 },
    'russia': { x: 75, y: 25 },
    'indonesia': { x: 80, y: 58 },
    'north america': { x: 25, y: 35 },
    'america': { x: 25, y: 35 },
    'united states': { x: 23, y: 38 },
    'usa': { x: 23, y: 38 },
    'canada': { x: 25, y: 25 },
    'alaska': { x: 15, y: 20 },
    'south america': { x: 30, y: 65 },
    'africa': { x: 55, y: 55 },
    'europe': { x: 55, y: 30 },
    'australia': { x: 85, y: 75 },
    'mexico': { x: 20, y: 45 },
    'japan': { x: 88, y: 38 },
    'korea': { x: 83, y: 40 },
    'pacific': { x: 45, y: 60 },
    'atlantic': { x: 40, y: 45 },
    'indian ocean': { x: 65, y: 60 },
    'arctic': { x: 50, y: 10 },
    'antarctica': { x: 50, y: 90 },
    'brazil': { x: 32, y: 68 },
    'argentina': { x: 30, y: 80 },
    'egypt': { x: 58, y: 45 },
    'south africa': { x: 58, y: 75 },
    'uk': { x: 50, y: 28 },
    'france': { x: 52, y: 32 },
    'germany': { x: 54, y: 30 },
    'italy': { x: 55, y: 35 },
    'spain': { x: 48, y: 38 },
    'scandinavia': { x: 55, y: 20 },
    'norway': { x: 54, y: 20 },
    'sweden': { x: 56, y: 22 },
    'finland': { x: 58, y: 20 },
    'poland': { x: 57, y: 30 },
    'turkey': { x: 60, y: 38 },
    'iran': { x: 65, y: 40 },
    'saudi arabia': { x: 62, y: 45 },
    'thailand': { x: 77, y: 50 },
    'vietnam': { x: 79, y: 48 },
    'philippines': { x: 83, y: 52 },
    'new zealand': { x: 90, y: 82 },
    'papua new guinea': { x: 87, y: 65 },
    'madagascar': { x: 65, y: 70 },
    'greenland': { x: 38, y: 15 },
    'iceland': { x: 45, y: 18 },
    'siberia': { x: 80, y: 25 },
    'mongolia': { x: 80, y: 35 },
    'tibet': { x: 75, y: 45 },
    'alps': { x: 53, y: 33 },
    'himalayas': { x: 73, y: 43 },
    'andes': { x: 25, y: 70 },
    'rockies': { x: 18, y: 35 },
    'appalachian': { x: 24, y: 38 }
};

let allAnimals = [];

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
            console.error('❌ Error loading animal data:', error);
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
    
    // Diet Icons - Updated to show multiple icons
const dietIcons = document.getElementById('diet-icons');
if (dietIcons && eco.diet) {
    const dietTypes = getDietTypes(eco.diet, animal.animal_type, animal.summary);
    dietIcons.innerHTML = dietTypes.map(type => `
        <div class="diet-icon ${type.class}" title="${type.title}">${type.icon}</div>
    `).join('');
}
    
    // Stats - Only show if data exists
    setStatContent('stat-length', 'stat-length-card', phys.length);
    setStatContent('stat-height', 'stat-height-card', phys.height);
    setStatContent('stat-weight', 'stat-weight-card', phys.weight);
    setStatContent('stat-speed', 'stat-speed-card', phys.top_speed);
    setStatContent('stat-lifespan', 'stat-lifespan-card', phys.lifespan);
    
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
        
        // Hide image wrapper if no image
        const imageWrapper = document.getElementById('hero-image-wrapper');
        if (imageWrapper && !animal.image) {
            imageWrapper.style.display = 'none';
        }
    }
    
    // === RIGHT SIDEBAR ===
    
    // Location with Map Dots
    const locationCard = document.getElementById('location-card');
    const locationText = document.getElementById('location-text');
    if (locationText && animal.ecology?.locations) {
        locationText.textContent = animal.ecology.locations;
        const mapImg = document.getElementById('world-map');
        if (mapImg && mapImg.complete) {
            addLocationDots(animal.ecology.locations);
        } else if (mapImg) {
            mapImg.addEventListener('load', () => {
                addLocationDots(animal.ecology.locations);
            });
        }
    } else if (locationCard) {
        locationCard.style.display = 'none';
    }
    
    // Conservation Status
    const conservationCard = document.getElementById('conservation-card');
    const conservationBox = document.getElementById('conservation-status-box');
    const conservationText = document.getElementById('conservation-status-text');
    if (conservationBox && animal.ecology?.conservation_status) {
        const statusClass = getConservationClass(animal.ecology.conservation_status);
        conservationBox.className = `conservation-status-box ${statusClass}`;
        if (conservationText) conservationText.textContent = animal.ecology.conservation_status;
    } else if (conservationCard) {
        conservationCard.style.display = 'none';
    }
    setStatContent('conservation-threats', null, animal.ecology?.biggest_threat);
    
    // Time Period
    const timeCard = document.getElementById('time-card');
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
    } else if (timeCard) {
        timeCard.style.display = 'none';
    }
    
    // Reproduction
    const reproCard = document.getElementById('reproduction-card');
    const hasReproData = repro.name_of_young || animal.young_name || animal.group_name || 
                         repro.gestation_period || repro.average_litter_size;
    
    if (hasReproData) {
        setStatContent('repro-young', null, repro.name_of_young || animal.young_name);
        setStatContent('repro-group', null, animal.group_name);
        setStatContent('repro-gestation', null, repro.gestation_period);
        setStatContent('repro-litter', null, repro.average_litter_size);
    } else if (reproCard) {
        reproCard.style.display = 'none';
    }
    
    // NEW: Common Names
    const commonNameCard = document.getElementById('common-name-card');
    const commonNamesText = document.getElementById('common-names-text');
    if (commonNamesText) {
        const commonNames = animal.common_names && animal.common_names.length > 0 
            ? animal.common_names.join(', ')
            : null;
        
        if (commonNames) {
            commonNamesText.textContent = commonNames;
        } else {
            commonNamesText.textContent = 'No alternative names';
            // Optionally hide card if no common names
            // commonNameCard.style.display = 'none';
        }
    }
    
    // === MAIN ARTICLE ===
    
    setStatContent('overview-text', null, animal.summary || animal.description || 'No description available.');
    
    const ecologyText = buildEcologyText(animal);
    setStatContent('ecology-text', null, ecologyText);
    
    // === FAQ ===
    document.querySelectorAll('.faq-animal-name').forEach(el => {
        el.textContent = animal.name.toLowerCase();
    });
    setStatContent('faq-diet', null, eco.diet || 'Unknown');
    setStatContent('faq-habitat', null, `${eco.habitat || 'Unknown'} - ${eco.locations || 'Unknown'}`);
    setStatContent('faq-conservation', null, animal.ecology?.conservation_status || 'Unknown');
    setStatContent('faq-features', null, eco.distinctive_features?.join(', ') || 'No data');
}

// ============================================
// NEW: Set Stat Content (Hide if empty)
// ============================================
function setStatContent(elementId, cardId, value) {
    const el = document.getElementById(elementId);
    const card = cardId ? document.getElementById(cardId) : null;
    
    if (el) {
        if (value && value !== '-' && value !== '' && value !== null) {
            el.textContent = value;
            if (card) card.style.display = 'flex';
        } else {
            el.textContent = '-';
            if (card) card.style.display = 'none';
        }
    }
}

// ============================================
// Location Map Functions
// ============================================
function addLocationDots(locationsString) {
    const dotsContainer = document.getElementById('location-dots');
    if (!dotsContainer || !locationsString) return;
    
    dotsContainer.innerHTML = '';
    
    const locations = locationsString.toLowerCase().split(',').map(l => l.trim());
    const addedDots = new Set();
    
    locations.forEach(location => {
        const coords = findLocationCoordinates(location);
        if (coords) {
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
    
    if (locationCoordinates[loc]) {
        return locationCoordinates[loc];
    }
    
    for (const key in locationCoordinates) {
        if (loc.includes(key) || key.includes(loc)) {
            return locationCoordinates[key];
        }
    }
    
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
    
    if (classType.includes('mammal') || animalType.includes('cat') || animalType.includes('feline') || 
        animalType.includes('dog') || animalType.includes('canine') || animalType.includes('elephant') ||
        animalType.includes('wolf') || animalType.includes('tiger')) {
        millionsYears = 200;
        text = `Evolved ~${millionsYears} million years ago`;
        width = '85%';
    }
    else if (classType.includes('aves') || animalType.includes('bird') || animalType.includes('eagle') || 
             animalType.includes('penguin') || animalType.includes('raptor')) {
        millionsYears = 150;
        text = `Evolved ~${millionsYears} million years ago`;
        width = '75%';
    }
    else if (classType.includes('reptil') || animalType.includes('snake') || animalType.includes('turtle') ||
             animalType.includes('cobra')) {
        millionsYears = 300;
        text = `Evolved ~${millionsYears} million years ago`;
        width = '90%';
    }
    else if (classType.includes('fish') || classType.includes('chondrichthyes') || classType.includes('actinopterygii') ||
             animalType.includes('shark') || animalType.includes('salmon')) {
        millionsYears = 500;
        text = `Evolved ~${millionsYears} million years ago`;
        width = '95%';
    }
    else if (classType.includes('amphib') || animalType.includes('frog')) {
        millionsYears = 370;
        text = `Evolved ~${millionsYears} million years ago`;
        width = '92%';
    }
    else if (classType.includes('insect') || animalType.includes('butterfly') || animalType.includes('bee')) {
        millionsYears = 400;
        text = `Evolved ~${millionsYears} million years ago`;
        width = '93%';
    }
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
// Diet Icons - Multiple Icons Per Animal
// ============================================
function getDietTypes(diet, animalType, summary) {
    if (!diet) return [{ class: 'unknown', icon: '❓' }];
    
    const dietLower = diet.toLowerCase();
    const summaryLower = (summary || '').toLowerCase();
    const typeLower = (animalType || '').toLowerCase();
    const types = [];
    
    // ========== CARNIVORE / MEAT ==========
    // Show for: Carnivore, OR if text mentions hunting/prey/meat
    if (dietLower.includes('carnivore') || 
        dietLower.includes('meat') ||
        summaryLower.includes('predator') ||
        summaryLower.includes('preys on') ||
        summaryLower.includes('hunts') ||
        ['feline', 'canine', 'bear', 'shark', 'raptor', 'snake', 'crocodile'].includes(typeLower)) {
        types.push({ class: 'carnivore', icon: '🥩', title: 'Meat' });
    }
    
    // ========== HERBIVORE / PLANTS ==========
    // Show for: Herbivore, OR if text mentions plants/grazing
    if (dietLower.includes('herbivore') || 
        dietLower.includes('plant') ||
        summaryLower.includes('grazes') ||
        summaryLower.includes('foliage') ||
        summaryLower.includes('vegetation') ||
        ['elephant', 'bovine', 'deer', 'rabbit', 'turtle'].includes(typeLower)) {
        types.push({ class: 'herbivore', icon: '🌿', title: 'Plants' });
    }
    
    // ========== PISCIVORE / FISH ==========
    // Show for: Piscivore, OR if text mentions fish, OR for fish-eating animals
    if (dietLower.includes('piscivore') || 
        dietLower.includes('fish') ||
        summaryLower.includes('fish') ||
        summaryLower.includes('salmon') ||
        summaryLower.includes('marine') ||
        ['shark', 'eagle', 'penguin', 'bear', 'seal', 'otter'].includes(typeLower)) {
        types.push({ class: 'piscivore', icon: '🐟', title: 'Fish' });
    }
    
    // ========== INSECTIVORE / INSECTS ==========
    // Show for: Insectivore, OR if text mentions insects, OR for insect-eating animals
    if (dietLower.includes('insectivore') || 
        summaryLower.includes('insects') ||
        summaryLower.includes('bugs') ||
        summaryLower.includes('arthropods') ||
        ['frog', 'bat', 'spider', 'lizard', 'bird'].includes(typeLower)) {
        types.push({ class: 'insectivore', icon: '🐛', title: 'Insects' });
    }
    
    // ========== OMNIVORE / MIXED ==========
    // Show for: Omnivore (in addition to other icons, not instead of)
    if (dietLower.includes('omnivore') || 
        summaryLower.includes('varied diet') ||
        summaryLower.includes('both plants and animals') ||
        ['bear', 'pig', 'raccoon', 'crow'].includes(typeLower)) {
        types.push({ class: 'omnivore', icon: '🍽️', title: 'Omnivore' });
    }
    
    // ========== NECTARIVORE / NECTAR ==========
    // Show for animals that eat nectar
    if (summaryLower.includes('nectar') ||
        summaryLower.includes('pollinator') ||
        ['butterfly', 'bee', 'hummingbird'].includes(typeLower)) {
        types.push({ class: 'nectarivore', icon: '🌸', title: 'Nectar' });
    }
    
    // ========== SCAVENGER ==========
    // Show for scavengers
    if (summaryLower.includes('scavenger') ||
        summaryLower.includes('carrion') ||
        ['vulture', 'hyena'].includes(typeLower)) {
        types.push({ class: 'scavenger', icon: '🦴', title: 'Scavenger' });
    }
    
    // ========== FALLBACK ==========
    if (types.length === 0) {
        // Default based on diet type
        if (dietLower.includes('carnivore')) {
            types.push({ class: 'carnivore', icon: '🥩', title: 'Carnivore' });
        } else if (dietLower.includes('herbivore')) {
            types.push({ class: 'herbivore', icon: '🌿', title: 'Herbivore' });
        } else {
            types.push({ class: 'omnivore', icon: '🍽️', title: 'Omnivore' });
        }
    }
    
    // Remove duplicates
    const unique = [];
    const seen = new Set();
    for (const t of types) {
        if (!seen.has(t.class)) {
            seen.add(t.class);
            unique.push(t);
        }
    }
    
    return unique;
}

console.log('🌍 WildAtlas - Discover the Animal Kingdom');
