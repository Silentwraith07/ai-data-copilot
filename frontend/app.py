# Streamlit frontend for AI Data Copilot
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional, Dict, Any
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import tempfile

# Configuration
API_URL = "http://backend:8000"  # Docker service name
API_KEY = "demo-api-key-change-in-production"  # Should match backend

# Page configuration
st.set_page_config(
    page_title="AI Data Copilot",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #666;
        text-align: center;
        margin-bottom: 3rem;
    }
    .stButton>button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# Session state initialization
if 'file_id' not in st.session_state:
    st.session_state.file_id = None
if 'metadata' not in st.session_state:
    st.session_state.metadata = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

def upload_file(file) -> Optional[Dict[str, Any]]:
    """Upload file to backend API"""
    files = {"file": (file.name, file, file.type)}
    headers = {"X-API-Key": API_KEY}
    
    try:
        response = requests.post(
            f"{API_URL}/upload",
            files=files,
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Upload failed: {str(e)}")
        return None

def query_data(file_id: str, question: str) -> Optional[Dict[str, Any]]:
    """Send natural language query to backend"""
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "file_id": file_id,
        "question": question
    }
    
    try:
        response = requests.post(
            f"{API_URL}/query",
            json=payload,  # Use json= not data=
            headers=headers,
            timeout=60  # Increase timeout
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        st.error(f"HTTP Error: {e.response.status_code} - {e.response.text}")
        return None
    except Exception as e:
        st.error(f"Query failed: {str(e)}")
        return None


def render_chart(chart_type: str, chart_data: Dict[str, Any]):
    """Render chart using Plotly"""
    if not chart_data or chart_type == "none":
        return None
    
    try:
        labels = chart_data.get("labels", [])
        datasets = chart_data.get("datasets", [])
        
        if not datasets:
            return None
        
        if chart_type == "bar":
            fig = go.Figure(data=[
                go.Bar(name=ds.get("label", "Data"), x=labels, y=ds.get("data", []))
                for ds in datasets
            ])
            fig.update_layout(title="Bar Chart", xaxis_title="Categories", yaxis_title="Values")
            
        elif chart_type == "line":
            fig = go.Figure(data=[
                go.Scatter(name=ds.get("label", "Data"), x=labels, y=ds.get("data", []), mode='lines+markers')
                for ds in datasets
            ])
            fig.update_layout(title="Line Chart", xaxis_title="X-Axis", yaxis_title="Y-Axis")
            
        elif chart_type == "pie":
            fig = go.Figure(data=[
                go.Pie(labels=labels, values=datasets[0].get("data", []))
            ])
            fig.update_layout(title="Pie Chart")
            
        elif chart_type == "scatter":
            data_points = datasets[0].get("data", [])
            x_vals = [point["x"] for point in data_points]
            y_vals = [point["y"] for point in data_points]
            fig = go.Figure(data=[
                go.Scatter(x=x_vals, y=y_vals, mode='markers')
            ])
            fig.update_layout(
                title="Scatter Plot",
                xaxis_title=chart_data.get("x_column", "X"),
                yaxis_title=chart_data.get("y_column", "Y")
            )
        else:
            return None
        
        st.plotly_chart(fig, use_container_width=True)
        return fig
        
    except Exception as e:
        st.error(f"Error rendering chart: {str(e)}")
        return None

def export_to_csv(chat_history):
    """Export chat history to CSV"""
    data = []
    for item in chat_history:
        data.append({
            "Question": item["question"],
            "Answer": item["answer"],
            "Chart Type": item.get("chart_type", "none")
        })
    df = pd.DataFrame(data)
    return df.to_csv(index=False).encode('utf-8')

def export_to_pdf(chat_history):
    """Export chat history to PDF"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title = Paragraph("AI Data Copilot - Analysis Report", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 12))
    
    # Chat history
    for i, item in enumerate(chat_history, 1):
        question = Paragraph(f"<b>Q{i}:</b> {item['question']}", styles['Normal'])
        answer = Paragraph(f"<b>A{i}:</b> {item['answer']}", styles['Normal'])
        elements.append(question)
        elements.append(Spacer(1, 6))
        elements.append(answer)
        elements.append(Spacer(1, 12))
        
        # Add recommendations if available
        if item.get('recommendations'):
            rec_text = "<b>Recommendations:</b><br/>" + "<br/>".join([f"• {r}" for r in item['recommendations']])
            recommendations = Paragraph(rec_text, styles['Normal'])
            elements.append(recommendations)
            elements.append(Spacer(1, 12))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer

# Main UI
st.markdown('<div class="main-header">📊 AI Data Copilot</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Upload your data, ask questions, and get AI-powered insights</div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("📁 File Upload")
    uploaded_file = st.file_uploader(
        "Choose a CSV or Excel file",
        type=['csv', 'xlsx', 'xls'],
        help="Upload your data file to get started"
    )
    
    if uploaded_file and st.button("Process File"):
        with st.spinner("Processing file..."):
            metadata = upload_file(uploaded_file)
            if metadata:
                st.session_state.file_id = metadata["file_id"]
                st.session_state.metadata = metadata
                st.session_state.chat_history = []
                st.success("✅ File processed successfully!")
    
    if st.session_state.metadata:
        st.divider()
        st.subheader("📋 File Summary")
        st.metric("Rows", st.session_state.metadata["row_count"])
        st.metric("Columns", st.session_state.metadata["column_count"])
        
        with st.expander("View Schema"):
            schema_df = pd.DataFrame(
                list(st.session_state.metadata["schema"].items()),
                columns=["Column", "Type"]
            )
            st.dataframe(schema_df, use_container_width=True)
        
        st.divider()
        st.subheader("📥 Export")
        
        if st.session_state.chat_history:
            csv_data = export_to_csv(st.session_state.chat_history)
            st.download_button(
                label="Download as CSV",
                data=csv_data,
                file_name="analysis_report.csv",
                mime="text/csv"
            )
            
            pdf_data = export_to_pdf(st.session_state.chat_history)
            st.download_button(
                label="Download as PDF",
                data=pdf_data,
                file_name="analysis_report.pdf",
                mime="application/pdf"
            )

# Main content area
if st.session_state.metadata:
    # Display sample data
    with st.expander("🔍 Preview Sample Data", expanded=True):
        sample_df = pd.DataFrame(st.session_state.metadata["sample_rows"])
        st.dataframe(sample_df, use_container_width=True)
    
    st.divider()
    
    # Chat interface
    st.subheader("💬 Ask Questions About Your Data")
    
    # Display chat history
    for item in st.session_state.chat_history:
        with st.chat_message("user"):
            st.write(item["question"])
        
        with st.chat_message("assistant"):
            st.write(item["answer"])
            
            if item.get("chart_type") and item["chart_type"] != "none":
                render_chart(item["chart_type"], item.get("chart_data"))
            
            if item.get("recommendations"):
                st.info("**Recommendations:**\n" + "\n".join([f"• {r}" for r in item["recommendations"]]))
    
    # Chat input
    user_question = st.chat_input("Ask a question about your data...")
    
    if user_question:
        # Add user message
        with st.chat_message("user"):
            st.write(user_question)
        
        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Analyzing..."):
                response = query_data(st.session_state.file_id, user_question)
                
                if response:
                    st.write(response["answer_text"])
                    
                    # Render chart if available
                    if response.get("chart_type") and response["chart_type"] != "none":
                        render_chart(response["chart_type"], response.get("chart_data"))
                    
                    # Show recommendations
                    if response.get("recommendations"):
                        st.info("**Recommendations:**\n" + "\n".join([f"• {r}" for r in response["recommendations"]]))
                    
                    # Add to chat history
                    st.session_state.chat_history.append({
                        "question": user_question,
                        "answer": response["answer_text"],
                        "chart_type": response.get("chart_type"),
                        "chart_data": response.get("chart_data"),
                        "recommendations": response.get("recommendations")
                    })
                    
                    st.rerun()
else:
    # Welcome screen
    st.info("👈 Please upload a CSV or Excel file to get started")
    
    st.subheader("✨ Features")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 📤 Upload Data")
        st.write("Support for CSV and Excel files")
    
    with col2:
        st.markdown("### 🤖 Ask Questions")
        st.write("Natural language queries powered by AI")
    
    with col3:
        st.markdown("### 📊 Visualize")
        st.write("Automatic chart generation and insights")
