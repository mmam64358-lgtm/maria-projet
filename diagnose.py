import urllib.request, json

# Test 1: Login page
try:
    r = urllib.request.urlopen('http://127.0.0.1:5500/login')
    print('LOGIN PAGE:', r.status)
except Exception as e:
    print('LOGIN PAGE ERROR:', e)

# Test 2: API health
try:
    r = urllib.request.urlopen('http://127.0.0.1:5500/api/health')
    print('API HEALTH:', json.loads(r.read()))
except Exception as e:
    print('API HEALTH ERROR:', e)

# Test 3: Alerts API
try:
    r = urllib.request.urlopen('http://127.0.0.1:5500/api/alerts')
    data = json.loads(r.read())
    print('ALERTS count:', len(data))
    if data:
        print('  First:', {k: data[0][k] for k in ['id','status','severity','lat','lng'] if k in data[0]})
except Exception as e:
    print('ALERTS API ERROR:', e)

# Test 4: Units API
try:
    r = urllib.request.urlopen('http://127.0.0.1:5500/api/units')
    data = json.loads(r.read())
    print('UNITS count:', len(data))
except Exception as e:
    print('UNITS API ERROR:', e)

# Test 5: Stats
try:
    r = urllib.request.urlopen('http://127.0.0.1:5500/api/stats')
    print('STATS:', json.loads(r.read()))
except Exception as e:
    print('STATS ERROR:', e)

# Test 6: script.js syntax check
try:
    r = urllib.request.urlopen('http://127.0.0.1:5500/static/js/script.js')
    content = r.read().decode()
    print('SCRIPT.JS size:', len(content), 'bytes')
    print('  function setMode present:', 'function setMode' in content)
    print('  function setHiddenPanels present:', 'function setHiddenPanels' in content)
    print('  L.map present:', 'L.map(' in content)
    # Count open/close braces to detect unbalanced
    opens = content.count('{')
    closes = content.count('}')
    print('  Braces: { =', opens, '} =', closes, '-> balanced:', opens == closes)
except Exception as e:
    print('SCRIPT.JS ERROR:', e)
