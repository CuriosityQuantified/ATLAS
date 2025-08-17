# Deep Agents UI - Test Checklist

## Workspace Functionality Tests

### 1. Workspace Creation
- [ ] Click the + button to create a new workspace
- [ ] Verify workspace is named "Workspace 2" (not "Untitled")
- [ ] Check console for "Workspaces saved successfully"

### 2. Workspace Persistence
- [ ] Create a new workspace
- [ ] Refresh the browser
- [ ] Verify the workspace persists with correct name
- [ ] Check that no errors appear in console

### 3. Task Management
- [ ] Start a research task in a workspace
- [ ] Verify tasks appear in the correct workspace
- [ ] Check that tasks persist after refresh

### 4. File Management
- [ ] Verify files are saved to the active workspace
- [ ] Check that files persist after refresh

### 5. Error Handling
- [ ] No "Maximum call stack exceeded" errors
- [ ] No JSON serialization errors
- [ ] No red error button appearing

## Console Commands for Testing

```javascript
// Run in browser console to test persistence
localStorage.getItem("deep-agents-workspaces")

// Check for circular references
JSON.parse(localStorage.getItem("deep-agents-workspaces"))

// Clear workspace data if needed
localStorage.removeItem("deep-agents-workspaces")
localStorage.removeItem("deep-agents-active-workspace")
```

## Expected Behavior
1. Workspaces should be numbered sequentially (Workspace 1, 2, 3...)
2. All data should persist across browser refreshes
3. No console errors during normal operation
4. Research tasks should save to the active workspace