#!/usr/bin/env python3
"""Test the ask_user_question interaction flow"""

import asyncio
from playwright.async_api import async_playwright
import time

async def test_question_interaction():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # Navigate to the app
        await page.goto("http://localhost:3000")
        
        # Wait for page to load
        await page.wait_for_selector('[data-test="chat-input"]', timeout=10000)
        
        print("✅ Page loaded successfully")
        
        # Test 1: Simple greeting - should NOT trigger ask_user_question
        print("\n📝 Test 1: Simple greeting")
        await page.fill('[data-test="chat-input"]', "Hello")
        await page.press('[data-test="chat-input"]', 'Enter')
        
        # Wait for response
        await asyncio.sleep(3)
        
        # Check if we see a respond_to_user message (not a question box)
        user_response = await page.query_selector('.userResponse')
        if user_response:
            print("✅ Agent responded with progress update (respond_to_user)")
        
        # Check if there's NO question box
        question_box = await page.query_selector('.questionBox')
        if not question_box:
            print("✅ No question box shown for simple greeting (correct)")
        else:
            print("❌ Unexpected question box for simple greeting")
        
        # Test 2: Ambiguous query - should trigger ask_user_question
        print("\n📝 Test 2: Ambiguous query")
        await page.fill('[data-test="chat-input"]', "Tell me about the latest developments")
        await page.press('[data-test="chat-input"]', 'Enter')
        
        # Wait for potential question box
        await asyncio.sleep(5)
        
        # Check if question box appears
        question_box = await page.wait_for_selector('.questionBox', timeout=10000)
        if question_box:
            print("✅ Question box appeared for ambiguous query")
            
            # Check if input field is present
            question_input = await page.query_selector('.questionInput')
            if question_input:
                print("✅ Input field is present in question box")
                
                # Type an answer
                await question_input.fill("I'm interested in AI developments in 2024")
                await question_input.press('Enter')
                print("✅ Submitted answer to clarifying question")
                
                # Wait for agent to process
                await asyncio.sleep(3)
        
        # Test 3: Complex research query
        print("\n📝 Test 3: Complex research query")
        await page.fill('[data-test="chat-input"]', "Research the impact of quantum computing on cybersecurity")
        await page.press('[data-test="chat-input"]', 'Enter')
        
        # Wait for response
        await asyncio.sleep(5)
        
        # Check for progress updates
        user_responses = await page.query_selector_all('.userResponse')
        if len(user_responses) > 0:
            print(f"✅ Agent sent {len(user_responses)} progress updates")
        
        # Check for tool calls
        tool_calls = await page.query_selector_all('[data-test^="tool-call-"]')
        if len(tool_calls) > 0:
            print(f"✅ Agent executed {len(tool_calls)} tool calls")
        
        print("\n🎉 All tests completed!")
        
        # Keep browser open for manual inspection
        print("Browser will stay open for 30 seconds for manual inspection...")
        await asyncio.sleep(30)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_question_interaction())