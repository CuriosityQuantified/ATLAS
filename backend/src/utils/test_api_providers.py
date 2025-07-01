#!/usr/bin/env python3
"""
ATLAS API Provider Testing Script
Tests all configured API providers to identify which are working
"""

import os
import sys
import asyncio
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.agui.handlers import AGUIEventBroadcaster

# Load environment variables
load_dotenv()

class APIProviderTester:
    """Tests various API providers for availability and functionality"""
    
    def __init__(self):
        self.results: Dict[str, Dict] = {}
        self.broadcaster = AGUIEventBroadcaster()
        self.task_id = f"api_test_{int(time.time())}"
        
    async def test_all_providers(self) -> Dict[str, Dict]:
        """Test all configured API providers"""
        print("🚀 Starting API Provider Tests...")
        print(f"Task ID: {self.task_id}")
        print("-" * 50)
        
        # Broadcast test start
        await self.broadcaster.broadcast_task_progress(
            self.task_id, 0.0, "initialization", "Starting API provider tests"
        )
        
        # Test each provider
        providers = [
            ("Anthropic", self.test_anthropic),
            ("OpenAI", self.test_openai),
            ("Groq", self.test_groq),
            ("Google", self.test_google),
            ("Tavily", self.test_tavily),
            ("GitHub", self.test_github),
            ("Firecrawl", self.test_firecrawl),
            ("OpenRouter", self.test_openrouter),
            ("HuggingFace", self.test_huggingface),
        ]
        
        total = len(providers)
        for idx, (name, test_func) in enumerate(providers):
            progress = (idx / total) * 100
            await self.broadcaster.broadcast_task_progress(
                self.task_id, progress, "testing", f"Testing {name}..."
            )
            
            print(f"\n📋 Testing {name}...")
            result = await test_func()
            self.results[name] = result
            
            # Broadcast individual result
            await self.broadcaster.broadcast_content_generated(
                self.task_id,
                f"api_tester_{name.lower()}",
                "json",
                len(json.dumps(result)),
                result.get("response_time", 0)
            )
            
            # Print result
            status = "✅ SUCCESS" if result["success"] else "❌ FAILED"
            print(f"   Status: {status}")
            if result["success"]:
                print(f"   Model: {result.get('model', 'N/A')}")
                print(f"   Response Time: {result.get('response_time', 0):.2f}s")
            else:
                print(f"   Error: {result.get('error', 'Unknown error')}")
        
        # Complete
        await self.broadcaster.broadcast_task_progress(
            self.task_id, 100.0, "completed", "All API provider tests completed"
        )
        
        self.print_summary()
        return self.results
    
    async def test_anthropic(self) -> Dict:
        """Test Anthropic Claude API"""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return {"success": False, "error": "No API key found", "provider": "Anthropic"}
        
        try:
            import anthropic
            
            start_time = time.time()
            client = anthropic.Anthropic(api_key=api_key)
            
            # Test with Claude 3.5 Haiku (fastest)
            response = client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=50,
                messages=[
                    {"role": "user", "content": "Say 'Hello ATLAS' in exactly 2 words."}
                ]
            )
            
            response_time = time.time() - start_time
            
            return {
                "success": True,
                "provider": "Anthropic",
                "model": "claude-3-5-haiku-20241022",
                "response": response.content[0].text,
                "response_time": response_time,
                "api_key_prefix": api_key[:10] + "..."
            }
            
        except Exception as e:
            return {
                "success": False,
                "provider": "Anthropic",
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def test_openai(self) -> Dict:
        """Test OpenAI GPT API"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return {"success": False, "error": "No API key found", "provider": "OpenAI"}
        
        try:
            import openai
            
            start_time = time.time()
            client = openai.OpenAI(api_key=api_key)
            
            # Test with GPT-4o-mini (fastest)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                max_tokens=50,
                messages=[
                    {"role": "user", "content": "Say 'Hello ATLAS' in exactly 2 words."}
                ]
            )
            
            response_time = time.time() - start_time
            
            return {
                "success": True,
                "provider": "OpenAI",
                "model": "gpt-4o-mini",
                "response": response.choices[0].message.content,
                "response_time": response_time,
                "api_key_prefix": api_key[:10] + "..."
            }
            
        except Exception as e:
            return {
                "success": False,
                "provider": "OpenAI",
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def test_groq(self) -> Dict:
        """Test Groq API"""
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return {"success": False, "error": "No API key found", "provider": "Groq"}
        
        try:
            import groq
            
            start_time = time.time()
            client = groq.Groq(api_key=api_key)
            
            # Test with Llama 3.1 8B (fastest)
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                max_tokens=50,
                messages=[
                    {"role": "user", "content": "Say 'Hello ATLAS' in exactly 2 words."}
                ]
            )
            
            response_time = time.time() - start_time
            
            return {
                "success": True,
                "provider": "Groq",
                "model": "llama-3.1-8b-instant",
                "response": response.choices[0].message.content,
                "response_time": response_time,
                "api_key_prefix": api_key[:10] + "..."
            }
            
        except Exception as e:
            return {
                "success": False,
                "provider": "Groq",
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def test_google(self) -> Dict:
        """Test Google Gemini API"""
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return {"success": False, "error": "No API key found", "provider": "Google"}
        
        try:
            import google.generativeai as genai
            
            start_time = time.time()
            genai.configure(api_key=api_key)
            
            # Test with Gemini 1.5 Flash (fastest)
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content("Say 'Hello ATLAS' in exactly 2 words.")
            
            response_time = time.time() - start_time
            
            return {
                "success": True,
                "provider": "Google",
                "model": "gemini-1.5-flash",
                "response": response.text,
                "response_time": response_time,
                "api_key_prefix": api_key[:10] + "..."
            }
            
        except Exception as e:
            return {
                "success": False,
                "provider": "Google",
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def test_tavily(self) -> Dict:
        """Test Tavily Search API"""
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            return {"success": False, "error": "No API key found", "provider": "Tavily"}
        
        try:
            import httpx
            
            start_time = time.time()
            
            # Test Tavily search
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": api_key,
                        "query": "ATLAS multi-agent system",
                        "max_results": 1,
                        "topic": "general"
                    },
                    timeout=10.0
                )
                
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "provider": "Tavily",
                    "model": "tavily-search",
                    "response": f"Found {len(data.get('results', []))} results",
                    "response_time": response_time,
                    "api_key_prefix": api_key[:10] + "..."
                }
            else:
                return {
                    "success": False,
                    "provider": "Tavily",
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "error_type": "HTTPError"
                }
                
        except Exception as e:
            return {
                "success": False,
                "provider": "Tavily",
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def test_github(self) -> Dict:
        """Test GitHub API (for Models access)"""
        api_key = os.getenv("GITHUB_API_KEY")
        if not api_key:
            return {"success": False, "error": "No API key found", "provider": "GitHub"}
        
        try:
            import httpx
            
            start_time = time.time()
            
            # Test GitHub API access
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.github.com/user",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Accept": "application/vnd.github.v3+json"
                    },
                    timeout=10.0
                )
                
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                user_data = response.json()
                return {
                    "success": True,
                    "provider": "GitHub",
                    "model": "github-api",
                    "response": f"Authenticated as: {user_data.get('login', 'Unknown')}",
                    "response_time": response_time,
                    "api_key_prefix": api_key[:10] + "...",
                    "note": "GitHub Models API requires additional setup"
                }
            else:
                return {
                    "success": False,
                    "provider": "GitHub",
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "error_type": "HTTPError"
                }
                
        except Exception as e:
            return {
                "success": False,
                "provider": "GitHub",
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def test_firecrawl(self) -> Dict:
        """Test Firecrawl API"""
        api_key = os.getenv("FIRECRAWL_API_KEY")
        if not api_key:
            return {"success": False, "error": "No API key found", "provider": "Firecrawl"}
        
        try:
            import httpx
            
            start_time = time.time()
            
            # Test Firecrawl scrape endpoint
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.firecrawl.dev/v0/scrape",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "url": "https://example.com",
                        "formats": ["markdown"]
                    },
                    timeout=15.0
                )
                
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "provider": "Firecrawl",
                    "model": "firecrawl-scraper",
                    "response": "Successfully scraped example.com",
                    "response_time": response_time,
                    "api_key_prefix": api_key[:10] + "..."
                }
            else:
                return {
                    "success": False,
                    "provider": "Firecrawl",
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "error_type": "HTTPError"
                }
                
        except Exception as e:
            return {
                "success": False,
                "provider": "Firecrawl",
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def test_openrouter(self) -> Dict:
        """Test OpenRouter API"""
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            return {"success": False, "error": "No API key found", "provider": "OpenRouter"}
        
        try:
            import httpx
            
            start_time = time.time()
            
            # Test OpenRouter with auto model selection
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://atlas.local",
                        "X-Title": "ATLAS Testing"
                    },
                    json={
                        "model": "auto",  # Let OpenRouter choose
                        "messages": [
                            {"role": "user", "content": "Say 'Hello ATLAS' in exactly 2 words."}
                        ],
                        "max_tokens": 50
                    },
                    timeout=15.0
                )
                
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "provider": "OpenRouter",
                    "model": data.get("model", "auto"),
                    "response": data["choices"][0]["message"]["content"],
                    "response_time": response_time,
                    "api_key_prefix": api_key[:10] + "..."
                }
            else:
                return {
                    "success": False,
                    "provider": "OpenRouter",
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "error_type": "HTTPError"
                }
                
        except Exception as e:
            return {
                "success": False,
                "provider": "OpenRouter",
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def test_huggingface(self) -> Dict:
        """Test HuggingFace Inference API"""
        api_key = os.getenv("HUGGINGFACE_API_KEY")
        if not api_key:
            return {"success": False, "error": "No API key found", "provider": "HuggingFace"}
        
        try:
            import httpx
            
            start_time = time.time()
            
            # Test with a small, fast model
            model_id = "microsoft/Phi-3-mini-4k-instruct"
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://api-inference.huggingface.co/models/{model_id}",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "inputs": "Say 'Hello ATLAS' in exactly 2 words.",
                        "parameters": {
                            "max_new_tokens": 50,
                            "temperature": 0.1
                        }
                    },
                    timeout=20.0
                )
                
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                # HF returns different formats, handle accordingly
                if isinstance(data, list) and len(data) > 0:
                    text_response = data[0].get("generated_text", "")
                else:
                    text_response = str(data)
                    
                return {
                    "success": True,
                    "provider": "HuggingFace",
                    "model": model_id,
                    "response": text_response,
                    "response_time": response_time,
                    "api_key_prefix": api_key[:10] + "..."
                }
            else:
                return {
                    "success": False,
                    "provider": "HuggingFace",
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "error_type": "HTTPError"
                }
                
        except Exception as e:
            return {
                "success": False,
                "provider": "HuggingFace",
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    def print_summary(self):
        """Print a summary of all test results"""
        print("\n" + "=" * 60)
        print("📊 API PROVIDER TEST SUMMARY")
        print("=" * 60)
        
        working = []
        failed = []
        
        for provider, result in self.results.items():
            if result["success"]:
                working.append((provider, result))
            else:
                failed.append((provider, result))
        
        # Print working providers
        print(f"\n✅ WORKING PROVIDERS ({len(working)}/{len(self.results)}):")
        print("-" * 40)
        for provider, result in working:
            print(f"  • {provider}")
            print(f"    - Model: {result.get('model', 'N/A')}")
            print(f"    - Response Time: {result.get('response_time', 0):.2f}s")
            print(f"    - API Key: {result.get('api_key_prefix', 'N/A')}")
        
        # Print failed providers
        print(f"\n❌ FAILED PROVIDERS ({len(failed)}/{len(self.results)}):")
        print("-" * 40)
        for provider, result in failed:
            print(f"  • {provider}")
            print(f"    - Error: {result.get('error', 'Unknown error')}")
            print(f"    - Type: {result.get('error_type', 'Unknown')}")
        
        # Print recommendations
        print("\n🎯 RECOMMENDATIONS:")
        print("-" * 40)
        if working:
            fastest = min(working, key=lambda x: x[1].get('response_time', float('inf')))
            print(f"  • Fastest Provider: {fastest[0]} ({fastest[1]['response_time']:.2f}s)")
            
            # Recommend based on capabilities
            if any(p[0] == "Anthropic" for p in working):
                print("  • Best for Complex Tasks: Anthropic Claude")
            if any(p[0] == "Groq" for p in working):
                print("  • Best for Speed: Groq (LPU acceleration)")
            if any(p[0] == "Tavily" for p in working):
                print("  • Web Search Available: Tavily")
        else:
            print("  • No working providers found!")
            print("  • Please check your .env file and API keys")
        
        print("\n" + "=" * 60)


async def main():
    """Main entry point"""
    tester = APIProviderTester()
    
    try:
        results = await tester.test_all_providers()
        
        # Save results to file
        output_file = f"api_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Results saved to: {output_file}")
        
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())