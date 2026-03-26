import streamlit as st
import pandas as pd
import json
import yaml
import os
from pathlib import Path
from datetime import datetime
import io

# Set page config
st.set_page_config(page_title="KAIB2026 Data Manager", layout="wide")

def get_config():
    config_path = Path(__file__).parent.parent.parent / 'config' / 'config.yaml'
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    return {}

def flatten_json(data):
    """Flatten nested JSON for projects."""
    flat_list = []
    for p in data:
        row = {
            'id': p.get('id'),
            'project_name': p.get('project_name'),
            'code': p.get('code'),
            'department': p.get('department'),
            'division': p.get('division'),
            'implementing_agency': p.get('implementing_agency'),
            'account_type': p.get('account_type'),
            'field': p.get('field'),
            'sector': p.get('sector'),
            'program_code': p.get('program', {}).get('code'),
            'program_name': p.get('program', {}).get('name'),
            'status': p.get('status'),
            'support_type': p.get('support_type'),
            'is_rnd': p.get('is_rnd'),
            'is_informatization': p.get('is_informatization'),
            'start_year': p.get('project_period', {}).get('start'),
            'end_year': p.get('project_period', {}).get('end'),
            'budget_2026': p.get('budget', {}).get('2026_budget'),
            'ai_domains': ', '.join(p.get('ai_classification', {}).get('ai_domains', [])),
            'ai_tech_types': ', '.join(p.get('ai_classification', {}).get('ai_tech_types', [])),
            'rnd_stage': p.get('ai_classification', {}).get('rnd_stage', '')
        }
        flat_list.append(row)
    return pd.DataFrame(flat_list)

def compare_structures(df1, df2, label1="File 1", label2="File 2"):
    """Compare columns between two DataFrames."""
    cols1 = list(df1.columns)
    cols2 = list(df2.columns)
    
    only1 = [c for c in cols1 if c not in cols2]
    only2 = [c for c in cols2 if c not in cols1]
    both = [c for c in cols1 if c in cols2]
    
    order_diff = []
    for i, c in enumerate(both):
        if i < len(cols2) and cols2[i] != c:
            order_diff.append({"Column": c, f"{label1} Pos": i, f"{label2} Pos": cols2.index(c)})

    return only1, only2, order_diff

def main():
    st.title("📊 KAIB2026 Data Management Dashboard")
    st.markdown("Bidirectional conversion, column mapping, and field comparison tool.")

    config = get_config()
    tab_conv, tab_comp, tab_settings = st.tabs(["🔄 Conversion & Mapping", "⚖️ Field Comparison", "⚙️ Settings"])

    with tab_conv:
        st.header("Bidirectional Data Conversion")
        col1, col2 = st.columns([1, 1])
        
        with col1:
            uploaded_file = st.file_uploader("Upload File (JSON, CSV, XLSX)", type=["json", "csv", "xlsx"])
        
        if uploaded_file is not None:
            # Load data
            if uploaded_file.name.endswith('.json'):
                raw_data = json.load(uploaded_file)
                # Check if it's budget_db or raw list
                projects = raw_data.get('projects', raw_data) if isinstance(raw_data, dict) else raw_data
                df = flatten_json(projects)
            elif uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            st.success(f"Successfully loaded {len(df)} records.")
            
            st.subheader("Edit/Manage Columns")
            st.info("You can rename cells, reorder columns by dragging, or delete rows.")
            
            # Interactive data editor
            edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)
            
            # Reorder columns
            all_cols = list(edited_df.columns)
            target_cols = st.multiselect("Select and Reorder Columns for Export", all_cols, default=all_cols)
            final_df = edited_df[target_cols]
            
            st.subheader("Dry-run Preview")
            st.write(final_df.head())
            
            # Download options
            st.subheader("Download Transformed Data")
            d_col1, d_col2, d_col3 = st.columns(3)
            
            # CSV Download
            csv_buffer = io.StringIO()
            final_df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
            d_col1.download_button("Download CSV", data=csv_buffer.getvalue(), file_name="transformed_data.csv", mime="text/csv")
            
            # Excel Download
            xlsx_buffer = io.BytesIO()
            with pd.ExcelWriter(xlsx_buffer, engine='openpyxl') as writer:
                final_df.to_excel(writer, index=False, sheet_name='Data')
            d_col2.download_button("Download Excel", data=xlsx_buffer.getvalue(), file_name="transformed_data.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            
            # JSON Download (Simplified)
            json_str = final_df.to_json(orient='records', force_ascii=False, indent=2)
            d_col3.download_button("Download JSON", data=json_str, file_name="transformed_data.json", mime="application/json")

    with tab_comp:
        st.header("Cross-Format Field Comparison")
        c_col1, c_col2 = st.columns(2)
        
        with c_col1:
            f1 = st.file_uploader("Base File (e.g. Current DB)", type=["json", "csv", "xlsx"], key="f1")
        with c_col2:
            f2 = st.file_uploader("Comparison File (e.g. New Template)", type=["json", "csv", "xlsx"], key="f2")
            
        if f1 and f2:
            def load_df(f):
                if f.name.endswith('.json'):
                    d = json.load(f)
                    p = d.get('projects', d) if isinstance(d, dict) else d
                    return flatten_json(p)
                elif f.name.endswith('.csv'): return pd.read_csv(f)
                else: return pd.read_excel(f)
            
            df1 = load_df(f1)
            df2 = load_df(f2)
            
            o1, o2, od = compare_structures(df1, df2, f1.name, f2.name)
            
            res_col1, res_col2 = st.columns(2)
            with res_col1:
                st.write(f"**Missing in {f2.name}**")
                if o1: st.error(", ".join(o1))
                else: st.success("None")
                
                st.write(f"**Unique to {f2.name}**")
                if o2: st.warning(", ".join(o2))
                else: st.info("None")
                
            with res_col2:
                st.write("**Order Differences**")
                if od: st.table(pd.DataFrame(od))
                else: st.success("Order matches exactly.")

    with tab_settings:
        st.header("Project Configuration")
        if config:
            st.json(config)
        else:
            st.warning("config.yaml not found.")
        
        st.subheader("System Information")
        st.text(f"Root: {Path(__file__).parent.parent.absolute()}")
        st.text(f"Last Modified: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
