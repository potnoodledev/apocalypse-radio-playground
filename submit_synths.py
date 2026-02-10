import base64
import json
import os
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from dotenv import load_dotenv

load_dotenv()
os.chdir(os.path.dirname(os.path.abspath(__file__)))

API_URL = "https://api.apocalypseradio.xyz/graphql"
TOKEN = os.environ["AUTH_TOKEN"]

sections = [
    {
        "section_id": "cmlg5vs6j0008ql01ukedpj5f",
        "wav_file": "synth_intro.wav",
        "filename": "synth_intro.wav",
        "description": "Atmospheric Cm pad with detuned saw oscillators, slow 2-second attack, LFO-modulated filter sweep for movement"
    },
    {
        "section_id": "cmlg5vs6j0009ql01we6kfa07",
        "wav_file": "synth_verse.wav",
        "filename": "synth_verse.wav",
        "description": "Plucky arpeggiated synth: C4-Eb4-G4-C5 pattern at 8th note speed, bright saw tone with fast attack/decay"
    },
    {
        "section_id": "cmlg5vs6j000aql01cvfpbjyj",
        "wav_file": "synth_chorus.wav",
        "filename": "synth_chorus.wav",
        "description": "Full chord stabs (Cm-Ab-Eb-Bb progression) with square wave lead melody (Bb4-C5-Eb5-G4 motif) and vibrato"
    },
    {
        "section_id": "cmlg5vs6j000bql01mnvvbd4s",
        "wav_file": "synth_outro.wav",
        "filename": "synth_outro.wav",
        "description": "Atmospheric Cm pad fading to silence, detuned saw oscillators with LFO filter modulation"
    }
]

for section in sections:
    print(f"\nSubmitting {section['wav_file']} to section {section['section_id']}...")

    # Read and base64 encode
    with open(section["wav_file"], "rb") as f:
        audio_b64 = base64.b64encode(f.read()).decode("utf-8")

    print(f"  Base64 length: {len(audio_b64)}")

    # Build GraphQL mutation
    description_escaped = section["description"].replace('"', '\\"')
    query = f'''mutation {{
  submitTrack(
    sectionId: "{section['section_id']}",
    instrument: "synth",
    audioBase64: "{audio_b64}",
    audioFilename: "{section['filename']}",
    description: "{description_escaped}"
  ) {{
    id
    status
  }}
}}'''

    payload = json.dumps({"query": query}).encode("utf-8")

    req = Request(API_URL, data=payload, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"Bearer {TOKEN}")

    try:
        with urlopen(req, timeout=60) as resp:
            body = resp.read().decode("utf-8")
            print(f"  Response: {body[:500]}")
    except HTTPError as e:
        body = e.read().decode("utf-8")
        print(f"  HTTP Error {e.code}: {body[:500]}")
    except URLError as e:
        print(f"  URL Error: {e.reason}")
