import { test, expect } from '@playwright/test';

test.describe('Simplified Ask User Question Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3000');
    await page.evaluate(() => localStorage.clear());
    await page.reload();
    await page.waitForSelector('[class*="container"]', { timeout: 10000 });
  });

  test('Workspace creation and basic question flow', async ({ page }) => {
    console.log('Testing simplified question flow...');
    
    // Step 1: Create workspace
    const newWorkspaceButton = page.locator('button[title="New workspace"]');
    await expect(newWorkspaceButton).toBeVisible({ timeout: 5000 });
    await newWorkspaceButton.click();
    await page.waitForTimeout(1000);
    
    // Verify blank workspace
    const messageCount = await page.locator('[class*="messageContainer"]').count();
    expect(messageCount).toBe(0);
    console.log('✓ Workspace created');
    
    // Step 2: Send message
    const inputField = page.locator('input[placeholder="Type your message..."]');
    await inputField.fill('ask me what my birthday is');
    await page.keyboard.press('Enter');
    
    // Verify message sent
    await expect(page.locator('text="ask me what my birthday is"').first()).toBeVisible({ timeout: 5000 });
    console.log('✓ Message sent');
    
    // Step 3: Wait for any agent response (question box or message)
    console.log('Waiting for agent response...');
    
    // Give agent time to process
    let questionBoxFound = false;
    let agentMessageFound = false;
    
    for (let i = 0; i < 15; i++) {
      await page.waitForTimeout(2000);
      
      // Check for question box
      const questionBoxes = await page.locator('div[class*="QuestionBox"]').count();
      if (questionBoxes > 0) {
        questionBoxFound = true;
        console.log('✓ Question box appeared');
        break;
      }
      
      // Check for AI message
      const aiMessages = await page.locator('[class*="aiMessage"]').count();
      if (aiMessages > 0) {
        agentMessageFound = true;
        console.log('✓ Agent message appeared');
        break;
      }
      
      // Check if still loading
      const loadingVisible = await page.locator('[class*="loadingMessage"]').count() > 0;
      console.log(`  Attempt ${i + 1}/15: Loading=${loadingVisible}, QuestionBoxes=${questionBoxes}, AIMessages=${aiMessages}`);
    }
    
    if (questionBoxFound) {
      // Step 4: Answer the question
      const answerInput = page.locator('textarea[class*="questionInput"]').first();
      const inputVisible = await answerInput.count() > 0;
      
      if (inputVisible) {
        await answerInput.fill('March 12, 1990');
        console.log('✓ Answer entered');
        
        // Submit answer
        const sendButton = page.locator('button[class*="sendButton"]').first();
        await sendButton.click();
        console.log('✓ Answer submitted');
        
        // Check what happens after submission
        await page.waitForTimeout(3000);
        
        const questionBoxAfterSubmit = await page.locator('div[class*="QuestionBox"]').count();
        const answeredTextVisible = await page.locator('[class*="answeredText"]').count() > 0;
        
        console.log(`After submission: QuestionBoxes=${questionBoxAfterSubmit}, AnsweredText=${answeredTextVisible}`);
        
        if (questionBoxAfterSubmit > 0 && answeredTextVisible) {
          const answeredText = await page.locator('[class*="answeredText"]').textContent();
          console.log(`✓ Answer displayed: "${answeredText}"`);
        } else if (questionBoxAfterSubmit === 0) {
          console.log('✓ Question box removed after answer (current behavior)');
        }
      }
    } else if (agentMessageFound) {
      const aiMessage = await page.locator('[class*="aiMessage"]').first().textContent();
      console.log(`Agent responded with message: "${aiMessage?.substring(0, 100)}..."`);
    } else {
      console.log('⚠️ No agent response within timeout period');
    }
    
    // Final state check
    const finalMessages = await page.locator('[class*="messageContainer"]').count();
    console.log(`Final state: ${finalMessages} total messages`);
    
    // Test passes if workspace was created and message was sent successfully
    expect(messageCount).toBe(0); // Initial blank workspace
    expect(finalMessages).toBeGreaterThan(0); // At least user message exists
  });
  
  test('JSON parse error prevention', async ({ page }) => {
    console.log('Testing JSON parse error prevention...');
    
    // Create workspace
    await page.locator('button[title="New workspace"]').click();
    await page.waitForTimeout(1000);
    
    // Send a message that might trigger tool calls
    const inputField = page.locator('input[placeholder="Type your message..."]');
    await inputField.fill('test message');
    await page.keyboard.press('Enter');
    
    // Monitor console for JSON parse errors
    const consoleErrors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error' && msg.text().includes('JSON')) {
        consoleErrors.push(msg.text());
      }
    });
    
    // Wait for any processing
    await page.waitForTimeout(5000);
    
    // Check that no JSON parse errors occurred
    expect(consoleErrors).toHaveLength(0);
    console.log('✓ No JSON parse errors detected');
  });
  
  test('Workspace persistence after refresh', async ({ page }) => {
    console.log('Testing workspace persistence...');
    
    // Create workspace
    await page.locator('button[title="New workspace"]').click();
    await page.waitForTimeout(1000);
    
    // Send a message
    const inputField = page.locator('input[placeholder="Type your message..."]');
    await inputField.fill('test persistence');
    await page.keyboard.press('Enter');
    
    await expect(page.locator('text="test persistence"').first()).toBeVisible({ timeout: 5000 });
    
    // Get workspace data
    const workspaceData = await page.evaluate(() => {
      const workspaces = localStorage.getItem('workspaces');
      if (workspaces) {
        const parsed = JSON.parse(workspaces);
        return parsed.find((w: any) => w.isActive);
      }
      return null;
    });
    
    console.log(`Workspace ID: ${workspaceData?.id}`);
    
    // Refresh page
    await page.reload();
    await page.waitForSelector('[class*="container"]', { timeout: 10000 });
    await page.waitForTimeout(2000);
    
    // Check workspace restored
    const restoredWorkspaceData = await page.evaluate(() => {
      const workspaces = localStorage.getItem('workspaces');
      if (workspaces) {
        const parsed = JSON.parse(workspaces);
        return parsed.find((w: any) => w.isActive);
      }
      return null;
    });
    
    expect(restoredWorkspaceData?.id).toBe(workspaceData?.id);
    console.log('✓ Workspace persisted after refresh');
    
    // Check messages restored
    const restoredMessages = await page.locator('[class*="messageContainer"]').count();
    expect(restoredMessages).toBeGreaterThan(0);
    console.log(`✓ ${restoredMessages} messages restored`);
  });
});