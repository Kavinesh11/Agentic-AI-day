"""
User-facing agent for personal finance assistant
Handles user queries and integrates with Google Wallet API
"""
import logging
import re
from typing import Dict, Any, Optional
from google.adk.agents import Agent
from google.adk.tools import Tool
from models.schemas import UserQuery, QueryType, FinancialContext
from tools.wallet_tools import get_wallet_passes
from config.settings import settings, AgentNames, ToolNames

logger = logging.getLogger(__name__)


class UserQueryProcessor:
    """Process and structure user queries"""

    @staticmethod
    def parse_user_query(query_text: str, user_id: str, session_id: str) -> UserQuery:
        """
        Parse natural language query into structured format
        
        Args:
            query_text: Raw user query
            user_id: User identifier
            session_id: Session identifier
            
        Returns:
            Structured UserQuery object
        """
        try:
            # Extract query components using regex patterns
            query_lower = query_text.lower()

            # Determine query type
            if any(keyword in query_lower for keyword in ["feasible", "afford", "can i pay", "will it be feasible"]):
                query_type = QueryType.FEASIBILITY
            elif any(keyword in query_lower for keyword in ["budget", "spending", "expenses"]):
                query_type = QueryType.BUDGET_CHECK
            elif any(keyword in query_lower for keyword in ["subscription", "monthly payment", "recurring"]):
                query_type = QueryType.SUBSCRIPTION_ANALYSIS
            else:
                query_type = QueryType.EXPENSE_PLANNING

            # Extract product/service name
            product_name = UserQueryProcessor._extract_product_name(query_text)

            # Extract duration in months
            duration_months = UserQueryProcessor._extract_duration(query_text)

            # Extract amount if mentioned
            amount = UserQueryProcessor._extract_amount(query_text)

            return UserQuery(
                query_text=query_text,
                query_type=query_type,
                product_name=product_name,
                duration_months=duration_months,
                amount=amount,
                user_id=user_id,
                session_id=session_id
            )

        except Exception as e:
            logger.error(f"Error parsing user query: {e}")
            # Return basic query structure
            return UserQuery(
                query_text=query_text,
                query_type=QueryType.EXPENSE_PLANNING,
                user_id=user_id,
                session_id=session_id
            )

    @staticmethod
    def _extract_product_name(query_text: str) -> Optional[str]:
        """Extract product/service name from query"""
        # Look for patterns like "pay for X" or "buy X"
        patterns = [
            r"pay for ([^,\.\?!]+)",
            r"buy ([^,\.\?!]+)",
            r"purchase ([^,\.\?!]+)",
            r"subscribe to ([^,\.\?!]+)",
            r"get ([^,\.\?!]+)"
        ]

        for pattern in patterns:
            match = re.search(pattern, query_text, re.IGNORECASE)
            if match:
                product = match.group(1).strip()
                # Clean up common words
                product = re.sub(r'\b(a|an|the)\b', '', product,
                                 flags=re.IGNORECASE).strip()
                return product if product else None

        return None

    @staticmethod
    def _extract_duration(query_text: str) -> Optional[int]:
        """Extract duration in months from query"""
        # Look for patterns like "X months", "for X years"
        month_patterns = [
            r"(\d+)\s*months?",
            r"for\s*(\d+)\s*months?",
            r"over\s*(\d+)\s*months?"
        ]

        year_patterns = [
            r"(\d+)\s*years?",
            r"for\s*(\d+)\s*years?",
            r"over\s*(\d+)\s*years?"
        ]

        # Check for months
        for pattern in month_patterns:
            match = re.search(pattern, query_text, re.IGNORECASE)
            if match:
                return int(match.group(1))

        # Check for years (convert to months)
        for pattern in year_patterns:
            match = re.search(pattern, query_text, re.IGNORECASE)
            if match:
                return int(match.group(1)) * 12

        return None

    @staticmethod
    def _extract_amount(query_text: str) -> Optional[float]:
        """Extract monetary amount from query"""
        # Look for currency patterns
        currency_patterns = [
            r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*dollars?',
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*USD'
        ]

        for pattern in currency_patterns:
            match = re.search(pattern, query_text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '')
                try:
                    return float(amount_str)
                except ValueError:
                    continue

        return None

# Define tools for the user agent


async def process_wallet_context(user_id: str, issuer_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Tool to retrieve and process wallet context
    
    Args:
        user_id: User identifier
        issuer_id: Optional Google Wallet issuer ID
        
    Returns:
        Dictionary containing wallet context and financial information
    """
    try:
        # Use configured issuer ID if not provided
        if not issuer_id:
            issuer_id = settings.wallet_issuer_id

        if not issuer_id:
            logger.warning("No Wallet issuer ID configured")
            return {"error": "Wallet integration not configured", "context": {}}

        # Retrieve wallet passes
        wallet_data = await get_wallet_passes(issuer_id, user_id)

        # Process financial context
        financial_context = wallet_data.get("financial_context", {})

        return {
            "success": True,
            "wallet_passes": wallet_data.get("passes", []),
            "financial_context": financial_context,
            "total_passes": wallet_data.get("total_passes", 0)
        }

    except Exception as e:
        logger.error(f"Error processing wallet context: {e}")
        return {
            "success": False,
            "error": str(e),
            "financial_context": {},
            "wallet_passes": [],
            "total_passes": 0
        }


async def extract_query_context(query_text: str, user_id: str, session_id: str) -> Dict[str, Any]:
    """
    Tool to extract and structure query context
    
    Args:
        query_text: Raw user query
        user_id: User identifier
        session_id: Session identifier
        
    Returns:
        Structured query information
    """
    try:
        # Parse the user query
        structured_query = UserQueryProcessor.parse_user_query(
            query_text, user_id, session_id)

        return {
            "success": True,
            "structured_query": structured_query.dict(),
            "query_type": structured_query.query_type.value,
            "extracted_info": {
                "product_name": structured_query.product_name,
                "duration_months": structured_query.duration_months,
                "amount": structured_query.amount
            }
        }

    except Exception as e:
        logger.error(f"Error extracting query context: {e}")
        return {
            "success": False,
            "error": str(e),
            "structured_query": {},
            "query_type": "expense_planning"
        }

# Create tool instances
wallet_context_tool = Tool(
    name=ToolNames.WALLET_PASSES,
    description="Retrieve user's financial context from Google Wallet Generic Passes",
    func=process_wallet_context
)

query_context_tool = Tool(
    name="extract_query_context",
    description="Extract and structure information from user queries",
    func=extract_query_context
)

# Create the user agent
user_agent = Agent(
    name=AgentNames.USER_AGENT,
    model=settings.adk_model,
    description="User-facing agent that processes queries and retrieves wallet context",
    instruction="""
    You are a personal finance assistant's user interface agent. Your role is to:
    
    1. Process user queries about financial feasibility and budget questions
    2. Extract relevant information like product names, costs, and timeframes
    3. Retrieve the user's financial context from their Google Wallet passes
    4. Structure all information for the next agent in the pipeline
    
    When a user asks questions like "If I pay for Netflix for 6 months, will it be feasible given my income?":
    - Extract the service name (Netflix)
    - Extract the duration (6 months)
    - Retrieve their financial context from Wallet passes
    - Pass structured information to the financial analysis agent
    
    Always be helpful and clear in your responses. If you cannot extract specific information,
    ask clarifying questions or make reasonable assumptions based on context.
    
    Remember: You are the first step in a sequential agent workflow. Your output will be
    used by the financial MCP agent for detailed analysis.
    """,
    tools=[wallet_context_tool, query_context_tool],
    output_key="user_context"  # Store results in session state
)

# Export for use in orchestrator
__all__ = ["user_agent", "UserQueryProcessor"]
