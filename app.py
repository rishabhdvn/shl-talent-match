import streamlit as st
import time
from engine import RecommendationEngine

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="SHL Talent Match AI",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. PREMIUM CSS (Main + Sidebar) ---
st.markdown("""
<style>
    /* MAIN BACKGROUND */
    .stApp {
        background: radial-gradient(circle at 10% 20%, rgb(15, 23, 42) 0%, rgb(23, 37, 84) 90%);
        color: #F8FAFC;
    }

    /* --- SIDEBAR STYLING --- */
    section[data-testid="stSidebar"] {
        background-color: #0F172A; /* Deep Navy */
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Sidebar Inputs (Text & Slider) */
    div[data-testid="stSidebar"] .stTextInput input {
        background-color: #1E293B;
        color: white;
        border: 1px solid #334155;
        border-radius: 8px;
    }
    div[data-testid="stSidebar"] .stTextInput input:focus {
        border-color: #60A5FA;
        box-shadow: 0 0 0 2px rgba(96, 165, 250, 0.2);
    }
    
    /* Slider Color */
    div[data-testid="stSidebar"] .stSlider div[data-testid="stTickBar"] {
        background-color: #334155;
    }
    
    /* MAIN UI GLASS CARDS */
    div[data-testid="stVerticalBlock"] > div[style*="background-color"] {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }

    /* TEXT STYLING */
    .hero-text {
        background: linear-gradient(to right, #60A5FA, #A78BFA, #F472B6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3.5rem;
        font-weight: 800;
        margin-bottom: 10px;
    }
    
    /* METRIC & BUTTONS */
    div[data-testid="stMetricValue"] {
        font-size: 2.2rem !important;
        color: #60A5FA !important;
        text-shadow: 0 0 10px rgba(96, 165, 250, 0.5);
    }
    div[data-testid="stMetricLabel"] { color: #94A3B8 !important; }
    
    .stButton > button {
        background: linear-gradient(90deg, #2563EB, #4F46E5);
        color: white; border: none; height: 55px; border-radius: 12px; font-weight: 600;
    }
    .stButton > button:hover { box-shadow: 0 0 15px rgba(37, 99, 235, 0.5); }
    
    /* Remove Links Underline */
    a { text-decoration: none !important; }
</style>
""", unsafe_allow_html=True)

# --- 3. LOAD ENGINE ---
@st.cache_resource
def load_engine(): return RecommendationEngine()

try: engine = load_engine()
except: st.error("⚠️ Engine not ready. Run scraper."); st.stop()

# --- 4. BEAUTIFUL SIDEBAR ---
with st.sidebar:
    # Logo Area
    st.image("https://www.shl.com/assets/images/shl-logo.svg", width=140)
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("### ⚙️ Intelligence Hub")
    
    # Styled Input
    api_key = st.text_input("Gemini API Key", type="password", help="Leave empty to use Simulation Mode")
    
    st.divider()
    
    # Styled Slider
    st.markdown("**Search Depth**")
    num_recs = st.slider("Max Results", 3, 10, 5, label_visibility="collapsed")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Info Box (Blue Background)
    st.markdown("""
    <div style="background: rgba(59, 130, 246, 0.1); padding: 15px; border-radius: 10px; border: 1px solid rgba(59, 130, 246, 0.2);">
        <small style="color: #94A3B8;">
        <b>💡 Pro Tip:</b><br>
        Try queries like <i>"Java Developer + Leadership"</i> to trigger Hybrid Matching.
        </small>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<div style='margin-top: 50px; color: #475569; font-size: 0.8em;'>v2.4 | SHL AI Project</div>", unsafe_allow_html=True)

# --- 5. MAIN HERO ---
st.markdown('<div class="hero-text">Talent Match AI</div>', unsafe_allow_html=True)
st.markdown("#### ⚡ The Intelligent Bridge Between Job Descriptions and Assessments.")

# --- 6. SEARCH INPUT ---
query = st.text_area("✍️ Describe the Ideal Candidate:", height=100, placeholder="Example: We need a Senior Product Manager who is data-driven (SQL) but has high empathy. Must be under 45 mins.")
search_btn = st.button("🚀 Analyze & Match", type="primary", use_container_width=True)

# --- 7. RESULTS ---
if search_btn and query:
    with st.spinner("🔮 Analyzing Semantics & Intents..."):
        results = engine.search(query, top_k=num_recs)
        
        # AI Logic
        ai_summary = None
        if api_key:
            ai_summary = engine.generate_ai_explanation(query, results, api_key)
        else:
            time.sleep(1) 
            ai_summary = f"**AI Strategy:** Selected a balanced mix of technical modules and behavioral scenarios matching '{query[:20]}...'."

    # A. Display AI Insight
    st.info(ai_summary, icon="🤖")
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown(f"### 🎯 Top {len(results)} Recommendations")

    # B. NATIVE UI LOOP (The Unbreakable Glass Cards)
    for item in results:
        with st.container():
            score = int(item['score'] * 100)
            
            # Safe Type Handling
            raw_type = item.get('test_type', "General")
            display_type = ", ".join(raw_type) if isinstance(raw_type, list) else str(raw_type)
            type_color = ":blue-background" if "Knowledge" in display_type else ":red-background"

            # Columns
            c1, c2, c3 = st.columns([1, 4, 1.5])
            
            with c1:
                st.metric("Match", f"{score}%")
            
            with c2:
                st.markdown(f"#### [{item['name']}]({item['url']})")
                st.markdown(
                    f"{type_color}[{display_type}] "
                    f":grey-background[⏱️ {item['duration']} mins] "
                    f":grey-background[🌍 {item.get('remote support', 'Yes')}]"
                )
                st.caption(item['description'][:230] + "...")
                
            with c3:
                st.markdown("<br>", unsafe_allow_html=True)
                st.link_button("View Details ↗", item['url'])

        # Spacer
        st.markdown("<br>", unsafe_allow_html=True)

    with st.expander("💾 System Output (JSON)"):
        st.json(results)