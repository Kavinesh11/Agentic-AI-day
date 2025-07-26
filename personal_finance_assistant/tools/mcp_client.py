"""
Budget analysis and financial calculation tools
"""
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from models.schemas import BudgetAnalysis, FeasibilityResult, SubscriptionInfo
from config.settings import settings

logger = logging.getLogger(__name__)


class BudgetAnalyzer:
    """Advanced budget analysis and financial calculations"""

    def __init__(self):
        self.risk_threshold = settings.risk_threshold
        self.emergency_fund_months = settings.emergency_fund_months

    def analyze_comprehensive_budget(self, financial_context: Dict[str, Any]) -> BudgetAnalysis:
        """
        Perform comprehensive budget analysis
        
        Args:
            financial_context: Complete financial information
            
        Returns:
            BudgetAnalysis with detailed insights
        """
        try:
            # Extract financial data
            monthly_income = financial_context.get("monthly_income", 0)
            current_expenses = financial_context.get("current_expenses", 0)
            subscriptions = financial_context.get("subscriptions", [])
            budget_categories = financial_context.get("budget_categories", {})
            emergency_fund = financial_context.get("emergency_fund", 0)

            # Calculate subscription costs
            total_subscription_cost = sum(
                sub.get("monthly_cost", 0) for sub in subscriptions
            )

            # Calculate total monthly expenses
            total_monthly_expenses = current_expenses + total_subscription_cost

            # Add category-based expenses
            category_expenses = sum(budget_categories.values())
            total_monthly_expenses += category_expenses

            # Calculate metrics
            available_budget = monthly_income - total_monthly_expenses
            budget_utilization = (
                total_monthly_expenses / monthly_income) if monthly_income > 0 else 1.0
            recommended_max_spend = monthly_income * self.risk_threshold

            # Determine risk level
            risk_level = self._calculate_risk_level(
                budget_utilization, emergency_fund, monthly_income)

            return BudgetAnalysis(
                total_monthly_income=monthly_income,
                total_monthly_expenses=total_monthly_expenses,
                available_budget=available_budget,
                budget_utilization=budget_utilization,
                recommended_max_spend=recommended_max_spend,
                risk_level=risk_level
            )

        except Exception as e:
            logger.error(f"Error in comprehensive budget analysis: {e}")
            # Return conservative defaults
            return BudgetAnalysis(
                total_monthly_income=0,
                total_monthly_expenses=0,
                available_budget=0,
                budget_utilization=1.0,
                recommended_max_spend=0,
                risk_level="high"
            )

    def calculate_purchase_feasibility(self,
                                       budget_analysis: BudgetAnalysis,
                                       product_name: str,
                                       total_cost: float,
                                       duration_months: int,
                                       payment_structure: str = "monthly") -> FeasibilityResult:
        """
        Calculate feasibility of a purchase or subscription
        
        Args:
            budget_analysis: Current budget analysis
            product_name: Name of product/service
            total_cost: Total cost of purchase
            duration_months: Duration in months
            payment_structure: Payment structure (monthly, annual, one-time)
            
        Returns:
            FeasibilityResult with detailed analysis
        """
        try:
            # Calculate monthly impact
            if payment_structure == "monthly" and duration_months > 0:
                monthly_impact = total_cost / duration_months
            elif payment_structure == "annual":
                monthly_impact = total_cost / 12
            else:  # one-time payment
                monthly_impact = total_cost  # Assume immediate impact

            # Calculate feasibility metrics
            after_purchase_budget = budget_analysis.available_budget - monthly_impact
            new_utilization = ((budget_analysis.total_monthly_expenses + monthly_impact) /
                               budget_analysis.total_monthly_income if budget_analysis.total_monthly_income > 0 else 1.0)

            # Determine feasibility
            is_feasible = (
                after_purchase_budget >= 0 and
                new_utilization <= self.risk_threshold and
                monthly_impact <= budget_analysis.recommended_max_spend
            )

            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(
                budget_analysis, monthly_impact, new_utilization
            )

            # Generate recommendations and risk factors
            recommendations = self._generate_recommendations(
                budget_analysis, monthly_impact, is_feasible, product_name
            )

            risk_factors = self._identify_risk_factors(
                budget_analysis, monthly_impact, new_utilization
            )

            # Suggest alternatives
            alternative_options = self._suggest_alternatives(
                total_cost, duration_months, monthly_impact, is_feasible
            )

            return FeasibilityResult(
                is_feasible=is_feasible,
                confidence_score=confidence_score,
                monthly_impact=monthly_impact,
                total_cost=total_cost,
                recommendations=recommendations,
                risk_factors=risk_factors,
                alternative_options=alternative_options
            )

        except Exception as e:
            logger.error(f"Error calculating purchase feasibility: {e}")
            return FeasibilityResult(
                is_feasible=False,
                confidence_score=0.0,
                monthly_impact=total_cost,
                total_cost=total_cost,
                recommendations=[
                    "Unable to analyze - please review your financial information"],
                risk_factors=["Analysis error occurred"],
                alternative_options=["Consult with a financial advisor"]
            )

    def optimize_subscription_portfolio(self, subscriptions: List[SubscriptionInfo]) -> Dict[str, Any]:
        """
        Analyze and optimize subscription portfolio
        
        Args:
            subscriptions: List of current subscriptions
            
        Returns:
            Optimization recommendations
        """
        try:
            # Calculate subscription metrics
            total_monthly_cost = sum(sub.monthly_cost for sub in subscriptions)
            total_annual_cost = sum(sub.annual_cost or (
                sub.monthly_cost * 12) for sub in subscriptions)

            # Group by category
            category_costs = {}
            for sub in subscriptions:
                category = sub.category or "other"
                category_costs[category] = category_costs.get(
                    category, 0) + sub.monthly_cost

            # Identify optimization opportunities
            optimization_opportunities = []

            # Find duplicate services
            service_names = [sub.name.lower() for sub in subscriptions]
            duplicates = []
            for i, name in enumerate(service_names):
                if service_names.count(name) > 1 and name not in duplicates:
                    duplicates.append(name)

            if duplicates:
                optimization_opportunities.append({
                    "type": "duplicate_services",
                    "description": f"Duplicate services found: {', '.join(duplicates)}",
                    "potential_savings": sum(sub.monthly_cost for sub in subscriptions
                                             if sub.name.lower() in duplicates) / 2
                })

            # Find expensive subscriptions
            high_cost_threshold = total_monthly_cost * \
                0.3  # 30% of total subscription budget
            expensive_subs = [
                sub for sub in subscriptions if sub.monthly_cost > high_cost_threshold]

            if expensive_subs:
                optimization_opportunities.append({
                    "type": "expensive_subscriptions",
                    "description": f"High-cost subscriptions: {', '.join(sub.name for sub in expensive_subs)}",
                    # 50% potential reduction
                    "potential_savings": sum(sub.monthly_cost * 0.5 for sub in expensive_subs)
                })

            # Annual vs monthly savings
            annual_savings = 0
            for sub in subscriptions:
                if sub.annual_cost and sub.annual_cost < (sub.monthly_cost * 12):
                    annual_savings += (sub.monthly_cost * 12) - sub.annual_cost

            if annual_savings > 0:
                optimization_opportunities.append({
                    "type": "annual_payment_savings",
                    "description": "Switch to annual payments for additional savings",
                    "potential_savings": annual_savings
                })

            return {
                "total_monthly_cost": total_monthly_cost,
                "total_annual_cost": total_annual_cost,
                "category_breakdown": category_costs,
                "optimization_opportunities": optimization_opportunities,
                "total_potential_savings": sum(op.get("potential_savings", 0) for op in optimization_opportunities)
            }

        except Exception as e:
            logger.error(f"Error optimizing subscription portfolio: {e}")
            return {
                "total_monthly_cost": 0,
                "total_annual_cost": 0,
                "category_breakdown": {},
                "optimization_opportunities": [],
                "total_potential_savings": 0
            }

    def _calculate_risk_level(self, budget_utilization: float, emergency_fund: float, monthly_income: float) -> str:
        """Calculate overall financial risk level"""
        # Emergency fund adequacy
        emergency_fund_ratio = (emergency_fund / (monthly_income * self.emergency_fund_months)
                                if monthly_income > 0 else 0)

        # Combined risk assessment
        if budget_utilization < 0.5 and emergency_fund_ratio >= 1.0:
            return "low"
        elif budget_utilization < 0.7 and emergency_fund_ratio >= 0.5:
            return "medium"
        elif budget_utilization < 0.85:
            return "high"
        else:
            return "critical"

    def _calculate_confidence_score(self, budget_analysis: BudgetAnalysis, monthly_impact: float, new_utilization: float) -> float:
        """Calculate confidence score for feasibility assessment"""
        try:
            # Base confidence on available budget buffer
            budget_buffer = budget_analysis.available_budget - monthly_impact
            buffer_ratio = budget_buffer / \
                budget_analysis.total_monthly_income if budget_analysis.total_monthly_income > 0 else 0

            # Adjust for utilization level
            utilization_penalty = max(0, new_utilization - self.risk_threshold)

            # Calculate final confidence score
            confidence = max(0, min(1, buffer_ratio - utilization_penalty))

            return round(confidence, 2)

        except Exception:
            return 0.0

    def _generate_recommendations(self, budget_analysis: BudgetAnalysis, monthly_impact: float, is_feasible: bool, product_name: str) -> List[str]:
        """Generate personalized recommendations"""
        recommendations = []

        if not is_feasible:
            recommendations.append(
                f"Consider waiting and saving for {product_name}")
            recommendations.append("Review and reduce current expenses first")
            recommendations.append("Look for promotional offers or discounts")

            if budget_analysis.budget_utilization > 0.9:
                recommendations.append(
                    "Focus on increasing income before new purchases")
        else:
            if monthly_impact > budget_analysis.available_budget * 0.5:
                recommendations.append(
                    "This purchase will significantly impact your budget")
                recommendations.append(
                    "Consider setting up automatic savings for future similar purchases")

            recommendations.append(
                "Monitor your spending closely after this purchase")

        # General financial health recommendations
        if budget_analysis.risk_level in ["high", "critical"]:
            recommendations.append(
                "Build an emergency fund before major purchases")
            recommendations.append(
                "Consider consulting with a financial advisor")

        return recommendations

    def _identify_risk_factors(self, budget_analysis: BudgetAnalysis, monthly_impact: float, new_utilization: float) -> List[str]:
        """Identify potential risk factors"""
        risk_factors = []

        if new_utilization > self.risk_threshold:
            risk_factors.append(
                f"Budget utilization will exceed {self.risk_threshold*100}% threshold")

        if monthly_impact > budget_analysis.available_budget:
            risk_factors.append("Monthly cost exceeds available budget")

        if budget_analysis.risk_level in ["high", "critical"]:
            risk_factors.append(
                "Current financial situation is already high-risk")

        if monthly_impact > budget_analysis.total_monthly_income * 0.2:
            risk_factors.append(
                "Purchase represents significant portion of income")

        return risk_factors

    def _suggest_alternatives(self, total_cost: float, duration_months: int, monthly_impact: float, is_feasible: bool) -> List[str]:
        """Suggest alternative approaches"""
        alternatives = []

        if not is_feasible:
            # Suggest longer payment terms
            if duration_months < 24:
                longer_term_cost = total_cost / 24
                alternatives.append(
                    f"Extend payment to 24 months (${longer_term_cost:.2f}/month)")

            # Suggest waiting and saving
            months_to_save = int(
                monthly_impact / (monthly_impact * 0.1)) if monthly_impact > 0 else 6
            alternatives.append(
                f"Save for {months_to_save} months and pay in full")

            # Suggest lower-cost alternatives
            alternatives.append("Look for similar products at lower cost")
            alternatives.append("Consider used or refurbished options")

        # Annual payment benefits
        if duration_months >= 12:
            annual_discount = total_cost * 0.1  # Assume 10% annual discount
            alternatives.append(
                f"Annual payment might save ~${annual_discount:.2f}")

        return alternatives

# Tool functions for ADK integration


async def analyze_budget(financial_context: Dict[str, Any]) -> Dict[str, Any]:
    """ADK tool function for budget analysis"""
    analyzer = BudgetAnalyzer()
    analysis = analyzer.analyze_comprehensive_budget(financial_context)
    return analysis.dict()


async def calculate_feasibility(financial_context: Dict[str, Any],
                                product_name: str,
                                total_cost: float,
                                duration_months: int) -> Dict[str, Any]:
    """ADK tool function for feasibility calculation"""
    analyzer = BudgetAnalyzer()
    budget_analysis = analyzer.analyze_comprehensive_budget(financial_context)
    feasibility = analyzer.calculate_purchase_feasibility(
        budget_analysis, product_name, total_cost, duration_months
    )
    return feasibility.dict()


async def optimize_subscriptions(subscriptions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """ADK tool function for subscription optimization"""
    analyzer = BudgetAnalyzer()
    subscription_objects = [SubscriptionInfo(**sub) for sub in subscriptions]
    optimization = analyzer.optimize_subscription_portfolio(
        subscription_objects)
    return optimization
