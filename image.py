import os
import requests
import base64
from typing import Optional, Dict, Any
import json
from datetime import datetime

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("python-dotenv not installed. Install with: pip install python-dotenv")
    print("Or manually set OPENAI_API_KEY environment variable.")


class ImageGenerator:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = "https://api.openai.com/v1/images/generations"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.image_cache: Dict[str, str] = {}
    
    def set_api_key(self, api_key: str):
        """Set the API key for image generation"""
        self.api_key = api_key
        self.headers["Authorization"] = f"Bearer {api_key}"
        print("API key set successfully!")
    
    def generate_image(self, prompt: str, size: str = "1024x1024", quality: str = "standard") -> Optional[str]:
        """Generate an image using ChatGPT's image generator"""
        if not self.api_key:
            print("Error: No API key set. Use set_api_key() first.")
            return None
        
        try:
            payload = {
                "model": "dall-e-3",
                "prompt": prompt,
                "size": size,
                "quality": quality,
                "n": 1
            }
            
            response = requests.post(self.base_url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            if data.get("data") and len(data["data"]) > 0:
                image_url = data["data"][0]["url"]
                print(f"Generated image: {prompt}")
                return image_url
            else:
                print("No image generated in response")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}")
            return None
        except Exception as e:
            print(f"Image generation failed: {e}")
            return None
    
    def generate_character_portrait(self, character_name: str, description: str, level: int) -> Optional[str]:
        """Generate a character portrait"""
        prompt = f"Fantasy RPG character portrait: {character_name}, level {level} adventurer. {description}. Detailed, high-quality fantasy art style, dramatic lighting, suitable for a D&D game."
        return self.generate_image(prompt)
    
    def generate_location_image(self, location_name: str, description: str) -> Optional[str]:
        """Generate a location image"""
        prompt = f"Fantasy RPG location: {location_name}. {description}. Atmospheric, detailed fantasy environment, suitable for a D&D game setting."
        return self.generate_image(prompt)
    
    def generate_item_image(self, item_name: str, description: str, rarity: str) -> Optional[str]:
        """Generate an item image"""
        prompt = f"Fantasy RPG item: {item_name}. {description}. {rarity} quality. Detailed fantasy weapon/equipment art, suitable for a D&D game."
        return self.generate_image(prompt)
    
    def generate_skill_effect(self, skill_name: str, description: str) -> Optional[str]:
        """Generate a skill effect image"""
        prompt = f"Fantasy RPG spell effect: {skill_name}. {description}. Magical energy, particles, dramatic lighting, suitable for a D&D game spell effect."
        return self.generate_image(prompt)
    
    def generate_quest_scene(self, quest_name: str, description: str) -> Optional[str]:
        """Generate a quest scene image"""
        prompt = f"Fantasy RPG quest scene: {quest_name}. {description}. Epic fantasy scene, dramatic composition, suitable for a D&D game quest."
        return self.generate_image(prompt)
    
    def generate_combat_scene(self, player_name: str, enemy_name: str, location: str) -> Optional[str]:
        """Generate a combat scene image"""
        prompt = f"Fantasy RPG combat scene: {player_name} fighting {enemy_name} in {location}. Dynamic action, dramatic lighting, suitable for a D&D game combat encounter."
        return self.generate_image(prompt)
    
    def generate_loot_drop(self, item_name: str, rarity: str) -> Optional[str]:
        """Generate a loot drop scene"""
        prompt = f"Fantasy RPG loot drop: {item_name} ({rarity} quality) glowing with magical energy. Treasure chest or magical aura, suitable for a D&D game loot scene."
        return self.generate_image(prompt)
    
    def generate_level_up(self, character_name: str, new_level: int) -> Optional[str]:
        """Generate a level up celebration image"""
        prompt = f"Fantasy RPG level up: {character_name} reaching level {new_level}. Magical energy, glowing effects, celebration, suitable for a D&D game level up moment."
        return self.generate_image(prompt)
    
    def generate_dialogue_scene(self, speaker_name: str, location: str, mood: str) -> Optional[str]:
        """Generate a dialogue scene image"""
        prompt = f"Fantasy RPG dialogue scene: {speaker_name} in {location}. {mood} atmosphere, character interaction, suitable for a D&D game dialogue moment."
        return self.generate_image(prompt)
    
    def save_image_url(self, key: str, url: str):
        """Cache an image URL with a key"""
        self.image_cache[key] = url
    
    def get_cached_image(self, key: str) -> Optional[str]:
        """Get a cached image URL"""
        return self.image_cache.get(key)
    
    def export_image_log(self, filename: str = "image_log.json"):
        """Export the image cache to a JSON file"""
        try:
            with open(filename, 'w') as f:
                json.dump(self.image_cache, f, indent=2)
            print(f"Image log exported to {filename}")
        except Exception as e:
            print(f"Failed to export image log: {e}")


# Global image generator instance
image_gen = ImageGenerator()


def setup_image_generation():
    """Setup function to configure image generation"""
    # Check if images are enabled in environment
    if os.getenv("IMAGES_ENABLED", "false").lower() != "true":
        print("Image generation disabled in environment (IMAGES_ENABLED=false)")
        return False
    
    print("=== DND Image Generator Setup ===")
    print("This will generate images for key game moments using ChatGPT's image generator.")
    print("You'll need an OpenAI API key with access to DALL-E 3.")
    
    # Check if API key is already set in environment
    if image_gen.api_key and image_gen.api_key != "your_openai_api_key_here":
        print("✅ API key found in environment variables!")
        return True
    
    # Try to load from .env file
    if os.path.exists('.env'):
        print("📁 Found .env file")
        load_dotenv()
        env_key = os.getenv("OPENAI_API_KEY")
        if env_key and env_key != "your_openai_api_key_here":
            image_gen.set_api_key(env_key)
            print("✅ API key loaded from .env file!")
            return True
    
    # Prompt user for API key
    api_key = input("Enter your OpenAI API key (or press Enter to skip): ").strip()
    
    if api_key:
        image_gen.set_api_key(api_key)
        print("✅ Image generation enabled!")
        return True
    else:
        print("❌ Image generation disabled. Game will run without images.")
        return False


def generate_game_images(game_state: Dict[str, Any], event_type: str, **kwargs):
    """Generate appropriate images based on game events"""
    if not image_gen.api_key:
        return
    
    try:
        if event_type == "character_creation":
            # Generate character portrait
            character = kwargs.get('character')
            if character:
                url = image_gen.generate_character_portrait(
                    character.name,
                    f"Level {character.stats.level} adventurer with {len(character.skills)} skills",
                    character.stats.level
                )
                if url:
                    image_gen.save_image_url(f"character_{character.id}", url)
        
        elif event_type == "location_enter":
            # Generate location image
            location = kwargs.get('location')
            if location:
                url = image_gen.generate_location_image(location.name, location.description)
                if url:
                    image_gen.save_image_url(f"location_{location.id}", url)
        
        elif event_type == "item_obtained":
            # Generate item image
            item = kwargs.get('item')
            if item:
                url = image_gen.generate_item_image(item.name, item.description, item.rarity.value)
                if url:
                    image_gen.save_image_url(f"item_{item.id}", url)
        
        elif event_type == "skill_used":
            # Generate skill effect
            skill = kwargs.get('skill')
            if skill:
                url = image_gen.generate_skill_effect(skill.name, skill.description)
                if url:
                    image_gen.save_image_url(f"skill_{skill.id}", url)
        
        elif event_type == "quest_started":
            # Generate quest scene
            quest = kwargs.get('quest')
            if quest:
                url = image_gen.generate_quest_scene(quest.name, quest.description)
                if url:
                    image_gen.save_image_url(f"quest_{quest.id}", url)
        
        elif event_type == "combat_started":
            # Generate combat scene
            player = kwargs.get('player')
            enemy = kwargs.get('enemy')
            location = kwargs.get('location')
            if player and enemy and location:
                url = image_gen.generate_combat_scene(player.name, enemy, location.name)
                if url:
                    image_gen.save_image_url(f"combat_{datetime.now().strftime('%Y%m%d_%H%M%S')}", url)
        
        elif event_type == "level_up":
            # Generate level up celebration
            character = kwargs.get('character')
            new_level = kwargs.get('new_level')
            if character and new_level:
                url = image_gen.generate_level_up(character.name, new_level)
                if url:
                    image_gen.save_image_url(f"levelup_{character.id}_{new_level}", url)
        
        elif event_type == "dialogue_started":
            # Generate dialogue scene
            speaker = kwargs.get('speaker')
            location = kwargs.get('location')
            mood = kwargs.get('mood', 'neutral')
            if speaker and location:
                url = image_gen.generate_dialogue_scene(speaker, location.name, mood)
                if url:
                    image_gen.save_image_url(f"dialogue_{datetime.now().strftime('%Y%m%d_%H%M%S')}", url)
    
    except Exception as e:
        print(f"Image generation failed for {event_type}: {e}")


def display_image_url(url: str, description: str):
    """Display image URL with description"""
    if url:
        print(f"\n🖼️  {description}")
        print(f"📷 {url}")
        print("(Copy and paste the URL in your browser to view the image)")
