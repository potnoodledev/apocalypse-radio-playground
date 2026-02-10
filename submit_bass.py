import base64
import json
import sys
import os
import urllib.request
import urllib.error
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://api.apocalypseradio.xyz/graphql"
AUTH_TOKEN = os.environ["AUTH_TOKEN"]

SECTIONS = [
    {
        "id": "cmlg5vs6j0008ql01ukedpj5f",
        "file": "bass_intro.wav",
        "name": "intro",
        "description": "Subtle sub bass drone on C2 with slow fade-in, setting the dark atmosphere"
    },
    {
        "id": "cmlg5vs6j0009ql01we6kfa07",
        "file": "bass_verse.wav",
        "name": "verse",
        "description": "Driving synthwave saw bass pattern C2-C2-Eb2-F2 with low-pass filter, one beat per note"
    },
    {
        "id": "cmlg5vs6j000aql01cvfpbjyj",
        "file": "bass_chorus.wav",
        "name": "chorus",
        "description": "Full saw bass arpeggio C2-G2-Ab2-F2-Eb2-F2-G2-C3 with filter sweep from 400-900Hz"
    },
    {
        "id": "cmlg5vs6j000bql01mnvvbd4s",
        "file": "bass_outro.wav",
        "name": "outro",
        "description": "Sustained C2 saw bass with sub-sine layer, fading out over 8 seconds"
    },
]


def submit_track(section):
    print(f"\nSubmitting {section['name']}...")

    # Read and base64 encode the WAV file
    with open(section["file"], "rb") as f:
        audio_data = f.read()
    audio_b64 = base64.b64encode(audio_data).decode("utf-8")

    print(f"  File size: {len(audio_data)} bytes, Base64 length: {len(audio_b64)}")

    # Build GraphQL mutation
    desc = section["description"]
    query = """mutation {
  submitTrack(
    sectionId: "%s",
    instrument: "bass",
    audioBase64: "%s",
    audioFilename: "bass_%s.wav",
    description: "%s"
  ) {
    id
    status
  }
}""" % (section['id'], audio_b64, section['name'], desc)

    payload = json.dumps({"query": query}).encode("utf-8")

    req = urllib.request.Request(
        API_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {AUTH_TOKEN}",
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            resp_text = response.read().decode("utf-8")
            print(f"  Response: {resp_text[:500]}")

            resp = json.loads(resp_text)
            if "errors" in resp:
                print(f"  ERROR: {resp['errors']}")
                return False
            if "data" in resp and resp["data"].get("submitTrack"):
                track = resp["data"]["submitTrack"]
                print(f"  SUCCESS: Track ID={track['id']}, Status={track['status']}")
                return True
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        print(f"  HTTP Error {e.code}: {body[:500]}")
        return False
    except urllib.error.URLError as e:
        print(f"  URL Error: {e.reason}")
        return False
    except Exception as e:
        print(f"  Error: {e}")
        return False

    return False


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    success_count = 0
    for section in SECTIONS:
        if submit_track(section):
            success_count += 1

    print(f"\n{'='*50}")
    print(f"Submitted {success_count}/{len(SECTIONS)} bass tracks successfully")

    if success_count < len(SECTIONS):
        sys.exit(1)
