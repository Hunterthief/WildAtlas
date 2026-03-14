// ============================================
// WildAtlas - Main JavaScript File
// Based on Facts.app Structure
// ============================================

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
            console.error('❌ Error loading animal ', error);
            document.getElementById('animal-summary').textContent = 'Error loading data.';
        });
}

function populateDetailPage(animal) {
    // Title Section
    document.getElementById('animal-name').textContent = animal.name;
    document.getElementById('animal-scientific').textContent = animal.scientific_name;
    
    // Badge
    const badgesContainer = document.getElementById('animal-badges');
    if (badgesContainer && animal.ecology?.conservation_status) {
        const statusClass = getConservationClass(animal.ecology.conservation_status);
        badgesContainer.innerHTML = `<span class="status-badge ${statusClass}">${animal.ecology.conservation_status}</span>`;
    }
    
    // Stats Bar
    const eco = animal.ecology || {};
    const phys = animal.physical || {};
    
    // Diet Icons
    const dietIcons = document.getElementById('diet-icons');
    if (dietIcons && eco.diet) {
        const dietTypes = getDietTypes(eco.diet);
        dietIcons.innerHTML = dietTypes.map(type => `
            <div class="diet-icon ${type.class}">${type.icon}</div>
        `).join('');
    }
    setTextContent('stat-diet', eco.diet);
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
    
    // Hero Image
    const heroImage = document.getElementById('animal-image');
    if (heroImage) {
        heroImage.src = animal.image ? animal.image.trim() : '';
        heroImage.alt = animal.name;
    }
    
    // Location & Conservation
    setTextContent('location-text', animal.ecology?.locations);
    setTextContent('conservation-text', animal.ecology?.conservation_status);
    
    // Overview (using summary)
    setTextContent('overview-text', animal.summary || animal.description || 'No description available.');
    
    // Physical Characteristics
    setTextContent('phys-weight', phys.weight);
    setTextContent('phys-length', phys.length);
    setTextContent('phys-height', phys.height);
    setTextContent('phys-speed', phys.top_speed);
    setTextContent('phys-lifespan', phys.lifespan);
    
    // Ecology
    setTextContent('eco-diet', eco.diet);
    setTextContent('eco-habitat', eco.habitat);
    setTextContent('eco-locations', eco.locations);
    setTextContent('eco-behavior', eco.group_behavior);
    
    // Features
    const featureTags = document.getElementById('feature-tags');
    if (featureTags && eco.distinctive_features?.length > 0) {
        featureTags.innerHTML = eco.distinctive_features.map(f => 
            `<span class="feature-tag">${f}</span>`
        ).join('');
    } else if (featureTags) {
        featureTags.innerHTML = '<span style="color:#888888">No data</span>';
    }
    
    // Reproduction
    const repro = animal.reproduction || {};
    setTextContent('repro-young', repro.name_of_young || animal.young_name);
    setTextContent('repro-group', animal.group_name);
    setTextContent('repro-gestation', repro.gestation_period);
    setTextContent('repro-litter', repro.average_litter_size);
    
    // FAQ
    document.querySelectorAll('.faq-animal-name').forEach(el => {
        el.textContent = animal.name.toLowerCase();
    });
    setTextContent('faq-diet', eco.diet || 'Unknown');
    setTextContent('faq-habitat', `${eco.habitat || 'Unknown'} - ${eco.locations || 'Unknown'}`);
    setTextContent('faq-conservation', animal.ecology?.conservation_status || 'Unknown');
    setTextContent('faq-features', eco.distinctive_features?.join(', ') || 'No data');
    setTextContent('faq-scientific', animal.scientific_name);
    setTextContent('faq-type', animal.animal_type || 'Unknown');
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

// ============================================
// Diet Icons (Facts.app Style)
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
