#!/usr/bin/env python3
"""
Example usage and test script for Personal Finance Assistant
Demonstrates how to use the system programmatically
"""

import asyncio
import json
import logging
from typing import Dict, Any
from orchestrator import process_query, initialize_system

# Configure logging for testing
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PersonalFinanceDemo:
    """Demo class showing various use cases"""

    def __init__(self):
        self.test_queries = [
            {
                "query": "If I pay for Netflix for 6 months, will it be feasible given my income?",
                "description": "Feasibility analysis for streaming service",
                "user_id": "demo_user_1",
                "session_id": "session_feasibility"
            },
            {
                "query": "Can I afford a $50/month gym membership?",
                "description": "Monthly subscription affordability check",
                "user_id": "demo_user_2",
                "session_id": "session_gym"
            },
            {
                "query": "Analyze my current subscription spending",
                "description": "Subscription portfolio analysis",
                "user_id": "demo_user_3",
                "session_id": "session_subscriptions"
            },
            {
                "query": "What's my budget situation this month?",
                "description": "General budget health check",
                "user_id": "demo_user_4",
                "session_id": "session_budget"
            }
        ]

    async def run_demo(self):
        """Run the complete demo with all test queries"""
        print("🏦 Personal Finance Assistant Demo")
        print("=" * 50)

        # Initialize the system
        print("\n🔄 Initializing system...")
        try:
            await initialize_system()
            print("✅ System initialized successfully")
        except Exception as e:
            print(f"❌ System initialization failed: {e}")
            print("⚠️ Continuing with demo - some features may not work")

        # Process each test query
        for i, test_case in enumerate(self.test_queries, 1):
            print(f"\n📝 Test Case {i}: {test_case['description']}")
            print(f"Query: '{test_case['query']}'")
            print("-" * 30)

            try:
                # Process the query
                result = await process_query(
                    query_text=test_case["query"],
                    user_id=test_case["user_id"],
                    session_id=test_case["session_id"]
                )

                # Display results
                await self.display_result(result)

            except Exception as e:
                print(f"❌ Error processing query: {e}")
                continue

            print("\n" + "="*50)

    async def display_result(self, result: Dict[str, Any]):
        """Display formatted results from query processing"""
        try:
            if not result.get("execution_metadata", {}).get("success", True):
                print(
                    f"❌ Query failed: {result.get('error', 'Unknown error')}")
                return

            # Extract key components
            final_response = result.get("final_response", {})
            user_context = result.get("user_context", {})
            financial_analysis = result.get("financial_analysis", {})

            # Display main response
            main_message = final_response.get("main_message", "")
            if main_message:
                print(f"🎯 {main_message}")

            recommendation = final_response.get("recommendation", "")
            if recommendation:
                print(f"💡 {recommendation}")

            # Show analysis details
            analysis_details = final_response.get("analysis_details", [])
            if analysis_details:
                print(f"\n📊 Analysis:")
                for detail in analysis_details[:3]:  # Show first 3 details
                    print(f"   • {detail}")

            # Show key recommendations
            recommendations = final_response.get(
                "specific_recommendations", [])
            if recommendations:
                print(f"\n🎯 Recommendations:")
                for rec in recommendations[:2]:  # Show first 2 recommendations
                    print(f"   • {rec}")

            # Show confidence level
            metadata = final_response.get("metadata", {})
            confidence = metadata.get("analysis_confidence")
            if confidence:
                print(f"\n📈 Confidence: {confidence*100:.0f}%")

            # Show workflow metadata
            workflow_info = result.get("execution_metadata", {})
            print(f"\n🔧 Workflow: {workflow_info.get('total_agents', 0)} agents, "
                  f"Type: {workflow_info.get('workflow_type', 'unknown')}")

        except Exception as e:
            logger.error(f"Error displaying result: {e}")
            print(f"❌ Error displaying result: {e}")

    async def run_single_query(self, query: str, user_id: str = "test_user") -> Dict[str, Any]:
        """Run a single query for testing"""
        print(f"\n🤖 Processing: {query}")

        try:
            result = await process_query(
                query_text=query,
                user_id=user_id,
                session_id=f"session_{hash(query) % 10000}"
            )

            await self.display_result(result)
            return result

        except Exception as e:
            print(f"❌ Error: {e}")
            return {"error": str(e), "success": False}

    def create_mock_financial_context(self) -> Dict[str, Any]:
        """Create mock financial context for testing without Wallet API"""
        return {
            "monthly_income": 4500.0,
            "current_expenses": 2800.0,
            "emergency_fund": 5000.0,
            "subscriptions": [
                {"name": "Spotify", "monthly_cost": 9.99,
                    "category": "entertainment"},
                {"name": "Phone Plan", "monthly_cost": 65.00, "category": "utilities"},
                {"name": "Netflix", "monthly_cost": 15.99,
                    "category": "entertainment"}
            ],
            "budget_categories": {
                "housing": 1200.0,
                "food": 400.0,
                "transportation": 300.0,
                "utilities": 200.0,
                "other": 300.0
            }
        }


async def main():
    """Main demo function"""
    demo = PersonalFinanceDemo()

    print("Choose an option:")
    print("1. Run full demo with all test cases")
    print("2. Enter a custom query")
    print("3. Show mock financial context")
    print("4. Test specific scenarios")

    try:
        choice = input("\nEnter your choice (1-4): ").strip()

        if choice == "1":
            await demo.run_demo()

        elif choice == "2":
            custom_query = input("\nEnter your financial query: ").strip()
            if custom_query:
                await demo.run_single_query(custom_query)
            else:
                print("❌ No query provided")

        elif choice == "3":
            mock_context = demo.create_mock_financial_context()
            print("\n📊 Mock Financial Context:")
            print(json.dumps(mock_context, indent=2))

        elif choice == "4":
            await run_specific_scenarios()

        else:
            print("❌ Invalid choice")

    except KeyboardInterrupt:
        print("\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"❌ Demo failed: {e}")


async def run_specific_scenarios():
    """Run specific test scenarios"""
    scenarios = [
        {
            "name": "High-cost subscription",
            "query": "Can I afford a $200/month premium software subscription for my business?",
            "context": "Tests high-value purchase feasibility"
        },
        {
            "name": "Multiple subscriptions",
            "query": "I want to add Disney+, HBO Max, and Apple TV+ - can I afford all three?",
            "context": "Tests multiple simultaneous additions"
        },
        {
            "name": "Budget optimization",
            "query": "How can I optimize my spending to save $200 per month?",
            "context": "Tests expense reduction strategies"
        },
        {
            "name": "Emergency fund check",
            "query": "Do I have enough emergency savings for unexpected expenses?",
            "context": "Tests financial safety assessment"
        }
    ]

    demo = PersonalFinanceDemo()

    print("\n🧪 Running Specific Test Scenarios")
    print("=" * 40)

    for i, scenario in enumerate(scenarios, 1):
        print(f"\n📋 Scenario {i}: {scenario['name']}")
        print(f"Context: {scenario['context']}")
        print(f"Query: {scenario['query']}")
        print("-" * 30)

        await demo.run_single_query(scenario["query"], f"scenario_user_{i}")

        if i < len(scenarios):
            input("\nPress Enter to continue to next scenario...")


def print_usage_examples():
    """Print usage examples for developers"""
    examples = """
🔧 Developer Usage Examples:

1. Basic Query Processing:
```python
from orchestrator import process_query

result = await process_query(
    query_text="Can I afford Netflix for 6 months?",
    user_id="user123",
    session_id="session456"
)
```

2. Batch Processing:
```python
from orchestrator import orchestrator

queries = [
    {"text": "Budget analysis", "user_id": "user1", "session_id": "s1"},
    {"text": "Netflix feasibility", "user_id": "user2", "session_id": "s2"}
]

results = await orchestrator.process_batch_queries(queries)
```

3. System Status Check:
```python
from orchestrator import get_system_status

status = get_system_status()
print(f"Agents active: {len(status['sequential_agent']['sub_agents'])}")
```

4. Custom Financial Context:
```python
custom_context = {
    "monthly_income": 5000,
    "current_expenses": 3000,
    "subscriptions": [...]
}

# Process with custom context (requires agent modification)
```
"""
    print(examples)


if __name__ == "__main__":
    print("🏦 Personal Finance Assistant - Test & Demo Script")
    print("This script demonstrates the system's capabilities")
    print()

    # Check if user wants to see usage examples
    show_examples = input(
        "Show developer usage examples? (y/N): ").strip().lower()
    if show_examples in ['y', 'yes']:
        print_usage_examples()
        print()

    # Run the main demo
    asyncio.run(main())
