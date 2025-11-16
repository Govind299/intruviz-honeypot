# 🎯 Manual Attack Testing Guide

## How to Manually Test Attack Detection

The honeypot at **http://127.0.0.1:8080/login** will automatically detect and classify your attacks!

### ✅ Yes! It WILL Detect Your Manual Attacks

When you manually submit attacks through the login form, the honeypot will:
1. ✅ Detect the attack pattern
2. ✅ Classify the attack type
3. ✅ Store it in the database
4. ✅ Display it in the live dashboard

---

## 🧪 Test These Attacks Manually

### 1️⃣ SQL Injection
**Go to:** http://127.0.0.1:8080/login

**Try these in the username field:**
```
admin' OR '1'='1
' OR 1=1--
admin'--
DROP TABLE users--
UNION SELECT * FROM users
```
**Expected Result:** Attack Type = `sql_injection`

---

### 2️⃣ XSS (Cross-Site Scripting)
**Try these in the username field:**
```
<script>alert('XSS')</script>
<img src=x onerror=alert(1)>
javascript:alert(1)
<iframe src="evil.com">
```
**Expected Result:** Attack Type = `xss`

---

### 3️⃣ Command Injection
**Try these in the username field:**
```
admin; ls
user && whoami
admin | cat /etc/passwd
test$(whoami)
```
**Expected Result:** Attack Type = `command_injection`

---

### 4️⃣ LDAP Injection
**Try these in the username field:**
```
admin*)(uid=*
user)(cn=*
admin)(mail=*
```
**Expected Result:** Attack Type = `ldap_injection`

---

### 5️⃣ Admin Unlock Attempt
**Try this:**
- Username: `admin` (or anything)
- Password: `admin123`

**Expected Result:** Attack Type = `admin_unlock`

---

### 6️⃣ Brute Force
**Try these common passwords:**
```
123456
password
admin
qwerty
letmein
welcome
```
**Expected Result:** Attack Type = `brute_force`

---

### 7️⃣ Normal Login Attempt
**Try strong passwords:**
```
MySecureP@ssw0rd!
ComplexPass2024!
SecureLogin#123
```
**Expected Result:** Attack Type = `login_attempt`

---

## 📊 How to Verify Detection

### Method 1: Live Dashboard
1. Open **http://127.0.0.1:5001/live/**
2. Login with operator credentials
3. Watch the **Live Events Feed** - your attacks appear in real-time!
4. Check the **Attack Types** pie chart - it updates with each attack

### Method 2: Database Query
Run this Python script:
```python
import sqlite3
conn = sqlite3.connect('honeypot/data/events.db')
cursor = conn.cursor()
cursor.execute("SELECT timestamp, attack_type, form_data FROM events ORDER BY timestamp DESC LIMIT 10")
for row in cursor.fetchall():
    print(f"{row[0]} | {row[1]} | {row[2]}")
conn.close()
```

---

## 🔥 Quick Test Sequence

**Try this 2-minute test:**

1. Open http://127.0.0.1:8080/login in one tab
2. Open http://127.0.0.1:5001/live/ in another tab
3. Login to the dashboard
4. Go back to the honeypot tab
5. Submit: `admin' OR 1=1--` / `test`
6. Switch to dashboard tab - you'll see it appear with **sql_injection** badge!
7. Try more attacks from the list above
8. Watch them appear in real-time with correct attack types!

---

## 🎨 Attack Type Colors in Dashboard

- **SQL Injection** - Red badge
- **XSS** - Orange badge
- **Command Injection** - Purple badge
- **LDAP Injection** - Pink badge
- **Admin Unlock** - Yellow badge
- **Brute Force** - Blue badge
- **Login Attempt** - Gray badge

---

## ✨ What Happens Behind the Scenes

1. **You submit** the form with attack payload
2. **Honeypot detects** the pattern (SQL, XSS, etc.)
3. **Attack is classified** based on patterns
4. **Stored in database** with attack_type column
5. **Real-time broadcast** via WebSocket to dashboard
6. **Dashboard displays** with colored badge and chart update

---

## 🚀 Pro Tips

- **Mix different attacks** to see variety in the dashboard
- **Use date filter** to view attacks from specific days
- **Check Attack Types chart** to see distribution
- **Click event cards** to see full details
- **Multiple attacks rapidly** will stress-test the real-time feed!

---

## ❓ Troubleshooting

**Q: I don't see my attack in the dashboard**
- Refresh the dashboard page
- Check if date filter is applied (should be in LIVE MODE)
- Logout and login again to start fresh session

**Q: Attack type shows as "unknown"**
- This shouldn't happen anymore - the detection is active
- If it does, restart both honeypot and dashboard

**Q: Attack appears but wrong type**
- The detection checks patterns in order (SQL > XSS > CMD > LDAP > Admin > Brute > Login)
- If input matches multiple patterns, it takes the first match

---

## 🎯 Ready to Test?

**Services Running:**
- 🍯 Honeypot: http://127.0.0.1:8080/login
- 📊 Live Dashboard: http://127.0.0.1:5001/live/

**Go ahead and try manual attacks - they WILL be detected!** 🚀
