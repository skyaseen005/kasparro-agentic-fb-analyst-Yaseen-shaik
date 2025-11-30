"""
Data Agent - Loads and summarizes Facebook Ads dataset
"""

import pandas as pd
import numpy as np
from typing import Dict, Any
from datetime import datetime, timedelta

from src.utils.logger import get_logger


class DataAgent:
    """Analyzes and summarizes Facebook Ads data"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = get_logger(__name__)
    
    def analyze(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate comprehensive data summary
        
        Args:
            df: Facebook Ads DataFrame
            
        Returns:
            Dictionary with statistical summaries and insights
        """
        self.logger.info("Generating data summary...")
        
        # Ensure date column is datetime
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
        
        summary = {
            "overview": self._get_overview(df),
            "performance_metrics": self._get_performance_metrics(df),
            "time_analysis": self._get_time_analysis(df),
            "campaign_breakdown": self._get_campaign_breakdown(df),
            "creative_analysis": self._get_creative_analysis(df),
            "audience_analysis": self._get_audience_analysis(df),
            "platform_analysis": self._get_platform_analysis(df),
            "top_performers": self._get_top_performers(df),
            "underperformers": self._get_underperformers(df)
        }
        
        self.logger.info("Data summary complete")
        return summary
    
    def _get_overview(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Basic dataset overview"""
        return {
            "total_rows": len(df),
            "date_range": {
                "start": df['date'].min().strftime('%Y-%m-%d') if 'date' in df.columns else None,
                "end": df['date'].max().strftime('%Y-%m-%d') if 'date' in df.columns else None,
                "days": (df['date'].max() - df['date'].min()).days if 'date' in df.columns else None
            },
            "unique_campaigns": df['campaign_name'].nunique() if 'campaign_name' in df.columns else 0,
            "unique_adsets": df['adset_name'].nunique() if 'adset_name' in df.columns else 0
        }
    
    def _get_performance_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Overall performance metrics"""
        return {
            "total_spend": float(df['spend'].sum()) if 'spend' in df.columns else 0,
            "total_revenue": float(df['revenue'].sum()) if 'revenue' in df.columns else 0,
            "total_impressions": int(df['impressions'].sum()) if 'impressions' in df.columns else 0,
            "total_clicks": int(df['clicks'].sum()) if 'clicks' in df.columns else 0,
            "total_purchases": int(df['purchases'].sum()) if 'purchases' in df.columns else 0,
            "avg_roas": float(df['roas'].mean()) if 'roas' in df.columns else 0,
            "avg_ctr": float(df['ctr'].mean()) if 'ctr' in df.columns else 0,
            "median_roas": float(df['roas'].median()) if 'roas' in df.columns else 0,
            "median_ctr": float(df['ctr'].median()) if 'ctr' in df.columns else 0
        }
    
    def _get_time_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Time-based trend analysis"""
        if 'date' not in df.columns:
            return {}
        
        # Group by date
        daily = df.groupby('date').agg({
            'spend': 'sum',
            'revenue': 'sum',
            'roas': 'mean',
            'ctr': 'mean',
            'clicks': 'sum',
            'purchases': 'sum'
        }).reset_index()
        
        # Recent vs previous comparison
        max_date = df['date'].max()
        week_ago = max_date - timedelta(days=7)
        two_weeks_ago = max_date - timedelta(days=14)
        
        recent_week = df[df['date'] > week_ago]
        previous_week = df[(df['date'] > two_weeks_ago) & (df['date'] <= week_ago)]
        
        return {
            "recent_week": {
                "avg_roas": float(recent_week['roas'].mean()),
                "avg_ctr": float(recent_week['ctr'].mean()),
                "total_spend": float(recent_week['spend'].sum()),
                "total_revenue": float(recent_week['revenue'].sum())
            },
            "previous_week": {
                "avg_roas": float(previous_week['roas'].mean()) if len(previous_week) > 0 else 0,
                "avg_ctr": float(previous_week['ctr'].mean()) if len(previous_week) > 0 else 0,
                "total_spend": float(previous_week['spend'].sum()) if len(previous_week) > 0 else 0,
                "total_revenue": float(previous_week['revenue'].sum()) if len(previous_week) > 0 else 0
            },
            "changes": {
                "roas_change_pct": self._pct_change(
                    recent_week['roas'].mean(),
                    previous_week['roas'].mean() if len(previous_week) > 0 else 0
                ),
                "ctr_change_pct": self._pct_change(
                    recent_week['ctr'].mean(),
                    previous_week['ctr'].mean() if len(previous_week) > 0 else 0
                )
            }
        }
    
    def _get_campaign_breakdown(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Campaign-level analysis"""
        if 'campaign_name' not in df.columns:
            return {}
        
        campaign_stats = df.groupby('campaign_name').agg({
            'spend': 'sum',
            'revenue': 'sum',
            'roas': 'mean',
            'ctr': 'mean',
            'impressions': 'sum',
            'clicks': 'sum',
            'purchases': 'sum'
        }).reset_index()
        
        return {
            "total_campaigns": len(campaign_stats),
            "top_by_revenue": campaign_stats.nlargest(5, 'revenue')[
                ['campaign_name', 'revenue', 'roas']
            ].to_dict('records'),
            "top_by_roas": campaign_stats.nlargest(5, 'roas')[
                ['campaign_name', 'roas', 'spend']
            ].to_dict('records')
        }
    
    def _get_creative_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Creative performance breakdown"""
        if 'creative_type' not in df.columns:
            return {}
        
        creative_stats = df.groupby('creative_type').agg({
            'roas': 'mean',
            'ctr': 'mean',
            'spend': 'sum',
            'clicks': 'sum'
        }).reset_index()
        
        return {
            "by_type": creative_stats.to_dict('records'),
            "best_type_roas": creative_stats.nlargest(1, 'roas')['creative_type'].values[0],
            "best_type_ctr": creative_stats.nlargest(1, 'ctr')['creative_type'].values[0]
        }
    
    def _get_audience_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Audience performance breakdown"""
        if 'audience_type' not in df.columns:
            return {}
        
        audience_stats = df.groupby('audience_type').agg({
            'roas': 'mean',
            'ctr': 'mean',
            'spend': 'sum'
        }).reset_index()
        
        return {
            "by_audience": audience_stats.to_dict('records')
        }
    
    def _get_platform_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Platform performance breakdown"""
        if 'platform' not in df.columns:
            return {}
        
        platform_stats = df.groupby('platform').agg({
            'roas': 'mean',
            'ctr': 'mean',
            'spend': 'sum',
            'revenue': 'sum'
        }).reset_index()
        
        return {
            "by_platform": platform_stats.to_dict('records')
        }
    
    def _get_top_performers(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Identify top performing campaigns/ads"""
        low_ctr_threshold = self.config['thresholds']['low_ctr']
        
        # Filter campaigns with sufficient spend
        min_spend = self.config['thresholds']['min_spend']
        df_filtered = df[df['spend'] >= min_spend].copy()
        
        if len(df_filtered) == 0:
            return {"campaigns": [], "messages": []}
        
        # Top campaigns by ROAS
        top_campaigns = df_filtered.nlargest(10, 'roas')[
            ['campaign_name', 'roas', 'ctr', 'spend', 'creative_message']
        ].to_dict('records')
        
        # Top messages by CTR
        message_stats = df_filtered.groupby('creative_message').agg({
            'ctr': 'mean',
            'roas': 'mean',
            'clicks': 'sum'
        }).reset_index()
        
        top_messages = message_stats.nlargest(10, 'ctr').to_dict('records')
        
        return {
            "campaigns": top_campaigns,
            "messages": top_messages
        }
    
    def _get_underperformers(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Identify underperforming campaigns needing attention"""
        low_ctr_threshold = self.config['thresholds']['low_ctr']
        low_roas_threshold = self.config['thresholds']['low_roas']
        min_spend = self.config['thresholds']['min_spend']
        
        # Filter campaigns with sufficient spend
        df_filtered = df[df['spend'] >= min_spend].copy()
        
        if len(df_filtered) == 0:
            return {"low_ctr": [], "low_roas": []}
        
        # Low CTR campaigns
        low_ctr = df_filtered[df_filtered['ctr'] < low_ctr_threshold].nsmallest(10, 'ctr')[
            ['campaign_name', 'ctr', 'roas', 'spend', 'creative_message']
        ].to_dict('records')
        
        # Low ROAS campaigns
        low_roas = df_filtered[df_filtered['roas'] < low_roas_threshold].nsmallest(10, 'roas')[
            ['campaign_name', 'roas', 'ctr', 'spend', 'creative_message']
        ].to_dict('records')
        
        return {
            "low_ctr": low_ctr,
            "low_roas": low_roas,
            "count_low_ctr": len(df_filtered[df_filtered['ctr'] < low_ctr_threshold]),
            "count_low_roas": len(df_filtered[df_filtered['roas'] < low_roas_threshold])
        }
    
    def _pct_change(self, new_val: float, old_val: float) -> float:
        """Calculate percentage change"""
        if old_val == 0:
            return 0.0
        return float(((new_val - old_val) / old_val) * 100)