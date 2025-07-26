"""
Personal Finance Assistant - Main Application Entry Point
Built with Google ADK using sequential agent workflow pattern
"""
import asyncio
import logging
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.adk.agents.sequential_agent import SequentialAgent

from config.settings import settings
from orchestrator import process_query, get_system_status, initialize_system

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('personal_finance_assistant.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class PersonalFinanceAssistantApp:
    """Main application class for Personal Finance Assistant"""

    def __init__(self):
        self.initialized = False

    async def initialize(self):
        """Initialize the complete system"""
        try:
            logger.info("Initializing Personal Finance Assistant...")

            # Load environment variables
            load_dotenv()

            # Validate configuration
            if not self._validate_configuration():
                raise ValueError(
                    "Invalid configuration - check environment variables")

            # Initialize MCP connections and system components
            await initialize_system()

            self.initialized = True
            logger.info("Personal Finance Assistant initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize system: {e}")
            raise

    def _validate_configuration(self) -> bool:
        """Validate required configuration settings"""
        required_settings = []

        if not settings.google_api_key and not settings.google_application_credentials:
            required_settings.append(
                "GOOGLE_API_KEY or GOOGLE_APPLICATION_CREDENTIALS")

        if not settings.google_cloud_project:
            logger.warning(
                "GOOGLE_CLOUD_PROJECT not set - some features may be limited")

        if not settings.wallet_issuer_id:
            logger.warning(
                "WALLET_ISSUER_ID not set - wallet integration disabled")

        if required_settings:
            logger.error(
                f"Missing required configuration: {', '.join(required_settings)}")
            return False

        return True

    async def process_query(self,
                            query_text: str,
                            user_id: Optional[str] = None,
                            session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a financial query through the system

        Args:
            query_text: User's financial question
            user_id: Optional user identifier
            session_id: Optional session identifier

        Returns:
            Complete response with analysis and recommendations
        """
        if not self.initialized:
            raise RuntimeError(
                "System not initialized - call initialize() first")

        try:
            logger.info(f"Processing query: {query_text[:100]}...")
            result = await process_query(query_text, user_id, session_id)
            logger.info("Query processed successfully")
            return result

        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                "error": str(e),
                "query": query_text,
                "success": False
            }

    def get_status(self) -> Dict[str, Any]:
        """Get current system status"""
        status = get_system_status()
        status["initialized"] = self.initialized
        return status


async def main():
    """Main application function with interactive CLI"""
    app = PersonalFinanceAssistantApp()

    try:
        # Initialize the system
        await app.initialize()

        print("\n" + "="*60)
        print("🏦 Personal Finance Assistant")
        print("Built with Google ADK and MCP Integration")
        print("="*60)
        print("\nSystem Status:")
        status = app.get_status()
        print(f"✅ System Initialized: {status.get('initialized', False)}")
        print(
            f"📊 Active Agents: {len(status.get('sequential_agent', {}).get('sub_agents', []))}")
        print(
            f"🔌 MCP Connections: {sum(status.get('mcp_connections', {}).values())}")

        print("\n" + "-"*60)
        print("💡 Example Queries:")
        print("• 'If I pay for Netflix for 6 months, will it be feasible given my income?'")
        print("• 'Can I afford a $50/month gym membership?'")
        print("• 'Analyze my current subscription spending'")
        print("• 'What's my budget situation this month?'")
        print("\nType 'quit' or 'exit' to end the session")
        print("-"*60)

        # Interactive query loop
        while True:
            try:
                query = input("\n🤖 Ask me about your finances: ").strip()

                if query.lower() in ['quit', 'exit', 'q']:
                    print("\n👋 Thanks for using Personal Finance Assistant!")
                    break

                if not query:
                    continue

                if query.lower() == 'status':
                    status = app.get_status()
                    print(f"\n📊 System Status: {status}")
                    continue

                print("\n🔄 Analyzing your query...")

                # Process the query
                result = await app.process_query(query)

                if result.get("success", True):
                    # Display the response
                    await display_response(result)
                else:
                    print(f"\n❌ Error: {result.get('error', 'Unknown error')}")

            except KeyboardInterrupt:
                print("\n\n👋 Session interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Unexpected error: {e}")
                continue

    except Exception as e:
        logger.error(f"Application error: {e}")
        print(f"\n❌ Failed to start application: {e}")
        print("Please check your configuration and try again.")


async def display_response(result: Dict[str, Any]):
    """Display the formatted response to the user"""
    try:
        final_response = result.get("final_response", {})

        if not final_response:
            print("\n⚠️ No response generated")
            return

        # Main message
        main_message = final_response.get("main_message", "")
        if main_message:
            print(f"\n{main_message}")

        # Recommendation
        recommendation = final_response.get("recommendation", "")
        if recommendation:
            print(f"\n💡 {recommendation}")

        # Analysis details
        analysis_details = final_response.get("analysis_details", [])
        if analysis_details:
            print(f"\n📊 **Analysis Details:**")
            for detail in analysis_details:
                print(f"   {detail}")

        # Budget breakdown
        budget_breakdown = final_response.get("budget_breakdown", [])
        if budget_breakdown:
            print(f"\n💰 **Budget Summary:**")
            for item in budget_breakdown:
                print(f"   {item}")

        # Recommendations
        specific_recommendations = final_response.get(
            "specific_recommendations", [])
        if specific_recommendations:
            print(f"\n🎯 **Recommendations:**")
            for i, rec in enumerate(specific_recommendations, 1):
                print(f"   {i}. {rec}")

        # Risk factors
        risk_factors = final_response.get("risk_factors", [])
        if risk_factors:
            print(f"\n⚠️ **Risk Factors:**")
            for risk in risk_factors:
                print(f"   • {risk}")

        # Alternatives
        alternatives = final_response.get("alternatives", [])
        if alternatives:
            print(f"\n🔄 **Alternatives to Consider:**")
            for alt in alternatives:
                print(f"   • {alt}")

        # Action items
        action_items = final_response.get("action_items", [])
        if action_items:
            print(f"\n✅ **Next Steps:**")
            for action in action_items:
                print(f"   {action}")

        # Market insights
        market_insights = final_response.get("market_insights", [])
        if market_insights:
            print(f"\n📈 **Market Insights:**")
            for insight in market_insights:
                print(f"   • {insight}")

        # Follow-up suggestions
        follow_up = final_response.get("follow_up_suggestions", [])
        if follow_up and len(follow_up) > 0:
            print(f"\n🤔 **Want to explore more?**")
            for suggestion in follow_up[:2]:
                print(f"   • {suggestion}")

        # Metadata
        metadata = final_response.get("metadata", {})
        if metadata.get("analysis_confidence"):
            confidence = metadata["analysis_confidence"]
            print(f"\n📊 Analysis Confidence: {confidence*100:.0f}%")

    except Exception as e:
        logger.error(f"Error displaying response: {e}")
        print(f"\n❌ Error displaying response: {e}")


def create_env_template():
    """Create a .env template file with required variables"""
    template = """# Personal Finance Assistant Configuration

# Google Cloud Configuration
GOOGLE_API_KEY=your_google_api_key_here
GOOGLE_CLOUD_PROJECT=your_project_id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
GOOGLE_GENAI_USE_VERTEXAI=false

# Google Wallet API Configuration
WALLET_ISSUER_ID=your_wallet_issuer_id
WALLET_SERVICE_ACCOUNT_FILE=path/to/wallet-service-account.json

# ADK Configuration
ADK_MODEL=gemini-2.0-flash
ADK_APP_NAME=PersonalFinanceAssistant

# MCP Configuration
MCP_SERVER_TIMEOUT=30
MCP_MAX_RETRIES=3

# Financial Analysis Configuration
DEFAULT_CURRENCY=USD
RISK_THRESHOLD=0.8
EMERGENCY_FUND_MONTHS=3
"""

    with open(".env.template", "w") as f:
        f.write(template)

    print("📝 Created .env.template file")
    print("Please copy this to .env and fill in your actual values")


if __name__ == "__main__":
    try:
        if not os.path.exists(".env"):
            print("⚠️ .env file not found")
            create_env_template()
            print("Please configure your .env file and run again")
        else:
            asyncio.run(main())

    except KeyboardInterrupt:
        print("\n👋 Application terminated by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"💥 Fatal error: {e}")
    finally:
        print("🔄 Cleanup completed")
