"""
visualizer.py
Analyzes query result DataFrames and builds interactive Plotly visualizations.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional, Dict, Any, Tuple

PLOTLY_TEMPLATE = "plotly_white"

def auto_detect_chart_type(df: pd.DataFrame) -> Tuple[str, Optional[str], Optional[str]]:
    """
    Intelligently determines the best chart type, x-axis, and y-axis based on DataFrame metadata.
    """
    if df.empty:
        return "none", None, None

    # Single scalar metric
    if df.shape == (1, 1):
        return "metric", None, df.columns[0]

    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    date_cols = df.select_dtypes(include=["datetime", "datetimetz"]).columns.tolist()
    
    # Check object columns that might look like dates
    for col in df.select_dtypes(include=["object"]).columns:
        sample_vals = df[col].dropna().astype(str).head(5)
        if any("-" in s or "/" in s for s in sample_vals):
            try:
                pd.to_datetime(sample_vals)
                date_cols.append(col)
            except Exception:
                pass

    categorical_cols = [c for c in df.columns if c not in numeric_cols and c not in date_cols]

    # Case 1: Date column + numeric column -> Line Chart
    if date_cols and numeric_cols:
        return "line", date_cols[0], numeric_cols[0]

    # Case 2: Categorical + numeric column
    if categorical_cols and numeric_cols:
        x_col = categorical_cols[0]
        y_col = numeric_cols[0]
        n_unique = df[x_col].nunique()

        # If 2 to 6 unique categories, Pie/Donut is great
        if 2 <= n_unique <= 6:
            return "donut", x_col, y_col
        # Otherwise Bar chart
        return "bar", x_col, y_col

    # Case 3: Two numeric columns without categories -> Scatter Plot
    if len(numeric_cols) >= 2 and not categorical_cols:
        return "scatter", numeric_cols[0], numeric_cols[1]

    # Case 4: Only 1 numeric column with 1 row -> Metric
    if len(df) == 1 and numeric_cols:
        return "metric", None, numeric_cols[0]

    # Case 5: Only categorical columns or multiple columns
    if len(categorical_cols) >= 1:
        return "bar", categorical_cols[0], None

    return "table", None, None

def create_visualization(df: pd.DataFrame, viz_spec: Optional[Dict[str, Any]] = None) -> Tuple[bool, Optional[go.Figure], str]:
    """
    Builds a Plotly figure from the DataFrame and visualization specification.
    Returns: (is_chart_created, figure_or_none, description_string)
    """
    if df is None or df.empty:
        return False, None, "The query returned an empty result set."

    # Normalize column names in df for easier matching
    cols = df.columns.tolist()
    
    # Determine chart parameters
    chart_type = None
    x_col = None
    y_col = None
    title = None
    color_col = None

    if viz_spec and isinstance(viz_spec, dict):
        chart_type = viz_spec.get("chart_type", "").lower()
        x_col = viz_spec.get("x_axis")
        y_col = viz_spec.get("y_axis")
        title = viz_spec.get("title")
        color_col = viz_spec.get("color")

    # Validate specified columns exist in dataframe
    if x_col and x_col not in cols:
        # Case insensitive match
        match = [c for c in cols if c.lower() == str(x_col).lower()]
        x_col = match[0] if match else None

    if y_col and y_col not in cols:
        match = [c for c in cols if c.lower() == str(y_col).lower()]
        y_col = match[0] if match else None

    if color_col and color_col not in cols:
        color_col = None

    # Fallback auto-detection if spec is incomplete
    auto_type, auto_x, auto_y = auto_detect_chart_type(df)
    if not chart_type or chart_type in ["none", "table"]:
        chart_type = auto_type
    if not x_col:
        x_col = auto_x
    if not y_col:
        y_col = auto_y

    if not title:
        if y_col and x_col:
            title = f"{y_col.replace('_', ' ').title()} by {x_col.replace('_', ' ').title()}"
        elif y_col:
            title = f"{y_col.replace('_', ' ').title()} Metric"
        else:
            title = "Query Visualization"

    try:
        # 1. Single Metric KPI Display
        if chart_type == "metric" or (len(df) == 1 and y_col and not x_col):
            val = df[y_col].iloc[0] if y_col in df.columns else df.iloc[0, 0]
            val_formatted = f"{val:,.2f}" if isinstance(val, (int, float)) else str(val)
            
            fig = go.Figure(go.Indicator(
                mode="number",
                value=float(val) if isinstance(val, (int, float)) else 0,
                number={"prefix": "₹" if "revenue" in str(y_col).lower() or "price" in str(y_col).lower() or "sales" in str(y_col).lower() else "", "valueformat": ",.2f"},
                title={"text": f"<span style='font-size:1.3em;color:#4B5563'>{title}</span>"},
            ))
            fig.update_layout(template=PLOTLY_TEMPLATE, height=280, margin=dict(l=20, r=20, t=50, b=20))
            return True, fig, f"Key Metric: {title}"

        # 2. Bar Chart
        elif chart_type in ["bar", "column"]:
            if not x_col or not y_col:
                return False, None, "Insufficient dimensions for a bar chart."
            
            # Sort for better presentation if <= 25 items
            plot_df = df.copy()
            if len(plot_df) <= 25 and pd.api.types.is_numeric_dtype(plot_df[y_col]):
                plot_df = plot_df.sort_values(by=y_col, ascending=False)

            is_horizontal = len(plot_df) > 12
            if is_horizontal:
                fig = px.bar(
                    plot_df,
                    y=x_col,
                    x=y_col,
                    orientation="h",
                    title=title,
                    color=color_col or y_col,
                    color_continuous_scale="Viridis",
                    template=PLOTLY_TEMPLATE
                )
            else:
                fig = px.bar(
                    plot_df,
                    x=x_col,
                    y=y_col,
                    title=title,
                    color=color_col or x_col,
                    template=PLOTLY_TEMPLATE
                )
            
            fig.update_layout(margin=dict(l=20, r=20, t=60, b=40), hovermode="x unified")
            return True, fig, f"Bar Chart: {title}"

        # 3. Line Chart
        elif chart_type in ["line", "area"]:
            if not x_col or not y_col:
                return False, None, "Insufficient dimensions for a line chart."
            plot_df = df.copy().sort_values(by=x_col)
            fig = px.line(
                plot_df,
                x=x_col,
                y=y_col,
                markers=True,
                title=title,
                color=color_col,
                template=PLOTLY_TEMPLATE
            )
            fig.update_layout(margin=dict(l=20, r=20, t=60, b=40), hovermode="x unified")
            return True, fig, f"Trend Line Chart: {title}"

        # 4. Pie / Donut Chart
        elif chart_type in ["pie", "donut"]:
            if not x_col or not y_col:
                return False, None, "Insufficient dimensions for a pie chart."
            hole_size = 0.45 if chart_type == "donut" else 0.0
            fig = px.pie(
                df,
                names=x_col,
                values=y_col,
                hole=hole_size,
                title=title,
                template=PLOTLY_TEMPLATE
            )
            fig.update_traces(textposition="inside", textinfo="percent+label")
            fig.update_layout(margin=dict(l=20, r=20, t=60, b=40))
            return True, fig, f"{'Donut' if hole_size > 0 else 'Pie'} Chart: {title}"

        # 5. Scatter Plot
        elif chart_type == "scatter":
            if not x_col or not y_col:
                return False, None, "Insufficient dimensions for a scatter plot."
            fig = px.scatter(
                df,
                x=x_col,
                y=y_col,
                color=color_col,
                title=title,
                template=PLOTLY_TEMPLATE,
                size_max=15
            )
            fig.update_layout(margin=dict(l=20, r=20, t=60, b=40))
            return True, fig, f"Scatter Plot: {title}"

        else:
            return False, None, "Data is best presented in tabular format."

    except Exception as e:
        return False, None, f"Failed to generate chart: {str(e)}"
