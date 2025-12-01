import streamlit as st
import requests
import google.generativeai as genai
import os

# Page configuration
st.set_page_config(
    page_title="Country Insights with AI",
    page_icon="🤖",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .ai-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
    }
    .insight-card {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #667eea;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

class CountryInsights:
    def __init__(self):
        self.base_url = "https://restcountries.com/v3.1"
        self.session = requests.Session()
        # Configure Gemini - you'll need to set up your API key in Streamlit secrets
        try:
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            self.model = genai.GenerativeModel('gemini-pro')
            self.gemini_available = True
        except:
            self.gemini_available = False

    def get_country_data(self, country_name):
        """Fetch data for a specific country"""
        try:
            response = self.session.get(f"{self.base_url}/name/{country_name}")
            if response.status_code == 200:
                data = response.json()
                return data[0] if data else None
        except:
            return None
        return None

    def get_country_comparison(self, country1, country2):
        """Fetch data for two countries to compare"""
        country1_data = self.get_country_data(country1)
        country2_data = self.get_country_data(country2)
        return country1_data, country2_data

    def generate_travel_guide(self, country_data, traveler_type, duration):
        """Generate a travel guide using Gemini"""
        if not self.gemini_available:
            return "Gemini API not configured. Please check your API key."
        
        country_name = country_data.get('name', {}).get('common', 'Unknown')
        capital = country_data.get('capital', ['Unknown'])[0] if country_data.get('capital') else 'Unknown'
        population = country_data.get('population', 0)
        area = country_data.get('area', 0)
        region = country_data.get('region', 'Unknown')
        languages = list(country_data.get('languages', {}).values()) if country_data.get('languages') else ['Unknown']
        
        prompt = f"""
        Create a detailed {duration}-day travel guide for {country_name} specifically for {traveler_type}.
        
        Country Information:
        - Capital: {capital}
        - Population: {population:,}
        - Area: {area:,} km²
        - Region: {region}
        - Languages: {', '.join(languages)}
        
        Please include:
        1. A brief introduction to the country
        2. Recommended itinerary for {duration} days
        3. Must-visit attractions and hidden gems
        4. Local cuisine recommendations
        5. Cultural tips and etiquette
        6. Budget recommendations for {traveler_type}
        7. Transportation advice
        
        Make it engaging and practical for someone actually planning to visit!
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error generating travel guide: {str(e)}"

    def generate_country_comparison(self, country1_data, country2_data, aspect):
        """Generate a comparison between two countries"""
        if not self.gemini_available:
            return "Gemini API not configured. Please check your API key."
        
        country1_name = country1_data.get('name', {}).get('common', 'Unknown')
        country2_name = country2_data.get('name', {}).get('common', 'Unknown')
        
        prompt = f"""
        Compare {country1_name} and {country2_name} focusing on {aspect}.
        
        {country1_name}:
        - Population: {country1_data.get('population', 0):,}
        - Area: {country1_data.get('area', 0):,} km²
        - Region: {country1_data.get('region', 'Unknown')}
        - Capital: {country1_data.get('capital', ['Unknown'])[0] if country1_data.get('capital') else 'Unknown'}
        - Languages: {list(country1_data.get('languages', {}).values()) if country1_data.get('languages') else ['Unknown']}
        
        {country2_name}:
        - Population: {country2_data.get('population', 0):,}
        - Area: {country2_data.get('area', 0):,} km²
        - Region: {country2_data.get('region', 'Unknown')}
        - Capital: {country2_data.get('capital', ['Unknown'])[0] if country2_data.get('capital') else 'Unknown'}
        - Languages: {list(country2_data.get('languages', {}).values()) if country2_data.get('languages') else ['Unknown']}
        
        Provide a detailed comparison covering:
        1. Key similarities and differences in {aspect}
        2. Cultural aspects related to {aspect}
        3. Economic or developmental perspectives
        4. Unique advantages of each country
        5. Interesting facts or insights
        
        Make the comparison informative and engaging!
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error generating comparison: {str(e)}"

def main():
    st.markdown('<div class="ai-header"><h1>🤖 AI-Powered Country Insights</h1><p>Generate detailed travel guides and country comparisons using Google Gemini</p></div>', unsafe_allow_html=True)
    
    # Initialize insights generator
    insights = CountryInsights()
    
    if not insights.gemini_available:
        st.warning("""
        ⚠️ Gemini API not configured. To use this page:
        1. Get a free API key from https://aistudio.google.com/app/apikey
        2. Add it to your Streamlit secrets as GEMINI_API_KEY
        3. Redeploy your app
        """)
    
    # Tab layout for different functionalities
    tab1, tab2 = st.tabs(["🎒 Travel Guide Generator", "📊 Country Comparison"])
    
    with tab1:
        st.subheader("Generate Personalized Travel Guides")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # User Input 1: Country selection
            country_name = st.text_input(
                "Enter a country name:",
                placeholder="e.g., France, Japan, Brazil...",
                help="Enter the name of the country you want to visit"
            )
            
            # User Input 2: Traveler type
            traveler_type = st.selectbox(
                "Type of traveler:",
                ["Backpacker/Budget", "Family", "Luxury", "Adventure", "Cultural", "Business"],
                help="Select the type of travel experience you're looking for"
            )
        
        with col2:
            # User Input 3: Trip duration
            duration = st.slider(
                "Trip duration (days):",
                min_value=3,
                max_value=21,
                value=7,
                step=1,
                help="How many days will you be traveling?"
            )
            
            # User Input 4: Travel focus
            travel_focus = st.multiselect(
                "Interests:",
                ["History", "Food", "Nature", "Cities", "Beaches", "Mountains", "Culture", "Nightlife"],
                default=["Culture", "Food"],
                help="Select your main interests"
            )
        
        if st.button("🎯 Generate Travel Guide", type="primary"):
            if country_name:
                with st.spinner(f"🧳 Creating your perfect {duration}-day {traveler_type.lower()} itinerary for {country_name}..."):
                    country_data = insights.get_country_data(country_name)
                    
                    if country_data:
                        travel_guide = insights.generate_travel_guide(country_data, traveler_type, duration)
                        
                        st.subheader(f"🎒 {duration}-Day {traveler_type} Guide for {country_name}")
                        st.markdown(f'<div class="insight-card">{travel_guide}</div>', unsafe_allow_html=True)
                        
                        # Display basic country info
                        col_info1, col_info2, col_info3 = st.columns(3)
                        with col_info1:
                            st.metric("Capital", country_data.get('capital', ['Unknown'])[0] if country_data.get('capital') else 'Unknown')
                        with col_info2:
                            st.metric("Population", f"{country_data.get('population', 0):,}")
                        with col_info3:
                            languages = list(country_data.get('languages', {}).values()) if country_data.get('languages') else ['Unknown']
                            st.metric("Languages", ", ".join(languages[:2]) + ("..." if len(languages) > 2 else ""))
                    else:
                        st.error(f"❌ Could not find data for '{country_name}'. Please check the spelling and try again.")
            else:
                st.warning("⚠️ Please enter a country name.")
    
    with tab2:
        st.subheader("Compare Two Countries")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # User Input 1: First country
            country1 = st.text_input(
                "First country:",
                placeholder="e.g., United States",
                key="country1"
            )
        
        with col2:
            # User Input 2: Second country
            country2 = st.text_input(
                "Second country:",
                placeholder="e.g., China", 
                key="country2"
            )
        
        # User Input 3: Comparison aspect
        comparison_aspect = st.selectbox(
            "Compare based on:",
            ["Culture and Lifestyle", "Economic Development", "Tourism and Attractions", 
             "Geography and Climate", "History and Heritage", "Overall Quality of Life"],
            help="Select what aspect you want to compare"
        )
        
        if st.button("📈 Generate Comparison", type="primary"):
            if country1 and country2:
                with st.spinner(f"🔍 Analyzing {country1} vs {country2}..."):
                    country1_data, country2_data = insights.get_country_comparison(country1, country2)
                    
                    if country1_data and country2_data:
                        comparison = insights.generate_country_comparison(
                            country1_data, country2_data, comparison_aspect
                        )
                        
                        st.subheader(f"⚖️ {country1} vs {country2}: {comparison_aspect}")
                        st.markdown(f'<div class="insight-card">{comparison}</div>', unsafe_allow_html=True)
                        
                        # Quick stats comparison
                        st.subheader("📊 Quick Stats Comparison")
                        col_stat1, col_stat2 = st.columns(2)
                        
                        with col_stat1:
                            st.metric(
                                f"🇺🇸 {country1} Population", 
                                f"{country1_data.get('population', 0):,}",
                                delta=None
                            )
                            st.metric(
                                f"🇺🇸 {country1} Area", 
                                f"{country1_data.get('area', 0):,} km²",
                                delta=None
                            )
                        
                        with col_stat2:
                            st.metric(
                                f"🇨🇳 {country2} Population", 
                                f"{country2_data.get('population', 0):,}",
                                delta=None
                            )
                            st.metric(
                                f"🇨🇳 {country2} Area", 
                                f"{country2_data.get('area', 0):,} km²", 
                                delta=None
                            )
                    
                    else:
                        missing = []
                        if not country1_data: missing.append(country1)
                        if not country2_data: missing.append(country2)
                        st.error(f"❌ Could not find data for: {', '.join(missing)}")
            else:
                st.warning("⚠️ Please enter both country names.")

    # Footer
    st.markdown("---")
    st.caption("💡 Powered by Google Gemini AI • Data from REST Countries API")

if __name__ == "__main__":
    main()
