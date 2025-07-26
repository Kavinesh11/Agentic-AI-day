#!/usr/bin/env python3
"""
Example MCP Financial Server for Personal Finance Assistant
Demonstrates how to create MCP tools for financial analysis
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from mcp.server.fastmcp import FastMCP
from mcp.server.stdio import stdio_server

logger = logging.getLogger(__name__)

# Create FastMCP server instance
mcp = FastMCP("financial_analysis_server")


@mcp.tool()
def analyze_budget(monthly_income: float, expenses: Dict[str, float], subscriptions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze user's budget and provide financial health assessment
    
    Args:
        monthly_income: User's monthly income
        expenses: Dictionary of expense categories and amounts
        subscriptions: List of subscription information
        
    Returns:
        Comprehensive budget analysis
    """
    try:
        # Calculate total expenses
        total_fixed_expenses = sum(expenses.values()) if expenses else 0
        total_subscription_cost = sum(
            sub.get("monthly_cost", 0) for sub in subscriptions)
        total_monthly_expenses = total_fixed_expenses + total_subscription_cost

        # Calculate key metrics
        available_budget = monthly_income - total_monthly_expenses
        budget_utilization = total_monthly_expenses / \
            monthly_income if monthly_income > 0 else 1.0
        recommended_max_spend = monthly_income * 0.8  # 80% threshold

        # Determine risk level
        if budget_utilization < 0.5:
            risk_level = "low"
        elif budget_utilization < 0.8:
            risk_level = "medium"
        else:
            risk_level = "high"

        # Generate insights
        insights = []
        if budget_utilization > 0.9:
            insights.append(
                "Budget utilization is very high - consider reducing expenses")
        if total_subscription_cost > monthly_income * 0.15:
            insights.append(
                "Subscriptions represent over 15% of income - review for optimization")
        if available_budget < monthly_income * 0.2:
            insights.append(
                "Limited financial flexibility - build emergency fund priority")

        return {
            "total_monthly_income": monthly_income,
            "total_monthly_expenses": total_monthly_expenses,
            "available_budget": available_budget,
            "budget_utilization": budget_utilization,
            "recommended_max_spend": recommended_max_spend,
            "risk_level": risk_level,
            "insights": insights,
            "category_breakdown": {
                "fixed_expenses": total_fixed_expenses,
                "subscriptions": total_subscription_cost,
                "available": available_budget
            }
        }

    except Exception as e:
        logger.error(f"Error in budget analysis: {e}")
        return {"error": str(e), "analysis_available": False}


@mcp.tool()
def calculate_feasibility(financial_context: Dict[str, Any], product_cost: float, duration_months: int, risk_threshold: float = 0.8) -> Dict[str, Any]:
    """
    Calculate feasibility of a purchase or subscription
    
    Args:
        financial_context: User's financial information
        product_cost: Total cost of product/service
        duration_months: Duration in months
        risk_threshold: Risk threshold for budget utilization
        
    Returns:
        Feasibility analysis with recommendations
    """
    try:
        monthly_income = financial_context.get("monthly_income", 0)
        current_expenses = financial_context.get("current_expenses", 0)

        # Calculate monthly impact
        monthly_cost = product_cost / duration_months if duration_months > 0 else product_cost
        new_total_expenses = current_expenses + monthly_cost
        new_utilization = new_total_expenses / \
            monthly_income if monthly_income > 0 else 1.0

        # Determine feasibility
        is_feasible = (new_utilization <= risk_threshold) and (
            monthly_income > new_total_expenses)

        # Calculate confidence score
        buffer = monthly_income - new_total_expenses
        confidence_score = max(
            0, min(1, buffer / (monthly_income * 0.2))) if monthly_income > 0 else 0

        # Generate recommendations
        recommendations = []
        risk_factors = []
        alternatives = []

        if not is_feasible:
            recommendations.extend([
                "Consider reducing other expenses first",
                "Look for promotional offers or discounts",
                "Explore payment plan options"
            ])
            risk_factors.append("Exceeds recommended budget threshold")
            alternatives.extend([
                f"Extend payment period to {duration_months + 6} months",
                "Wait and save for 3-6 months",
                "Look for lower-cost alternatives"
            ])
        else:
            recommendations.extend([
                "Purchase fits within your budget",
                "Monitor spending after this addition",
                "Consider setting up automatic savings"
            ])

            if new_utilization > 0.7:
                risk_factors.append("Will use significant portion of budget")

        # Add market-based alternatives
        alternatives.extend([
            "Check for annual payment discounts",
            "Compare with competitor offerings",
            "Consider sharing plans with family/friends"
        ])

        return {
            "is_feasible": is_feasible,
            "confidence_score": round(confidence_score, 2),
            "monthly_impact": monthly_cost,
            "total_cost": product_cost,
            "new_budget_utilization": round(new_utilization, 3),
            "recommendations": recommendations,
            "risk_factors": risk_factors,
            "alternative_options": alternatives,
            "financial_impact": {
                "current_monthly_expenses": current_expenses,
                "new_monthly_expenses": new_total_expenses,
                "remaining_budget": monthly_income - new_total_expenses
            }
        }

    except Exception as e:
        logger.error(f"Error in feasibility calculation: {e}")
        return {"error": str(e), "is_feasible": False}


@mcp.tool()
def analyze_subscriptions(subscriptions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Analyze subscription portfolio and provide optimization insights
    
    Args:
        subscriptions: List of subscription data
        
    Returns:
        Enhanced subscription analysis with optimization opportunities
    """
    try:
        enhanced_subscriptions = []
        total_monthly = 0
        category_totals = {}

        for sub in subscriptions:
            monthly_cost = sub.get("monthly_cost", 0)
            category = sub.get("category", "other")
            name = sub.get("name", "Unknown Service")

            total_monthly += monthly_cost
            category_totals[category] = category_totals.get(
                category, 0) + monthly_cost

            # Calculate value metrics
            annual_cost = monthly_cost * 12

            # Determine optimization potential
            optimization_score = 1.0  # Default: no optimization needed
            optimization_reasons = []

            # High-cost services
            if monthly_cost > 50:
                optimization_score = 0.7
                optimization_reasons.append(
                    "High monthly cost - consider negotiating or alternatives")

            # Specific service insights
            if "netflix" in name.lower() or "streaming" in category.lower():
                optimization_reasons.append(
                    "Consider sharing plan or seasonal subscriptions")
            elif "gym" in name.lower() or "fitness" in category.lower():
                optimization_reasons.append("Evaluate actual usage vs. cost")
            elif "phone" in name.lower() or "mobile" in category.lower():
                optimization_reasons.append(
                    "Review data plan needs and competitor offers")

            enhanced_sub = {
                **sub,
                "annual_cost": annual_cost,
                "optimization_score": optimization_score,
                "optimization_suggestions": optimization_reasons,
                "category_percentage": 0  # Will calculate after processing all
            }

            enhanced_subscriptions.append(enhanced_sub)

        # Calculate category percentages
        for sub in enhanced_subscriptions:
            if total_monthly > 0:
                sub["cost_percentage"] = (
                    sub["monthly_cost"] / total_monthly) * 100

        # Add portfolio-level insights
        portfolio_insights = []

        if total_monthly > 200:
            portfolio_insights.append(
                "High total subscription cost - consider consolidation")

        # Check for potential duplicates
        service_names = [sub["name"].lower() for sub in subscriptions]
        if len(service_names) != len(set(service_names)):
            portfolio_insights.append("Potential duplicate services detected")

        # Category analysis
        if category_totals.get("entertainment", 0) > total_monthly * 0.4:
            portfolio_insights.append(
                "Entertainment subscriptions are 40%+ of total")

        return enhanced_subscriptions

    except Exception as e:
        logger.error(f"Error in subscription analysis: {e}")
        return [{"error": str(e)} for _ in subscriptions]


@mcp.tool()
def get_product_pricing(product_name: str) -> Dict[str, Any]:
    """
    Get market pricing information for a product or service
    
    Args:
        product_name: Name of product/service
        
    Returns:
        Market pricing data and insights
    """
    try:
        # Simulated market data - in production, this would call real APIs
        pricing_database = {
            "netflix": {
                "average_price": 15.99,
                "price_range": {"min": 6.99, "max": 22.99},
                "alternatives": [
                    {"name": "Hulu", "price": 7.99},
                    {"name": "Disney+", "price": 10.99},
                    {"name": "Apple TV+", "price": 6.99}
                ],
                "annual_discount_available": True,
                "seasonal_trends": "Prices typically stable, but promotions common in Q4"
            },
            "spotify": {
                "average_price": 10.99,
                "price_range": {"min": 5.99, "max": 16.99},
                "alternatives": [
                    {"name": "Apple Music", "price": 10.99},
                    {"name": "YouTube Music", "price": 10.99},
                    {"name": "Amazon Music", "price": 8.99}
                ],
                "annual_discount_available": False,
                "seasonal_trends": "Student discounts available year-round"
            },
            "gym membership": {
                "average_price": 45.00,
                "price_range": {"min": 20.00, "max": 100.00},
                "alternatives": [
                    {"name": "Home workout apps", "price": 15.00},
                    {"name": "Community center", "price": 25.00},
                    {"name": "Outdoor activities", "price": 0.00}
                ],
                "annual_discount_available": True,
                "seasonal_trends": "January promotions common, summer deals frequent"
            }
        }

        # Normalize product name for lookup
        normalized_name = product_name.lower().strip()

        # Find matching product data
        product_data = None
        for key in pricing_database:
            if key in normalized_name or normalized_name in key:
                product_data = pricing_database[key]
                break

        if not product_data:
            # Generic response for unknown products
            return {
                "product_name": product_name,
                "average_price": 25.00,  # Generic estimate
                "price_range": {"min": 10.00, "max": 50.00},
                "alternatives": [],
                "insights": [f"Research {product_name} pricing across multiple providers"],
                "data_availability": "limited"
            }

        # Generate insights
        insights = []
        avg_price = product_data["average_price"]

        if product_data.get("annual_discount_available"):
            insights.append(f"Annual plans typically save 10-20% vs monthly")

        if len(product_data.get("alternatives", [])) > 0:
            cheapest_alt = min(
                product_data["alternatives"], key=lambda x: x["price"])
            insights.append(
                f"Cheapest alternative: {cheapest_alt['name']} at ${cheapest_alt['price']:.2f}")

        insights.append(product_data.get("seasonal_trends",
                        "Monitor for seasonal promotions"))

        return {
            "product_name": product_name,
            "average_price": avg_price,
            "price_range": product_data["price_range"],
            "alternatives": product_data.get("alternatives", []),
            "insights": insights,
            "seasonal_trends": product_data.get("seasonal_trends"),
            "data_availability": "comprehensive"
        }

    except Exception as e:
        logger.error(f"Error getting product pricing: {e}")
        return {
            "product_name": product_name,
            "error": str(e),
            "data_availability": "unavailable"
        }


@mcp.resource("financial-tips://daily")
def get_daily_financial_tip() -> str:
    """Daily financial wisdom"""
    tips = [
        "Track your expenses for 30 days to identify spending patterns",
        "Set up automatic transfers to savings - even $25/month helps",
        "Review and cancel unused subscriptions quarterly",
        "Use the 24-hour rule for non-essential purchases over $50",
        "Build an emergency fund covering 3-6 months of expenses",
        "Compare prices before major purchases - savings add up",
        "Negotiate bills annually - many providers offer retention discounts",
        "Invest in your financial education - knowledge pays dividends"
    ]

    import random
    return random.choice(tips)


@mcp.prompt()
def create_savings_plan(goal_amount: float, target_months: int, current_savings: float = 0) -> str:
    """Generate a personalized savings plan"""
    remaining_amount = goal_amount - current_savings
    monthly_savings_needed = remaining_amount / \
        target_months if target_months > 0 else remaining_amount

    return f"""
# Savings Plan for ${goal_amount:,.2f} Goal

## Current Situation
- Target Amount: ${goal_amount:,.2f}
- Current Savings: ${current_savings:,.2f}
- Remaining Needed: ${remaining_amount:,.2f}
- Timeline: {target_months} months

## Monthly Savings Required
You need to save **${monthly_savings_needed:,.2f} per month** to reach your goal.

## Strategies to Reach Your Goal:
1. **Automate Your Savings**: Set up automatic transfer on payday
2. **Track Progress**: Review monthly and celebrate milestones
3. **Find Extra Money**: 
   - Cancel unused subscriptions (avg. saves $50/month)
   - Cook at home 2 extra days/week (saves $80/month)
   - Use cashback apps and rewards programs
4. **Increase Income**: Consider side gigs if monthly target is challenging

## Milestone Checkpoints:
- Month 3: ${monthly_savings_needed * 3:,.2f} saved
- Month 6: ${monthly_savings_needed * 6:,.2f} saved  
- Month 9: ${monthly_savings_needed * 9:,.2f} saved
- Goal Achievement: ${goal_amount:,.2f} saved!

Remember: Small, consistent actions lead to big results!
"""


async def main():
    """Run the MCP financial server"""
    async with stdio_server() as (read_stream, write_stream):
        await mcp.run(read_stream, write_stream, mcp.create_initialization_options())

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger.info("Starting Financial Analysis MCP Server")
    asyncio.run(main())
