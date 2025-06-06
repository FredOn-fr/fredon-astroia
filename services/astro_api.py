import requests
import os
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth

load_dotenv()

ASTRO_API_KEY = os.getenv("ASTROLOGYAPI_API_KEY")
ASTRO_API_USERID = os.getenv("ASTROLOGYAPI_USER_ID")
BASE_URL = "https://json.astrologyapi.com/v1/"

AUTH = HTTPBasicAuth(ASTRO_API_USERID, ASTRO_API_KEY)
HEADERS = {
    "Content-Type": "application/json"
}

def get_natal_wheel_chart(data):
    response = requests.post(
        url=BASE_URL + "natal_wheel_chart",
        auth=AUTH,
        headers=HEADERS,
        json=data
    )
    return response.json() if response.status_code == 200 else None

def get_planet_positions(data):
    response = requests.post(
        url=BASE_URL + "planets/tropical",
        auth=AUTH,
        headers=HEADERS,
        json=data
    )
    return response.json() if response.status_code == 200 else None

def get_aspects(data):
    response = requests.post(
        url=BASE_URL + "western_horoscope",
        auth=AUTH,
        headers=HEADERS,
        json=data
    )
    return response.json() if response.status_code == 200 else None
