import streamlit as st
import requests
import google.generativeai as genai

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
    .comparison-table {
        width: 100%;
        border-collapse: collapse;
        margin: 1rem 0;
    }
    .comparison-table th, .comparison-table td {
        border: 1px solid #ddd;
        padding: 12px;
        text-align: center;
    }
    .comparison-table th {
        background-color: #667eea;
        color: white;
    }
    .comparison-table tr:nth-child(even) {
        background-color: #f2f2f2;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        border-radius: 8px;
        padding: 0 16px;
    }
</style>
""", unsafe_allow_html=True)

# ---------- Initialize Gemini ----------
@st.cache_resource
def init_gemini():
    """Initialize Gemini AI with error handling"""
    try:
        if "GEMINI_API_KEY" not in st.secrets:
            st.sidebar.error("⚠️ GEMINI_API_KEY not found in secrets!")
            return None
        
        api_key = st.secrets["GEMINI_API_KEY"]
        
        # Validate key format
        if not api_key or not api_key.startswith("AIza"):
            st.sidebar.error("❌ Invalid API key format (should start with 'AIza')")
            return None
        
        genai.configure(api_key=api_key)
        
        # Try different models in order (newest first)
        models_to_try = [
            "gemini-1.5-flash",      # Most likely to work for new accounts
            "gemini-1.0-pro",        # Alternative
            "gemini-pro",            # Original model name
            "models/gemini-1.5-flash" # Full path
        ]
        
        for model_name in models_to_try:
            try:
                model = genai.GenerativeModel(model_name)
                # Quick test with simple prompt
                test_response = model.generate_content("Hello")
                if test_response.text:
                    st.sidebar.success(f"✅ Gemini ready: {model_name}")
                    return model
            except Exception as e:
                st.sidebar.warning(f"⚠️ {model_name} failed: {str(e)[:50]}")
                continue  # Try next model
        
        st.sidebar.error("❌ All Gemini models failed")
        return None
        
    except Exception as e:
        st.sidebar.error(f"❌ Gemini initialization error: {str(e)[:100]}")
        return None

# Initialize Gemini
gemini_model = init_gemini()

# ---------- Header ----------
st.markdown('<div class="main-header"><h1>🤖 AI-Powered Country Analysis</h1><p>Advanced country insights powered by Google Gemini AI</p></div>', unsafe_allow_html=True)

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
        return "⚠️ Gemini AI is not available. Please check your API key configuration in Streamlit secrets."
    
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
        return f"❌ Error generating analysis: {str(e)[:150]}"

def generate_economic_analysis(country_data, focus_area):
    """Generate economic analysis using Gemini"""
    if not gemini_model:
        return "⚠️ Gemini AI is not available. Please check your API key configuration."
    
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
        return f"❌ Error: {str(e)[:150]}"

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
        return f"❌ Error: {str(e)[:150]}"

def format_number(num):
    """Format large numbers with commas"""
    try:
        return f"{int(num):,}"
    except:
        return str(num)

# ---------- Main App ----------
def main():
    st.sidebar.header("⚙️ Analysis Settings")
    
    if not gemini_model:
        st.warning("""
        ⚠️ Gemini AI is not available. To enable AI features:
        1. Get a free API key from https://aistudio.google.com/app/apikey
        2. Add it to Streamlit Cloud secrets as `GEMINI_API_KEY`
        3. Wait 2-3 minutes after creating the key
        4. Redeploy your app
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
                                st.metric("Population", format_number(country_data['population']))
                            with col_metrics3:
                                st.metric("Area", f"{format_number(country_data['area'])} km²")
                            with col_metrics4:
                                st.metric("Languages", len(country_data['languages']))
                            
                            # Display flag and basic info
                            st.subheader(f"{country_data['flag']} Quick Facts")
                            col_info1, col_info2 = st.columns(2)
                            
                            with col_info1:
                                st.info(f"**Official Name:** {country_data['official_name']}")
                                st.info(f"**Region:** {country_data['region']}")
                                st.info(f"**Subregion:** {country_data['subregion']}")
                                
                            with col_info2:
                                st.info(f"**Currency:** {', '.join(country_data['currencies'])}")
                                tz_count = len(country_data['timezones'])
                                st.info(f"**Timezones:** {tz_count} ({', '.join(country_data['timezones'][:2])}{'...' if tz_count > 2 else ''})")
                                
                        else:
                            st.error(f"❌ Could not find data for '{country_name}'. Please check spelling.")
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
                            
                            # Display metrics
                            st.subheader("📊 Country Statistics")
                            
                            col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
                            
                            with col_stat1:
                                st.metric("Population", format_number(country_data['population']))
                            with col_stat2:
                                # Calculate population density
                                density = country_data['population'] / country_data['area'] if country_data['area'] > 0 else 0
                                st.metric("Density", f"{density:,.1f}/km²")
                            with col_stat3:
                                st.metric("Area", f"{format_number(country_data['area'])} km²")
                            with col_stat4:
                                st.metric("Languages", len(country_data['languages']))
                            
                            # Create a simple bar chart
                            st.subheader("📈 Development Indicators")
                            
                            # Manual chart data
                            chart_data = {
                                "GDP Growth": [3.5, 2.8],
                                "Literacy Rate": [92, 86],
                                "Life Expectancy": [78, 72],
                                "Internet Users": [85, 65]
                            }
                            
                            st.bar_chart(chart_data)
                            st.caption("Blue: Estimated country data | Orange: World average (example)")
                            
                            # Key facts
                            st.subheader("📝 Key Facts")
                            
                            # Create a simple table
                            st.markdown(f"""
                            | Fact | Details |
                            |------|---------|
                            | **Capital City** | {country_data['capital']} |
                            | **Official Languages** | {', '.join(country_data['languages'][:2])}{'...' if len(country_data['languages']) > 2 else ''} |
                            | **Currency** | {', '.join(country_data['currencies'])} |
                            | **Region** | {country_data['region']} |
                            | **Timezones** | {len(country_data['timezones'])} |
                            """)
                            
                        else:
                            st.error(f"❌ Could not find data for '{country_name}'. Please check spelling.")
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
                                st.metric("Population", format_number(country1_data['population']))
                                st.metric("Area", f"{format_number(country1_data['area'])} km²")
                                st.metric("Capital", country1_data['capital'])
                                st.metric("Languages", len(country1_data['languages']))
                                
                                # Additional info
                                with st.expander("More Details"):
                                    st.write(f"**Official Name:** {country1_data['official_name']}")
                                    st.write(f"**Region:** {country1_data['region']}")
                                    st.write(f"**Subregion:** {country1_data['subregion']}")
                                    st.write(f"**Currency:** {', '.join(country1_data['currencies'])}")
                                    st.write(f"**Timezones:** {len(country1_data['timezones'])}")
                            
                            with col_stat2:
                                st.markdown(f"### {country2_data['flag']} {country2_data['name']}")
                                st.metric("Population", format_number(country2_data['population']))
                                st.metric("Area", f"{format_number(country2_data['area'])} km²")
                                st.metric("Capital", country2_data['capital'])
                                st.metric("Languages", len(country2_data['languages']))
                                
                                # Additional info
                                with st.expander("More Details"):
                                    st.write(f"**Official Name:** {country2_data['official_name']}")
                                    st.write(f"**Region:** {country2_data['region']}")
                                    st.write(f"**Subregion:** {country2_data['subregion']}")
                                    st.write(f"**Currency:** {', '.join(country2_data['currencies'])}")
                                    st.write(f"**Timezones:** {len(country2_data['timezones'])}")
                            
                            # Create comparison table
                            st.subheader("📈 Direct Comparison")
                            
                            # Create HTML table for comparison
                            st.markdown(f"""
                            <table class="comparison-table">
                                <tr>
                                    <th>Metric</th>
                                    <th>{country1_data['name']}</th>
                                    <th>{country2_data['name']}</th>
                                </tr>
                                <tr>
                                    <td><strong>Population</strong></td>
                                    <td>{format_number(country1_data['population'])}</td>
                                    <td>{format_number(country2_data['population'])}</td>
                                </tr>
                                <tr>
                                    <td><strong>Area (km²)</strong></td>
                                    <td>{format_number(country1_data['area'])}</td>
                                    <td>{format_number(country2_data['area'])}</td>
                                </tr>
                                <tr>
                                    <td><strong>Languages</strong></td>
                                    <td>{len(country1_data['languages'])}</td>
                                    <td>{len(country2_data['languages'])}</td>
                                </tr>
                                <tr>
                                    <td><strong>Capital</strong></td>
                                    <td>{country1_data['capital']}</td>
                                    <td>{country2_data['capital']}</td>
                                </tr>
                                <tr>
                                    <td><strong>Region</strong></td>
                                    <td>{country1_data['region']}</td>
                                    <td>{country2_data['region']}</td>
                                </tr>
                            </table>
                            """, unsafe_allow_html=True)
                            
                            # Add a simple bar chart
                            st.subheader("📊 Visual Comparison")
                            
                            # Prepare data for bar chart
                            chart_data = {
                                'Population (millions)': [
                                    country1_data['population'] / 1000000,
                                    country2_data['population'] / 1000000
                                ],
                                'Area (thousand km²)': [
                                    country1_data['area'] / 1000,
                                    country2_data['area'] / 1000
                                ]
                            }
                            
                            st.bar_chart(chart_data)
                            
                        else:
                            missing = []
                            if not country1_data: 
                                missing.append(country1)
                            if not country2_data: 
                                missing.append(country2)
                            st.error(f"❌ Could not find data for: {', '.join(missing)}")
                else:
                    st.warning("⚠️ Please enter both country names")
    
    # Footer
    st.markdown("---")
    st.caption("🤖 Powered by Google Gemini AI • 📊 Data from REST Countries API • Phase 3: Advanced AI Analysis")

if __name__ == "__main__":
    main()
