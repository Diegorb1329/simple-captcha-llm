"""Configuration constants for SAT Certificate Lookup."""

from pathlib import Path

# Paths
DEFAULT_URL = "https://portalsat.plataforma.sat.gob.mx/RecuperacionDeCertificados/faces/recuperaRFC.xhtml"
DEFAULT_INPUT = Path(__file__).parent.parent / "input" / "rfcs.csv"
DEFAULT_OUTPUT = Path(__file__).parent.parent / "outputs"

# Captcha prompts (case-sensitive)
CAPTCHA_PROMPTS = [
    """You are an ancient scribe deciphering weathered manuscripts.
CRITICAL: Preserve the EXACT case - uppercase stays uppercase, lowercase stays lowercase.
Speak only the characters you see, nothing more.""",
    
    """Master of calligraphy, see through the distortion to the truth beneath.
IMPORTANT: Case matters! Capital letters are taller, lowercase are smaller.
Respond with only the word itself, nothing else.""",
    
    """Oracle of Symbols, what word reveals itself through the noise?
REMEMBER: Uppercase and lowercase are different - preserve exact case.
Whisper only the characters, no explanation.""",
]

PROMPT_NAMES = ["ancient_scribe", "calligraphy_master", "oracle_vision"]

# CSS selectors
CAPTCHA_IMAGE_SELECTORS = ["img[src*='captcha']", "img[src*='Captcha']", "img[src*='jcaptcha']"]
RFC_INPUT_SELECTORS = ["input[id='consultaCertificados:entradaRFC']", "input[id*='entradaRFC']", "input[id*='rfc']"]
CAPTCHA_INPUT_SELECTORS = ["input[id='consultaCertificados:verCaptchaRFC']", "input[id*='verCaptcha']", "input[id*='Captcha'][type='text']"]
SEARCH_BUTTON_SELECTORS = ["input[id='consultaCertificados:botonRFC']", "input[id*='botonRFC']"]

CSV_FIELDNAMES = ["rfc", "razon_social", "numero_serie", "estado", "tipo", "fecha_inicial", "fecha_final", "url_certificado"]
