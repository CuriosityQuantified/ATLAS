const { chromium } = require('playwright');
const fs = require('fs').promises;

// Test configuration
const CONFIG = {
  url: 'http://localhost:3003',
  headless: false,
  slowMo: 500,
  timeout: 30000,
  screenshotDir: './test-screenshots'
};

class DeepAgentsUITestSuite {
  constructor() {
    this.browser = null;
    this.page = null;
    this.results = [];
    this.consoleMessages = [];
  }

  async setup() {
    console.log('🚀 Starting Deep Agents UI Test Suite\n');
    console.log(`📍 Target URL: ${CONFIG.url}`);
    console.log(`⏱️  Timeout: ${CONFIG.timeout}ms\n`);
    
    this.browser = await chromium.launch({
      headless: CONFIG.headless,
      slowMo: CONFIG.slowMo
    });
    
    const context = await this.browser.newContext();
    this.page = await context.newPage();
    this.page.setDefaultTimeout(CONFIG.timeout);
    
    // Monitor console
    this.page.on('console', msg => {
      const text = msg.text();
      this.consoleMessages.push({ type: msg.type(), text, time: new Date() });
      
      if (text.includes('error') || text.includes('Error')) {
        console.log(`  ⚠️  Console ${msg.type()}: ${text}`);
      } else if (text.includes('saved successfully')) {
        console.log(`  ✅ ${text}`);
      }
    });
    
    // Monitor errors
    this.page.on('pageerror', error => {
      console.error(`  ❌ Page Error: ${error.message}`);
      this.results.push({ test: 'Page Error', passed: false, message: error.message });
    });
  }

  async navigateToApp() {
    console.log('📂 Test 1: Navigation');
    try {
      await this.page.goto(CONFIG.url, { waitUntil: 'domcontentloaded' });
      await this.page.waitForTimeout(2000);
      
      // Take screenshot
      await this.screenshot('01-loaded');
      
      this.results.push({ test: 'Navigation', passed: true, message: 'App loaded successfully' });
      console.log('  ✅ App loaded successfully\n');
      return true;
    } catch (error) {
      this.results.push({ test: 'Navigation', passed: false, message: error.message });
      console.log(`  ❌ Failed to load app: ${error.message}\n`);
      return false;
    }
  }

  async testWorkspaceCreation() {
    console.log('🔨 Test 2: Workspace Creation');
    
    try {
      // Count existing workspaces
      const initialCount = await this.page.getByText(/Workspace \d+/).count();
      console.log(`  📊 Initial workspaces: ${initialCount}`);
      
      // Look for add button
      const addButton = await this.page.getByRole('button', { name: '+' });
      
      if (await addButton.isVisible({ timeout: 5000 })) {
        await addButton.click();
        await this.page.waitForTimeout(1000);
        
        const newCount = await this.page.getByText(/Workspace \d+/).count();
        
        if (newCount > initialCount) {
          this.results.push({ test: 'Workspace Creation', passed: true, message: `Created workspace ${newCount}` });
          console.log(`  ✅ Created workspace ${newCount}\n`);
          
          await this.screenshot('02-workspace-created');
          return true;
        }
      }
      
      // Try alternative approach
      console.log('  🔄 Trying alternative creation method...');
      
      // Check for any button with workspace-related text
      const createButtons = await this.page.getByRole('button').all();
      for (const btn of createButtons) {
        const text = await btn.textContent();
        if (text && (text.includes('+') || text.includes('Add') || text.includes('New'))) {
          await btn.click();
          await this.page.waitForTimeout(1000);
          
          const afterClick = await this.page.getByText(/Workspace \d+/).count();
          if (afterClick > initialCount) {
            this.results.push({ test: 'Workspace Creation', passed: true, message: 'Created via alternative method' });
            console.log('  ✅ Created workspace via alternative method\n');
            return true;
          }
        }
      }
      
      this.results.push({ test: 'Workspace Creation', passed: false, message: 'Could not create workspace' });
      console.log('  ❌ Failed to create workspace\n');
      return false;
      
    } catch (error) {
      this.results.push({ test: 'Workspace Creation', passed: false, message: error.message });
      console.log(`  ❌ Error: ${error.message}\n`);
      return false;
    }
  }

  async testResearchQuery() {
    console.log('🔍 Test 3: Research Query Submission');
    
    try {
      // Find message input
      const input = await this.page.getByPlaceholder(/Type your message/i);
      
      if (await input.isVisible()) {
        const query = 'What are the latest breakthroughs in quantum computing?';
        console.log(`  📝 Typing: "${query}"`);
        
        await input.fill(query);
        await this.page.waitForTimeout(500);
        
        // Submit query
        await input.press('Enter');
        console.log('  ⏎ Query submitted');
        
        // Wait for response
        await this.page.waitForTimeout(3000);
        
        // Check for task creation or response
        const hasTask = await this.page.getByText(/quantum/i).count() > 0;
        const hasProgress = await this.page.locator('.loading, .spinner, [role="progressbar"]').count() > 0;
        
        if (hasTask || hasProgress) {
          this.results.push({ test: 'Research Query', passed: true, message: 'Query processed' });
          console.log('  ✅ Query is being processed\n');
          
          await this.screenshot('03-query-submitted');
          return true;
        } else {
          this.results.push({ test: 'Research Query', passed: false, message: 'No response to query' });
          console.log('  ⚠️  No visible response to query\n');
          return false;
        }
      } else {
        this.results.push({ test: 'Research Query', passed: false, message: 'Input field not found' });
        console.log('  ❌ Message input field not found\n');
        return false;
      }
      
    } catch (error) {
      this.results.push({ test: 'Research Query', passed: false, message: error.message });
      console.log(`  ❌ Error: ${error.message}\n`);
      return false;
    }
  }

  async testStatePersistence() {
    console.log('💾 Test 4: State Persistence');
    
    try {
      // Get initial state
      const stateBefore = await this.page.evaluate(() => ({
        workspaces: localStorage.getItem('deep-agents-workspaces'),
        activeWorkspace: localStorage.getItem('deep-agents-active-workspace'),
        keys: Object.keys(localStorage).length
      }));
      
      console.log(`  📦 LocalStorage keys: ${stateBefore.keys}`);
      
      if (stateBefore.workspaces) {
        const data = JSON.parse(stateBefore.workspaces);
        console.log(`  📊 Workspaces in storage: ${data.length}`);
      }
      
      // Take screenshot before refresh
      await this.screenshot('04-before-refresh');
      
      // Refresh page
      console.log('  🔄 Refreshing browser...');
      await this.page.reload({ waitUntil: 'domcontentloaded' });
      await this.page.waitForTimeout(3000);
      
      // Get state after refresh
      const stateAfter = await this.page.evaluate(() => ({
        workspaces: localStorage.getItem('deep-agents-workspaces'),
        activeWorkspace: localStorage.getItem('deep-agents-active-workspace')
      }));
      
      // Compare states
      if (stateAfter.workspaces === stateBefore.workspaces) {
        this.results.push({ test: 'State Persistence', passed: true, message: 'State persisted correctly' });
        console.log('  ✅ State persisted after refresh\n');
        
        await this.screenshot('05-after-refresh');
        return true;
      } else {
        this.results.push({ test: 'State Persistence', passed: false, message: 'State changed after refresh' });
        console.log('  ❌ State changed after refresh\n');
        return false;
      }
      
    } catch (error) {
      this.results.push({ test: 'State Persistence', passed: false, message: error.message });
      console.log(`  ❌ Error: ${error.message}\n`);
      return false;
    }
  }

  async testFileManagement() {
    console.log('📁 Test 5: File Management');
    
    try {
      // Look for Files tab
      const filesTab = await this.page.getByText(/Files \(\d+\)/);
      
      if (await filesTab.isVisible()) {
        console.log('  📂 Files tab found');
        await filesTab.click();
        await this.page.waitForTimeout(1000);
        
        // Check if files view is displayed
        const filesView = await this.page.locator('[role="tabpanel"]').last();
        
        if (await filesView.isVisible()) {
          this.results.push({ test: 'File Management', passed: true, message: 'Files tab functional' });
          console.log('  ✅ Files tab is functional\n');
          
          await this.screenshot('06-files-tab');
          
          // Switch back to Tasks
          const tasksTab = await this.page.getByText(/Tasks \(\d+\)/);
          if (await tasksTab.isVisible()) {
            await tasksTab.click();
          }
          
          return true;
        }
      }
      
      this.results.push({ test: 'File Management', passed: false, message: 'Files tab not accessible' });
      console.log('  ❌ Files tab not accessible\n');
      return false;
      
    } catch (error) {
      this.results.push({ test: 'File Management', passed: false, message: error.message });
      console.log(`  ❌ Error: ${error.message}\n`);
      return false;
    }
  }

  async testProgressTracking() {
    console.log('📊 Test 6: Progress Tracking');
    
    try {
      // Check for any progress indicators
      const indicators = [
        await this.page.locator('.progress').count(),
        await this.page.locator('[role="progressbar"]').count(),
        await this.page.locator('.loading').count(),
        await this.page.locator('.spinner').count()
      ];
      
      const total = indicators.reduce((a, b) => a + b, 0);
      
      if (total > 0) {
        this.results.push({ test: 'Progress Tracking', passed: true, message: `${total} indicators found` });
        console.log(`  ✅ Found ${total} progress indicator(s)\n`);
        
        await this.screenshot('07-progress-indicators');
        return true;
      } else {
        this.results.push({ test: 'Progress Tracking', passed: false, message: 'No progress indicators' });
        console.log('  ⚠️  No progress indicators found\n');
        return false;
      }
      
    } catch (error) {
      this.results.push({ test: 'Progress Tracking', passed: false, message: error.message });
      console.log(`  ❌ Error: ${error.message}\n`);
      return false;
    }
  }

  async testErrorHandling() {
    console.log('⚠️ Test 7: Error Handling');
    
    // Check console messages for errors
    const errors = this.consoleMessages.filter(m => 
      m.text.includes('Error') || 
      m.text.includes('error') ||
      m.text.includes('Maximum call stack') ||
      m.text.includes('JSON')
    );
    
    // Check for error UI elements
    const errorUI = await this.page.locator('.error, [data-error]').count();
    
    if (errors.length === 0 && errorUI === 0) {
      this.results.push({ test: 'Error Handling', passed: true, message: 'No errors detected' });
      console.log('  ✅ No errors detected\n');
      return true;
    } else {
      const message = `${errors.length} console errors, ${errorUI} UI errors`;
      this.results.push({ test: 'Error Handling', passed: false, message });
      console.log(`  ❌ ${message}\n`);
      return false;
    }
  }

  async screenshot(name) {
    try {
      await fs.mkdir(CONFIG.screenshotDir, { recursive: true });
      const path = `${CONFIG.screenshotDir}/${name}.png`;
      await this.page.screenshot({ path, fullPage: true });
      console.log(`  📸 Screenshot: ${name}.png`);
    } catch (error) {
      console.error(`  ⚠️  Failed to save screenshot: ${error.message}`);
    }
  }

  async generateReport() {
    console.log('=' .repeat(60));
    console.log('📊 TEST RESULTS SUMMARY');
    console.log('=' .repeat(60));
    
    const passed = this.results.filter(r => r.passed).length;
    const failed = this.results.filter(r => !r.passed).length;
    const total = this.results.length;
    const passRate = total > 0 ? ((passed / total) * 100).toFixed(1) : 0;
    
    console.log(`\n✅ Passed: ${passed}`);
    console.log(`❌ Failed: ${failed}`);
    console.log(`📈 Pass Rate: ${passRate}%\n`);
    
    // List failed tests
    if (failed > 0) {
      console.log('Failed Tests:');
      this.results.filter(r => !r.passed).forEach(r => {
        console.log(`  • ${r.test}: ${r.message}`);
      });
      console.log('');
    }
    
    // Save report
    const report = {
      timestamp: new Date().toISOString(),
      url: CONFIG.url,
      results: this.results,
      summary: { passed, failed, total, passRate },
      consoleMessages: this.consoleMessages.length
    };
    
    await fs.mkdir(CONFIG.screenshotDir, { recursive: true });
    await fs.writeFile(
      `${CONFIG.screenshotDir}/report.json`,
      JSON.stringify(report, null, 2)
    );
    
    console.log(`📄 Report saved to ${CONFIG.screenshotDir}/report.json`);
    console.log('=' .repeat(60));
    
    return report;
  }

  async cleanup() {
    if (this.browser) {
      await this.browser.close();
    }
    console.log('\n✨ Test suite complete\n');
  }

  async run() {
    try {
      await this.setup();
      
      if (await this.navigateToApp()) {
        await this.testWorkspaceCreation();
        await this.testResearchQuery();
        await this.testStatePersistence();
        await this.testFileManagement();
        await this.testProgressTracking();
        await this.testErrorHandling();
      }
      
      return await this.generateReport();
      
    } catch (error) {
      console.error('💥 Critical error:', error);
      return null;
    } finally {
      await this.cleanup();
    }
  }
}

// Run the test suite
(async () => {
  const tester = new DeepAgentsUITestSuite();
  const report = await tester.run();
  
  if (report && report.summary.failed === 0) {
    process.exit(0);
  } else {
    process.exit(1);
  }
})();