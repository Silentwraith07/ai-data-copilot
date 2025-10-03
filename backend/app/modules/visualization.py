# Module for data visualization and chart generation
import pandas as pd
from typing import Dict, Any, Optional

class VisualizationModule:
    """
    Handles chart data preparation for different visualization types.
    Frontend will use this structured data to render charts.
    """
    
    @staticmethod
    def prepare_bar_chart(df: pd.DataFrame, x_col: str, y_col: str, limit: int = 10) -> Dict[str, Any]:
        """
        Prepare data for bar chart.
        """
        # Aggregate if necessary
        if df[y_col].dtype in ['int64', 'float64']:
            data = df.groupby(x_col)[y_col].sum().head(limit)
        else:
            data = df[x_col].value_counts().head(limit)
        
        return {
            "labels": data.index.tolist(),
            "datasets": [{
                "label": y_col,
                "data": data.values.tolist()
            }]
        }
    
    @staticmethod
    def prepare_line_chart(df: pd.DataFrame, x_col: str, y_col: str) -> Dict[str, Any]:
        """
        Prepare data for line chart (typically time series).
        """
        data = df[[x_col, y_col]].dropna().sort_values(x_col)
        
        return {
            "labels": data[x_col].astype(str).tolist(),
            "datasets": [{
                "label": y_col,
                "data": data[y_col].tolist()
            }]
        }
    
    @staticmethod
    def prepare_pie_chart(df: pd.DataFrame, column: str, limit: int = 8) -> Dict[str, Any]:
        """
        Prepare data for pie chart.
        """
        data = df[column].value_counts().head(limit)
        
        return {
            "labels": data.index.tolist(),
            "datasets": [{
                "label": column,
                "data": data.values.tolist()
            }]
        }
    
    @staticmethod
    def prepare_scatter_chart(df: pd.DataFrame, x_col: str, y_col: str, limit: int = 100) -> Dict[str, Any]:
        """
        Prepare data for scatter plot.
        """
        data = df[[x_col, y_col]].dropna().head(limit)
        
        return {
            "x_column": x_col,
            "y_column": y_col,
            "datasets": [{
                "label": f"{y_col} vs {x_col}",
                "data": [{"x": x, "y": y} for x, y in zip(data[x_col].tolist(), data[y_col].tolist())]
            }]
        }
