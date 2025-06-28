"""
AI Tools and Function Definitions for D&D Text Adventure Game
Tool definitions for OpenAI function calling to handle game actions.
"""

# Tool definitions for OpenAI function calling
STRATEGY_DECISION_TOOL = {
    "type": "function",
    "function": {
        "name": "decide_action_strategy",
        "description": "Analyze player input and decide whether to use existing actions or create a dynamic action",
        "parameters": {
            "type": "object",
            "properties": {
                "strategy": {
                    "type": "string",
                    "enum": ["existing", "dynamic"],
                    "description": "Whether to use existing actions or create a dynamic action"
                },
                "confidence": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "description": "Confidence level in the decision (0.0 to 1.0)"
                },
                "suggested_action": {
                    "type": "string",
                    "description": "The closest matching existing action (if strategy is 'existing')"
                },
                "reasoning": {
                    "type": "string",
                    "description": "Detailed explanation of the decision"
                },
                "should_create_dynamic": {
                    "type": "boolean",
                    "description": "Whether to create a dynamic action anyway"
                }
            },
            "required": ["strategy", "confidence", "reasoning", "should_create_dynamic"]
        }
    }
}

DYNAMIC_ACTION_TOOL = {
    "type": "function",
    "function": {
        "name": "create_dynamic_action",
        "description": "Create a new dynamic action for the player's request",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "Unique identifier for the action"
                },
                "name": {
                    "type": "string",
                    "description": "Creative name for the action"
                },
                "description": {
                    "type": "string",
                    "description": "Detailed, flavorful description of what this action does"
                },
                "action_type": {
                    "type": "string",
                    "enum": [
                        "magical", "social", "exploration", "crafting", "combat", 
                        "environmental", "character", "economic", "mystical", 
                        "adventure", "creative", "survival", "transportation", 
                        "communication", "stealth"
                    ],
                    "description": "Type of action"
                },
                "parameters": {
                    "type": "object",
                    "description": "Action-specific parameters"
                },
                "targets": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "What/who the action affects"
                },
                "requirements": {
                    "type": "object",
                    "description": "Requirements to perform action (level, items, skills, location)"
                },
                "effects": {
                    "type": "object",
                    "description": "What happens when action is performed"
                },
                "cost": {
                    "type": "object",
                    "description": "Resource costs (mana, health, gold, stamina)"
                },
                "duration": {
                    "type": ["number", "null"],
                    "description": "How long the action takes (in game time)"
                },
                "cooldown": {
                    "type": ["number", "null"],
                    "description": "Cooldown period before action can be used again"
                },
                "success_chance": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "description": "Probability of success (0.0 to 1.0)"
                }
            },
            "required": ["id", "name", "description", "action_type", "parameters", "targets", "requirements", "effects", "cost", "success_chance"]
        }
    }
}

SUGGESTION_TOOL = {
    "type": "function",
    "function": {
        "name": "provide_suggestion",
        "description": "Provide a helpful suggestion or response to the player",
        "parameters": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Helpful message to the player"
                },
                "suggested_action": {
                    "type": "string",
                    "description": "Optional suggested action to try"
                },
                "encourage_dynamic": {
                    "type": "boolean",
                    "description": "Whether to encourage creating a dynamic action"
                }
            },
            "required": ["message"]
        }
    }
}

# List of all available tools
AVAILABLE_TOOLS = [
    STRATEGY_DECISION_TOOL,
    DYNAMIC_ACTION_TOOL,
    SUGGESTION_TOOL
]

# Tool function implementations
def decide_action_strategy(strategy: str, confidence: float, reasoning: str, should_create_dynamic: bool, suggested_action: str = None):
    """
    Implementation of the strategy decision tool.
    This function is called by the AI when it decides on an action strategy.
    """
    return {
        "strategy": strategy,
        "confidence": confidence,
        "suggested_action": suggested_action,
        "reasoning": reasoning,
        "should_create_dynamic": should_create_dynamic
    }

def create_dynamic_action(id: str, name: str, description: str, action_type: str, parameters: dict, targets: list, requirements: dict, effects: dict, cost: dict, success_chance: float, duration: int = None, cooldown: int = None):
    """
    Implementation of the dynamic action creation tool.
    This function is called by the AI when it creates a new dynamic action.
    """
    return {
        "id": id,
        "name": name,
        "description": description,
        "action_type": action_type,
        "parameters": parameters,
        "targets": targets,
        "requirements": requirements,
        "effects": effects,
        "cost": cost,
        "duration": duration,
        "cooldown": cooldown,
        "success_chance": success_chance
    }

def provide_suggestion(message: str, suggested_action: str = None, encourage_dynamic: bool = False):
    """
    Implementation of the suggestion tool.
    This function is called by the AI when it provides suggestions to the player.
    """
    return {
        "message": message,
        "suggested_action": suggested_action,
        "encourage_dynamic": encourage_dynamic
    }

# Tool function mapping
TOOL_FUNCTIONS = {
    "decide_action_strategy": decide_action_strategy,
    "create_dynamic_action": create_dynamic_action,
    "provide_suggestion": provide_suggestion
} 