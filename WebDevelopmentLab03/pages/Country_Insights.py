import streamlit as st
import requests
import google.generativeai as genai
import pandas as pd
import plotly.express as px

# ---------- Page Configuration ----------
st.set_page_config(
    page_title="AI Country Analysis",
    page_icon="🤖",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
    }
    .analysis-card {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #4CAF50;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .metric-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# ---------- Header ----------
st.markdown('<div class="main-header"><h1>🤖 AI-Powered Country Analysis</h1><p>Advanced country insights powered by Google Gemini AI</p></div>', unsafe_allow_html=True)

# ---------- Initialize Gemini ----------
@st.cache_resource
def init_gemini():
    """Initialize Gemini AI with error handling"""
    try:
        if "GEMINI_API_KEY" not in st.secrets:
            st.sidebar.error("⚠️ GEMINI_API_KEY not found!")
            return None
        
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        
        # Try different models
        models_to_try = ["gemini-pro", "gemini-1.0-pro", "models/gemini-pro"]
        
        for model_name in models_to_try:
            try:
                model = genai.GenerativeModel(model_name)
                # Quick test
                response = model.generate_content("Test")
                st.sidebar.success(f"✅ Using {model_name}")
                return model
            except:
                continue
        
        return None
    except Exception as e:
        st.sidebar.error(f"❌ Gemini Error: {str(e)}")
        return None

# Initialize Gemini
gemini_model = init_gemini()

# ---------- REST Countries API Helper ----------
def fetch_country_data(country_name):
    """Fetch data for a specific country"""
    try:
        response = requests.get(f"https://restcountries.com/v3.1/name/{country_name}", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data:
                country = data[0]
                return {
                    "name": country.get("name", {}).get("common"),
                    "official_name": country.get("name", {}).get("official"),
                    "capital": country.get("capital", ["Unknown"])[0] if country.get("capital") else "Unknown",
                    "region": country.get("region", "Unknown"),
                    "subregion": country.get("subregion", "Unknown"),
                    "population": country.get("population", 0),
                    "area": country.get("area", 0),
                    "languages": list(country.get("languages", {}).values()) if country.get("languages") else ["Unknown"],
                    "currencies": list(country.get("currencies", {}).keys()) if country.get("currencies") else ["Unknown"],
                    "timezones": country.get("timezones", []),
                    "flag": country.get("flag", "🏳️"),
                    "coordinates": country.get("latlng", [0, 0])
                }
    except Exception as e:
        st.error(f"Error fetching data: {str(e)}")
    return None

def fetch_comparison_data(country1, country2):
    """Fetch data for two countries to compare"""
    return fetch_country_data(country1), fetch_country_data(country2)

# ---------- AI Analysis Functions ----------
def generate_travel_analysis(country_data, traveler_type, season, duration):
    """Generate travel analysis using Gemini"""
    if not gemini_model:
        return "⚠️ Gemini AI is not available. Please check your API key configuration."
    
    try:
        prompt = f"""
        Create a comprehensive travel analysis for {country_data['name']} for a {traveler_type} traveler.
        
        Travel Details:
        - Season: {season}
        - Duration: {duration} days
        - Traveler Type: {traveler_type}
        
        Country Information:
        - Capital: {country_data['capital']}
        - Population: {country_data['population']:,}
        - Area: {country_data['area']:,} km²
        - Region: {country_data['region']}
        - Languages: {', '.join(country_data['languages'])}
        - Currency: {', '.join(country_data['currencies'])}
        
        Please provide:
        1. Best travel itinerary for {duration} days
        2. Seasonal weather analysis for {season}
        3. Cultural etiquette and tips
        4. Budget recommendations for {traveler_type}
        5. Must-try local foods
        6. Hidden gems and off-the-beaten-path locations
        7. Safety considerations
        
        Make it practical and engaging!
        """
        
        response = gemini_model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"❌ Error generating analysis: {str(e)}"

def generate_economic_analysis(country_data, focus_area):
    """Generate economic analysis using Gemini"""
    if not gemini_model:
        return "⚠️ Gemini AI is not available."
    
    try:
        prompt = f"""
        Provide an economic analysis of {country_data['name']} focusing on {focus_area}.
        
        Country Data:
        - Population: {country_data['population']:,}
        - Area: {country_data['area']:,} km²
        - Region: {country_data['region']}
        - Languages: {', '.join(country_data['languages'])}
        - Currency: {', '.join(country_data['currencies'])}
        
        Focus Area: {focus_area}
        
        Please analyze:
        1. Current economic status
        2. Key industries and GDP contributors
        3. {focus_area} specific analysis
        4. Growth opportunities
        5. Challenges and risks
        6. Investment climate
        7. Future economic outlook
        
        Provide data-driven insights and practical information.
        """
        
        response = gemini_model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"❌ Error: {str(e)}"

def generate_country_comparison(country1_data, country2_data, comparison_aspect):
    """Generate comparison between two countries"""
    if not gemini_model:
        return "⚠️ Gemini AI is not available."
    
    try:
        prompt = f"""
        Compare {country1_data['name']} and {country2_data['name']} focusing on {comparison_aspect}.
        
        {country1_data['name']}:
        - Capital: {country1_data['capital']}
        - Population: {country1_data['population']:,}
        - Area: {country1_data['area']:,} km²
        - Region: {country1_data['region']}
        - Languages: {', '.join(country1_data['languages'])}
        
        {country2_data['name']}:
        - Capital: {country2_data['capital']}
        - Population: {country2_data['population']:,}
        - Area: {country2_data['area']:,} km²
        - Region: {country2_data['region']}
        - Languages: {', '.join(country2_data['languages'])}
        
        Comparison Aspect: {comparison_aspect}
        
        Provide a detailed comparison covering:
        1. Key similarities and differences
        2. Strengths and weaknesses in {comparison_aspect}
        3. Cultural aspects
        4. Development indicators
        5. Recommendations based on {comparison_aspect}
        6. Interesting insights and facts
        
        Make it informative and engaging!
        """
        
        response = gemini_model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"❌ Error: {str(e)}"

# ---------- Main App ----------
def main():
    st.sidebar.header("⚙️ Analysis Settings")
    
    if not gemini_model:
        st.warning("""
        ⚠️ Gemini AI is not available. To enable AI features:
        1. Get a free API key from https://aistudio.google.com/app/apikey
        2. Add it to Streamlit Cloud secrets as `GEMINI_API_KEY`
        3. Redeploy your app
        """)
    else:
        st.sidebar.success("✅ Gemini AI is ready!")
    
    # Tab Layout
    tab1, tab2, tab3 = st.tabs(["🧳 Travel Analysis", "💰 Economic Analysis", "📊 Country Comparison"])
    
    with tab1:
        st.subheader("AI-Powered Travel Planning")
        
        with st.container():
            col1, col2, col3 = st.columns(3)
            
            with col1:
                country_name = st.text_input(
                    "Country to visit:",
                    placeholder="e.g., Japan, France, Brazil...",
                    key="travel_country"
                )
                
            with col2:
                traveler_type = st.selectbox(
                    "Traveler Type:",
                    ["Backpacker", "Family", "Luxury", "Adventure", "Cultural", "Business", "Student"],
                    key="traveler_type"
                )
                
            with col3:
                season = st.selectbox(
                    "Travel Season:",
                    ["Spring", "Summer", "Fall", "Winter", "Any"],
                    key="season"
                )
            
            duration = st.slider(
                "Trip Duration (days):",
                min_value=3,
                max_value=30,
                value=7,
                step=1,
                key="duration"
            )
            
            if st.button("🧭 Generate Travel Analysis", type="primary", use_container_width=True):
                if country_name:
                    with st.spinner(f"✈️ Creating your {duration}-day {traveler_type.lower()} itinerary for {country_name}..."):
                        country_data = fetch_country_data(country_name)
                        
                        if country_data:
                            analysis = generate_travel_analysis(country_data, traveler_type, season, duration)
                            
                            st.markdown(f'<div class="analysis-card">{analysis}</div>', unsafe_allow_html=True)
                            
                            # Display country metrics
                            st.subheader("📈 Country Overview")
                            col_metrics1, col_metrics2, col_metrics3, col_metrics4 = st.columns(4)
                            
                            with col_metrics1:
                                st.metric("Capital", country_data['capital'])
                            with col_metrics2:
                                st.metric("Population", f"{country_data['population']:,}")
                            with col_metrics3:
                                st.metric("Area", f"{country_data['area']:,} km²")
                            with col_metrics4:
                                st.metric("Languages", len(country_data['languages']))
                        else:
                            st.error(f"❌ Could not find data for '{country_name}'")
                else:
                    st.warning("⚠️ Please enter a country name")
    
    with tab2:
        st.subheader("Economic & Development Analysis")
        
        with st.container():
            col1, col2 = st.columns(2)
            
            with col1:
                country_name = st.text_input(
                    "Country to analyze:",
                    placeholder="e.g., Germany, India, Australia...",
                    key="economic_country"
                )
                
            with col2:
                focus_area = st.selectbox(
                    "Analysis Focus:",
                    ["Technology & Innovation", "Agriculture", "Manufacturing", 
                     "Tourism", "Healthcare", "Education", "Infrastructure", 
                     "Renewable Energy", "Overall Economy"],
                    key="focus_area"
                )
            
            if st.button("📊 Generate Economic Analysis", type="primary", use_container_width=True):
                if country_name:
                    with st.spinner(f"📈 Analyzing {focus_area.lower()} in {country_name}..."):
                        country_data = fetch_country_data(country_name)
                        
                        if country_data:
                            analysis = generate_economic_analysis(country_data, focus_area)
                            
                            st.markdown(f'<div class="analysis-card">{analysis}</div>', unsafe_allow_html=True)
                            
                            # Create visualizations
                            st.subheader("📊 Economic Indicators")
                            
                            # Population distribution chart
                            pop_data = pd.DataFrame({
                                'Category': ['Urban Population', 'Rural Population'],
                                'Percentage': [70, 30]  # Example data - in real app, use API data
                            })
                            
                            fig = px.pie(pop_data, values='Percentage', names='Category', 
                                       title="Population Distribution",
                                       color_discrete_sequence=px.colors.qualitative.Set3)
                            st.plotly_chart(fig, use_container_width=True)
                            
                        else:
                            st.error(f"❌ Could not find data for '{country_name}'")
                else:
                    st.warning("⚠️ Please enter a country name")
    
    with tab3:
        st.subheader("Country Comparison Analysis")
        
        with st.container():
            col1, col2, col3 = st.columns(3)
            
            with col1:
                country1 = st.text_input(
                    "First country:",
                    placeholder="e.g., United States",
                    key="country1"
                )
                
            with col2:
                country2 = st.text_input(
                    "Second country:",
                    placeholder="e.g., China",
                    key="country2"
                )
                
            with col3:
                comparison_aspect = st.selectbox(
                    "Comparison Aspect:",
                    ["Economy", "Culture", "Tourism", "Education", 
                     "Healthcare", "Technology", "Quality of Life", "Overall Development"],
                    key="comparison_aspect"
                )
            
            if st.button("⚖️ Generate Comparison", type="primary", use_container_width=True):
                if country1 and country2:
                    with st.spinner(f"🔍 Comparing {country1} and {country2}..."):
                        country1_data, country2_data = fetch_comparison_data(country1, country2)
                        
                        if country1_data and country2_data:
                            comparison = generate_country_comparison(
                                country1_data, country2_data, comparison_aspect
                            )
                            
                            st.markdown(f'<div class="analysis-card">{comparison}</div>', unsafe_allow_html=True)
                            
                            # Side-by-side metrics
                            st.subheader("📊 Quick Stats Comparison")
                            
                            col_stat1, col_stat2 = st.columns(2)
                            
                            with col_stat1:
                                st.markdown(f"### {country1_data['flag']} {country1_data['name']}")
                                st.metric("Population", f"{country1_data['population']:,}")
                                st.metric("Area", f"{country1_data['area']:,} km²")
                                st.metric("Capital", country1_data['capital'])
                                st.metric("Languages", len(country1_data['languages']))
                            
                            with col_stat2:
                                st.markdown(f"### {country2_data['flag']} {country2_data['name']}")
                                st.metric("Population", f"{country2_data['population']:,}")
                                st.metric("Area", f"{country2_data['area']:,} km²")
                                st.metric("Capital", country2_data['capital'])
                                st.metric("Languages", len(country2_data['languages']))
                            
                        else:
                            missing = []
                            if not country1_data: missing.append(country1)
                            if not country2_data: missing.append(country2)
                            st.error(f"❌ Could not find data for: {', '.join(missing)}")
                else:
                    st.warning("⚠️ Please enter both country names")
    
    # Footer
    st.markdown("---")
    st.caption("🤖 Powered by Google Gemini AI • 📊 Data from REST Countries API • Phase 3: Advanced AI Analysis")

if __name__ == "__main__":
    main()
