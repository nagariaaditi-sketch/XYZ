import streamlit as st
import pandas as pd
import io
import os
from datetime import datetime

def inject_theme_and_styles(theme="dark"):
    """Reads styles.css and injects it with the correct theme class applied to stApp."""
    css_file = "styles.css"
    if os.path.exists(css_file):
        with open(css_file, "r") as f:
            css_content = f.read()
        
        # Inject the CSS content
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
    
    # Inject active theme wrapper class into session state or layout
    theme_class = "theme-dark" if theme == "dark" else "theme-light"
    
    # Inject variables onto body/root level
    st.markdown(f"""
        <script>
            var body = window.parent.document.querySelector(".stApp");
            if (body) {{
                body.className = body.className.replace(/\\btheme-\\w+\\b/g, "");
                body.classList.add("{theme_class}");
            }}
        </script>
    """, unsafe_allow_html=True)
    
    # CSS overrides for streamlit default widgets to align with the active theme
    if theme == "dark":
        st.markdown("""
            <style>
            /* Dark mode theme overrides */
            div[data-testid="stSidebar"] {
                background-color: #0b0f19 !important;
                border-right: 1px solid #1e293b;
            }
            .stTabs [data-baseweb="tab-list"] {
                background-color: #131a30;
                border-radius: 8px;
                padding: 4px;
                border-bottom: none;
            }
            .stTabs [data-baseweb="tab"] {
                color: #94a3b8;
                border-radius: 6px;
                padding: 8px 16px;
            }
            .stTabs [aria-selected="true"] {
                background-color: #1e293b;
                color: #d4af37 !important;
                font-weight: 600;
            }
            </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <style>
            /* Light mode theme overrides */
            div[data-testid="stSidebar"] {
                background-color: #ffffff !important;
                border-right: 1px solid #e2e8f0;
            }
            .stTabs [data-baseweb="tab-list"] {
                background-color: #f1f5f9;
                border-radius: 8px;
                padding: 4px;
                border-bottom: none;
            }
            .stTabs [data-baseweb="tab"] {
                color: #64748b;
                border-radius: 6px;
                padding: 8px 16px;
            }
            .stTabs [aria-selected="true"] {
                background-color: #ffffff;
                color: #1d4ed8 !important;
                font-weight: 600;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            </style>
        """, unsafe_allow_html=True)


def render_kpi_card(label, value, change_val=None, is_positive=True, prefix="", suffix="", tooltip=""):
    """
    Renders an HTML metrics card matching the active theme.
    Can display positive or negative deltas.
    """
    change_html = ""
    if change_val is not None:
        sign = "+" if is_positive else ""
        class_name = "positive" if is_positive else "negative"
        arrow = "▲" if is_positive else "▼"
        change_html = f"""
        <div class="metric-change {class_name}">
            <span>{arrow} {sign}{change_val}</span>
        </div>
        """
        
    tooltip_html = f'title="{tooltip}"' if tooltip else ""
    
    card_html = f"""
    <div class="metric-card" {tooltip_html}>
        <div class="metric-label">{label}</div>
        <div class="metric-value">{prefix}{value}{suffix}</div>
        {change_html}
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)


def export_to_excel(df, sheet_name="IPO Analytics"):
    """
    Creates a styled Excel spreadsheet buffer from a DataFrame.
    Includes custom header row styles and adjusted column widths.
    """
    output = io.BytesIO()
    
    # Pre-process datetime columns to strings for compatibility
    df_export = df.copy()
    for col in df_export.select_dtypes(include=['datetime', 'datetimetz']).columns:
        df_export[col] = df_export[col].dt.strftime('%Y-%m-%d')
        
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_export.to_excel(writer, index=False, sheet_name=sheet_name)
        
        # Access worksheets to adjust styles
        workbook = writer.book
        worksheet = writer.sheets[sheet_name]
        
        # Header formatting
        for col_num in range(1, len(df_export.columns) + 1):
            cell = worksheet.cell(row=1, column=col_num)
            cell.font = cell.font.copy(bold=True, color="FFFFFF")
            cell.fill = cell.fill.copy(fill_type="solid", start_color="1B365D", end_color="1B365D")
            
        # Adjust column widths dynamically
        for col in worksheet.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = col[0].column_letter
            worksheet.column_dimensions[col_letter].width = max(max_len + 3, 12)
            
    return output.getvalue()


def generate_html_report(ipo_name, analysis, score, recommendation):
    """
    Generates a beautiful print-ready HTML research report.
    Users can open this page in browser and print to PDF.
    """
    rec_class = "buy" if recommendation == "BUY" else ("neutral" if recommendation == "NEUTRAL" else "avoid")
    
    report_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>IPO Research Report - {ipo_name}</title>
        <style>
            body {{
                font-family: 'Segoe UI', Arial, sans-serif;
                color: #1a202c;
                margin: 0;
                padding: 40px;
                line-height: 1.6;
            }}
            .report-header {{
                border-bottom: 2px solid #2b6cb0;
                padding-bottom: 20px;
                margin-bottom: 30px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            .report-title {{
                margin: 0;
                color: #2b6cb0;
                font-size: 28px;
                font-weight: 700;
            }}
            .date {{
                color: #718096;
                font-size: 14px;
            }}
            .score-container {{
                display: flex;
                margin-bottom: 30px;
                gap: 20px;
            }}
            .score-box {{
                background-color: #f7fafc;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 20px;
                text-align: center;
                flex: 1;
            }}
            .score-val {{
                font-size: 36px;
                font-weight: 800;
                color: #2b6cb0;
                margin-bottom: 5px;
            }}
            .rec-badge {{
                display: inline-block;
                padding: 10px 20px;
                border-radius: 30px;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 1px;
                font-size: 18px;
            }}
            .rec-badge.buy {{
                background-color: #c6f6d5;
                color: #22543d;
                border: 2px solid #38a169;
            }}
            .rec-badge.neutral {{
                background-color: #ebf8ff;
                color: #2b6cb0;
                border: 2px solid #4299e1;
            }}
            .rec-badge.avoid {{
                background-color: #fed7d7;
                color: #742a2a;
                border: 2px solid #e53e3e;
            }}
            h2 {{
                color: #2d3748;
                font-size: 20px;
                border-bottom: 1px solid #e2e8f0;
                padding-bottom: 8px;
                margin-top: 30px;
            }}
            .section {{
                margin-bottom: 25px;
            }}
            .grid {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
            }}
            .card {{
                background-color: #f8fafc;
                border-radius: 6px;
                padding: 15px;
                border-left: 4px solid #4299e1;
            }}
            .footer {{
                margin-top: 50px;
                border-top: 1px solid #e2e8f0;
                padding-top: 15px;
                text-align: center;
                font-size: 12px;
                color: #a0aec0;
            }}
        </style>
    </head>
    <body>
        <div class="report-header">
            <div>
                <h1 class="report-title">IPO INTELLIGENCE REPORT</h1>
                <div style="font-weight: 600; font-size: 18px; color: #4a5568;">{ipo_name}</div>
            </div>
            <div class="date">
                Generated: {datetime.now().strftime('%d %B %Y')}<br>
                IPO Tracker India
            </div>
        </div>
        
        <div class="score-container">
            <div class="score-box">
                <div style="font-size: 12px; text-transform: uppercase; color: #718096; font-weight: 600;">Investment Score</div>
                <div class="score-val">{score} <span style="font-size: 18px; color: #a0aec0;">/ 100</span></div>
            </div>
            <div class="score-box" style="display: flex; flex-direction: column; justify-content: center; align-items: center;">
                <div style="font-size: 12px; text-transform: uppercase; color: #718096; font-weight: 600; margin-bottom: 8px;">Action Recommendation</div>
                <div class="rec-badge {rec_class}">{recommendation}</div>
            </div>
        </div>

        <div class="section">
            <h2>1. Company Profile & Valuation</h2>
            <div class="grid">
                <div class="card">
                    <strong>Revenue Growth:</strong> {analysis.get('revenue_growth', 'N/A')}<br>
                    <strong>Profit Growth:</strong> {analysis.get('profit_growth', 'N/A')}<br>
                    <strong>ROE:</strong> {analysis.get('roe', 'N/A')}<br>
                </div>
                <div class="card" style="border-left-color: #ecc94b;">
                    <strong>Valuation PE Ratio:</strong> {analysis.get('pe_ratio', 'N/A')}<br>
                    <strong>Debt to Equity:</strong> {analysis.get('debt_equity', 'N/A')}<br>
                    <strong>Sector Outlook:</strong> {analysis.get('sector_outlook', 'N/A')}<br>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>2. Key Strengths</h2>
            <ul>
                { "".join(f"<li>{item}</li>" for item in analysis.get('strengths', ['No strength points listed'])) }
            </ul>
        </div>

        <div class="section">
            <h2>3. Risks & Red Flags</h2>
            <ul>
                { "".join(f"<li>{item}</li>" for item in analysis.get('risks', ['No risk points listed'])) }
            </ul>
        </div>
        
        <div class="section">
            <h2>4. Peer Comparison</h2>
            <p>{analysis.get('peer_comparison', 'No peer analysis available')}</p>
        </div>

        <div class="footer">
            Disclaimer: This report is generated algorithmically by the IPO Intelligence Dashboard using public details and historical valuation models. It does not constitute formal financial advice. Investors should perform their own due diligence.
        </div>
    </body>
    </html>
    """
    return report_html
