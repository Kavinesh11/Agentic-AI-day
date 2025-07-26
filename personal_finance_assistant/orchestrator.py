"""
Sequential Agent Orchestrator for Personal Finance Assistant
Manages the three-agent workflow: User -> Financial MCP -> Response
"""
import logging
import uuid
from typing import Dict, Any, Optional
from google.adk.agents import SequentialAgent
from google.adk.orchestration import Runner
from google.adk.orchestration.session import InMemorySessionService
from agents.user_agent import user_agent
from agents.fi_mcp_agent import fi_mcp_agent
from agents.respond_agent import respond_agent
from config.settings import settings, AgentNames
from tools.mcp_client import mcp_client
from mcp import StdioServerParameters

logger = logging.getLogger(__name__)


class PersonalFinanceOrchestrator:
    """Orchestrates the sequential agent workflow for personal finance queries"""

    def __init__(self):
        self.session_service = InMemorySessionService()
        self.runner = None
        self.sequential_agent = None
        self._initialize_orchestrator()

    def _initialize_orchestrator(self):
        """Initialize the sequential agent workflow"""
        try:
            # Create sequential agent with our three agents
            self.sequential_agent = SequentialAgent(
                name="personal_finance_sequential_agent",
                description="Sequential workflow for personal finance analysis",
                sub_agents=[user_agent, fi_mcp_agent, respond_agent]
            )

            # Create runner with session management
            self.runner = Runner(
                root_agent=self.sequential_agent,
                app_name=settings.adk_app_name,
                session_service=self.session_service
            )

            logger.info(
                "Personal Finance Orchestrator initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize orchestrator: {e}")
            raise

    async def initialize_mcp_connections(self):
        """Initialize MCP server connections for financial tools"""
        try:
            # Example MCP server configurations
            # In a production environment, these would be configured based on available servers

            # Financial analysis server (example configuration)
            financial_server_params = StdioServerParameters(
                command="python3",
                args=["financial_mcp_server.py"],  # Hypothetical MCP server
                env={"API_KEY": "your-api-key"}
            )

            # Connect to financial MCP server
            success = await mcp_client.connect_to_server("financial_server", financial_server_params)
            if success:
                logger.info("Connected to financial MCP server")
            else:
                logger.warning(
                    "Failed to connect to financial MCP server - using fallback analysis")

            # Market data server (example configuration)
            market_server_params = StdioServerParameters(
                command="npx",
                args=["@example/market-data-mcp-server"],
                env={}
            )

            # Connect to market data MCP server
            success = await mcp_client.connect_to_server("market_data_server", market_server_params)
            if success:
                logger.info("Connected to market data MCP server")
            else:
                logger.warning(
                    "Failed to connect to market data MCP server - using basic analysis")

        except Exception as e:
            logger.error(f"Error initializing MCP connections: {e}")
            # Continue without MCP servers - agents will use fallback methods

    async def process_financial_query(self,
                                      query_text: str,
                                      user_id: Optional[str] = None,
                                      session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a financial query through the sequential agent workflow
        
        Args:
            query_text: User's financial query
            user_id: Optional user identifier
            session_id: Optional session identifier
            
        Returns:
            Complete response from the sequential workflow
        """
        try:
            # Generate IDs if not provided
            if not user_id:
                user_id = f"user_{uuid.uuid4().hex[:8]}"
            if not session_id:
                session_id = f"session_{uuid.uuid4().hex[:8]}"

            logger.info(
                f"Processing query for user {user_id}, session {session_id}")

            # Create or get session
            session = self.session_service.create_session(
                app_name=settings.adk_app_name,
                user_id=user_id,
                session_id=session_id
            )

            # Prepare input content for the sequential agent
            from google.generativeai.types import content_types
            from google.generativeai.types.content_types import Part

            input_content = content_types.Content(
                role="user",
                parts=[Part.from_text(query_text)]
            )

            # Run the sequential agent workflow
            response = await self.runner.run_async(
                user_id=user_id,
                session_id=session_id,
                content=input_content
            )

            # Extract results from session state
            session_state = session.state

            # Get outputs from each agent
            user_context = session_state.get("user_context", {})
            financial_analysis = session_state.get("financial_analysis", {})
            final_response = session_state.get("final_response", {})

            # Compile complete response
            complete_response = {
                "query": query_text,
                "user_id": user_id,
                "session_id": session_id,
                "user_context": user_context,
                "financial_analysis": financial_analysis,
                "final_response": final_response,
                "agent_responses": self._extract_agent_responses(response),
                "execution_metadata": {
                    "total_agents": 3,
                    "workflow_type": "sequential",
                    "success": True
                }
            }

            logger.info(f"Successfully processed query for user {user_id}")
            return complete_response

        except Exception as e:
            logger.error(f"Error processing financial query: {e}")
            return {
                "query": query_text,
                "error": str(e),
                "execution_metadata": {
                    "success": False,
                    "error_type": type(e).__name__
                }
            }

    async def process_batch_queries(self, queries: list[Dict[str, str]]) -> list[Dict[str, Any]]:
        """
        Process multiple queries in batch
        
        Args:
            queries: List of query dictionaries with 'text', 'user_id', 'session_id'
            
        Returns:
            List of complete responses
        """
        results = []

        for query_info in queries:
            try:
                result = await self.process_financial_query(
                    query_text=query_info.get("text", ""),
                    user_id=query_info.get("user_id"),
                    session_id=query_info.get("session_id")
                )
                results.append(result)

            except Exception as e:
                logger.error(f"Error processing batch query: {e}")
                results.append({
                    "query": query_info.get("text", ""),
                    "error": str(e),
                    "execution_metadata": {"success": False}
                })

        return results

    def _extract_agent_responses(self, response) -> Dict[str, Any]:
        """Extract individual agent responses from workflow response"""
        agent_responses = {}

        try:
            # Process response events to extract agent-specific outputs
            for event in response.events:
                if hasattr(event, 'author') and hasattr(event, 'content'):
                    agent_name = event.author
                    if agent_name in [AgentNames.USER_AGENT, AgentNames.FI_MCP_AGENT, AgentNames.RESPOND_AGENT]:
                        agent_responses[agent_name] = {
                            "content": event.content.parts[0].text if event.content.parts else "",
                            "timestamp": getattr(event, 'timestamp', None)
                        }

        except Exception as e:
            logger.error(f"Error extracting agent responses: {e}")

        return agent_responses

    async def get_user_session_history(self, user_id: str, limit: int = 10) -> list[Dict[str, Any]]:
        """
        Get session history for a user
        
        Args:
            user_id: User identifier
            limit: Maximum number of sessions to return
            
        Returns:
            List of session summaries
        """
        try:
            # In a production system, this would query a persistent store
            # For now, we'll return sessions from the in-memory service
            sessions = []

            # Get all sessions for the user (limited implementation)
            # This would be enhanced with proper session persistence

            return sessions[:limit]

        except Exception as e:
            logger.error(f"Error getting user session history: {e}")
            return []

    async def clear_user_session(self, user_id: str, session_id: str) -> bool:
        """
        Clear a specific user session
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            
        Returns:
            True if session was cleared successfully
        """
        try:
            # Clear session from memory
            session = self.session_service.get_session(user_id, session_id)
            if session:
                session.state.clear()
                logger.info(f"Cleared session {session_id} for user {user_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"Error clearing user session: {e}")
            return False

    def get_agent_status(self) -> Dict[str, Any]:
        """
        Get status of all agents in the workflow
        
        Returns:
            Status information for each agent
        """
        try:
            return {
                "sequential_agent": {
                    "name": self.sequential_agent.name if self.sequential_agent else "Not initialized",
                    "sub_agents": [
                        {"name": AgentNames.USER_AGENT, "status": "active"},
                        {"name": AgentNames.FI_MCP_AGENT, "status": "active"},
                        {"name": AgentNames.RESPOND_AGENT, "status": "active"}
                    ]
                },
                "mcp_connections": {
                    "financial_server": "financial_server" in mcp_client.sessions,
                    "market_data_server": "market_data_server" in mcp_client.sessions
                },
                "session_service": {
                    "type": "InMemorySessionService",
                    "active": self.session_service is not None
                }
            }

        except Exception as e:
            logger.error(f"Error getting agent status: {e}")
            return {"error": str(e)}


# Global orchestrator instance
orchestrator = PersonalFinanceOrchestrator()

# Convenience functions for external use


async def process_query(query_text: str, user_id: Optional[str] = None, session_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to process a single financial query
    
    Args:
        query_text: User's financial query
        user_id: Optional user identifier
        session_id: Optional session identifier
        
    Returns:
        Complete response from the sequential workflow
    """
    return await orchestrator.process_financial_query(query_text, user_id, session_id)


async def initialize_system():
    """Initialize the complete system including MCP connections"""
    await orchestrator.initialize_mcp_connections()
    logger.info("Personal Finance Assistant system initialized")


def get_system_status() -> Dict[str, Any]:
    """Get current system status"""
    return orchestrator.get_agent_status()


# Export main components
__all__ = ["PersonalFinanceOrchestrator", "orchestrator",
           "process_query", "initialize_system", "get_system_status"]
