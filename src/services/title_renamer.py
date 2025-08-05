from agents import Runner

from src.services.chat_service import ChatService
from src.core.agent_factory import get_agent_by_key
from src.core.agent_key import AgentKey
from src.logging_config import get_logger

logger = get_logger(__name__)


class ChatTitleRenamer:
    """Service for generating and updating chat titles using AI agents"""

    @staticmethod
    async def generate_title_in_background_and_update(session_id: str, user_id: str):
        """
        Background task function to generate and update conversation title.
        Completely self-contained with only serializable parameters.
        """
        try:
            # Create fresh instances for the background task
            chat_service_bg = ChatService()

            # Get the first 2-3 messages from the conversation
            conversation_result = await chat_service_bg.get_conversation(
                session_id=session_id, user_id=user_id, limit=3, offset=0
            )

            # Check if conversation exists and has messages
            if not conversation_result.messages:
                logger.warning(f"No messages found for conversation {session_id}")
                return

            # Only rename if still has default title
            current_title = conversation_result.conversation.title
            if current_title not in ["New Chat", "New Conversation"]:
                logger.info(
                    f"Conversation {session_id} already has custom title: {current_title}"
                )
                return

            # Extract first few messages for context
            message_texts = []
            for msg in conversation_result.messages[:3]:
                # Assuming message_data is a string or JSON with content
                message_texts.append(str(msg.message_data))

            conversation_context = "\n".join(message_texts)

            # Create prompt for title generation
            title_prompt = f"""Based on the following conversation messages, generate a concise, meaningful title (maximum 6 words):

{conversation_context}

Generate only the title, nothing else."""

            # Get the title renamer agent and generate title
            title_agent = await get_agent_by_key(AgentKey.CHAT_TITLE_RENAMER)
            result = await Runner.run(
                starting_agent=title_agent,
                input=title_prompt,
                context=None,
                session=None,
                max_turns=3,
            )

            # Extract and clean the generated title
            new_title = result.final_output.strip()

            # Remove quotes if present
            if new_title.startswith('"') and new_title.endswith('"'):
                new_title = new_title[1:-1]
            if new_title.startswith("'") and new_title.endswith("'"):
                new_title = new_title[1:-1]

            # Limit title length
            if len(new_title) > 50:
                new_title = new_title[:47] + "..."

            if new_title:
                logger.info(
                    f"Successfully generated title '{new_title}' for conversation {session_id}"
                )
                # Update the conversation title in the database
                await chat_service_bg.update_conversation_title(
                    session_id, user_id, new_title
                )
            else:
                logger.warning(f"No title generated for conversation {session_id}")

        except Exception as e:
            logger.error(
                f"Failed to generate title for {session_id}: {str(e)}", exc_info=True
            )
