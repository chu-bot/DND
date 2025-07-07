import os
import json
from typing import List, Dict, Any, Optional, Tuple
from difflib import get_close_matches
from openai import OpenAI
from ai_prompts import (
    get_strategy_decision_message, 
    get_suggestion_message,
    get_permission_check_message,
    get_data_action_message,
    get_primitive_selection_message
)
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

    def check_player_permission(self, user_input: str, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if a player should be allowed to perform the requested action.
        
        Returns a dictionary with:
        - allowed: boolean indicating if the action is permitted
        - reasoning: explanation of the decision
        - restricted_effects: list of any restricted effects
        """
        

        # automated sanitation based on past commands judged to be "invalid"
        cleaned = user_input.strip().lower()
        # Load invalid inputs from file
        invalid_path = os.path.join(os.path.dirname(__file__), "invalid_inputs.txt")
        try:
            with open(invalid_path, "r") as f:
                invalid_inputs = set(line.strip().lower() for line in f if line.strip())
        except Exception:
            invalid_inputs = set()
        # Reject if input is in invalid_inputs
        if cleaned in invalid_inputs:
            return {
                "allowed": False,
                "reasoning": "Input is not a valid or comprehensible action. Please enter a meaningful command.",
                "restricted_effects": []
            }
        # No API Key Given
        if not self.client:
            return {
                "allowed": True,
                "reasoning": "No API key available, defaulting to allowed",
                "restricted_effects": []
            }
        
        # 
        try:
            message = get_permission_check_message(user_input, game_state)
            
            response = self.client.chat.completions.create(
                model="gpt-4.1-nano",
                messages=[
                    {"role": "system", "content": message},
                    {"role": "user", "content": f"Check permission for: {user_input}"}
                ],
                tools=[tool for tool in AVAILABLE_TOOLS if tool["function"]["name"] == "check_player_permission"],
                tool_choice={"type": "function", "function": {"name": "check_player_permission"}},
                temperature=0.3
            )
            
            # Extract tool call response
            tool_call = response.choices[0].message.tool_calls[0]
            permission_data = json.loads(tool_call.function.arguments)
            
            allowed = bool(permission_data.get("allowed", True))
            reasoning = permission_data.get("reasoning", "No reasoning provided")
            # If OpenAI returns a non-specific denial, add to invalid_inputs.txt
            if not allowed and ("not a valid" in reasoning or "not comprehensible" in reasoning or "unclear" in reasoning or "meaningful" in reasoning):
                try:
                    with open(invalid_path, "a") as f:
                        f.write(f"{cleaned}\n")
                except Exception:
                    pass
            return {
                "allowed": allowed,
                "reasoning": reasoning,
                "restricted_effects": permission_data.get("restricted_effects", [])
            }
                
        except Exception as e:
            print(f"Error in permission check: {e}")
            # Fallback - allow by default if there's an error
            return {
                "allowed": True,
                "reasoning": f"Error occurred during permission check: {e}",
                "restricted_effects": []
            }

    def determine_data_action(self, user_input: str, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determine if an action should create new data or modify existing data.
        Returns a dictionary with:
        - action_type: "create_new" or "modify_existing" or "immediate"
        - data_type: which type of data to create/modify (location, quest, item, etc.)
        - reasoning: explanation of the decision
        - confidence: confidence level in the decision
        """
        if not self.client:
            return {
                "action_type": "immediate",
                "data_type": "none",
                "reasoning": "No API key available, defaulting to immediate action",
                "confidence": 0.5
            }
        
        try:
            # Create the data action determination message
            message = get_data_action_message(user_input, game_state)
            
            # Call OpenAI with tool calling
            response = self.client.chat.completions.create(
                model="gpt-4.1-nano",
                messages=[
                    {"role": "system", "content": message},
                    {"role": "user", "content": f"Analyze this action: {user_input}"}
                ],
                tools=[tool for tool in AVAILABLE_TOOLS if tool["function"]["name"] == "determine_data_action"],
                tool_choice={"type": "function", "function": {"name": "determine_data_action"}},
                temperature=0.3
            )
            
            # Extract tool call response
            tool_call = response.choices[0].message.tool_calls[0]
            data_action = json.loads(tool_call.function.arguments)
            
            return {
                "action_type": data_action.get("action_type", "immediate"),
                "data_type": data_action.get("data_type", "none"),
                "reasoning": data_action.get("reasoning", "No reasoning provided"),
                "confidence": float(data_action.get("confidence", 0.5))
            }
                
        except Exception as e:
            print(f"Error in data action determination: {e}")
            return {
                "action_type": "immediate",
                "data_type": "none",
                "reasoning": f"Error occurred during analysis: {e}",
                "confidence": 0.3
            }

    def select_action_primitive(self, user_input: str, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decide whether to use specific game primitives or fall back to general Action.
        
        Returns a dictionary with:
        - use_specific_primitive: boolean indicating if a specific primitive should be used
        - primitive_type: which primitive to use (location, item, quest, blueprint, none)
        - reasoning: explanation of the decision
        - confidence: confidence level in the decision
        """
        if not self.client:
            return {
                "use_specific_primitive": False,
                "primitive_type": "none",
                "reasoning": "No API key available, defaulting to general Action",
                "confidence": 0.5
            }
        
        try:
            # Create the primitive selection message
            message = get_primitive_selection_message(user_input, game_state)
            
            # Call OpenAI with tool calling
            response = self.client.chat.completions.create(
                model="gpt-4.1-nano",
                messages=[
                    {"role": "system", "content": message},
                    {"role": "user", "content": f"Select primitive for: {user_input}"}
                ],
                tools=[tool for tool in AVAILABLE_TOOLS if tool["function"]["name"] == "select_action_primitive"],
                tool_choice={"type": "function", "function": {"name": "select_action_primitive"}},
                temperature=0.3
            )
            
            # Extract tool call response
            tool_call = response.choices[0].message.tool_calls[0]
            primitive_data = json.loads(tool_call.function.arguments)
            
            return {
                "use_specific_primitive": bool(primitive_data.get("use_specific_primitive", False)),
                "primitive_type": primitive_data.get("primitive_type", "none"),
                "reasoning": primitive_data.get("reasoning", "No reasoning provided"),
                "confidence": float(primitive_data.get("confidence", 0.5))
            }
                
        except Exception as e:
            print(f"Error in primitive selection: {e}")
            # Fallback - use general Action if there's an error
            return {
                "use_specific_primitive": False,
                "primitive_type": "none",
                "reasoning": f"Error occurred during primitive selection: {e}",
                "confidence": 0.3
            }

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