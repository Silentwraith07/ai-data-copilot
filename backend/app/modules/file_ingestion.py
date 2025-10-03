# Module for file upload, cleaning, schema extraction, and summary generation
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, Tuple
import uuid
import json

class FileIngestionModule:
    """
    Handles CSV/Excel file ingestion, data cleaning, schema extraction,
    and summary statistics generation.
    Designed to be extended to PySpark for larger files.
    """
    
    def __init__(self, upload_dir: str):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(exist_ok=True)
        self.data_cache: Dict[str, pd.DataFrame] = {}  # In-memory cache for MVP
    
    def ingest_file(self, file_path: str, original_filename: str) -> Tuple[str, Dict[str, Any]]:
        """
        Ingest and process uploaded file.
        Returns: (file_id, metadata_dict)
        """
        file_id = str(uuid.uuid4())
        
        # Read file based on extension
        if original_filename.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif original_filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file_path)
        else:
            raise ValueError(f"Unsupported file format: {original_filename}")
        
        # Clean data: handle missing values, strip whitespace
        df = self._clean_dataframe(df)
        
        # Cache dataframe for future queries
        self.data_cache[file_id] = df
        
        # Extract schema and summary
        schema = self._extract_schema(df)
        summary = self._generate_summary(df)
        sample_rows = self._get_sample_rows(df, n=5)
        
        # Save processed dataframe for persistence
        processed_path = self.upload_dir / f"{file_id}.parquet"
        df.to_parquet(processed_path, index=False)
        
        metadata = {
            "file_id": file_id,
            "filename": original_filename,
            "schema": schema,
            "summary": summary,
            "sample_rows": sample_rows,
            "row_count": len(df),
            "column_count": len(df.columns)
        }
        
        # Save metadata
        metadata_path = self.upload_dir / f"{file_id}_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
        
        return file_id, metadata
    
    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Basic data cleaning operations.
        Extensible for more sophisticated cleaning logic.
        """
        # Strip whitespace from column names
        df.columns = df.columns.str.strip()
        
        # Strip whitespace from string columns
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].str.strip() if df[col].dtype == 'object' else df[col]
        
        # Replace empty strings with NaN
        df.replace(r'^\s*$', np.nan, regex=True, inplace=True)
        
        return df
    
    def _extract_schema(self, df: pd.DataFrame) -> Dict[str, str]:
        """
        Extract column names and their data types.
        """
        schema = {}
        for col in df.columns:
            dtype = str(df[col].dtype)
            # Simplify dtype names
            if 'int' in dtype:
                schema[col] = 'integer'
            elif 'float' in dtype:
                schema[col] = 'float'
            elif 'datetime' in dtype:
                schema[col] = 'datetime'
            elif 'bool' in dtype:
                schema[col] = 'boolean'
            else:
                schema[col] = 'string'
        return schema
    
    def _generate_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate summary statistics for numeric and categorical columns.
        """
        summary = {
            "numeric_columns": {},
            "categorical_columns": {},
            "missing_values": {}
        }
        
        # Numeric summary
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            summary["numeric_columns"][col] = {
                "mean": float(df[col].mean()),
                "median": float(df[col].median()),
                "min": float(df[col].min()),
                "max": float(df[col].max()),
                "std": float(df[col].std())
            }
        
        # Categorical summary
        categorical_cols = df.select_dtypes(include=['object']).columns
        for col in categorical_cols:
            value_counts = df[col].value_counts().head(10).to_dict()
            summary["categorical_columns"][col] = {
                "unique_count": int(df[col].nunique()),
                "top_values": {str(k): int(v) for k, v in value_counts.items()}
            }
        
        # Missing values
        for col in df.columns:
            missing = int(df[col].isna().sum())
            if missing > 0:
                summary["missing_values"][col] = missing
        
        return summary
    
    def _get_sample_rows(self, df: pd.DataFrame, n: int = 5) -> list:
        """
        Get sample rows from the dataframe.
        """
        return df.head(n).to_dict(orient='records')
    
    def get_dataframe(self, file_id: str) -> pd.DataFrame:
        """
        Retrieve cached dataframe or load from disk.
        """
        if file_id in self.data_cache:
            return self.data_cache[file_id]
        
        # Load from disk
        parquet_path = self.upload_dir / f"{file_id}.parquet"
        if parquet_path.exists():
            df = pd.read_parquet(parquet_path)
            self.data_cache[file_id] = df
            return df
        
        raise ValueError(f"File ID {file_id} not found")
    
    def get_metadata(self, file_id: str) -> Dict[str, Any]:
        """
        Retrieve file metadata.
        """
        metadata_path = self.upload_dir / f"{file_id}_metadata.json"
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                return json.load(f)
        raise ValueError(f"Metadata for file ID {file_id} not found")
