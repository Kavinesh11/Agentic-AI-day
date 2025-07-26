"""
Financial MCP Agent - Uses MCP tools and APIs to enrich queries with budget and subscription data
"""
import logging
import json
from typing import Dict, Any, List, Optional
from google.adk.agents import Agent
from google.adk.tools import Tool
from tools.mcp_client import mcp_client
from tools.budget_tools import analyze_budget, calculate_feasibility, optimize_subscriptions
from models.schemas import BudgetAnalysis, FeasibilityResult
from config.settings import settings, AgentNames, ToolNames

logger = logging.getLogger(__name__)


class FinancialDataEnricher:
    """Enrich financial queries with comprehensive data analysis"""

    def __init__(self):
        self.mcp_client = mcp_client

    async def enrich_financial_context(self, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich user context with comprehensive financial analysis
        
        Args:
            user_context: Context from user agent
            
        Returns:
            Enriched financial context with analysis
        """
        try:
            # Extract base financial data
            financial_context = user_context.get("financial_context", {})
            structured_query = user_context.get("structured_query", {})

            # Perform budget analysis
            budget_analysis = await self._perform_budget_analysis(financial_context)

            # Analyze subscriptions if available
            subscription_analysis = await self._analyze_subscriptions(
                financial_context.get("subscriptions", [])
            )

            # Get market insights via MCP if available
            market_insights = await self._get_market_insights(structured_query)

            # Calculate feasibility if specific product query
            feasibility_analysis = await self._calculate_product_feasibility(
                structured_query, financial_context, budget_analysis
            )

            return {
                "original_context": user_context,
                "budget_analysis": budget_analysis,
                "subscription_analysis": subscription_analysis,
                "market_insights": market_insights,
                "feasibility_analysis": feasibility_analysis,
                "enrichment_metadata": {
                    "analysis_timestamp": str(self._get_current_timestamp()),
                    "data_sources": ["wallet_api", "mcp_tools", "budget_analyzer"],
                    "confidence_level": self._calculate_overall_confidence(budget_analysis, feasibility_analysis)
                }
            }

        except Exception as e:
            logger.error(f"Error enriching financial context: {e}")
            return {
                "original_context": user_context,
                "error": str(e),
                "fallback_analysis": await self._fallback_analysis(user_context)
            }

    async def _perform_budget_analysis(self, financial_context: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive budget analysis"""
        try:
            # Try MCP-enhanced analysis first
            mcp_analysis = await self.mcp_client.get_budget_analysis(financial_context)
            if mcp_analysis:
                return mcp_analysis.dict()

            # Fallback to local analysis
            analysis = await analyze_budget(financial_context)
            return analysis

        except Exception as e:
            logger.error(f"Error in budget analysis: {e}")
            return {
                "total_monthly_income": financial_context.get("monthly_income", 0),
                "total_monthly_expenses": financial_context.get("current_expenses", 0),
                "available_budget": 0,
                "budget_utilization": 1.0,
                "recommended_max_spend": 0,
                "risk_level": "unknown"
            }

    async def _analyze_subscriptions(self, subscriptions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze subscription portfolio"""
        try:
            if not subscriptions:
                return {"total_subscriptions": 0, "monthly_cost": 0, "optimization_potential": 0}

            # Try MCP-enhanced subscription analysis
            mcp_insights = await self.mcp_client.get_subscription_insights(subscriptions)

            # Local optimization analysis
            optimization = await optimize_subscriptions(subscriptions)

            return {
                "subscription_insights": [insight.dict() for insight in mcp_insights] if mcp_insights else [],
                "optimization_analysis": optimization,
                "total_subscriptions": len(subscriptions),
                "monthly_subscription_cost": sum(sub.get("monthly_cost", 0) for sub in subscriptions)
            }

        except Exception as e:
            logger.error(f"Error analyzing subscriptions: {e}")
            return {
                "total_subscriptions": len(subscriptions),
                "monthly_subscription_cost": sum(sub.get("monthly_cost", 0) for sub in subscriptions),
                "error": str(e)
            }

    async def _get_market_insights(self, structured_query: Dict[str, Any]) -> Dict[str, Any]:
        """Get market insights for the queried product/service"""
        try:
            product_name = structured_query.get("product_name")
            if not product_name:
                return {"insights": [], "market_data": {}}

            # Try to get market data via MCP tools
            market_result = await self.mcp_client.call_tool(
                server_name="market_data_server",
                tool_name="get_product_pricing",
                arguments={"product_name": product_name}
            )

            if market_result.success:
                return {
                    "product_name": product_name,
                    "market_data": market_result.result,
                    "insights": self._extract_market_insights(market_result.result)
                }

            # Fallback to basic insights
            return {
                "product_name": product_name,
                "market_data": {},
                "insights": [f"Consider comparing prices for {product_name} across different providers"]
            }

        except Exception as e:
            logger.error(f"Error getting market insights: {e}")
            return {"insights": [], "market_data": {}, "error": str(e)}

    async def _calculate_product_feasibility(self,
                                             structured_query: Dict[str, Any],
                                             financial_context: Dict[str, Any],
                                             budget_analysis: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Calculate feasibility for specific product/service"""
        try:
            product_name = structured_query.get("product_name")
            duration_months = structured_query.get("duration_months")
            amount = structured_query.get("amount")

            if not product_name:
                return None

            # Estimate cost if not provided
            if not amount:
                amount = await self._estimate_product_cost(product_name)

            if not duration_months:
                duration_months = 12  # Default to 1 year

            # Use MCP-enhanced feasibility calculation
            feasibility_data = await self.mcp_client.calculate_feasibility(
                financial_context, amount, duration_months
            )

            # Add product-specific context
            feasibility_data["product_context"] = {
                "product_name": product_name,
                "estimated_cost": amount,
                "duration_months": duration_months
            }

            return feasibility_data

        except Exception as e:
            logger.error(f"Error calculating product feasibility: {e}")
            return None

    async def _estimate_product_cost(self, product_name: str) -> float:
        """Estimate product cost using MCP tools or fallback logic"""
        try:
            # Try MCP pricing tool
            pricing_result = await self.mcp_client.call_tool(
                server_name="pricing_server",
                tool_name="estimate_cost",
                arguments={"product_name": product_name}
            )

            if pricing_result.success and pricing_result.result:
                return float(pricing_result.result.get("estimated_cost", 0))

            # Fallback to basic estimation logic
            product_lower = product_name.lower()

            # Common service price estimates
            if "netflix" in product_lower:
                return 15.99
            elif "spotify" in product_lower or "music" in product_lower:
                return 9.99
            elif "gym" in product_lower or "fitness" in product_lower:
                return 50.0
            elif "phone" in product_lower or "mobile" in product_lower:
                return 70.0
            elif "internet" in product_lower or "wifi" in product_lower:
                return 60.0
            else:
                return 25.0  # Generic subscription estimate

        except Exception as e:
            logger.error(f"Error estimating product cost: {e}")
            return 25.0

    def _extract_market_insights(self, market_data: Any) -> List[str]:
        """Extract actionable insights from market data"""
        insights = []

        try:
            if isinstance(market_data, dict):
                # Price comparison insights
                if "average_price" in market_data and "price_range" in market_data:
                    avg_price = market_data["average_price"]
                    price_range = market_data["price_range"]
                    insights.append(f"Average market price: ${avg_price:.2f}")
                    insights.append(
                        f"Price range: ${price_range.get('min', 0):.2f} - ${price_range.get('max', 0):.2f}")

                # Seasonal insights
                if "seasonal_trends" in market_data:
                    insights.append(
                        "Consider seasonal pricing trends when making your purchase")

                # Alternative suggestions
                if "alternatives" in market_data:
                    # Top 3 alternatives
                    alternatives = market_data["alternatives"][:3]
                    if alternatives:
                        alt_names = [alt.get("name", "Unknown")
                                     for alt in alternatives]
                        insights.append(
                            f"Consider alternatives: {', '.join(alt_names)}")

        except Exception as e:
            logger.error(f"Error extracting market insights: {e}")

        return insights

    def _calculate_overall_confidence(self, budget_analysis: Dict[str, Any], feasibility_analysis: Optional[Dict[str, Any]]) -> float:
        """Calculate overall confidence in the analysis"""
        confidence_factors = []

        # Budget analysis confidence
        if budget_analysis.get("total_monthly_income", 0) > 0:
            confidence_factors.append(0.8)
        else:
            confidence_factors.append(0.3)

        # Feasibility analysis confidence
        if feasibility_analysis and feasibility_analysis.get("confidence_score"):
            confidence_factors.append(feasibility_analysis["confidence_score"])
        else:
            confidence_factors.append(0.5)

        # Data completeness confidence
        data_completeness = 0.6  # Base confidence
        if budget_analysis.get("available_budget") is not None:
            data_completeness += 0.2
        if feasibility_analysis:
            data_completeness += 0.2

        confidence_factors.append(data_completeness)

        return round(sum(confidence_factors) / len(confidence_factors), 2)

    async def _fallback_analysis(self, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Provide fallback analysis when enrichment fails"""
        return {
            "message": "Using basic analysis due to data limitations",
            "recommendations": [
                "Please provide more detailed financial information for better analysis",
                "Consider connecting more financial accounts for comprehensive insights",
                "Manual review recommended for important financial decisions"
            ],
            "confidence_level": 0.3
        }

    def _get_current_timestamp(self):
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now()

# Tool functions for the financial MCP agent


async def enrich_financial_data(user_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main tool function to enrich financial data
    
    Args:
        user_context: Context from user agent
        
    Returns:
        Enriched financial context
    """
    enricher = FinancialDataEnricher()
    return await enricher.enrich_financial_context(user_context)


async def get_subscription_recommendations(subscriptions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Get subscription optimization recommendations
    
    Args:
        subscriptions: List of subscription data
        
    Returns:
        Optimization recommendations
    """
    try:
        optimization = await optimize_subscriptions(subscriptions)
        return {
            "recommendations": optimization.get("optimization_opportunities", []),
            "potential_savings": optimization.get("total_potential_savings", 0),
            "category_breakdown": optimization.get("category_breakdown", {})
        }
    except Exception as e:
        logger.error(f"Error getting subscription recommendations: {e}")
        return {"error": str(e), "recommendations": []}

# Create tool instances
financial_enrichment_tool = Tool(
    name=ToolNames.BUDGET_ANALYSIS,
    description="Enrich user financial context with comprehensive budget and market analysis",
    func=enrich_financial_data
)

subscription_tool = Tool(
    name=ToolNames.SUBSCRIPTION_CHECK,
    description="Analyze subscription portfolio and provide optimization recommendations",
    func=get_subscription_recommendations
)

# Create the financial MCP agent
fi_mcp_agent = Agent(
    name=AgentNames.FI_MCP_AGENT,
    model=settings.adk_model,
    description="Financial analysis agent that uses MCP tools to enrich queries with budget and subscription data",
    instruction="""
    You are a financial analysis agent that enriches user queries with comprehensive financial data.
    Your role is to:
    
    1. Take structured user context from the user agent
    2. Perform detailed budget analysis using available financial data
    3. Use MCP tools to get market insights and pricing information
    4. Analyze subscription portfolios for optimization opportunities
    5. Calculate feasibility for specific products or services
    6. Provide data-driven insights and recommendations
    
    When processing financial context:
    - Always prioritize accuracy and conservative estimates
    - Use multiple data sources when available (Wallet API, MCP tools, market data)
    - Provide confidence levels for your analysis
    - Include both optimistic and pessimistic scenarios
    - Consider the user's overall financial health, not just immediate affordability
    
    Your output will be used by the response agent to generate the final user-facing recommendation.
    Make sure your analysis is thorough, well-structured, and includes actionable insights.
    """,
    tools=[financial_enrichment_tool, subscription_tool],
    output_key="financial_analysis"  # Store results in session state
)

# Export for use in orchestrator
__all__ = ["fi_mcp_agent", "FinancialDataEnricher"]
