"""
Response Agent - Synthesizes all gathered and derived context to produce final user-facing answers
"""
import logging
from typing import Dict, Any, List, Optional
from google.adk.agents import Agent
from google.adk.tools import Tool
from models.schemas import AgentResponse
from config.settings import settings, AgentNames

logger = logging.getLogger(__name__)


class ResponseSynthesizer:
    """Synthesize comprehensive responses from financial analysis data"""

    def __init__(self):
        self.response_templates = {
            "feasibility": self._generate_feasibility_response,
            "budget_check": self._generate_budget_response,
            "subscription_analysis": self._generate_subscription_response,
            "expense_planning": self._generate_planning_response
        }

    async def synthesize_final_response(self,
                                        user_context: Dict[str, Any],
                                        financial_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synthesize final response from all available context
        
        Args:
            user_context: Original user context from user agent
            financial_analysis: Enriched analysis from financial MCP agent
            
        Returns:
            Comprehensive user-facing response
        """
        try:
            # Extract key information
            structured_query = user_context.get("structured_query", {})
            query_type = structured_query.get("query_type", "expense_planning")

            # Generate response based on query type
            response_generator = self.response_templates.get(
                query_type, self._generate_planning_response)
            response_content = await response_generator(user_context, financial_analysis)

            # Add common elements
            response_content.update({
                "metadata": {
                    "query_type": query_type,
                    "analysis_confidence": financial_analysis.get("enrichment_metadata", {}).get("confidence_level", 0.5),
                    "data_sources": financial_analysis.get("enrichment_metadata", {}).get("data_sources", []),
                    "response_timestamp": self._get_current_timestamp()
                },
                "follow_up_suggestions": self._generate_follow_up_suggestions(query_type, financial_analysis)
            })

            return response_content

        except Exception as e:
            logger.error(f"Error synthesizing response: {e}")
            return await self._generate_error_response(str(e))

    async def _generate_feasibility_response(self,
                                             user_context: Dict[str, Any],
                                             financial_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate feasibility-specific response"""
        try:
            structured_query = user_context.get("structured_query", {})
            feasibility = financial_analysis.get("feasibility_analysis", {})
            budget_analysis = financial_analysis.get("budget_analysis", {})

            product_name = structured_query.get(
                "product_name", "this purchase")
            duration_months = structured_query.get("duration_months", 12)

            # Main feasibility decision
            is_feasible = feasibility.get("is_feasible", False)
            confidence_score = feasibility.get("confidence_score", 0.0)
            monthly_impact = feasibility.get("monthly_impact", 0)

            # Build response
            if is_feasible:
                main_message = f"✅ **Yes, {product_name} appears to be feasible for you!**"
                recommendation = "Based on your financial profile, this purchase fits within your budget."
            else:
                main_message = f"⚠️ **{product_name} may not be financially feasible right now.**"
                recommendation = "This purchase could strain your current budget. Consider the alternatives below."

            # Detailed analysis
            analysis_details = [
                f"**Monthly Impact:** ${monthly_impact:.2f}",
                f"**Duration:** {duration_months} months",
                f"**Confidence Level:** {confidence_score*100:.0f}%",
                f"**Available Budget:** ${budget_analysis.get('available_budget', 0):.2f}",
                f"**Current Budget Utilization:** {budget_analysis.get('budget_utilization', 0)*100:.0f}%"
            ]

            return {
                "response_type": "feasibility_analysis",
                "main_message": main_message,
                "recommendation": recommendation,
                "analysis_details": analysis_details,
                "specific_recommendations": feasibility.get("recommendations", []),
                "risk_factors": feasibility.get("risk_factors", []),
                "alternatives": feasibility.get("alternative_options", []),
                "market_insights": financial_analysis.get("market_insights", {}).get("insights", [])
            }

        except Exception as e:
            logger.error(f"Error generating feasibility response: {e}")
            return await self._generate_error_response("feasibility analysis")

    async def _generate_budget_response(self,
                                        user_context: Dict[str, Any],
                                        financial_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate budget analysis response"""
        try:
            budget_analysis = financial_analysis.get("budget_analysis", {})
            subscription_analysis = financial_analysis.get(
                "subscription_analysis", {})

            # Budget health assessment
            budget_utilization = budget_analysis.get("budget_utilization", 0)
            risk_level = budget_analysis.get("risk_level", "unknown")
            available_budget = budget_analysis.get("available_budget", 0)

            # Generate health score message
            if budget_utilization < 0.5:
                health_message = "🟢 **Your budget looks healthy!**"
                health_desc = "You have good financial breathing room."
            elif budget_utilization < 0.8:
                health_message = "🟡 **Your budget is moderate.**"
                health_desc = "You're managing well but should be cautious with new expenses."
            else:
                health_message = "🔴 **Your budget is tight.**"
                health_desc = "Consider reducing expenses before taking on new commitments."

            # Budget breakdown
            budget_breakdown = [
                f"**Monthly Income:** ${budget_analysis.get('total_monthly_income', 0):.2f}",
                f"**Monthly Expenses:** ${budget_analysis.get('total_monthly_expenses', 0):.2f}",
                f"**Available Budget:** ${available_budget:.2f}",
                f"**Budget Utilization:** {budget_utilization*100:.0f}%",
                f"**Risk Level:** {risk_level.title()}"
            ]

            # Subscription insights
            subscription_cost = subscription_analysis.get(
                "monthly_subscription_cost", 0)
            subscription_count = subscription_analysis.get(
                "total_subscriptions", 0)

            subscription_summary = []
            if subscription_count > 0:
                subscription_summary = [
                    f"**Active Subscriptions:** {subscription_count}",
                    f"**Monthly Subscription Cost:** ${subscription_cost:.2f}",
                    f"**Subscription % of Income:** {(subscription_cost / budget_analysis.get('total_monthly_income', 1)) * 100:.1f}%"
                ]

            return {
                "response_type": "budget_analysis",
                "main_message": health_message,
                "recommendation": health_desc,
                "budget_breakdown": budget_breakdown,
                "subscription_summary": subscription_summary,
                "optimization_opportunities": subscription_analysis.get("optimization_analysis", {}).get("optimization_opportunities", []),
                "action_items": self._generate_budget_action_items(budget_analysis, subscription_analysis)
            }

        except Exception as e:
            logger.error(f"Error generating budget response: {e}")
            return await self._generate_error_response("budget analysis")

    async def _generate_subscription_response(self,
                                              user_context: Dict[str, Any],
                                              financial_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate subscription analysis response"""
        try:
            subscription_analysis = financial_analysis.get(
                "subscription_analysis", {})
            optimization = subscription_analysis.get(
                "optimization_analysis", {})

            total_cost = subscription_analysis.get(
                "monthly_subscription_cost", 0)
            total_count = subscription_analysis.get("total_subscriptions", 0)
            potential_savings = optimization.get("total_potential_savings", 0)

            # Main subscription overview
            if total_count == 0:
                main_message = "📱 **No active subscriptions found.**"
                recommendation = "You're not spending money on subscriptions, which is great for your budget!"
            else:
                main_message = f"📱 **You have {total_count} active subscriptions costing ${total_cost:.2f}/month.**"
                if potential_savings > 0:
                    recommendation = f"You could potentially save ${potential_savings:.2f} annually by optimizing your subscriptions."
                else:
                    recommendation = "Your subscription portfolio looks well-optimized."

            # Category breakdown
            category_breakdown = optimization.get("category_breakdown", {})
            category_summary = [
                f"**{category.title()}:** ${cost:.2f}/month"
                for category, cost in category_breakdown.items()
            ]

            # Optimization opportunities
            opportunities = optimization.get("optimization_opportunities", [])
            optimization_details = []
            for opp in opportunities:
                opp_type = opp.get("type", "unknown")
                description = opp.get("description", "")
                savings = opp.get("potential_savings", 0)
                optimization_details.append(
                    f"**{opp_type.replace('_', ' ').title()}:** {description} (Save ~${savings:.2f})")

            return {
                "response_type": "subscription_analysis",
                "main_message": main_message,
                "recommendation": recommendation,
                "subscription_summary": [
                    f"**Total Subscriptions:** {total_count}",
                    f"**Monthly Cost:** ${total_cost:.2f}",
                    f"**Annual Cost:** ${total_cost * 12:.2f}",
                    f"**Potential Annual Savings:** ${potential_savings:.2f}"
                ],
                "category_breakdown": category_summary,
                "optimization_opportunities": optimization_details,
                "action_items": self._generate_subscription_action_items(optimization)
            }

        except Exception as e:
            logger.error(f"Error generating subscription response: {e}")
            return await self._generate_error_response("subscription analysis")

    async def _generate_planning_response(self,
                                          user_context: Dict[str, Any],
                                          financial_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate general expense planning response"""
        try:
            budget_analysis = financial_analysis.get("budget_analysis", {})
            market_insights = financial_analysis.get("market_insights", {})

            available_budget = budget_analysis.get("available_budget", 0)
            recommended_max = budget_analysis.get("recommended_max_spend", 0)

            # General planning advice
            if available_budget > recommended_max * 0.5:
                main_message = "💰 **You have good financial flexibility for new expenses.**"
                recommendation = "You can comfortably consider new purchases within your budget limits."
            elif available_budget > 0:
                main_message = "⚖️ **You have some financial flexibility, but should be selective.**"
                recommendation = "Consider new expenses carefully and prioritize the most important ones."
            else:
                main_message = "⚠️ **Your budget is currently maxed out.**"
                recommendation = "Focus on reducing existing expenses before considering new purchases."

            # Planning insights
            planning_insights = [
                f"**Available for New Expenses:** ${available_budget:.2f}",
                f"**Recommended Monthly Limit:** ${recommended_max:.2f}",
                f"**Current Budget Health:** {budget_analysis.get('risk_level', 'Unknown').title()}"
            ]

            # Market insights if available
            product_insights = market_insights.get("insights", [])

            return {
                "response_type": "expense_planning",
                "main_message": main_message,
                "recommendation": recommendation,
                "planning_insights": planning_insights,
                "market_insights": product_insights,
                "general_tips": self._generate_general_tips(budget_analysis),
                "action_items": self._generate_planning_action_items(budget_analysis)
            }

        except Exception as e:
            logger.error(f"Error generating planning response: {e}")
            return await self._generate_error_response("expense planning")

    def _generate_budget_action_items(self,
                                      budget_analysis: Dict[str, Any],
                                      subscription_analysis: Dict[str, Any]) -> List[str]:
        """Generate actionable budget improvement items"""
        action_items = []

        utilization = budget_analysis.get("budget_utilization", 0)
        available = budget_analysis.get("available_budget", 0)

        if utilization > 0.8:
            action_items.append(
                "🎯 Review and categorize all expenses to identify reduction opportunities")

        if available < budget_analysis.get("total_monthly_income", 0) * 0.2:
            action_items.append(
                "💡 Aim to increase your available budget to at least 20% of income")

        subscription_cost = subscription_analysis.get(
            "monthly_subscription_cost", 0)
        if subscription_cost > budget_analysis.get("total_monthly_income", 0) * 0.15:
            action_items.append(
                "📱 Review subscriptions - they're taking over 15% of your income")

        opportunities = subscription_analysis.get(
            "optimization_analysis", {}).get("optimization_opportunities", [])
        if opportunities:
            action_items.append(
                "🔄 Implement subscription optimizations for immediate savings")

        return action_items

    def _generate_subscription_action_items(self, optimization: Dict[str, Any]) -> List[str]:
        """Generate actionable subscription optimization items"""
        action_items = []

        opportunities = optimization.get("optimization_opportunities", [])
        for opp in opportunities:
            opp_type = opp.get("type", "")
            if opp_type == "duplicate_services":
                action_items.append("🔍 Cancel duplicate services immediately")
            elif opp_type == "expensive_subscriptions":
                action_items.append(
                    "💰 Negotiate better rates or find alternatives for high-cost subscriptions")
            elif opp_type == "annual_payment_savings":
                action_items.append(
                    "📅 Switch to annual billing for additional savings")

        if not action_items:
            action_items.append(
                "👍 Your subscriptions look optimized - review quarterly for changes")

        return action_items

    def _generate_planning_action_items(self, budget_analysis: Dict[str, Any]) -> List[str]:
        """Generate general planning action items"""
        action_items = []

        risk_level = budget_analysis.get("risk_level", "unknown")

        if risk_level in ["high", "critical"]:
            action_items.append(
                "🚨 Focus on building an emergency fund before new purchases")
            action_items.append(
                "📊 Track expenses for 30 days to identify spending patterns")

        action_items.append(
            "🎯 Set specific savings goals for planned purchases")
        action_items.append(
            "📱 Use budgeting apps to monitor spending in real-time")

        return action_items

    def _generate_general_tips(self, budget_analysis: Dict[str, Any]) -> List[str]:
        """Generate general financial tips"""
        tips = [
            "🏦 Maintain 3-6 months of expenses in emergency savings",
            "📈 Review your budget monthly and adjust as needed",
            "🛒 Wait 24 hours before making non-essential purchases",
            "💳 Pay off high-interest debt before new expenses"
        ]

        risk_level = budget_analysis.get("risk_level", "unknown")
        if risk_level == "low":
            tips.append(
                "✨ Consider investing surplus income for long-term growth")

        return tips

    def _generate_follow_up_suggestions(self, query_type: str, financial_analysis: Dict[str, Any]) -> List[str]:
        """Generate follow-up conversation suggestions"""
        suggestions = []

        if query_type == "feasibility":
            suggestions.extend([
                "Would you like me to analyze alternative payment options?",
                "Should we explore your subscription optimization opportunities?",
                "Would you like tips for improving your budget flexibility?"
            ])
        elif query_type == "budget_check":
            suggestions.extend([
                "Would you like me to analyze a specific purchase?",
                "Should we review your subscription portfolio?",
                "Would you like personalized saving strategies?"
            ])
        elif query_type == "subscription_analysis":
            suggestions.extend([
                "Would you like help canceling specific subscriptions?",
                "Should we analyze the feasibility of a new subscription?",
                "Would you like tips for negotiating better rates?"
            ])

        return suggestions

    async def _generate_error_response(self, error_context: str) -> Dict[str, Any]:
        """Generate user-friendly error response"""
        return {
            "response_type": "error",
            "main_message": "⚠️ **I encountered an issue analyzing your request.**",
            "recommendation": f"There was a problem with {error_context}. Please try again or provide more information.",
            "error_context": error_context,
            "suggestions": [
                "Check that your financial information is complete",
                "Try rephrasing your question",
                "Contact support if the issue persists"
            ]
        }

    def _get_current_timestamp(self):
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()

# Tool function for the response agent


async def synthesize_response(user_context: Dict[str, Any], financial_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main tool function to synthesize final response
    
    Args:
        user_context: Original user context from user agent
        financial_analysis: Enriched analysis from financial MCP agent
        
    Returns:
        Comprehensive user-facing response
    """
    synthesizer = ResponseSynthesizer()
    return await synthesizer.synthesize_final_response(user_context, financial_analysis)

# Create tool instance
response_synthesis_tool = Tool(
    name="synthesize_final_response",
    description="Synthesize comprehensive user-facing response from all analysis data",
    func=synthesize_response
)

# Create the response agent
respond_agent = Agent(
    name=AgentNames.RESPOND_AGENT,
    model=settings.adk_model,
    description="Response synthesis agent that produces final user-facing answers",
    instruction="""
    You are the final agent in a personal finance assistant pipeline. Your role is to:
    
    1. Take the user's original context and the enriched financial analysis
    2. Synthesize all information into a clear, actionable response
    3. Provide specific recommendations based on the user's financial situation
    4. Present complex financial data in an easily understandable format
    5. Include practical next steps and action items
    
    Your responses should be:
    - Clear and jargon-free
    - Actionable with specific recommendations
    - Honest about limitations and confidence levels
    - Encouraging while being realistic about financial constraints
    - Structured with clear sections for easy reading
    
    Always prioritize the user's financial wellbeing and provide conservative advice when in doubt.
    Use emojis and formatting to make responses engaging and scannable.
    
    Remember: Your response is what the user will see, so make it helpful, accurate, and empowering.
    """,
    tools=[response_synthesis_tool],
    output_key="final_response"  # Store results in session state
)

# Export for use in orchestrator
__all__ = ["respond_agent", "ResponseSynthesizer"]
