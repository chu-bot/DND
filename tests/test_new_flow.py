#!/usr/bin/env python3
"""
Test the new action flow without dynamic action caching
"""

import os
import sys
from engine import GameEngine
from ai_actions import AIActionHandler

def test_new_action_flow():
    """Test the new action flow with immediate execution"""
    print("🧪 Testing new action flow...")
    
    # Initialize game
    game = GameEngine()
    ai_handler = AIActionHandler()
    
    # Test cases
    test_cases = [
        {
            "input": "I want to dance",
            "expected_action_type": "immediate",
            "description": "Creative action in tavern"
        },
        {
            "input": "I want to explore the forest",
            "expected_action_type": "create_new",
            "expected_data_type": "location",
            "description": "New location creation"
        },
        {
            "input": "I want to complete the goblin quest",
            "expected_action_type": "modify_existing",
            "expected_data_type": "quest",
            "description": "Modify existing quest"
        },
        {
            "input": "Give me a level",
            "expected_allowed": False,
            "description": "Restricted action"
        }
    ]
    
    # Get current game state
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
    
    print(f"📍 Current location: {game.current_location}")
    print(f"👥 NPCs present: {game_state_dict['location_npcs']}")
    print()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: {test_case['description']}")
        print(f"   Input: '{test_case['input']}'")
        
        # Test permission check
        print("   🔒 Checking permissions...")
        permission = ai_handler.check_player_permission(test_case['input'], game_state_dict)
        print(f"      Allowed: {permission['allowed']}")
        print(f"      Reasoning: {permission['reasoning']}")
        
        if not permission['allowed']:
            print("      ❌ Action blocked by permission system")
            if test_case.get('expected_allowed') == False:
                print("      ✅ Correctly blocked restricted action")
            else:
                print("      ❌ Unexpectedly blocked allowed action")
            print()
            continue
        
        # Test data action determination
        print("   📊 Analyzing data requirements...")
        data_action = ai_handler.determine_data_action(test_case['input'], game_state_dict)
        print(f"      Action type: {data_action['action_type']}")
        print(f"      Data type: {data_action['data_type']}")
        print(f"      Reasoning: {data_action['reasoning']}")
        
        # Check if results match expectations
        if test_case.get('expected_action_type'):
            if data_action['action_type'] == test_case['expected_action_type']:
                print(f"      ✅ Correct action type: {data_action['action_type']}")
            else:
                print(f"      ❌ Expected {test_case['expected_action_type']}, got {data_action['action_type']}")
        
        if test_case.get('expected_data_type'):
            if data_action['data_type'] == test_case['expected_data_type']:
                print(f"      ✅ Correct data type: {data_action['data_type']}")
            else:
                print(f"      ❌ Expected {test_case['expected_data_type']}, got {data_action['data_type']}")
        
        print()
    
    print("✅ New action flow test completed!")

def test_comprehensive_context():
    """Test the comprehensive context gathering system"""
    print("\n🧪 Testing comprehensive context system...")
    
    # Initialize game
    game = GameEngine()
    
    # Get comprehensive context
    game_state_dict = {
        "player_location": game.current_location,
        "player_health": game.get_player().stats.health,
        "player_mana": game.get_player().stats.mana,
        "player_gold": game.get_player().gold,
        "player_level": game.get_player().stats.level,
        "active_quests": game.get_player().quests_in_progress,
        "inventory": game.get_player().inventory,
        "location_npcs": game.get_current_location().npcs if game.get_current_location() else [],
        "location_description": game.get_current_location().description if game.get_current_location() else "Unknown location"
    }
    
    context = game.gather_comprehensive_context(game_state_dict)
    
    print(f"📊 Context gathered successfully!")
    print(f"   Player state: {len(context['player_state'])} fields")
    print(f"   Locations: {len(context['all_locations'])} available")
    print(f"   Items: {len(context['all_items'])} available")
    print(f"   Skills: {len(context['all_skills'])} available")
    print(f"   Quests: {len(context['all_quests'])} available")
    print(f"   NPCs: {len(context['all_npcs'])} available")
    print(f"   Blueprints: {len(context['all_blueprints'])} available")
    
    # Test a few specific context items
    print(f"\n   Current location: {context['current_location']['name']}")
    print(f"   Player inventory: {context['player_state']['inventory']}")
    print(f"   Player skills: {context['player_state']['skills']}")
    
    print("✅ Comprehensive context test completed!")

def test_modification_system():
    """Test the data modification system"""
    print("\n🧪 Testing data modification system...")
    
    # Initialize game
    game = GameEngine()
    
    # Test modification cases
    modification_cases = [
        {
            "input": "Complete the goblin hunt quest",
            "data_type": "quest",
            "description": "Quest completion modification"
        },
        {
            "input": "Update the tavern description to be more welcoming",
            "data_type": "location", 
            "description": "Location description modification"
        },
        {
            "input": "Make the iron sword more powerful",
            "data_type": "item",
            "description": "Item modification"
        }
    ]
    
    game_state_dict = {
        "player_location": game.current_location,
        "player_health": game.get_player().stats.health,
        "player_mana": game.get_player().stats.mana,
        "player_gold": game.get_player().gold,
        "player_level": game.get_player().stats.level,
        "active_quests": game.get_player().quests_in_progress,
        "inventory": game.get_player().inventory,
        "location_npcs": game.get_current_location().npcs if game.get_current_location() else [],
        "location_description": game.get_current_location().description if game.get_current_location() else "Unknown location"
    }
    
    for i, test_case in enumerate(modification_cases, 1):
        print(f"Test {i}: {test_case['description']}")
        print(f"   Input: '{test_case['input']}'")
        print(f"   Data type: {test_case['data_type']}")
        
        # Test modification (this will only work if OpenAI API key is available)
        try:
            success = game.modify_existing_data(test_case['input'], test_case['data_type'], game_state_dict)
            if success:
                print(f"   ✅ Modification successful")
            else:
                print(f"   ❌ Modification failed")
        except Exception as e:
            print(f"   ⚠️  Modification test skipped (no API key or error: {e})")
        
        print()
    
    print("✅ Data modification test completed!")

def test_change_tracking_and_balance():
    """Test the change tracking and game balance validation system"""
    print("\n🧪 Testing change tracking and balance validation...")
    
    # Initialize game
    game = GameEngine()
    
    # Test cases for balance validation
    balance_test_cases = [
        {
            "input": "Make my iron sword more powerful",
            "data_type": "item",
            "description": "Attempt to modify item power (should be blocked)",
            "expected_success": False
        },
        {
            "input": "Change the description of my iron sword to be more detailed",
            "data_type": "item",
            "description": "Cosmetic item modification (should be allowed)",
            "expected_success": True
        },
        {
            "input": "I used my iron sword to cut my food and it got chipped",
            "data_type": "item",
            "description": "Ingenious item modification with consequence (should be allowed)",
            "expected_success": True
        },
        {
            "input": "I was using my sword to dig a hole and it got dull",
            "data_type": "item",
            "description": "Creative item use with realistic consequence (should be allowed)",
            "expected_success": True
        },
        {
            "input": "Make my healing skill cost less mana",
            "data_type": "skill",
            "description": "Attempt to modify skill cost (should be blocked)",
            "expected_success": False
        },
        {
            "input": "I've been overusing my healing skill and it's becoming exhausting",
            "data_type": "skill",
            "description": "Ingenious skill modification with consequence (should be allowed)",
            "expected_success": True
        },
        {
            "input": "Update the tavern description to be more welcoming",
            "data_type": "location",
            "description": "Cosmetic location modification (should be allowed)",
            "expected_success": True
        },
        {
            "input": "Give myself a legendary sword",
            "data_type": "item",
            "description": "Attempt to create overpowered item (should be blocked)",
            "expected_success": False
        },
        {
            "input": "I dropped my sword in the river and it got rusty",
            "data_type": "item",
            "description": "Realistic item consequence (should be allowed)",
            "expected_success": True
        },
        {
            "input": "I've been practicing my healing too much and developed a bad habit",
            "data_type": "skill",
            "description": "Skill development with consequence (should be allowed)",
            "expected_success": True
        }
    ]
    
    game_state_dict = {
        "player_location": game.current_location,
        "player_health": game.get_player().stats.health,
        "player_mana": game.get_player().stats.mana,
        "player_gold": game.get_player().gold,
        "player_level": game.get_player().stats.level,
        "active_quests": game.get_player().quests_in_progress,
        "inventory": game.get_player().inventory,
        "location_npcs": game.get_current_location().npcs if game.get_current_location() else [],
        "location_description": game.get_current_location().description if game.get_current_location() else "Unknown location"
    }
    
    successful_modifications = 0
    
    for i, test_case in enumerate(balance_test_cases, 1):
        print(f"Test {i}: {test_case['description']}")
        print(f"   Input: '{test_case['input']}'")
        print(f"   Data type: {test_case['data_type']}")
        
        # Test modification
        try:
            success = game.modify_existing_data(test_case['input'], test_case['data_type'], game_state_dict)
            if success == test_case['expected_success']:
                print(f"   ✅ Expected {test_case['expected_success']}, got {success}")
                if success:
                    successful_modifications += 1
            else:
                print(f"   ❌ Expected {test_case['expected_success']}, got {success}")
        except Exception as e:
            print(f"   ⚠️  Test skipped (error: {e})")
        
        print()
    
    # Test change history
    print("📝 Testing change history...")
    game.print_change_history(hours=1)
    
    # Test active consequences
    print("\n📋 Testing active consequences...")
    game.print_active_consequences()
    
    # Test reverting changes
    if successful_modifications > 0:
        print("\n🔄 Testing change reversion...")
        success = game.revert_last_change()
        if success:
            print("   ✅ Successfully reverted last change")
        else:
            print("   ❌ Failed to revert last change")
    
    # Test consequence management
    print("\n🧹 Testing consequence management...")
    consequences = game.get_active_consequences()
    if consequences:
        # Clear one consequence as example
        for consequence_id, data in consequences.items():
            if data["type"] == "item":
                game.clear_consequence(data["item_name"], "item")
                break
            elif data["type"] == "skill":
                game.clear_consequence(data["skill_name"], "skill")
                break
    
    print(f"✅ Change tracking and balance validation test completed! ({successful_modifications} successful modifications)")

if __name__ == "__main__":
    test_new_action_flow()
    test_comprehensive_context()
    test_modification_system()
    test_change_tracking_and_balance() 