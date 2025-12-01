import streamlit as st
import requests
import google.generativeai as genai
import time

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
        border-radius: 15px 15px 15px 5px;
        margin: 0.5rem 0;
        border-left: 5px solid #2196F3;
        max-width: 80%;
        margin-left: auto;
    }
    .assistant-message {
        background-color: #f3e5f5;
        padding: 1rem;
        border-radius: 15px 15px 5px 15px;
        margin: 0.5rem 0;
        border-left: 5px solid #9C27B0;
        max-width: 80%;
        margin-right: auto;
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
        margin-top: 20px;
    }
    .suggested-question {
        background-color: #f0f2f6;
        padding: 10px 15px;
        border-radius: 20px;
        margin: 5px;
        cursor: pointer;
        transition: all 0.3s;
        border: 2px solid #667eea;
    }
    .suggested-question:hover {
        background-color: #667eea;
        color: white;
        transform: translateY(-2px);
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
if "chat_started" not in st.session_state:
    st.session_state.chat_started = False

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
        
        # Try different models in order
        models_to_try = [
            "gemini-1.5-flash",      # Most likely to work
            "gemini-1.0-pro",        # Alternative
            "gemini-pro",            # Original
            "models/gemini-1.5-flash" # Full path
        ]
        
        for model_name in models_to_try:
            try:
                model = genai.GenerativeModel(model_name)
                # Quick test
                test_response = model.generate_content("Hello")
                if test_response.text:
                    st.sidebar.success(f"✅ Gemini ready: {model_name}")
                    return model
            except Exception as e:
                continue  # Try next model
        
        st.sidebar.error("❌ All Gemini models failed")
        return None
        
    except Exception as e:
        st.sidebar.error(f"❌ Gemini initialization error: {str(e)[:100]}")
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
                    "independent": country.get("independent", False),
                    "un_member": country.get("unMember", False)
                }
    except Exception as e:
        return None
    return None

def format_number(num):
    """Format large numbers with commas"""
    try:
        return f"{int(num):,}"
    except:
        return str(num)

def get_country_context(country_data):
    """Create context string for the chatbot"""
    if not country_data:
        return "No country data available."
    
    return f"""
    Current Country: {country_data['name']} {country_data['flag']}
    - Official Name: {country_data['official_name']}
    - Capital: {country_data['capital']}
    - Region: {country_data['region']} ({country_data['subregion']})
    - Population: {format_number(country_data['population'])}
    - Area: {format_number(country_data['area'])} km²
    - Languages: {', '.join(country_data['languages'])}
    - Currencies: {', '.join(country_data['currencies'])}
    - Timezones: {len(country_data['timezones'])}
    - UN Member: {'Yes' if country_data['un_member'] else 'No'}
    - Independent: {'Yes' if country_data['independent'] else 'No'}
    """

def generate_chat_response(user_message, country_context, chat_history):
    """Generate response using Gemini"""
    if not gemini_model:
        return "⚠️ Gemini AI is not available. Please check your API key configuration."
    
    try:
        # Build conversation history (last 6 messages)
        history_text = ""
        for msg in chat_history[-6:]:
            role = "User" if msg["role"] == "user" else "Assistant"
            history_text += f"{role}: {msg['content']}\n"
        
        # Build system prompt
        system_prompt = f"""You are CountryAI, a helpful assistant specialized in country information.
        
        Current Country Context:
        {country_context}
        
        Conversation History (recent messages):
        {history_text}
        
        Guidelines:
        1. Use the country data above to answer questions accurately
        2. If information isn't in the data, use general knowledge but mention it's not from current data
        3. Keep responses conversational but informative
        4. Be friendly and helpful
        5. If asked about comparisons, suggest using "switch to [country]" command
        6. Remember we're discussing {st.session_state.current_country}
        
        User's Latest Message: {user_message}
        
        Provide a helpful response as CountryAI:"""
        
        response = gemini_model.generate_content(system_prompt)
        return response.text.strip()
        
    except Exception as e:
        return f"❌ Sorry, I encountered an error: {str(e)[:100]}"

def handle_special_command(message):
    """Handle commands like changing country"""
    message_lower = message.lower().strip()
    
    if message_lower.startswith("switch to "):
        country_name = message_lower.replace("switch to ", "").strip().title()
        return "change_country", country_name
    elif message_lower in ["new country", "change country", "different country"]:
        return "prompt_country", None
    elif message_lower in ["help", "what can you do", "commands"]:
        return "show_help", None
    
    return "normal_message", None

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
        
        # Quick country buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🇺🇸 USA", use_container_width=True, type="secondary"):
                st.session_state.current_country = "United States"
                st.session_state.country_data = fetch_country_data("United States")
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": f"✅ Switched to United States! 🇺🇸 What would you like to know about the USA?"
                })
                st.rerun()
        
        with col2:
            if st.button("🇯🇵 Japan", use_container_width=True, type="secondary"):
                st.session_state.current_country = "Japan"
                st.session_state.country_data = fetch_country_data("Japan")
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": f"✅ Switched to Japan! 🇯🇵 What would you like to know about Japan?"
                })
                st.rerun()
        
        # Custom country input
        custom_country = st.text_input(
            "Or enter custom country:",
            placeholder="e.g., France, Brazil, India...",
            key="custom_country_input"
        )
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("Load Country", use_container_width=True) and custom_country:
                st.session_state.current_country = custom_country
                st.session_state.country_data = fetch_country_data(custom_country)
                if st.session_state.country_data:
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": f"✅ Switched to {custom_country}! What would you like to know?"
                    })
                else:
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": f"❌ Could not find data for '{custom_country}'. Please try another country."
                    })
                st.rerun()
        
        with col_btn2:
            if st.button("Show Info", use_container_width=True):
                if st.session_state.country_data:
                    context = get_country_context(st.session_state.country_data)
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": f"**Current Country Information:**\n\n{context}"
                    })
                    st.rerun()
        
        st.divider()
        
        # Chat Controls
        st.subheader("💬 Chat Controls")
        
        if st.button("🗑️ Clear Chat", use_container_width=True, type="secondary"):
            st.session_state.chat_history = []
            st.session_state.chat_started = False
            st.rerun()
        
        if st.button("🔄 Reset Country", use_container_width=True, type="secondary"):
            st.session_state.current_country = "United States"
            st.session_state.country_data = fetch_country_data("United States")
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": "🔄 Reset to United States. What would you like to know?"
            })
            st.rerun()
        
        st.divider()
        
        # Display current country info
        if st.session_state.country_data:
            st.subheader(f"{st.session_state.country_data['flag']} Current Country")
            st.metric("Country", st.session_state.country_data['name'])
            st.metric("Population", format_number(st.session_state.country_data['population']))
            st.metric("Capital", st.session_state.country_data['capital'])
        
        st.divider()
        
        # Chat Stats
        st.subheader("📊 Chat Stats")
        st.metric("Messages", len(st.session_state.chat_history))
        if st.session_state.chat_history:
            last_role = "You" if st.session_state.chat_history[-1]["role"] == "user" else "AI"
            st.caption(f"Last: {last_role}")
    
    # Main Chat Area
    col_main, col_suggestions = st.columns([3, 1])
    
    with col_main:
        # Display chat history
        chat_container = st.container()
        
        with chat_container:
            if not st.session_state.chat_history and not st.session_state.chat_started:
                st.info("👋 Welcome to Country AI Assistant! Select a country on the left and start chatting.")
                st.session_state.chat_started = True
            
            for message in st.session_state.chat_history:
                if message["role"] == "user":
                    st.markdown(f'<div class="user-message"><strong>👤 You:</strong> {message["content"]}</div>', 
                              unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="assistant-message"><strong>🤖 CountryAI:</strong> {message["content"]}</div>', 
                              unsafe_allow_html=True)
        
        # Chat input
        user_input = st.chat_input("Ask me anything about countries...", key="main_chat_input")
        
        if user_input:
            # Handle special commands
            command_type, command_data = handle_special_command(user_input)
            
            if command_type == "change_country":
                # Change country
                st.session_state.current_country = command_data
                st.session_state.country_data = fetch_country_data(command_data)
                if st.session_state.country_data:
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": f"✅ Switched to {command_data}! What would you like to know?"
                    })
                else:
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": f"❌ Could not find data for '{command_data}'. Please try another country."
                    })
            
            elif command_type == "show_help":
                # Show help
                help_text = """
                **Available Commands:**
                - `switch to [country]` - Change to a different country
                - `help` - Show this help message
                
                **You can ask about:**
                - Capital cities and major cities
                - Population and demographics
                - Languages and culture
                - Economy and currency
                - Travel information
                - History and government
                - And much more!
                """
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": help_text
                })
            
            elif command_type == "prompt_country":
                # Prompt for country change
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": "Please use the sidebar to select a country, or type: `switch to [country name]`"
                })
            
            else:
                # Normal message
                st.session_state.chat_history.append({
                    "role": "user",
                    "content": user_input
                })
                
                # Get or update country data
                if not st.session_state.country_data:
                    st.session_state.country_data = fetch_country_data(st.session_state.current_country)
                
                # Prepare context
                country_context = get_country_context(st.session_state.country_data)
                
                # Get AI response
                with st.spinner("🤔 Thinking..."):
                    response = generate_chat_response(
                        user_input, 
                        country_context, 
                        st.session_state.chat_history
                    )
                
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": response
                })
            
            st.rerun()
    
    with col_suggestions:
        # Suggested Questions
        st.subheader("💡 Try asking:")
        
        suggested_questions = [
            "What's the capital?",
            "Tell me about the culture",
            "Best time to visit?",
            "Popular local foods?",
            "Major tourist attractions?",
            "What language do they speak?",
            "Tell me about the history",
            "What is the currency?",
            "Switch to France",
            "Help me plan a trip"
        ]
        
        for question in suggested_questions:
            if st.button(f"❓ {question}", key=f"q_{question}", use_container_width=True):
                # Add to chat
                st.session_state.chat_history.append({
                    "role": "user",
                    "content": question
                })
                
                # Get response
                if st.session_state.country_data:
                    country_context = get_country_context(st.session_state.country_data)
                    with st.spinner("Thinking..."):
                        response = generate_chat_response(
                            question, 
                            country_context, 
                            st.session_state.chat_history
                        )
                    
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": response
                    })
                    st.rerun()
        
        st.divider()
        
        # Quick Tips
        st.subheader("💎 Quick Tips")
        st.caption("💡 Use **switch to [country]** to change countries")
        st.caption("💡 Try comparing countries")
        st.caption("💡 Ask about travel, culture, or economy")
        st.caption("💡 Use sidebar to load different countries")
    
    # Initialize country data if not loaded
    if not st.session_state.country_data:
        st.session_state.country_data = fetch_country_data(st.session_state.current_country)
    
    # Footer
    st.markdown("---")
    st.caption("💬 Phase 4: AI Chatbot • 🤖 Powered by Google Gemini • 🌍 Data from REST Countries API")
    st.caption("💡 **Tip**: Type 'switch to France' to change countries or use the sidebar")

if __name__ == "__main__":
    main()
