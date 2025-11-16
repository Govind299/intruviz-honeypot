// Leaflet Dark Map Configuration for Intruviz Honeypot
// Add this to your dashboard JavaScript file

// ============================================
// Dark Map Tile Providers
// ============================================

const darkMapProviders = {
    // Option 1: Carto Dark (Recommended)
    cartoDark: {
        url: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        subdomains: 'abcd',
        maxZoom: 19
    },

    // Option 2: Carto Dark (No Labels)
    cartoDarkNoLabels: {
        url: 'https://{s}.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}{r}.png',
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        subdomains: 'abcd',
        maxZoom: 19
    },

    // Option 3: Stamen Toner Dark
    stamenToner: {
        url: 'https://stamen-tiles-{s}.a.ssl.fastly.net/toner/{z}/{x}/{y}{r}.png',
        attribution: 'Map tiles by <a href="http://stamen.com">Stamen Design</a>, <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a> &mdash; Map data &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        subdomains: 'abcd',
        maxZoom: 20
    },

    // Option 4: OpenStreetMap (Dark style - requires custom tiles)
    // Note: This is a placeholder - you'd need to host your own dark tiles
    osmDark: {
        url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19,
        // You would apply CSS filter to darken it (see below)
    }
};

// ============================================
// Map Initialization with Dark Theme
// ============================================

function initializeDarkMap(containerId, centerLat = 0, centerLng = 0, zoom = 2) {
    // Create map
    const map = L.map(containerId, {
        center: [centerLat, centerLng],
        zoom: zoom,
        zoomControl: true,
        scrollWheelZoom: true,
        attributionControl: true
    });

    // Add dark tile layer (using Carto Dark)
    L.tileLayer(darkMapProviders.cartoDark.url, {
        attribution: darkMapProviders.cartoDark.attribution,
        subdomains: darkMapProviders.cartoDark.subdomains,
        maxZoom: darkMapProviders.cartoDark.maxZoom
    }).addTo(map);

    // Style the attribution control to match dark theme
    const attributionControl = map.attributionControl;
    if (attributionControl) {
        const attrContainer = attributionControl.getContainer();
        attrContainer.style.backgroundColor = 'rgba(17, 28, 68, 0.8)';
        attrContainer.style.color = '#e4e6eb';
        attrContainer.style.backdropFilter = 'blur(10px)';
        attrContainer.style.borderTop = '1px solid rgba(0, 234, 255, 0.2)';
    }

    // Style zoom controls
    const zoomControl = map.zoomControl;
    if (zoomControl) {
        const zoomContainer = zoomControl.getContainer();
        zoomContainer.style.filter = 'invert(0.9) hue-rotate(180deg)';
    }

    return map;
}

// ============================================
// Custom Marker Icons (Cyber Theme)
// ============================================

// Neon Cyan Marker
const cyberMarkerIcon = L.divIcon({
    className: 'cyber-marker',
    html: `
        <div style="
            width: 30px;
            height: 30px;
            border-radius: 50%;
            background: radial-gradient(circle, #00eaff 0%, #0088cc 70%);
            border: 2px solid rgba(255, 255, 255, 0.8);
            box-shadow: 0 0 15px rgba(0, 234, 255, 0.8), 0 0 25px rgba(0, 234, 255, 0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            color: #0a0f24;
            font-weight: bold;
            font-size: 16px;
        ">⚠</div>
    `,
    iconSize: [30, 30],
    iconAnchor: [15, 15],
    popupAnchor: [0, -15]
});

// Attack Marker (Red)
const attackMarkerIcon = L.divIcon({
    className: 'attack-marker',
    html: `
        <div style="
            width: 28px;
            height: 28px;
            border-radius: 50%;
            background: radial-gradient(circle, #ef5350 0%, #c62828 70%);
            border: 2px solid rgba(255, 255, 255, 0.9);
            box-shadow: 0 0 15px rgba(239, 83, 80, 0.8);
            animation: pulse-marker 2s infinite;
        "></div>
    `,
    iconSize: [28, 28],
    iconAnchor: [14, 14],
    popupAnchor: [0, -14]
});

// Success Marker (Green)
const successMarkerIcon = L.divIcon({
    className: 'success-marker',
    html: `
        <div style="
            width: 24px;
            height: 24px;
            border-radius: 50%;
            background: radial-gradient(circle, #00ff88 0%, #00cc66 70%);
            border: 2px solid rgba(255, 255, 255, 0.9);
            box-shadow: 0 0 10px rgba(0, 255, 136, 0.6);
        "></div>
    `,
    iconSize: [24, 24],
    iconAnchor: [12, 12],
    popupAnchor: [0, -12]
});

// ============================================
// Custom Popup Style
// ============================================

function createStyledPopup(content) {
    return L.popup({
        className: 'cyber-popup',
        maxWidth: 300,
        closeButton: true
    }).setContent(`
        <div style="
            background: linear-gradient(135deg, #111c44 0%, #0f1729 100%);
            color: #e4e6eb;
            padding: 12px;
            border-radius: 8px;
            font-family: 'Inter', sans-serif;
            font-size: 13px;
            line-height: 1.6;
        ">
            ${content}
        </div>
    `);
}

// ============================================
// Add Attack Marker with Info
// ============================================

function addAttackMarker(map, lat, lng, attackInfo) {
    const popupContent = `
        <div style="font-family: 'Courier New', monospace;">
            <strong style="color: #00eaff; font-size: 14px;">${attackInfo.ip}</strong><br>
            <span style="color: #64b5f6;">📍 ${attackInfo.country} (${attackInfo.city || 'Unknown'})</span><br>
            <span style="color: #e4e6eb;">🕒 ${attackInfo.timestamp}</span><br>
            <span style="color: #ffab00;">⚠️ ${attackInfo.attack_type}</span><br>
            ${attackInfo.details ? `<span style="color: rgba(228, 230, 235, 0.7); font-size: 12px;">${attackInfo.details}</span>` : ''}
        </div>
    `;

    const marker = L.marker([lat, lng], { icon: attackMarkerIcon })
        .bindPopup(createStyledPopup(popupContent))
        .addTo(map);

    return marker;
}

// ============================================
// Marker Clustering (for many attacks)
// ============================================

function createMarkerCluster(map) {
    // Create custom cluster icon
    const markers = L.markerClusterGroup({
        iconCreateFunction: function (cluster) {
            const count = cluster.getChildCount();
            let size = 'small';
            let color = '#00eaff';

            if (count > 100) {
                size = 'large';
                color = '#ef5350';
            } else if (count > 50) {
                size = 'medium';
                color = '#ffab00';
            }

            return L.divIcon({
                html: `
                    <div style="
                        width: ${size === 'large' ? '50' : size === 'medium' ? '40' : '30'}px;
                        height: ${size === 'large' ? '50' : size === 'medium' ? '40' : '30'}px;
                        border-radius: 50%;
                        background: radial-gradient(circle, ${color} 0%, ${color}99 70%);
                        border: 2px solid rgba(255, 255, 255, 0.9);
                        box-shadow: 0 0 20px ${color}CC;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        color: #0a0f24;
                        font-weight: bold;
                        font-size: ${size === 'large' ? '16' : size === 'medium' ? '14' : '12'}px;
                    ">${count}</div>
                `,
                className: 'cyber-cluster',
                iconSize: L.point(
                    size === 'large' ? 50 : size === 'medium' ? 40 : 30,
                    size === 'large' ? 50 : size === 'medium' ? 40 : 30
                )
            });
        },
        spiderfyOnMaxZoom: true,
        showCoverageOnHover: false,
        zoomToBoundsOnClick: true
    });

    map.addLayer(markers);
    return markers;
}

// ============================================
// CSS Animations (add to your CSS file)
// ============================================

const mapAnimations = `
    @keyframes pulse-marker {
        0%, 100% {
            transform: scale(1);
            opacity: 1;
        }
        50% {
            transform: scale(1.15);
            opacity: 0.8;
        }
    }

    /* Style Leaflet popups */
    .leaflet-popup-content-wrapper {
        background: linear-gradient(135deg, #111c44 0%, #0f1729 100%) !important;
        color: #e4e6eb !important;
        border: 1px solid rgba(0, 234, 255, 0.3) !important;
        border-radius: 10px !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5) !important;
    }

    .leaflet-popup-content {
        margin: 0 !important;
    }

    .leaflet-popup-tip {
        background: #111c44 !important;
        border: 1px solid rgba(0, 234, 255, 0.3) !important;
    }

    /* Style cluster polygons */
    .leaflet-cluster-anim .leaflet-marker-icon,
    .leaflet-cluster-anim .leaflet-marker-shadow {
        transition: transform 0.3s ease-out, opacity 0.3s ease-in;
    }
`;

// ============================================
// Usage Example
// ============================================

/*
// Initialize the map
const attackMap = initializeDarkMap('attack-map', 20, 0, 2);

// Add some example attack markers
addAttackMarker(attackMap, 40.7128, -74.0060, {
    ip: '203.0.113.45',
    country: 'United States',
    city: 'New York',
    timestamp: '2025-11-16 15:30:22',
    attack_type: 'SQL Injection',
    details: 'Attempted injection in login form'
});

addAttackMarker(attackMap, 39.9042, 116.4074, {
    ip: '198.51.100.22',
    country: 'China',
    city: 'Beijing',
    timestamp: '2025-11-16 15:28:10',
    attack_type: 'Login Attempt',
    details: 'Failed login with username: admin'
});

// For many markers, use clustering
const clusterGroup = createMarkerCluster(attackMap);
// Add markers to cluster instead of map directly
// marker.addTo(clusterGroup);
*/

// ============================================
// Export Configuration
// ============================================

window.LeafletDarkTheme = {
    darkMapProviders,
    initializeDarkMap,
    cyberMarkerIcon,
    attackMarkerIcon,
    successMarkerIcon,
    createStyledPopup,
    addAttackMarker,
    createMarkerCluster,
    mapAnimations
};
