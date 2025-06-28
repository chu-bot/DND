from flask import Flask, render_template, request, jsonify, redirect, url_for
from game_types import *
from engine import GameEngine
from image import ImageGenerator, setup_image_generation, generate_game_images
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'dnd_game_secret_key'

# Global game instance
game = None
image_gen = ImageGenerator()

class WebGameEngine(GameEngine):
    def __init__(self):
        super().__init__()
        self.game_log = []
        self.current_images = []
    
    def log_event(self, event_type: str, message: str, image_url: str = None):
        """Log game events for the web interface"""
        log_entry = {
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'type': event_type,
            'message': message,
            'image_url': image_url
        }
        self.game_log.append(log_entry)
        if image_url:
            self.current_images.append(image_url)
    
    def move_to_location(self, location_id: str) -> bool:
        """Override to add logging"""
        result = super().move_to_location(location_id)
        if result and self.images_enabled:
            location = self.get_current_location()
            cached_url = image_gen.get_cached_image(f"location_{location_id}")
            if cached_url:
                self.log_event('location', f"Entered {location.name}", cached_url)
        return result
    
    def use_skill(self, skill_id: str, target_id: str = None) -> bool:
        """Override to add logging"""
        result = super().use_skill(skill_id, target_id)
        if result and self.images_enabled:
            skill = self.skills[skill_id]
            cached_url = image_gen.get_cached_image(f"skill_{skill_id}")
            if cached_url:
                self.log_event('skill', f"Used {skill.name}", cached_url)
        return result
    
    def add_item_to_inventory(self, item_id: str) -> bool:
        """Override to add logging"""
        result = super().add_item_to_inventory(item_id)
        if result and self.images_enabled:
            item = self.items[item_id]
            cached_url = image_gen.get_cached_image(f"item_{item_id}")
            if cached_url:
                self.log_event('item', f"Obtained {item.name}", cached_url)
        return result
    
    def start_quest(self, quest_id: str) -> bool:
        """Override to add logging"""
        result = super().start_quest(quest_id)
        if result and self.images_enabled:
            quest = self.quests[quest_id]
            cached_url = image_gen.get_cached_image(f"quest_{quest_id}")
            if cached_url:
                self.log_event('quest', f"Started {quest.name}", cached_url)
        return result

def initialize_game():
    """Initialize the game with web interface"""
    global game
    game = WebGameEngine()
    
    # Setup image generation
    if os.path.exists('.env'):
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key and api_key != "your_openai_api_key_here":
            image_gen.set_api_key(api_key)
            game.images_enabled = True
            game.log_event('system', 'Image generation enabled!')
        else:
            game.log_event('system', 'Image generation disabled - no API key found')
    else:
        game.log_event('system', 'Image generation disabled - no .env file found')

@app.route('/')
def index():
    """Main game interface"""
    if not game:
        initialize_game()
    
    player = game.get_player()
    location = game.get_current_location()
    
    return render_template('game.html', 
                         player=player, 
                         location=location,
                         game_log=game.game_log[-10:],  # Last 10 events
                         current_images=game.current_images[-5:])  # Last 5 images

@app.route('/api/status')
def get_status():
    """Get current game status as JSON"""
    if not game:
        return jsonify({'error': 'Game not initialized'})
    
    player = game.get_player()
    location = game.get_current_location()
    
    return jsonify({
        'player': {
            'name': player.name,
            'level': player.stats.level,
            'health': player.stats.health,
            'max_health': player.stats.max_health,
            'mana': player.stats.mana,
            'max_mana': player.stats.max_mana,
            'experience': player.stats.experience
        },
        'location': {
            'name': location.name,
            'description': location.description
        },
        'inventory': [game.items[item_id] for item_id in player.inventory],
        'skills': [game.skills[skill_id] for skill_id in player.skills],
        'quests': [game.quests[quest_id] for quest_id in player.quests_in_progress]
    })

@app.route('/api/action', methods=['POST'])
def perform_action():
    """Perform a game action"""
    if not game:
        return jsonify({'error': 'Game not initialized'})
    
    data = request.get_json()
    action = data.get('action')
    
    if action == 'move':
        location_id = data.get('location')
        if game.move_to_location(location_id):
            return jsonify({'success': True, 'message': f'Moved to {game.get_current_location().name}'})
        else:
            return jsonify({'success': False, 'message': 'Invalid location'})
    
    elif action == 'use_skill':
        skill_id = data.get('skill')
        if game.use_skill(skill_id):
            return jsonify({'success': True, 'message': f'Used skill {skill_id}'})
        else:
            return jsonify({'success': False, 'message': 'Cannot use skill'})
    
    elif action == 'add_item':
        item_id = data.get('item')
        if game.add_item_to_inventory(item_id):
            return jsonify({'success': True, 'message': f'Added {item_id} to inventory'})
        else:
            return jsonify({'success': False, 'message': 'Cannot add item'})
    
    elif action == 'start_quest':
        quest_id = data.get('quest')
        if game.start_quest(quest_id):
            return jsonify({'success': True, 'message': f'Started quest {quest_id}'})
        else:
            return jsonify({'success': False, 'message': 'Cannot start quest'})
    
    elif action == 'combat':
        if game.simulate_combat():
            return jsonify({'success': True, 'message': 'Combat completed successfully'})
        else:
            return jsonify({'success': False, 'message': 'Combat failed'})
    
    elif action == 'levelup':
        if game.level_up_player():
            return jsonify({'success': True, 'message': 'Level up successful'})
        else:
            return jsonify({'success': False, 'message': 'Level up failed'})
    
    return jsonify({'error': 'Unknown action'})

@app.route('/api/locations')
def get_locations():
    """Get available locations"""
    if not game:
        return jsonify({'error': 'Game not initialized'})
    
    return jsonify({
        'locations': list(game.locations.keys()),
        'current': game.current_location
    })

@app.route('/api/items')
def get_items():
    """Get available items"""
    if not game:
        return jsonify({'error': 'Game not initialized'})
    
    return jsonify({
        'items': list(game.items.keys())
    })

@app.route('/api/quests')
def get_quests():
    """Get available quests"""
    if not game:
        return jsonify({'error': 'Game not initialized'})
    
    return jsonify({
        'quests': list(game.quests.keys())
    })

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    # Create the HTML template
    create_html_template()
    
    print("Starting DND Web Interface...")
    print("Open your browser to: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)

def create_html_template():
    """Create the HTML template for the game interface"""
    html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DND Adventure Game</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: #fff;
            min-height: 100vh;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            display: grid;
            grid-template-columns: 300px 1fr 300px;
            grid-template-rows: auto 1fr auto;
            gap: 20px;
            height: 100vh;
        }
        
        .header {
            grid-column: 1 / -1;
            background: rgba(0, 0, 0, 0.3);
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }
        
        .sidebar {
            background: rgba(0, 0, 0, 0.4);
            padding: 20px;
            border-radius: 10px;
            overflow-y: auto;
        }
        
        .main-content {
            background: rgba(0, 0, 0, 0.4);
            padding: 20px;
            border-radius: 10px;
            overflow-y: auto;
        }
        
        .inventory {
            background: rgba(0, 0, 0, 0.4);
            padding: 20px;
            border-radius: 10px;
            overflow-y: auto;
        }
        
        .status-bar {
            grid-column: 1 / -1;
            background: rgba(0, 0, 0, 0.3);
            padding: 15px;
            border-radius: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .health-bar, .mana-bar {
            width: 200px;
            height: 20px;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 10px;
            overflow: hidden;
        }
        
        .health-fill {
            height: 100%;
            background: linear-gradient(90deg, #ff4757, #ff3742);
            transition: width 0.3s ease;
        }
        
        .mana-fill {
            height: 100%;
            background: linear-gradient(90deg, #3742fa, #2f3542);
            transition: width 0.3s ease;
        }
        
        .game-log {
            background: rgba(0, 0, 0, 0.2);
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 15px;
            max-height: 300px;
            overflow-y: auto;
        }
        
        .log-entry {
            margin-bottom: 8px;
            padding: 8px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 5px;
            border-left: 3px solid #ffa502;
        }
        
        .image-display {
            text-align: center;
            margin: 15px 0;
        }
        
        .image-display img {
            max-width: 100%;
            max-height: 300px;
            border-radius: 8px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        }
        
        .inventory-item {
            background: rgba(255, 255, 255, 0.1);
            padding: 10px;
            margin-bottom: 10px;
            border-radius: 5px;
            border-left: 3px solid #ffa502;
        }
        
        .skill-item {
            background: rgba(255, 255, 255, 0.1);
            padding: 10px;
            margin-bottom: 10px;
            border-radius: 5px;
            border-left: 3px solid #3742fa;
        }
        
        .button {
            background: linear-gradient(45deg, #ffa502, #ff6348);
            color: white;
            border: none;
            padding: 10px 15px;
            border-radius: 5px;
            cursor: pointer;
            margin: 5px;
            transition: transform 0.2s;
        }
        
        .button:hover {
            transform: translateY(-2px);
        }
        
        .button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .rarity-common { border-left-color: #95a5a6; }
        .rarity-uncommon { border-left-color: #27ae60; }
        .rarity-rare { border-left-color: #3498db; }
        .rarity-epic { border-left-color: #9b59b6; }
        .rarity-legendary { border-left-color: #f39c12; }
        
        .location-info {
            background: rgba(255, 255, 255, 0.1);
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 15px;
        }
        
        .quest-info {
            background: rgba(255, 255, 255, 0.1);
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 15px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎲 DND Adventure Game</h1>
            <p>Embark on an epic journey with AI-generated images!</p>
        </div>
        
        <div class="sidebar">
            <h3>🎯 Game Actions</h3>
            <div class="game-log" id="gameLog">
                <!-- Game log entries will be populated here -->
            </div>
            
            <h3>🗺️ Locations</h3>
            <div id="locationButtons">
                <!-- Location buttons will be populated here -->
            </div>
            
            <h3>⚔️ Combat & Skills</h3>
            <button class="button" onclick="performAction('combat')">Fight Goblin</button>
            <button class="button" onclick="performAction('levelup')">Level Up</button>
            <div id="skillButtons">
                <!-- Skill buttons will be populated here -->
            </div>
        </div>
        
        <div class="main-content">
            <div class="location-info">
                <h3>📍 Current Location</h3>
                <div id="locationInfo">
                    <!-- Location info will be populated here -->
                </div>
            </div>
            
            <div class="image-display" id="imageDisplay">
                <!-- Generated images will be displayed here -->
            </div>
            
            <div class="quest-info">
                <h3>📜 Quests</h3>
                <div id="questInfo">
                    <!-- Quest info will be populated here -->
                </div>
            </div>
        </div>
        
        <div class="inventory">
            <h3>🎒 Inventory</h3>
            <div id="inventoryList">
                <!-- Inventory items will be populated here -->
            </div>
            
            <h3>🔮 Skills</h3>
            <div id="skillList">
                <!-- Skills will be populated here -->
            </div>
            
            <h3>➕ Add Items</h3>
            <div id="itemButtons">
                <!-- Item buttons will be populated here -->
            </div>
        </div>
        
        <div class="status-bar">
            <div>
                <strong id="playerName">Hero</strong> - Level <span id="playerLevel">1</span>
                (XP: <span id="playerXP">0</span>)
            </div>
            <div>
                <span>❤️ Health: </span>
                <div class="health-bar">
                    <div class="health-fill" id="healthBar"></div>
                </div>
                <span id="healthText">100/100</span>
            </div>
            <div>
                <span>🔮 Mana: </span>
                <div class="mana-bar">
                    <div class="mana-fill" id="manaBar"></div>
                </div>
                <span id="manaText">50/50</span>
            </div>
        </div>
    </div>

    <script>
        // Game state
        let gameState = {};
        
        // Initialize the game
        async function initGame() {
            await updateStatus();
            await loadLocations();
            await loadItems();
            await loadQuests();
            updateDisplay();
        }
        
        // Update game status
        async function updateStatus() {
            try {
                const response = await fetch('/api/status');
                gameState = await response.json();
                updateStatusDisplay();
            } catch (error) {
                console.error('Error updating status:', error);
            }
        }
        
        // Update status display
        function updateStatusDisplay() {
            if (gameState.player) {
                document.getElementById('playerName').textContent = gameState.player.name;
                document.getElementById('playerLevel').textContent = gameState.player.level;
                document.getElementById('playerXP').textContent = gameState.player.experience;
                
                const healthPercent = (gameState.player.health / gameState.player.max_health) * 100;
                const manaPercent = (gameState.player.mana / gameState.player.max_mana) * 100;
                
                document.getElementById('healthBar').style.width = healthPercent + '%';
                document.getElementById('manaBar').style.width = manaPercent + '%';
                document.getElementById('healthText').textContent = `${gameState.player.health}/${gameState.player.max_health}`;
                document.getElementById('manaText').textContent = `${gameState.player.mana}/${gameState.player.max_mana}`;
            }
        }
        
        // Load locations
        async function loadLocations() {
            try {
                const response = await fetch('/api/locations');
                const data = await response.json();
                
                const container = document.getElementById('locationButtons');
                container.innerHTML = '';
                
                data.locations.forEach(location => {
                    const button = document.createElement('button');
                    button.className = 'button';
                    button.textContent = location;
                    button.onclick = () => performAction('move', { location: location });
                    container.appendChild(button);
                });
            } catch (error) {
                console.error('Error loading locations:', error);
            }
        }
        
        // Load items
        async function loadItems() {
            try {
                const response = await fetch('/api/items');
                const data = await response.json();
                
                const container = document.getElementById('itemButtons');
                container.innerHTML = '';
                
                data.items.forEach(item => {
                    const button = document.createElement('button');
                    button.className = 'button';
                    button.textContent = `Add ${item}`;
                    button.onclick = () => performAction('add_item', { item: item });
                    container.appendChild(button);
                });
            } catch (error) {
                console.error('Error loading items:', error);
            }
        }
        
        // Load quests
        async function loadQuests() {
            try {
                const response = await fetch('/api/quests');
                const data = await response.json();
                
                const container = document.getElementById('questInfo');
                container.innerHTML = '';
                
                data.quests.forEach(quest => {
                    const button = document.createElement('button');
                    button.className = 'button';
                    button.textContent = `Start ${quest}`;
                    button.onclick = () => performAction('start_quest', { quest: quest });
                    container.appendChild(button);
                });
            } catch (error) {
                console.error('Error loading quests:', error);
            }
        }
        
        // Perform game action
        async function performAction(action, data = {}) {
            try {
                const response = await fetch('/api/action', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ action, ...data })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    addLogEntry('success', result.message);
                    await updateStatus();
                    updateDisplay();
                } else {
                    addLogEntry('error', result.message);
                }
            } catch (error) {
                console.error('Error performing action:', error);
                addLogEntry('error', 'Action failed');
            }
        }
        
        // Add log entry
        function addLogEntry(type, message) {
            const log = document.getElementById('gameLog');
            const entry = document.createElement('div');
            entry.className = `log-entry ${type}`;
            entry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
            log.appendChild(entry);
            log.scrollTop = log.scrollHeight;
        }
        
        // Update display
        function updateDisplay() {
            updateInventory();
            updateSkills();
            updateLocationInfo();
            updateQuestInfo();
        }
        
        // Update inventory display
        function updateInventory() {
            const container = document.getElementById('inventoryList');
            container.innerHTML = '';
            
            if (gameState.inventory) {
                gameState.inventory.forEach(item => {
                    const div = document.createElement('div');
                    div.className = `inventory-item rarity-${item.rarity}`;
                    div.innerHTML = `
                        <strong>${item.name}</strong><br>
                        <small>${item.description}</small><br>
                        <small>Cost: ${item.cost} | Weight: ${item.weight}</small>
                    `;
                    container.appendChild(div);
                });
            }
        }
        
        // Update skills display
        function updateSkills() {
            const container = document.getElementById('skillList');
            container.innerHTML = '';
            
            if (gameState.skills) {
                gameState.skills.forEach(skill => {
                    const div = document.createElement('div');
                    div.className = 'skill-item';
                    div.innerHTML = `
                        <strong>${skill.name}</strong><br>
                        <small>${skill.description}</small><br>
                        <small>Cost: ${skill.cost} mana | Range: ${skill.range}</small>
                    `;
                    container.appendChild(div);
                });
            }
        }
        
        // Update location info
        function updateLocationInfo() {
            const container = document.getElementById('locationInfo');
            if (gameState.location) {
                container.innerHTML = `
                    <h4>${gameState.location.name}</h4>
                    <p>${gameState.location.description}</p>
                `;
            }
        }
        
        // Update quest info
        function updateQuestInfo() {
            const container = document.getElementById('questInfo');
            container.innerHTML = '';
            
            if (gameState.quests) {
                gameState.quests.forEach(quest => {
                    const div = document.createElement('div');
                    div.className = 'quest-info';
                    div.innerHTML = `
                        <h4>${quest.name}</h4>
                        <p>${quest.description}</p>
                        <small>Level: ${quest.level}</small>
                    `;
                    container.appendChild(div);
                });
            }
        }
        
        // Initialize when page loads
        document.addEventListener('DOMContentLoaded', initGame);
        
        // Auto-refresh every 5 seconds
        setInterval(updateStatus, 5000);
    </script>
</body>
</html>'''
    
    with open('templates/game.html', 'w') as f:
        f.write(html_content) 