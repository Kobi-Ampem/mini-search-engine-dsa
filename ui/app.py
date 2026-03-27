"""
Streamlit-based user interface for the mini search engine.
Features file upload, multi-keyword search, boolean queries, and snippet preview.
"""
import streamlit as st
import os
import sys
from pathlib import Path

# Add project root to path so 'engine' module is resolvable
sys.path.insert(0, str(Path(__file__).parent.parent))

from engine.search_engine import SearchEngine

# Configure Streamlit page
st.set_page_config(
    page_title="Mini Search Engine",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .searchbox {
        border: 2px solid #4CAF50;
        border-radius: 5px;
        padding: 10px;
    }
    
    .result-card {
        border-left: 4px solid #4CAF50;
        padding: 15px;
        margin: 10px 0;
        border-radius: 5px;
        background-color: #f9f9f9;
    }
    
    .snippet {
        color: #333;
        font-size: 14px;
        line-height: 1.6;
        margin-top: 8px;
    }
    
    .score-badge {
        background-color: #4CAF50;
        color: white;
        padding: 5px 10px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
    }
    
    .stats {
        background-color: #e3f2fd;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    
    .keyword-highlight {
        background-color: yellow;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'engine' not in st.session_state:
    st.session_state.engine = SearchEngine(remove_stop_words=True)
    st.session_state.documents_loaded = False

# Header
st.title("🔍 Mini Search Engine")
st.markdown("*A lightweight full-text search engine with advanced query capabilities*")

# Sidebar
with st.sidebar:
    st.header("Configuration")
    
    # Stop words toggle
    remove_stops = st.checkbox("Remove stop words", value=True, 
                               help="Stop words like 'the', 'and', 'or' will be filtered")
    
    if remove_stops != st.session_state.engine.index.remove_stops:
        st.session_state.engine = SearchEngine(remove_stop_words=remove_stops)
        st.session_state.documents_loaded = False
    
    st.divider()
    
    # Document management
    st.header("📁 Document Management")
    
    # Show current documents
    doc_count = st.session_state.engine.index.get_document_count()
    st.metric("Documents Indexed", doc_count)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📂 Load Sample Data", use_container_width=True):
            # Load sample documents
            data_dir = Path(__file__).parent.parent / "data"
            count = 0
            for file in data_dir.glob("*.txt"):
                with open(file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    st.session_state.engine.add_document(file.stem, content)
                    count += 1
            st.session_state.documents_loaded = True
            st.success(f"✅ Loaded {count} sample documents")
            st.rerun()
    
    with col2:
        if st.button("🗑️ Clear Index", use_container_width=True):
            st.session_state.engine = SearchEngine(remove_stop_words=remove_stops)
            st.session_state.documents_loaded = False
            st.success("✅ Index cleared")
            st.rerun()
    
    # File uploader
    st.header("📤 Upload Documents")
    uploaded_files = st.file_uploader(
        "Upload text files to search",
        type=['txt', 'md'],
        accept_multiple_files=True,
        help="Support for .txt and .md files"
    )
    
    if uploaded_files:
        for uploaded_file in uploaded_files:
            try:
                content = uploaded_file.read().decode('utf-8')
                st.session_state.engine.add_document(uploaded_file.name, content)
            except Exception as e:
                st.error(f"Error loading {uploaded_file.name}: {str(e)}")
        
        if uploaded_files:
            st.success(f"✅ Loaded {len(uploaded_files)} file(s)")
            st.session_state.documents_loaded = True
    
    # Index statistics
    st.divider()
    st.header("📊 Index Statistics")
    stats = st.session_state.engine.get_statistics()
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Keywords", stats['total_keywords'])
    with col2:
        st.metric("Total Documents", stats['total_documents'])


# Main content
if not st.session_state.documents_loaded:
    st.info("👈 Load sample data or upload documents to get started!")
    st.markdown("""
    ### How to use:
    1. Load sample data from the sidebar or upload your own documents
    2. Use the search tabs below to explore:
       - **Simple Search**: Multi-keyword search with ranking
       - **Boolean Search**: Advanced queries with AND, OR, NOT operators
    3. View results with highlighted snippets and relevance scores
    """)
else:
    # Search interface
    st.header("🔎 Search")
    
    # Create tabs for different search types
    tab1, tab2 = st.tabs(["🔍 Simple Search", "⚙️ Boolean Search"])
    
    with tab1:
        st.subheader("Multi-Keyword Search")
        simple_query = st.text_input(
            "Enter keywords (space-separated):",
            placeholder="e.g., python programming",
            key="simple_search"
        )
        
        col1, col2, col3 = st.columns([2, 1, 1])
        with col2:
            top_k = st.number_input("Top results", min_value=1, max_value=20, value=5)
        
        with col1:
            search_button1 = st.button("🔍 Search", key="btn_simple")
        
        if search_button1 and simple_query:
            results = st.session_state.engine.search_simple(simple_query, top_k=top_k)
            
            # Display performance metrics
            stats = st.session_state.engine.get_statistics()
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Results Found", len(results))
            with col2:
                st.metric("Search Time", f"{stats['last_search_time_ms']:.2f} ms")
            with col3:
                st.metric("Documents Searched", stats['total_documents'])
            
            st.divider()
            
            # Display results
            if results:
                for i, (doc_id, score, snippet) in enumerate(results, 1):
                    with st.container():
                        col1, col2 = st.columns([0.8, 0.2])
                        
                        with col1:
                            st.markdown(f"**Result {i}: {doc_id}**")
                        with col2:
                            st.markdown(f'<span class="score-badge">Score: {score:.1f}</span>', 
                                      unsafe_allow_html=True)
                        
                        st.markdown(f'<div class="snippet">{snippet}</div>', unsafe_allow_html=True)
                        
                        st.divider()
            else:
                st.warning("No results found. Try different keywords.")
    
    with tab2:
        st.subheader("Boolean Query Search")
        st.markdown("""
        **Query syntax:**
        - `AND`: Find documents with all terms (e.g., `python AND programming`)
        - `OR`: Find documents with any term (e.g., `AI OR machine learning`)
        - `NOT`: Exclude documents with a term (e.g., `python NOT beginner`)
        - Combine: `python AND tutorial NOT beginner`
        """)
        
        boolean_query = st.text_input(
            "Enter boolean query:",
            placeholder="e.g., python AND tutorial NOT beginner",
            key="boolean_search"
        )
        
        col1, col2, col3 = st.columns([2, 1, 1])
        with col2:
            top_k_bool = st.number_input("Top results", min_value=1, max_value=20, 
                                         value=5, key="bool_topk")
        
        with col1:
            search_button2 = st.button("🔍 Search", key="btn_boolean")
        
        if search_button2 and boolean_query:
            try:
                results = st.session_state.engine.search_boolean(boolean_query, top_k=top_k_bool)
                
                # Display performance metrics
                stats = st.session_state.engine.get_statistics()
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Results Found", len(results))
                with col2:
                    st.metric("Search Time", f"{stats['last_search_time_ms']:.2f} ms")
                with col3:
                    st.metric("Documents Searched", stats['total_documents'])
                
                st.divider()
                
                # Display results
                if results:
                    for i, (doc_id, score, snippet) in enumerate(results, 1):
                        with st.container():
                            col1, col2 = st.columns([0.8, 0.2])
                            
                            with col1:
                                st.markdown(f"**Result {i}: {doc_id}**")
                            with col2:
                                st.markdown(f'<span class="score-badge">Score: {score:.1f}</span>', 
                                          unsafe_allow_html=True)
                            
                            st.markdown(f'<div class="snippet">{snippet}</div>', 
                                      unsafe_allow_html=True)
                            
                            st.divider()
                else:
                    st.warning("No results found. Try a different query.")
            
            except Exception as e:
                st.error(f"⚠️ Query Error: {str(e)}")
                st.info("Check your boolean query syntax and try again.")
    
    # Information section
    st.divider()
    st.header("ℹ️ Information")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("Features")
        st.markdown("""
        ✅ Case-insensitive search
        ✅ Multi-keyword queries
        ✅ Boolean operators
        ✅ Stop word removal
        ✅ Relevance ranking
        """)
    
    with col2:
        st.subheader("Data Structures")
        st.markdown("""
        📊 Inverted Index
        📊 Hash Maps
        📊 Sets
        📊 Frequency Counters
        """)
    
    with col3:
        st.subheader("Performance")
        st.markdown("""
        ⚡ O(1) keyword lookup
        ⚡ Efficient ranking
        ⚡ Real-time indexing
        ⚡ Performance timing
        """)
