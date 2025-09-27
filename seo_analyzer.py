import requests
import os
from dotenv import load_dotenv
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter
from typing import Dict, List, Tuple
import logging
from bs4 import BeautifulSoup
import spacy

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Load OpenAI API Key
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# --- Load Thresholds from .env ---
PERFORMANCE_THRESHOLD_GOOD = float(os.getenv('PERFORMANCE_THRESHOLD_GOOD', 90)) / 100
PERFORMANCE_THRESHOLD_WARNING = float(os.getenv('PERFORMANCE_THRESHOLD_WARNING', 70)) / 100
LCP_THRESHOLD_GOOD = float(os.getenv('LCP_THRESHOLD_GOOD', 2.5))
LCP_THRESHOLD_WARNING = float(os.getenv('LCP_THRESHOLD_WARNING', 4.0))
FID_THRESHOLD_GOOD = float(os.getenv('FID_THRESHOLD_GOOD', 100))
FID_THRESHOLD_WARNING = float(os.getenv('FID_THRESHOLD_WARNING', 300))
CLS_THRESHOLD_GOOD = float(os.getenv('CLS_THRESHOLD_GOOD', 0.1))
CLS_THRESHOLD_WARNING = float(os.getenv('CLS_THRESHOLD_WARNING', 0.25))

# --- Load spaCy Model ---
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    logger.warning("Downloading en_core_web_sm model for spaCy...")
    spacy.cli.download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

# --- Utility Functions ---
def is_valid_url(url: str) -> bool:
    """Verifica se a URL é válida."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

def generate_recommendations(prompt: str) -> str:
    """Generate recommendations using OpenAI GPT-4o API."""
    api_url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "gpt-4o",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 200,
        "n": 1,
        "temperature": 0.7
    }

    response = requests.post(api_url, headers=headers, json=payload)
    response.raise_for_status()
    result = response.json()
    return result['choices'][0]['message']['content'].strip()


# --- SEO Analyzer Class ---
class SEOAnalyzer:
    """Class to perform SEO analysis of a website."""

    def __init__(self, url: str):
        self.url = url
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def _fetch_url(self, url: str) -> requests.Response:
        # Fetch the URL content
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response

    def get_lighthouse_data(self) -> Dict:
        # Mock implementation for lighthouse data
        return {
            'lighthouse_scores': {'performance': 85},
            'core_vitals': {'FCP': '2.0s', 'LCP': '2.5s', 'CLS': '0.1'},
            'opportunities': {'Blocking Resources (ms)': 100, 'Unused CSS (bytes)': 2000}
        }

    def get_technical_audit(self) -> Dict:
        # Mock implementation for technical audit
        return {
            'meta': {'description': 'Example description'},
            'headings': {'h1': 1, 'h2': 3},
            'links': {'total': 10, 'internal': 5, 'external': 5, 'broken': 1},
            'images': {'total': 5, 'missing_alt': 2, 'large_images': [{'url': 'example.com/image1.jpg', 'size': '500KB'}]}
        }

    def analyze_keywords(self, content: str) -> Dict:
        # Mock implementation for keyword analysis
        return {'keyword_metrics': [{'keyword': 'example', 'count': 5}]}

    def analyze_ada_compliance(self, soup: BeautifulSoup) -> Dict:
        # Mock implementation for ADA compliance
        return {'images': 2, 'headings': 1, 'links': 1, 'forms': 1}

    def get_ai_recommendations(self, data: Dict) -> str:
        # Generate recommendations using OpenAI GPT-4 API
        prompt = "Generate SEO recommendations based on the following data: " + str(data)
        return generate_recommendations(prompt)

    def _generate_fallback_recommendations(self, data: Dict) -> str:
        recommendations = []

        # Performance recommendations
        perf_score = data.get('lighthouse_scores', {}).get('performance', 0)
        if perf_score < 90:
            recommendations.append("🚀 **Performance Improvements Needed:**")
            opportunities = data.get('opportunities', {})
            if opportunities.get('Blocking Resources (ms)', 0) > 0:
                recommendations.append("- Optimize render-blocking resources to improve page load time.")
            if opportunities.get('Unused CSS (bytes)', 0) > 0:
                recommendations.append("- Remove unused CSS to reduce page size and improve load speed.")
                
        # Keyword recommendations
        keyword_analysis = data.get('keyword_analysis', {})
        if keyword_analysis:
            recommendations.append("\n📝 **Keyword Optimization:**")
            focus_keywords = keyword_analysis.get('focus_keywords', [])
            if focus_keywords:
                recommendations.append(f"- Optimize content for main keywords: {', '.join(focus_keywords[:3])}. Use these keywords naturally in headings, body text, and meta descriptions.")
            else:
                recommendations.append("- No focus keywords identified. Review content and identify relevant keywords.")
                
        # Technical recommendations
        recommendations.append("\n🔧 **Technical Improvements:**")
        
        # Safely check for meta description
        meta_info = data.get('meta', {})
        if not meta_info.get('description'):
            recommendations.append("- Add a meta description to improve search engine visibility.")
        
        # Check for broken links
        links_info = data.get('links', {})
        if links_info.get('broken', 0) > 0:
            recommendations.append(f"- Fix {links_info.get('broken', 0)} broken links to improve user experience and SEO.")
        
        # Check for ADA issues
        ada_issues = data.get('ada_compliance', {})
        if ada_issues:
            recommendations.append("\n♿ **Accessibility Improvements:**")
            if ada_issues.get('images', 0) > 0:
                recommendations.append(f"- Add alt text to {ada_issues.get('images', 0)} images to improve accessibility.")
            if ada_issues.get('headings', 0) > 0:
                recommendations.append(f"- Review heading structure for {ada_issues.get('headings', 0)} issues to ensure proper hierarchy.")
            if ada_issues.get('links', 0) > 0:
                recommendations.append(f"- Fix {ada_issues.get('links', 0)} link issues to improve navigation.")
            if ada_issues.get('forms', 0) > 0:
                recommendations.append(f"- Address {ada_issues.get('forms', 0)} form issues to improve usability.")
        
        return "\n".join(recommendations)