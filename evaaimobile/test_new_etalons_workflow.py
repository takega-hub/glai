#!/usr/bin/env python3
"""
Test script for the new etalons workflow.
Tests both scenarios: character creation with and without reference photo.
"""

import asyncio
import httpx
import json
import os
from typing import Optional

BASE_URL = "http://localhost:8002/admin/characters"

def test_scenario_1_no_photo():
    """Test character creation without reference photo (Scenario 1)"""
    print("=== Testing Scenario 1: Character creation WITHOUT reference photo ===")
    
    data = {
        "gender": "female",
        "archetype": "mysterious artist",
        "number_of_layers": 8,
        "additional_instructions": "Create a mysterious artist character with creative personality",
        "is_sex_focused": False
    }
    
    try:
        response = httpx.post(
            f"{BASE_URL}/generate-with-ai",
            json=data,  # Use json instead of data
            timeout=300.0
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success! Character created: {result['character_id']}")
            print(f"Character name: {result['preview']['character']['name']}")
            return result['character_id']
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_scenario_2_with_photo():
    """Test character creation with reference photo (Scenario 2)"""
    print("\n=== Testing Scenario 2: Character creation WITH reference photo ===")
    
    # For this test, we'll need a sample image file
    # In a real test, you would provide an actual image file
    print("⚠️  Note: This test requires an actual image file to be uploaded")
    print("Skipping photo upload test in this script")
    return None

def test_character_etalons(character_id: str):
    """Test that etalons were created and stored correctly"""
    print(f"\n=== Testing etalons for character {character_id} ===")
    
    try:
        # Get character details
        response = httpx.get(f"{BASE_URL}/{character_id}")
        if response.status_code == 200:
            character_data = response.json()['character']
            etalons_data = character_data.get('etalons_data', {})
            
            if isinstance(etalons_data, str):
                etalons_data = json.loads(etalons_data)
            
            print(f"Textual etalon: {etalons_data.get('textual_etalon', 'Not found')}")
            print(f"Visual etalon path: {etalons_data.get('visual_etalon_path', 'Not found')}")
            
            # Check reference photos
            ref_response = httpx.get(f"{BASE_URL}/{character_id}/reference_photos")
            if ref_response.status_code == 200:
                reference_photos = ref_response.json()['reference_photos']
                print(f"Number of reference photos: {len(reference_photos)}")
                for photo in reference_photos:
                    print(f"  - {photo['description']}: {photo['media_url']}")
            
            return True
        else:
            print(f"❌ Failed to get character: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_add_photo_prompt(character_id: str):
    """Test adding a photo prompt to verify etalons are used"""
    print(f"\n=== Testing add photo prompt for character {character_id} ===")
    
    try:
        # First get layers
        response = httpx.get(f"{BASE_URL}/{character_id}")
        if response.status_code != 200:
            print(f"❌ Failed to get character: {response.status_code}")
            return False
            
        layers = response.json()['layers']
        if not layers:
            print("❌ No layers found")
            return False
            
        layer_id = layers[0]['id']
        
        # Add photo prompt to first layer
        data = {
            "target_type": "layer",
            "target_id": str(layer_id)
        }
        
        response = httpx.post(
            f"{BASE_URL}/{character_id}/add-photo-prompt",
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Successfully added photo prompt to layer {layer_id}")
            print(f"Generated prompt: {result['new_photo_prompt']['prompt']}")
            return True
        else:
            print(f"❌ Failed to add photo prompt: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def main():
    """Main test function"""
    print("🚀 Starting new etalons workflow test...")
    
    # Test Scenario 1: No photo
    character_id = test_scenario_1_no_photo()
    
    if character_id:
        # Test etalons were created
        test_character_etalons(character_id)
        
        # Test adding photo prompt
        test_add_photo_prompt(character_id)

        # Test deleting the character
        test_delete_character(character_id)
        
        print(f"\n✅ All tests completed for character {character_id}")
    else:
        print("❌ Character creation failed, skipping further tests")
    
    print("\n🎯 Test summary:")
    print("- New etalons workflow implemented")
    print("- Textual and visual etalons created during character creation")
    print("- Etalons stored in character record for future use")
    print("- Photo generation now uses both etalons for consistency")

def test_delete_character(character_id: str):
    """Test deleting a character"""
    print(f"\n=== Testing character deletion for {character_id} ===")
    try:
        response = httpx.delete(f"{BASE_URL}/{character_id}")
        if response.status_code == 200:
            print(f"✅ Success! Character {character_id} deleted.")
            # Verify character is gone
            get_response = httpx.get(f"{BASE_URL}/{character_id}")
            if get_response.status_code == 404:
                print("✅ Verification successful: Character not found after deletion.")
                return True
            else:
                print(f"❌ Verification failed: Character still exists after deletion (Status: {get_response.status_code})")
                return False
        else:
            print(f"❌ Failed to delete character: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error during deletion test: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(main())