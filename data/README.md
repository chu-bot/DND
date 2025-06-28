# DND Game Data Guide

This directory contains JSON files that define all the game content. Each file follows a specific structure and contains examples of how to store different types of game data.

## 📁 File Structure

```
data/
├── skills.json      # Player abilities and spells
├── items.json       # Equipment, weapons, consumables
├── quests.json      # Missions and objectives
├── locations.json   # Areas and places to explore
├── blueprints.json  # Crafting recipes
├── dialogues.json   # NPC conversations
└── conversations.json # Dialogue trees
```

## 🎯 Skills (skills.json)

**Purpose:** Define player abilities, spells, and special actions.

**Structure:**
```json
{
  "skill_id": {
    "id": "skill_id",
    "name": "Display Name",
    "description": "What the skill does",
    "skill_type": "active|passive",
    "target": "enemies|one_enemy|allies|self|all",
    "range": 60,
    "area_of_effect": 20,
    "cost": 3
  }
}
```

**Valid Values:**
- `skill_type`: `"active"` (requires action) or `"passive"` (always active)
- `target`: `"enemies"`, `"one_enemy"`, `"allies"`, `"self"`, `"all"`
- `range`: Distance in feet (0 for self-targeting)
- `area_of_effect`: Radius in feet (0 for single target)
- `cost`: Mana/energy cost (0 for passive skills)

## 🗡️ Items (items.json)

**Purpose:** Define equipment, weapons, armor, and consumables.

**Structure:**
```json
{
  "item_id": {
    "id": "item_id",
    "name": "Display Name",
    "description": "What the item is",
    "cost": 50,
    "rarity": "common|uncommon|rare|epic|legendary",
    "weight": 3.0,
    "skill": "skill_id|null"
  }
}
```

**Valid Values:**
- `rarity`: `"common"`, `"uncommon"`, `"rare"`, `"epic"`, `"legendary"`
- `skill`: ID of a skill the item grants, or `null`
- `cost`: Gold value
- `weight`: Weight in pounds

## 📜 Quests (quests.json)

**Purpose:** Define missions, objectives, and rewards.

**Structure:**
```json
{
  "quest_id": {
    "id": "quest_id",
    "name": "Quest Name",
    "status": "not_started|in_progress|completed|failed",
    "description": "Quest description",
    "objectives": [
      {
        "id": "objective_id",
        "description": "What to do",
        "completed": false,
        "required_count": 3,
        "current_count": 0
      }
    ],
    "level": 1,
    "reward": {
      "gold": 100,
      "experience": 50,
      "items": ["item_id1", "item_id2"]
    }
  }
}
```

**Valid Values:**
- `status`: `"not_started"`, `"in_progress"`, `"completed"`, `"failed"`
- `level`: Recommended player level
- `reward`: Object containing gold, experience, and item IDs

## 🗺️ Locations (locations.json)

**Purpose:** Define areas, dungeons, towns, and their connections.

**Structure:**
```json
{
  "location_id": {
    "id": "location_id",
    "name": "Location Name",
    "description": "Detailed description",
    "entities_within": ["entity_id1", "entity_id2"],
    "sub_locations": ["sub_location_id1"],
    "quests": ["quest_id1", "quest_id2"]
  }
}
```

**Fields:**
- `entities_within`: List of entities currently in this location
- `sub_locations`: List of locations that can be reached from here
- `quests`: List of quests available in this location

## 🔨 Blueprints (blueprints.json)

**Purpose:** Define crafting recipes and requirements.

**Structure:**
```json
{
  "blueprint_id": {
    "id": "blueprint_id",
    "name": "Recipe Name",
    "resulting_item": "item_id",
    "required_items": [
      {"item_id": 2},
      {"another_item": 1}
    ],
    "required_skills": ["skill_id1"],
    "location_needed": "location_id|null"
  }
}
```

**Fields:**
- `required_items`: Array of objects with item_id and quantity
- `required_skills`: List of skill IDs needed to craft
- `location_needed`: Location where crafting can be done (or null)

## 💬 Dialogues (dialogues.json)

**Purpose:** Define individual dialogue exchanges.

**Structure:**
```json
{
  "dialogue_id": {
    "id": "dialogue_id",
    "text": "What the NPC says",
    "sender_id": "npc_id",
    "receiver_id": "player_id",
    "condition": "optional_condition",
    "action": "optional_action"
  }
}
```

**Fields:**
- `condition`: Optional requirement that must be met
- `action`: Optional action to perform when dialogue triggers

## 🗣️ Conversations (conversations.json)

**Purpose:** Define dialogue trees and conversation flow.

**Structure:**
```json
{
  "conversation_id": {
    "id": "conversation_id",
    "root_dialogue": "dialogue_id",
    "dialogue_list": ["dialogue_id1", "dialogue_id2"]
  }
}
```

## ✨ Best Practices

### 1. **Consistent Naming**
- Use lowercase with underscores for IDs: `iron_sword`, `healing_touch`
- Use descriptive names: `goblin_hunt` not just `quest1`

### 2. **References**
- Always reference existing IDs when linking items
- Use `null` for optional fields, not empty strings

### 3. **Validation**
- Ensure all required fields are present
- Use valid enum values for fields like `rarity`, `skill_type`
- Check that referenced IDs exist in other files

### 4. **Organization**
- Group related items together
- Use comments in JSON for complex data
- Keep descriptions concise but informative

### 5. **Extensibility**
- Design for future additions
- Use arrays for variable-length data
- Include optional fields for future features

## 🔧 Adding New Content

1. **Create the JSON entry** following the structure above
2. **Add references** to other files if needed
3. **Test the data** by running the game
4. **Update documentation** if adding new fields

## 🚨 Common Mistakes

- **Missing required fields**: Ensure all required fields are present
- **Invalid references**: Check that all referenced IDs exist
- **Wrong data types**: Use numbers for numeric fields, strings for text
- **Inconsistent naming**: Follow the naming conventions
- **Circular references**: Avoid creating loops in references

## 📝 Example Workflow

1. **Design the content** on paper first
2. **Create the JSON entry** with all required fields
3. **Add to the appropriate file** in the data directory
4. **Test in-game** to ensure it works correctly
5. **Iterate and improve** based on gameplay feedback 