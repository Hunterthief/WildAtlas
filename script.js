// Global state
let allAnimals = [];
let filteredAnimals = [];

// DOM Elements - Wait for DOM to be ready
let gridElement, searchInput, backLink, animalPage, homePage;

document.addEventListener('DOMContentLoaded', () => {
    console.log('🔍 WildAtlas initializing...');
    
    // Get DOM elements
    gridElement = document.getElementById('grid');
    searchInput = document.getElementById('search-input');
    backLink = document.getElementById('back-link');
    animalPage = document.getElementById('animal-page');
    homePage = document.getElementById('home-page');
    
    // Debug: Check if elements exist
    console.log('Grid element:', gridElement);
    console.log('Home page:', homePage);
    console.log('Animal page:', animalPage);
    
    if (!gridElement) {
        console.error('❌ ERROR: Grid element not found!');
        return;
    }
    
    // Initialize
    fetchAnimals();
    
    // Search listener
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const term = e.target.value.toLowerCase().trim();
            filterAnimals(term);
        });
    }
    
    // Back button listener
    if (backLink) {
        backLink.addEventListener('click', (e) => {
            e.preventDefault();
            showHomePage();
        });
    }
});

/**
 * Fetch animals.json
 */
async function fetchAnimals() {
    console.log('📡 Fetching animals.json...');
    
    try {
        const response = await fetch('animals.json');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        allAnimals = await response.json();
        console.log(`✅ Loaded ${allAnimals.length} animals`);
        
        filteredAnimals = [...allAnimals];
        renderGrid(filteredAnimals);
        
    } catch (error) {
        console.error('❌ Error loading animals:', error);
        
        if (gridElement) {
            gridElement.innerHTML = `
                <div class="no-results" style="grid-column: 1/-1;">
                    <h2>⚠️ Unable to Load Data</h2>
                    <p>Make sure you're running this on a local server (not file://)</p>
                    <p style="margin-top: 10px; color: #f87171;">Error: ${error.message}</p>
                    <p style="margin-top: 20px; font-size: 0.9rem;">
                        <strong>Quick Fix:</strong> Use VS Code Live Server extension or run:<br>
                        <code>python -m http.server 8000</code>
                    </p>
                </div>
            `;
        }
    }
}

/**
 * Render grid of animal cards
 */
function renderGrid(animals) {
    console.log('🎨 Rendering grid with', animals.length, 'animals');
    
    if (!gridElement) {
        console.error('Grid element is null!');
        return;
    }
    
    gridElement.innerHTML = '';
    
    if (animals.length === 0) {
        gridElement.innerHTML = `
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
        card.onclick = () => showAnimalDetail(animal.id);
        
        const statusClass = getConservationClass(animal.ecology?.conservation_status);
        const statusLabel = animal.ecology?.conservation_status || 'Unknown';
        const imageUrl = animal.image ? animal.image.trim() : 'https://via.placeholder.com/330x200?text=No+Image';
        
        card.innerHTML = `
            <img src="${imageUrl}" alt="${animal.name}" loading="lazy">
            <div class="card-content">
                <h3>${animal.name}</h3>
                <p class="scientific-name">${animal.scientific_name}</p>
                <p>${truncateText(animal.summary, 80)}</p>
                <span class="conservation-badge ${statusClass}">${statusLabel}</span>
            </div>
        `;
        
        gridElement.appendChild(card);
    });
    
    console.log('✅ Grid rendered successfully');
}

/**
 * Filter animals by search term
 */
function filterAnimals(term) {
    if (!term) {
        filteredAnimals = [...allAnimals];
    } else {
        filteredAnimals = allAnimals.filter(animal => {
            const nameMatch = animal.name?.toLowerCase().includes(term);
            const scientificMatch = animal.scientific_name?.toLowerCase().includes(term);
            const typeMatch = animal.animal_type?.toLowerCase().includes(term);
            const habitatMatch = animal.ecology?.habitat?.toLowerCase().includes(term);
            
            return nameMatch || scientificMatch || typeMatch || habitatMatch;
        });
    }
    renderGrid(filteredAnimals);
}

/**
 * Show animal detail page
 */
function showAnimalDetail(id) {
    console.log('📄 Showing detail for animal ID:', id);
    
    const animal = allAnimals.find(a => a.id === id);
    if (!animal) {
        console.error('Animal not found:', id);
        return;
    }
    
    if (homePage) homePage.style.display = 'none';
    if (animalPage) animalPage.style.display = 'block';
    
    window.scrollTo(0, 0);
    populateAnimalPage(animal);
}

/**
 * Show home page
 */
function showHomePage() {
    if (animalPage) animalPage.style.display = 'none';
    if (homePage) homePage.style.display = 'block';
    if (searchInput) searchInput.value = '';
    filterAnimals('');
}

/**
 * Populate detail page with animal data
 */
function populateAnimalPage(animal) {
    const statusClass = getConservationClass(animal.ecology?.conservation_status);
    const statusLabel = animal.ecology?.conservation_status || 'Unknown';
    const imageUrl = animal.image ? animal.image.trim() : '';
    
    // Header
    const titleEl = document.getElementById('detail-title');
    const sciEl = document.getElementById('detail-scientific');
    const heroEl = document.getElementById('animal-hero');
    const summaryEl = document.getElementById('animal-summary');
    
    if (titleEl) titleEl.textContent = animal.name;
    if (sciEl) sciEl.textContent = animal.scientific_name;
    if (heroEl) heroEl.src = imageUrl;
    if (summaryEl) {
        summaryEl.querySelector('p').textContent = animal.summary;
    }
    
    // Add conservation badge to header
    const existingBadge = document.querySelector('.animal-header .conservation-badge');
    if (existingBadge) existingBadge.remove();
    
    const headerBadge = document.createElement('span');
    headerBadge.className = `conservation-badge ${statusClass}`;
    headerBadge.style.fontSize = '0.9rem';
    headerBadge.style.marginTop = '15px';
    headerBadge.style.display = 'inline-block';
    headerBadge.textContent = statusLabel;
    
    if (sciEl) {
        sciEl.parentNode.insertBefore(headerBadge, sciEl.nextSibling);
    }
    
    // Classification Table
    const classTableBody = document.querySelector('#classification-table tbody');
    if (classTableBody) {
        classTableBody.innerHTML = '';
        if (animal.classification) {
            const order = ['kingdom', 'phylum', 'class', 'order', 'family', 'genus', 'species'];
            order.forEach(key => {
                if (animal.classification[key]) {
                    classTableBody.innerHTML += `
                        <tr>
                            <th>${capitalizeFirst(key)}</th>
                            <td>${animal.classification[key]}</td>
                        </tr>
                    `;
                }
            });
        }
    }
    
    // Physical Stats
    const physicalList = document.querySelector('#physical-stats ul');
    if (physicalList) {
        physicalList.innerHTML = '';
        const phys = animal.physical || {};
        addStatRow(physicalList, 'Weight', phys.weight);
        addStatRow(physicalList, 'Length', phys.length);
        addStatRow(physicalList, 'Height', phys.height);
        addStatRow(physicalList, 'Top Speed', phys.top_speed);
        addStatRow(physicalList, 'Lifespan', phys.lifespan);
        
        if (physicalList.children.length === 0) {
            physicalList.innerHTML = '<li><span class="label">Data</span><span class="value">Not available</span></li>';
        }
    }
    
    // Ecology Stats
    const ecoList = document.querySelector('#ecology-stats ul');
    if (ecoList) {
        ecoList.innerHTML = '';
        const eco = animal.ecology || {};
        addStatRow(ecoList, 'Diet', eco.diet);
        addStatRow(ecoList, 'Habitat', eco.habitat);
        addStatRow(ecoList, 'Locations', eco.locations);
        addStatRow(ecoList, 'Behavior', eco.group_behavior);
        addStatRow(ecoList, 'Threats', eco.biggest_threat);
    }
    
    // Features
    const featuresContainer = document.getElementById('features-list');
    if (featuresContainer) {
        featuresContainer.innerHTML = '';
        if (animal.ecology?.distinctive_features?.length > 0) {
            animal.ecology.distinctive_features.forEach(feature => {
                const tag = document.createElement('span');
                tag.className = 'feature-tag';
                tag.textContent = feature;
                featuresContainer.appendChild(tag);
            });
        } else {
            featuresContainer.innerHTML = '<span style="color:#64748b">No distinctive features listed.</span>';
        }
    }
    
    // Reproduction
    const reproList = document.querySelector('#reproduction-stats ul');
    if (reproList) {
        reproList.innerHTML = '';
        const repro = animal.reproduction || {};
        addStatRow(reproList, 'Young Name', repro.name_of_young || animal.young_name);
        addStatRow(reproList, 'Group Name', animal.group_name);
        addStatRow(reproList, 'Gestation', repro.gestation_period);
        addStatRow(reproList, 'Litter Size', repro.average_litter_size);
    }
    
    // Sources
    const sourcesEl = document.getElementById('data-sources');
    if (sourcesEl && animal.sources) {
        sourcesEl.textContent = animal.sources.join(', ');
    }
}

/**
 * Helper: Add stat row
 */
function addStatRow(container, label, value) {
    if (!value) return;
    const li = document.createElement('li');
    li.innerHTML = `
        <span class="label">${label}</span>
        <span class="value">${value}</span>
    `;
    container.appendChild(li);
}

/**
 * Helper: Get conservation class
 */
function getConservationClass(status) {
    if (!status) return '';
    const s = status.toLowerCase().replace(/\s+/g, '-');
    if (s.includes('critically')) return 'critically-endangered';
    if (s.includes('endangered')) return 'endangered';
    if (s.includes('vulnerable')) return 'vulnerable';
    if (s.includes('least') || s.includes('concern')) return 'least-concern';
    return 'endangered';
}

/**
 * Helper: Truncate text
 */
function truncateText(str, length) {
    if (!str) return '';
    if (str.length <= length) return str;
    return str.slice(0, length) + '...';
}

/**
 * Helper: Capitalize first letter
 */
function capitalizeFirst(str) {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1);
}
