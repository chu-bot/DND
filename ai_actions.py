import openai
import json
import os
from typing import List, Dict, Any, Optional, Tuple
from difflib import get_close_matches
import re
import uuid
from game_types import Action


class AIActionHandler:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if self.api_key:
            openai.api_key = self.api_key
        self.available_actions = []
        self.action_suggestions = {}
        
    def set_available_actions(self, actions: List[str]):
        """Set the list of available actions for autocorrect and suggestions"""
        self.available_actions = actions
        
    def autocorrect_command(self, user_input: str) -> Tuple[str, bool]:
        """
        Autocorrect common spelling mistakes in commands.
        Returns (corrected_command, was_corrected)
        """
        if not user_input:
            return user_input, False
            
        # Split into command and arguments
        parts = user_input.split()
        if not parts:
            return user_input, False
            
        command = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        # Common misspellings and corrections
        corrections = {
            # Commands
            "staus": "status",
            "inventry": "inventory", 
            "inventori": "inventory",
            "skilbook": "skillbook",
            "skillbok": "skillbook",
            "quests": "available_quests",
            "quest": "available_quests",
            "shp": "shop",
            "by": "buy",
            "mov": "move",
            "tavel": "travel",
            "travl": "travel",
            "us": "use",
            "strt": "start",
            "hel": "help",
            "quit": "quit",
            "exi": "quit",
            "exit": "quit",
            
            # Common item names
            "potion": "health_potion",
            "health": "health_potion",
            "mana": "mana_potion",
            "sword": "iron_sword",
            "armor": "leather_armor",
            "scroll": "fireball_scroll",
            "staff": "magic_staff",
            "ring": "magic_ring",
            "dagger": "dagger",
            
            # Location names
            "tavern": "tavern",
            "forest": "forest",
            "cave": "cave",
            "village": "village",
            "market": "market",
            "blacksmith": "blacksmith",
            "clearing": "clearing",
            "treasure": "treasure_room",
            
            # Quest names
            "goblin": "goblin_hunt",
            "herb": "herb_collection",
            "treasure": "lost_treasure",
            
            # Skill names
            "heal": "healing",
            "fireball": "fireball",
            "lightning": "lightning_bolt",
            "shield": "shield",
            "stealth": "stealth"
        }
        
        # Check for exact corrections first
        if command in corrections:
            corrected_command = corrections[command]
            corrected_input = f"{corrected_command} {' '.join(args)}"
            return corrected_input, True
        
        # Use fuzzy matching for similar commands
        if self.available_actions:
            # Extract base commands from available actions
            base_commands = []
            for action in self.available_actions:
                if ' ' in action:
                    base_commands.append(action.split()[0])
                else:
                    base_commands.append(action)
            
            # Find close matches
            matches = get_close_matches(command, base_commands, n=1, cutoff=0.6)
            if matches:
                corrected_command = matches[0]
                corrected_input = f"{corrected_command} {' '.join(args)}"
                return corrected_input, True
        
        return user_input, False
    
    def create_dynamic_action(self, user_input: str, game_state: Dict[str, Any]) -> Optional[Action]:
        """
        Use AI to create a dynamic action based on user input.
        Returns an Action object or None.
        """
        if not self.api_key:
            return None
            
        try:
            # Ask AI to create an action
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": f"""You are a creative game master for a D&D text adventure. Your job is to create unique, fun, and imaginative actions based on what the player wants to do.

CURRENT GAME STATE:
- Location: {game_state.get('player_location', 'unknown')}
- Health: {game_state.get('player_health', 100)}/100
- Mana: {game_state.get('player_mana', 50)}/50
- Gold: {game_state.get('player_gold', 100)}
- Level: {game_state.get('player_level', 1)}
- Active quests: {game_state.get('active_quests', [])}
- Inventory: {game_state.get('inventory', [])}

THE PLAYER SAID: "{user_input}"

YOUR TASK: Create a dynamic action that fulfills the player's request. Be creative, imaginative, and fun! Think outside the box.

ACTION CREATION GUIDELINES:
1. **Be Creative**: Don't limit yourself to standard RPG actions. Think of unique, interesting, and fun things the player could do.
2. **Make it Fun**: The action should be enjoyable and add to the player's experience.
3. **Be Imaginative**: Consider magical effects, social interactions, environmental interactions, crafting, exploration, and more.
4. **Balance it**: Make sure the action is appropriate for the player's level and resources.
5. **Add Flavor**: Give the action personality and make it feel like part of a living world.

POSSIBLE ACTION TYPES (but don't limit yourself to these):
- **Magical**: Spells, enchantments, rituals, magical experiments
- **Social**: Persuasion, intimidation, diplomacy, performance, deception
- **Exploration**: Searching, investigating, climbing, swimming, flying
- **Crafting**: Brewing, cooking, blacksmithing, enchanting, alchemy
- **Combat**: Special attacks, defensive maneuvers, tactical actions
- **Environmental**: Interacting with objects, manipulating the environment
- **Character Development**: Training, meditation, learning, practicing
- **Economic**: Trading, gambling, investing, bartering
- **Mystical**: Divination, communing with spirits, reading omens
- **Adventure**: Treasure hunting, dungeon delving, monster hunting
- **Creative**: Art, music, storytelling, dancing, acting
- **Survival**: Hunting, fishing, gathering, shelter building
- **Transportation**: Riding, sailing, flying, teleporting
- **Communication**: Animal handling, language learning, signaling
- **Stealth**: Hiding, sneaking, disguising, lockpicking

EFFECTS YOU CAN CREATE:
- **Healing/Restoration**: heal, restore_mana, restore_stamina
- **Resources**: add_gold, add_experience, add_item, learn_skill
- **Movement**: move_to, teleport_to, unlock_location
- **Combat**: damage_enemy, buff_ally, debuff_enemy
- **Social**: improve_relationship, gain_reputation, unlock_dialogue
- **Environmental**: change_weather, create_light, open_secret_passage
- **Temporary**: invisibility, flight, enhanced_senses, protection
- **Permanent**: unlock_ability, gain_title, establish_connection
- **Story**: trigger_event, reveal_secret, advance_quest
- **Creative**: create_art, compose_song, write_story

COSTS TO CONSIDER:
- **Resources**: mana, health, gold, stamina
- **Time**: duration, cooldown, time_consuming
- **Requirements**: level, items, skills, location, relationships
- **Risks**: health_damage, reputation_loss, item_loss

EXAMPLES OF CREATIVE ACTIONS:
- "I want to dance" → "Tavern Dance Performance" (social, costs stamina, gains gold and reputation)
- "I want to brew a potion" → "Alchemical Experimentation" (crafting, costs materials, creates random potion)
- "I want to talk to animals" → "Beast Tongue Ritual" (magical, costs mana, unlocks animal communication)
- "I want to climb the wall" → "Spider Climb" (exploration, costs stamina, reveals hidden area)
- "I want to read minds" → "Mind Reading Spell" (magical, high mana cost, reveals NPC secrets)
- "I want to become invisible" → "Shadow Cloak" (stealth, costs mana, temporary invisibility)
- "I want to fly" → "Levitation Charm" (magical, costs mana, temporary flight ability)
- "I want to predict the future" → "Divination Ritual" (mystical, costs gold, reveals quest hints)
- "I want to tame a beast" → "Beast Bonding" (social, costs time, gains animal companion)
- "I want to create fire" → "Pyromancy" (magical, costs mana, creates fire for various uses)

RETURN A JSON OBJECT WITH THIS STRUCTURE:
{{
    "id": "unique_action_id",
    "name": "Creative Action Name",
    "description": "A detailed, flavorful description of what this action does",
    "action_type": "magical|social|exploration|crafting|combat|environmental|character|economic|mystical|adventure|creative|survival|transportation|communication|stealth",
    "parameters": {{}},
    "targets": [],
    "requirements": {{}},
    "effects": {{}},
    "cost": {{}},
    "duration": null,
    "cooldown": null,
    "success_chance": 1.0
}}

Remember: Be creative, fun, and imaginative! Don't be afraid to create unique and interesting actions that will make the game more enjoyable."""
                    }
                ],
                temperature=0.9
            )
            
            # Parse AI response
            content = response.choices[0].message["content"]
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                action_data = json.loads(json_match.group())
                
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
        if not self.api_key:
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
            
            # Ask AI for suggestion
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": f"""You are a helpful assistant for a D&D text adventure game. 
                        The player tried to do something that's not in the available actions: {user_input}
                        
                        Current game state:
                        - Location: {context['current_location']}
                        - Health: {context['player_health']}
                        - Mana: {context['player_mana']}
                        - Gold: {context['player_gold']}
                        - Active quests: {context['active_quests']}
                        
                        Available actions: {context['available_actions']}
                        
                        Your job is to help the player by either:
                        1. Suggesting the closest available action if their intent is clear
                        2. Encouraging them to create a dynamic action for their unique request
                        3. Providing helpful information about the game
                        
                        If the player wants to do something creative, unique, or not in the available actions,
                        encourage them to try it - the game can create custom actions for almost anything!
                        
                        Be encouraging and creative in your response."""
                    },
                    {
                        "role": "user",
                        "content": f"Player said: {user_input}"
                    }
                ],
                temperature=0.8
            )
            
            # Return a simple response encouraging dynamic action creation
            return {
                "type": "response",
                "message": response.choices[0].message["content"]
            }
                
        except Exception as e:
            print(f"AI suggestion error: {e}")
            return None
    
    def _create_function_definitions(self) -> List[Dict[str, Any]]:
        """This method is no longer used - function calling is removed"""
        return []


# Global instance
ai_handler = AIActionHandler() 