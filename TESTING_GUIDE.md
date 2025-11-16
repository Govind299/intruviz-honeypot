# How to Test the Live Events Feed Implementation

## Prerequisites
Make sure all dependencies are installed:
```powershell
cd intruviz-honeypot
pip install -r requirements.txt
```

## Step-by-Step Testing Guide

### Step 1: Start the Operator Dashboard
Open a terminal and run:
```powershell
cd intruviz-honeypot
python backend/operator_app.py
```

You should see:
```
HONEYPOT OPERATOR DASHBOARD - MODULE D
==================================================
WARNING: [Security warning message]
Operator Password: operator123
Dashboard URL: http://0.0.0.0:5001/operator
API Base URL: http://0.0.0.0:5001/api
WebSocket: ws://0.0.0.0:5001/ws/events
==================================================
```

### Step 2: Login to the Dashboard
1. Open your browser and go to: `http://localhost:5001/operator/login`
2. Enter password: `operator123` (or your configured password)
3. You should be redirected to the dashboard
4. **Note the login time** displayed in the top-right corner

### Step 3: Verify Initial State
At this point, you should see:
- ✅ Login time displayed in header
- ✅ Blue info banner saying "Showing only attacks that occurred after your login time"
- ✅ Empty or minimal events in the Live Events Feed (since you just logged in)
- ✅ Status showing "Real-time: Connected"

### Step 4: Start the Honeypot (in a new terminal)
```powershell
cd intruviz-honeypot
python honeypot/webapp.py
```

You should see:
```
HONEYPOT WEB APPLICATION - MODULE A
==================================================
Flask app running on: http://0.0.0.0:8080
==================================================
```

### Step 5: Generate Some Attacks
In another terminal, run:
```powershell
cd intruviz-honeypot
python test_attacks.py
```

This will simulate various attacks against the honeypot.

### Step 6: Verify Real-time Updates
**Watch the operator dashboard (NO REFRESH NEEDED!):**

You should see:
- ✅ New events appearing at the TOP of the Live Events Feed
- ✅ Events have a green "new" animation when they appear
- ✅ Events show immediately (within 1-2 seconds of attack)
- ✅ Stats update automatically every 2 seconds
- ✅ Map shows new attack origins
- ✅ Charts update with new data
- ✅ "Total Events" counter increases
- ✅ "Last Attack" time updates

**Important:** You should NOT need to refresh your browser!

### Step 7: Test Historical Data Access
Now let's verify you can see past records:

1. In the filters section, click the "From date/time" field
2. Select a date/time from BEFORE you logged in (e.g., yesterday)
3. Click "Apply Filters"

You should see:
- ✅ Events from before your login time now appear
- ✅ The filter is applied and showing historical data

4. Click "Clear" button

You should see:
- ✅ Events list returns to showing only post-login events
- ✅ Historical events are hidden again

### Step 8: Run Automated Tests
To verify the backend is working correctly:
```powershell
cd intruviz-honeypot
python test_live_events.py
```

This will test:
- Login and session tracking
- Default filtering by login time
- Custom filter override
- Stats API filtering

## Expected Results Checklist

### ✅ Default Behavior (After Login)
- [ ] Login time is displayed in header
- [ ] Live Events Feed shows info banner about filtering
- [ ] Only events AFTER login time are shown by default
- [ ] Empty or minimal events if no attacks occurred yet

### ✅ Real-time Updates
- [ ] New attacks appear within 1-2 seconds
- [ ] No manual browser refresh needed
- [ ] Events animate in with "new" badge
- [ ] Stats update automatically
- [ ] Map updates with new locations
- [ ] WebSocket status shows "Connected"

### ✅ Historical Data Access
- [ ] Datetime filter allows selecting past dates
- [ ] Applying past datetime shows historical events
- [ ] Events from before login become visible
- [ ] Clear button returns to default (post-login only)

### ✅ Filter Functionality
- [ ] IP filter works
- [ ] Country filter works  
- [ ] Attack type filter works
- [ ] Datetime filter works
- [ ] Multiple filters can be combined
- [ ] Export CSV respects filters

## Troubleshooting

### Events not appearing in real-time?
1. Check WebSocket status (top bar should say "Connected")
2. Check browser console for errors (F12)
3. Verify honeypot is running and receiving attacks
4. Check that both services are on same machine/network

### Seeing ALL events (not filtered by login time)?
1. Check that you logged in (not just accessed without auth)
2. Check browser console for login time
3. Verify session is active
4. Try logging out and back in

### No historical data when using datetime filter?
1. Make sure you have events in database before login time
2. Check datetime format is correct
3. Try selecting a date far in the past (e.g., last week)
4. Check database has events: `sqlite3 honeypot.db "SELECT COUNT(*) FROM events;"`

## Advanced Testing

### Test Multiple Operators
1. Open dashboard in multiple browser tabs/windows
2. Login with each
3. Run attacks
4. Verify all dashboards update in real-time

### Test Load
1. Run continuous attacks: `python run_attacks.py`
2. Verify dashboard handles high event volume
3. Check that throttling prevents UI lag

### Test Persistence
1. Login and note the login time
2. Generate some attacks
3. Logout
4. Login again (new login time!)
5. Verify only events after NEW login time are shown
6. Use filters to see events from previous session

## What to Report

If everything works:
✅ "All tests passed! Real-time events are working perfectly."

If issues found:
- Which step failed
- Error messages (from browser console or terminal)
- Screenshots if UI issues
- Browser and version used
