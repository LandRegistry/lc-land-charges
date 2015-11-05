import os
import requests

url = os.getenv('LAND_CHARGES_URI', 'http://localhost:5004')
requests.delete(url + '/registrations')
