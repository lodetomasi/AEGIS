#!/usr/bin/env python3
"""
Quick test to verify all models are working with rate limit handling
"""

import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from openrouter_client import OpenRouterClient

def test_models():
    """Test each model with a simple prompt"""
    load_dotenv()
    
    # Initialize client with rate limiting
    client = OpenRouterClient(rate_limit_delay=3.0)  # 3 second delay between requests
    
    models = [
        "google/gemini-2.0-flash-exp:free",
        "meta-llama/llama-3.3-70b-instruct:free",
        "deepseek/deepseek-chat-v3-0324:free",
    ]
    
    print("🧪 Testing models with rate limiting...\n")
    
    for model in models:
        print(f"Testing {model}...")
        try:
            response = client.chat_completion(
                model=model,
                messages=[{"role": "user", "content": "Say 'Hello AETHER' in exactly 3 words"}],
                temperature=0,
                max_tokens=50,
                use_cache=False
            )
            print(f"✅ Success: {response.content[:50]}")
            print(f"   Latency: {response.latency_ms:.0f}ms\n")
        except Exception as e:
            print(f"❌ Failed: {str(e)}\n")
    
    print("✅ Test complete!")

if __name__ == "__main__":
    test_models()