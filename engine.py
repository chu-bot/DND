from game_types import (
    SkillType, QuestStatus,
    Skill, Item, Location, Blueprint, DialogueInstance,
    Conversation, Stats, Entity, GameState,
    NPC, Quest, ConversationState
)
from image import setup_image_generation, generate_game_images, display_image_url, image_gen
from data_loader import data_loader
from ai_actions import ai_handler
from ai_conversation import AIConversationHandler
from ai_tools import AVAILABLE_TOOLS
from ai_prompts import get_data_creation_message, get_immediate_action_message, get_data_modification_message
from typing import Dict, List, Optional, Any, Tuple
import random
from datetime import datetime
import os
import uuid
import json


class GameEngine:
    def __init__(self):
        self.entities: Dict[str, Entity] = {}
        self.items: Dict[str, Item] = {}
        self.skills: Dict[str, Skill] = {}
        self.quests: Dict[str, Quest] = {}
        self.locations: Dict[str, Location] = {}
        self.blueprints: Dict[str, Blueprint] = {}
        self.dialogues: Dict[str, DialogueInstance] = {}
        self.conversations: Dict[str, Conversation] = {}
        self.npcs: Dict[str, NPC] = {}
        self.current_location: Optional[str] = None
        self.player_id: Optional[str] = None
        self.images_enabled: bool = False
        self.game_state: Optional[GameState] = None
        self.ai_conversation_handler: AIConversationHandler = AIConversationHandler()
        
        # Check if images are enabled in environment
        self.images_enabled = os.getenv("IMAGES_ENABLED", "false").lower() == "true"
        
        # Setup image generation if enabled
        if self.images_enabled:
            setup_image_generation()
        
        # Load all game data from JSON files
        data_loader.load_all_data()
        
        # Copy loaded data to engine
        self.skills = data_loader.skills.copy()
        self.items = data_loader.items.copy()
        self.quests = data_loader.quests.copy()
        self.locations = data_loader.locations.copy()
        self.blueprints = data_loader.blueprints.copy()
        self.dialogues = data_loader.dialogues.copy()
        self.conversations = data_loader.conversations.copy()
        self.npcs = data_loader.npcs.copy()
        
        self._initialize_game_state()
        self._initialize_player()
    
    def _initialize_game_state(self):
        """Initialize or load game state"""
        # Try to load existing state
        self.game_state = GameState.load_from_file()
        
        if not self.game_state:
            # Create new state
            self.game_state = GameState(
                session_id=str(uuid.uuid4()),
                timestamp=datetime.now().isoformat(),
                player_location="tavern",
                player_health=100,
                player_mana=50,
                player_gold=100,
                player_level=1,
                player_experience=0,
                active_quests=[],
                completed_quests=[],
                discovered_locations=["tavern"],
                npc_relationships={},
                conversation_history={},
                world_events=[],
                temporary_effects={}
            )
            self.game_state.save_to_file()
    
    def _update_game_state(self):
        """Update game state with current player and world status"""
        if not self.game_state:
            return
            
        player = self.get_player()
        self.game_state.player_location = self.current_location
        self.game_state.player_health = player.stats.health
        self.game_state.player_mana = player.stats.mana
        self.game_state.player_gold = player.gold
        self.game_state.player_level = player.stats.level
        self.game_state.player_experience = player.stats.experience
        self.game_state.active_quests = player.quests_in_progress.copy()
        
        # Add current location to discovered locations
        if self.current_location not in self.game_state.discovered_locations:
            self.game_state.discovered_locations.append(self.current_location)
        
        self.game_state.save_to_file()
    
    def _initialize_player(self):
        """Initialize the player with basic stats and starting equipment"""
        # Create player stats
        player_stats = Stats(
            health=100,
            max_health=100,
            mana=50,
            max_mana=50,
            strength=15,
            dexterity=12,
            constitution=14,
            intelligence=10,
            wisdom=8,
            charisma=12,
            level=1,
            experience=0
        )
        
        # Create player entity
        player = Entity(
            id="player",
            name="Hero",
            stats=player_stats,
            inventory=["iron_sword"],
            skills=["healing"],
            gold=100
        )
        
        self.entities["player"] = player
        self.player_id = "player"
        
        # Generate character portrait if images enabled
        if self.images_enabled:
            generate_game_images(self.__dict__, "character_creation", character=player)
        
        # Set starting location
        if "tavern" in self.locations:
            self.current_location = "tavern"
            # Add player to tavern
            tavern = self.locations["tavern"]
            if self.player_id not in tavern.entities_within:
                tavern.entities_within.append(self.player_id)
            
            # Generate location image if images enabled
            if self.images_enabled:
                generate_game_images(self.__dict__, "location_enter", location=tavern)
            
            # Show scene-setting text
            self.show_scene()
            
            # Update game state
            self._update_game_state()
    
    def show_scene(self):
        """Display the scene-setting text for the current location, if available."""
        location = self.get_current_location()
        if hasattr(location, 'scene') and location.scene:
            print(f"\n{location.scene}")
        else:
            print(f"\n{location.description}")
    
    def get_player(self) -> Entity:
        """Get the current player entity"""
        return self.entities[self.player_id]
    
    def get_current_location(self) -> Location:
        """Get the current location"""
        return self.locations[self.current_location]
    
    def move_to_location(self, location_id: str) -> bool:
        """Move player to a new location, only allowing free movement to sub-locations."""
        if location_id not in self.locations:
            print(f"Location {location_id} not found!")
            return False
        
        current_loc = self.get_current_location()
        # Only allow moving to sub-locations freely
        if location_id not in current_loc.sub_locations:
            print(f"You can't move directly to {location_id} from here. Try a sub-location.")
            return False
        
        # Remove player from current location
        if self.current_location:
            if self.player_id in current_loc.entities_within:
                current_loc.entities_within.remove(self.player_id)
        
        # Add player to new location
        new_loc = self.locations[location_id]
        if self.player_id not in new_loc.entities_within:
            new_loc.entities_within.append(self.player_id)
        
        self.current_location = location_id
        
        # Generate location image if images enabled
        if self.images_enabled:
            generate_game_images(self.__dict__, "location_enter", location=new_loc)
            cached_url = image_gen.get_cached_image(f"location_{location_id}")
            if cached_url:
                display_image_url(cached_url, f"Welcome to {new_loc.name}!")
        
        # Show scene-setting text
        self.show_scene()
        
        # Update game state
        self._update_game_state()
        return True
    
    def use_skill(self, skill_id: str, target_id: Optional[str] = None) -> bool:
        """Use a skill"""
        player = self.get_player()
        
        if skill_id not in player.skills:
            print(f"You don't have the skill {skill_id}")
            return False
        
        skill = self.skills[skill_id]
        
        if skill.skill_type == SkillType.ACTIVE:
            if player.stats.mana < skill.cost:
                print(f"Not enough mana! Need {skill.cost}, have {player.stats.mana}")
                return False
            
            player.stats.mana -= skill.cost
            print(f"Used {skill.name}: {skill.description}")
            
            # Generate skill effect image if images enabled
            if self.images_enabled:
                generate_game_images(self.__dict__, "skill_used", skill=skill)
                cached_url = image_gen.get_cached_image(f"skill_{skill_id}")
                if cached_url:
                    display_image_url(cached_url, f"{skill.name} effect!")
            
            # Simple effect simulation
            if skill_id == "healing":
                heal_amount = 20
                player.stats.health = min(player.stats.max_health, player.stats.health + heal_amount)
                print(f"Healed for {heal_amount} HP!")
        
        # Update game state
        self._update_game_state()
        return True
    
    def start_quest(self, quest_id: str) -> bool:
        """Start a quest (only if available at current location)"""
        if quest_id not in self.quests:
            print(f"Quest {quest_id} not found!")
            return False
        
        quest = self.quests[quest_id]
        player = self.get_player()
        current_loc = self.get_current_location()
        
        # Check if quest is available at current location
        if quest_id not in current_loc.quests:
            print(f"Quest {quest.name} is not available at this location!")
            return False
        
        if quest.status != QuestStatus.NOT_STARTED:
            print(f"Quest {quest.name} is already {quest.status.value}")
            return False
        
        quest.status = QuestStatus.IN_PROGRESS
        if quest_id not in player.quests_in_progress:
            player.quests_in_progress.append(quest_id)
        
        print(f"Started quest: {quest.name}")
        print(f"Description: {quest.description}")
        for obj in quest.objectives:
            print(f"- {obj.description}")
        
        # Generate quest scene image if images enabled
        if self.images_enabled:
            generate_game_images(self.__dict__, "quest_started", quest=quest)
            cached_url = image_gen.get_cached_image(f"quest_{quest_id}")
            if cached_url:
                display_image_url(cached_url, f"Quest: {quest.name}")
        
        # Update game state
        self._update_game_state()
        return True
    
    def add_item_to_inventory(self, item_id: str) -> bool:
        """Add an item to player's inventory"""
        if item_id not in self.items:
            print(f"Item {item_id} not found!")
            return False
        
        player = self.get_player()
        if item_id not in player.inventory:
            player.inventory.append(item_id)
            item = self.items[item_id]
            print(f"Added {item.name} to inventory")
            
            # Generate item image if images enabled
            if self.images_enabled:
                generate_game_images(self.__dict__, "item_obtained", item=item)
                cached_url = image_gen.get_cached_image(f"item_{item_id}")
                if cached_url:
                    display_image_url(cached_url, f"Obtained: {item.name}")
            
            # If item has a skill, add it to player's skills
            if item.skill and item.skill.id not in player.skills:
                player.skills.append(item.skill.id)
                print(f"Learned skill: {item.skill.name}")
        
        # Update game state
        self._update_game_state()
        return True
    
    def simulate_combat(self, enemy_name: str = "Goblin") -> bool:
        """Simulate a combat encounter"""
        player = self.get_player()
        location = self.get_current_location()
        
        print(f"\n⚔️  Combat started with {enemy_name}!")
        
        # Generate combat scene image if images enabled
        if self.images_enabled:
            generate_game_images(self.__dict__, "combat_started", 
                               player=player, enemy=enemy_name, location=location)
            cached_url = image_gen.get_cached_image(f"combat_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            if cached_url:
                display_image_url(cached_url, f"Combat with {enemy_name}!")
        
        # Simple combat simulation
        enemy_health = 30
        while enemy_health > 0 and player.stats.health > 0:
            # Player attacks
            damage = player.stats.strength + random.randint(1, 6)
            enemy_health -= damage
            print(f"You deal {damage} damage to {enemy_name}!")
            
            if enemy_health <= 0:
                print(f"You defeated {enemy_name}!")
                break
            
            # Enemy attacks
            enemy_damage = random.randint(5, 15)
            player.stats.health -= enemy_damage
            print(f"{enemy_name} deals {enemy_damage} damage to you!")
            
            if player.stats.health <= 0:
                print(f"You were defeated by {enemy_name}!")
                return False
        
        # Update game state
        self._update_game_state()
        return True
    
    def level_up_player(self) -> bool:
        """Level up the player"""
        player = self.get_player()
        new_level = player.stats.level + 1
        
        player.stats.level = new_level
        player.stats.max_health += 10
        player.stats.health = player.stats.max_health
        player.stats.max_mana += 5
        player.stats.mana = player.stats.max_mana
        player.stats.strength += 2
        player.stats.experience += 100
        
        print(f"\n🎉 Level Up! You are now level {new_level}!")
        print(f"Health: {player.stats.max_health}, Mana: {player.stats.max_mana}")
        
        # Generate level up image if images enabled
        if self.images_enabled:
            generate_game_images(self.__dict__, "level_up", character=player, new_level=new_level)
            cached_url = image_gen.get_cached_image(f"levelup_{player.id}_{new_level}")
            if cached_url:
                display_image_url(cached_url, f"Level {new_level} achieved!")
        
        # Update game state
        self._update_game_state()
        return True
    
    def show_status(self):
        """Display current player status"""
        player = self.get_player()
        location = self.get_current_location()
        
        # Ensure player has gold attribute
        if not hasattr(player, 'gold'):
            player.gold = 100
        
        print("\n" + "="*50)
        print(f"Player: {player.name} (Level {player.stats.level})")
        print(f"Location: {location.name}")
        print(f"Health: {player.stats.health}/{player.stats.max_health}")
        print(f"Mana: {player.stats.mana}/{player.stats.max_mana}")
        print(f"Gold: {player.gold}")
        print(f"Experience: {player.stats.experience}")
        print(f"Inventory: {len(player.inventory)} items")
        print(f"Skills: {len(player.skills)} skills")
        print(f"Active Quests: {len(player.quests_in_progress)}")
        print(f"Images: {'Enabled' if self.images_enabled else 'Disabled'}")
        print("="*50)
    
    def show_inventory(self):
        """Display player's inventory"""
        player = self.get_player()
        print("\n--- INVENTORY ---")
        for item_id in player.inventory:
            item = self.items[item_id]
            print(f"- {item.name} ({item.rarity.value})")
            print(f"  {item.description}")
            if item.skill:
                print(f"  Skill: {item.skill.name}")
        print("----------------")
    
    def show_skills(self):
        """Display player's skills"""
        player = self.get_player()
        print("\n--- SKILLS ---")
        for skill_id in player.skills:
            skill = self.skills[skill_id]
            print(f"- {skill.name} ({skill.skill_type.value})")
            print(f"  {skill.description}")
            print(f"  Cost: {skill.cost} mana, Range: {skill.range}")
        print("---------------")
    
    def show_skillbook(self):
        """Display all available skills in a skillbook format."""
        print("\n" + "="*50)
        print("📚 SKILLBOOK")
        print("="*50)
        
        # Group skills by type
        active_skills = []
        passive_skills = []
        
        for skill_id, skill in self.skills.items():
            if skill.skill_type == SkillType.ACTIVE:
                active_skills.append((skill_id, skill))
            else:
                passive_skills.append((skill_id, skill))
        
        # Show active skills
        if active_skills:
            print("⚡ ACTIVE SKILLS (require mana and action):")
            for skill_id, skill in active_skills:
                print(f"   • {skill.name}")
                print(f"     Description: {skill.description}")
                print(f"     Target: {skill.target.value}")
                print(f"     Range: {skill.range}ft, Area: {skill.area_of_effect}ft")
                print(f"     Mana Cost: {skill.cost}")
                print()
        
        # Show passive skills
        if passive_skills:
            print("🛡️  PASSIVE SKILLS (always active):")
            for skill_id, skill in passive_skills:
                print(f"   • {skill.name}")
                print(f"     Description: {skill.description}")
                print(f"     Target: {skill.target.value}")
                print()
        
        # Show player's learned skills
        player = self.get_player()
        learned_skills = [skill_id for skill_id in player.skills if skill_id in self.skills]
        if learned_skills:
            print("🎓 YOUR LEARNED SKILLS:")
            for skill_id in learned_skills:
                skill = self.skills[skill_id]
                status = "✓" if skill_id in player.skills else "○"
                print(f"   {status} {skill.name} ({skill.skill_type.value})")
        
        print("="*50)
    
    def show_available_quests(self):
        """Display only quests that the player can access and start at current location."""
        print("\n" + "="*50)
        print("📜 AVAILABLE QUESTS")
        print("="*50)
        
        current_loc = self.get_current_location()
        available_quests = []
        
        # Check quests at current location only
        for quest_id in current_loc.quests:
            quest = self.quests[quest_id]
            if quest.status == QuestStatus.NOT_STARTED:
                available_quests.append((quest_id, quest, "current_location"))
        
        if available_quests:
            print("🎯 Quests you can start here:")
            for quest_id, quest, access_type in available_quests:
                print(f"   • {quest.name} (Level {quest.level})")
                print(f"     {quest.description}")
                print("     Objectives:")
                for obj in quest.objectives:
                    print(f"       - {obj.description}")
                print(f"     Reward: {self._format_reward(quest.reward)}")
                print(f"     Command: start {quest_id}")
                print()
        else:
            print("   No quests available at this location.")
            print("   Explore other locations to find new quests!")
        
        # Show active quests
        player = self.get_player()
        if player.quests_in_progress:
            print("🔄 ACTIVE QUESTS:")
            for quest_id in player.quests_in_progress:
                if quest_id in self.quests:
                    quest = self.quests[quest_id]
                    print(f"   • {quest.name}")
                    for obj in quest.objectives:
                        progress = f"{obj.current_count}/{obj.required_count}"
                        status = "✓" if obj.completed else "○"
                        print(f"     {status} {obj.description} [{progress}]")
                    print()
        
        print("="*50)
    
    def _can_access_quest(self, quest_id: str) -> bool:
        """Check if player can access a quest."""
        quest = self.quests[quest_id]
        player = self.get_player()
        
        # Check level requirement
        if player.stats.level < quest.level:
            return False
        
        # Add more conditions here (location, items, etc.)
        return True
    
    def _format_reward(self, reward: dict) -> str:
        """Format quest reward for display."""
        parts = []
        if "gold" in reward:
            parts.append(f"{reward['gold']} gold")
        if "experience" in reward:
            parts.append(f"{reward['experience']} XP")
        if "items" in reward:
            item_names = [self.items[item_id].name for item_id in reward["items"] if item_id in self.items]
            if item_names:
                parts.append(f"Items: {', '.join(item_names)}")
        return ", ".join(parts)
    
    def _get_quest_location(self, quest_id: str) -> str:
        """Get the location where a quest is available."""
        for loc_id, location in self.locations.items():
            if quest_id in location.quests:
                return location.name
        return "Unknown"
    
    def show_shop(self):
        """Display the shop inventory and allow purchasing."""
        current_loc = self.get_current_location()
        
        # Check if current location has a shop
        if not hasattr(current_loc, 'shop_items') or not current_loc.shop_items:
            print("   This location doesn't have a shop.")
            return
        
        print("\n" + "="*50)
        print("🏪 SHOP")
        print("="*50)
        
        print(f"Welcome to the shop in {current_loc.name}!")
        print("Available items:")
        
        for item_id in current_loc.shop_items:
            if item_id in self.items:
                item = self.items[item_id]
                print(f"   • {item.name} ({item.rarity.value})")
                print(f"     {item.description}")
                print(f"     Price: {item.cost} gold")
                if item.skill:
                    print(f"     Grants skill: {item.skill.name}")
                print()
        
        print("Commands:")
        print("   buy <item_id> - Purchase an item")
        print("   sell <item_id> - Sell an item from your inventory")
        print("="*50)
    
    def buy_item(self, item_id: str) -> bool:
        """Buy an item from the shop."""
        current_loc = self.get_current_location()
        
        # Check if shop exists and item is available
        if not hasattr(current_loc, 'shop_items') or item_id not in current_loc.shop_items:
            print(f"Item {item_id} is not available in this shop.")
            return False
        
        if item_id not in self.items:
            print(f"Item {item_id} not found.")
            return False
        
        item = self.items[item_id]
        player = self.get_player()
        
        # Check if player has enough gold (assuming player has gold attribute)
        if not hasattr(player, 'gold'):
            player.gold = 100
        
        if player.gold < item.cost:
            print(f"You don't have enough gold! Need {item.cost}, have {player.gold}")
            return False
        
        # Purchase the item
        player.gold -= item.cost
        player.inventory.append(item_id)
        
        print(f"Purchased {item.name} for {item.cost} gold!")
        print(f"Remaining gold: {player.gold}")
        
        # If item grants a skill, add it
        if item.skill and item.skill.id not in player.skills:
            player.skills.append(item.skill.id)
            print(f"Learned skill: {item.skill.name}")
        
        # Update game state
        self._update_game_state()
        return True
    
    def show_npcs(self):
        """Display NPCs at the current location."""
        current_loc = self.get_current_location()
        npcs_here = []
        
        for npc_id in current_loc.npcs:
            if npc_id in self.npcs:
                npcs_here.append(self.npcs[npc_id])
        
        if not npcs_here:
            print("   No NPCs are present at this location.")
            return
        
        print("\n" + "="*50)
        print("👥 NPCs HERE")
        print("="*50)
        
        for npc in npcs_here:
            print(f"   • {npc.name}")
            print(f"     {npc.description}")
            print(f"     Personality: {npc.personality}")
            if npc.quests_offered:
                print(f"     Offers quests: {', '.join(npc.quests_offered)}")
            if npc.shop_items:
                print(f"     Sells items: {', '.join(npc.shop_items)}")
            print(f"     Command: talk {npc.id}")
            print()
        
        print("="*50)
    
    def talk_to_npc(self, npc_id: str, player_input: str = None) -> bool:
        """Start or continue a conversation with an NPC."""
        if npc_id not in self.npcs:
            print(f"NPC {npc_id} not found!")
            return False
        
        npc = self.npcs[npc_id]
        current_loc = self.get_current_location()
        
        # Check if NPC is at current location
        if npc_id not in current_loc.npcs:
            print(f"{npc.name} is not at this location!")
            return False
        
        # Initialize conversation state if it doesn't exist
        if self.game_state and npc_id not in self.game_state.conversation_states:
            self.game_state.conversation_states[npc_id] = ConversationState(
                npc_id=npc_id,
                max_questions_remaining=npc.max_daily_questions
            )
        
        conversation_state = self.game_state.conversation_states[npc_id] if self.game_state else None
        
        # If no player input, show greeting and available topics
        if not player_input:
            print(f"\n💬 {npc.name}: {npc.dialogue_tree.get('greeting', 'Hello there!')}")
            
            # Show conversation topics
            topics = npc.dialogue_tree.get('topics', [])
            if topics:
                print("\nTopics you can discuss:")
                for i, topic in enumerate(topics, 1):
                    topic_name = topic.replace('_', ' ').title()
                    print(f"   {i}. {topic_name}")
                    print(f"      Say: '{topic_name}' or '{topic}' or '{i}'")
            
            # Show available actions
            print("\nAvailable actions:")
            if npc.quests_offered:
                print(f"   • start <quest_id> - Start a quest from {npc.name}")
            if npc.shop_items:
                print(f"   • shop - Browse {npc.name}'s wares")
            
            # Show conversation info
            if conversation_state:
                print("\n💭 Conversation Info:")
                print(f"   • Questions remaining: {conversation_state.max_questions_remaining}")
                print(f"   • Relationship level: {conversation_state.relationship_level}")
                if conversation_state.essential_topics_created:
                    print(f"   • Topics discovered: {len(conversation_state.essential_topics_created)}")
            
            print(f"\n💡 You can ask {npc.name} anything! Just type your question.")
            
            # Update conversation history
            if self.game_state:
                if npc_id not in self.game_state.conversation_history:
                    self.game_state.conversation_history[npc_id] = []
                self.game_state.conversation_history[npc_id].append(f"Talked at {datetime.now().isoformat()}")
                self.game_state.save_to_file()
            
            return True
        
        # Handle player input with AI conversation system
        if not conversation_state:
            print("Error: Conversation state not initialized!")
            return False
        
        # Check if player has questions remaining
        if conversation_state.max_questions_remaining <= 0:
            print(f"💬 {npc.name}: I'm getting tired of all these questions. Maybe we can talk again later?")
            return True
        
        # Check if input matches a pre-set topic first
        preset_topic = self._match_preset_topic(player_input, npc)
        if preset_topic:
            return self._handle_preset_topic(npc, preset_topic, conversation_state)
        
        # Validate input - ignore single words, numbers, or very short inputs (but only if not a topic)
        if self._is_invalid_conversation_input(player_input):
            print(f"💬 {npc.name}: *looks at you curiously*")
            return True
        
        # Analyze the conversation input with AI
        analysis = self.ai_conversation_handler.analyze_conversation_input(
            player_input, npc, conversation_state
        )
        
        # Handle the conversation based on strategy
        if analysis["strategy"] == "preset":
            # Use pre-set response
            preset_topic = analysis["preset_topic"]
            preset_response = npc.dialogue_tree.get("responses", {}).get(preset_topic, "I'm not sure about that.")
            print(f"💬 {npc.name}: {preset_response}")
            
            # Update conversation state
            conversation_state = self.ai_conversation_handler.update_conversation_state(
                conversation_state, player_input, preset_response, 
                analysis["similarity_score"], analysis["is_essential"]
            )
            
        elif analysis["strategy"] == "redirect":
            # Redirect to pre-set topic with dynamic response
            preset_topic = analysis["preset_topic"]
            preset_response = npc.dialogue_tree.get("responses", {}).get(preset_topic, "")
            
            print(f"💬 {npc.name}: {analysis['npc_response']}")
            if preset_response:
                print(f"   (Related to: {preset_topic.replace('_', ' ').title()})")
            
            # Update conversation state
            conversation_state = self.ai_conversation_handler.update_conversation_state(
                conversation_state, player_input, analysis["npc_response"], 
                analysis["similarity_score"], analysis["is_essential"]
            )
            
        else:  # dynamic
            # Generate dynamic response
            dynamic_response = self.ai_conversation_handler.generate_dynamic_response(
                player_input, npc, conversation_state, analysis["is_essential"]
            )
            
            print(f"💬 {npc.name}: {dynamic_response}")
            
            # Update conversation state
            conversation_state = self.ai_conversation_handler.update_conversation_state(
                conversation_state, player_input, dynamic_response, 
                analysis["similarity_score"], analysis["is_essential"]
            )
            
            # Create conversation node if essential
            if analysis["is_essential"]:
                conversation_node = self.ai_conversation_handler.create_conversation_node(
                    player_input, dynamic_response, True, npc
                )
                npc.conversation_nodes.append(conversation_node)
        
        # Update game state
        if self.game_state:
            self.game_state.conversation_states[npc_id] = conversation_state
            self.game_state.save_to_file()
        
        return True
    
    def _is_invalid_conversation_input(self, player_input: str) -> bool:
        """Check if the input should be ignored as a user mistake."""
        if not player_input:
            return True
        
        # Remove extra whitespace and check length
        cleaned_input = player_input.strip()
        if len(cleaned_input) < 3:
            return True
        
        # Check if it's just a single word (no spaces)
        if ' ' not in cleaned_input:
            return True
        
        # Check if it's just a number
        if cleaned_input.isdigit():
            return True
        
        # Check if it's just punctuation or very short
        if len(cleaned_input) < 5 and not any(c.isalpha() for c in cleaned_input):
            return True
        
        return False
    
    def _match_preset_topic(self, player_input: str, npc: NPC) -> Optional[str]:
        """Match player input to a pre-set topic."""
        topics = npc.dialogue_tree.get('topics', [])
        player_input_lower = player_input.lower().strip()
        
        # Check for exact topic name match
        for topic in topics:
            if topic.lower() == player_input_lower:
                return topic
        
        # Check for topic name with spaces
        for topic in topics:
            topic_name = topic.replace('_', ' ').lower()
            if topic_name == player_input_lower:
                return topic
        
        # Check for number input
        try:
            topic_index = int(player_input_lower) - 1
            if 0 <= topic_index < len(topics):
                return topics[topic_index]
        except ValueError:
            pass
        
        return None
    
    def _handle_preset_topic(self, npc: NPC, topic: str, conversation_state: ConversationState) -> bool:
        """Handle a pre-set topic conversation."""
        # Get conversation starter and response
        conversation_starters = npc.dialogue_tree.get('conversation_starters', {})
        responses = npc.dialogue_tree.get('responses', {})
        
        starter = conversation_starters.get(topic, f"Tell me about {topic.replace('_', ' ')}!")
        response = responses.get(topic, "I'm not sure about that.")
        
        # Show the conversation
        print(f"💬 You ask {npc.name}: \"{starter}\"")
        print(f"💬 {npc.name}: {response}")
        
        # Update conversation state
        conversation_state = self.ai_conversation_handler.update_conversation_state(
            conversation_state, starter, response, 1.0, False  # High similarity, not essential
        )
        
        # Update game state
        if self.game_state:
            self.game_state.conversation_states[npc.id] = conversation_state
            self.game_state.save_to_file()
        
        return True
    
    def show_locations(self):
        """Display available locations"""
        current_loc = self.get_current_location()
        print("\n--- LOCATIONS ---")
        print(f"Current: {current_loc.name}")
        print("Available:")
        for location_id, location in self.locations.items():
            if location_id != self.current_location:
                print(f"- {location.name}: {location.description[:50]}...")
        print("-----------------")
    
    def list_data(self, data_type: str):
        """List all available data of a specific type"""
        if data_type == "skills":
            print(f"\n--- ALL SKILLS ({len(self.skills)}) ---")
            for skill_id, skill in self.skills.items():
                print(f"- {skill.name}: {skill.description}")
        elif data_type == "items":
            print(f"\n--- ALL ITEMS ({len(self.items)}) ---")
            for item_id, item in self.items.items():
                print(f"- {item.name} ({item.rarity.value}): {item.description}")
        elif data_type == "quests":
            print(f"\n--- ALL QUESTS ({len(self.quests)}) ---")
            for quest_id, quest in self.quests.items():
                print(f"- {quest.name} (Level {quest.level}): {quest.description}")
        elif data_type == "locations":
            print(f"\n--- ALL LOCATIONS ({len(self.locations)}) ---")
            for location_id, location in self.locations.items():
                print(f"- {location.name}: {location.description[:50]}...")
        else:
            print(f"Unknown data type: {data_type}")

    def show_map(self):
        """Display a simple directed map showing where you can travel from your current location."""
        current_loc = self.get_current_location()
        print("\n" + "="*50)
        print("🗺️  TRAVEL MAP")
        print("="*50)
        
        # Show current location info
        print(f"📍 You are at: {current_loc.name}")
        print(f"   {current_loc.description}")
        
        # Show available quests at current location
        if current_loc.quests:
            print("\n📜 Quests available here:")
            for quest_id in current_loc.quests:
                quest = self.quests[quest_id]
                if quest.status == QuestStatus.NOT_STARTED:
                    print(f"   • {quest.name}: {quest.description}")
        
        # Show NPCs at current location
        if current_loc.npcs:
            print("\n👥 NPCs here:")
            for npc_id in current_loc.npcs:
                if npc_id in self.npcs:
                    npc = self.npcs[npc_id]
                    print(f"   • {npc.name}: {npc.description[:50]}...")
                    print(f"     Command: talk {npc_id}")
        
        # Show where you can travel
        print("\n🚶 Where you can go:")
        
        # Sub-locations (easy travel - use 'move')
        if current_loc.sub_locations:
            print("   📍 Nearby (sub-locations) - Use 'move':")
            print("      These are connected areas you can walk to directly.")
            for sub_id in current_loc.sub_locations:
                sub = self.locations[sub_id]
                print(f"      • {sub.name} - {sub.description[:50]}...")
                print(f"        Command: move {sub_id}")
        
        # Other accessible locations (restricted travel - use 'travel')
        accessible_locations = []
        for loc_id, location in self.locations.items():
            if loc_id != self.current_location and loc_id not in current_loc.sub_locations:
                if self._can_travel_to(loc_id):
                    accessible_locations.append((loc_id, location))
        
        if accessible_locations:
            print("   🌍 Other locations - Use 'travel':")
            print("      These require longer journeys and may have requirements.")
            for loc_id, location in accessible_locations:
                requirement = self._get_travel_requirement(loc_id)
                print(f"      • {location.name} - {location.description[:50]}...")
                print(f"        Requirement: {requirement}")
                print(f"        Command: travel {loc_id}")
        
        if not current_loc.sub_locations and not accessible_locations:
            print("   (No travel options available)")
        
        print("="*50)
        print("💡 Travel Tips:")
        print("   • 'move' = Quick travel to connected areas")
        print("   • 'travel' = Longer journeys with requirements")
        print("="*50)
    
    def _can_travel_to(self, location_id: str) -> bool:
        """Check if player can travel to a specific location."""
        # For now, allow travel to any location (you can add restrictions later)
        return True
    
    def _get_travel_requirement(self, location_id: str) -> str:
        """Get the requirement to travel to a location."""
        # You can implement different requirements based on location
        if location_id == "village":
            return "Travel by road (free)"
        elif location_id == "forest":
            return "Walk through wilderness (free)"
        elif location_id == "cave":
            return "Navigate through forest (free)"
        elif location_id == "treasure_room":
            return "Find hidden passage (requires exploration)"
        else:
            return "Standard travel (free)"
    
    def travel_to_location(self, location_id: str) -> bool:
        """Travel to a location (different from moving to sub-locations)."""
        if location_id not in self.locations:
            print(f"Location {location_id} not found!")
            return False
        
        current_loc = self.get_current_location()
        
        # Check if it's a sub-location (use regular move)
        if location_id in current_loc.sub_locations:
            return self.move_to_location(location_id)
        
        # Check if travel is allowed
        if not self._can_travel_to(location_id):
            requirement = self._get_travel_requirement(location_id)
            print(f"You cannot travel to {location_id}. {requirement}")
            return False
        
        # Remove player from current location
        if self.player_id in current_loc.entities_within:
            current_loc.entities_within.remove(self.player_id)
        
        # Add player to new location
        new_loc = self.locations[location_id]
        if self.player_id not in new_loc.entities_within:
            new_loc.entities_within.append(self.player_id)
        
        self.current_location = location_id
        
        print(f"🚶 You travel to {new_loc.name}...")
        
        # Generate location image if images enabled
        if self.images_enabled:
            generate_game_images(self.__dict__, "location_enter", location=new_loc)
            cached_url = image_gen.get_cached_image(f"location_{location_id}")
            if cached_url:
                display_image_url(cached_url, f"Welcome to {new_loc.name}!")
        
        # Show scene-setting text
        self.show_scene()
        
        # Update game state
        self._update_game_state()
        return True

    def create_new_data(self, user_input: str, data_type: str, game_state: Dict[str, Any]) -> bool:
        """
        Create new data using AI with tool use for specific types.
        Returns True if successful, False otherwise.
        """
        if not hasattr(self, 'ai_handler'):
            from ai_actions import AIActionHandler
            self.ai_handler = AIActionHandler()
        
        try:
            print(f"   🤖 Using AI to create new {data_type}...")
            
            # Create the data creation message
            message = get_data_creation_message(user_input, data_type, game_state)
            
            # Call OpenAI with tool calling for the specific data type
            response = self.ai_handler.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": message},
                    {"role": "user", "content": f"Create new {data_type} for: {user_input}"}
                ],
                tools=[tool for tool in AVAILABLE_TOOLS if tool["function"]["name"] == f"create_{data_type}"],
                tool_choice={"type": "function", "function": {"name": f"create_{data_type}"}},
                temperature=0.7
            )
            
            # Extract tool call response
            tool_call = response.choices[0].message.tool_calls[0]
            new_data = json.loads(tool_call.function.arguments)
            
            # Add the new data to the game state
            if data_type == "location":
                self.locations[new_data["id"]] = new_data
                print(f"   📍 Created new location: {new_data['name']}")
            elif data_type == "quest":
                self.quests[new_data["id"]] = new_data
                print(f"   🎯 Created new quest: {new_data['name']}")
            elif data_type == "item":
                self.items[new_data["id"]] = new_data
                print(f"   🗡️  Created new item: {new_data['name']}")
            elif data_type == "npc":
                self.npcs[new_data["id"]] = new_data
                print(f"   👤 Created new NPC: {new_data['name']}")
            elif data_type == "blueprint":
                self.blueprints[new_data["id"]] = new_data
                print(f"   📋 Created new blueprint: {new_data['name']}")
            
            # Update game state
            self._update_game_state()
            
            return True
            
        except Exception as e:
            print(f"   ❌ Error creating new {data_type}: {e}")
            return False

    def execute_immediate_action(self, user_input: str, game_state: Dict[str, Any]) -> bool:
        """
        Execute an immediate action without creating or modifying data.
        Returns True if successful, False otherwise.
        """
        if not hasattr(self, 'ai_handler'):
            from ai_actions import AIActionHandler
            self.ai_handler = AIActionHandler()
        
        try:
            print("   🤖 Using AI to execute immediate action...")
            
            # Create the immediate action message
            message = get_immediate_action_message(user_input, game_state)
            
            # Call OpenAI with tool calling for immediate action
            response = self.ai_handler.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": message},
                    {"role": "user", "content": f"Execute immediate action: {user_input}"}
                ],
                tools=[tool for tool in AVAILABLE_TOOLS if tool["function"]["name"] == "execute_immediate_action"],
                tool_choice={"type": "function", "function": {"name": "execute_immediate_action"}},
                temperature=0.8
            )
            
            # Extract tool call response
            tool_call = response.choices[0].message.tool_calls[0]
            action_result = json.loads(tool_call.function.arguments)
            
            # Display the result
            print(f"   {action_result['message']}")
            
            # Apply any immediate effects
            if action_result.get('effects'):
                self._apply_immediate_effects(action_result['effects'])
            
            return True
            
        except Exception as e:
            print(f"   ❌ Error executing immediate action: {e}")
            return False

    def _apply_immediate_effects(self, effects: Dict[str, Any]):
        """Apply immediate effects from an action to the player."""
        player = self.get_player()
        
        if 'health_change' in effects:
            player.stats.health = max(0, min(100, player.stats.health + effects['health_change']))
            print(f"   💚 Health changed by {effects['health_change']}")
        
        if 'mana_change' in effects:
            player.stats.mana = max(0, min(50, player.stats.mana + effects['mana_change']))
            print(f"   🔮 Mana changed by {effects['mana_change']}")
        
        if 'gold_change' in effects:
            player.gold = max(0, player.gold + effects['gold_change'])
            print(f"   🪙 Gold changed by {effects['gold_change']}")
        
        if 'experience_change' in effects:
            player.stats.experience += effects['experience_change']
            print(f"   ⭐ Experience gained: {effects['experience_change']}")
            
            # Check for level up
            if player.stats.experience >= player.stats.experience_to_next_level:
                self.level_up_player()

    def modify_existing_data(self, user_input: str, data_type: str, game_state: Dict[str, Any]) -> bool:
        """
        Modify existing data using AI with comprehensive context.
        Returns True if successful, False otherwise.
        """
        if not hasattr(self, 'ai_handler'):
            from ai_actions import AIActionHandler
            self.ai_handler = AIActionHandler()
        
        try:
            print(f"   🤖 Using AI to modify existing {data_type} data...")
            
            # Gather comprehensive context
            comprehensive_context = self.gather_comprehensive_context(game_state)
            
            # Create the modification message
            message = get_data_modification_message(user_input, data_type, comprehensive_context, game_state)
            
            # Call OpenAI with tool calling for data modification
            response = self.ai_handler.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": message},
                    {"role": "user", "content": f"Modify {data_type} data based on: {user_input}"}
                ],
                tools=[tool for tool in AVAILABLE_TOOLS if tool["function"]["name"] == f"modify_{data_type}"],
                tool_choice={"type": "function", "function": {"name": f"modify_{data_type}"}},
                temperature=0.3
            )
            
            # Extract tool call response
            tool_call = response.choices[0].message.tool_calls[0]
            modification_data = json.loads(tool_call.function.arguments)
            
            # Apply the modifications
            success = self._apply_data_modifications(data_type, modification_data, user_input)
            
            if success:
                print(f"   ✅ Successfully modified {data_type} data")
                # Update game state
                self._update_game_state()
            else:
                print(f"   ❌ Failed to modify {data_type} data")
            
            return success
            
        except Exception as e:
            print(f"   ❌ Error modifying {data_type} data: {e}")
            return False

    def _apply_data_modifications(self, data_type: str, modification_data: Dict[str, Any], user_input: str) -> bool:
        """Apply modifications to the specified data type with balance validation and change tracking."""
        try:
            target_id = modification_data.get("target_id")
            modifications = modification_data.get("modifications", {})
            reasoning = modification_data.get("reasoning", "")
            
            # Validate game balance
            is_valid, reason, filtered_modifications = self.validate_game_balance(data_type, target_id, modifications, user_input)
            if not is_valid:
                print(f"   ❌ Balance validation failed: {reason}")
                return False
            
            if not filtered_modifications:
                print("   ❌ No valid modifications after balance validation")
                return False
            
            # Apply modifications and track changes
            changes_made = False
            
            if data_type == "location":
                if target_id in self.locations:
                    location = self.locations[target_id]
                    for field, value in filtered_modifications.items():
                        if hasattr(location, field):
                            old_value = getattr(location, field)
                            setattr(location, field, value)
                            # Track the change
                            self.game_state.change_tracker.add_change(
                                data_type, target_id, field, old_value, value, user_input, reasoning
                            )
                            changes_made = True
                    
            elif data_type == "quest":
                if target_id in self.quests:
                    quest = self.quests[target_id]
                    for field, value in filtered_modifications.items():
                        if hasattr(quest, field):
                            old_value = getattr(quest, field)
                            setattr(quest, field, value)
                            # Track the change
                            self.game_state.change_tracker.add_change(
                                data_type, target_id, field, old_value, value, user_input, reasoning
                            )
                            changes_made = True
                    
            elif data_type == "item":
                if target_id in self.items:
                    item = self.items[target_id]
                    for field, value in filtered_modifications.items():
                        if field == "_consequence":
                            # Handle consequences
                            consequence = value
                            print(f"   ⚠️  Consequence: {consequence['description']}")
                            # Store consequence in game state for future reference
                            if "item_consequences" not in self.game_state.temporary_effects:
                                self.game_state.temporary_effects["item_consequences"] = {}
                            self.game_state.temporary_effects["item_consequences"][target_id] = consequence
                            continue
                        
                        if hasattr(item, field):
                            old_value = getattr(item, field)
                            setattr(item, field, value)
                            # Track the change
                            self.game_state.change_tracker.add_change(
                                data_type, target_id, field, old_value, value, user_input, reasoning
                            )
                            changes_made = True
                    
            elif data_type == "npc":
                if target_id in self.npcs:
                    npc = self.npcs[target_id]
                    for field, value in filtered_modifications.items():
                        if hasattr(npc, field):
                            old_value = getattr(npc, field)
                            setattr(npc, field, value)
                            # Track the change
                            self.game_state.change_tracker.add_change(
                                data_type, target_id, field, old_value, value, user_input, reasoning
                            )
                            changes_made = True
                    
            elif data_type == "skill":
                if target_id in self.skills:
                    skill = self.skills[target_id]
                    for field, value in filtered_modifications.items():
                        if field == "_consequence":
                            # Handle consequences
                            consequence = value
                            print(f"   ⚠️  Consequence: {consequence['description']}")
                            # Store consequence in game state for future reference
                            if "skill_consequences" not in self.game_state.temporary_effects:
                                self.game_state.temporary_effects["skill_consequences"] = {}
                            self.game_state.temporary_effects["skill_consequences"][target_id] = consequence
                            continue
                        
                        if hasattr(skill, field):
                            old_value = getattr(skill, field)
                            setattr(skill, field, value)
                            # Track the change
                            self.game_state.change_tracker.add_change(
                                data_type, target_id, field, old_value, value, user_input, reasoning
                            )
                            changes_made = True
                    
            elif data_type == "blueprint":
                if target_id in self.blueprints:
                    blueprint = self.blueprints[target_id]
                    for field, value in filtered_modifications.items():
                        if hasattr(blueprint, field):
                            old_value = getattr(blueprint, field)
                            setattr(blueprint, field, value)
                            # Track the change
                            self.game_state.change_tracker.add_change(
                                data_type, target_id, field, old_value, value, user_input, reasoning
                            )
                            changes_made = True
            
            if not changes_made:
                print(f"   ❌ Target {data_type} with ID '{target_id}' not found")
                return False
            
            return True
            
        except Exception as e:
            print(f"   ❌ Error applying modifications: {e}")
            return False

    def get_available_actions(self):
        """Return a list of available actions for the player at the current location."""
        actions = ["status", "inventory", "skillbook", "available_quests", "map", "npcs"]
        
        # Add shop command if current location has a shop
        current_loc = self.get_current_location()
        if hasattr(current_loc, 'shop_items') and current_loc.shop_items:
            actions.append("shop")
        
        # Add move command if sub-locations exist
        if current_loc.sub_locations:
            actions.append("move <sub-location> (quick travel to connected areas)")
        
        # Add travel command for other locations
        accessible_locations = []
        for loc_id, location in self.locations.items():
            if loc_id != self.current_location and loc_id not in current_loc.sub_locations:
                if self._can_travel_to(loc_id):
                    accessible_locations.append(loc_id)
        
        if accessible_locations:
            actions.append("travel <location> (longer journeys with requirements)")
        
        # Only show 'use <skill>' if player has active skills
        player = self.get_player()
        if any(self.skills[sk].skill_type == SkillType.ACTIVE for sk in player.skills):
            actions.append("use <skill>")
        
        # Add buy command if in a shop
        if hasattr(current_loc, 'shop_items') and current_loc.shop_items:
            actions.append("buy <item_id>")
        
        # Add talk and ask commands if NPCs are present
        if current_loc.npcs:
            actions.append("talk <npc_id>")
            actions.append("ask <npc_id> <question>")
        
        return actions

    def print_available_actions(self):
        actions = self.get_available_actions()
        print("\nAvailable actions:")
        for act in actions:
            print(f"- {act}")

    def gather_comprehensive_context(self, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gather comprehensive context including all game data and player state.
        This provides the AI with complete information for making modification decisions.
        """
        player = self.get_player()
        current_location = self.get_current_location()
        
        context = {
            "player_state": {
                "location": self.current_location,
                "health": player.stats.health,
                "mana": player.stats.mana,
                "gold": player.gold,
                "level": player.stats.level,
                "experience": player.stats.experience,
                "inventory": player.inventory,
                "equipped_items": player.inventory,  # For now, all inventory is equipped
                "skills": player.skills,
                "active_quests": player.quests_in_progress,
                "completed_quests": self.game_state.completed_quests if self.game_state else [],
                "npc_relationships": self.game_state.npc_relationships if self.game_state else {},
                "discovered_locations": self.game_state.discovered_locations if self.game_state else []
            },
            
            "current_location": {
                "id": current_location.id if current_location else None,
                "name": current_location.name if current_location else None,
                "description": current_location.description if current_location else None,
                "scene": current_location.scene if current_location else None,
                "npcs": current_location.npcs if current_location else [],
                "sub_locations": current_location.sub_locations if current_location else [],
                "shop_items": current_location.shop_items if current_location else [],
                "entities_within": current_location.entities_within if current_location else []
            },
            
            "all_locations": {
                loc_id: {
                    "id": loc.id,
                    "name": loc.name,
                    "description": loc.description,
                    "scene": loc.scene,
                    "npcs": loc.npcs,
                    "sub_locations": loc.sub_locations,
                    "shop_items": loc.shop_items,
                    "entities_within": loc.entities_within,
                    "requirements": getattr(loc, 'requirements', {})
                }
                for loc_id, loc in self.locations.items()
            },
            
            "all_items": {
                item_id: {
                    "id": item.id,
                    "name": item.name,
                    "description": item.description,
                    "cost": item.cost,
                    "rarity": item.rarity.value if hasattr(item.rarity, 'value') else str(item.rarity),
                    "weight": item.weight,
                    "skill": item.skill.id if item.skill else None,
                    "effects": getattr(item, 'effects', {}),
                    "requirements": getattr(item, 'requirements', {})
                }
                for item_id, item in self.items.items()
            },
            
            "all_skills": {
                skill_id: {
                    "id": skill.id,
                    "name": skill.name,
                    "description": skill.description,
                    "skill_type": skill.skill_type.value if hasattr(skill.skill_type, 'value') else str(skill.skill_type),
                    "target": skill.target.value if hasattr(skill.target, 'value') else str(skill.target),
                    "range": skill.range,
                    "area_of_effect": skill.area_of_effect,
                    "cost": skill.cost
                }
                for skill_id, skill in self.skills.items()
            },
            
            "all_quests": {
                quest_id: {
                    "id": quest.id,
                    "name": quest.name,
                    "description": quest.description,
                    "level": quest.level,
                    "objectives": [obj.description for obj in getattr(quest, 'objectives', [])],
                    "reward": getattr(quest, 'reward', {}),
                    "status": quest.status.value if hasattr(quest.status, 'value') else str(quest.status),
                    "location_id": getattr(quest, 'location_id', None)
                }
                for quest_id, quest in self.quests.items()
            },
            
            "all_npcs": {
                npc_id: {
                    "id": npc.id,
                    "name": npc.name,
                    "description": npc.description,
                    "personality": npc.personality,
                    "location_id": npc.location_id,
                    "level": npc.level,
                    "conversation_id": npc.conversation_id,
                    "quests_offered": npc.quests_offered,
                    "shop_items": npc.shop_items,
                    "dialogue_tree": npc.dialogue_tree,
                    "bio": npc.bio,
                    "conversation_nodes": [node.topic for node in getattr(npc, 'conversation_nodes', [])],
                    "temperament": npc.temperament,
                    "max_daily_questions": npc.max_daily_questions
                }
                for npc_id, npc in self.npcs.items()
            },
            
            "all_blueprints": {
                blueprint_id: {
                    "id": blueprint.id,
                    "name": blueprint.name,
                    "resulting_item": blueprint.resulting_item,
                    "required_items": blueprint.required_items,
                    "required_skills": blueprint.required_skills,
                    "location_needed": blueprint.location_needed
                }
                for blueprint_id, blueprint in self.blueprints.items()
            },
            
            "game_state": {
                "session_id": self.game_state.session_id if self.game_state else None,
                "timestamp": self.game_state.timestamp if self.game_state else None,
                "world_events": self.game_state.world_events if self.game_state else [],
                "temporary_effects": self.game_state.temporary_effects if self.game_state else {},
                "conversation_history": self.game_state.conversation_history if self.game_state else {}
            }
        }
        
        return context

    def validate_game_balance(self, data_type: str, target_id: str, modifications: Dict[str, Any], user_input: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Validate that modifications don't break game balance.
        Returns (is_valid, reason, filtered_modifications)
        """
        if data_type == "item":
            return self._validate_item_balance(target_id, modifications, user_input)
        elif data_type == "skill":
            return self._validate_skill_balance(target_id, modifications, user_input)
        elif data_type == "quest":
            return self._validate_quest_balance(target_id, modifications, user_input)
        elif data_type == "location":
            return self._validate_location_balance(target_id, modifications, user_input)
        elif data_type == "npc":
            return self._validate_npc_balance(target_id, modifications, user_input)
        else:
            return True, "No balance validation for this data type", modifications

    def _validate_item_balance(self, target_id: str, modifications: Dict[str, Any], user_input: str) -> Tuple[bool, str, Dict[str, Any]]:
        """Validate item modifications for game balance with ingenuity rewards"""
        if target_id not in self.items:
            return False, f"Item {target_id} not found", {}
        
        item = self.items[target_id]
        filtered_modifications = {}
        
        # Check if player owns this item
        player = self.get_player()
        if target_id not in player.inventory:
            return False, f"You don't own the item {item.name}", {}
        
        # Analyze the user input for ingenuity and creativity
        ingenuity_score = self._calculate_ingenuity_score(user_input, modifications)
        
        # Allow cosmetic changes that don't affect power
        allowed_cosmetic_fields = ["description", "name"]
        for field, value in modifications.items():
            if field in allowed_cosmetic_fields:
                filtered_modifications[field] = value
                continue
            
            # Block direct power-affecting changes
            if field in ["cost", "rarity"]:
                return False, f"Cannot modify {field} - this would affect game balance", {}
            
            # Allow ingenious modifications with consequences
            if field == "description":
                # Check for ingenious modifications
                if self._is_ingenious_modification(user_input, value, ingenuity_score):
                    # Allow the modification but add consequences
                    consequence = self._generate_consequence(user_input, item, modifications)
                    if consequence:
                        filtered_modifications[field] = value
                        filtered_modifications["_consequence"] = consequence
                        continue
                
                # Check if the modification is trying to add magical properties
                if any(word in str(value).lower() for word in ["magic", "enchanted", "powerful", "legendary", "epic"]):
                    return False, "Cannot add magical properties to items through description changes", {}
                
                # Allow regular cosmetic changes
                filtered_modifications[field] = value
        
        if not filtered_modifications:
            return False, "No valid modifications found. Consider cosmetic changes like description or name, or try more creative modifications with realistic consequences.", {}
        
        return True, "Valid modifications", filtered_modifications

    def _calculate_ingenuity_score(self, user_input: str, modifications: Dict[str, Any]) -> float:
        """Calculate how ingenious and creative the modification is"""
        score = 0.0
        
        # Check for creative use scenarios
        creative_scenarios = [
            "using", "using the", "with the", "to cut", "to carve", "to dig", "to pry",
            "breaking", "damaging", "wearing out", "dulling", "chipped", "cracked",
            "repurposing", "modifying", "altering", "customizing", "personalizing"
        ]
        
        input_lower = user_input.lower()
        for scenario in creative_scenarios:
            if scenario in input_lower:
                score += 0.2
        
        # Check for realistic consequences
        consequence_words = [
            "break", "damage", "wear", "dull", "chip", "crack", "rust", "bend",
            "lose", "drop", "misplace", "forget", "leave behind"
        ]
        
        for word in consequence_words:
            if word in input_lower:
                score += 0.3
        
        # Check for detailed reasoning
        if len(user_input) > 50:
            score += 0.1
        
        # Check for specific context
        if any(word in input_lower for word in ["because", "since", "after", "while", "during"]):
            score += 0.2
        
        return min(score, 1.0)

    def _is_ingenious_modification(self, user_input: str, new_value: str, ingenuity_score: float) -> bool:
        """Determine if a modification is ingenious enough to allow"""
        input_lower = user_input.lower()
        
        # High ingenuity scenarios that should be allowed
        ingenious_patterns = [
            # Using items for unintended purposes
            ("using", "to cut", "food"),  # Using sword to cut food
            ("using", "to carve", "wood"),  # Using sword to carve
            ("using", "to dig", "hole"),  # Using sword to dig
            ("using", "to pry", "open"),  # Using sword to pry
            ("breaking", "while", "using"),  # Breaking during use
            ("damaging", "during", "battle"),  # Damaging in combat
            ("wearing out", "from", "use"),  # Wearing out from use
            ("losing", "while", "traveling"),  # Losing while traveling
            ("dropping", "in", "water"),  # Dropping in water
            ("rusting", "from", "moisture"),  # Rusting from moisture
        ]
        
        for pattern in ingenious_patterns:
            if all(word in input_lower for word in pattern):
                return True
        
        # Check for creative repurposing
        if ingenuity_score >= 0.6:
            return True
        
        return False

    def _generate_consequence(self, user_input: str, item, modifications: Dict[str, Any]) -> Dict[str, Any]:
        """Generate realistic consequences for ingenious modifications"""
        input_lower = user_input.lower()
        
        # Consequences based on the type of modification
        if any(word in input_lower for word in ["break", "damage", "crack", "chip"]):
            return {
                "type": "damage",
                "description": f"The {item.name} shows signs of wear and damage from your creative use.",
                "effect": "item_damaged",
                "severity": "minor"
            }
        
        elif any(word in input_lower for word in ["dull", "wearing out", "blunt"]):
            return {
                "type": "deterioration",
                "description": f"The {item.name} has become dulled from overuse.",
                "effect": "item_dulled",
                "severity": "minor"
            }
        
        elif any(word in input_lower for word in ["rust", "corrode", "water"]):
            return {
                "type": "corrosion",
                "description": f"The {item.name} has developed rust spots from exposure to moisture.",
                "effect": "item_rusted",
                "severity": "minor"
            }
        
        elif any(word in input_lower for word in ["lose", "drop", "misplace"]):
            return {
                "type": "loss",
                "description": f"You realize the {item.name} is missing - perhaps lost during your adventures.",
                "effect": "item_lost",
                "severity": "major"
            }
        
        elif any(word in input_lower for word in ["bend", "warp", "deform"]):
            return {
                "type": "deformation",
                "description": f"The {item.name} has been bent out of shape from improper use.",
                "effect": "item_bent",
                "severity": "moderate"
            }
        
        # Default consequence for creative use
        return {
            "type": "wear",
            "description": f"The {item.name} shows signs of creative use and wear.",
            "effect": "item_worn",
            "severity": "minor"
        }

    def _validate_skill_balance(self, target_id: str, modifications: Dict[str, Any], user_input: str) -> Tuple[bool, str, Dict[str, Any]]:
        """Validate skill modifications for game balance with ingenuity rewards"""
        if target_id not in self.skills:
            return False, f"Skill {target_id} not found", {}
        
        skill = self.skills[target_id]
        filtered_modifications = {}
        
        # Check if player has this skill
        player = self.get_player()
        if target_id not in player.skills:
            return False, f"You don't have the skill {skill.name}", {}
        
        # Analyze ingenuity for skill modifications
        ingenuity_score = self._calculate_ingenuity_score(user_input, modifications)
        
        # Allow cosmetic changes
        allowed_cosmetic_fields = ["description", "name"]
        for field, value in modifications.items():
            if field in allowed_cosmetic_fields:
                filtered_modifications[field] = value
                continue
            
            # Block direct power-affecting changes
            if field in ["cost", "skill_type", "target", "range", "area_of_effect"]:
                return False, f"Cannot modify {field} - this would affect game balance", {}
        
        # Allow ingenious skill modifications with consequences
        if "description" in modifications and ingenuity_score >= 0.5:
            # Check for creative skill use scenarios
            if self._is_ingenious_skill_modification(user_input, modifications["description"]):
                consequence = self._generate_skill_consequence(user_input, skill, modifications)
                if consequence:
                    filtered_modifications["description"] = modifications["description"]
                    filtered_modifications["_consequence"] = consequence
        
        if not filtered_modifications:
            return False, "No valid modifications found. Consider cosmetic changes like description or name, or try more creative skill modifications.", {}
        
        return True, "Valid modifications", filtered_modifications

    def _is_ingenious_skill_modification(self, user_input: str, new_description: str) -> bool:
        """Determine if a skill modification is ingenious enough to allow"""
        input_lower = user_input.lower()
        
        # Ingenious skill use scenarios
        ingenious_skill_patterns = [
            ("overusing", "skill"),  # Overusing a skill
            ("practicing", "too much"),  # Practicing too much
            ("learning", "new technique"),  # Learning new technique
            ("adapting", "skill"),  # Adapting skill for new use
            ("forgetting", "how to"),  # Forgetting how to use
            ("improving", "technique"),  # Improving technique
            ("developing", "bad habit"),  # Developing bad habit
        ]
        
        for pattern in ingenious_skill_patterns:
            if all(word in input_lower for word in pattern):
                return True
        
        return False

    def _generate_skill_consequence(self, user_input: str, skill, modifications: Dict[str, Any]) -> Dict[str, Any]:
        """Generate realistic consequences for ingenious skill modifications"""
        input_lower = user_input.lower()
        
        if any(word in input_lower for word in ["overusing", "too much", "exhaustion"]):
            return {
                "type": "exhaustion",
                "description": f"Your {skill.name} has become exhausting from overuse.",
                "effect": "skill_exhausted",
                "severity": "minor"
            }
        
        elif any(word in input_lower for word in ["forgetting", "losing", "rusty"]):
            return {
                "type": "rust",
                "description": f"Your {skill.name} has become rusty from lack of practice.",
                "effect": "skill_rusty",
                "severity": "minor"
            }
        
        elif any(word in input_lower for word in ["bad habit", "wrong way", "incorrect"]):
            return {
                "type": "bad_habit",
                "description": f"You've developed a bad habit with your {skill.name} technique.",
                "effect": "skill_bad_habit",
                "severity": "minor"
            }
        
        return {
            "type": "development",
            "description": f"Your {skill.name} has evolved through creative use.",
            "effect": "skill_evolved",
            "severity": "minor"
        }

    def _validate_quest_balance(self, target_id: str, modifications: Dict[str, Any], user_input: str) -> Tuple[bool, str, Dict[str, Any]]:
        """Validate quest modifications for game balance"""
        if target_id not in self.quests:
            return False, f"Quest {target_id} not found", {}
        
        quest = self.quests[target_id]
        filtered_modifications = {}
        
        # Check if player has this quest active
        player = self.get_player()
        if target_id not in player.quests_in_progress:
            return False, f"You don't have the quest {quest.name} active", {}
        
        # Allow some quest modifications
        allowed_fields = ["description", "name"]
        for field, value in modifications.items():
            if field in allowed_fields:
                filtered_modifications[field] = value
                continue
            
            # Block reward and objective changes
            if field in ["reward", "objectives", "level"]:
                return False, f"Cannot modify {field} - this would affect game balance", {}
        
        if not filtered_modifications:
            return False, "No valid modifications found. Consider cosmetic changes like description or name.", {}
        
        return True, "Valid cosmetic modifications", filtered_modifications

    def _validate_location_balance(self, target_id: str, modifications: Dict[str, Any], user_input: str) -> Tuple[bool, str, Dict[str, Any]]:
        """Validate location modifications for game balance"""
        if target_id not in self.locations:
            return False, f"Location {target_id} not found", {}
        
        filtered_modifications = {}
        
        # Allow most location modifications as they're mostly cosmetic
        allowed_fields = ["description", "name", "scene"]
        for field, value in modifications.items():
            if field in allowed_fields:
                filtered_modifications[field] = value
                continue
            
            # Block structural changes that could break game flow
            if field in ["npcs", "sub_locations", "shop_items", "entities_within"]:
                return False, f"Cannot modify {field} - this would affect game structure", {}
        
        if not filtered_modifications:
            return False, "No valid modifications found. Consider cosmetic changes like description, name, or scene.", {}
        
        return True, "Valid cosmetic modifications", filtered_modifications

    def _validate_npc_balance(self, target_id: str, modifications: Dict[str, Any], user_input: str) -> Tuple[bool, str, Dict[str, Any]]:
        """Validate NPC modifications for game balance"""
        if target_id not in self.npcs:
            return False, f"NPC {target_id} not found", {}
        
        filtered_modifications = {}
        
        # Allow personality and description changes
        allowed_fields = ["description", "personality", "bio", "name"]
        for field, value in modifications.items():
            if field in allowed_fields:
                filtered_modifications[field] = value
                continue
            
            # Block structural changes
            if field in ["location_id", "level", "quests_offered", "shop_items"]:
                return False, f"Cannot modify {field} - this would affect game structure", {}
        
        if not filtered_modifications:
            return False, "No valid modifications found. Consider cosmetic changes like description, personality, or bio.", {}
        
        return True, "Valid cosmetic modifications", filtered_modifications

    def get_change_history(self, data_type: str = None, target_id: str = None, hours: int = None) -> List[Dict[str, Any]]:
        """Get change history with optional filtering"""
        if not self.game_state:
            return []
        
        if hours:
            changes = self.game_state.change_tracker.get_recent_changes(hours)
        else:
            changes = self.game_state.change_tracker.get_changes_for(data_type, target_id)
        
        return [change.to_dict() for change in changes]
    
    def print_change_history(self, data_type: str = None, target_id: str = None, hours: int = None):
        """Print change history in a readable format"""
        changes = self.get_change_history(data_type, target_id, hours)
        
        if not changes:
            print("📝 No changes found")
            return
        
        print(f"📝 Change History ({len(changes)} changes):")
        print("=" * 80)
        
        for change in changes:
            timestamp = change['timestamp'][:19]  # Remove microseconds
            print(f"🕒 {timestamp}")
            print(f"   Type: {change['data_type']}")
            print(f"   Target: {change['target_id']}")
            print(f"   Field: {change['field_name']}")
            print(f"   Old: {change['old_value']}")
            print(f"   New: {change['new_value']}")
            print(f"   User Input: '{change['user_input']}'")
            print(f"   Reasoning: {change['reasoning']}")
            print("-" * 40)
    
    def revert_last_change(self, data_type: str = None, target_id: str = None) -> bool:
        """Revert the last change made to the specified data type/target"""
        if not self.game_state:
            return False
        
        changes = self.game_state.change_tracker.get_changes_for(data_type, target_id)
        if not changes:
            print("   ❌ No changes found to revert")
            return False
        
        # Get the most recent change
        latest_change = max(changes, key=lambda x: x.timestamp)
        
        try:
            # Apply the reversion
            if latest_change.data_type == "location" and latest_change.target_id in self.locations:
                location = self.locations[latest_change.target_id]
                setattr(location, latest_change.field_name, latest_change.old_value)
            elif latest_change.data_type == "quest" and latest_change.target_id in self.quests:
                quest = self.quests[latest_change.target_id]
                setattr(quest, latest_change.field_name, latest_change.old_value)
            elif latest_change.data_type == "item" and latest_change.target_id in self.items:
                item = self.items[latest_change.target_id]
                setattr(item, latest_change.field_name, latest_change.old_value)
            elif latest_change.data_type == "npc" and latest_change.target_id in self.npcs:
                npc = self.npcs[latest_change.target_id]
                setattr(npc, latest_change.field_name, latest_change.old_value)
            elif latest_change.data_type == "skill" and latest_change.target_id in self.skills:
                skill = self.skills[latest_change.target_id]
                setattr(skill, latest_change.field_name, latest_change.old_value)
            elif latest_change.data_type == "blueprint" and latest_change.target_id in self.blueprints:
                blueprint = self.blueprints[latest_change.target_id]
                setattr(blueprint, latest_change.field_name, latest_change.old_value)
            else:
                print(f"   ❌ Cannot revert change for {latest_change.data_type} {latest_change.target_id}")
                return False
            
            # Remove the change from history
            self.game_state.change_tracker.changes.remove(latest_change)
            
            print(f"   ✅ Reverted change: {latest_change.field_name} on {latest_change.target_id}")
            return True
            
        except Exception as e:
            print(f"   ❌ Error reverting change: {e}")
            return False

    def get_active_consequences(self) -> Dict[str, Any]:
        """Get all active consequences for items and skills"""
        if not self.game_state:
            return {}
        
        consequences = {}
        
        # Get item consequences
        item_consequences = self.game_state.temporary_effects.get("item_consequences", {})
        for item_id, consequence in item_consequences.items():
            if item_id in self.items:
                item_name = self.items[item_id].name
                consequences[f"item_{item_id}"] = {
                    "type": "item",
                    "item_name": item_name,
                    "consequence": consequence
                }
        
        # Get skill consequences
        skill_consequences = self.game_state.temporary_effects.get("skill_consequences", {})
        for skill_id, consequence in skill_consequences.items():
            if skill_id in self.skills:
                skill_name = self.skills[skill_id].name
                consequences[f"skill_{skill_id}"] = {
                    "type": "skill",
                    "skill_name": skill_name,
                    "consequence": consequence
                }
        
        return consequences
    
    def print_active_consequences(self):
        """Print all active consequences in a readable format"""
        consequences = self.get_active_consequences()
        
        if not consequences:
            print("📋 No active consequences")
            return
        
        print("📋 Active Consequences:")
        print("=" * 50)
        
        for consequence_id, data in consequences.items():
            if data["type"] == "item":
                print(f"🗡️  {data['item_name']}: {data['consequence']['description']}")
            elif data["type"] == "skill":
                print(f"⚡ {data['skill_name']}: {data['consequence']['description']}")
        
        print("=" * 50)
    
    def clear_consequence(self, item_or_skill_id: str, consequence_type: str = "item"):
        """Clear a specific consequence"""
        if not self.game_state:
            return False
        
        if consequence_type == "item":
            item_consequences = self.game_state.temporary_effects.get("item_consequences", {})
            if item_or_skill_id in item_consequences:
                del item_consequences[item_or_skill_id]
                print(f"   ✅ Cleared consequence for item {item_or_skill_id}")
                return True
        elif consequence_type == "skill":
            skill_consequences = self.game_state.temporary_effects.get("skill_consequences", {})
            if item_or_skill_id in skill_consequences:
                del skill_consequences[item_or_skill_id]
                print(f"   ✅ Cleared consequence for skill {item_or_skill_id}")
                return True
        
        print(f"   ❌ No consequence found for {consequence_type} {item_or_skill_id}")
        return False
    
    def clear_all_consequences(self):
        """Clear all active consequences"""
        if not self.game_state:
            return False
        
        if "item_consequences" in self.game_state.temporary_effects:
            del self.game_state.temporary_effects["item_consequences"]
        
        if "skill_consequences" in self.game_state.temporary_effects:
            del self.game_state.temporary_effects["skill_consequences"]
        
        print("   ✅ Cleared all active consequences")
        return True


def main():
    """Main game loop"""
    game = GameEngine()
    
    print("Welcome to DND Adventure!")
    game.print_available_actions()
    
    while True:
        try:
            user_input = input("\n> ").strip()
            if not user_input:
                continue
                        
            command = user_input.lower().split()
            if not command:
                continue
            
            cmd = command[0]
            
            # Set available actions for AI handler
            available_actions = game.get_available_actions()
            ai_handler.set_available_actions(available_actions)
            
            if cmd == "help":
                game.print_available_actions()
            elif cmd == "status":
                game.show_status()
            elif cmd == "inventory":
                game.show_inventory()
            elif cmd == "skills":
                game.show_skills()
            elif cmd == "skillbook":
                game.show_skillbook()
            elif cmd == "quests":
                game.show_available_quests()
            elif cmd == "available_quests":
                game.show_available_quests()
            elif cmd == "map":
                game.show_map()
            elif cmd == "npcs":
                game.show_npcs()
            elif cmd == "move" and len(command) > 1:
                location = command[1]
                if game.move_to_location(location):
                    game.print_available_actions()
            elif cmd == "use" and len(command) > 1:
                skill = command[1]
                game.use_skill(skill)
            elif cmd == "start" and len(command) > 1:
                quest = command[1]
                game.start_quest(quest)
            elif cmd == "travel" and len(command) > 1:
                location = command[1]
                game.travel_to_location(location)
            elif cmd == "shop":
                game.show_shop()
            elif cmd == "buy" and len(command) > 1:
                item_id = command[1]
                game.buy_item(item_id)
            elif cmd == "talk" and len(command) > 1:
                npc_id = command[1]
                game.talk_to_npc(npc_id)
            elif cmd == "ask" and len(command) > 2:
                npc_id = command[1]
                question = " ".join(command[2:])
                game.talk_to_npc(npc_id, question)
            elif cmd == "quit":
                if game.images_enabled:
                    image_gen.export_image_log()
                print("Thanks for playing!")
                break
            else:
                # Use AI to analyze and execute the action immediately
                current_location = game.get_current_location()
                game_state_dict = {
                    "player_location": game.current_location,
                    "player_health": game.get_player().stats.health,
                    "player_mana": game.get_player().stats.mana,
                    "player_gold": game.get_player().gold,
                    "player_level": game.get_player().stats.level,
                    "active_quests": game.get_player().quests_in_progress,
                    "inventory": game.get_player().inventory,
                    "location_npcs": current_location.npcs if current_location else [],
                    "location_description": current_location.description if current_location else "Unknown location"
                }
                
                # Step 1: Check if player should be allowed to do this
                print("🔒 Checking permissions...")
                permission = ai_handler.check_player_permission(user_input, game_state_dict)
                
                if not permission['allowed']:
                    print(f"❌ {permission['reasoning']}")
                    if permission['restricted_effects']:
                        print(f"   Restricted effects: {', '.join(permission['restricted_effects'])}")
                    continue
                
                # Step 2: Determine if this should create new data or modify existing data
                print("📊 Analyzing data requirements...")
                data_action = ai_handler.determine_data_action(user_input, game_state_dict)
                print(f"   Action type: {data_action['action_type']}")
                print(f"   Data type: {data_action['data_type']}")
                print(f"   Reasoning: {data_action['reasoning']}")
                
                # Step 3: Execute based on data action type
                if data_action['action_type'] == 'create_new':
                    print("🆕 Creating new data...")
                    success = game.create_new_data(user_input, data_action['data_type'], game_state_dict)
                    if success:
                        print(f"✅ Successfully created new {data_action['data_type']} data")
                    else:
                        print(f"❌ Failed to create new {data_action['data_type']} data")
                    
                elif data_action['action_type'] == 'modify_existing':
                    print("✏️  Modifying existing data...")
                    success = game.modify_existing_data(user_input, data_action['data_type'], game_state_dict)
                    if success:
                        print(f"✅ Successfully modified existing {data_action['data_type']} data")
                    else:
                        print(f"❌ Failed to modify existing {data_action['data_type']} data")
                    
                else:  # immediate action
                    print("⚡ Executing immediate action...")
                    success = game.execute_immediate_action(user_input, game_state_dict)
                    if success:
                        print("✅ Immediate action executed successfully")
                    else:
                        print("❌ Failed to execute immediate action")
                
                print("✅ Action analysis completed")
        except KeyboardInterrupt:
            if game.images_enabled:
                image_gen.export_image_log()
            print("\nThanks for playing!")
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
