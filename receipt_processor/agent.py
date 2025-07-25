import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from google.adk.agents.llm_agent import Agent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent, AGENT_CARD_WELL_KNOWN_PATH
from google.genai import types as genai_types

# Import our specialized agents
from agents.input_handler_agent import input_handler_agent
from agents.pass_generator_agent import pass_generator_agent

logger = logging.getLogger(__name__)


class ReceiptProcessorSystem:
    def __init__(self):
        # Set up A2A connections to remote parser agents
        self.retail_parser = RemoteA2aAgent(
            name="retail_parser_agent",
            description="Specialized parser for retail and e-commerce receipts",
            agent_card=f"http://localhost:8001/a2a/retail_parser{AGENT_CARD_WELL_KNOWN_PATH}"
        )

        self.food_parser = RemoteA2aAgent(
            name="food_parser_agent",
            description="Specialized parser for food and dining receipts",
            agent_card=f"http://localhost:8002/a2a/food_parser{AGENT_CARD_WELL_KNOWN_PATH}"
        )

        self.misc_parser = RemoteA2aAgent(
            name="misc_parser_agent",
            description="Specialized parser for miscellaneous receipts",
            agent_card=f"http://localhost:8003/a2a/misc_parser{AGENT_CARD_WELL_KNOWN_PATH}"
        )

        # Create the main orchestrator agent following ADK patterns
        self.agent = Agent(
            model="gemini-2.0-flash-exp",
            name="receipt_processor",
            description="Multi-agent receipt processing system with Firebase integration and wallet pass generation",
            instruction="""  
            You are a comprehensive receipt processing system that orchestrates multiple specialized agents to:  
              
            1. Accept receipt inputs from multiple sources (camera, screenshot, email)  
            2. Classify and route receipts to appropriate parser agents  
            3. Extract structured data from different receipt types  
            4. Store receipt data and metadata in Firebase  
            5. Generate personalized wallet passes  
            6. Provide spending insights and notifications  
              
            Your workflow:  
            1. Delegate receipt input handling to input_handler_agent  
            2. Route classified receipts to specialized parser agents (retail, food, misc)  
            3. Process parsed data through pass_generator_agent  
            4. Coordinate Firebase storage operations  
            5. Generate final wallet passes and insights  
              
            Always ensure data security and accuracy throughout the processing pipeline.  
            """,
            global_instruction="""  
            You are part of a secure financial receipt processing system.   
            Maintain data privacy, ensure accurate extraction, and provide valuable insights to users.  
            All agents should work together seamlessly to deliver a complete receipt processing experience.  
            """,
            tools=[
                self.process_receipt_workflow,
                self.get_system_status,
                self.handle_receipt_upload,
                self.generate_spending_report
            ],
            sub_agents=[
                input_handler_agent.agent,
                self.retail_parser,
                self.food_parser,
                self.misc_parser,
                pass_generator_agent.agent
            ],
            generate_content_config=genai_types.GenerateContentConfig(
                temperature=0.2,  # Low temperature for consistent orchestration
                safety_settings=[
                    genai_types.SafetySetting(
                        category=genai_types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                        threshold=genai_types.HarmBlockThreshold.BLOCK_NONE,
                    ),
                ]
            ),
        )

    async def process_receipt_workflow(
        self,
        image_data: bytes,
        mime_type: str = "image/jpeg",
        input_mode: str = "camera",
        user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Complete receipt processing workflow from input to wallet pass."""

        workflow_id = f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        try:
            # Step 1: Input handling and classification
            logger.info(f"Starting receipt workflow {workflow_id}")

            classification_result = await input_handler_agent.agent.run_async(
                user_message="Classify and process this receipt",
                image_data=image_data,
                mime_type=mime_type,
                input_mode=input_mode,
                user_context=user_context or {}
            )

            if not classification_result or "error" in classification_result:
                return {
                    "workflow_id": workflow_id,
                    "status": "failed",
                    "stage": "classification",
                    "error": "Failed to classify receipt"
                }

            # Step 2: Route to appropriate parser
            category = classification_result.get("category", "miscellaneous")
            parser_agent = self._select_parser_agent(category)

            parsing_result = await parser_agent.run_async(
                user_message=f"Parse this {category} receipt",
                image_data=image_data,
                mime_type=mime_type,
                classification=classification_result
            )

            if not parsing_result or "error" in parsing_result:
                return {
                    "workflow_id": workflow_id,
                    "status": "failed",
                    "stage": "parsing",
                    "error": "Failed to parse receipt data"
                }

            # Step 3: Generate wallet pass
            pass_result = await pass_generator_agent.agent.run_async(
                user_message="Generate wallet pass from parsed receipt",
                receipt_data=parsing_result
            )

            # Step 4: Compile final result
            return {
                "workflow_id": workflow_id,
                "status": "completed",
                "classification": classification_result,
                "parsed_data": parsing_result,
                "wallet_pass": pass_result,
                "processed_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Workflow {workflow_id} failed: {e}")
            return {
                "workflow_id": workflow_id,
                "status": "failed",
                "error": str(e),
                "failed_at": datetime.now().isoformat()
            }

    def _select_parser_agent(self, category: str) -> RemoteA2aAgent:
        """Select appropriate parser agent based on receipt category."""
        parser_mapping = {
            "retail": self.retail_parser,
            "food_dining": self.food_parser,
            "miscellaneous": self.misc_parser
        }
        return parser_mapping.get(category, self.misc_parser)

    async def handle_receipt_upload(
        self,
        file_data: bytes,
        filename: str,
        user_id: str,
        upload_mode: str = "manual"
    ) -> Dict[str, Any]:
        """Handle receipt upload with metadata tracking."""

        upload_metadata = {
            "user_id": user_id,
            "filename": filename,
            "upload_mode": upload_mode,
            "upload_time": datetime.now().isoformat(),
            "file_size": len(file_data)
        }

        # Process through the main workflow
        result = await self.process_receipt_workflow(
            image_data=file_data,
            mime_type="image/jpeg",
            input_mode=upload_mode,
            user_context=upload_metadata
        )

        result["upload_metadata"] = upload_metadata
        return result

    async def get_system_status(self) -> Dict[str, Any]:
        """Get status of all system components."""

        status = {
            "system": "receipt_processor",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "input_handler": "active",
                "retail_parser": "remote_a2a",
                "food_parser": "remote_a2a",
                "misc_parser": "remote_a2a",
                "pass_generator": "active"
            },
            "supported_features": [
                "multi_modal_input",
                "receipt_classification",
                "structured_extraction",
                "wallet_pass_generation",
                "firebase_integration",
                "a2a_communication"
            ]
        }

        return status

    async def generate_spending_report(
        self,
        user_id: str,
        date_range: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Generate spending insights and reports."""

        report = {
            "user_id": user_id,
            "report_period": date_range or {
                "start": datetime.now().replace(day=1).strftime("%Y-%m-%d"),
                "end": datetime.now().strftime("%Y-%m-%d")
            },
            "categories": {
                "food_dining": {"count": 0, "total": 0.0},
                "retail": {"count": 0, "total": 0.0},
                "miscellaneous": {"count": 0, "total": 0.0}
            },
            "insights": [],
            "generated_at": datetime.now().isoformat()
        }

        return report


# Create the main system instance
receipt_processor_system = ReceiptProcessorSystem()

# Export the root agent for ADK
root_agent = receipt_processor_system.agent
