import os

import streamlit as st
import requests
import pandas as pd

API_BASE_URL = os.getenv("QUERYZEN_API_URL", "http://127.0.0.1:8000")

# Page configuration
st.set_page_config(
    page_title="QueryZen - AI SQL Generator",
    page_icon="🧠",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-title {
        text-align: center;
        color: #1f77b4;
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        text-align: center;
        color: #666;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    .success-msg {
        padding: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 0.25rem;
        color: #155724;
        margin: 1rem 0;
    }
    .error-msg {
        padding: 0.5rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 0.25rem;
        color: #721c24;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-title">🧠 Welcome to QueryZen</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">AI-Powered SQL Query Generator</p>', unsafe_allow_html=True)

# Sidebar with sample queries
with st.sidebar:
    st.header("💡 Sample Queries")
    sample_queries = [
        "Show all countries",
        "Find countries with population over 50 million", 
        "List cities in the United States",
        "Get the top 10 most populated countries",
        "Show countries in Europe"
    ]
    
    st.write("Click to use:")
    for query in sample_queries:
        if st.button(f"📝 {query}", key=f"sample_{query}", use_container_width=True):
            st.session_state["query_input"] = query

# Main query input
query_input = st.text_area(
    "📝 Enter your natural language query:",
    value=st.session_state.get("query_input", ""),
    height=100,
    placeholder="e.g., Show me all customers who made purchases over $1000",
    help="Describe what data you want to retrieve in plain English"
)

# Update session state
st.session_state["query_input"] = query_input

# Generate SQL button
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    generate_clicked = st.button(
        "🚀 Generate SQL Query", 
        type="primary", 
        use_container_width=True,
        disabled=not query_input.strip()
    )

if generate_clicked and query_input.strip():
    with st.spinner("🤖 Generating SQL query..."):
        try:
            response = requests.post(
                f"{API_BASE_URL}/generate_sql/",
                json={"query": query_input},
                timeout=30
            )
            if response.status_code == 200:
                sql_query = response.json().get("sql_query", "Error generating query")
                st.session_state["generated_sql"] = sql_query
                st.markdown('<div class="success-msg">✅ SQL query generated successfully!</div>', unsafe_allow_html=True)
            else:
                detail = response.json().get("detail", "Unknown error")
                st.markdown(f'<div class="error-msg">❌ Failed to generate SQL query: {detail}</div>', unsafe_allow_html=True)
        except requests.exceptions.RequestException as e:
            st.markdown(f'<div class="error-msg">❌ Connection error: {str(e)}</div>', unsafe_allow_html=True)

# Display generated SQL if available
if "generated_sql" in st.session_state and st.session_state["generated_sql"]:
    st.subheader("📄 Generated SQL Query")
    st.code(st.session_state["generated_sql"], language="sql")
    
    # Execute SQL button
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        execute_clicked = st.button(
            "▶️ Execute SQL Query", 
            type="primary", 
            use_container_width=True
        )
    
    if execute_clicked:
        with st.spinner("⚡ Executing query..."):
            try:
                response = requests.post(
                    f"{API_BASE_URL}/execute_sql/",
                    json={"query": st.session_state["generated_sql"]},
                    timeout=30
                )
                if response.status_code == 200:
                    data = response.json()
                    results = data.get("results", [])
                    optimization_tips = data.get("optimization_tips", "")
                    
                    st.markdown('<div class="success-msg">✅ Query executed successfully!</div>', unsafe_allow_html=True)
                    
                    # Display results
                    if results:
                        st.subheader("📊 Query Results")
                        
                        # Create DataFrame for better display
                        df = pd.DataFrame(results)
                        st.dataframe(df, use_container_width=True)
                        
                        # Show metrics
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("📈 Rows Found", len(results))
                        with col2:
                            st.metric("📋 Columns", len(df.columns))
                        with col3:
                            st.metric("✅ Status", "Success")
                        
                        # Download option
                        csv = df.to_csv(index=False)
                        st.download_button(
                            label="📥 Download Results as CSV",
                            data=csv,
                            file_name="query_results.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                    else:
                        st.info("📭 No results found for this query")
                    
                    # Show optimization tips
                    if optimization_tips and optimization_tips != "No optimization tips available.":
                        st.subheader("💡 Optimization Tips")
                        st.info(optimization_tips)
                        
                else:
                    detail = response.json().get("detail", "Unknown error")
                    st.markdown(f'<div class="error-msg">❌ Failed to execute query: {detail}</div>', unsafe_allow_html=True)
            except requests.exceptions.RequestException as e:
                st.markdown(f'<div class="error-msg">❌ Connection error: {str(e)}</div>', unsafe_allow_html=True)

# Clear button
if "generated_sql" in st.session_state and st.session_state["generated_sql"]:
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🗑️ Clear Query", use_container_width=True):
            if "generated_sql" in st.session_state:
                del st.session_state["generated_sql"]
            if "query_input" in st.session_state:
                del st.session_state["query_input"]
            st.rerun()

# Footer
st.markdown("---")
col1, col2 = st.columns(2)
with col1:
    st.markdown("🔗 **API Docs:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)")
with col2:
    st.markdown("📚 **GitHub:** [Abhijeet Patil](https://github.com/abhiee-9)")