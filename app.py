from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from seo_analyzer import SEOAnalyzer
import logging
import os

app = Flask(__name__)
CORS(app)
limiter = Limiter(app=app, key_func=get_remote_address)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/analyze', methods=['POST'])
@limiter.limit("5/minute")
def analyze():
    try:
        # Verify HF_API_KEY is set
        if not os.getenv('HF_API_KEY'):
            raise ValueError("Hugging Face API key not configured")
            
        url = request.json['url']
        analyzer = SEOAnalyzer(url)
        
        performance_data = analyzer.get_real_performance_data()
        
        try:
            recommendations = analyzer.get_ai_recommendations(performance_data)
        except Exception as e:
            logging.error(f"AI recommendations failed: {str(e)}")
            recommendations = "Unable to generate AI recommendations at this time."
        
        return jsonify({
            'performance': performance_data['scores'],
            'core_vitals': performance_data['core_vitals'],
            'opportunities': performance_data['opportunities'],
            'recommendations': recommendations
        })
    
    except KeyError:
        return jsonify({'error': 'Missing URL parameter'}), 400
    except Exception as e:
        logging.error(f"Analysis failed: {str(e)}")
        return jsonify({'error': 'Analysis failed. Try again later.'}), 500

if __name__ == '__main__':
    app.run(debug=os.getenv('DEBUG', 'false').lower() == 'true')