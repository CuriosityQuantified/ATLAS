"""
Worker agents module.
Contains all worker agent implementations that use ReAct pattern with tools.
"""

from .web_researcher import WebResearchWorker

__all__ = [
    "WebResearchWorker",
    # Future workers will be added here:
    # "DocumentAnalystWorker",
    # "AcademicResearchWorker", 
    # "SourceVerifierWorker",
    # "DataAnalystWorker",
    # "ContentWriterWorker",
    # etc.
]