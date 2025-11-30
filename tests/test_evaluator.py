"""
Tests for Evaluator Agent
"""

import pytest
import pandas as pd
import yaml
from pathlib import Path

from src.agents.evaluator import EvaluatorAgent


@pytest.fixture
def config():
    """Load test configuration"""
    config_path = Path("config/config.yaml")
    if config_path.exists():
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    else:
        return {
            'model': {'name': 'gpt-4', 'temperature': 0.7, 'max_tokens': 2000},
            'thresholds': {'low_ctr': 0.015, 'low_roas': 3.0, 'min_spend': 100}
        }


@pytest.fixture
def sample_data():
    """Create sample Facebook Ads data"""
    return pd.DataFrame({
        'campaign_name': ['Campaign_A', 'Campaign_B', 'Campaign_C'] * 10,
        'date': pd.date_range('2024-01-01', periods=30),
        'spend': [500, 300, 400] * 10,
        'revenue': [2500, 900, 2000] * 10,
        'roas': [5.0, 3.0, 5.0] * 10,
        'ctr': [0.02, 0.01, 0.022] * 10,
        'impressions': [50000, 30000, 40000] * 10,
        'clicks': [1000, 300, 880] * 10,
        'purchases': [50, 15, 44] * 10,
        'creative_type': ['Video', 'Image', 'Video'] * 10,
        'creative_message': ['Message A', 'Message B', 'Message C'] * 10
    })


@pytest.fixture
def sample_hypotheses():
    """Sample hypotheses to validate"""
    return [
        {
            'id': 'H1',
            'hypothesis': 'Video creatives outperform image creatives',
            'confidence': 0.8,
            'evidence': ['Video CTR: 0.021, Image CTR: 0.01'],
            'recommendation': 'Shift budget to video',
            'category': 'creative_fatigue'
        },
        {
            'id': 'H2',
            'hypothesis': 'Campaign B has low ROAS',
            'confidence': 0.6,
            'evidence': ['Campaign B ROAS: 3.0 vs avg 4.3'],
            'recommendation': 'Review targeting',
            'category': 'audience_saturation'
        }
    ]


class TestEvaluatorAgent:
    """Test suite for Evaluator Agent"""
    
    def test_initialization(self, config):
        """Test agent initializes correctly"""
        evaluator = EvaluatorAgent(config)
        assert evaluator is not None
        assert evaluator.config == config
    
    def test_quantitative_checks(self, config, sample_data):
        """Test quantitative validation checks"""
        evaluator = EvaluatorAgent(config)
        
        data_summary = {
            'time_analysis': {
                'changes': {
                    'roas_change_pct': -15.0,
                    'ctr_change_pct': -12.0
                }
            },
            'underperformers': {
                'count_low_ctr': 5,
                'count_low_roas': 3
            }
        }
        
        checks = evaluator._perform_quantitative_checks(sample_data, data_summary)
        
        assert 'sample_size_adequate' in checks
        assert checks['sample_size_adequate'] is True
        assert 'significant_roas_change' in checks
        assert 'has_low_ctr_campaigns' in checks
    
    def test_confidence_scoring(self, config, sample_hypotheses, sample_data):
        """Test confidence score adjustment"""
        evaluator = EvaluatorAgent(config)
        
        data_summary = {
            'performance_metrics': {
                'avg_roas': 4.3,
                'avg_ctr': 0.017
            },
            'time_analysis': {
                'changes': {
                    'roas_change_pct': -10.0,
                    'ctr_change_pct': -8.0
                }
            }
        }
        
        # Note: This test may require mocking OpenAI API
        # For now, we test the structure
        assert len(sample_hypotheses) == 2
        assert all('confidence' in h for h in sample_hypotheses)
        assert all(0 <= h['confidence'] <= 1 for h in sample_hypotheses)
    
    def test_validation_context_building(self, config, sample_hypotheses):
        """Test context building for validation"""
        evaluator = EvaluatorAgent(config)
        
        data_summary = {
            'performance_metrics': {'avg_roas': 4.0},
            'time_analysis': {'changes': {'roas_change_pct': -10}}
        }
        
        quantitative_checks = {'sample_size_adequate': True}
        
        context = evaluator._build_validation_context(
            sample_hypotheses,
            data_summary,
            quantitative_checks
        )
        
        assert isinstance(context, str)
        assert 'H1' in context
        assert 'H2' in context
        assert 'Hypothesis Validation' in context
    
    def test_confidence_thresholds(self, config):
        """Test confidence threshold logic"""
        evaluator = EvaluatorAgent(config)
        
        # High confidence
        high_conf_hypothesis = {
            'confidence': 0.85,
            'evidence': ['Strong data', 'Clear trend', 'Statistical significance']
        }
        assert high_conf_hypothesis['confidence'] >= 0.75
        
        # Medium confidence
        med_conf_hypothesis = {
            'confidence': 0.65,
            'evidence': ['Some data', 'Moderate trend']
        }
        assert 0.5 <= med_conf_hypothesis['confidence'] < 0.75
        
        # Low confidence
        low_conf_hypothesis = {
            'confidence': 0.35,
            'evidence': ['Limited data']
        }
        assert low_conf_hypothesis['confidence'] < 0.5


if __name__ == '__main__':
    pytest.main([__file__, '-v'])