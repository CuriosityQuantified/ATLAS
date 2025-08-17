#!/usr/bin/env node

/**
 * Test script to verify workspace persistence
 * Run this in the browser console to test
 */

console.log("=== Testing Workspace Persistence ===");

// Function to create test workspace
function createTestWorkspace() {
  const testWorkspace = {
    id: "test-" + Date.now(),
    title: "Test Workspace " + new Date().toLocaleTimeString(),
    threadId: null,
    isActive: false,
    createdAt: new Date(),
    todos: [
      {
        id: "todo-1",
        content: "Test todo item",
        status: "pending",
        createdAt: new Date(),
        updatedAt: new Date()
      }
    ],
    files: {
      "test.txt": "Test content"
    }
  };
  
  console.log("Creating test workspace:", testWorkspace);
  
  // Get existing workspaces
  const existingData = localStorage.getItem("deep-agents-workspaces");
  let workspaces = [];
  
  if (existingData) {
    try {
      workspaces = JSON.parse(existingData);
      console.log("Existing workspaces:", workspaces.length);
    } catch (e) {
      console.error("Failed to parse existing workspaces:", e);
      workspaces = [];
    }
  }
  
  // Add test workspace
  workspaces.push(testWorkspace);
  
  // Try to save
  try {
    const jsonString = JSON.stringify(workspaces);
    localStorage.setItem("deep-agents-workspaces", jsonString);
    console.log("✅ Successfully saved workspace to localStorage");
    console.log("Saved data length:", jsonString.length);
    return true;
  } catch (error) {
    console.error("❌ Failed to save workspace:", error);
    return false;
  }
}

// Function to verify persistence
function verifyPersistence() {
  console.log("\n=== Verifying Persistence ===");
  
  try {
    const data = localStorage.getItem("deep-agents-workspaces");
    if (!data) {
      console.error("❌ No data found in localStorage");
      return false;
    }
    
    const workspaces = JSON.parse(data);
    console.log("✅ Successfully loaded workspaces from localStorage");
    console.log("Number of workspaces:", workspaces.length);
    
    // Check for test workspace
    const testWorkspace = workspaces.find(w => w.id && w.id.startsWith("test-"));
    if (testWorkspace) {
      console.log("✅ Found test workspace:", testWorkspace.title);
      console.log("Workspace details:", testWorkspace);
      return true;
    } else {
      console.log("⚠️ Test workspace not found in loaded data");
      return false;
    }
  } catch (error) {
    console.error("❌ Failed to load/parse workspace data:", error);
    return false;
  }
}

// Function to clean test data
function cleanTestData() {
  console.log("\n=== Cleaning Test Data ===");
  
  try {
    const data = localStorage.getItem("deep-agents-workspaces");
    if (!data) return;
    
    let workspaces = JSON.parse(data);
    const originalCount = workspaces.length;
    
    // Remove test workspaces
    workspaces = workspaces.filter(w => !w.id || !w.id.startsWith("test-"));
    
    localStorage.setItem("deep-agents-workspaces", JSON.stringify(workspaces));
    console.log(`✅ Removed ${originalCount - workspaces.length} test workspace(s)`);
  } catch (error) {
    console.error("❌ Failed to clean test data:", error);
  }
}

// Run tests
console.log("\nStep 1: Creating test workspace...");
const created = createTestWorkspace();

if (created) {
  console.log("\nStep 2: Verifying persistence...");
  const verified = verifyPersistence();
  
  if (verified) {
    console.log("\n✅ Workspace persistence is working correctly!");
  } else {
    console.log("\n❌ Workspace persistence verification failed!");
  }
  
  console.log("\nStep 3: Cleaning up test data...");
  cleanTestData();
} else {
  console.log("\n❌ Failed to create test workspace!");
}

console.log("\n=== Test Complete ===");
console.log("To manually test in the UI:");
console.log("1. Create a new workspace using the + button");
console.log("2. Refresh the browser");
console.log("3. Check if the workspace persists");