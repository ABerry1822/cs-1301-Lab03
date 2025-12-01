import streamlit as st
import requests
import google.generativeai as genai
import json
from datetime import datetime

# ---------- Page Configuration ----------
st.set_page_config(
    page_title="Country AI Assistant",
    page_icon="💬",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .chat-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
    }
    .user-message {
        background-color: #e3f2fd;
        padding: 1rem;
        border-radius: 15px;
        margin: 0.5rem 0;
        border-left: 5px solid #2196F3;
    }
    .assistant-message {
        background-color: #f3e5f5;
        padding: 1rem;
        border-radius: 15px;
        margin: 0.5rem 0;
        border-left: 5px solid #9C27B0;
    }
    .country-info-card {
        background-color: #f1f8e9;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 5px solid #8BC34A;
    }
    .stChatInput {
        background-color: white;
        border-radius: 10px;
        padding: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ---------- Initialize Session State ----------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "current_country" not in st.session_state:
    st.session_state.current_country = "United States"
if "country_data" not in st.session_state:
    st.session_state.country_data = None
if "chat_context" not in st.session_state:
    st.session_state.chat_context = []

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
                response = model.generate_content("Hello")
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
    """Fetch comprehensive data for a country"""
    try:
        response = requests.get(f"https://restcountries.com/v3.1/name/{country_name}", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data:
                country = data[0]
                
                # Get additional details
                borders = country.get("borders", [])
                capital_info = country.get("capital", ["Unknown"])
                capital = capital_info[0] if capital_info else "Unknown"
                
                # Get neighboring countries names
                neighbor_names = []
                if borders:
                    try:
                        border_response = requests.get(
                            f"https://restcountries.com/v3.1/alpha?codes={','.join(borders[:5])}",
                            timeout=10
                        )
                        if border_response.status_code == 200:
                            neighbor_data = border_response.json()
                            neighbor_names = [c.get("name", {}).get("common", "") for c in neighbor_data]
                    except:
                        neighbor_names = borders[:3]
                
                return {
                    "name": country.get("name", {}).get("common"),
                    "official_name": country.get("name", {}).get("official"),
                    "capital": capital,
                    "region": country.get("region", "Unknown"),
                    "subregion": country.get("subregion", "Unknown"),
                    "population": country.get("population", 0),
                    "area": country.get("area", 0),
                    "languages": list(country.get("languages", {}).values()) if country.get("languages") else ["Unknown"],
                    "currencies": list(country.get("currencies", {}).keys()) if country.get("currencies") else ["Unknown"],
                    "timezones": country.get("timezones", []),
                    "flag": country.get("flag", "🏳️"),
                    "coordinates": country.get("latlng", [0, 0]),
                    "borders": neighbor_names[:3],
                    "independent": country.get("independent", False),
                    "un_member": country.get("unMember", False),
                    "landlocked": country.get("landlocked", False),
                    "start_of_week": country.get("startOfWeek", "Unknown")
                }
    except Exception as e:
        st.error(f"API Error: {str(e)}")
    return None

def update_country_context(country_data):
    """Update chat context with country information"""
    if country_data:
        context = f"""
        Current Country Context: {country_data['name']}
        - Official Name: {country_data['official_name']}
        - Capital: {country_data['capital']}
        - Region: {country_data['region']} ({country_data['subregion']})
        - Population: {country_data['population']:,}
        - Area: {country_data['area']:,} km²
        - Languages: {', '.join(country_data['languages'])}
        - Currencies: {', '.join(country_data['currencies'])}
        - Timezones: {', '.join(country_data['timezones'][:3])}
        - Neighbors: {', '.join(country_data['borders']) if country_data['borders'] else 'None'}
        - UN Member: {'Yes' if country_data['un_member'] else 'No'}
        - Landlocked: {'Yes' if country_data['landlocked'] else 'No'}
        - Flag: {country_data['flag']}
        """
        return context
    return "No country data available."

# ---------- Chat Functions ----------
def process_chat_message(user_message, country_context):
    """Process user message with Gemini"""
    if not gemini_model:
        return "⚠️ Gemini AI is not available. Please check your API key configuration."
    
    try:
        # Build conversation history
        history_text = ""
        for msg in st.session_state.chat_history[-6:]:  # Last 6 messages for context
            role = "Human" if msg["role"] == "user" else "Assistant"
            history_text += f"{role}: {msg['content']}\n"
        
        # Build system prompt
        system_prompt = f"""You are CountryAI, a knowledgeable assistant specializing in country information.
        
        Current Country Context:
        {country_context}
        
        Conversation History:
        {history_text}
        
        Guidelines:
        1. Use the country data provided above to answer questions accurately
        2. If information isn't in the data, use your general knowledge but mention it
        3. Keep responses conversational but informative
        4. Be helpful and friendly
        5. If asked about comparisons or recommendations, provide balanced insights
        6. Remember we're discussing {st.session_state.current_country} unless specified otherwise
        
        User's Question: {user_message}
        
        Please respond as a helpful country expert:"""
        
        # Generate response
        response = gemini_model.generate_content(system_prompt)
        return response.text.strip()
        
    except Exception as e:
        return f"❌ Sorry, I encountered an error: {str(e)[:100]}"

def handle_special_commands(message):
    """Handle special commands like changing country"""
    message_lower = message.lower().strip()
    
    if message_lower.startswith("switch to "):
        country_name = message_lower.replace("switch to ", "").title()
        return True, country_name
    elif message_lower in ["change country", "new country", "different country"]:
        return True, None
    elif message_lower.startswith("compare with "):
        other_country = message_lower.replace("compare with ", "").title()
        return True, f"compare_{other_country}"
    
    return False, None

# ---------- Main App ----------
def main():
    # Header
    st.markdown('<div class="chat-header"><h1>💬 Country AI Assistant</h1><p>Chat with an AI expert about any country in the world</p></div>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Chat Settings")
        
        if not gemini_model:
            st.error("""
            ⚠️ Gemini AI not available.
            
            To enable the chatbot:
            1. Get API key from https://aistudio.google.com/app/apikey
            2. Add to Streamlit secrets as `GEMINI_API_KEY`
            3. Redeploy app
            """)
        else:
            st.success("✅ AI Assistant is ready!")
        
        st.divider()
        
        # Country Selection
        st.subheader("🌍 Select Country")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🇺🇸 USA", use_container_width=True):
                st.session_state.current_country = "United States"
                st.session_state.country_data = fetch_country_data("United States")
                st.rerun()
        
        with col2:
            if st.button("🇯🇵 Japan", use_container_width=True):
                st.session_state.current_country = "Japan"
                st.session_state.country_data = fetch_country_data("Japan")
                st.rerun()
        
        custom_country = st.text_input(
            "Or enter custom country:",
            placeholder="e.g., France, Brazil, India...",
            key="custom_country"
        )
        
        if st.button("Load Country", use_container_width=True) and custom_country:
            st.session_state.current_country = custom_country
            st.session_state.country_data = fetch_country_data(custom_country)
            st.rerun()
        
        st.divider()
        
        # Chat Controls
        st.subheader("💬 Chat Controls")
        
        if st.button("🔄 Clear Chat History", use_container_width=True):
            st.session_state.chat_history = []
            st.session_state.chat_context = []
            st.rerun()
        
        if st.button("📋 Show Country Info", use_container_width=True):
            if st.session_state.country_data:
                info = update_country_context(st.session_state.country_data)
                st.session_state.chat_history.append({
                    "role": "assistant", 
                    "content": f"Here's current information about {st.session_state.current_country}:\n\n{info}"
                })
                st.rerun()
        
        st.divider()
        
        # Display current country info
        if st.session_state.country_data:
            st.subheader(f"Current: {st.session_state.country_data['flag']} {st.session_state.current_country}")
            st.metric("Population", f"{st.session_state.country_data['population']:,}")
            st.metric("Area", f"{st.session_state.country_data['area']:,} km²")
            st.metric("Capital", st.session_state.country_data['capital'])
    
    # Main Chat Area
    col_main1, col_main2 = st.columns([3, 1])
    
    with col_main1:
        # Display chat history
        chat_container = st.container()
        
        with chat_container:
            for message in st.session_state.chat_history[-20:]:  # Show last 20 messages
                if message["role"] == "user":
                    st.markdown(f'<div class="user-message"><strong>👤 You:</strong> {message["content"]}</div>', 
                              unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="assistant-message"><strong>🤖 CountryAI:</strong> {message["content"]}</div>', 
                              unsafe_allow_html=True)
        
        # Chat input
        user_input = st.chat_input("Ask me anything about countries...", key="chat_input")
        
        if user_input:
            # Handle special commands
            is_command, command_data = handle_special_commands(user_input)
            
            if is_command:
                if command_data and not command_data.startswith("compare_"):
                    # Change country
                    st.session_state.current_country = command_data
                    st.session_state.country_data = fetch_country_data(command_data)
                    if st.session_state.country_data:
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": f"✅ Switched to {command_data}! {st.session_state.country_data['flag']} What would you like to know about {command_data}?"
                        })
                    else:
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": f"❌ Could not find data for '{command_data}'. Please try another country."
                        })
                elif command_data and command_data.startswith("compare_"):
                    # Comparison request
                    other_country = command_data.replace("compare_", "")
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": f"🔍 I'll help you compare {st.session_state.current_country} with {other_country}. What specific aspect would you like to compare?"
                    })
                else:
                    # Generic change country prompt
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": "Please use 'switch to [country name]' or enter a country name in the sidebar."
                    })
            else:
                # Regular chat message
                st.session_state.chat_history.append({
                    "role": "user",
                    "content": user_input
                })
                
                # Get or update country data
                if not st.session_state.country_data:
                    st.session_state.country_data = fetch_country_data(st.session_state.current_country)
                
                # Prepare context
                country_context = update_country_context(st.session_state.country_data)
                
                # Get AI response
                with st.spinner("🤔 Thinking..."):
                    response = process_chat_message(user_input, country_context)
                
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": response
                })
            
            st.rerun()
    
    with col_main2:
        # Suggested Questions
        st.subheader("💡 Try asking:")
        
        questions = [
            "What's the capital?",
            "Tell me about the culture",
            "Best time to visit?",
            "Popular foods?",
            "Compare with [another country]",
            "Economic situation?",
            "Tourist attractions?",
            "Switch to France"
        ]
        
        for q in questions:
            if st.button(f"❓ {q}", use_container_width=True, key=f"q_{q}"):
                # Add to chat
                st.session_state.chat_history.append({
                    "role": "user",
                    "content": q
                })
                
                # Get response
                if st.session_state.country_data:
                    country_context = update_country_context(st.session_state.country_data)
                    with st.spinner("Thinking..."):
                        response = process_chat_message(q, country_context)
                    
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": response
                    })
                    st.rerun()
        
        st.divider()
        
        # Chat Stats
        st.subheader("📊 Chat Stats")
        st.metric("Total Messages", len(st.session_state.chat_history))
        st.metric("Current Country", st.session_state.current_country)
        
        if st.session_state.chat_history:
            last_message = st.session_state.chat_history[-1]
            st.caption(f"Last: {last_message['role']} - {last_message['content'][:30]}...")
    
    # Footer
    st.markdown("---")
    st.caption("💬 Phase 4: AI Chatbot • 🤖 Powered by Google Gemini • 🌍 Data from REST Countries API")
    st.caption("💡 Tip: Try commands like 'switch to Japan' or 'compare with Germany'")

# Initialize country data on first load
if __name__ == "__main__":
    if not st.session_state.country_data:
        st.session_state.country_data = fetch_country_data(st.session_state.current_country)
    main()
