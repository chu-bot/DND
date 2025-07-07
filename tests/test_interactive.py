#!/usr/bin/env python3
"""
Interactive test to verify the game flow works properly.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engine import GameEngine

def test_interactive():
    """Test the game with simulated user input."""
    
    print("🎮 Interactive Game Test")
    print("=" * 50)
    
    # Create game instance
    game = GameEngine()
    
    # Simulate user inputs
    test_inputs = [
        "I want to dance",
        "give me a level",
        "go to the forest",
        "status"
    ]
    
    for user_input in test_inputs:
        print(f"\n🎯 Testing input: '{user_input}'")
        print("-" * 40)
        
        # Simulate the game's input processing
        command = user_input.lower().split()
        if not command:
            continue
        
        cmd = command[0]
        
        # Set available actions for AI handler
        available_actions = game.get_available_actions()
        from ai_actions import ai_handler
        ai_handler.set_available_actions(available_actions)
        
        # Check if it's a standard command
        if cmd in ["help", "status", "inventory", "skills", "skillbook", "quests", "available_quests", "map", "npcs", "shop", "dynamic_actions", "quit"]:
            print(f"   ✅ Standard command: {cmd}")
            continue
        elif cmd in ["move", "use", "start", "travel", "buy", "talk", "ask", "execute"]:
            print(f"   ✅ Command with parameters: {cmd}")
            continue
        else:
            # This would trigger the AI flow
            print("   🤖 Would trigger AI analysis flow...")
            
            # Simulate the AI flow
            game_state_dict = {
                "player_location": game.current_location,
                "player_health": game.get_player().stats.health,
                "player_mana": game.get_player().stats.mana,
                "player_gold": game.get_player().gold,
                "player_level": game.get_player().stats.level,
                "active_quests": game.get_player().quests_in_progress,
                "inventory": game.get_player().inventory
            }
            
            # Step 1: Permission check
            print("   🔒 Checking permissions...")
            permission = ai_handler.check_player_permission(user_input, game_state_dict)
            print(f"      Allowed: {permission['allowed']}")
            
            if not permission['allowed']:
                print(f"      ❌ Blocked: {permission['reasoning']}")
                continue
            
            # Step 2: Primitive selection
            print("   🔧 Selecting primitive...")
            primitive = ai_handler.select_action_primitive(user_input, game_state_dict)
            print(f"      Primitive: {primitive['primitive_type']}")
            
            # Step 3: Strategy decision
            print("   🧠 Analyzing strategy...")
            strategy = ai_handler.decide_action_strategy(user_input, game_state_dict)
            print(f"      Strategy: {strategy['strategy']}")
            
            print("   ✅ AI flow completed successfully")
    
    print("\n🎉 Interactive test completed!")

if __name__ == "__main__":
    test_interactive() 