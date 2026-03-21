// ============================================
// Evolution/Time Period Extractor
// Parses Wikipedia Evolution/Phylogeny sections
// ============================================

/**
 * Extract evolutionary time period from Wikipedia article
 * Looks for species split times, common ancestor dates, fossil records
 */
async function extractEvolutionTime(animalName) {
    try {
        const wikiTitle = animalName.replace(' ', '_');
        const url = `https://en.wikipedia.org/wiki/${wikiTitle}`;
        
        const headers = {
            "User-Agent": "WildAtlas/1.0 (https://github.com/Hunterthief/WildAtlas)"
        };
        
        const response = await fetch(url, { headers, timeout: 10000 });
        
        if (!response.ok) {
            console.log(`⚠️  Could not fetch Wikipedia article for ${animalName}`);
            return null;
        }
        
        const html = await response.text();
        
        // Parse the HTML
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
        
        // Look for Evolution/Phylogeny/History sections
        const evolutionData = findEvolutionSection(doc, animalName);
        
        if (evolutionData) {
            console.log(`✅ Found evolution data for ${animalName}: ${evolutionData.text}`);
            return evolutionData;
        }
        
        console.log(`ℹ️  No evolution data found for ${animalName}`);
        return null;
        
    } catch (error) {
        console.error(`❌ Error extracting evolution time for ${animalName}:`, error);
        return null;
    }
}

/**
 * Find and parse Evolution/Phylogeny section from Wikipedia HTML
 */
function findEvolutionSection(doc, animalName) {
    // Section headers to look for
    const sectionHeaders = [
        'Evolution',
        'Phylogeny',
        'Evolutionary history',
        'Taxonomy',
        'Phylogeography',
        'Genetics',
        'Fossil record',
        'Origin'
    ];
    
    // Find all section headings (h2, h3)
    const headings = doc.querySelectorAll('h2, h3');
    
    for (const heading of headings) {
        const headingText = heading.textContent.trim().toLowerCase();
        
        // Check if this is an evolution-related section
        const isEvolutionSection = sectionHeaders.some(header => 
            headingText.includes(header.toLowerCase())
        );
        
        if (isEvolutionSection) {
            // Get the content after this heading
            const content = extractSectionContent(heading);
            
            if (content) {
                // Parse time periods from the content
                const timeData = parseTimePeriods(content, animalName);
                
                if (timeData) {
                    return timeData;
                }
            }
        }
    }
    
    // Also check infobox for time period data
    const infoboxTime = extractInfoboxTime(doc);
    if (infoboxTime) {
        return infoboxTime;
    }
    
    return null;
}

/**
 * Extract content following a section heading
 */
function extractSectionContent(heading) {
    let content = '';
    let current = heading.nextElementSibling;
    
    // Collect text until next heading
    while (current && !['H2', 'H3', 'H4'].includes(current.tagName)) {
        content += current.textContent + ' ';
        current = current.nextElementSibling;
    }
    
    return content;
}

/**
 * Parse time periods from text content
 */
function parseTimePeriods(text, animalName) {
    const textLower = text.toLowerCase();
    
    // Time period patterns to search for
    const patterns = [
        // "split from each other between 2.70 and 3.70 million years ago"
        {
            regex: /split\s+(?:from\s+)?(?:each\s+other\s+)?between\s+([\d.]+)\s+(?:and|to)\s+([\d.]+)\s+(?:million\s+years?\s+ago|mya)/i,
            type: 'split_range',
            priority: 1
        },
        // "diverged approximately 3.7 million years ago"
        {
            regex: /diverged\s+(?:approximately\s+)?([\d.]+)\s+(?:million\s+years?\s+ago|mya)/i,
            type: 'diverged',
            priority: 2
        },
        // "lineages split from each other between 2.70 and 3.70 million years ago"
        {
            regex: /lineages?\s+split\s+(?:from\s+)?(?:each\s+other\s+)?between\s+([\d.]+)\s+(?:and|to)\s+([\d.]+)\s+(?:million\s+years?\s+ago|mya)/i,
            type: 'lineage_split',
            priority: 1
        },
        // "common ancestor that lived between 108,000 and 72,000 years ago"
        {
            regex: /common\s+ancestor\s+(?:that\s+)?lived\s+between\s+([\d,]+)\s+(?:and|to)\s+([\d,]+)\s+years?\s+ago/i,
            type: 'ancestor_range',
            priority: 3
        },
        // "evolved approximately 2 million years ago"
        {
            regex: /evolved\s+(?:approximately\s+)?([\d.]+)\s+(?:million\s+years?\s+ago|mya)/i,
            type: 'evolved',
            priority: 2
        },
        // "species emerged around 3 million years ago"
        {
            regex: /(?:species|appeared|emerged)\s+(?:around|approximately)?\s*([\d.]+)\s+(?:million\s+years?\s+ago|mya)/i,
            type: 'emerged',
            priority: 2
        },
        // "dated to the early Pleistocene" / "late Pleistocene"
        {
            regex: /(?:dated\s+to|from)\s+(?:the\s+)?(early|middle|late)\s+(pleistocene|holocene|miocene|oligocene|eocene|paleocene|jurassic|cretaceous|triassic)/i,
            type: 'epoch',
            priority: 4
        },
        // "around 115,000 years ago"
        {
            regex: /(?:around|approximately|about)\s+([\d,]+)\s+years?\s+ago/i,
            type: 'years_ago',
            priority: 3
        },
        // "2.70-3.70 million years ago"
        {
            regex: /([\d.]+)\s*[-–]\s*([\d.]+)\s+(?:million\s+years?\s+ago|mya)/i,
            type: 'range_short',
            priority: 1
        },
        // "3.7 million years ago" (single value)
        {
            regex: /([\d.]+)\s+(?:million\s+years?\s+ago|mya)/i,
            type: 'single_million',
            priority: 2
        }
    ];
    
    // Epoch to millions of years mapping
    const epochMapping = {
        'early pleistocene': { min: 2.58, max: 1.8, display: '2.6-1.8' },
        'middle pleistocene': { min: 1.8, max: 0.78, display: '1.8-0.78' },
        'late pleistocene': { min: 0.78, max: 0.0117, display: '0.78-0.01' },
        'early holocene': { min: 0.0117, max: 0.0082, display: '0.01-0.008' },
        'middle holocene': { min: 0.0082, max: 0.0042, display: '0.008-0.004' },
        'late holocene': { min: 0.0042, max: 0, display: '0.004-Present' },
        'early miocene': { min: 23, max: 16, display: '23-16' },
        'middle miocene': { min: 16, max: 11.6, display: '16-11.6' },
        'late miocene': { min: 11.6, max: 5.3, display: '11.6-5.3' },
        'early oligocene': { min: 33.9, max: 28, display: '33.9-28' },
        'late oligocene': { min: 28, max: 23, display: '28-23' },
        'early eocene': { min: 56, max: 47.8, display: '56-47.8' },
        'late eocene': { min: 47.8, max: 33.9, display: '47.8-33.9' },
        'early paleocene': { min: 66, max: 61.6, display: '66-61.6' },
        'late paleocene': { min: 61.6, max: 56, display: '61.6-56' },
        'early jurassic': { min: 201, max: 174, display: '201-174' },
        'middle jurassic': { min: 174, max: 163, display: '174-163' },
        'late jurassic': { min: 163, max: 145, display: '163-145' },
        'early cretaceous': { min: 145, max: 100, display: '145-100' },
        'late cretaceous': { min: 100, max: 66, display: '100-66' },
        'early triassic': { min: 252, max: 247, display: '252-247' },
        'late triassic': { min: 247, max: 201, display: '247-201' }
    };
    
    let bestMatch = null;
    
    // Try each pattern
    for (const pattern of patterns) {
        const match = text.match(pattern.regex);
        
        if (match) {
            let millionsYears = 0;
            let textDisplay = '';
            let width = '50%';
            
            if (pattern.type === 'split_range' || pattern.type === 'lineage_split' || pattern.type === 'range_short') {
                // Range like "2.70 and 3.70 million years ago"
                const minVal = parseFloat(match[1].replace(/,/g, ''));
                const maxVal = parseFloat(match[2].replace(/,/g, ''));
                millionsYears = Math.max(minVal, maxVal); // Use older value
                textDisplay = `~${millionsYears} million years ago`;
                width = calculateTimelineWidth(millionsYears);
            }
            else if (pattern.type === 'ancestor_range' || pattern.type === 'years_ago') {
                // Years ago (not millions)
                const minVal = parseFloat(match[1].replace(/,/g, ''));
                const maxVal = parseFloat(match[2] ? match[2].replace(/,/g, '') : match[1]);
                millionsYears = Math.max(minVal, maxVal) / 1000000; // Convert to millions
                if (millionsYears < 0.1) {
                    textDisplay = `~${Math.max(minVal, maxVal).toLocaleString()} years ago`;
                    width = '10%'; // Recent species
                } else {
                    textDisplay = `~${millionsYears.toFixed(2)} million years ago`;
                    width = calculateTimelineWidth(millionsYears);
                }
            }
            else if (pattern.type === 'epoch') {
                // Geological epoch
                const epochKey = `${match[1].toLowerCase()} ${match[2].toLowerCase()}`;
                const epochData = epochMapping[epochKey];
                if (epochData) {
                    millionsYears = epochData.min;
                    textDisplay = `${match[1].capitalize()} ${match[2].capitalize()} (~${epochData.display} million years ago)`;
                    width = calculateTimelineWidth(millionsYears);
                }
            }
            else if (pattern.type === 'single_million' || pattern.type === 'diverged' || pattern.type === 'evolved' || pattern.type === 'emerged') {
                // Single value
                millionsYears = parseFloat(match[1].replace(/,/g, ''));
                textDisplay = `~${millionsYears} million years ago`;
                width = calculateTimelineWidth(millionsYears);
            }
            
            // Check if this is a better match (lower priority = better)
            if (!bestMatch || pattern.priority < bestMatch.priority) {
                bestMatch = {
                    millionsYears: millionsYears,
                    text: textDisplay,
                    width: width,
                    start: formatStartText(millionsYears),
                    end: 'Present',
                    confidence: pattern.priority,
                    rawMatch: match[0]
                };
            }
        }
    }
    
    return bestMatch;
}

/**
 * Extract time period from infobox
 */
function extractInfoboxTime(doc) {
    // Look for common infobox fields
    const infoboxFields = [
        'range',
        'temporal range',
        'period',
        'epoch',
        'appeared',
        'origin',
        'evolved'
    ];
    
    const infobox = doc.querySelector('.infobox');
    if (!infobox) return null;
    
    const rows = infobox.querySelectorAll('tr');
    
    for (const row of rows) {
        const label = row.querySelector('th');
        const value = row.querySelector('td');
        
        if (label && value) {
            const labelText = label.textContent.toLowerCase();
            
            if (infoboxFields.some(field => labelText.includes(field))) {
                const valueText = value.textContent;
                
                // Parse the value for time periods
                const timeMatch = valueText.match(/([\d.]+)\s*(?:million\s+)?years?\s+ago/i);
                if (timeMatch) {
                    const millionsYears = parseFloat(timeMatch[1]);
                    return {
                        millionsYears: millionsYears,
                        text: `~${millionsYears} million years ago`,
                        width: calculateTimelineWidth(millionsYears),
                        start: formatStartText(millionsYears),
                        end: 'Present',
                        confidence: 5,
                        source: 'infobox'
                    };
                }
            }
        }
    }
    
    return null;
}

/**
 * Calculate timeline width percentage based on millions of years
 */
function calculateTimelineWidth(millionsYears) {
    // Scale: 0-1 million = 10%, 500+ million = 95%
    if (millionsYears <= 0.1) return '10%';
    if (millionsYears <= 1) return '20%';
    if (millionsYears <= 5) return '40%';
    if (millionsYears <= 10) return '55%';
    if (millionsYears <= 50) return '70%';
    if (millionsYears <= 100) return '80%';
    if (millionsYears <= 200) return '85%';
    if (millionsYears <= 300) return '90%';
    if (millionsYears <= 400) return '92%';
    if (millionsYears <= 500) return '94%';
    return '95%';
}

/**
 * Format start text for timeline
 */
function formatStartText(millionsYears) {
    if (millionsYears < 0.001) {
        return `${(millionsYears * 1000).toFixed(1)}K years ago`;
    } else if (millionsYears < 1) {
        return `${(millionsYears * 1000).toFixed(0)}K years ago`;
    } else if (millionsYears < 10) {
        return `${millionsYears.toFixed(1)}M years ago`;
    } else {
        return `${millionsYears.toFixed(0)}M years ago`;
    }
}

/**
 * Get time period with Wikipedia extraction (fallback to class-based)
 */
async function getTimePeriodWithExtraction(animal) {
    // Try to extract from Wikipedia first
    const evolutionData = await extractEvolutionTime(animal.name);
    
    if (evolutionData) {
        return evolutionData;
    }
    
    // Fallback to class-based estimation
    return getTimePeriodFallback(animal);
}

/**
 * Fallback time period estimation (original logic)
 */
function getTimePeriodFallback(animal) {
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

// String helper
String.prototype.capitalize = function() {
    return this.charAt(0).toUpperCase() + this.slice(1);
};
