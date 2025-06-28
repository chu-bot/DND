from game_types import *
from image import setup_image_generation, generate_game_images, display_image_url, image_gen
from data_loader import data_loader
from ai_actions import ai_handler
from typing import Dict, List, Optional
import random
from datetime import datetime
import os
import uuid


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
                print(f"     Objectives:")
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
    
    def talk_to_npc(self, npc_id: str) -> bool:
        """Start a conversation with an NPC."""
        if npc_id not in self.npcs:
            print(f"NPC {npc_id} not found!")
            return False
        
        npc = self.npcs[npc_id]
        current_loc = self.get_current_location()
        
        # Check if NPC is at current location
        if npc_id not in current_loc.npcs:
            print(f"{npc.name} is not at this location!")
            return False
        
        print(f"\n💬 {npc.name}: {npc.dialogue_tree.get('greeting', 'Hello there!')}")
        
        # Show conversation topics
        topics = npc.dialogue_tree.get('topics', [])
        if topics:
            print("\nTopics you can discuss:")
            for i, topic in enumerate(topics, 1):
                print(f"   {i}. {topic.replace('_', ' ').title()}")
        
        # Show available actions
        print("\nAvailable actions:")
        if npc.quests_offered:
            print(f"   • start <quest_id> - Start a quest from {npc.name}")
        if npc.shop_items:
            print(f"   • shop - Browse {npc.name}'s wares")
        
        # Update conversation history
        if self.game_state:
            if npc_id not in self.game_state.conversation_history:
                self.game_state.conversation_history[npc_id] = []
            self.game_state.conversation_history[npc_id].append(f"Talked at {datetime.now().isoformat()}")
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
            print(f"\n📜 Quests available here:")
            for quest_id in current_loc.quests:
                quest = self.quests[quest_id]
                if quest.status == QuestStatus.NOT_STARTED:
                    print(f"   • {quest.name}: {quest.description}")
        
        # Show NPCs at current location
        if current_loc.npcs:
            print(f"\n👥 NPCs here:")
            for npc_id in current_loc.npcs:
                if npc_id in self.npcs:
                    npc = self.npcs[npc_id]
                    print(f"   • {npc.name}: {npc.description[:50]}...")
                    print(f"     Command: talk {npc_id}")
        
        # Show where you can travel
        print(f"\n🚶 Where you can go:")
        
        # Sub-locations (easy travel - use 'move')
        if current_loc.sub_locations:
            print(f"   📍 Nearby (sub-locations) - Use 'move':")
            print(f"      These are connected areas you can walk to directly.")
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
            print(f"   🌍 Other locations - Use 'travel':")
            print(f"      These require longer journeys and may have requirements.")
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

    def execute_dynamic_action(self, action_id: str) -> bool:
        """Execute a dynamic action from the game state"""
        if not self.game_state or action_id not in self.game_state.ai_generated_actions:
            print(f"Action {action_id} not found!")
            return False
        
        action = self.game_state.ai_generated_actions[action_id]
        player = self.get_player()
        
        # Execute the action
        success, message = action.execute(player, self.game_state)
        
        if success:
            print(f"✅ {message}")
            
            # Update game state
            self._update_game_state()
            
            # Generate image if enabled
            if self.images_enabled:
                generate_game_images(self.__dict__, "dynamic_action", action=action)
            
            return True
        else:
            print(f"❌ {message}")
            return False
    
    def show_dynamic_actions(self):
        """Display all available AI-generated actions"""
        if not self.game_state:
            print("No game state available.")
            return
        
        available_actions = self.game_state.get_available_ai_actions(self.get_player())
        
        if not available_actions:
            print("No AI-generated actions available.")
            return
        
        print("\n" + "="*50)
        print("🤖 AI-GENERATED ACTIONS")
        print("="*50)
        
        for action in available_actions:
            print(f"   • {action.name}")
            print(f"     {action.description}")
            print(f"     Type: {action.action_type}")
            
            if action.cost:
                costs = [f"{amount} {resource}" for resource, amount in action.cost.items()]
                print(f"     Cost: {', '.join(costs)}")
            
            if action.requirements:
                reqs = []
                for req_type, req_value in action.requirements.items():
                    if req_type == "level":
                        reqs.append(f"Level {req_value}")
                    elif req_type == "items":
                        reqs.append(f"Items: {', '.join(req_value)}")
                    elif req_type == "skills":
                        reqs.append(f"Skills: {', '.join(req_value)}")
                    elif req_type == "location":
                        reqs.append(f"Location: {req_value}")
                if reqs:
                    print(f"     Requirements: {', '.join(reqs)}")
            
            print(f"     Command: execute {action.id}")
            print()
        
        print("="*50)
    
    def create_dynamic_action(self, user_input: str) -> bool:
        """Create a new dynamic action using AI"""
        if not self.game_state:
            print("No game state available.")
            return False
        
        print("🤖 Creating a new dynamic action...")
        
        # Prepare game state for AI
        game_state_dict = {
            "player_location": self.current_location,
            "player_health": self.get_player().stats.health,
            "player_mana": self.get_player().stats.mana,
            "player_gold": self.get_player().gold,
            "player_level": self.get_player().stats.level,
            "active_quests": self.get_player().quests_in_progress,
            "inventory": self.get_player().inventory
        }
        
        # Create the action
        action = ai_handler.create_dynamic_action(user_input, game_state_dict)
        
        if action:
            # Add to game state
            self.game_state.add_ai_action(action)
            
            print(f"✅ Created new action: {action.name}")
            print(f"   {action.description}")
            print(f"   Command: execute {action.id}")
            
            return True
        else:
            print("❌ Failed to create dynamic action.")
            return False

    def execute_suggested_action(self, suggested_action: str, original_command: List[str]) -> bool:
        """
        Execute a suggested action from the AI strategy decision.
        Returns True if the action was successfully executed, False otherwise.
        """
        if not suggested_action:
            return False
        
        # Parse the suggested action
        suggested_parts = suggested_action.split()
        if not suggested_parts:
            return False
        
        suggested_cmd = suggested_parts[0].lower()
        
        try:
            # Handle different types of suggested actions
            if suggested_cmd == "status":
                self.show_status()
                return True
            elif suggested_cmd == "inventory":
                self.show_inventory()
                return True
            elif suggested_cmd == "skillbook":
                self.show_skillbook()
                return True
            elif suggested_cmd == "available_quests":
                self.show_available_quests()
                return True
            elif suggested_cmd == "map":
                self.show_map()
                return True
            elif suggested_cmd == "npcs":
                self.show_npcs()
                return True
            elif suggested_cmd == "shop":
                self.show_shop()
                return True
            elif suggested_cmd == "dynamic_actions":
                self.show_dynamic_actions()
                return True
            elif suggested_cmd == "move":
                # Use the original command's location parameter
                if len(original_command) > 1:
                    location = original_command[1]
                    return self.move_to_location(location)
                else:
                    print("❌ Move command requires a location parameter.")
                    return False
            elif suggested_cmd == "use":
                # Use the original command's skill parameter
                if len(original_command) > 1:
                    skill = original_command[1]
                    return self.use_skill(skill)
                else:
                    print("❌ Use command requires a skill parameter.")
                    return False
            elif suggested_cmd == "travel":
                # Use the original command's location parameter
                if len(original_command) > 1:
                    location = original_command[1]
                    return self.travel_to_location(location)
                else:
                    print("❌ Travel command requires a location parameter.")
                    return False
            elif suggested_cmd == "buy":
                # Use the original command's item parameter
                if len(original_command) > 1:
                    item_id = original_command[1]
                    return self.buy_item(item_id)
                else:
                    print("❌ Buy command requires an item parameter.")
                    return False
            elif suggested_cmd == "talk":
                # Use the original command's NPC parameter
                if len(original_command) > 1:
                    npc_id = original_command[1]
                    return self.talk_to_npc(npc_id)
                else:
                    print("❌ Talk command requires an NPC parameter.")
                    return False
            elif suggested_cmd == "start":
                # Use the original command's quest parameter
                if len(original_command) > 1:
                    quest = original_command[1]
                    return self.start_quest(quest)
                else:
                    print("❌ Start command requires a quest parameter.")
                    return False
            else:
                print(f"❌ Unknown suggested action: {suggested_action}")
                return False
                
        except Exception as e:
            print(f"❌ Error executing suggested action: {e}")
            return False

    def get_available_actions(self):
        """Return a list of available actions for the player at the current location."""
        actions = ["status", "inventory", "skillbook", "available_quests", "map", "npcs", "dynamic_actions"]
        
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
        
        # Add talk command if NPCs are present
        if current_loc.npcs:
            actions.append("talk <npc_id>")
        
        return actions

    def print_available_actions(self):
        actions = self.get_available_actions()
        print("\nAvailable actions:")
        for act in actions:
            print(f"- {act}")


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
            elif cmd == "dynamic_actions":
                game.show_dynamic_actions()
            elif cmd == "execute" and len(command) > 1:
                action_id = command[1]
                game.execute_dynamic_action(action_id)
            elif cmd == "quit":
                if game.images_enabled:
                    image_gen.export_image_log()
                print("Thanks for playing!")
                break
            else:
                # Use AI to decide the best strategy for handling this input
                game_state_dict = {
                    "player_location": game.current_location,
                    "player_health": game.get_player().stats.health,
                    "player_mana": game.get_player().stats.mana,
                    "player_gold": game.get_player().gold,
                    "player_level": game.get_player().stats.level,
                    "active_quests": game.get_player().quests_in_progress,
                    "inventory": game.get_player().inventory
                }
                
                # Get AI strategy decision
                strategy = ai_handler.decide_action_strategy(user_input, game_state_dict)
                
                print(f"🤖 Analysis: {strategy['reasoning']}")
                print(f"   Confidence: {strategy['confidence']:.1%}")
                
                if strategy['strategy'] == 'existing' and strategy['suggested_action']:
                    # Try to execute the suggested existing action
                    suggested_cmd = strategy['suggested_action'].split()[0]
                    print(f"🤖 Trying to execute: {strategy['suggested_action']}")
                    
                    # Use the helper method to execute the suggested action
                    if game.execute_suggested_action(strategy['suggested_action'], command):
                        # Action was successful
                        pass
                    else:
                        # Action failed, try dynamic action if recommended
                        if strategy['should_create_dynamic']:
                            print("🤖 Creating a dynamic action instead...")
                            if game.create_dynamic_action(user_input):
                                print("💡 You can now use 'dynamic_actions' to see your custom actions!")
                        else:
                            print("Unknown or unavailable command. Type 'help' for available actions.")
                
                elif strategy['strategy'] == 'dynamic' or strategy['should_create_dynamic']:
                    # Create a dynamic action
                    print("🤖 Creating a custom action for you...")
                    if game.create_dynamic_action(user_input):
                        print("💡 You can now use 'dynamic_actions' to see your custom actions!")
                    else:
                        print("❌ Failed to create dynamic action.")
                        print("Unknown or unavailable command. Type 'help' for available actions.")
                
                else:
                    # Fallback for low confidence or unclear strategy
                    print("🤖 I'm not sure what you want to do. Let me try creating a custom action...")
                    if game.create_dynamic_action(user_input):
                        print("💡 You can now use 'dynamic_actions' to see your custom actions!")
                    else:
                        print("Unknown or unavailable command. Type 'help' for available actions.")
        except KeyboardInterrupt:
            if game.images_enabled:
                image_gen.export_image_log()
            print("\nThanks for playing!")
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
