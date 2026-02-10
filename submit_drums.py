import requests
import base64
import os
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://api.apocalypseradio.xyz/graphql"
AUTH_TOKEN = os.environ["AUTH_TOKEN"]

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {AUTH_TOKEN}"
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

sections = [
    {
        "section_id": "cmlg5vs6j0008ql01ukedpj5f",
        "filename": "drums_intro.wav",
        "description": "Light hi-hats building atmosphere, starting soft and gradually increasing in volume with occasional open hats in the second half"
    },
    {
        "section_id": "cmlg5vs6j0009ql01we6kfa07",
        "filename": "drums_verse.wav",
        "description": "Classic electronic beat with kick on 1 and 3, snare on 2 and 4, closed hi-hats on eighth notes"
    },
    {
        "section_id": "cmlg5vs6j000aql01cvfpbjyj",
        "filename": "drums_chorus.wav",
        "description": "Energetic four-on-the-floor kick pattern with snare on 2 and 4, open hi-hats on off-beats, snare fills every 4th bar"
    },
    {
        "section_id": "cmlg5vs6j000bql01mnvvbd4s",
        "filename": "drums_outro.wav",
        "description": "Gradually fading drum pattern, elements dropping out progressively as the track winds down"
    },
]

for section in sections:
    filepath = os.path.join(BASE_DIR, section["filename"])
    with open(filepath, "rb") as f:
        audio_b64 = base64.b64encode(f.read()).decode("utf-8")

    mutation = """
    mutation($sectionId: String!, $instrument: String!, $audioBase64: String!, $audioFilename: String!, $description: String!) {
        submitTrack(sectionId: $sectionId, instrument: $instrument, audioBase64: $audioBase64, audioFilename: $audioFilename, description: $description) {
            id
            status
        }
    }
    """

    variables = {
        "sectionId": section["section_id"],
        "instrument": "drums",
        "audioBase64": audio_b64,
        "audioFilename": section["filename"],
        "description": section["description"]
    }

    payload = {
        "query": mutation,
        "variables": variables
    }

    print(f"Submitting {section['filename']}...")
    resp = requests.post(API_URL, json=payload, headers=HEADERS, timeout=60)
    print(f"  Status: {resp.status_code}")
    print(f"  Response: {resp.text[:500]}")
    print()

print("All drum tracks submitted!")
