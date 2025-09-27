import streamlit as st
import pandas as pd
import plotly.express as px
from typing import Dict

# Import configuration and analyzer
from config import (
    logger, is_valid_url, get_metric_color, extract_numeric_value,
    PERFORMANCE_THRESHOLD_GOOD, PERFORMANCE_THRESHOLD_WARNING,
    LCP_THRESHOLD_GOOD, LCP_THRESHOLD_WARNING
)
from seo_analyzer import SEOAnalyzer

# --- Streamlit Configuration ---
st.set_page_config(page_title="Local CEO SEO Analyzer Pro", layout="wide")

# --- Dashboard Creation Functions ---
def create_dashboard(analyzer: SEOAnalyzer, data: Dict):
    """Creates a Streamlit dashboard to display SEO analysis results."""
    if not data:
        st.error("No data to display. Please try again.")
        return

    # Custom CSS
    st.markdown("""
        <style>
        .metric-card {
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }
        .metric-card:hover { transform: translateY(-5px); }
        .good-score { color: #28a745; font-weight: bold; } /* Green for good */
        .warning-score { color: #ffc107; font-weight: bold; } /* Yellow for warning */
        .poor-score { color: #dc3545; font-weight: bold; } /* Red for poor */
        .recommendation { 
            background-color: #f8f9fa;
            padding: 15px;
            border-left: 4px solid #007bff;
            margin: 10px 0;
            color: black;
        }
        .metric-card h3, .metric-card h4, .metric-card p {
            color: black;
        }
        </style>
    """, unsafe_allow_html=True)

    # Header
    st.title("🎯 Local CEO SEO Analyzer Pro")

    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Performance",
        "🔍 Technical Audit",
        "📝 Content Analysis",
        "♿ ADA Compliance",
        "🤖 AI Insights"
    ])

    with tab1:
        create_performance_view(data)

    with tab2:
        create_technical_view(data)

    with tab3:
        create_content_view(data)
        
        # Add keyword analysis section
        st.subheader("Keyword Analysis")
        if 'keyword_analysis' in data:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Words", data['keyword_analysis']['total_words'])
                st.metric("Unique Keywords", data['keyword_analysis']['unique_keywords'])
            
            # Create keyword density table
            keyword_data = []
            for keyword, metrics in data['keyword_analysis']['keyword_metrics'].items():
                keyword_data.append({
                    'Keyword': keyword,
                    'Count': metrics['count'],
                    'Density %': f"{metrics['density']:.2f}%",
                    'Relevance': f"{metrics['relevance_score']:.2f}",
                    'Type': metrics['type'],
                    'Search Volume': metrics['search_volume_category']
                })
            
            st.dataframe(
                pd.DataFrame(keyword_data),
                hide_index=True
            )

    with tab4:
        create_ada_view(data)

    with tab5:
        create_ai_insights(data)

def create_performance_view(data: Dict):
    """Creates the performance metrics visualization."""
    st.subheader("Lighthouse Scores")
    cols = st.columns(4)
    for i, (metric, score) in enumerate(data['lighthouse_scores'].items()):
        score_class = get_metric_color(score, PERFORMANCE_THRESHOLD_GOOD * 100, PERFORMANCE_THRESHOLD_WARNING * 100)
        with cols[i]:
            st.markdown(f"""
                <div class="metric-card">
                    <h3>{metric.title()}</h3>
                    <p class="{score_class}">{score:.0f}%</p>
                </div>
            """, unsafe_allow_html=True)

    st.subheader("Core Web Vitals")
    core_vitals = data['core_vitals']
    
    # Prepare data for table
    vitals_data = {
        'Metric': [],
        'Value': []
    }
    for metric, value in core_vitals.items():
        vitals_data['Metric'].append(metric)
        if value != 'N/A':
            value_numeric = extract_numeric_value(value)
            if value_numeric is not None:
                color = get_metric_color(value_numeric, LCP_THRESHOLD_GOOD, LCP_THRESHOLD_WARNING)
                vitals_data['Value'].append(f'<span style="color:{color};">{value}</span>')
            else:
                vitals_data['Value'].append(f'<span>{value}</span>')
        else:
            vitals_data['Value'].append(f'<span>{value}</span>')

    vitals_df = pd.DataFrame(vitals_data)

    # Display the table with HTML formatting
    st.markdown(vitals_df.to_html(escape=False, index=False), unsafe_allow_html=True)

    st.subheader("Optimization Opportunities")
    for metric, value in data['opportunities'].items():
        if value > 0:
            score_class = "good-score" if value <= LCP_THRESHOLD_GOOD else "warning-score" if value <= LCP_THRESHOLD_WARNING else "poor-score"
            st.markdown(f"""
                <div class="metric-card">
                    <h4>{metric}</h4>
                    <p class="{score_class}">Potential Savings: {value:,} {'bytes' if 'CSS' in metric or 'JS' in metric else 'ms'}</p>
                </div>
            """, unsafe_allow_html=True)

def create_technical_view(data: Dict):
    """Creates the technical audit visualization."""
    st.subheader("Meta Information")
    meta_cols = st.columns(2)
    with meta_cols[0]:
        st.metric("Meta Title", "✅ Present" if data['meta']['title'] else "❌ Missing", delta_color="off")
    with meta_cols[1]:
        st.metric("Meta Description", "✅ Present" if data['meta']['description'] else "❌ Missing", delta_color="off")

    st.subheader("Heading Structure")
    fig = px.bar(
        x=list(data['headings'].keys()),
        y=list(data['headings'].values()),
        title="Heading Distribution"
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Link Analysis")
    link_cols = st.columns(4)
    with link_cols[0]:
        st.metric("Total Links", data['links']['total'])
    with link_cols[1]:
        st.metric("Internal Links", data['links']['internal'])
    with link_cols[2]:
        st.metric("External Links", data['links']['external'])
    with link_cols[3]:
        st.metric("Broken Links", len(data['links']['broken']), delta_color="inverse")

    if data['links']['broken']:
        st.warning("Broken Links Found:")
        for link in data['links']['broken']:
            st.write(f"- {link}")

def create_content_view(data: Dict):
    """Creates the content analysis visualization."""
    st.subheader("Image Analysis")
    st.metric("Total Images", data['images']['total'])
    st.metric("Images Missing Alt Text", data['images']['missing_alt'], delta_color="inverse")
    if data['images']['large_images']:
        st.warning("Large Images Found:")
        for img in data['images']['large_images']:
            st.write(f"- {img['url']} ({img['size']})")

def create_ada_view(data: Dict):
    """Creates the accessibility analysis visualization."""
    st.subheader("ADA Compliance Analysis")
    
    if 'ada_issues' in data:
        issues = data['ada_issues']
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Image Issues", len(issues['images']))
        with col2:
            st.metric("Heading Issues", len(issues['headings']))
        with col3:
            st.metric("Link Issues", len(issues['links']))
        with col4:
            st.metric("Form Issues", len(issues['forms']))

        # Detailed issues
        if issues['images']:
            st.subheader("Image Accessibility Issues")
            for issue in issues['images']:
                st.warning(issue['issue'])
                with st.expander("Show Element"):
                    st.code(issue['element'])

        if issues['headings']:
            st.subheader("Heading Structure Issues")
            for issue in issues['headings']:
                st.warning(issue['issue'])
                if 'element' in issue:
                    with st.expander("Show Element"):
                        st.code(issue['element'])

        if issues['links']:
            st.subheader("Link Accessibility Issues")
            for issue in issues['links']:
                st.warning(issue['issue'])
                with st.expander("Show Element"):
                    st.code(issue['element'])

        if issues['forms']:
            st.subheader("Form Accessibility Issues")
            for issue in issues['forms']:
                st.warning(issue['issue'])
                with st.expander("Show Element"):
                    st.code(issue['element'])

def create_ai_insights(data: Dict):
    """Creates the AI recommendations visualization."""
    st.subheader("AI Recommendations")
    st.markdown(f"""
        <div class="recommendation">
            <h4>Recommendations</h4>
            {data.get('ai_recommendations', '')}
        </div>
    """, unsafe_allow_html=True)

# --- Main Function ---
def main():
    st.title("🔍 Local CEO SEO Analyzer Pro")
    url = st.text_input("Enter Website URL:", "")

    if st.button("Analyze"):
        if not is_valid_url(url):
            st.error("Please enter a valid URL.")
            return
        
        with st.spinner("Analyzing website..."):
            try:
                analyzer = SEOAnalyzer(url)
                # Single call to analyze_site method to get all data
                data = analyzer.analyze_site()
                
                if not data:
                    st.error("Error analyzing website. Check logs for details.")
                    return
                    
                create_dashboard(analyzer, data)

            except Exception as e:
                st.error(f"An error occurred during analysis: {e}")
                logger.error(f"Error during analysis: {e}", exc_info=True)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"Application error: {e}")
        logger.error(f"Application error: {e}", exc_info=True)
