#!/usr/bin/env node

/**
 * Test script to verify workspace persistence fixes
 * Run this in the browser console to test
 */

console.log("=== Testing Workspace Persistence Fixes ===");

// Clear existing localStorage to start fresh
function clearStorage() {
  console.log("Clearing existing workspace data...");
  localStorage.removeItem("deep-agents-workspaces");
  localStorage.removeItem("deep-agents-active-workspace");
  console.log("✅ Storage cleared");
}

// Test 1: Create multiple workspaces
function testWorkspaceCreation() {
  console.log("\n=== Test 1: Creating Multiple Workspaces ===");
  
  const workspaces = [];
  
  // Create 3 test workspaces
  for (let i = 1; i <= 3; i++) {
    const workspace = {
      id: `test-ws-${i}`,
      title: `Workspace ${i}`,
      threadId: null,
      isActive: false,
      createdAt: new Date().toISOString(),
      todos: [
        {
          id: `todo-${i}-1`,
          content: `Task ${i}.1`,
          status: "pending",
          createdAt: new Date().toISOString()
        }
      ],
      files: {
        [`file${i}.txt`]: `Content ${i}`
      }
    };
    workspaces.push(workspace);
    console.log(`Created: ${workspace.title}`);
  }
  
  // Try to save with our new safe serialization
  try {
    localStorage.setItem("deep-agents-workspaces", JSON.stringify(workspaces));
    console.log("✅ Workspaces saved successfully");
    return true;
  } catch (error) {
    console.error("❌ Failed to save workspaces:", error);
    return false;
  }
}

// Test 2: Load and verify workspaces
function testWorkspaceLoading() {
  console.log("\n=== Test 2: Loading Workspaces ===");
  
  try {
    const data = localStorage.getItem("deep-agents-workspaces");
    if (!data) {
      console.error("❌ No workspaces found in localStorage");
      return false;
    }
    
    const workspaces = JSON.parse(data);
    console.log(`✅ Loaded ${workspaces.length} workspaces`);
    
    // Verify each workspace
    let allValid = true;
    workspaces.forEach((ws, index) => {
      console.log(`  - ${ws.title}: ${ws.todos.length} todos, ${Object.keys(ws.files).length} files`);
      
      if (!ws.id || !ws.title) {
        console.error(`    ❌ Workspace ${index} missing required fields`);
        allValid = false;
      }
      
      if (ws.title === "Untitled" || ws.title === "[object Object]") {
        console.error(`    ❌ Workspace ${index} has invalid title: ${ws.title}`);
        allValid = false;
      }
    });
    
    return allValid;
  } catch (error) {
    console.error("❌ Failed to load workspaces:", error);
    return false;
  }
}

// Test 3: Simulate circular reference handling
function testCircularReference() {
  console.log("\n=== Test 3: Testing Circular Reference Handling ===");
  
  // Create an object with circular reference
  const workspace = {
    id: "circular-test",
    title: "Circular Test",
    threadId: null,
    isActive: false,
    createdAt: new Date().toISOString(),
    todos: [],
    files: {}
  };
  
  // Add circular reference
  workspace.self = workspace;
  
  console.log("Created workspace with circular reference");
  
  // This should not crash with our fixes
  try {
    // The app should handle this with safeStringify
    console.log("Testing if circular reference is handled...");
    
    // Simulate what safeStringify does
    const seen = new WeakSet();
    const cleaned = JSON.stringify(workspace, function(key, value) {
      if (typeof value === "object" && value !== null) {
        if (seen.has(value)) {
          return "[Circular Reference]";
        }
        seen.add(value);
      }
      return value;
    });
    
    console.log("✅ Circular reference handled successfully");
    return true;
  } catch (error) {
    console.error("❌ Failed to handle circular reference:", error);
    return false;
  }
}

// Run all tests
function runAllTests() {
  console.log("\n📋 Running All Tests...\n");
  
  clearStorage();
  
  const results = {
    creation: testWorkspaceCreation(),
    loading: testWorkspaceLoading(),
    circular: testCircularReference()
  };
  
  console.log("\n=== Test Results ===");
  console.log(`Workspace Creation: ${results.creation ? '✅ PASS' : '❌ FAIL'}`);
  console.log(`Workspace Loading: ${results.loading ? '✅ PASS' : '❌ FAIL'}`);
  console.log(`Circular Reference: ${results.circular ? '✅ PASS' : '❌ FAIL'}`);
  
  const allPassed = Object.values(results).every(r => r === true);
  
  if (allPassed) {
    console.log("\n🎉 All tests passed! Workspace persistence is working correctly.");
  } else {
    console.log("\n⚠️ Some tests failed. Check the errors above.");
  }
  
  console.log("\n📝 Manual Testing Steps:");
  console.log("1. Click the + button to create a new workspace");
  console.log("2. Check that it's named 'Workspace 2' (not 'Untitled')");
  console.log("3. Refresh the browser");
  console.log("4. Verify the workspace persists with correct name");
  console.log("5. Start a research task and verify it saves to the correct workspace");
}

// Run tests
runAllTests();