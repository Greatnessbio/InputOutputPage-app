import streamlit as st
import requests
import json
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import time
import os
import difflib

# Initialize session state
if 'content' not in st.session_state:
    st.session_state.content = ""
if 'organic_kw_ranks' not in st.session_state:
    st.session_state.organic_kw_ranks = ""
if 'semrush_site_audit' not in st.session_state:
    st.session_state.semrush_site_audit = ""
if 'technical_seo_audit' not in st.session_state:
    st.session_state.technical_seo_audit = ""
if 'seo_analysis' not in st.session_state:
    st.session_state.seo_analysis = ""
if 'recommendations' not in st.session_state:
    st.session_state.recommendations = ""

# User agent to mimic a browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Create a retry strategy
retry_strategy = Retry(
    total=3,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["HEAD", "GET", "OPTIONS"],
    backoff_factor=1
)
adapter = HTTPAdapter(max_retries=retry_strategy)
http = requests.Session()
http.mount("https://", adapter)
http.mount("http://", adapter)

def check_password():
    """Returns `True` if the user had the correct password."""
    def password_entered():
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 Password incorrect")
        return False
    else:
        return True

def get_jina_reader_content(url):
    jina_url = f"https://r.jina.ai/{url}"
    try:
        response = http.get(jina_url, headers=HEADERS)
        response.raise_for_status()
        time.sleep(3)  # 3-second delay between requests
        return response.text
    except requests.exceptions.RequestException as e:
        return f"Failed to fetch content: {str(e)}"

def analyze_seo_data(organic_kw_ranks, semrush_site_audit, technical_seo_audit):
    OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
    if not OPENROUTER_API_KEY:
        st.error("OpenRouter API key not found. Please set the OPENROUTER_API_KEY environment variable.")
        return None

    prompt = f"""Analyze the following SEO data from organic keyword rankings, SEMrush site audit, and technical SEO audit. Provide a detailed analysis and prioritization of keywords and opportunities.

Organic Keyword Rankings:
<organic_kw_ranks>
{organic_kw_ranks}
</organic_kw_ranks>

SEMrush Site Audit:
<semrush_site_audit>
{semrush_site_audit}
</semrush_site_audit>

Technical SEO Audit:
<technical_seo_audit>
{technical_seo_audit}
</technical_seo_audit>

Provide your analysis in the following format:

<seo_analysis>
1. Key Issues and Opportunities:
   - Summary of critical issues from the SEMrush and technical SEO audits
   - Top keyword opportunities based on current rankings, volume, and difficulty

2. Keyword Clustering and Prioritization:
   - Grouped keywords by theme and intent
   - Prioritized list of keywords to target

3. Content Gap Analysis:
   - Topics and themes missing from the current content based on keyword data
   - Suggestions for new content topics

4. On-Page Optimization Priorities:
   - Elements needing immediate attention (titles, meta descriptions, headings) based on the audit reports
   - Suggestions for content structure improvements

5. Technical SEO Insights:
   - Key technical issues identified
   - Prioritized list of technical improvements
</seo_analysis>
"""

    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "anthropic/claude-3.5-sonnet",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant that analyzes SEO data and provides strategic insights."},
                {"role": "user", "content": prompt}
            ]
        }
    )
    
    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    else:
        st.error(f"Error from OpenRouter API: {response.status_code} - {response.text}")
        return None

def generate_recommendations(url, content, seo_analysis):
    OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
    if not OPENROUTER_API_KEY:
        st.error("OpenRouter API key not found. Please set the OPENROUTER_API_KEY environment variable.")
        return None

    prompt = f"""Based on the following SEO analysis and the current page content, generate specific recommendations for optimizing the page at {url}.

SEO Analysis:
<seo_analysis>
{seo_analysis}
</seo_analysis>

Current page content:
<current_content>
{content}
</current_content>

Provide your recommendations in the following format:

<page_recommendations>
1. Page Title:
   - Current: [current title]
   - Recommended: [proposed title]
   - Explanation: [brief justification]

2. Meta Description:
   - Current: [current meta description]
   - Recommended: [proposed meta description]
   - Explanation: [brief justification]

3. Heading Structure:
   - Current structure
   - Recommended structure
   - Explanations for changes

4. Content Additions/Improvements:
   - List of suggested additions or modifications
   - Target keywords for each suggestion

5. Internal Linking:
   - Suggested internal links to add
   - Anchor text recommendations

6. Additional On-Page Optimizations:
   - Other specific recommendations (e.g., image alt text, schema markup)

7. Technical Improvements:
   - List of technical SEO improvements specific to this page
</page_recommendations>
"""

    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "anthropic/claude-3.5-sonnet",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant that provides specific SEO recommendations for web pages."},
                {"role": "user", "content": prompt}
            ]
        }
    )
    
    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    else:
        st.error(f"Error from OpenRouter API: {response.status_code} - {response.text}")
        return None

def main():
    st.title('Advanced SEO Content Optimizer')

    if check_password():
        st.success("Logged in successfully!")

        url = st.text_input('Enter URL to analyze (including http:// or https://):')
        st.session_state.organic_kw_ranks = st.text_area('Paste the content of OligoFactory_Current_Organic_KW_Ranks.txt here:', height=200)
        st.session_state.semrush_site_audit = st.text_area('Paste the content of OligoFactory_Semrush_Site_Audit.txt here:', height=200)
        st.session_state.technical_seo_audit = st.text_area('Paste the content of OligoFactory_TechnicalSEO_Audit.txt here:', height=200)
        
        if st.button('Analyze and Generate Recommendations'):
            if url and st.session_state.organic_kw_ranks and st.session_state.semrush_site_audit and st.session_state.technical_seo_audit:
                with st.spinner('Fetching content...'):
                    st.session_state.content = get_jina_reader_content(url)
                
                if st.session_state.content and not st.session_state.content.startswith("Failed to fetch content"):
                    st.success("Content fetched successfully!")
                    
                    with st.spinner('Analyzing SEO data...'):
                        seo_analysis = analyze_seo_data(st.session_state.organic_kw_ranks, st.session_state.semrush_site_audit, st.session_state.technical_seo_audit)
                    
                    if seo_analysis:
                        st.success("SEO data analyzed successfully!")
                        st.session_state.seo_analysis = seo_analysis
                        
                        with st.spinner('Generating recommendations...'):
                            recommendations = generate_recommendations(url, st.session_state.content, seo_analysis)
                        
                        if recommendations:
                            st.success("Recommendations generated successfully!")
                            st.session_state.recommendations = recommendations
                        else:
                            st.error("Failed to generate recommendations.")
                    else:
                        st.error("Failed to analyze SEO data.")
                else:
                    st.error(st.session_state.content)
            else:
                st.warning('Please enter a URL and paste all required data')
        
        if st.session_state.content:
            st.subheader("Current Page Content:")
            st.text_area("Full content", st.session_state.content, height=200)
        
        if 'seo_analysis' in st.session_state and st.session_state.seo_analysis:
            st.subheader("SEO Analysis:")
            st.text_area("Analysis and insights", st.session_state.seo_analysis, height=300)
        
        if 'recommendations' in st.session_state and st.session_state.recommendations:
            st.subheader("Page Optimization Recommendations:")
            st.text_area("Specific recommendations", st.session_state.recommendations, height=400)

if __name__ == "__main__":
    main()
