"""
Receipt Management Root Agent

This module defines the root agent for the receipt management system.
It uses a sequential flow: first input handler/classifier, then parallel parsers.
"""

from google.adk.agents import ParallelAgent, SequentialAgent

from .subagents.input_handler_agent import input_handler_agent
from .subagents.retail_parser_agent import retail_parser_agent
from .subagents.food_parser_agent import food_parser_agent
from .subagents.misc_parser_agent import misc_parser_agent
from .subagents.result_synthesizer_agent import result_synthesizer_agent

# --- 1. Create Parallel Agent for receipt parsing based on classification ---
receipt_parser_agents = ParallelAgent(
    name="receipt_parser_agents",
    sub_agents=[retail_parser_agent, food_parser_agent, misc_parser_agent],
)

# --- 2. Create Sequential Pipeline: Input Handler -> Parallel Parsers -> Synthesizer ---
root_agent = SequentialAgent(
    name="receipt_management_agent",
    sub_agents=[input_handler_agent, receipt_parser_agents, result_synthesizer_agent],
) 