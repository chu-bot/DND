import json
import os
from typing import Dict, Any, List, Optional
from game_types import *


class DataLoader:
    """Loads game data from JSON files and converts them to Python objects"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.skills: Dict[str, Skill] = {}
        self.items: Dict[str, Item] = {}
        self.quests: Dict[str, Quest] = {}
        self.locations: Dict[str, Location] = {}
        self.blueprints: Dict[str, Blueprint] = {}
        self.dialogues: Dict[str, DialogueInstance] = {}
        self.conversations: Dict[str, Conversation] = {}
        self.npcs: Dict[str, NPC] = {}
        
        # Ensure data directory exists
        os.makedirs(data_dir, exist_ok=True)
    
    def load_all_data(self):
        """Load all game data from JSON files"""
        print("Loading game data...")
        
        self.load_skills()
        self.load_items()
        self.load_quests()
        self.load_locations()
        self.load_blueprints()
        self.load_dialogues()
        self.load_conversations()
        self.load_npcs()
        
        print(f"Loaded: {len(self.skills)} skills, {len(self.items)} items, "
              f"{len(self.quests)} quests, {len(self.locations)} locations")
    
    def load_skills(self):
        """Load skills from JSON file"""
        filepath = os.path.join(self.data_dir, "skills.json")
        if not os.path.exists(filepath):
            print(f"Warning: {filepath} not found, using default skills")
            return
        
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            for skill_id, skill_data in data.items():
                skill = self._create_skill_from_dict(skill_data)
                self.skills[skill_id] = skill
                
        except Exception as e:
            print(f"Error loading skills: {e}")
    
    def load_items(self):
        """Load items from JSON file"""
        filepath = os.path.join(self.data_dir, "items.json")
        if not os.path.exists(filepath):
            print(f"Warning: {filepath} not found, using default items")
            return
        
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            for item_id, item_data in data.items():
                item = self._create_item_from_dict(item_data)
                self.items[item_id] = item
                
        except Exception as e:
            print(f"Error loading items: {e}")
    
    def load_quests(self):
        """Load quests from JSON file"""
        filepath = os.path.join(self.data_dir, "quests.json")
        if not os.path.exists(filepath):
            print(f"Warning: {filepath} not found, using default quests")
            return
        
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            for quest_id, quest_data in data.items():
                quest = self._create_quest_from_dict(quest_data)
                self.quests[quest_id] = quest
                
        except Exception as e:
            print(f"Error loading quests: {e}")
    
    def load_locations(self):
        """Load locations from JSON file"""
        filepath = os.path.join(self.data_dir, "locations.json")
        if not os.path.exists(filepath):
            print(f"Warning: {filepath} not found, using default locations")
            return
        
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            for location_id, location_data in data.items():
                location = self._create_location_from_dict(location_data)
                self.locations[location_id] = location
                
        except Exception as e:
            print(f"Error loading locations: {e}")
    
    def load_blueprints(self):
        """Load blueprints from JSON file"""
        filepath = os.path.join(self.data_dir, "blueprints.json")
        if not os.path.exists(filepath):
            print(f"Warning: {filepath} not found, using default blueprints")
            return
        
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            for blueprint_id, blueprint_data in data.items():
                blueprint = self._create_blueprint_from_dict(blueprint_data)
                self.blueprints[blueprint_id] = blueprint
                
        except Exception as e:
            print(f"Error loading blueprints: {e}")
    
    def load_dialogues(self):
        """Load dialogues from JSON file"""
        filepath = os.path.join(self.data_dir, "dialogues.json")
        if not os.path.exists(filepath):
            print(f"Warning: {filepath} not found, using default dialogues")
            return
        
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            for dialogue_id, dialogue_data in data.items():
                dialogue = self._create_dialogue_from_dict(dialogue_data)
                self.dialogues[dialogue_id] = dialogue
                
        except Exception as e:
            print(f"Error loading dialogues: {e}")
    
    def load_conversations(self):
        """Load conversations from JSON file"""
        filepath = os.path.join(self.data_dir, "conversations.json")
        if not os.path.exists(filepath):
            print(f"Warning: {filepath} not found, using default conversations")
            return
        
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            for conversation_id, conversation_data in data.items():
                conversation = self._create_conversation_from_dict(conversation_data)
                self.conversations[conversation_id] = conversation
                
        except Exception as e:
            print(f"Error loading conversations: {e}")
    
    def load_npcs(self):
        """Load NPCs from JSON file"""
        try:
            with open(os.path.join(self.data_dir, "npcs.json"), 'r') as f:
                npc_data = json.load(f)
            
            for npc_id, npc_info in npc_data.items():
                npc = NPC(
                    id=npc_info['id'],
                    name=npc_info['name'],
                    description=npc_info['description'],
                    personality=npc_info['personality'],
                    location_id=npc_info['location_id'],
                    level=npc_info['level'],
                    conversation_id=npc_info.get('conversation_id'),
                    quests_offered=npc_info.get('quests_offered', []),
                    shop_items=npc_info.get('shop_items', []),
                    dialogue_tree=npc_info.get('dialogue_tree', {}),
                    bio=npc_info.get('bio', ''),
                    temperament=npc_info.get('temperament', 'neutral'),
                    max_daily_questions=npc_info.get('max_daily_questions', 10)
                )
                self.npcs[npc_id] = npc
                
                # Add NPC to their location
                if npc.location_id in self.locations:
                    if npc_id not in self.locations[npc.location_id].npcs:
                        self.locations[npc.location_id].npcs.append(npc_id)
            
            print(f"Loaded {len(self.npcs)} NPCs")
        except FileNotFoundError:
            print("No NPCs file found, skipping NPC loading")
        except Exception as e:
            print(f"Error loading NPCs: {e}")
    
    def _create_skill_from_dict(self, data: Dict[str, Any]) -> Skill:
        """Create a Skill object from dictionary data"""
        return Skill(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            skill_type=SkillType(data["skill_type"]),
            target=TargetType(data["target"]),
            range=data["range"],
            area_of_effect=data["area_of_effect"],
            cost=data["cost"]
        )
    
    def _create_item_from_dict(self, data: Dict[str, Any]) -> Item:
        """Create an Item object from dictionary data"""
        skill = None
        if "skill" in data and data["skill"]:
            skill = self.skills.get(data["skill"])
        
        return Item(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            cost=data["cost"],
            rarity=Rarity(data["rarity"]),
            weight=data["weight"],
            skill=skill
        )
    
    def _create_quest_from_dict(self, data: Dict[str, Any]) -> Quest:
        """Create a Quest object from dictionary data"""
        objectives = []
        for obj_data in data["objectives"]:
            objective = Objective(
                id=obj_data["id"],
                description=obj_data["description"],
                completed=obj_data.get("completed", False),
                required_count=obj_data.get("required_count", 1),
                current_count=obj_data.get("current_count", 0)
            )
            objectives.append(objective)
        
        return Quest(
            id=data["id"],
            name=data["name"],
            status=QuestStatus(data["status"]),
            description=data["description"],
            objectives=objectives,
            level=data["level"],
            reward=data["reward"]
        )
    
    def _create_location_from_dict(self, data: Dict[str, Any]) -> Location:
        """Create a Location object from dictionary data"""
        # Support new fields: scene, lat, long, symbol
        return Location(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            entities_within=data.get("entities_within", []),
            sub_locations=data.get("sub_locations", []),
            quests=data.get("quests", []),
            scene=data.get("scene"),
            lat=data.get("lat"),
            long=data.get("long"),
            symbol=data.get("symbol")
        )
    
    def _create_blueprint_from_dict(self, data: Dict[str, Any]) -> Blueprint:
        """Create a Blueprint object from dictionary data"""
        return Blueprint(
            id=data["id"],
            name=data["name"],
            resulting_item=data["resulting_item"],
            required_items=data.get("required_items", []),
            required_skills=data.get("required_skills", []),
            location_needed=data.get("location_needed")
        )
    
    def _create_dialogue_from_dict(self, data: Dict[str, Any]) -> DialogueInstance:
        """Create a DialogueInstance object from dictionary data"""
        return DialogueInstance(
            id=data["id"],
            text=data["text"],
            sender_id=data["sender_id"],
            receiver_id=data["receiver_id"],
            condition=data.get("condition"),
            action=data.get("action")
        )
    
    def _create_conversation_from_dict(self, data: Dict[str, Any]) -> Conversation:
        """Create a Conversation object from dictionary data"""
        return Conversation(
            id=data["id"],
            root_dialogue=data["root_dialogue"],
            dialogue_list=data.get("dialogue_list", [])
        )
    
    def get_skill(self, skill_id: str) -> Optional[Skill]:
        """Get a skill by ID"""
        return self.skills.get(skill_id)
    
    def get_item(self, item_id: str) -> Optional[Item]:
        """Get an item by ID"""
        return self.items.get(item_id)
    
    def get_quest(self, quest_id: str) -> Optional[Quest]:
        """Get a quest by ID"""
        return self.quests.get(quest_id)
    
    def get_location(self, location_id: str) -> Optional[Location]:
        """Get a location by ID"""
        return self.locations.get(location_id)
    
    def get_blueprint(self, blueprint_id: str) -> Optional[Blueprint]:
        """Get a blueprint by ID"""
        return self.blueprints.get(blueprint_id)
    
    def list_skills(self) -> List[str]:
        """Get list of all skill IDs"""
        return list(self.skills.keys())
    
    def list_items(self) -> List[str]:
        """Get list of all item IDs"""
        return list(self.items.keys())
    
    def list_quests(self) -> List[str]:
        """Get list of all quest IDs"""
        return list(self.quests.keys())
    
    def list_locations(self) -> List[str]:
        """Get list of all location IDs"""
        return list(self.locations.keys())
    
    def list_blueprints(self) -> List[str]:
        """Get list of all blueprint IDs"""
        return list(self.blueprints.keys())


# Global data loader instance
data_loader = DataLoader() 