import os
import logging
from dotenv import load_dotenv
import spacy
from openai import OpenAI

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Load Environment Variables ---
load_dotenv()

# --- API Clients ---
def init_openai_client():
    """Initialize and return OpenAI client."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OpenAI API key not found.")
        return None
    
    try:
        client = OpenAI(api_key=api_key)
        return client
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI client: {e}")
        return None

openai_client = init_openai_client()

# --- Load Thresholds from .env ---
PERFORMANCE_THRESHOLD_GOOD = float(os.getenv('PERFORMANCE_THRESHOLD_GOOD', 0.90))
PERFORMANCE_THRESHOLD_WARNING = float(os.getenv('PERFORMANCE_THRESHOLD_WARNING', 0.50))
LCP_THRESHOLD_GOOD = float(os.getenv('LCP_THRESHOLD_GOOD', 2.5))
LCP_THRESHOLD_WARNING = float(os.getenv('LCP_THRESHOLD_WARNING', 4.0))
FID_THRESHOLD_GOOD = float(os.getenv('FID_THRESHOLD_GOOD', 100))
FID_THRESHOLD_WARNING = float(os.getenv('FID_THRESHOLD_WARNING', 300))
CLS_THRESHOLD_GOOD = float(os.getenv('CLS_THRESHOLD_GOOD', 0.1))
CLS_THRESHOLD_WARNING = float(os.getenv('CLS_THRESHOLD_WARNING', 0.25))
MODEL_NAME = os.getenv('MODEL_NAME', 'gpt-4o')
MAX_TOKENS = int(os.getenv('MAX_TOKENS', 1000))
TEMPERATURE = float(os.getenv('TEMPERATURE', 0.7))

# --- Load spaCy Model ---
def load_spacy_model():
    """Load spaCy model or download if not available."""
    try:
        model = spacy.load("en_core_web_sm")
        logger.info("Loaded spaCy model successfully.")
        return model
    except OSError:
        logger.warning("Downloading spaCy model...")
        import subprocess
        subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
        model = spacy.load("en_core_web_sm")
        logger.info("Downloaded and loaded spaCy model successfully.")
        return model

nlp = load_spacy_model()

# --- Utility Functions ---
def is_valid_url(url: str) -> bool:
    """Verifies if a URL is valid."""
    from urllib.parse import urlparse
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

def get_metric_color(value, good_threshold, warning_threshold):
    """Determines the color based on the metric value against specified thresholds."""
    if value is None:
        return "poor-score"
    try:
        if value <= good_threshold:
            return "good-score"
        elif value <= warning_threshold:
            return "warning-score"
        else:
            return "poor-score"
    except TypeError:
        logger.error(f"Type error comparing values: value={value}, good={good_threshold}, warning={warning_threshold}")
        return "poor-score"

def extract_numeric_value(value):
    """Extracts and converts a numeric value from a string, handling different units."""
    if value == 'N/A' or value is None:
        return None
    
    try:
        if isinstance(value, (int, float)):
            return float(value)
        elif " s" in value:
            return float(value.replace(" s", ""))
        elif " ms" in value:
            return float(value.replace(" ms", "").replace(",", "")) / 1000  # Convert to seconds
        else:
            return float(value)
    except (ValueError, TypeError) as e:
        logger.error(f"Failed to convert value: {value}, Error: {e}")
        return None

# --- Check configuration ---
def check_configuration():
    """Verify that all required components are properly configured."""
    config_status = {
        "openai": openai_client is not None,
        "spacy": nlp is not None,
        "page_speed_api": os.getenv("PAGE_SPEED_API_KEY") is not None
    }
    
    for key, status in config_status.items():
        logger.info(f"Configuration check for {key}: {'OK' if status else 'FAILED'}")
    
    return all(config_status.values())

# Run configuration check at import time
config_valid = check_configuration()
