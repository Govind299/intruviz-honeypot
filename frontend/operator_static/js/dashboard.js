/**
 * Dashboard JavaScript - Module D Real-time Analytics
 * Handles WebSocket connections, chart updates, and UI interactions
 */

class HoneypotDashboard {
    constructor() {
        this.socket = null;
        this.charts = {};
        this.map = null;
        this.markers = null;
        this.autoScroll = true;
        this.filters = {};
        this.eventQueue = [];
        this.updateThrottle = null;
        
        this.init();
    }
    
    init() {
        this.initSocketIO();
        this.initCharts();
        this.initMap();
        this.initEventHandlers();
        this.loadInitialData();
        
        // Start periodic updates
        setInterval(() => this.updateStats(), 30000); // Every 30 seconds
    }
    
    initSocketIO() {
        console.log('🔌 Connecting to WebSocket...');
        this.socket = io('/events');
        
        this.socket.on('connect', () => {
            console.log('Connected to real-time events');
            this.updateStatus('realtime', 'Connected', 'connected');
            this.socket.emit('request_recent', { limit: 10 });
        });
        
        this.socket.on('disconnect', () => {
            console.log('Disconnected from real-time events');
            this.updateStatus('realtime', 'Disconnected', 'disconnected');
        });
        
        this.socket.on('event.new', (event) => {
            console.log('New event received:', event);
            this.handleNewEvent(event);
        });
        
        this.socket.on('event.updated', (update) => {
            console.log('Event updated:', update);
            this.handleEventUpdate(update);
        });
        
        this.socket.on('recent_events', (data) => {
            console.log('Recent events received:', data);
            this.populateInitialEvents(data.events || []);
        });
    }
    
    initCharts() {
        // Timeline Chart
        const timelineCtx = document.getElementById('timeline-chart');
        if (timelineCtx) {
            this.charts.timeline = new Chart(timelineCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Events',
                        data: [],
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }
        
        // Countries Chart
        const countriesCtx = document.getElementById('countries-chart');
        if (countriesCtx) {
            this.charts.countries = new Chart(countriesCtx, {
                type: 'bar',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Attacks',
                        data: [],
                        backgroundColor: [
                            '#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#ffeaa7',
                            '#dda0dd', '#98d8c8', '#f7dc6f', '#bb8fce', '#85c1e9'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    indexAxis: 'y'
                }
            });
        }
        
        // IPs Chart
        const ipsCtx = document.getElementById('ips-chart');
        if (ipsCtx) {
            this.charts.ips = new Chart(ipsCtx, {
                type: 'bar',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Attacks',
                        data: [],
                        backgroundColor: '#ff6b6b'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    indexAxis: 'y'
                }
            });
        }
        
        // Attack Types Chart
        const typesCtx = document.getElementById('types-chart');
        if (typesCtx) {
            this.charts.types = new Chart(typesCtx, {
                type: 'doughnut',
                data: {
                    labels: [],
                    datasets: [{
                        data: [],
                        backgroundColor: [
                            '#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#ffeaa7'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
        }
    }
    
    initMap() {
        const mapElement = document.getElementById('attack-map');
        if (!mapElement) return;
        
        this.map = L.map('attack-map').setView([20, 0], 2);
        
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(this.map);
        
        this.markers = L.markerClusterGroup();
        this.map.addLayer(this.markers);
    }
    
    initEventHandlers() {
        // Auto-scroll toggle
        const autoScrollCheckbox = document.getElementById('auto-scroll');
        if (autoScrollCheckbox) {
            autoScrollCheckbox.addEventListener('change', (e) => {
                this.autoScroll = e.target.checked;
            });
        }
        
        // Time range selector
        const timeRangeSelect = document.getElementById('time-range');
        if (timeRangeSelect) {
            timeRangeSelect.addEventListener('change', () => {
                this.updateStats();
                this.updateMapData();
            });
        }
        
        // Filter controls
        document.getElementById('btn-apply-filters')?.addEventListener('click', () => {
            this.applyFilters();
        });
        
        document.getElementById('btn-clear-filters')?.addEventListener('click', () => {
            this.clearFilters();
        });
        
        document.getElementById('btn-export-csv')?.addEventListener('click', () => {
            this.exportCSV();
        });
        
        // Modal controls
        const modal = document.getElementById('event-modal');
        const closeBtn = document.querySelector('.modal-close');
        
        closeBtn?.addEventListener('click', () => {
            modal.style.display = 'none';
        });
        
        window.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.style.display = 'none';
            }
        });
    }
    
    handleNewEvent(event) {
        // Add to event queue for throttled updates
        this.eventQueue.push(event);
        
        // Throttle UI updates to avoid flooding
        if (!this.updateThrottle) {
            this.updateThrottle = setTimeout(() => {
                this.processEventQueue();
                this.updateThrottle = null;
            }, 1000);
        }
    }
    
    processEventQueue() {
        if (this.eventQueue.length === 0) return;
        
        // Process all queued events
        const events = [...this.eventQueue];
        this.eventQueue = [];
        
        // Add events to feed
        events.forEach(event => this.addEventToFeed(event));
        
        // Update status
        this.updateStats();
        this.updateMapData();
    }
    
    addEventToFeed(event) {
        const eventsContainer = document.getElementById('events-feed');
        if (!eventsContainer) return;
        
        const eventCard = document.createElement('div');
        eventCard.className = 'event-card new';
        eventCard.onclick = () => this.showEventDetail(event.id);
        
        eventCard.innerHTML = `
            <div class="event-header">
                <span class="event-ip">${event.ip}</span>
                <span class="event-time">${new Date(event.timestamp).toLocaleTimeString()}</span>
            </div>
            <div class="event-location">${event.country}, ${event.city}</div>
            <div class="event-details">
                ${event.endpoint} • ${event.user_agent.substring(0, 50)}...
            </div>
            <span class="attack-badge">${event.attack_type}</span>
        `;
        
        // Add to top of feed
        eventsContainer.insertBefore(eventCard, eventsContainer.firstChild);
        
        // Remove old events (keep max 50)
        const eventCards = eventsContainer.querySelectorAll('.event-card');
        if (eventCards.length > 50) {
            eventCards[eventCards.length - 1].remove();
        }
        
        // Auto-scroll if enabled
        if (this.autoScroll) {
            eventsContainer.scrollTop = 0;
        }
        
        // Remove 'new' class after animation
        setTimeout(() => {
            eventCard.classList.remove('new');
        }, 500);
    }
    
    populateInitialEvents(events) {
        const eventsContainer = document.getElementById('events-feed');
        if (!eventsContainer) return;
        
        eventsContainer.innerHTML = '';
        
        events.forEach(event => {
            const eventCard = document.createElement('div');
            eventCard.className = 'event-card';
            eventCard.onclick = () => this.showEventDetail(event.id);
            
            eventCard.innerHTML = `
                <div class="event-header">
                    <span class="event-ip">${event.client_ip}</span>
                    <span class="event-time">${new Date(event.timestamp).toLocaleTimeString()}</span>
                </div>
                <div class="event-location">${event.country || 'Unknown'}, ${event.city || 'Unknown'}</div>
                <div class="event-details">
                    ${event.endpoint || '/login'} • ${(event.user_agent || '').substring(0, 50)}...
                </div>
                <span class="attack-badge">${event.attack_type || 'login_attempt'}</span>
            `;
            
            eventsContainer.appendChild(eventCard);
        });
    }
    
    updateStats() {
        const timeRange = document.getElementById('time-range')?.value || '24';
        
        fetch(`/api/stats?hours=${timeRange}`)
            .then(response => response.json())
            .then(data => {
                // Update status bar
                this.updateStatus('total', data.total_events.toLocaleString());
                this.updateStatus('countries', data.top_countries.length);
                
                if (data.timeline && data.timeline.length > 0) {
                    const lastEvent = data.timeline[data.timeline.length - 1];
                    this.updateStatus('last', new Date(lastEvent.time).toLocaleTimeString());
                }
                
                // Update charts
                this.updateTimelineChart(data.timeline);
                this.updateCountriesChart(data.top_countries);
                this.updateIPsChart(data.top_ips);
                this.updateTypesChart(data.attack_types);
            })
            .catch(error => {
                console.error('Failed to update stats:', error);
            });
    }
    
    updateTimelineChart(timeline) {
        if (!this.charts.timeline || !timeline) return;
        
        const labels = timeline.map(item => new Date(item.time).toLocaleTimeString());
        const data = timeline.map(item => item.count);
        
        this.charts.timeline.data.labels = labels;
        this.charts.timeline.data.datasets[0].data = data;
        this.charts.timeline.update();
    }
    
    updateCountriesChart(countries) {
        if (!this.charts.countries || !countries) return;
        
        const labels = countries.slice(0, 5).map(item => item.country);
        const data = countries.slice(0, 5).map(item => item.count);
        
        this.charts.countries.data.labels = labels;
        this.charts.countries.data.datasets[0].data = data;
        this.charts.countries.update();
    }
    
    updateIPsChart(ips) {
        if (!this.charts.ips || !ips) return;
        
        const labels = ips.slice(0, 5).map(item => item.ip);
        const data = ips.slice(0, 5).map(item => item.count);
        
        this.charts.ips.data.labels = labels;
        this.charts.ips.data.datasets[0].data = data;
        this.charts.ips.update();
    }
    
    updateTypesChart(types) {
        if (!this.charts.types || !types) return;
        
        const labels = types.map(item => item.type);
        const data = types.map(item => item.count);
        
        this.charts.types.data.labels = labels;
        this.charts.types.data.datasets[0].data = data;
        this.charts.types.update();
    }
    
    updateMapData() {
        const timeRange = document.getElementById('time-range')?.value || '24';
        
        fetch(`/api/map_points?hours=${timeRange}&limit=1000`)
            .then(response => response.json())
            .then(data => {
                if (!this.markers) return;
                
                this.markers.clearLayers();
                
                data.points.forEach(point => {
                    const marker = L.marker([point.lat, point.lng]);
                    marker.bindPopup(point.popup);
                    this.markers.addLayer(marker);
                });
            })
            .catch(error => {
                console.error('Failed to update map data:', error);
            });
    }
    
    showEventDetail(eventId) {
        const modal = document.getElementById('event-modal');
        const content = document.getElementById('event-detail-content');
        
        if (!modal || !content) return;
        
        content.innerHTML = '<div class="loading">Loading event details...</div>';
        modal.style.display = 'block';
        
        fetch(`/api/event/${eventId}`)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    content.innerHTML = `<div class="error">Error: ${data.error}</div>`;
                    return;
                }
                
                const event = data.event;
                const enrichment = data.enrichment;
                
                content.innerHTML = `
                    <div class="event-detail-summary">
                        <h3>Event Summary</h3>
                        <table class="detail-table">
                            <tr><td><strong>Event ID:</strong></td><td>${event.id}</td></tr>
                            <tr><td><strong>Timestamp:</strong></td><td>${event.timestamp}</td></tr>
                            <tr><td><strong>Client IP:</strong></td><td>${event.client_ip}</td></tr>
                            <tr><td><strong>Location:</strong></td><td>${event.country}, ${event.region}, ${event.city}</td></tr>
                            <tr><td><strong>Attack Type:</strong></td><td>${event.attack_type || 'login_attempt'}</td></tr>
                        </table>
                        
                        <h3>Form Data</h3>
                        <pre class="json-display">${JSON.stringify(event.form_data || {}, null, 2)}</pre>
                        
                        <h3>Headers</h3>
                        <pre class="json-display">${JSON.stringify(event.headers || {}, null, 2)}</pre>
                        
                        <div style="margin-top: 1rem;">
                            <a href="/operator/event/${eventId}" target="_blank" class="detail-link">
                                View Full Details
                            </a>
                        </div>
                    </div>
                `;
            })
            .catch(error => {
                content.innerHTML = `<div class="error">Failed to load event details: ${error}</div>`;
            });
    }
    
    applyFilters() {
        this.filters = {
            ip: document.getElementById('filter-ip')?.value || '',
            country: document.getElementById('filter-country')?.value || '',
            type: document.getElementById('filter-type')?.value || '',
            since: document.getElementById('filter-since')?.value || ''
        };
        
        this.loadFilteredEvents();
    }
    
    clearFilters() {
        document.getElementById('filter-ip').value = '';
        document.getElementById('filter-country').value = '';
        document.getElementById('filter-type').value = '';
        document.getElementById('filter-since').value = '';
        
        this.filters = {};
        this.loadInitialData();
    }
    
    loadFilteredEvents() {
        const params = new URLSearchParams();
        Object.entries(this.filters).forEach(([key, value]) => {
            if (value) params.append(key, value);
        });
        
        fetch(`/api/events?${params.toString()}`)
            .then(response => response.json())
            .then(data => {
                this.populateInitialEvents(data.events || []);
            })
            .catch(error => {
                console.error('Failed to load filtered events:', error);
            });
    }
    
    exportCSV() {
        const params = new URLSearchParams();
        Object.entries(this.filters).forEach(([key, value]) => {
            if (value) params.append(key, value);
        });
        
        window.open(`/api/export/csv?${params.toString()}`, '_blank');
    }
    
    loadInitialData() {
        this.updateStats();
        this.updateMapData();
        
        // Load recent events
        fetch('/api/events?limit=20')
            .then(response => response.json())
            .then(data => {
                this.populateInitialEvents(data.events || []);
            })
            .catch(error => {
                console.error('Failed to load initial events:', error);
            });
    }
    
    updateStatus(element, value, className = '') {
        const statusElement = document.getElementById(`status-${element}`);
        if (statusElement) {
            statusElement.textContent = value;
            if (className) {
                statusElement.className = className;
            }
        }
    }
    
    handleEventUpdate(update) {
        console.log('Event updated:', update);
        // Could implement event card updates here if needed
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new HoneypotDashboard();
});

// Add some CSS for dynamic elements
const style = document.createElement('style');
style.textContent = `
    .loading {
        text-align: center;
        padding: 2rem;
        color: #7f8c8d;
    }
    
    .detail-link {
        display: inline-block;
        background: #667eea;
        color: white;
        padding: 0.5rem 1rem;
        text-decoration: none;
        border-radius: 5px;
        font-size: 0.9rem;
    }
    
    .detail-link:hover {
        background: #5a6fd8;
    }
    
    .event-detail-summary {
        max-height: 60vh;
        overflow-y: auto;
    }
`;
document.head.appendChild(style);
