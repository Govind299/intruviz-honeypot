/**
 * Dashboard JavaScript -Real-time Analytics
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
        this.loginTime = null; // Store login time
        this.latestEventTime = null; // Track the latest event timestamp
        this.isFilterActive = false; // Track if user has applied filters
        this.totalEventsCount = 0; // Store total events count (never changes with filters)

        this.init();
    }

    init() {
        // Get login time from page
        this.loginTime = document.querySelector('.login-info')?.textContent.replace('Logged in: ', '').trim() || null;
        console.log('Login time:', this.loginTime);

        this.initSocketIO();
        this.initCharts();
        this.initMap();
        this.initEventHandlers();
        this.loadInitialData();

        // Start periodic updates
        setInterval(() => this.updateStats(), 30000); // Every 30 seconds
    }

    initSocketIO() {
        console.log('🔌 Connecting to LIVE WebSocket...');
        this.socket = io('/live');

        this.socket.on('connect', () => {
            console.log('✅ Connected to LIVE real-time events');
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
            console.log('Number of events:', (data.events || []).length);
            console.log('Filters applied:', data.filters);
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
        // If user has applied date filter, don't show new real-time events
        if (this.isFilterActive) {
            console.log('⏸️ Filter active - skipping real-time event display');
            return;
        }

        // Add to event queue for throttled updates
        this.eventQueue.push(event);

        // Immediately add to feed for real-time display (no throttle for new events)
        this.addEventToFeed(event);

        // Throttle stats/chart updates to avoid flooding
        if (!this.updateThrottle) {
            this.updateThrottle = setTimeout(() => {
                this.updateStats();
                this.updateMapData();
                this.updateThrottle = null;
            }, 2000); // Update stats every 2 seconds
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

        // CLIENT-SIDE FILTER: Only show events after login time
        if (this.loginTime) {
            const loginTimestamp = new Date(this.loginTime).getTime();
            const eventTimestamp = new Date(event.timestamp).getTime();
            if (eventTimestamp <= loginTimestamp) {
                console.log(`⏭️ Skipping event from ${event.timestamp} (before login at ${this.loginTime})`);
                return; // Skip this event
            }
        }

        // Remove "No Live Attacks" message if it exists
        const noEventsMsg = eventsContainer.querySelector('.no-events-message');
        if (noEventsMsg) {
            noEventsMsg.remove();
        }

        const eventCard = document.createElement('div');
        eventCard.className = 'event-card new';
        eventCard.onclick = () => this.showEventDetail(event.id);

        // Handle both new real-time events and loaded events
        const ip = event.ip || event.client_ip;
        const timestamp = event.timestamp;
        const country = event.country || 'Unknown';
        const city = event.city || 'Unknown';
        const endpoint = event.endpoint || '/login';
        const userAgent = event.user_agent || '';
        const attackType = event.attack_type || 'login_attempt';

        const eventTime = new Date(timestamp);
        const timeStr = eventTime.toLocaleTimeString();

        // Update latest event time
        if (!this.latestEventTime || eventTime > new Date(this.latestEventTime)) {
            this.latestEventTime = timestamp;
            this.updateStatus('last', timeStr);
        }

        eventCard.innerHTML = `
            <div class="event-header">
                <span class="event-ip">${ip}</span>
                <span class="event-time">${timeStr}</span>
            </div>
            <div class="event-location">${country}, ${city}</div>
            <div class="event-details">
                ${endpoint} • ${userAgent.substring(0, 50)}...
            </div>
            <span class="attack-badge">${attackType}</span>
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

        // ADDITIONAL CLIENT-SIDE FILTER: Only show events after login time
        let filteredEvents = events;
        if (this.loginTime && events && events.length > 0) {
            const loginTimestamp = new Date(this.loginTime).getTime();
            filteredEvents = events.filter(event => {
                const eventTimestamp = new Date(event.timestamp).getTime();
                return eventTimestamp > loginTimestamp;
            });
            console.log(`🔍 Login time: ${this.loginTime}`);
            console.log(`🔍 Filtered ${events.length} events to ${filteredEvents.length} events`);
        }

        // Show message if no events after filtering
        if (!filteredEvents || filteredEvents.length === 0) {
            eventsContainer.innerHTML = `
                <div class="no-events-message" style="text-align: center; padding: 3rem; color: #7f8c8d;">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">🔒</div>
                    <h3 style="margin: 0 0 0.5rem 0; color: #2c3e50;">No Live Attacks</h3>
                    <p style="margin: 0; font-size: 0.9rem;">No attacks detected since your login.</p>
                    <p style="margin: 0.5rem 0 0 0; font-size: 0.85rem; color: #95a5a6;">
                        Use filters above to view historical data.
                    </p>
                </div>
            `;
            return;
        }

        // Show "Live Mode" indicator
        const liveModeMessage = document.createElement('div');
        liveModeMessage.className = 'live-mode-message';
        liveModeMessage.style.cssText = 'background: #27ae60; color: white; padding: 1rem; text-align: center; margin-bottom: 1rem; border-radius: 5px; font-weight: bold;';
        liveModeMessage.innerHTML = `🔴 LIVE MODE - Showing attacks since ${this.loginTime}`;
        eventsContainer.appendChild(liveModeMessage);

        filteredEvents.forEach(event => {
            const eventCard = document.createElement('div');
            eventCard.className = 'event-card';
            eventCard.onclick = () => this.showEventDetail(event.id);

            const eventTime = new Date(event.timestamp);
            const timeStr = eventTime.toLocaleTimeString();

            // Track latest event time
            if (!this.latestEventTime || eventTime > new Date(this.latestEventTime)) {
                this.latestEventTime = event.timestamp;
            }

            eventCard.innerHTML = `
                <div class="event-header">
                    <span class="event-ip">${event.client_ip}</span>
                    <span class="event-time">${timeStr}</span>
                </div>
                <div class="event-location">${event.country || 'Unknown'}, ${event.city || 'Unknown'}</div>
                <div class="event-details">
                    ${event.endpoint || '/login'} • ${(event.user_agent || '').substring(0, 50)}...
                </div>
                <span class="attack-badge">${event.attack_type || 'login_attempt'}</span>
            `;

            eventsContainer.appendChild(eventCard);
        });

        // Update the "Last Attack" status with the actual latest event
        if (this.latestEventTime) {
            this.updateStatus('last', new Date(this.latestEventTime).toLocaleTimeString());
        }
    }

    populateFilteredEvents(events) {
        const eventsContainer = document.getElementById('events-feed');
        if (!eventsContainer) return;

        eventsContainer.innerHTML = '';

        // When user applies filters, show ALL returned events (no client-side filtering by login time)
        console.log(`🔍 Showing ${events.length} filtered events from backend`);

        // Show message if no events
        if (!events || events.length === 0) {
            eventsContainer.innerHTML = `
                <div class="no-events-message" style="text-align: center; padding: 3rem; color: #7f8c8d;">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">🔍</div>
                    <h3 style="margin: 0 0 0.5rem 0; color: #2c3e50;">No Events Found</h3>
                    <p style="margin: 0; font-size: 0.9rem;">No events match your filter criteria.</p>
                    <p style="margin: 0.5rem 0 0 0; font-size: 0.85rem; color: #95a5a6;">
                        Try adjusting your filters or click "Clear" to reset.
                    </p>
                </div>
            `;
            return;
        }

        // Show filter active message at the top
        const filterMessage = document.createElement('div');
        filterMessage.className = 'filter-active-message';
        filterMessage.style.cssText = 'background: #3498db; color: white; padding: 1rem; text-align: center; margin-bottom: 1rem; border-radius: 5px; font-weight: bold;';

        const dateFilter = this.filters.since;
        if (dateFilter) {
            filterMessage.innerHTML = `📅 Viewing events from: ${dateFilter} | <span style="cursor: pointer; text-decoration: underline;" onclick="dashboard.clearFilters()">Clear Filter</span>`;
        } else {
            filterMessage.innerHTML = `🔍 Filters Active | <span style="cursor: pointer; text-decoration: underline;" onclick="dashboard.clearFilters()">Clear Filters</span>`;
        }
        eventsContainer.appendChild(filterMessage);

        // Render all filtered events
        events.forEach(event => {
            const eventCard = document.createElement('div');
            eventCard.className = 'event-card';
            eventCard.onclick = () => this.showEventDetail(event.id);

            const eventTime = new Date(event.timestamp);
            const timeStr = eventTime.toLocaleTimeString();

            // Track latest event time
            if (!this.latestEventTime || eventTime > new Date(this.latestEventTime)) {
                this.latestEventTime = event.timestamp;
            }

            eventCard.innerHTML = `
                <div class="event-header">
                    <span class="event-ip">${event.client_ip}</span>
                    <span class="event-time">${timeStr}</span>
                </div>
                <div class="event-location">${event.country || 'Unknown'}, ${event.city || 'Unknown'}</div>
                <div class="event-details">
                    ${event.endpoint || '/login'} • ${(event.user_agent || '').substring(0, 50)}...
                </div>
                <span class="attack-badge">${event.attack_type || 'login_attempt'}</span>
            `;

            eventsContainer.appendChild(eventCard);
        });

        // Update the "Last Attack" status with the actual latest event
        if (this.latestEventTime) {
            this.updateStatus('last', new Date(this.latestEventTime).toLocaleTimeString());
        }
    }

    updateStats() {
        // Build query params with same filters as events
        const params = new URLSearchParams();

        // Use time range from filters if applied, otherwise default to 24 hours
        const timeRangeHours = this.filters?.timeRange || '24';
        params.append('hours', timeRangeHours);

        // Add current filters if active
        if (this.filters && Object.keys(this.filters).length > 0) {
            Object.entries(this.filters).forEach(([key, value]) => {
                if (value && key !== 'timeRange') { // Don't add timeRange to params, we use 'hours' instead
                    params.append(key, value);
                }
            });
        }

        fetch(`/api/live/stats?${params.toString()}`)
            .then(response => response.json())
            .then(data => {
                // ALWAYS use total_all_events from backend (ALL events in database)
                // This never changes with filters
                console.log('📊 Received total_all_events from backend:', data.total_all_events);
                if (data.total_all_events !== undefined) {
                    this.totalEventsCount = data.total_all_events;
                    console.log('✅ Updated totalEventsCount to:', this.totalEventsCount);
                }

                // Always display the total count of ALL events in database
                console.log('🔢 Displaying total events:', this.totalEventsCount.toLocaleString());
                this.updateStatus('total', this.totalEventsCount.toLocaleString());
                this.updateStatus('countries', data.top_countries.length);

                // Don't update "last attack" time from filtered stats
                // It should always show the most recent attack regardless of filters
                // The latestEventTime is set by populateInitialEvents and handleNewEvent

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

        fetch(`/api/live/map_points?hours=${timeRange}&limit=1000`)
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

        fetch(`/api/live/event/${eventId}`)
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
                            <a href="/live/event/${eventId}" target="_blank" class="detail-link">
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
        const dateFilter = document.getElementById('filter-since')?.value || '';
        const timeRangeFilter = document.getElementById('filter-time-range')?.value || '';

        // Time range filter takes precedence over date filter
        let sinceValue = '';
        let timeRangeHours = '';

        if (timeRangeFilter) {
            // Calculate timestamp for time range (hours ago from now)
            const hoursAgo = parseInt(timeRangeFilter);
            const sinceDate = new Date();
            sinceDate.setHours(sinceDate.getHours() - hoursAgo);
            sinceValue = sinceDate.toISOString();
            timeRangeHours = timeRangeFilter; // Store for stats API
        } else if (dateFilter) {
            // Use the selected date if no time range is selected
            sinceValue = dateFilter;
        }

        this.filters = {
            ip: document.getElementById('filter-ip')?.value || '',
            country: document.getElementById('filter-country')?.value || '',
            type: document.getElementById('filter-type')?.value || '',
            since: sinceValue,
            timeRange: timeRangeHours // Store time range for stats
        };

        // Mark that filters are active
        this.isFilterActive = true;

        // When filters are applied, update everything
        this.loadFilteredEvents();
        this.updateStats();
        this.updateMapData();
    }

    clearFilters() {
        document.getElementById('filter-ip').value = '';
        document.getElementById('filter-country').value = '';
        document.getElementById('filter-type').value = '';
        document.getElementById('filter-since').value = '';
        document.getElementById('filter-time-range').value = '';

        this.filters = {};
        this.isFilterActive = false; // Clear filter active flag

        // Go back to showing only post-login events
        this.loadInitialData();
    }

    loadFilteredEvents() {
        const params = new URLSearchParams();
        Object.entries(this.filters).forEach(([key, value]) => {
            if (value) params.append(key, value);
        });

        fetch(`/api/live/events?${params.toString()}`)
            .then(response => response.json())
            .then(data => {
                // When user applies filters, show ALL returned events (don't apply client-side login time filter)
                this.populateFilteredEvents(data.events || []);
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

        window.open(`/api/live/export/csv?${params.toString()}`, '_blank');
    }

    loadInitialData() {
        this.updateStats();
        this.updateMapData();

        // Load recent events (will automatically filter by login time on backend)
        fetch('/api/live/events?limit=20')
            .then(response => response.json())
            .then(data => {
                this.populateInitialEvents(data.events || []);
            })
            .catch(error => {
                console.error('Failed to load initial events:', error);
            });
    } updateStatus(element, value, className = '') {
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
