

import pandas as pd
from pathlib import Path
from typing import Optional
import yaml

from src.utils.logger import get_logger


class DataLoader:
    """Handles loading and validation of Facebook Ads data"""
    
    def __init__(self, data_path: str, config_path: str = "config/config.yaml"):
        self.data_path = Path(data_path)
        self.logger = get_logger(__name__)
        
        # Load config
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.required_columns = self.config['data']['required_columns']
    
    def load(self) -> pd.DataFrame:
        """
        Load and validate Facebook Ads CSV data
        
        Returns:
            Validated DataFrame
        """
        self.logger.info(f"Loading data from {self.data_path}")
        
        if not self.data_path.exists():
            raise FileNotFoundError(f"Data file not found: {self.data_path}")
        
        # Load CSV
        try:
            df = pd.read_csv(self.data_path)
            self.logger.info(f"Loaded {len(df)} rows, {len(df.columns)} columns")
        except Exception as e:
            self.logger.error(f"Error loading CSV: {str(e)}")
            raise
        
        # Validate
        df = self._validate(df)
        df = self._clean(df)
        
        self.logger.info("Data loaded and validated successfully")
        return df
    
    def _validate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate required columns exist"""
        
        missing_cols = set(self.required_columns) - set(df.columns)
        
        if missing_cols:
            self.logger.warning(f"Missing columns: {missing_cols}")
            # For flexibility, don't fail - just warn
        
        # Check for critical columns
        critical = ['spend', 'revenue', 'roas', 'ctr']
        missing_critical = set(critical) - set(df.columns)
        
        if missing_critical:
            raise ValueError(f"Critical columns missing: {missing_critical}")
        
        self.logger.info("✓ Data validation passed")
        return df
    
    def _clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and prepare data"""
        
        # Convert date column
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
        
        # Handle missing values
        numeric_cols = ['spend', 'impressions', 'clicks', 'purchases', 'revenue']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Calculate derived metrics if missing
        if 'ctr' not in df.columns and 'clicks' in df.columns and 'impressions' in df.columns:
            df['ctr'] = df['clicks'] / df['impressions'].replace(0, 1)
        
        if 'roas' not in df.columns and 'revenue' in df.columns and 'spend' in df.columns:
            df['roas'] = df['revenue'] / df['spend'].replace(0, 1)
        
        # Remove rows with zero spend
        if 'spend' in df.columns:
            original_len = len(df)
            df = df[df['spend'] > 0]
            removed = original_len - len(df)
            if removed > 0:
                self.logger.info(f"Removed {removed} rows with zero spend")
        
        self.logger.info("✓ Data cleaning complete")
        return df
    
    def create_sample(self, df: pd.DataFrame, n: int = 100) -> pd.DataFrame:
        """Create a sample dataset for testing"""
        if len(df) <= n:
            return df
        return df.sample(n=n, random_state=self.config.get('random_seed', 42))