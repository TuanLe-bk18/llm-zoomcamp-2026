import streamlit as st
import os
import sys
import time
import pandas as pd

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from agent.advisor import MCPAdvisor
from monitoring import db

st.set_page_config(page_title="MCP Advisor", page_icon="🤖", layout="wide")

st.title("🤖 MCP Advisor")
st.markdown("Discover, compare, and select Model Context Protocol (MCP) servers using natural language.")

# Sidebar setup
with st.sidebar:
    st.header("Configuration")
    api_key = st.text_input("Gemini API Key", type="password", value=os.getenv("GEMINI_API_KEY", ""))
    if api_key:
        os.environ["GEMINI_API_KEY"] = api_key
        
    st.markdown("---")

@st.cache_resource
def get_advisor():
    return MCPAdvisor()

tab1, tab2 = st.tabs(["Search", "Dashboard"])

with tab1:
    # Main UI
    query = st.text_area("What do you want the MCP to do?", placeholder="e.g. I need to automate local browser tasks without cloud APIs...")
    
    col1, col2 = st.columns(2)
    with col1:
        auth_pref = st.selectbox("Authentication Preference", ["Any", "No Auth Required", "API Key / OAuth"])
    with col2:
        local_remote = st.selectbox("Environment", ["Any", "Local execution", "Cloud/Remote"])
    
    if st.button("Search & Recommend", type="primary"):
        if not os.getenv("GEMINI_API_KEY"):
            st.error("Please enter your Gemini API Key in the sidebar.")
        elif not query:
            st.warning("Please enter a requirement.")
        else:
            with st.spinner("Retrieving candidates & analyzing..."):
                start_time = time.time()
                advisor = get_advisor()
                
                # Incorporate constraints into query
                full_query = query
                if auth_pref != "Any":
                    full_query += f" (Preference: {auth_pref})"
                if local_remote != "Any":
                    full_query += f" (Must support: {local_remote})"
                    
                try:
                    result = advisor.recommend(full_query)
                    latency = (time.time() - start_time) * 1000
                    
                    st.success("Recommendation Ready!")
                    
                    st.markdown("### Result")
                    st.markdown(result["answer"])
                    
                    # Log to DB
                    interaction_id = db.log_interaction(
                        query, 
                        result["rewritten_query"], 
                        latency, 
                        result["recommended_server"], 
                        result["candidates"]
                    )
                    st.session_state['last_interaction_id'] = interaction_id
                    
                except Exception as e:
                    st.error(f"An error occurred: {e}")
                    
    # Feedback collection outside the button so it doesn't clear on click
    if 'last_interaction_id' in st.session_state:
        st.markdown("---")
        st.write("Was this recommendation helpful?")
        c1, c2, c3 = st.columns([1,1,10])
        with c1:
            if st.button("👍", key="upvote"):
                db.update_feedback(st.session_state['last_interaction_id'], 1)
                st.success("Thanks for the feedback!")
        with c2:
            if st.button("👎", key="downvote"):
                db.update_feedback(st.session_state['last_interaction_id'], -1)
                st.success("Thanks for the feedback!")

with tab2:
    st.header("System Dashboard")
    if st.button("Refresh Metrics"):
        pass
        
    metrics = db.get_dashboard_metrics()
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Requests", metrics["total_requests"])
    col2.metric("Avg Latency (ms)", f"{metrics['avg_latency']:.0f}")
    col3.metric("Positive Feedback", metrics["positive_feedback"])
    col4.metric("Negative Feedback", metrics["negative_feedback"])
    
    st.subheader("Top Recommended Servers")
    if metrics["top_servers"]:
        df = pd.DataFrame(metrics["top_servers"])
        df.columns = ["Server", "Recommendation Count"]
        st.dataframe(df, hide_index=True)
    else:
        st.write("No recommendations yet.")
