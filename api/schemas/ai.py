from pydantic import BaseModel, Field
from typing import Dict, Any, List
from api.schemas.analyze import InsightResponse

class AIExplainRequest(BaseModel):
    metrics: Dict[str, Any] = Field(..., description="Metrics bundle from analysis")
    insights: List[InsightResponse] = Field(..., description="Triggered insights list")

class AIRemediationCard(BaseModel):
    title: str = Field(..., description="Short title of the remediation")
    description: str = Field(..., description="Explanation of what this remediation solves")
    code: str = Field(..., description="Remediation command, configuration, or code snippet")
    language: str = Field(..., description="Programming language or format of the code snippet for syntax highlighting")

class AIExplainResponse(BaseModel):
    summary: str = Field(..., description="A concise high-level overview of the log state")
    explanation: str = Field(..., description="Markdown-formatted detailed analysis and root-cause explanation")
    remediations: List[AIRemediationCard] = Field(..., description="Actionable remediation steps with code snippets")
