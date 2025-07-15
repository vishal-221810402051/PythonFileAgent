import streamlit as st
import json
import pandas as pd
import collections
import matplotlib.pyplot as plt


st.set_page_config(page_title="Python File Evaluation Dashboard", layout="wide")
st.title("🚀 Python File Evaluation Dashboard")

uploaded_file = st.file_uploader("Upload JSON report", type="json")

if uploaded_file:
    data = json.load(uploaded_file)
    st.subheader(f"📄 Analysis of: `{data['file']}`")
    
    # Determine colors for maintainability index
    mi_value = data['maintainability']
    if mi_value >= 80:
        mi_color = "🟢"
    elif mi_value >= 50:
        mi_color = "🟡"
    else:
        mi_color = "🔴"
    
    # KPI style cards
    col1, col2, col3 = st.columns(3)
    col1.metric("Classes", len(data["classes"]))
    col2.metric("Functions", len(data["functions"]))
    col3.metric("Maintainability Index", f"{mi_value:.2f}", help="Green >80, Yellow 50-80, Red <50")
    col3.write(mi_color)
    
    st.markdown("---")

    # Top 3 most complex functions
    if data["complexity"]:
        sorted_complex = sorted(data["complexity"], key=lambda x: x["complexity"], reverse=True)
        top3 = sorted_complex[:3]
        st.subheader("🏆 Top 3 Most Complex Functions")
        for item in top3:
            st.write(f"- `{item['name']}` at line {item['lineno']} with complexity **{item['complexity']}**")
    else:
        st.info("No functions found to rank.")
    
    st.markdown("---")
    
    # Expanders
    with st.expander("📊 Show Function Complexity Details"):
        df_complexity = pd.DataFrame(data["complexity"])
        if not df_complexity.empty:
            st.bar_chart(df_complexity.set_index("name")["complexity"])
        else:
            st.info("No functions to show complexity.")

    with st.expander("🚨 Show Style & Linting Issues"):
        if data["lint"]:
            for issue in data["lint"]:
                st.write(f"- {issue}")
        else:
            st.success("No style issues found!")

    with st.expander("🔥 Show Anomalies Detected"):
        if data["anomalies"]:
            for anomaly in data["anomalies"]:
                st.warning(f"{anomaly['name']} at line {anomaly['lineno']}: {anomaly['reason']}")
        else:
            st.success("No anomalies detected.")
    with st.expander("🚨 Show Style & Linting Issues"):
        if data["lint"]:
            lint_data = pd.DataFrame([issue.split(":") for issue in data["lint"]], columns=["file", "line", "col", "desc"])
            lint_data["code"] = lint_data["desc"].str.extract(r"([EW]\d{3})")

            st.subheader("Lint Issues Table")
            st.dataframe(lint_data[["file", "line", "code", "desc"]])

            # Build bar chart for lint codes
            code_counts = collections.Counter(lint_data["code"].dropna())
            codes = list(code_counts.keys())
            counts = list(code_counts.values())

            fig, ax = plt.subplots(figsize=(8, 5))
            ax.bar(codes, counts, color='steelblue')
            ax.set_ylabel("Count")
            ax.set_xlabel("Lint Code")
            ax.set_title("Lint Issue Frequency by Type")
            ax.grid(axis='y', linestyle='--', alpha=0.7)

            # Annotate bars
            for i, v in enumerate(counts):
                ax.text(i, v + 0.5, str(v), ha='center', fontweight='bold')

            st.pyplot(fig)
        else:
            st.success("No style issues found!")        
