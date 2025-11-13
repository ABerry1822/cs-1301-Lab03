import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Country Analysis",
    page_icon="🌍",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .country-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .metric-container {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

class CountryAnalyzer:
    def __init__(self):
        self.base_url = "https://restcountries.com/v3.1"
        self.session = requests.Session()
    
    def get_all_countries(self):
        """Fetch all countries data with multiple fallback methods"""
        try:
            with st.spinner('🌍 Fetching country data from around the world...'):
                # Try the main endpoint first
                response = self.session.get(f"{self.base_url}/all", timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if data and len(data) > 0:
                        st.success("✅ Live data loaded successfully!")
                        return data
                
                # If main endpoint fails, try alternative approaches
                return self.get_countries_by_regions()
                
        except requests.exceptions.RequestException as e:
            st.warning("⚠️ Using sample data for demonstration")
            return self.get_sample_data()
    
    def get_countries_by_regions(self):
        """Get countries by querying each region separately"""
        regions = ["africa", "americas", "asia", "europe", "oceania"]
        all_countries = []
        
        for region in regions:
            try:
                response = self.session.get(f"{self.base_url}/region/{region}", timeout=10)
                if response.status_code == 200:
                    region_data = response.json()
                    all_countries.extend(region_data)
            except:
                continue
        
        if all_countries:
            st.success("✅ Live data loaded by regions!")
            return all_countries
        else:
            st.warning("⚠️ Using sample dataset")
            return self.get_sample_data()
    
    def get_sample_data(self):
        """Provide sample data when API is unavailable"""
        sample_countries = [
            {
                'name': {'common': 'United States', 'official': 'United States of America'},
                'population': 331002651,
                'area': 9833517,
                'region': 'Americas',
                'capital': ['Washington D.C.'],
                'languages': {'eng': 'English'},
                'flags': {'png': 'https://flagcdn.com/w320/us.png'}
            },
            {
                'name': {'common': 'India', 'official': 'Republic of India'},
                'population': 1380004385,
                'area': 3287263,
                'region': 'Asia',
                'capital': ['New Delhi'],
                'languages': {'hin': 'Hindi', 'eng': 'English'},
                'flags': {'png': 'https://flagcdn.com/w320/in.png'}
            },
            {
                'name': {'common': 'China', 'official': "People's Republic of China"},
                'population': 1402112000,
                'area': 9706961,
                'region': 'Asia',
                'capital': ['Beijing'],
                'languages': {'zho': 'Chinese'},
                'flags': {'png': 'https://flagcdn.com/w320/cn.png'}
            },
            {
                'name': {'common': 'Brazil', 'official': 'Federative Republic of Brazil'},
                'population': 212559417,
                'area': 8515767,
                'region': 'Americas',
                'capital': ['Brasília'],
                'languages': {'por': 'Portuguese'},
                'flags': {'png': 'https://flagcdn.com/w320/br.png'}
            },
            {
                'name': {'common': 'Germany', 'official': 'Federal Republic of Germany'},
                'population': 83240525,
                'area': 357114,
                'region': 'Europe',
                'capital': ['Berlin'],
                'languages': {'deu': 'German'},
                'flags': {'png': 'https://flagcdn.com/w320/de.png'}
            },
            {
                'name': {'common': 'Nigeria', 'official': 'Federal Republic of Nigeria'},
                'population': 206139587,
                'area': 923768,
                'region': 'Africa',
                'capital': ['Abuja'],
                'languages': {'eng': 'English'},
                'flags': {'png': 'https://flagcdn.com/w320/ng.png'}
            },
            {
                'name': {'common': 'Australia', 'official': 'Commonwealth of Australia'},
                'population': 25499884,
                'area': 7692024,
                'region': 'Oceania',
                'capital': ['Canberra'],
                'languages': {'eng': 'English'},
                'flags': {'png': 'https://flagcdn.com/w320/au.png'}
            },
            {
                'name': {'common': 'Canada', 'official': 'Canada'},
                'population': 38005238,
                'area': 9984670,
                'region': 'Americas',
                'capital': ['Ottawa'],
                'languages': {'eng': 'English', 'fra': 'French'},
                'flags': {'png': 'https://flagcdn.com/w320/ca.png'}
            },
            {
                'name': {'common': 'Japan', 'official': 'Japan'},
                'population': 125836021,
                'area': 377930,
                'region': 'Asia',
                'capital': ['Tokyo'],
                'languages': {'jpn': 'Japanese'},
                'flags': {'png': 'https://flagcdn.com/w320/jp.png'}
            },
            {
                'name': {'common': 'France', 'official': 'French Republic'},
                'population': 67391582,
                'area': 551695,
                'region': 'Europe',
                'capital': ['Paris'],
                'languages': {'fra': 'French'},
                'flags': {'png': 'https://flagcdn.com/w320/fr.png'}
            }
        ]
        return sample_countries

def format_population(population):
    """Format population numbers with commas and appropriate units"""
    if population >= 1_000_000_000:
        return f"{population/1_000_000_000:.2f}B"
    elif population >= 1_000_000:
        return f"{population/1_000_000:.2f}M"
    elif population >= 1_000:
        return f"{population/1_000:.1f}K"
    else:
        return f"{population:,}"

def create_population_table(countries_data, selected_countries):
    """Create a table showing population comparison"""
    filtered_data = []
    for country in countries_data:
        country_name = country.get('name', {}).get('common', 'Unknown')
        if country_name in selected_countries:
            filtered_data.append({
                'Country': country_name,
                'Population': country.get('population', 0),
                'Formatted Population': format_population(country.get('population', 0)),
                'Region': country.get('region', 'Unknown'),
                'Area (km²)': f"{country.get('area', 0):,}" if country.get('area', 0) > 0 else 'Unknown',
                'Density (/km²)': f"{(country.get('population', 0) / country.get('area', 1)):,.1f}" if country.get('area', 0) > 0 else 'Unknown'
            })
    
    if not filtered_data:
        return None
    
    df = pd.DataFrame(filtered_data)
    return df[['Country', 'Formatted Population', 'Region', 'Area (km²)', 'Density (/km²)']]

def create_region_summary(countries_data):
    """Create a summary table of regions"""
    regions = {}
    for country in countries_data:
        region = country.get('region', 'Unknown')
        if region not in regions:
            regions[region] = {'count': 0, 'population': 0, 'area': 0}
        
        regions[region]['count'] += 1
        regions[region]['population'] += country.get('population', 0)
        regions[region]['area'] += country.get('area', 0)
    
    summary_data = []
    for region, stats in regions.items():
        avg_population = stats['population'] / stats['count'] if stats['count'] > 0 else 0
        summary_data.append({
            'Region': region,
            'Countries': stats['count'],
            'Total Population': format_population(stats['population']),
            'Average Population': format_population(avg_population),
            'Total Area (km²)': f"{stats['area']:,}"
        })
    
    return pd.DataFrame(summary_data)

def display_country_details(country):
    """Display individual country information in a clean layout"""
    name = country.get('name', {}).get('common', 'Unknown')
    official_name = country.get('name', {}).get('official', '')
    population = country.get('population', 0)
    area = country.get('area', 0)
    region = country.get('region', 'Unknown')
    capital = country.get('capital', ['Unknown'])[0] if country.get('capital') else 'Unknown'
    density = population / area if area and area > 0 else 0
    
    # Country header with flag
    col_header1, col_header2 = st.columns([3, 1])
    
    with col_header1:
        st.markdown(f'<div class="country-card"><h3>🇺🇳 {name}</h3><p>{official_name}</p></div>', unsafe_allow_html=True)
    
    with col_header2:
        if country.get('flags'):
            flag_url = country.get('flags', {}).get('png') or country.get('flags', {}).get('svg')
            if flag_url:
                st.image(flag_url, width=100, caption=f"Flag of {name}")
    
    # Metrics in a clean grid
    st.subheader("Country Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="👥 Population", 
            value=format_population(population)
        )
    
    with col2:
        st.metric(
            label="🗺️ Area", 
            value=f"{area:,.0f} km²" if area else "Unknown"
        )
    
    with col3:
        st.metric(
            label="🏛️ Capital", 
            value=capital
        )
    
    with col4:
        st.metric(
            label="🌍 Region", 
            value=region
        )
    
    # Additional metrics
    col5, col6 = st.columns(2)
    
    with col5:
        st.metric(
            label="📊 Population Density", 
            value=f"{density:,.1f}/km²" if density else "Unknown"
        )
    
    with col6:
        # Show languages if available
        languages = country.get('languages', {})
        if languages:
            lang_list = list(languages.values())[:3]  # Show first 3 languages
            st.metric(
                label="🗣️ Languages", 
                value=", ".join(lang_list) + ("..." if len(languages) > 3 else "")
            )

def main():
    st.markdown('<h1 class="main-header">🌍 Country Analysis Dashboard</h1>', unsafe_allow_html=True)
    
    # Initialize analyzer
    analyzer = CountryAnalyzer()
    
    # Sidebar for user inputs
    st.sidebar.title("🔧 Analysis Controls")
    
    # User input 1: Region filter
    regions = ["All", "Africa", "Americas", "Asia", "Europe", "Oceania"]
    selected_region = st.sidebar.selectbox(
        "Filter by Region",
        regions,
        index=0,
        help="Select a specific region or view all regions"
    )
    
    # User input 2: Minimum population filter
    min_population = st.sidebar.slider(
        "Minimum Population",
        min_value=0,
        max_value=100_000_000,
        value=1_000_000,
        step=1_000_000,
        help="Filter countries by minimum population"
    )
    
    # User input 3: Number of countries to display
    country_limit = st.sidebar.slider(
        "Number of Countries to Display",
        min_value=5,
        max_value=50,
        value=10,
        help="Select how many countries to show in lists and charts"
    )
    
    # User input 4: Sort criteria
    sort_by = st.sidebar.selectbox(
        "Sort Countries By",
        ["Population", "Area", "Name"],
        index=0,
        help="Choose how to sort the country list"
    )
    
    # Fetch all countries data
    countries_data = analyzer.get_all_countries()
    
    if not countries_data:
        st.error("""
        Unable to load country data. Please check your internet connection and try again.
        """)
        return
    
    # Filter and sort data based on user inputs
    filtered_countries = []
    for country in countries_data:
        population = country.get('population', 0)
        region = country.get('region', '')
        
        # Apply filters
        if selected_region != "All" and region != selected_region:
            continue
        if population < min_population:
            continue
            
        filtered_countries.append(country)
    
    # Sort based on user selection
    if sort_by == "Population":
        filtered_countries.sort(key=lambda x: x.get('population', 0), reverse=True)
    elif sort_by == "Area":
        filtered_countries.sort(key=lambda x: x.get('area', 0), reverse=True)
    else:  # Name
        filtered_countries.sort(key=lambda x: x.get('name', {}).get('common', ''))
    
    # Limit number of countries
    filtered_countries = filtered_countries[:country_limit]
    
    # Display summary metrics
    st.subheader("📊 Global Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_countries = len(filtered_countries)
    total_population = sum(country.get('population', 0) for country in filtered_countries)
    avg_population = total_population / total_countries if total_countries > 0 else 0
    total_area = sum(country.get('area', 0) for country in filtered_countries)
    
    with col1:
        st.metric("Countries Analyzed", total_countries)
    with col2:
        st.metric("Total Population", format_population(total_population))
    with col3:
        st.metric("Average Population", format_population(avg_population))
    with col4:
        st.metric("Total Area", f"{total_area:,.0f} km²")
    
    # Main content area with tabs
    tab1, tab2, tab3 = st.tabs(["🏠 Country Explorer", "📈 Data Analysis", "🌐 Regional Insights"])
    
    with tab1:
        st.subheader("Country Details")
        
        if filtered_countries:
            # Country selector
            country_names = [country.get('name', {}).get('common', 'Unknown') for country in filtered_countries]
            selected_country = st.selectbox("Select a country to view details:", country_names)
            
            if selected_country:
                country_data = next((c for c in filtered_countries if c.get('name', {}).get('common') == selected_country), None)
                if country_data:
                    display_country_details(country_data)
        else:
            st.warning("No countries match the current filters. Try adjusting the filters above.")
    
    with tab2:
        st.subheader("Data Analysis")
        
        if len(filtered_countries) > 1:
            col1, col2 = st.columns(2)
            
            with col1:
                # Population comparison table
                st.subheader("📊 Population Comparison")
                selected_for_table = st.multiselect(
                    "Select countries to compare:",
                    [c.get('name', {}).get('common', 'Unknown') for c in filtered_countries],
                    default=[c.get('name', {}).get('common', 'Unknown') for c in filtered_countries[:3]]
                )
                
                if selected_for_table:
                    pop_table = create_population_table(filtered_countries, selected_for_table)
                    if pop_table is not None:
                        st.dataframe(pop_table, use_container_width=True)
                    else:
                        st.info("Select countries to see comparison table")
                else:
                    st.info("Select countries from the list above to compare their data")
            
            with col2:
                # Quick statistics
                st.subheader("📈 Quick Stats")
                if filtered_countries:
                    largest_country = max(filtered_countries, key=lambda x: x.get('population', 0))
                    smallest_country = min(filtered_countries, key=lambda x: x.get('population', 0))
                    
                    st.metric(
                        "Largest Population", 
                        f"{largest_country.get('name', {}).get('common', 'Unknown')} ({format_population(largest_country.get('population', 0))})"
                    )
                    st.metric(
                        "Smallest Population", 
                        f"{smallest_country.get('name', {}).get('common', 'Unknown')} ({format_population(smallest_country.get('population', 0))})"
                    )
                    
                    # Area comparison
                    largest_area = max(filtered_countries, key=lambda x: x.get('area', 0))
                    st.metric(
                        "Largest Area", 
                        f"{largest_area.get('name', {}).get('common', 'Unknown')} ({largest_area.get('area', 0):,} km²)"
                    )
        else:
            st.info("Select at least 2 countries to see data analysis features.")
    
    with tab3:
        st.subheader("Regional Insights")
        
        # Regional statistics table
        region_table = create_region_summary(countries_data)
        if not region_table.empty:
            st.subheader("🌍 Regional Summary")
            st.dataframe(region_table, use_container_width=True)
        
        # Regional breakdown
        st.subheader("Regional Distribution")
        region_counts = {}
        for country in filtered_countries:
            region = country.get('region', 'Unknown')
            region_counts[region] = region_counts.get(region, 0) + 1
        
        if region_counts:
            for region, count in region_counts.items():
                st.write(f"**{region}**: {count} countries")
                # Simple bar using text (since we don't have plotly)
                bar_length = int((count / len(filtered_countries)) * 50)
                st.write("▮" * bar_length + f" ({count/len(filtered_countries)*100:.1f}%)")
        else:
            st.info("Regional data will be displayed when countries are available.")

    # Footer
    st.markdown("---")
    st.markdown(
        "📡 Data provided by [REST Countries API](https://restcountries.com/) | "
        "🕐 Last updated: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

if __name__ == "__main__":
    main()
