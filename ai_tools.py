"""
AI Tools and Function Definitions for D&D Text Adventure Game
Tool definitions for OpenAI function calling to handle game actions.
"""

# Tool definitions for OpenAI function calling
PERMISSION_CHECK_TOOL = {
    "type": "function",
    "function": {
        "name": "check_player_permission",
        "description": "Check if a player should be allowed to perform the requested action",
        "parameters": {
            "type": "object",
            "properties": {
                "allowed": {
                    "type": "boolean",
                    "description": "Whether the player should be allowed to do this"
                },
                "reasoning": {
                    "type": "string",
                    "description": "Explanation of why this is or isn't allowed"
                },
                "restricted_effects": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of any restricted effects this action would have"
                }
            },
            "required": ["allowed", "reasoning"]
        }
    }
}

PRIMITIVE_SELECTION_TOOL = {
    "type": "function",
    "function": {
        "name": "select_action_primitive",
        "description": "Decide whether to use specific game primitives or fall back to general Action",
        "parameters": {
            "type": "object",
            "properties": {
                "use_specific_primitive": {
                    "type": "boolean",
                    "description": "Whether to use a specific primitive (location, item, quest, blueprint)"
                },
                "primitive_type": {
                    "type": "string",
                    "enum": ["location", "item", "quest", "blueprint", "none"],
                    "description": "Which specific primitive to use, or 'none' for general Action"
                },
                "reasoning": {
                    "type": "string",
                    "description": "Explanation of the primitive selection decision"
                },
                "confidence": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "description": "Confidence in the primitive selection (0.0 to 1.0)"
                }
            },
            "required": ["use_specific_primitive", "primitive_type", "reasoning", "confidence"]
        }
    }
}

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
                    "description": "Resource costs (mana, health, gold)"
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

DATA_ACTION_TOOL = {
    "type": "function",
    "function": {
        "name": "determine_data_action",
        "description": "Determine if an action should create new data, modify existing data, or execute immediately",
        "parameters": {
            "type": "object",
            "properties": {
                "action_type": {
                    "type": "string",
                    "enum": ["create_new", "modify_existing", "immediate"],
                    "description": "Type of action to perform"
                },
                "data_type": {
                    "type": "string",
                    "enum": ["location", "quest", "item", "npc", "blueprint", "none"],
                    "description": "Type of data to create or modify"
                },
                "reasoning": {
                    "type": "string",
                    "description": "Explanation of the decision"
                },
                "confidence": {
                    "type": "number",
                    "description": "Confidence level in the decision (0.0-1.0)"
                }
            },
            "required": ["action_type", "data_type", "reasoning", "confidence"]
        }
    }
}

# Data creation tools
CREATE_LOCATION_TOOL = {
    "type": "function",
    "function": {
        "name": "create_location",
        "description": "Create a new location for the game world",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {"type": "string", "description": "Unique identifier for the location"},
                "name": {"type": "string", "description": "Name of the location"},
                "description": {"type": "string", "description": "Description of the location"},
                "scene": {"type": "string", "description": "Scene-setting text for the location"},
                "npcs": {"type": "array", "items": {"type": "string"}, "description": "List of NPC IDs in this location"},
                "sub_locations": {"type": "array", "items": {"type": "string"}, "description": "Connected sub-locations"},
                "shop_items": {"type": "array", "items": {"type": "string"}, "description": "Items available for purchase"},
                "requirements": {"type": "object", "description": "Requirements to access this location"}
            },
            "required": ["id", "name", "description"]
        }
    }
}

CREATE_QUEST_TOOL = {
    "type": "function",
    "function": {
        "name": "create_quest",
        "description": "Create a new quest for the player",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {"type": "string", "description": "Unique identifier for the quest"},
                "name": {"type": "string", "description": "Name of the quest"},
                "description": {"type": "string", "description": "Description of the quest"},
                "objectives": {"type": "array", "items": {"type": "string"}, "description": "Quest objectives"},
                "location": {"type": "string", "description": "Location where quest is available"},
                "requirements": {"type": "object", "description": "Requirements to start the quest"},
                "rewards": {"type": "object", "description": "Quest rewards"},
                "difficulty": {"type": "string", "enum": ["easy", "medium", "hard"], "description": "Quest difficulty"}
            },
            "required": ["id", "name", "description", "objectives", "rewards"]
        }
    }
}

CREATE_ITEM_TOOL = {
    "type": "function",
    "function": {
        "name": "create_item",
        "description": "Create a new item for the game world",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {"type": "string", "description": "Unique identifier for the item"},
                "name": {"type": "string", "description": "Name of the item"},
                "description": {"type": "string", "description": "Description of the item"},
                "type": {"type": "string", "enum": ["weapon", "armor", "potion", "scroll", "tool", "treasure"], "description": "Type of item"},
                "value": {"type": "number", "description": "Gold value of the item"},
                "effects": {"type": "object", "description": "Effects when used"},
                "requirements": {"type": "object", "description": "Requirements to use the item"}
            },
            "required": ["id", "name", "description", "type", "value"]
        }
    }
}

CREATE_NPC_TOOL = {
    "type": "function",
    "function": {
        "name": "create_npc",
        "description": "Create a new NPC for the game world",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {"type": "string", "description": "Unique identifier for the NPC"},
                "name": {"type": "string", "description": "Name of the NPC"},
                "description": {"type": "string", "description": "Description of the NPC"},
                "personality": {"type": "string", "description": "NPC personality"},
                "bio": {"type": "string", "description": "NPC background story"},
                "temperament": {"type": "string", "enum": ["friendly", "neutral", "hostile"], "description": "NPC temperament"},
                "location": {"type": "string", "description": "Location where NPC is found"},
                "preset_topics": {"type": "array", "items": {"type": "string"}, "description": "Topics NPC can discuss"},
                "preset_responses": {"type": "object", "description": "Responses to preset topics"}
            },
            "required": ["id", "name", "description", "personality", "temperament"]
        }
    }
}

CREATE_BLUEPRINT_TOOL = {
    "type": "function",
    "function": {
        "name": "create_blueprint",
        "description": "Create a new crafting blueprint",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {"type": "string", "description": "Unique identifier for the blueprint"},
                "name": {"type": "string", "description": "Name of the blueprint"},
                "description": {"type": "string", "description": "Description of the blueprint"},
                "result_item": {"type": "string", "description": "Item created by this blueprint"},
                "materials": {"type": "object", "description": "Required materials and quantities"},
                "difficulty": {"type": "string", "enum": ["easy", "medium", "hard"], "description": "Crafting difficulty"},
                "skill_required": {"type": "string", "description": "Skill required to craft"}
            },
            "required": ["id", "name", "description", "result_item", "materials"]
        }
    }
}

EXECUTE_IMMEDIATE_ACTION_TOOL = {
    "type": "function",
    "function": {
        "name": "execute_immediate_action",
        "description": "Execute an immediate action without creating or modifying data",
        "parameters": {
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "Flavorful description of what happens"},
                "effects": {
                    "type": "object",
                    "properties": {
                        "health_change": {"type": "number", "description": "Change in player health"},
                        "mana_change": {"type": "number", "description": "Change in player mana"},
                        "gold_change": {"type": "number", "description": "Change in player gold"},
                        "experience_change": {"type": "number", "description": "Change in player experience"}
                    },
                    "description": "Immediate effects on the player"
                }
            },
            "required": ["message"]
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

# Data modification tools
MODIFY_LOCATION_TOOL = {
    "type": "function",
    "function": {
        "name": "modify_location",
        "description": "Modify existing location data",
        "parameters": {
            "type": "object",
            "properties": {
                "target_id": {"type": "string", "description": "ID of the location to modify"},
                "modifications": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Location name"},
                        "description": {"type": "string", "description": "Location description"},
                        "scene": {"type": "string", "description": "Scene-setting text"},
                        "npcs": {"type": "array", "items": {"type": "string"}, "description": "List of NPC IDs"},
                        "sub_locations": {"type": "array", "items": {"type": "string"}, "description": "Connected sub-locations"},
                        "shop_items": {"type": "array", "items": {"type": "string"}, "description": "Items available for purchase"},
                        "requirements": {"type": "object", "description": "Requirements to access location"}
                    },
                    "description": "Fields to modify"
                },
                "reasoning": {"type": "string", "description": "Why these modifications were chosen"}
            },
            "required": ["target_id", "modifications"]
        }
    }
}

MODIFY_QUEST_TOOL = {
    "type": "function",
    "function": {
        "name": "modify_quest",
        "description": "Modify existing quest data",
        "parameters": {
            "type": "object",
            "properties": {
                "target_id": {"type": "string", "description": "ID of the quest to modify"},
                "modifications": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Quest name"},
                        "description": {"type": "string", "description": "Quest description"},
                        "objectives": {"type": "array", "items": {"type": "string"}, "description": "Quest objectives"},
                        "location": {"type": "string", "description": "Quest location"},
                        "requirements": {"type": "object", "description": "Requirements to start quest"},
                        "rewards": {"type": "object", "description": "Quest rewards"},
                        "difficulty": {"type": "string", "enum": ["easy", "medium", "hard"], "description": "Quest difficulty"}
                    },
                    "description": "Fields to modify"
                },
                "reasoning": {"type": "string", "description": "Why these modifications were chosen"}
            },
            "required": ["target_id", "modifications"]
        }
    }
}

MODIFY_ITEM_TOOL = {
    "type": "function",
    "function": {
        "name": "modify_item",
        "description": "Modify existing item data",
        "parameters": {
            "type": "object",
            "properties": {
                "target_id": {"type": "string", "description": "ID of the item to modify"},
                "modifications": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Item name"},
                        "description": {"type": "string", "description": "Item description"},
                        "type": {"type": "string", "enum": ["weapon", "armor", "potion", "scroll", "tool", "treasure"], "description": "Item type"},
                        "value": {"type": "number", "description": "Gold value"},
                        "effects": {"type": "object", "description": "Effects when used"},
                        "requirements": {"type": "object", "description": "Requirements to use item"},
                        "rarity": {"type": "string", "enum": ["common", "uncommon", "rare", "epic", "legendary"], "description": "Item rarity"}
                    },
                    "description": "Fields to modify"
                },
                "reasoning": {"type": "string", "description": "Why these modifications were chosen"}
            },
            "required": ["target_id", "modifications"]
        }
    }
}

MODIFY_NPC_TOOL = {
    "type": "function",
    "function": {
        "name": "modify_npc",
        "description": "Modify existing NPC data",
        "parameters": {
            "type": "object",
            "properties": {
                "target_id": {"type": "string", "description": "ID of the NPC to modify"},
                "modifications": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "NPC name"},
                        "description": {"type": "string", "description": "NPC description"},
                        "personality": {"type": "string", "description": "NPC personality"},
                        "bio": {"type": "string", "description": "NPC background story"},
                        "temperament": {"type": "string", "enum": ["friendly", "neutral", "hostile"], "description": "NPC temperament"},
                        "location": {"type": "string", "description": "Location where NPC is found"},
                        "preset_topics": {"type": "array", "items": {"type": "string"}, "description": "Topics NPC can discuss"},
                        "preset_responses": {"type": "object", "description": "Responses to preset topics"}
                    },
                    "description": "Fields to modify"
                },
                "reasoning": {"type": "string", "description": "Why these modifications were chosen"}
            },
            "required": ["target_id", "modifications"]
        }
    }
}

MODIFY_SKILL_TOOL = {
    "type": "function",
    "function": {
        "name": "modify_skill",
        "description": "Modify existing skill data",
        "parameters": {
            "type": "object",
            "properties": {
                "target_id": {"type": "string", "description": "ID of the skill to modify"},
                "modifications": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Skill name"},
                        "description": {"type": "string", "description": "Skill description"},
                        "skill_type": {"type": "string", "enum": ["active", "passive"], "description": "Skill type"},
                        "mana_cost": {"type": "number", "description": "Mana cost to use skill"},
                        "cooldown": {"type": "number", "description": "Cooldown time in seconds"},
                        "effects": {"type": "object", "description": "Skill effects"},
                        "requirements": {"type": "object", "description": "Requirements to use skill"}
                    },
                    "description": "Fields to modify"
                },
                "reasoning": {"type": "string", "description": "Why these modifications were chosen"}
            },
            "required": ["target_id", "modifications"]
        }
    }
}

MODIFY_BLUEPRINT_TOOL = {
    "type": "function",
    "function": {
        "name": "modify_blueprint",
        "description": "Modify existing blueprint data",
        "parameters": {
            "type": "object",
            "properties": {
                "target_id": {"type": "string", "description": "ID of the blueprint to modify"},
                "modifications": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Blueprint name"},
                        "description": {"type": "string", "description": "Blueprint description"},
                        "result_item": {"type": "string", "description": "Item created by blueprint"},
                        "materials": {"type": "object", "description": "Required materials and quantities"},
                        "difficulty": {"type": "string", "enum": ["easy", "medium", "hard"], "description": "Crafting difficulty"},
                        "skill_required": {"type": "string", "description": "Skill required to craft"}
                    },
                    "description": "Fields to modify"
                },
                "reasoning": {"type": "string", "description": "Why these modifications were chosen"}
            },
            "required": ["target_id", "modifications"]
        }
    }
}

# List of all available tools
AVAILABLE_TOOLS = [
    PERMISSION_CHECK_TOOL,
    DATA_ACTION_TOOL,
    PRIMITIVE_SELECTION_TOOL,
    STRATEGY_DECISION_TOOL,
    DYNAMIC_ACTION_TOOL,
    CREATE_LOCATION_TOOL,
    CREATE_QUEST_TOOL,
    CREATE_ITEM_TOOL,
    CREATE_NPC_TOOL,
    CREATE_BLUEPRINT_TOOL,
    EXECUTE_IMMEDIATE_ACTION_TOOL,
    SUGGESTION_TOOL,
    MODIFY_LOCATION_TOOL,
    MODIFY_QUEST_TOOL,
    MODIFY_ITEM_TOOL,
    MODIFY_NPC_TOOL,
    MODIFY_SKILL_TOOL,
    MODIFY_BLUEPRINT_TOOL
]

# Tool function implementations
def check_player_permission(allowed: bool, reasoning: str, restricted_effects: list = None):
    """
    Implementation of the permission check tool.
    This function is called by the AI when it checks if a player should be allowed to do something.
    """
    return {
        "allowed": allowed,
        "reasoning": reasoning,
        "restricted_effects": restricted_effects or []
    }

def determine_data_action(action_type: str, data_type: str, reasoning: str, confidence: float):
    """
    Implementation of the data action determination tool.
    This function is called by the AI when it decides what type of data action to perform.
    """
    return {
        "action_type": action_type,
        "data_type": data_type,
        "reasoning": reasoning,
        "confidence": confidence
    }

def select_action_primitive(use_specific_primitive: bool, primitive_type: str, reasoning: str, confidence: float):
    """
    Implementation of the primitive selection tool.
    This function is called by the AI when it decides which primitive to use.
    """
    return {
        "use_specific_primitive": use_specific_primitive,
        "primitive_type": primitive_type,
        "reasoning": reasoning,
        "confidence": confidence
    }

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

def create_location(id: str, name: str, description: str, scene: str = None, npcs: list = None, sub_locations: list = None, shop_items: list = None, requirements: dict = None):
    """Implementation of the create location tool."""
    return {
        "id": id,
        "name": name,
        "description": description,
        "scene": scene,
        "npcs": npcs or [],
        "sub_locations": sub_locations or [],
        "shop_items": shop_items or [],
        "requirements": requirements or {}
    }

def create_quest(id: str, name: str, description: str, objectives: list, rewards: dict, location: str = None, requirements: dict = None, difficulty: str = "medium"):
    """Implementation of the create quest tool."""
    return {
        "id": id,
        "name": name,
        "description": description,
        "objectives": objectives,
        "location": location,
        "requirements": requirements or {},
        "rewards": rewards,
        "difficulty": difficulty
    }

def create_item(id: str, name: str, description: str, type: str, value: int, effects: dict = None, requirements: dict = None):
    """Implementation of the create item tool."""
    return {
        "id": id,
        "name": name,
        "description": description,
        "type": type,
        "value": value,
        "effects": effects or {},
        "requirements": requirements or {}
    }

def create_npc(id: str, name: str, description: str, personality: str, temperament: str, bio: str = None, location: str = None, preset_topics: list = None, preset_responses: dict = None):
    """Implementation of the create NPC tool."""
    return {
        "id": id,
        "name": name,
        "description": description,
        "personality": personality,
        "bio": bio,
        "temperament": temperament,
        "location": location,
        "preset_topics": preset_topics or [],
        "preset_responses": preset_responses or {}
    }

def create_blueprint(id: str, name: str, description: str, result_item: str, materials: dict, difficulty: str = "medium", skill_required: str = None):
    """Implementation of the create blueprint tool."""
    return {
        "id": id,
        "name": name,
        "description": description,
        "result_item": result_item,
        "materials": materials,
        "difficulty": difficulty,
        "skill_required": skill_required
    }

def execute_immediate_action(message: str, effects: dict = None):
    """Implementation of the execute immediate action tool."""
    return {
        "message": message,
        "effects": effects or {}
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

def modify_location(target_id: str, modifications: dict, reasoning: str = ""):
    """Implementation of the modify location tool."""
    return {
        "target_id": target_id,
        "modifications": modifications,
        "reasoning": reasoning
    }

def modify_quest(target_id: str, modifications: dict, reasoning: str = ""):
    """Implementation of the modify quest tool."""
    return {
        "target_id": target_id,
        "modifications": modifications,
        "reasoning": reasoning
    }

def modify_item(target_id: str, modifications: dict, reasoning: str = ""):
    """Implementation of the modify item tool."""
    return {
        "target_id": target_id,
        "modifications": modifications,
        "reasoning": reasoning
    }

def modify_npc(target_id: str, modifications: dict, reasoning: str = ""):
    """Implementation of the modify NPC tool."""
    return {
        "target_id": target_id,
        "modifications": modifications,
        "reasoning": reasoning
    }

def modify_skill(target_id: str, modifications: dict, reasoning: str = ""):
    """Implementation of the modify skill tool."""
    return {
        "target_id": target_id,
        "modifications": modifications,
        "reasoning": reasoning
    }

def modify_blueprint(target_id: str, modifications: dict, reasoning: str = ""):
    """Implementation of the modify blueprint tool."""
    return {
        "target_id": target_id,
        "modifications": modifications,
        "reasoning": reasoning
    }

# Tool function mapping
TOOL_FUNCTIONS = {
    "check_player_permission": check_player_permission,
    "determine_data_action": determine_data_action,
    "select_action_primitive": select_action_primitive,
    "decide_action_strategy": decide_action_strategy,
    "create_dynamic_action": create_dynamic_action,
    "create_location": create_location,
    "create_quest": create_quest,
    "create_item": create_item,
    "create_npc": create_npc,
    "create_blueprint": create_blueprint,
    "execute_immediate_action": execute_immediate_action,
    "modify_location": modify_location,
    "modify_quest": modify_quest,
    "modify_item": modify_item,
    "modify_npc": modify_npc,
    "modify_skill": modify_skill,
    "modify_blueprint": modify_blueprint,
    "provide_suggestion": provide_suggestion
} 