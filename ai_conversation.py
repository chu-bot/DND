"""
AI Conversation Handler for D&D Text Adventure Game
Manages hybrid conversation system with pre-set and dynamic conversations.
"""

import os
import json
from typing import Dict, Any
from datetime import datetime
from openai import OpenAI
from game_types import NPC, ConversationNode, DynamicExchange, ConversationState
from ai_prompts import get_conversation_analysis_message, get_dynamic_response_message


class AIConversationHandler:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = None
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
        
    def analyze_conversation_input(self, player_input: str, npc: NPC, conversation_state: ConversationState) -> Dict[str, Any]:
        """
        Analyze player input and decide how to handle the conversation.
        
        Returns:
        - strategy: "preset" (use pre-set conversation), "dynamic" (generate new response), or "redirect" (redirect to preset)
        - similarity_score: float (0.0 to 1.0) indicating similarity to pre-set topics
        - preset_topic: the matching pre-set topic (if strategy is "preset" or "redirect")
        - is_essential: boolean indicating if this topic is story-relevant
        - reasoning: explanation of the decision
        """
        if not self.client:
            return {
                "strategy": "dynamic",
                "similarity_score": 0.0,
                "preset_topic": None,
                "is_essential": False,
                "reasoning": "No API key available, defaulting to dynamic response",
                "npc_response": "I'm not sure how to respond to that right now."
            }
        
        try:
            # Prepare context for AI analysis
            context = {
                "player_input": player_input,
                "npc_name": npc.name,
                "npc_personality": npc.personality,
                "npc_bio": npc.bio,
                "npc_temperament": npc.temperament,
                "preset_topics": list(npc.dialogue_tree.get("topics", [])),
                "preset_responses": npc.dialogue_tree.get("responses", {}),
                "conversation_history": [ex.player_input for ex in conversation_state.conversation_history[-5:]],  # Last 5 exchanges
                "essential_topics_created": conversation_state.essential_topics_created,
                "relationship_level": conversation_state.relationship_level,
                "questions_remaining": conversation_state.max_questions_remaining
            }
            
            # Create the message with context
            message = get_conversation_analysis_message(context)
            
            # Call OpenAI with tool calling
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": message},
                    {"role": "user", "content": f"Player asks: {player_input}"}
                ],
                tools=[tool for tool in AVAILABLE_CONVERSATION_TOOLS if tool["function"]["name"] == "analyze_conversation"],
                tool_choice={"type": "function", "function": {"name": "analyze_conversation"}},
                temperature=0.7
            )
            
            # Extract tool call response
            tool_call = response.choices[0].message.tool_calls[0]
            analysis_data = json.loads(tool_call.function.arguments)
            
            return {
                "strategy": analysis_data.get("strategy", "dynamic"),
                "similarity_score": float(analysis_data.get("similarity_score", 0.0)),
                "preset_topic": analysis_data.get("preset_topic"),
                "is_essential": bool(analysis_data.get("is_essential", False)),
                "reasoning": analysis_data.get("reasoning", "No reasoning provided"),
                "npc_response": analysis_data.get("npc_response", "I'm not sure how to respond to that.")
            }
                
        except Exception as e:
            print(f"Error in conversation analysis: {e}")
            return {
                "strategy": "dynamic",
                "similarity_score": 0.0,
                "preset_topic": None,
                "is_essential": False,
                "reasoning": f"Error occurred during analysis: {e}",
                "npc_response": "I'm having trouble understanding. Could you rephrase that?"
            }
    
    def generate_dynamic_response(self, player_input: str, npc: NPC, conversation_state: ConversationState, is_essential: bool = False) -> str:
        """
        Generate a dynamic response based on NPC personality and bio.
        """
        if not self.client:
            return "I'm not sure how to respond to that right now."
        
        try:
            # Prepare context for response generation
            context = {
                "player_input": player_input,
                "npc_name": npc.name,
                "npc_personality": npc.personality,
                "npc_bio": npc.bio,
                "npc_temperament": npc.temperament,
                "conversation_history": [ex.player_input for ex in conversation_state.conversation_history[-3:]],  # Last 3 exchanges
                "relationship_level": conversation_state.relationship_level,
                "is_essential": is_essential,
                "questions_remaining": conversation_state.max_questions_remaining
            }
            
            # Create the message with context
            message = get_dynamic_response_message(context)
            
            # Call OpenAI with high temperature for creative responses
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": message},
                    {"role": "user", "content": f"Player asks: {player_input}"}
                ],
                temperature=0.9,  # High temperature for creative responses
                max_tokens=200
            )
            
            return response.choices[0].message.content.strip()
                
        except Exception as e:
            print(f"Error generating dynamic response: {e}")
            return "I'm having trouble thinking of a response right now."
    
    def create_conversation_node(self, topic: str, content: str, is_essential: bool, npc: NPC) -> ConversationNode:
        """
        Create a new conversation node for an essential topic.
        """
        return ConversationNode(
            topic=topic,
            content=content,
            is_essential=is_essential,
            created_dynamically=True
        )
    
    def update_conversation_state(self, conversation_state: ConversationState, player_input: str, npc_response: str, 
                                similarity_score: float, is_essential: bool) -> ConversationState:
        """
        Update the conversation state with the new exchange.
        """
        # Create new exchange
        exchange = DynamicExchange(
            player_input=player_input,
            npc_response=npc_response,
            similarity_score=similarity_score,
            is_essential=is_essential
        )
        
        # Add to history
        conversation_state.conversation_history.append(exchange)
        
        # Update relationship based on interaction
        if is_essential:
            conversation_state.relationship_level += 1
            conversation_state.essential_topics_created.append(player_input)
        
        # Decrease questions remaining
        conversation_state.max_questions_remaining = max(0, conversation_state.max_questions_remaining - 1)
        
        # Update last interaction
        conversation_state.last_interaction = datetime.now().isoformat()
        
        return conversation_state


# Tool definitions for conversation analysis
CONVERSATION_ANALYSIS_TOOL = {
    "type": "function",
    "function": {
        "name": "analyze_conversation",
        "description": "Analyze player input and decide conversation strategy",
        "parameters": {
            "type": "object",
            "properties": {
                "strategy": {
                    "type": "string",
                    "enum": ["preset", "dynamic", "redirect"],
                    "description": "How to handle the conversation"
                },
                "similarity_score": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "description": "Similarity to pre-set topics (0.0 to 1.0)"
                },
                "preset_topic": {
                    "type": "string",
                    "description": "The matching pre-set topic (if applicable)"
                },
                "is_essential": {
                    "type": "boolean",
                    "description": "Whether this topic is story-relevant"
                },
                "reasoning": {
                    "type": "string",
                    "description": "Explanation of the decision"
                },
                "npc_response": {
                    "type": "string",
                    "description": "The NPC's response to the player"
                }
            },
            "required": ["strategy", "similarity_score", "is_essential", "reasoning", "npc_response"]
        }
    }
}

AVAILABLE_CONVERSATION_TOOLS = [CONVERSATION_ANALYSIS_TOOL] 