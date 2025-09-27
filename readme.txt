pip install flask flask-cors flask-limiter beautifulsoup4 requests spacy python-dotenv
python -m spacy download en_core_web_sm
PAGESPEED_API_KEY=your_google_api_key
HF_API_KEY=your_huggingface_api_key
DEBUG=False
PORT=5000
/project
  /static
    script.js
    styles.css
    logo.jpg
  /templates
    index.html
  app.py
  seo_analyzer.py
  .env
python app.py
heck HuggingFace credentials and tokens