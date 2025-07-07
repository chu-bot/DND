#!/usr/bin/env python3
"""
Test script for the new AI system with modern OpenAI client and tool calling.
"""

import os
from ai_actions import ai_handler
from ai_prompts import (
    get_strategy_decision_message, 
    get_dynamic_action_message,
    get_permission_check_message,
    get_primitive_selection_message
)
from ai_tools import AVAILABLE_TOOLS

def test_ai_system():
    """Test the new AI system components."""
    
    print("🤖 Testing New AI System")
    print("=" * 50)
    
    # Test 1: Check if API key is available
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        print("✅ OpenAI API key found")
    else:
        print("⚠️  No OpenAI API key found - some tests will be skipped")
    
    # Test 2: Test available actions setup
    test_actions = ["status", "inventory", "move", "use", "talk"]
    ai_handler.set_available_actions(test_actions)
    print(f"✅ Available actions set: {test_actions}")
    
    # Test 3: Test permission check (without API call)
    print("\n🔒 Testing Permission Check Logic...")
    game_state = {
        "player_location": "tavern",
        "player_health": 80,
        "player_mana": 30,
        "player_gold": 150,
        "player_level": 3,
        "active_quests": ["quest_1"],
        "inventory": ["sword", "potion"]
    }
    
    # Test with allowed action
    permission = ai_handler.check_player_permission("I want to dance", game_state)
    print(f"   Permission for 'I want to dance': {permission['allowed']}")
    print(f"   Reasoning: {permission['reasoning']}")
    
    # Test with restricted action
    permission = ai_handler.check_player_permission("give me a level", game_state)
    print(f"   Permission for 'give me a level': {permission['allowed']}")
    print(f"   Reasoning: {permission['reasoning']}")
    
    # Test 4: Test primitive selection (without API call)
    print("\n🔧 Testing Primitive Selection Logic...")
    
    # Test with location-based action
    primitive = ai_handler.select_action_primitive("go to the forest", game_state)
    print(f"   Primitive for 'go to the forest': {primitive['primitive_type']}")
    print(f"   Confidence: {primitive['confidence']:.1%}")
    print(f"   Reasoning: {primitive['reasoning']}")
    
    # Test with creative action
    primitive = ai_handler.select_action_primitive("I want to dance", game_state)
    print(f"   Primitive for 'I want to dance': {primitive['primitive_type']}")
    print(f"   Confidence: {primitive['confidence']:.1%}")
    print(f"   Reasoning: {primitive['reasoning']}")
    
    # Test 5: Test strategy decision (without API call)
    print("\n🧠 Testing Strategy Decision Logic...")
    
    # Test with a simple command
    strategy = ai_handler.decide_action_strategy("status", game_state)
    print(f"   Strategy for 'status': {strategy['strategy']}")
    print(f"   Confidence: {strategy['confidence']:.1%}")
    print(f"   Reasoning: {strategy['reasoning']}")
    
    # Test with a creative command
    strategy = ai_handler.decide_action_strategy("I want to dance", game_state)
    print(f"   Strategy for 'I want to dance': {strategy['strategy']}")
    print(f"   Confidence: {strategy['confidence']:.1%}")
    print(f"   Reasoning: {strategy['reasoning']}")
    
    # Test 6: Test fuzzy matching
    print("\n🔍 Testing Fuzzy Matching...")
    closest_action, score = ai_handler.find_closest_existing_action("show status")
    print(f"   'show status' → {closest_action} (score: {score:.1f})")
    
    closest_action, score = ai_handler.find_closest_existing_action("check inventory")
    print(f"   'check inventory' → {closest_action} (score: {score:.1f})")
    
    # Test 7: Test prompt generation
    print("\n📝 Testing Prompt Generation...")
    context = {
        "user_input": "test input",
        "available_actions": test_actions,
        "current_location": "tavern",
        "player_health": 80,
        "player_mana": 30,
        "player_gold": 150,
        "player_level": 3,
        "active_quests": ["quest_1"],
        "inventory": ["sword", "potion"]
    }
    
    strategy_message = get_strategy_decision_message(context)
    print(f"   Strategy message length: {len(strategy_message)} characters")
    
    dynamic_message = get_dynamic_action_message("I want to dance", game_state)
    print(f"   Dynamic action message length: {len(dynamic_message)} characters")
    
    permission_message = get_permission_check_message("I want to dance", game_state)
    print(f"   Permission check message length: {len(permission_message)} characters")
    
    primitive_message = get_primitive_selection_message("I want to dance", game_state)
    print(f"   Primitive selection message length: {len(primitive_message)} characters")
    
    # Test 8: Test tools
    print("\n🛠️  Testing Tools...")
    print(f"   Available tools: {len(AVAILABLE_TOOLS)}")
    for tool in AVAILABLE_TOOLS:
        tool_name = tool["function"]["name"]
        print(f"   - {tool_name}")
    
    print("\n✅ All tests completed!")
    print("\n💡 To test with actual API calls, set your OPENAI_API_KEY environment variable")
    print("   and run the game with: python engine.py")

if __name__ == "__main__":
    test_ai_system() 