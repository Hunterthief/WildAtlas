// Global state to hold animal data
let allAnimals = [];
let filteredAnimals = [];

// DOM Elements
const gridElement = document.getElementById('grid');
const searchInput = document.getElementById('search-input');
const backLink = document.getElementById('back-link');
const animalPage = document.getElementById('animal-page');
const homePage = document.getElementById('home-page');

// Initialize the app
document.addEventListener('DOMContentLoaded', () => {
    fetchAnimals();
    
    // Search Event Listener
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const term = e.target.value.toLowerCase().trim();
            filterAnimals(term);
        });
    }

    // Back Button Event Listener
    if (backLink) {
        backLink.addEventListener('click', (e) => {
            e.preventDefault();
            showHomePage();
        });
    }
});

/**
 * Fetch animals.json data
 */
async function fetchAnimals() {
    try {
        const response = await fetch('animals.json');
        if (!response.ok) throw new Error('Failed to load animal data');
        
        allAnimals = await response.json();
        filteredAnimals = [...allAnimals];
        
        renderGrid(filteredAnimals);
    } catch (error) {
        console.error('Error loading data:', error);
        gridElement.innerHTML = `
            <div class="no-results" style="grid-column: 1/-1;">
                <h2>Oops! Something went wrong.</h2>
                <p>We couldn't load the animal database. Please check your connection or file structure.</p>
            </div>
        `;
    }
}

/**
 * Render the grid of animal cards
 */
function renderGrid(animals) {
    gridElement.innerHTML = '';

    if (animals.length === 0) {
        gridElement.innerHTML = `
            <div class="no-results" style="grid-column: 1/-1;">
                <h2>No animals found</h2>
                <p>Try searching for something else like "Tiger", "Elephant", or "Shark".</p>
            </div>
        `;
        return;
    }

    animals.forEach(animal => {
        const card = document.createElement('div');
        card.className = 'card';
        card.onclick = () => showAnimalDetail(animal.id);

        // Determine conservation badge class
        const statusClass = getConservationClass(animal.ecology?.conservation_status);
        const statusLabel = animal.ecology?.conservation_status || 'Unknown';

        // Clean up image URL (remove trailing spaces from your JSON)
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
}

/**
 * Filter animals based on search term
 */
function filterAnimals(term) {
    if (!term) {
        filteredAnimals = [...allAnimals];
    } else {
        filteredAnimals = allAnimals.filter(animal => {
            const nameMatch = animal.name.toLowerCase().includes(term);
            const scientificMatch = animal.scientific_name.toLowerCase().includes(term);
            const typeMatch = animal.animal_type?.toLowerCase().includes(term);
            const habitatMatch = animal.ecology?.habitat?.toLowerCase().includes(term);
            
            return nameMatch || scientificMatch || typeMatch || habitatMatch;
        });
    }
    renderGrid(filteredAnimals);
}

/**
 * Show the detailed view for a specific animal
 */
function showAnimalDetail(id) {
    const animal = allAnimals.find(a => a.id === id);
    if (!animal) return;

    // Hide Home, Show Detail
    homePage.style.display = 'none';
    animalPage.style.display = 'block';
    window.scrollTo(0, 0);

    // Populate Data
    populateAnimalPage(animal);
}

/**
 * Return to the home grid
 */
function showHomePage() {
    animalPage.style.display = 'none';
    homePage.style.display = 'block';
    if(searchInput) searchInput.value = '';
    filterAnimals(''); // Reset filter
}

/**
 * Populate the detail page HTML
 */
function populateAnimalPage(animal) {
    const statusClass = getConservationClass(animal.ecology?.conservation_status);
    const statusLabel = animal.ecology?.conservation_status || 'Unknown';
    const imageUrl = animal.image ? animal.image.trim() : '';

    // Header
    document.querySelector('#animal-page h1').textContent = animal.name;
    document.querySelector('#animal-page .scientific-name').textContent = animal.scientific_name;
    document.querySelector('#animal-hero').src = imageUrl;
    document.querySelector('#animal-summary p').textContent = animal.summary;

    // Conservation Badge in Header (Optional, adds visual flair)
    const headerBadge = document.createElement('span');
    headerBadge.className = `conservation-badge ${statusClass}`;
    headerBadge.style.fontSize = '0.9rem';
    headerBadge.style.marginTop = '15px';
    headerBadge.style.display = 'inline-block';
    headerBadge.textContent = statusLabel;
    
    // Insert badge after scientific name
    const sciNameEl = document.querySelector('#animal-page .scientific-name');
    if(sciNameEl.nextSibling) {
        sciNameEl.parentNode.insertBefore(headerBadge, sciNameEl.nextSibling);
    } else {
        sciNameEl.parentNode.appendChild(headerBadge);
    }

    // Classification Table
    const classTableBody = document.querySelector('#classification-table tbody');
    classTableBody.innerHTML = '';
    if (animal.classification) {
        const order = ['kingdom', 'phylum', 'class', 'order', 'family', 'genus', 'species'];
        order.forEach(key => {
            if (animal.classification[key]) {
                const row = `
                    <tr>
                        <th>${capitalizeFirst(key)}</th>
                        <td>${animal.classification[key]}</td>
                    </tr>
                `;
                classTableBody.innerHTML += row;
            }
        });
    }

    // Physical Stats Card
    const physicalList = document.querySelector('#physical-stats ul');
    physicalList.innerHTML = '';
    const phys = animal.physical || {};
    addStatRow(physicalList, 'Weight', phys.weight);
    addStatRow(physicalList, 'Length', phys.length);
    addStatRow(physicalList, 'Height', phys.height);
    addStatRow(physicalList, 'Top Speed', phys.top_speed);
    addStatRow(physicalList, 'Lifespan', phys.lifespan);
    
    // If no physical stats, show placeholder
    if (physicalList.children.length === 0) {
        physicalList.innerHTML = '<li><span class="label">Data</span><span class="value">Not available</span></li>';
    }

    // Ecology Card
    const ecoList = document.querySelector('#ecology-stats ul');
    ecoList.innerHTML = '';
    const eco = animal.ecology || {};
    addStatRow(ecoList, 'Diet', eco.diet);
    addStatRow(ecoList, 'Habitat', eco.habitat);
    addStatRow(ecoList, 'Locations', eco.locations);
    addStatRow(ecoList, 'Behavior', eco.group_behavior);
    addStatRow(ecoList, 'Threats', eco.biggest_threat);

    // Distinctive Features (Tags)
    const featuresContainer = document.querySelector('#features-list');
    featuresContainer.innerHTML = '';
    if (eco.distinctive_features && eco.distinctive_features.length > 0) {
        eco.distinctive_features.forEach(feature => {
            const tag = document.createElement('span');
            tag.className = 'feature-tag';
            tag.textContent = feature;
            featuresContainer.appendChild(tag);
        });
    } else {
        featuresContainer.innerHTML = '<span style="color:#64748b">No distinctive features listed.</span>';
    }

    // Reproduction Card
    const reproList = document.querySelector('#reproduction-stats ul');
    reproList.innerHTML = '';
    const repro = animal.reproduction || {};
    addStatRow(reproList, 'Young Name', repro.name_of_young || animal.young_name);
    addStatRow(reproList, 'Group Name', animal.group_name);
    addStatRow(reproList, 'Gestation', repro.gestation_period);
    addStatRow(reproList, 'Litter Size', repro.average_litter_size);
}

/**
 * Helper: Add a row to a stats list if data exists
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
 * Helper: Get CSS class for conservation status
 */
function getConservationClass(status) {
    if (!status) return '';
    const s = status.toLowerCase().replace(/\s+/g, '-');
    // Map specific strings to our CSS classes
    if (s.includes('critically')) return 'critically-endangered';
    if (s.includes('endangered')) return 'endangered';
    if (s.includes('vulnerable')) return 'vulnerable';
    if (s.includes('least') || s.includes('concern')) return 'least-concern';
    return 'endangered'; // Default fallback
}

/**
 * Helper: Truncate text for cards
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
