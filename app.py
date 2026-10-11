"""
app.py
Streamlit web application for Text-to-SQL querying and visual analytics powered by Sarvam AI.
"""

import os
import streamlit as st
import pandas as pd
from config import Config
from db_connector import MySQLConnector
from sql_generator import SarvamSQLGenerator
from visualizer import create_visualization
from generate_dummy_data import seed_database, generate_sql_file

# Set Streamlit Page Configuration
st.set_page_config(
    page_title="Text-to-SQL & Analytics | Sarvam AI",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(90deg, #1E3A8A, #3B82F6, #10B981);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1rem;
        color: #64748B;
        margin-bottom: 1.5rem;
    }
    .stMetric {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        padding: 12px;
        border-radius: 8px;
    }
    .status-badge-ok {
        background-color: #DCFCE7;
        color: #166534;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .status-badge-err {
        background-color: #FEE2E2;
        color: #991B1B;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.85rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []
if "sarvam_api_key" not in st.session_state:
    st.session_state.sarvam_api_key = Config.SARVAM_API_KEY
if "db_host" not in st.session_state:
    st.session_state.db_host = Config.MYSQL_HOST
if "db_port" not in st.session_state:
    st.session_state.db_port = Config.MYSQL_PORT
if "db_user" not in st.session_state:
    st.session_state.db_user = Config.MYSQL_USER
if "db_pass" not in st.session_state:
    st.session_state.db_pass = Config.MYSQL_PASSWORD
if "db_name" not in st.session_state:
    st.session_state.db_name = Config.MYSQL_DATABASE
if "selected_model" not in st.session_state:
    st.session_state.selected_model = Config.SARVAM_MODEL
if "active_prompt" not in st.session_state:
    st.session_state.active_prompt = None

# Sidebar Configuration
with st.sidebar:
    st.image("https://img.icons8.com/color/96/artificial-intelligence.png", width=64)
    st.title("Settings & DB Config")
    
    # 1. Sarvam AI Section
    with st.expander("🤖 Sarvam AI Settings", expanded=True):
        st.session_state.sarvam_api_key = st.text_input(
            "Sarvam API Key",
            value=st.session_state.sarvam_api_key,
            type="password",
            help="Enter your Sarvam AI API subscription key"
        )
        st.session_state.selected_model = st.selectbox(
            "Model",
            options=["sarvam-105b", "sarvam-105b-conversations", "deepseekv4-flash", "glm5.2", "gemma4"],
            index=0,
            help="Select the Sarvam AI model"
        )
        
    # 2. MySQL Connection Section
    with st.expander("🗄️ MySQL Connection", expanded=True):
        st.session_state.db_host = st.text_input("Host", value=st.session_state.db_host)
        st.session_state.db_port = st.number_input("Port", value=int(st.session_state.db_port), min_value=1, max_value=65535)
        st.session_state.db_user = st.text_input("Username", value=st.session_state.db_user)
        st.session_state.db_pass = st.text_input("Password", value=st.session_state.db_pass, type="password")
        st.session_state.db_name = st.text_input("Database Name", value=st.session_state.db_name)
        
        connector = MySQLConnector(
            host=st.session_state.db_host,
            port=st.session_state.db_port,
            user=st.session_state.db_user,
            password=st.session_state.db_pass,
            database=st.session_state.db_name
        )
        
        if st.button("🔌 Test Connection", use_container_width=True):
            with st.spinner("Connecting to MySQL..."):
                ok, msg = connector.test_connection()
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)

    # 3. Dummy Database Seeder Section
    with st.expander("📦 Dummy Database Seeder", expanded=False):
        st.markdown("Populate MySQL with a rich **Retail & E-commerce Analytics** database (Customers, Products, Orders, Items, Reviews).")
        if st.button("⚡ Seed Dummy DB Now", use_container_width=True):
            with st.spinner("Generating and populating dummy database..."):
                ok, msg = seed_database(
                    host=st.session_state.db_host,
                    port=st.session_state.db_port,
                    user=st.session_state.db_user,
                    password=st.session_state.db_pass,
                    db_name=st.session_state.db_name
                )
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(f"Seeding failed: {msg}")

        if st.button("📄 Generate dummy_data.sql File", use_container_width=True):
            sql_path = generate_sql_file("dummy_data.sql", db_name=st.session_state.db_name)
            st.success(f"Generated {sql_path} in workspace!")

    # 4. Schema Explorer
    with st.expander("🔍 Schema Explorer", expanded=False):
        if st.button("Refresh Schema"):
            st.rerun()
        schema = connector.get_schema_info()
        if "error" in schema:
            st.info("Connect to database to inspect schema.")
        else:
            for table_name, details in schema.items():
                with st.expander(f"📁 {table_name}"):
                    cols = details.get("columns", [])
                    st.write("**Columns:**")
                    for c in cols:
                        st.caption(f"- `{c['name']}` ({c['type']})")
                    fks = details.get("foreign_keys", [])
                    if fks:
                        st.write("**Foreign Keys:**")
                        for fk in fks:
                            st.caption(f"- `{fk['column']}` → `{fk['ref_table']}.{fk['ref_column']}`")

    st.markdown("---")
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# Main Application Header
col_title, col_status = st.columns([4, 1])
with col_title:
    st.markdown('<div class="main-title">Text-to-SQL & Visual Analytics</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Query your MySQL database using natural English & visualize trends with Sarvam AI</div>', unsafe_allow_html=True)

with col_status:
    # Test connection silently for status badge
    db_ok, _ = connector.test_connection()
    if db_ok:
        st.markdown('<span class="status-badge-ok">● DB Connected</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-badge-err">● DB Disconnected</span>', unsafe_allow_html=True)

# Quick Prompts / Pills
st.markdown("**Sample Questions to Try:**")
sample_queries = [
    "What are the top 5 product categories by total sales revenue?",
    "Show monthly sales trend for the past year",
    "What is the distribution of orders by payment method?",
    "Who are the top 5 customers by total spending?",
    "What is the total revenue, total orders, and average order value?"
]

p_cols = st.columns(len(sample_queries))
for i, query in enumerate(sample_queries):
    with p_cols[i]:
        if st.button(query, key=f"pill_{i}", use_container_width=True):
            st.session_state.active_prompt = query

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "user":
            st.markdown(message["content"])
        else:
            # Explanation
            if message.get("explanation"):
                st.markdown(f"**Insight:** {message['explanation']}")

            # Reasoning
            if message.get("reasoning"):
                with st.expander("🧠 Model Reasoning", expanded=False):
                    st.markdown(message["reasoning"])

            # Generated SQL Query
            if message.get("sql"):
                with st.expander("🛠️ View Generated MySQL Query", expanded=False):
                    st.code(message["sql"], language="sql")

            # Visualization
            if message.get("figure"):
                st.plotly_chart(message["figure"], use_container_width=True)

            # Data Table
            if message.get("df") is not None and not message["df"].empty:
                with st.expander("📋 View Data Table", expanded=not message.get("figure")):
                    st.dataframe(message["df"], use_container_width=True)
                    csv = message["df"].to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download Data as CSV",
                        data=csv,
                        file_name="query_results.csv",
                        mime="text/csv",
                        key=f"dl_{message.get('id', '')}"
                    )

            # Execution stats
            if message.get("duration") is not None:
                st.caption(f"⚡ Executed in {message['duration']}s | {len(message['df']) if message.get('df') is not None else 0} rows")

# Handle User Input
user_input = st.chat_input("Ask a question about your data (e.g. 'Show total revenue by category')...")

# Check if user clicked a sample query button
if st.session_state.active_prompt:
    user_input = st.session_state.active_prompt
    st.session_state.active_prompt = None

if user_input:
    # 1. Append User Message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # 2. Assistant Processing
    with st.chat_message("assistant"):
        # Validate Prerequisites
        if not st.session_state.sarvam_api_key:
            st.error("⚠️ Please provide your Sarvam AI API Key in the left sidebar to continue.")
            st.stop()

        if not db_ok:
            st.error("⚠️ Cannot connect to MySQL database. Please verify your connection credentials in the sidebar.")
            st.stop()

        generator = SarvamSQLGenerator(
            api_key=st.session_state.sarvam_api_key,
            model_name=st.session_state.selected_model
        )

        with st.spinner("🤖 Translating question to SQL via Sarvam AI..."):
            try:
                schema_prompt = connector.get_schema_prompt_text()
                result_payload = generator.generate(user_input, schema_prompt)
                generated_sql = result_payload.get("sql_query", "")
                explanation = result_payload.get("explanation", "")
                viz_spec = result_payload.get("visualization", {})
                reasoning = result_payload.get("reasoning", "")
            except Exception as e:
                st.error(f"Error during SQL generation: {str(e)}")
                st.stop()

        if reasoning:
            with st.expander("🧠 Model Reasoning", expanded=False):
                st.markdown(reasoning)

        st.markdown(f"**Insight:** {explanation}")

        # Show SQL Expandable
        with st.expander("🛠️ View Generated MySQL Query", expanded=False):
            st.code(generated_sql, language="sql")

        with st.spinner("⚡ Executing query on MySQL..."):
            success, df_or_err, duration = connector.execute_query(generated_sql)

        if not success:
            st.error(f"SQL Execution Failed: {df_or_err}")
            st.session_state.messages.append({
                "role": "assistant",
                "explanation": explanation,
                "reasoning": reasoning,
                "sql": generated_sql,
                "df": None,
                "figure": None,
                "error": str(df_or_err)
            })
        else:
            df = df_or_err
            fig = None
            if not df.empty:
                # Build Visualization
                has_chart, fig, viz_desc = create_visualization(df, viz_spec)
                if has_chart and fig:
                    st.plotly_chart(fig, use_container_width=True)

                with st.expander("📋 View Data Table", expanded=not fig):
                    st.dataframe(df, use_container_width=True)
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download Data as CSV",
                        data=csv,
                        file_name="query_results.csv",
                        mime="text/csv",
                        key=f"dl_now_{len(st.session_state.messages)}"
                    )
            else:
                st.info("The query executed successfully but returned 0 rows.")

            st.caption(f"⚡ Executed in {duration}s | {len(df)} rows")

            # Save to conversation history
            import uuid
            st.session_state.messages.append({
                "id": str(uuid.uuid4())[:8],
                "role": "assistant",
                "explanation": explanation,
                "reasoning": reasoning,
                "sql": generated_sql,
                "df": df,
                "figure": fig,
                "duration": duration
            })
