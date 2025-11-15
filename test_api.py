import requests

API_KEY = "6910ce5a4c184b44b39803b73fd72bf5"
test_ip = "8.8.8.8"

print("Testing ipgeolocation.io API")
print(f"API Key: {API_KEY[:10]}...")
print(f"Test IP: {test_ip}")
print()

try:
    response = requests.get(f"https://api.ipgeolocation.io/ipgeo?apiKey={API_KEY}&ip={test_ip}", timeout=10)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("API Test Successful!")
        print(f"Country: {data.get('country_name', 'Unknown')}")
        print(f"Region: {data.get('state_prov', 'Unknown')}")
        print(f"City: {data.get('city', 'Unknown')}")
        print(f"ISP: {data.get('isp', 'Unknown')}")
        print(f"Organization: {data.get('organization', 'Unknown')}")
        print(f"Continent: {data.get('continent_name', 'Unknown')}")
    else:
        print(f"API Error: {response.text}")
        
except Exception as e:
    print(f"Request failed: {e}")