from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Union, Tuple
from enum import Enum
import json
from datetime import datetime


class Rarity(Enum):
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


class SkillType(Enum):
    PASSIVE = "passive"
    ACTIVE = "active"


class TargetType(Enum):
    ENEMIES = "enemies"
    ONE_ENEMY = "one_enemy"
    ALLIES = "allies"
    SELF = "self"
    ALL = "all"
    ONE_ALLY = "one_ally"


class QuestStatus(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class QuestObjectiveType(Enum):
    KILL = "kill"
    COLLECT = "collect"
    TALK = "talk"
    EXPLORE = "explore"
    CRAFT = "craft"


@dataclass
class Skill:
    id: str
    name: str
    description: str
    skill_type: SkillType
    target: TargetType
    range: int
    area_of_effect: int
    cost: int


@dataclass
class Item:
    id: str
    name: str
    description: str
    cost: int
    rarity: Rarity
    weight: float
    skill: Optional[Skill] = None


@dataclass
class Objective:
    id: str
    description: str
    completed: bool = False
    required_count: int = 1
    current_count: int = 0


@dataclass
class Quest:
    id: str
    name: str
    status: QuestStatus
    description: str
    objectives: List[Objective]
    level: int
    reward: Dict[str, Any]


@dataclass
class Location:
    id: str
    name: str
    description: str
    entities_within: List[str] = field(default_factory=list)
    sub_locations: List[str] = field(default_factory=list)
    quests: List[str] = field(default_factory=list)
    scene: Optional[str] = None
    lat: Optional[float] = None
    long: Optional[float] = None
    symbol: Optional[str] = None
    shop_items: List[str] = field(default_factory=list)
    npcs: List[str] = field(default_factory=list)


@dataclass
class Blueprint:
    id: str
    name: str
    resulting_item: str
    required_items: List[Dict[str, int]] = field(default_factory=list)
    required_skills: List[str] = field(default_factory=list)
    location_needed: Optional[str] = None


@dataclass
class DialogueInstance:
    id: str
    text: str
    sender_id: str
    receiver_id: str
    condition: Optional[str] = None
    action: Optional[str] = None


@dataclass
class Conversation:
    id: str
    root_dialogue: str
    dialogue_list: List[str] = field(default_factory=list)


@dataclass
class Stats:
    health: int
    max_health: int
    mana: int
    max_mana: int
    strength: int
    dexterity: int
    constitution: int
    intelligence: int
    wisdom: int
    charisma: int
    level: int
    experience: int


@dataclass
class Entity:
    id: str
    name: str
    stats: Stats
    inventory: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    blue_dot: Optional[str] = None
    quests_in_progress: List[str] = field(default_factory=list)
    lore: Dict[str, Any] = field(default_factory=dict)
    gold: int = 100


@dataclass
class NPC:
    id: str
    name: str
    description: str
    personality: str
    location_id: str
    level: int
    conversation_id: Optional[str] = None
    quests_offered: List[str] = field(default_factory=list)
    shop_items: List[str] = field(default_factory=list)
    dialogue_tree: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QuestObjective:
    id: str
    description: str
    objective_type: QuestObjectiveType
    required_count: int
    current_count: int = 0
    completed: bool = False
    target_id: Optional[str] = None


@dataclass
class Quest:
    id: str
    name: str
    description: str
    level: int
    objectives: List[QuestObjective]
    reward: Dict[str, Any]
    status: QuestStatus = QuestStatus.NOT_STARTED
    location_id: Optional[str] = None


@dataclass
class Action:
    """A flexible action primitive that can handle any type of game action"""
    id: str
    name: str
    description: str
    action_type: str  # e.g., "movement", "combat", "social", "crafting", "exploration"
    parameters: Dict[str, Any] = field(default_factory=dict)  # Action-specific parameters
    targets: List[str] = field(default_factory=list)  # What/who the action affects
    requirements: Dict[str, Any] = field(default_factory=dict)  # Requirements to perform action
    effects: Dict[str, Any] = field(default_factory=dict)  # What happens when action is performed
    cost: Dict[str, int] = field(default_factory=dict)  # Resource costs (mana, gold, health, etc.)
    duration: Optional[int] = None  # How long the action takes (in game time)
    cooldown: Optional[int] = None  # Cooldown period before action can be used again
    success_chance: float = 1.0  # Probability of success (0.0 to 1.0)
    ai_generated: bool = False  # Whether this action was created by AI
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "action_type": self.action_type,
            "parameters": self.parameters,
            "targets": self.targets,
            "requirements": self.requirements,
            "effects": self.effects,
            "cost": self.cost,
            "duration": self.duration,
            "cooldown": self.cooldown,
            "success_chance": self.success_chance,
            "ai_generated": self.ai_generated
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Action':
        """Create from dictionary"""
        return cls(**data)
    
    def can_perform(self, player: 'Entity', game_state: 'GameState') -> Tuple[bool, str]:
        """Check if the action can be performed by the player"""
        # Check level requirement
        if "level" in self.requirements:
            if player.stats.level < self.requirements["level"]:
                return False, f"Requires level {self.requirements['level']}"
        
        # Check resource costs
        for resource, amount in self.cost.items():
            if resource == "mana" and player.stats.mana < amount:
                return False, f"Not enough mana (need {amount}, have {player.stats.mana})"
            elif resource == "health" and player.stats.health < amount:
                return False, f"Not enough health (need {amount}, have {player.stats.health})"
            elif resource == "gold" and player.gold < amount:
                return False, f"Not enough gold (need {amount}, have {player.gold})"
        
        # Check item requirements
        if "items" in self.requirements:
            for item_id in self.requirements["items"]:
                if item_id not in player.inventory:
                    return False, f"Missing required item: {item_id}"
        
        # Check skill requirements
        if "skills" in self.requirements:
            for skill_id in self.requirements["skills"]:
                if skill_id not in player.skills:
                    return False, f"Missing required skill: {skill_id}"
        
        # Check location requirements
        if "location" in self.requirements:
            if game_state.player_location != self.requirements["location"]:
                return False, f"Must be at {self.requirements['location']}"
        
        return True, "Action can be performed"
    
    def execute(self, player: 'Entity', game_state: 'GameState', **kwargs) -> Tuple[bool, str]:
        """Execute the action and return (success, message)"""
        # Check if action can be performed
        can_perform, message = self.can_perform(player, game_state)
        if not can_perform:
            return False, message
        
        # Apply resource costs
        for resource, amount in self.cost.items():
            if resource == "mana":
                player.stats.mana -= amount
            elif resource == "health":
                player.stats.health -= amount
            elif resource == "gold":
                player.gold -= amount
            elif resource == "stamina":
                # Stamina as a percentage of max health
                stamina_cost = int(player.stats.max_health * (amount / 100))
                player.stats.health = max(1, player.stats.health - stamina_cost)
        
        # Apply effects
        for effect_type, effect_data in self.effects.items():
            if effect_type == "heal":
                heal_amount = effect_data.get("amount", 0)
                player.stats.health = min(player.stats.max_health, player.stats.health + heal_amount)
            elif effect_type == "restore_mana":
                mana_amount = effect_data.get("amount", 0)
                player.stats.mana = min(player.stats.max_mana, player.stats.mana + mana_amount)
            elif effect_type == "add_gold":
                gold_amount = effect_data.get("amount", 0)
                player.gold += gold_amount
            elif effect_type == "add_experience":
                exp_amount = effect_data.get("amount", 0)
                player.stats.experience += exp_amount
            elif effect_type == "add_item":
                item_id = effect_data.get("item_id")
                if item_id and item_id not in player.inventory:
                    player.inventory.append(item_id)
            elif effect_type == "learn_skill":
                skill_id = effect_data.get("skill_id")
                if skill_id and skill_id not in player.skills:
                    player.skills.append(skill_id)
            elif effect_type == "move_to":
                new_location = effect_data.get("location_id")
                if new_location:
                    game_state.player_location = new_location
            elif effect_type == "teleport_to":
                new_location = effect_data.get("location_id")
                if new_location:
                    game_state.player_location = new_location
            elif effect_type == "unlock_location":
                location_id = effect_data.get("location_id")
                if location_id and location_id not in game_state.discovered_locations:
                    game_state.discovered_locations.append(location_id)
            elif effect_type == "improve_relationship":
                npc_id = effect_data.get("npc_id")
                amount = effect_data.get("amount", 1)
                if npc_id:
                    current_relationship = game_state.npc_relationships.get(npc_id, 0)
                    game_state.npc_relationships[npc_id] = current_relationship + amount
            elif effect_type == "gain_reputation":
                amount = effect_data.get("amount", 1)
                # Store reputation in temporary effects
                current_reputation = game_state.temporary_effects.get("reputation", 0)
                game_state.temporary_effects["reputation"] = current_reputation + amount
            elif effect_type == "unlock_dialogue":
                dialogue_id = effect_data.get("dialogue_id")
                if dialogue_id:
                    if "unlocked_dialogues" not in game_state.temporary_effects:
                        game_state.temporary_effects["unlocked_dialogues"] = []
                    game_state.temporary_effects["unlocked_dialogues"].append(dialogue_id)
            elif effect_type == "change_weather":
                weather = effect_data.get("weather", "clear")
                game_state.temporary_effects["weather"] = weather
            elif effect_type == "create_light":
                duration = effect_data.get("duration", 10)
                game_state.temporary_effects["light_source"] = duration
            elif effect_type == "open_secret_passage":
                passage_id = effect_data.get("passage_id")
                if passage_id:
                    if "open_passages" not in game_state.temporary_effects:
                        game_state.temporary_effects["open_passages"] = []
                    game_state.temporary_effects["open_passages"].append(passage_id)
            elif effect_type == "invisibility":
                duration = effect_data.get("duration", 5)
                game_state.temporary_effects["invisible"] = duration
            elif effect_type == "flight":
                duration = effect_data.get("duration", 3)
                game_state.temporary_effects["flying"] = duration
            elif effect_type == "enhanced_senses":
                duration = effect_data.get("duration", 10)
                game_state.temporary_effects["enhanced_senses"] = duration
            elif effect_type == "protection":
                duration = effect_data.get("duration", 5)
                protection_type = effect_data.get("type", "general")
                game_state.temporary_effects[f"protection_{protection_type}"] = duration
            elif effect_type == "unlock_ability":
                ability_id = effect_data.get("ability_id")
                if ability_id:
                    if "unlocked_abilities" not in game_state.temporary_effects:
                        game_state.temporary_effects["unlocked_abilities"] = []
                    game_state.temporary_abilities.append(ability_id)
            elif effect_type == "gain_title":
                title = effect_data.get("title", "Adventurer")
                game_state.temporary_effects["title"] = title
            elif effect_type == "establish_connection":
                connection_type = effect_data.get("type", "general")
                target = effect_data.get("target", "unknown")
                game_state.temporary_effects[f"connection_{connection_type}"] = target
            elif effect_type == "trigger_event":
                event_id = effect_data.get("event_id")
                if event_id:
                    game_state.world_events.append({
                        "id": event_id,
                        "triggered_by": self.id,
                        "timestamp": game_state.timestamp
                    })
            elif effect_type == "reveal_secret":
                secret_id = effect_data.get("secret_id")
                if secret_id:
                    if "revealed_secrets" not in game_state.temporary_effects:
                        game_state.temporary_effects["revealed_secrets"] = []
                    game_state.temporary_effects["revealed_secrets"].append(secret_id)
            elif effect_type == "advance_quest":
                quest_id = effect_data.get("quest_id")
                if quest_id and quest_id in player.quests_in_progress:
                    # Mark quest as advanced
                    if "advanced_quests" not in game_state.temporary_effects:
                        game_state.temporary_effects["advanced_quests"] = []
                    game_state.temporary_effects["advanced_quests"].append(quest_id)
            elif effect_type == "create_art":
                art_type = effect_data.get("type", "painting")
                value = effect_data.get("value", 10)
                game_state.temporary_effects[f"created_art_{art_type}"] = value
            elif effect_type == "compose_song":
                song_type = effect_data.get("type", "ballad")
                game_state.temporary_effects[f"composed_song_{song_type}"] = True
            elif effect_type == "write_story":
                story_type = effect_data.get("type", "tale")
                game_state.temporary_effects[f"written_story_{story_type}"] = True
            elif effect_type == "damage_enemy":
                # This would be handled in combat context
                pass
            elif effect_type == "buff_ally":
                # This would be handled in combat context
                pass
            elif effect_type == "debuff_enemy":
                # This would be handled in combat context
                pass
        
        return True, f"Successfully performed {self.name}"


@dataclass
class GameState:
    """Dynamic game state that changes during gameplay"""
    session_id: str
    timestamp: str
    player_location: str
    player_health: int
    player_mana: int
    player_gold: int
    player_level: int
    player_experience: int
    active_quests: List[str] = field(default_factory=list)
    completed_quests: List[str] = field(default_factory=list)
    discovered_locations: List[str] = field(default_factory=list)
    npc_relationships: Dict[str, int] = field(default_factory=dict)  # NPC ID -> relationship level
    conversation_history: Dict[str, List[str]] = field(default_factory=dict)  # NPC ID -> conversation history
    world_events: List[Dict[str, Any]] = field(default_factory=list)
    temporary_effects: Dict[str, Any] = field(default_factory=dict)
    ai_generated_actions: Dict[str, 'Action'] = field(default_factory=dict)  # AI-created actions
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "session_id": self.session_id,
            "timestamp": self.timestamp,
            "player_location": self.player_location,
            "player_health": self.player_health,
            "player_mana": self.player_mana,
            "player_gold": self.player_gold,
            "player_level": self.player_level,
            "player_experience": self.player_experience,
            "active_quests": self.active_quests,
            "completed_quests": self.completed_quests,
            "discovered_locations": self.discovered_locations,
            "npc_relationships": self.npc_relationships,
            "conversation_history": self.conversation_history,
            "world_events": self.world_events,
            "temporary_effects": self.temporary_effects,
            "ai_generated_actions": {k: v.to_dict() for k, v in self.ai_generated_actions.items()}
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GameState':
        """Create from dictionary"""
        # Handle AI-generated actions separately
        ai_actions_data = data.pop("ai_generated_actions", {})
        game_state = cls(**data)
        
        # Convert AI actions back to Action objects
        for action_id, action_data in ai_actions_data.items():
            game_state.ai_generated_actions[action_id] = Action.from_dict(action_data)
        
        return game_state
    
    def save_to_file(self, filename: str = "game_state.json"):
        """Save state to file"""
        with open(filename, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load_from_file(cls, filename: str = "game_state.json") -> Optional['GameState']:
        """Load state from file"""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            return cls.from_dict(data)
        except FileNotFoundError:
            return None
    
    def add_ai_action(self, action: 'Action'):
        """Add an AI-generated action to the game state"""
        self.ai_generated_actions[action.id] = action
        self.save_to_file()
    
    def remove_ai_action(self, action_id: str):
        """Remove an AI-generated action"""
        if action_id in self.ai_generated_actions:
            del self.ai_generated_actions[action_id]
            self.save_to_file()
    
    def get_available_ai_actions(self, player: 'Entity') -> List['Action']:
        """Get all AI-generated actions that the player can currently perform"""
        available_actions = []
        for action in self.ai_generated_actions.values():
            can_perform, _ = action.can_perform(player, self)
            if can_perform:
                available_actions.append(action)
        return available_actions
