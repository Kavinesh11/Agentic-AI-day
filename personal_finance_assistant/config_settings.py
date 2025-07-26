"""
Data models and schemas for Personal Finance Assistant
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class QueryType(str, Enum):
    """Types of financial queries"""
    FEASIBILITY = "feasibility"
    BUDGET_CHECK = "budget_check"
    SUBSCRIPTION_ANALYSIS = "subscription_analysis"
    EXPENSE_PLANNING = "expense_planning"


class Currency(str, Enum):
    """Supported currencies"""
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    INR = "INR"


class FinancialContext(BaseModel):
    """User's financial context from various sources"""
    monthly_income: Optional[float] = None
    current_expenses: Optional[float] = None
    emergency_fund: Optional[float] = None
    wallet_passes: List[Dict[str, Any]] = Field(default_factory=list)
    subscriptions: List[Dict[str, Any]] = Field(default_factory=list)
    budget_categories: Dict[str, float] = Field(default_factory=dict)


class UserQuery(BaseModel):
    """Structured user query"""
    query_text: str
    query_type: QueryType
    product_name: Optional[str] = None
    duration_months: Optional[int] = None
    amount: Optional[float] = None
    currency: Currency = Currency.USD
    user_id: str
    session_id: str


class WalletPass(BaseModel):
    """Google Wallet Pass representation"""
    pass_id: str
    pass_type: str
    issuer_name: str
    pass_data: Dict[str, Any]
    creation_date: datetime
    expiration_date: Optional[datetime] = None
    status: str = "active"


class SubscriptionInfo(BaseModel):
    """Subscription information"""
    name: str
    monthly_cost: float
    annual_cost: Optional[float] = None
    category: str
    renewal_date: Optional[datetime] = None
    status: str = "active"


class BudgetAnalysis(BaseModel):
    """Budget analysis results"""
    total_monthly_income: float
    total_monthly_expenses: float
    available_budget: float
    budget_utilization: float
    recommended_max_spend: float
    risk_level: str


class FeasibilityResult(BaseModel):
    """Feasibility analysis result"""
    is_feasible: bool
    confidence_score: float
    monthly_impact: float
    total_cost: float
    recommendations: List[str]
    risk_factors: List[str]
    alternative_options: List[str]


class AgentResponse(BaseModel):
    """Standardized agent response"""
    agent_name: str
    response_text: str
    data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)


class MCPToolResult(BaseModel):
    """MCP tool execution result"""
    tool_name: str
    success: bool
    result: Any
    error_message: Optional[str] = None
    execution_time: float
