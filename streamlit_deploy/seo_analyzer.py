import requests
import json
from bs4 import BeautifulSoup
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List
from urllib.parse import urljoin
import logging

# Import configuration
from config import (
    nlp, openai_client, logger, 
    MODEL_NAME, MAX_TOKENS, TEMPERATURE,
    extract_numeric_value
)

class SEOAnalyzer:
    """Class to perform SEO analysis of a website."""

    def __init__(self, url: str):
        """Initialize the SEO analyzer with a URL and configuration."""
        self.url = url
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.openai_cache = {}

    def _fetch_url(self, url: str) -> requests.Response:
        """Performs an HTTP GET request to the given URL."""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching URL: {e}")
            return None

    def _get_pagespeed_api_url(self, strategy: str = 'mobile', page_speed_api_key: str = None) -> str:
        """Constructs the PageSpeed Insights API URL."""
        from config import os
        return (
            f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
            f"?url={self.url}"
            f"&key={page_speed_api_key or os.getenv('PAGE_SPEED_API_KEY')}"
            f"&category=ACCESSIBILITY"
            f"&category=BEST_PRACTICES"
            f"&category=PERFORMANCE"
            f"&category=SEO"
            f"&strategy={strategy}"
        )

    def get_lighthouse_data(self) -> Dict:
        """Fetches data from PageSpeed Insights for mobile and desktop strategies."""
        strategies = ['mobile', 'desktop']
        best_scores = {
            'performance': 0,
            'accessibility': 0,
            'best-practices': 0,
            'seo': 0
        }
        lighthouse_data = None  # Store the last successful lighthouse data

        for strategy in strategies:
            api_url = self._get_pagespeed_api_url(strategy)
            response = self._fetch_url(api_url)
            if not response:
                continue

            data = response.json()
            lighthouse = data.get('lighthouseResult', {})
            lighthouse_data = lighthouse  # Save the latest data
            categories = lighthouse.get('categories', {})

            # Correctly capture best-practices score
            if 'best-practices' in categories:
                score = float(categories['best-practices'].get('score', 0)) * 100
                best_scores['best-practices'] = max(best_scores['best-practices'], score)

            # Capture scores for other categories
            for metric in ['performance', 'accessibility', 'seo']:
                if metric in categories:
                    score = float(categories[metric].get('score', 0)) * 100
                    best_scores[metric] = max(best_scores[metric], score)

        # Get core vitals and opportunities from the latest lighthouse data
        core_vitals = {
            'First Contentful Paint': 'N/A',
            'Speed Index': 'N/A',
            'Largest Contentful Paint': 'N/A',
            'Time to Interactive': 'N/A',
            'Total Blocking Time': 'N/A',
            'Cumulative Layout Shift': 'N/A'
        }
        
        opportunities = {
            'Blocking Resources (ms)': 0,
            'Unminified CSS (bytes)': 0,
            'Unminified JS (bytes)': 0,
            'Unused CSS (bytes)': 0,
            'Unused JS (bytes)': 0
        }
        
        if lighthouse_data:
            audits = lighthouse_data.get('audits', {})
            
            # Extract core vitals
            if 'first-contentful-paint' in audits:
                core_vitals['First Contentful Paint'] = audits['first-contentful-paint'].get('displayValue', 'N/A')
            if 'speed-index' in audits:
                core_vitals['Speed Index'] = audits['speed-index'].get('displayValue', 'N/A')
            if 'largest-contentful-paint' in audits:
                core_vitals['Largest Contentful Paint'] = audits['largest-contentful-paint'].get('displayValue', 'N/A')
            if 'interactive' in audits:
                core_vitals['Time to Interactive'] = audits['interactive'].get('displayValue', 'N/A')
            if 'total-blocking-time' in audits:
                core_vitals['Total Blocking Time'] = audits['total-blocking-time'].get('displayValue', 'N/A')
            if 'cumulative-layout-shift' in audits:
                core_vitals['Cumulative Layout Shift'] = audits['cumulative-layout-shift'].get('displayValue', 'N/A')
            
            # Extract opportunities
            if 'render-blocking-resources' in audits:
                details = audits['render-blocking-resources'].get('details', {})
                opportunities['Blocking Resources (ms)'] = details.get('overallSavingsMs', 0) or 0
            if 'unminified-css' in audits:
                details = audits['unminified-css'].get('details', {})
                opportunities['Unminified CSS (bytes)'] = details.get('overallSavingsBytes', 0) or 0
            if 'unminified-javascript' in audits:
                details = audits['unminified-javascript'].get('details', {})
                opportunities['Unminified JS (bytes)'] = details.get('overallSavingsBytes', 0) or 0
            if 'unused-css-rules' in audits:
                details = audits['unused-css-rules'].get('details', {})
                opportunities['Unused CSS (bytes)'] = details.get('overallSavingsBytes', 0) or 0
            if 'unused-javascript' in audits:
                details = audits['unused-javascript'].get('details', {})
                opportunities['Unused JS (bytes)'] = details.get('overallSavingsBytes', 0) or 0

        return {
            'lighthouse_scores': best_scores,
            'core_vitals': core_vitals,
            'opportunities': opportunities
        }

    def get_technical_audit(self) -> Dict:
        """Performs a technical SEO audit, analyzing headers, meta tags, links, and images."""
        response = self._fetch_url(self.url)
        if not response:
            return {}

        soup = BeautifulSoup(response.content, 'html.parser')

        headings = {f"H{i}": len(soup.find_all(f'h{i}')) for i in range(1, 7)}

        meta = {
            'title': soup.title.string if soup.title else None,
            'description': soup.find('meta', {'name': 'description'})['content'] if soup.find('meta', {'name': 'description'}) else None,
            'robots': soup.find('meta', {'name': 'robots'})['content'] if soup.find('meta', {'name': 'robots'}) else None,
            'canonical': soup.find('link', {'rel': 'canonical'})['href'] if soup.find('link', {'rel': 'canonical'}) else None,
            'og_tags': {tag['property']: tag['content'] for tag in soup.find_all('meta', property=True) if tag['property'].startswith('og:')}
        }

        links = soup.find_all('a', href=True)
        internal, external, broken = self._analyze_links(links)

        images = soup.find_all('img')
        image_data = self._analyze_images(images)

        return {
            'meta': meta,
            'headings': headings,
            'links': {
                'total': len(links),
                'internal': len(internal),
                'external': len(external),
                'broken': broken
            },
            'images': image_data,
            'soup': soup  # Return soup for further analysis
        }

    def _analyze_links(self, links: List) -> tuple:
        """Analyzes page links, classifying them as internal, external, or broken."""
        internal, external, broken = [], [], []
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(self._check_link, link['href']): link['href'] for link in links}
            for future in as_completed(futures):
                href = futures[future]
                try:
                    result = future.result()
                    if result == 'broken':
                        broken.append(href)
                    elif self.url in href:
                        internal.append(href)
                    else:
                        external.append(href)
                except Exception as e:
                    logger.error(f"Error checking link {href}: {e}")
                    broken.append(href)
        return internal, external, broken

    def _check_link(self, href: str) -> str:
        """Checks if a link is broken."""
        if not href.startswith(('http', 'https')):
            href = urljoin(self.url, href)
        try:
            response = requests.head(href, allow_redirects=True, headers=self.headers, timeout=5)
            if response.status_code >= 400:
                return 'broken'
            return 'ok'
        except Exception as e:
            logger.error(f"Error checking link {href}: {e}")
            return 'broken'

    def _analyze_images(self, images: List) -> Dict:
        """Analyzes page images, checking for alt attributes and size."""
        image_data = {
            'total': len(images),
            'missing_alt': 0,
            'large_images': []
        }
        for img in images:
            if not img.get('alt'):
                image_data['missing_alt'] += 1
            src = img.get('src')
            if src:
                try:
                    img_url = urljoin(self.url, src)
                    response = requests.get(img_url, headers=self.headers, timeout=5)
                    img_size = len(response.content) / 1024
                    if img_size > 100:
                        image_data['large_images'].append({
                            'url': img_url,
                            'size': f"{img_size:.1f}KB"
                        })
                except Exception as e:
                    logger.error(f"Error fetching image {src}: {e}")
                    continue
        return image_data

    def analyze_keywords(self, content: str) -> Dict:
        """
        Analyzes keywords and their relevance for SEO purposes.
        Removes stopwords, focuses on business-relevant terms, and calculates search potential.
        """
        # Remove HTML tags and get clean text
        text = BeautifulSoup(content, 'html.parser').get_text()
        
        # Process with spaCy
        doc = nlp(text.lower())
        
        # Extract keywords (focusing on relevant business terms)
        keywords = []
        for token in doc:
            # Only include relevant parts of speech and remove stopwords
            if (not token.is_stop and not token.is_punct and not token.is_space and
                token.pos_ in ['NOUN', 'PROPN'] and len(token.text) > 2):
                keywords.append(token.text)
        
        # Extract noun phrases (for long-tail keywords)
        noun_phrases = []
        for chunk in doc.noun_chunks:
            # Clean and filter noun phrases
            clean_chunk = ' '.join([token.text for token in chunk if not token.is_stop])
            if clean_chunk and len(clean_chunk.split()) <= 4:  # Limit to 4-word phrases
                noun_phrases.append(clean_chunk)
        
        # Combine and count all keywords
        all_keywords = keywords + noun_phrases
        keyword_freq = Counter(all_keywords)
        
        # Calculate metrics
        total_words = len([token for token in doc if not token.is_space])
        
        # Calculate keyword metrics with search volume estimation
        keyword_metrics = {}
        for word, count in keyword_freq.most_common(20):  # Top 20 keywords
            # Calculate normalized frequency score (0-1)
            frequency_score = count / total_words
            
            # Calculate length score (favoring 2-3 word phrases)
            length_score = 1.0 if 2 <= len(word.split()) <= 3 else 0.7
            
            # Calculate relevance score
            relevance_score = frequency_score * length_score
            
            keyword_metrics[word] = {
                'count': count,
                'density': (count / total_words) * 100,
                'relevance_score': relevance_score,
                'type': 'long-tail' if len(word.split()) > 1 else 'focus',
                'search_volume_category': self._estimate_search_volume(relevance_score)
            }
        
        return {
            'keyword_metrics': keyword_metrics,
            'total_words': total_words,
            'unique_keywords': len(keyword_metrics),
            'focus_keywords': self._get_focus_keywords(keyword_metrics),
            'keyword_groups': self._group_keywords(keyword_metrics)
        }

    def _estimate_search_volume(self, relevance_score: float) -> str:
        """Estimates search volume category based on relevance score."""
        if relevance_score > 0.8:
            return "High"
        elif relevance_score > 0.5:
            return "Medium"
        else:
            return "Low"

    def _get_focus_keywords(self, keyword_metrics: Dict) -> List[str]:
        """Identifies the main focus keywords based on metrics."""
        return [
            keyword for keyword, metrics in keyword_metrics.items()
            if metrics['relevance_score'] > 0.7 and metrics['type'] == 'focus'
        ][:5]  # Top 5 focus keywords

    def _group_keywords(self, keyword_metrics: Dict) -> Dict:
        """Groups keywords by their type and search volume."""
        groups = {
            'high_value': [],
            'long_tail': [],
            'supporting': []
        }
        
        for keyword, metrics in keyword_metrics.items():
            if metrics['relevance_score'] > 0.8:
                groups['high_value'].append(keyword)
            elif metrics['type'] == 'long-tail':
                groups['long_tail'].append(keyword)
            else:
                groups['supporting'].append(keyword)
        
        return groups

    def analyze_ada_compliance(self, soup: BeautifulSoup) -> Dict:
        """Analyzes compliance with WCAG 2.1 AA."""
        ada_issues = {
            'images': [],
            'headings': [],
            'links': [],
            'forms': []
        }

        # Check images
        for img in soup.find_all('img'):
            if not img.get('alt'):
                ada_issues['images'].append({
                    'element': str(img),
                    'issue': 'Missing alt text'
                })

        # Check headings
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        if not soup.find('h1'):
            ada_issues['headings'].append({
                'issue': 'Missing H1 heading'
            })
        
        # Check heading order
        previous_level = 0
        for heading in headings:
            current_level = int(heading.name[1])
            if current_level - previous_level > 1:
                ada_issues['headings'].append({
                    'element': str(heading),
                    'issue': f'Skipped heading level (from H{previous_level} to H{current_level})'
                })
            previous_level = current_level

        # Check links
        for link in soup.find_all('a'):
            if not link.get_text().strip():
                ada_issues['links'].append({
                    'element': str(link),
                    'issue': 'Empty link text'
                })

        # Check forms
        for input_element in soup.find_all('input'):
            if input_element.get('type') not in ['submit', 'button', 'hidden']:
                if not input_element.get('label') and not input_element.get('aria-label'):
                    ada_issues['forms'].append({
                        'element': str(input_element),
                        'issue': 'Form control missing label'
                    })

        return ada_issues

    def get_ai_recommendations(self, data: Dict) -> str:
        """Uses OpenAI to generate SEO insights."""
        # Check if OpenAI client is available
        if not openai_client:
            logger.error("OpenAI client not initialized. Cannot generate recommendations.")
            return self._generate_fallback_recommendations(data)
            
        cache_key = str(hash(json.dumps(data, sort_keys=True)))

        if cache_key in self.openai_cache:
            logger.info("Returning cached OpenAI recommendations.")
            return self.openai_cache[cache_key]

        try:
            prompt = f"""
            As an expert SEO consultant, analyze the following website data and provide detailed, actionable recommendations:

            URL: {self.url}

            **Performance Analysis:**
            - Performance Score: {data.get('lighthouse_scores', {}).get('performance', 0)}%
            - SEO Score: {data.get('lighthouse_scores', {}).get('seo', 0)}%
            - Best Practices Score: {data.get('lighthouse_scores', {}).get('best-practices', 0)}%
            - Core Web Vitals: {data.get('core_vitals', {})}
            - Optimization Opportunities: {data.get('opportunities', {})}

            **Content Analysis:**
            - Focus Keywords: {data.get('keyword_analysis', {}).get('focus_keywords', [])}
            - Keyword Metrics: {data.get('keyword_analysis', {}).get('keyword_metrics', {})}

            **Technical SEO Audit:**
            - Meta Information: {data.get('meta', {})}
            - Link Analysis: {data.get('links', {})}
            - Image Analysis: {data.get('images', {})}

            **Accessibility (ADA) Issues:**
            - ADA Issues: {data.get('ada_issues', {})}

            Based on this data, provide specific recommendations for:
            1. **Critical Performance Improvements:** Identify specific issues and suggest solutions.
            2. **Content Optimization:** Suggest how to improve content based on keyword analysis.
            3. **Technical SEO Fixes:** Address meta tags, links, images, and other technical issues.
            4. **Keyword Strategy Adjustments:** Recommend how to use keywords effectively.
            5. **Accessibility Improvements:** Address ADA compliance issues.
            6. **Priority Actions:** List the most important actions to take, ordered by impact.

            Format the response into clear, actionable bullet points with detailed explanations, ensuring each point is optimized for search engine visibility by including keywords, relevant subtopics, and examples tailored to the target audience's search intent.
            """

            response = openai_client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": "You are an expert SEO consultant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE
            )
            
            recommendations = response.choices[0].message.content.strip()
            
            # If no recommendations generated, provide fallback
            if not recommendations:
                return self._generate_fallback_recommendations(data)
                
            self.openai_cache[cache_key] = recommendations  # Store in cache
            logger.info("Generated new OpenAI recommendations and stored in cache.")
            return recommendations

        except Exception as e:
            logger.error(f"Error generating OpenAI recommendations: {e}")
            return self._generate_fallback_recommendations(data)

    def _generate_fallback_recommendations(self, data: Dict) -> str:
        """Generates basic recommendations when OpenAI fails."""
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
        if links_info.get('broken'):
            recommendations.append(f"- Fix {len(links_info.get('broken'))} broken links to improve user experience and SEO.")
        
        # Check for ADA issues
        ada_issues = data.get('ada_issues', {})
        if ada_issues:
            recommendations.append("\n♿ **Accessibility Improvements:**")
            if ada_issues.get('images'):
                recommendations.append(f"- Add alt text to {len(ada_issues.get('images'))} images to improve accessibility.")
            if ada_issues.get('headings'):
                recommendations.append(f"- Review heading structure for {len(ada_issues.get('headings'))} issues to ensure proper hierarchy.")
            if ada_issues.get('links'):
                recommendations.append(f"- Fix {len(ada_issues.get('links'))} link issues to improve navigation.")
            if ada_issues.get('forms'):
                recommendations.append(f"- Address {len(ada_issues.get('forms'))} form issues to improve usability.")
            
        return "\n".join(recommendations)

    def analyze_site(self):
        """Performs a complete analysis of the site, returning all data."""
        # Get lighthouse data
        lighthouse_data = self.get_lighthouse_data()
        if not lighthouse_data:
            logger.error("Failed to get lighthouse data")
            return None
            
        # Get technical audit
        technical_data = self.get_technical_audit()
        if not technical_data:
            logger.error("Failed to get technical audit")
            return None
            
        # Get soup from technical audit
        soup = technical_data.pop('soup', None)
        if not soup:
            logger.error("Failed to get page content")
            return None
            
        # Analyze keywords
        keyword_analysis = self.analyze_keywords(str(soup))
        if not keyword_analysis:
            logger.error("Failed to analyze keywords")
            keyword_analysis = {}
            
        # Analyze ADA compliance
        ada_issues = self.analyze_ada_compliance(soup)
        if not ada_issues:
            logger.error("Failed to analyze ADA compliance")
            ada_issues = {}
            
        # Get AI recommendations
        ai_recommendations = self.get_ai_recommendations({
            'lighthouse_scores': lighthouse_data['lighthouse_scores'],
            'core_vitals': lighthouse_data['core_vitals'],
            'opportunities': lighthouse_data['opportunities'],
            'keyword_analysis': keyword_analysis,
            'meta': technical_data['meta'],
            'headings': technical_data['headings'],
            'links': technical_data['links'],
            'images': technical_data['images'],
            'ada_issues': ada_issues
        })

        # Combine all data
        return {
            'lighthouse_scores': lighthouse_data['lighthouse_scores'],
            'core_vitals': lighthouse_data['core_vitals'],
            'opportunities': lighthouse_data['opportunities'],
            'meta': technical_data['meta'],
            'headings': technical_data['headings'],
            'links': technical_data['links'],
            'images': technical_data['images'],
            'keyword_analysis': keyword_analysis,
            'ada_issues': ada_issues,
            'ai_recommendations': ai_recommendations
        }
