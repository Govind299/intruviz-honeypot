/**
 * Honeypot Client-Side Event Capture
 * 
 * This script captures client-side events and user interactions
 * for additional analysis. It helps identify automated tools and
 * provides insights into attacker behavior patterns.
 */

(function() {
    'use strict';
    
    // Event capture configuration
    const CAPTURE_CONFIG = {
        enableMouseTracking: true,
        enableKeyboardTracking: true,
        enableTimingTracking: true,
        enableJSDisabledDetection: true
    };
    
    // Store captured events
    let capturedEvents = [];
    let sessionStartTime = Date.now();
    let formInteractionStart = null;
    
    // Generate a session ID for client-side tracking
    const sessionId = 'client_' + Math.random().toString(36).substr(2, 9);
    
    /**
     * Add an event to the capture buffer
     */
    function addEvent(eventType, data = {}) {
        const event = {
            type: eventType,
            timestamp: Date.now(),
            sessionId: sessionId,
            timeFromStart: Date.now() - sessionStartTime,
            ...data
        };
        
        capturedEvents.push(event);
        
        // Keep only last 50 events to prevent memory issues
        if (capturedEvents.length > 50) {
            capturedEvents = capturedEvents.slice(-50);
        }
    }
    
    /**
     * Detect if JavaScript is enabled (it is, since this runs)
     */
    function detectJSEnabled() {
        // Add a hidden field to indicate JS is enabled
        const form = document.getElementById('loginForm');
        if (form) {
            const jsField = document.createElement('input');
            jsField.type = 'hidden';
            jsField.name = 'js_enabled';
            jsField.value = 'true';
            form.appendChild(jsField);
        }
        
        addEvent('js_enabled_detected', {
            userAgent: navigator.userAgent,
            screen: {
                width: screen.width,
                height: screen.height,
                colorDepth: screen.colorDepth
            },
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            language: navigator.language
        });
    }
    
    /**
     * Track mouse movement patterns
     */
    function setupMouseTracking() {
        if (!CAPTURE_CONFIG.enableMouseTracking) return;
        
        let mouseEvents = [];
        let lastMouseEvent = 0;
        
        document.addEventListener('mousemove', function(e) {
            const now = Date.now();
            // Throttle mouse events to avoid spam
            if (now - lastMouseEvent < 100) return;
            lastMouseEvent = now;
            
            mouseEvents.push({
                x: e.clientX,
                y: e.clientY,
                time: now
            });
            
            // Keep only last 20 mouse positions
            if (mouseEvents.length > 20) {
                mouseEvents = mouseEvents.slice(-20);
            }
        });
        
        // Analyze mouse patterns on form submission
        const form = document.getElementById('loginForm');
        if (form) {
            form.addEventListener('submit', function() {
                if (mouseEvents.length > 0) {
                    const totalDistance = calculateMouseDistance(mouseEvents);
                    const avgSpeed = totalDistance / (mouseEvents[mouseEvents.length - 1].time - mouseEvents[0].time);
                    
                    addEvent('mouse_analysis', {
                        totalEvents: mouseEvents.length,
                        totalDistance: totalDistance,
                        averageSpeed: avgSpeed,
                        humanLikely: mouseEvents.length > 5 && avgSpeed < 2.0  // Basic heuristic
                    });
                }
            });
        }
    }
    
    /**
     * Calculate total mouse movement distance
     */
    function calculateMouseDistance(events) {
        let distance = 0;
        for (let i = 1; i < events.length; i++) {
            const dx = events[i].x - events[i-1].x;
            const dy = events[i].y - events[i-1].y;
            distance += Math.sqrt(dx * dx + dy * dy);
        }
        return distance;
    }
    
    /**
     * Track keyboard interaction patterns
     */
    function setupKeyboardTracking() {
        if (!CAPTURE_CONFIG.enableKeyboardTracking) return;
        
        let keyEvents = [];
        
        ['keydown', 'keyup'].forEach(eventType => {
            document.addEventListener(eventType, function(e) {
                // Don't log actual key values for privacy
                keyEvents.push({
                    type: eventType,
                    time: Date.now(),
                    keyCode: e.keyCode,
                    target: e.target.name || e.target.id || 'unknown'
                });
                
                // Keep only last 50 key events
                if (keyEvents.length > 50) {
                    keyEvents = keyEvents.slice(-50);
                }
            });
        });
        
        // Analyze typing patterns on form submission
        const form = document.getElementById('loginForm');
        if (form) {
            form.addEventListener('submit', function() {
                if (keyEvents.length > 0) {
                    const typingIntervals = [];
                    const keyDownEvents = keyEvents.filter(e => e.type === 'keydown');
                    
                    for (let i = 1; i < keyDownEvents.length; i++) {
                        typingIntervals.push(keyDownEvents[i].time - keyDownEvents[i-1].time);
                    }
                    
                    const avgInterval = typingIntervals.reduce((a, b) => a + b, 0) / typingIntervals.length;
                    const variance = calculateVariance(typingIntervals);
                    
                    addEvent('typing_analysis', {
                        totalKeyEvents: keyEvents.length,
                        averageInterval: avgInterval,
                        variance: variance,
                        humanLikely: avgInterval > 50 && variance > 100  // Basic heuristic
                    });
                }
            });
        }
    }
    
    /**
     * Calculate variance of an array
     */
    function calculateVariance(arr) {
        const mean = arr.reduce((a, b) => a + b, 0) / arr.length;
        return arr.reduce((sq, n) => sq + Math.pow(n - mean, 2), 0) / arr.length;
    }
    
    /**
     * Track form interaction timing
     */
    function setupTimingTracking() {
        if (!CAPTURE_CONFIG.enableTimingTracking) return;
        
        const usernameField = document.getElementById('username');
        const passwordField = document.getElementById('password');
        const form = document.getElementById('loginForm');
        
        if (usernameField) {
            usernameField.addEventListener('focus', function() {
                if (!formInteractionStart) {
                    formInteractionStart = Date.now();
                    addEvent('form_interaction_start');
                }
            });
        }
        
        if (form) {
            form.addEventListener('submit', function() {
                const interactionTime = formInteractionStart ? Date.now() - formInteractionStart : 0;
                
                addEvent('form_submission_timing', {
                    interactionTime: interactionTime,
                    tooFast: interactionTime < 2000,  // Less than 2 seconds might be automated
                    reasonable: interactionTime > 2000 && interactionTime < 300000  // 2s to 5min seems reasonable
                });
            });
        }
    }
    
    /**
     * Add captured events to form submission
     */
    function attachEventsToForm() {
        const form = document.getElementById('loginForm');
        if (form) {
            form.addEventListener('submit', function() {
                // Add all captured events as a hidden field
                const eventsField = document.createElement('input');
                eventsField.type = 'hidden';
                eventsField.name = 'client_events';
                eventsField.value = JSON.stringify(capturedEvents);
                form.appendChild(eventsField);
                
                // Add form submission timestamp
                const timestampField = document.createElement('input');
                timestampField.type = 'hidden';
                timestampField.name = 'client_submit_time';
                timestampField.value = Date.now().toString();
                form.appendChild(timestampField);
            });
        }
    }
    
    /**
     * Handle button loading state
     */
    function setupButtonLoadingState() {
        const form = document.getElementById('loginForm');
        const submitBtn = form ? form.querySelector('.login-btn') : null;
        
        if (form && submitBtn) {
            form.addEventListener('submit', function() {
                const btnText = submitBtn.querySelector('.btn-text');
                const btnLoading = submitBtn.querySelector('.btn-loading');
                
                if (btnText && btnLoading) {
                    btnText.style.display = 'none';
                    btnLoading.style.display = 'inline';
                    submitBtn.disabled = true;
                }
                
                addEvent('form_submission_started');
            });
        }
    }
    
    /**
     * Global function to capture custom events (called from HTML)
     */
    window.captureEvent = function(eventName, data = {}) {
        addEvent('custom_interaction', {
            eventName: eventName,
            ...data
        });
    };
    
    /**
     * Initialize all tracking when DOM is ready
     */
    function initializeTracking() {
        addEvent('client_script_loaded');
        
        detectJSEnabled();
        setupMouseTracking();
        setupKeyboardTracking();
        setupTimingTracking();
        attachEventsToForm();
        setupButtonLoadingState();
        
        addEvent('tracking_initialized');
    }
    
    // Start tracking when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeTracking);
    } else {
        initializeTracking();
    }
    
    // Track page unload
    window.addEventListener('beforeunload', function() {
        addEvent('page_unload');
    });
    
})();