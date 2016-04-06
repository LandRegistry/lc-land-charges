import requests, json, os, sys

LAND_CHARGES_URI = os.getenv('LAND_CHARGES_URL', 'http://localhost:5004')
url = LAND_CHARGES_URI + '/registrations'
for item in sys.argv[1:]:
    url += '/' + item

get = requests.get(url)
print(json.dumps(get.json(), indent=4))
