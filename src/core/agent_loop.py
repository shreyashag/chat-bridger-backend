import json
from typing import AsyncGenerator, List, Optional

from agents import Agent, Runner

from src.api.models.requests import ClientToolDefinition, ClientToolResult
from src.core.client_tools import convert_client_tools_to_function_tools
from src.core.event_handlers import EventProcessor
from src.logging_config import get_logger
from src.services.conversation_context_manager import ConversationContextManager

logger = get_logger(__name__)


class AgentLoop:
    @staticmethod
    async def run_agent_stream(
        agent: Agent,
        event_processor: EventProcessor,
        conversation_manager: ConversationContextManager,
        message: str,
        client_tools: Optional[List[ClientToolDefinition]] = None,
    ) -> AsyncGenerator[str, None]:
        """Single method to handle both initial and continuation execution."""

        # Add client tools if provided and configure to stop at client tools
        agent_with_tools = agent.clone()
        client_tool_names = set()
        if client_tools:
            from agents.agent import StopAtTools

            client_function_tools = convert_client_tools_to_function_tools(client_tools)
            agent_with_tools.tools = (
                list(agent_with_tools.tools or []) + client_function_tools
            )
            client_tool_names = {tool.name for tool in client_tools}

            # Configure agent to stop at client tools
            agent_with_tools.tool_use_behavior = StopAtTools(
                stop_at_tool_names=list(client_tool_names)
            )

            logger.info(
                f"Added {len(client_function_tools)} client tools to agent with stop behavior"
            )

        # Use SDK's native streaming
        async for event in Runner.run_streamed(
            agent_with_tools,
            input=message,
            session=conversation_manager.session,
            context=await conversation_manager.get_message_with_context(message),
            max_turns=5,
        ).stream_events():
            print(event)

            # Process and yield events - SDK will automatically stop at client tools
            processed_event = await event_processor.process_event(event)
            if processed_event:
                yield f"{json.dumps(processed_event)}\n"

    @staticmethod
    async def continue_after_client_tools(
        agent: Agent,
        event_processor: EventProcessor,
        conversation_manager: ConversationContextManager,
        tool_results: List[ClientToolResult],
        client_tools: Optional[List[ClientToolDefinition]] = None,
    ) -> AsyncGenerator[str, None]:
        """Continue execution after client tool results."""

        if not conversation_manager.session:
            raise ValueError("Session required for continuation")

        # Get the current conversation history
        session_items = await conversation_manager.session.get_items()
        logger.info(f"Retrieved {len(session_items)} items from session")
        for tool_result in tool_results:
            logger.info(tool_result)
        # Find and replace the pending tool results
        updated_items = []
        for item in session_items:
            # Convert session item to dict if needed
            if isinstance(item, str):
                item_dict = json.loads(item)
            else:
                item_dict = item

            # Check if this is a tool result with PENDING_CLIENT_EXECUTION
            if (
                item_dict.get("role") == "tool"
                and isinstance(item_dict.get("content"), str)
                and "PENDING_CLIENT_EXECUTION" in item_dict.get("content", "")
            ):
                # Replace with actual tool result
                for tool_result in tool_results:
                    if item_dict.get("tool_call_id") == tool_result.tool_call_id:
                        updated_items.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_result.tool_call_id,
                                "content": tool_result.result
                                or f"Tool {tool_result.tool_name} executed successfully",
                            }
                        )
                        logger.info(
                            f"Replaced pending result for tool {tool_result.tool_name}"
                        )
                        break
            else:
                updated_items.append(item_dict)

        # Update session with the tool results BEFORE continuing
        await conversation_manager.session.clear_session()
        await conversation_manager.session.add_items(updated_items)
        logger.info(
            f"Updated session with {len(updated_items)} items including actual tool results"
        )

        # Now continue with the agent using the session (like in run_agent_stream)
        continue_agent = agent.clone()

        # Use SDK's native streaming with session - this will automatically persist all messages
        async for event in Runner.run_streamed(
            continue_agent,
            input="",  # Empty input since we're continuing from session
            session=conversation_manager.session,  # Pass session for automatic persistence
            max_turns=5,
        ).stream_events():
            print(event)

            # Process and yield events - SDK will automatically handle persistence
            processed_event = await event_processor.process_event(event)
            if processed_event:
                yield f"{json.dumps(processed_event)}\n"

    @staticmethod
    def _create_client_tool_event(tool_call) -> str:
        """Create client tool execution event from tool call."""
        client_tool_event = {
            "type": "client_tool_execution_required",
            "data": {
                "tool_name": tool_call.function.name,
                "parameters": json.loads(tool_call.function.arguments)
                if tool_call.function.arguments
                else {},
                "tool_call_id": tool_call.id,
                "session_id": None,  # Will be filled by event processor
                "message": f"Client must execute '{tool_call.function.name}' and provide the result to continue the conversation.",
            },
        }
        return f"{json.dumps(client_tool_event)}\n"
