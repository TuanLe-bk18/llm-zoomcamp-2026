import streamlit as st
import os
import sys

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from agent.advisor import MCPAdvisor

st.set_page_config(page_title="MCP Advisor", page_icon="🤖", layout="wide")

st.title("🤖 MCP Advisor")
st.markdown("Discover, compare, and select Model Context Protocol (MCP) servers using natural language.")

# Sidebar setup
with st.sidebar:
    st.header("Configuration")
    api_key = st.text_input("OpenAI API Key", type="password")
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key
        
    st.markdown("---")
    st.markdown("""
    ### Project Phases Implemented
    ✅ Phase 1: Registry Ingestion  
    ✅ Phase 2: Hybrid Retrieval (ES)  
    ✅ Phase 3: Benchmarking  
    ✅ Phase 4: Agent RAG Flow  
    ✅ Phase 7: Streamlit UI  
    """)

# Main UI
query = st.text_area("What do you want the MCP to do?", placeholder="e.g. I need to automate local browser tasks without cloud APIs...")

col1, col2 = st.columns(2)
with col1:
    auth_pref = st.selectbox("Authentication Preference", ["Any", "No Auth Required", "API Key / OAuth"])
with col2:
    local_remote = st.selectbox("Environment", ["Any", "Local execution", "Cloud/Remote"])

if st.button("Search & Recommend", type="primary"):
    if not os.getenv("OPENAI_API_KEY"):
        st.error("Please enter your OpenAI API Key in the sidebar.")
    elif not query:
        st.warning("Please enter a requirement.")
    else:
        with st.spinner("Retrieving candidates & analyzing..."):
            advisor = MCPAdvisor()
            
            # Incorporate constraints into query
            full_query = query
            if auth_pref != "Any":
                full_query += f" (Preference: {auth_pref})"
            if local_remote != "Any":
                full_query += f" (Must support: {local_remote})"
                
            try:
                result = advisor.recommend(full_query)
                st.success("Recommendation Ready!")
                
                st.markdown("### Result")
                st.markdown(result)
                
                # Feedback collection
                st.markdown("---")
                st.write("Was this recommendation helpful?")
                c1, c2, c3 = st.columns([1,1,10])
                with c1:
                    st.button("👍")
                with c2:
                    st.button("👎")
            except Exception as e:
                st.error(f"An error occurred: {e}")
