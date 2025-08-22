"""
Clinical AI Guardrails: Agentic ML Validation Pipeline

This package provides a minimal-viable prototype of an agentic AI pipeline 
for reproducible validation experiments in clinical machine learning.

Architecture:
    - Core ML Components: Data processing, model training, statistical validation
    - Agent Framework: Testing infrastructure using smolagents
    - Testing Pyramid: Unit → Integration → End-to-End validation

Key Modules:
    - data_processing: Data cleaning, feature engineering, preprocessing
    - model_training: Model training, evaluation, comparison, inference  
    - stats_tools: Statistical validation, hypothesis testing, effect sizes
    - agent: Agentic testing infrastructure and validation suite

Usage:
    from clinical_ai_guardrails.agent import validate_ml_codebase
    
    results = validate_ml_codebase(
        codebase_path="./src",
        data_path="./data/clinical_data.csv" 
    )
"""

__version__ = "0.1.0"

# Import key classes and functions for easy access
# from .data_processing import DataProcessor
# from .model_training import ModelTrainer, ModelInference
# from ...tests.stats_tools import StatisticalValidator
# from ...tests.orchestrator.agent import ValidationTestSuite, validate_ml_codebase

# __all__ = [
#     "DataProcessor",
#     "ModelTrainer", 
#     "ModelInference",
#     "StatisticalValidator",
#     "ValidationTestSuite",
#     "validate_ml_codebase"
# ]
