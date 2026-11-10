"""Gnani Vachana adapter: Prisma v2.5 (STT) + Timbre v2.5 (TTS).
Endpoints/fields follow docs.gnani.ai (STT REST /stt/v3, TTS REST /api/v1/tts/inference).
Auth: single header X-API-Key-ID. Key lives only in backend env."""
import os, shutil, subprocess
import httpx
from fastapi import HTTPException

BASE = os.getenv("GNANI_BASE_URL", "https://api.vachana.ai")


def _key() -> str:
    k = os.getenv("GNANI_API_KEY")
    if not k:
        raise HTTPException(503, "GNANI_API_KEY is not set in backend/.env")
    return k


def to_wav(audio: bytes) -> bytes:
    """Browser MediaRecorder gives webm/opus, which Prisma doesn't list as supported
    (WAV, MP3, OGG, FLAC, AAC, M4A). Convert to 16 kHz mono WAV with FFmpeg."""
    if not shutil.which("ffmpeg"):
        raise HTTPException(500, "FFmpeg not found. Install FFmpeg and add it to PATH.")
    p = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", "pipe:0", "-ar", "16000", "-ac", "1",
                        "-f", "wav", "pipe:1"], input=audio, capture_output=True)
    if p.returncode != 0 or not p.stdout:
        raise HTTPException(400, "Could not decode audio: " + p.stderr.decode()[:200])
    return p.stdout


def _stt_form(lang: str) -> dict:
    form = {"language_code": lang}  # no model => Prisma v2.5 (default)
    if os.getenv("GNANI_STT_MODEL"):      # e.g. prisma-v3.0
        form["model"] = os.getenv("GNANI_STT_MODEL")
    if os.getenv("GNANI_STT_FORMAT"):     # prisma-v3.0 only: transcribe | transliterate (Latin Hinglish)
        form["format"] = os.getenv("GNANI_STT_FORMAT")
    return form


async def transcribe(audio: bytes, language: str | None = None) -> str:
    wav = to_wav(audio)
    lang = language or os.getenv("GNANI_STT_LANGUAGE", "hi-IN")  # hi-IN handles Hindi+English mix
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.post(f"{BASE}/stt/v3", headers={"X-API-Key-ID": _key()},
                         files={"audio_file": ("rec.wav", wav, "audio/wav")},
                         data=_stt_form(lang))
    if r.status_code != 200:
        raise HTTPException(502, f"Prisma error {r.status_code}: {r.text[:300]}")
    body = r.json()
    return (body.get("transcript") or body.get("text") or "").strip()


async def speak(text: str, language: str | None = None) -> bytes:
    payload = {
        "text": text,
        "model": os.getenv("GNANI_TTS_MODEL", "timbre-v2.5"),
        "voice": os.getenv("GNANI_TTS_VOICE", "Nalini"),
        "language": language or os.getenv("GNANI_TTS_LANGUAGE", "hi-IN"),
        "speed": 1.0,
        "audio_config": {"sample_rate": 24000, "num_channels": 1, "sample_width": 2,
                         "encoding": "linear_pcm", "container": "wav"},
    }
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.post(f"{BASE}/api/v1/tts/inference",
                         headers={"X-API-Key-ID": _key(), "Content-Type": "application/json"},
                         json=payload)
    if r.status_code != 200:
        raise HTTPException(502, f"Timbre error {r.status_code}: {r.text[:300]}")
    return r.content  # raw binary WAV
