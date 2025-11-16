"""
API helper functions for operator dashboard
Query aggregation and data processing functions for analytics.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Any
import sys
import os

# Add honeypot to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from honeypot.storage import (
    query_recent, query_top_ips, query_top_countries, 
    query_stats_by_time, query_map_points, get_event_by_id
)

def get_dashboard_stats(since_hours: int = 24, since_time: str = None, until_time: str = None, filters: Dict[str, Any] = None) -> Dict[str, Any]:
    """Get comprehensive dashboard statistics"""
    
    # Calculate since timestamp - use provided since_time or calculate from hours
    if since_time:
        since_timestamp = since_time
    else:
        since_timestamp = (datetime.utcnow() - timedelta(hours=since_hours)).isoformat()
    
    # Build filters for querying
    query_filters = filters.copy() if filters else {}
    if 'since' not in query_filters:
        query_filters['since'] = since_timestamp
    if until_time:
        query_filters['until'] = until_time
    
    # Get various statistics using the same filters
    top_ips = query_top_ips(limit=10, since=query_filters.get('since'), until=query_filters.get('until'))
    top_countries = query_top_countries(limit=10, since=query_filters.get('since'), until=query_filters.get('until'))
    timeline = query_stats_by_time(bucket='hour', since=query_filters.get('since'), until=query_filters.get('until'))
    recent_events = query_recent(limit=1000, filters=query_filters)  # Increased limit to get all filtered events
    
    # Calculate attack type distribution from filtered events
    attack_types = {}
    for event in recent_events:
        attack_type = event.get('attack_type', 'unknown')
        attack_types[attack_type] = attack_types.get(attack_type, 0) + 1
    
    return {
        'top_ips': top_ips,
        'top_countries': top_countries,
        'timeline': timeline,
        'attack_types': [{'type': k, 'count': v} for k, v in attack_types.items()],
        'total_events': len(recent_events),
        'timeframe_hours': since_hours,
        'since_time': query_filters.get('since'),
        'until_time': query_filters.get('until'),
        'generated_at': datetime.utcnow().isoformat()
    }

def get_filtered_events(
    limit: int = 100, 
    offset: int = 0,
    since: str = None,
    ip: str = None,
    country: str = None,
    attack_type: str = None
) -> Dict[str, Any]:
    """Get filtered events with pagination"""
    
    filters = {}
    if since:
        filters['since'] = since
    if ip:
        filters['ip'] = ip
    if country:
        filters['country'] = country
    if attack_type:
        filters['type'] = attack_type
    
    events = query_recent(limit=limit, offset=offset, filters=filters)
    
    return {
        'events': events,
        'limit': limit,
        'offset': offset,
        'count': len(events),
        'filters': filters
    }

def get_map_data(since_hours: int = 24, limit: int = 1000, since_time: str = None) -> Dict[str, Any]:
    """Get geolocation data for map visualization"""
    
    # Use provided since_time or calculate from hours
    if since_time:
        since_timestamp = since_time
    else:
        since_timestamp = (datetime.utcnow() - timedelta(hours=since_hours)).isoformat()
    
    map_points = query_map_points(limit=limit, since=since_timestamp)
    
    # Format for Leaflet map
    formatted_points = []
    for point in map_points:
        if point['lat'] != 0 and point['lon'] != 0:
            formatted_points.append({
                'lat': point['lat'],
                'lng': point['lon'],
                'popup': f"IP: {point['ip']}<br>Country: {point['country']}<br>City: {point['city']}<br>Attacks: {point['count']}<br>First: {point['first_seen']}<br>Last: {point['last_seen']}"
            })
    
    return {
        'points': formatted_points,
        'total_points': len(formatted_points),
        'timeframe_hours': since_hours,
        'since_time': since_timestamp
    }

def export_events_csv(filters: Dict[str, Any] = None) -> str:
    """Export filtered events to CSV format"""
    
    events = query_recent(limit=10000, filters=filters or {})
    
    # CSV header
    csv_lines = [
        'timestamp,ip,country,city,attack_type,endpoint,user_agent,form_data'
    ]
    
    # CSV rows
    for event in events:
        form_data = str(event.get('form_data', {})).replace(',', ';')
        user_agent = str(event.get('user_agent', '')).replace(',', ';')
        
        csv_lines.append(
            f"{event.get('timestamp', '')},"
            f"{event.get('client_ip', '')},"
            f"{event.get('country', '')},"
            f"{event.get('city', '')},"
            f"{event.get('attack_type', '')},"
            f"{event.get('endpoint', '')},"
            f"\"{user_agent}\","
            f"\"{form_data}\""
        )
    
    return '\n'.join(csv_lines)

def get_event_detail(event_id: str) -> Dict[str, Any]:
    """Get detailed event information by ID"""
    
    event = get_event_by_id(event_id)
    if not event:
        return {'error': 'Event not found'}
    
    # Add enrichment metadata
    enrichment_info = {
        'geolocation_available': bool(event.get('latitude') and event.get('longitude')),
        'country_detected': bool(event.get('country')),
        'isp_detected': bool(event.get('isp')),
        'user_agent_parsed': bool(event.get('user_agent')),
        'form_data_captured': bool(event.get('form_data'))
    }
    
    return {
        'event': event,
        'enrichment': enrichment_info,
        'raw_size': len(str(event.get('raw_json', {}))),
        'retrieved_at': datetime.utcnow().isoformat()
    }