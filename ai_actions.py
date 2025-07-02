import os
import json
import uuid
from typing import List, Dict, Any, Optional, Tuple
from difflib import get_close_matches
from openai import OpenAI
from game_types import Action
from ai_prompts import get_strategy_decision_message, get_dynamic_action_message, get_suggestion_message
from ai_tools import AVAILABLE_TOOLS


class AIActionHandler:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = None
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
        self.available_actions = []
        
    def set_available_actions(self, actions: List[str]):
        """Set the list of available actions for autocorrect and suggestions"""
        self.available_actions = actions

    def decide_action_strategy(self, user_input: str, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze user input and decide whether to use existing actions or create a dynamic action.
        
        Returns a dictionary with:
        - strategy: "existing" or "dynamic"
        - confidence: float (0.0 to 1.0) indicating confidence in the decision
        - suggested_action: the closest existing action (if strategy is "existing")
        - reasoning: explanation of the decision
        - should_create_dynamic: boolean indicating if we should create a dynamic action anyway
        """
        if not self.client:
            return {
                "strategy": "dynamic",
                "confidence": 0.5,
                "suggested_action": None,
                "reasoning": "No API key available, defaulting to dynamic action creation",
                "should_create_dynamic": True
            }
        
        try:
            # Prepare context for AI analysis
            context = {
                "user_input": user_input,
                "available_actions": self.available_actions,
                "current_location": game_state.get("player_location", "unknown"),
                "player_health": game_state.get("player_health", 100),
                "player_mana": game_state.get("player_mana", 50),
                "player_gold": game_state.get("player_gold", 100),
                "player_level": game_state.get("player_level", 1),
                "active_quests": game_state.get("active_quests", []),
                "inventory": game_state.get("inventory", [])
            }
            
            # Create the message with context
            message = get_strategy_decision_message(context)
            
            # Call OpenAI with tool calling
            response = self.client.chat.completions.create(
                model="gpt-4.1-nano",
                messages=[
                    {"role": "system", "content": message},
                    {"role": "user", "content": f"Analyze this player input: {user_input}"}
                ],
                tools=[tool for tool in AVAILABLE_TOOLS if tool["function"]["name"] == "decide_action_strategy"],
                tool_choice={"type": "function", "function": {"name": "decide_action_strategy"}},
                temperature=0.3
            )
            
            # Extract tool call response
            tool_call = response.choices[0].message.tool_calls[0]
            function_args = json.loads(tool_call.function.arguments)
            
            # Return the strategy decision
            return {
                "strategy": function_args.get("strategy", "dynamic"),
                "confidence": float(function_args.get("confidence", 0.5)),
                "suggested_action": function_args.get("suggested_action"),
                "reasoning": function_args.get("reasoning", "No reasoning provided"),
                "should_create_dynamic": bool(function_args.get("should_create_dynamic", True))
            }
                
        except Exception as e:
            print(f"Error in action strategy decision: {e}")
            # Fallback decision
            return {
                "strategy": "dynamic",
                "confidence": 0.3,
                "suggested_action": None,
                "reasoning": f"Error occurred during analysis: {e}",
                "should_create_dynamic": True
            }

    def create_dynamic_action(self, user_input: str, game_state: Dict[str, Any]) -> Optional[Action]:
        """ 
        Use AI to create a dynamic action based on user input.
        Returns an Action object or None.
        """
        if not self.client:
            return None
            
        try:
            # Create the message with context
            message = get_dynamic_action_message(user_input, game_state)
            
            # Call OpenAI with tool calling
            response = self.client.chat.completions.create(
                model="gpt-4.1-nano",
                messages=[
                    {"role": "system", "content": message},
                    {"role": "user", "content": f"Create a dynamic action for: {user_input}"}
                ],
                tools=[tool for tool in AVAILABLE_TOOLS if tool["function"]["name"] == "create_dynamic_action"],
                tool_choice={"type": "function", "function": {"name": "create_dynamic_action"}},
                temperature=0.9
            )
            
            # Extract tool call response
            tool_call = response.choices[0].message.tool_calls[0]
            action_data = json.loads(tool_call.function.arguments)
            
            # Create Action object
            action = Action(
                id=action_data.get("id", f"ai_action_{uuid.uuid4().hex[:8]}"),
                name=action_data.get("name", "AI Generated Action"),
                description=action_data.get("description", "An AI-generated action"),
                action_type=action_data.get("action_type", "utility"),
                parameters=action_data.get("parameters", {}),
                targets=action_data.get("targets", []),
                requirements=action_data.get("requirements", {}),
                effects=action_data.get("effects", {}),
                cost=action_data.get("cost", {}),
                duration=action_data.get("duration"),
                cooldown=action_data.get("cooldown"),
                success_chance=action_data.get("success_chance", 1.0),
                ai_generated=True
            )
            
            return action
                
        except Exception as e:
            print(f"Error creating dynamic action: {e}")
            return None
    
    def suggest_ai_action(self, user_input: str, game_state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Use AI to suggest actions when user input doesn't match available commands.
        Returns a suggestion to create a dynamic action.
        """
        if not self.client:
            return None
            
        try:
            # Prepare context for AI
            context = {
                "available_actions": self.available_actions,
                "current_location": game_state.get("player_location", "unknown"),
                "player_health": game_state.get("player_health", 100),
                "player_mana": game_state.get("player_mana", 50),
                "player_gold": game_state.get("player_gold", 100),
                "active_quests": game_state.get("active_quests", []),
                "inventory": game_state.get("inventory", [])
            }
            
            # Create the message with context
            message = get_suggestion_message(user_input, context)
            
            # Call OpenAI with tool calling
            response = self.client.chat.completions.create(
                model="gpt-4.1-nano",
                messages=[
                    {"role": "system", "content": message},
                    {"role": "user", "content": f"Player said: {user_input}"}
                ],
                tools=[tool for tool in AVAILABLE_TOOLS if tool["function"]["name"] == "provide_suggestion"],
                tool_choice={"type": "function", "function": {"name": "provide_suggestion"}},
                temperature=0.8
            )
            
            # Extract tool call response
            tool_call = response.choices[0].message.tool_calls[0]
            suggestion_data = json.loads(tool_call.function.arguments)
            
            # Return a simple response encouraging dynamic action creation
            return {
                "type": "response",
                "message": suggestion_data.get("message", "I can help you with that!"),
                "suggested_action": suggestion_data.get("suggested_action"),
                "encourage_dynamic": suggestion_data.get("encourage_dynamic", True)
            }
                
        except Exception as e:
            print(f"AI suggestion error: {e}")
            return None
    
    def find_closest_existing_action(self, user_input: str) -> Tuple[str, float]:
        """
        Find the closest matching existing action using fuzzy matching.
        Returns (action_name, similarity_score).
        """
        if not self.available_actions:
            return None, 0.0
        
        # Clean and normalize user input
        clean_input = user_input.lower().strip()
        
        # Try exact matches first
        for action in self.available_actions:
            if clean_input == action.lower():
                return action, 1.0
        
        # Try partial matches
        for action in self.available_actions:
            if action.lower() in clean_input or clean_input in action.lower():
                return action, 0.8
        
        # Use difflib for fuzzy matching
        matches = get_close_matches(clean_input, [a.lower() for a in self.available_actions], n=1, cutoff=0.6)
        if matches:
            matched_action = matches[0]
            # Find the original action name
            for action in self.available_actions:
                if action.lower() == matched_action:
                    return action, 0.6
        
        return None, 0.0


# Global instance
ai_handler = AIActionHandler() 