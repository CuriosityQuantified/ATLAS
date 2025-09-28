const { chromium } = require('playwright');

// Test configuration
const CONFIG = {
  url: 'http://localhost:3003',
  headless: false,
  slowMo: 300,
  timeout: 60000,
  screenshotDir: './test-screenshots'
};

// Test data
const TEST_DATA = {
  researchQuery: 'What are the latest developments in quantum computing and their potential applications?',
  secondQuery: 'Explain the key differences between machine learning and deep learning',
  testFileName: 'test-document.txt',
  testFileContent: 'This is a test file for workspace persistence testing'
};

class DeepAgentsUITester {
  constructor() {
    this.browser = null;
    this.context = null;
    this.page = null;
    this.testResults = [];
    this.consoleMessages = [];
    this.errors = [];
  }

  async initialize() {
    console.log('🚀 Initializing Playwright browser...\n');
    
    this.browser = await chromium.launch({
      headless: CONFIG.headless,
      slowMo: CONFIG.slowMo
    });
    
    this.context = await this.browser.newContext({
      viewport: { width: 1920, height: 1080 }
    });
    
    this.page = await this.context.newPage();
    this.page.setDefaultTimeout(CONFIG.timeout);
    
    // Set up console and error monitoring
    this.page.on('console', msg => {
      const text = msg.text();
      this.consoleMessages.push({ type: msg.type(), text });
      
      // Log important messages
      if (text.includes('saved successfully') || text.includes('error') || text.includes('Error')) {
        console.log(`[Console ${msg.type()}]: ${text}`);
      }
    });
    
    this.page.on('pageerror', error => {
      this.errors.push(error.message);
      console.error(`[Page Error]: ${error.message}`);
    });
  }

  async navigateToApp() {
    console.log(`📍 Navigating to ${CONFIG.url}...`);
    
    try {
      await this.page.goto(CONFIG.url, { 
        waitUntil: 'networkidle',
        timeout: 30000 
      });
      
      await this.page.waitForTimeout(2000);
      this.recordTest('Navigation', true, 'Successfully loaded application');
      
      // Take initial screenshot
      await this.takeScreenshot('01-initial-load');
      
      return true;
    } catch (error) {
      this.recordTest('Navigation', false, `Failed to load: ${error.message}`);
      return false;
    }
  }

  async testWorkspaceCreation() {
    console.log('\n🔧 Testing Workspace Creation...');
    
    try {
      // Count initial workspaces
      const initialCount = await this.page.locator('text=/Workspace \\d+/').count();
      console.log(`  Initial workspace count: ${initialCount}`);
      
      // Find and click the + button
      const addButton = await this.page.locator('button:has-text("+")').first();
      
      if (await addButton.isVisible()) {
        await addButton.click();
        await this.page.waitForTimeout(1000);
        
        // Count workspaces after creation
        const newCount = await this.page.locator('text=/Workspace \\d+/').count();
        
        if (newCount > initialCount) {
          // Check the name of the new workspace
          const workspaces = await this.page.locator('text=/Workspace \\d+/').all();
          const lastWorkspace = workspaces[workspaces.length - 1];
          const name = await lastWorkspace.textContent();
          
          if (name && name.includes('Workspace')) {
            this.recordTest('Workspace Creation', true, `Created ${name}`);
            await this.takeScreenshot('02-workspace-created');
            
            // Click on the new workspace to select it
            await lastWorkspace.click();
            await this.page.waitForTimeout(500);
            
            return true;
          } else {
            this.recordTest('Workspace Creation', false, 'Incorrect naming');
          }
        } else {
          this.recordTest('Workspace Creation', false, 'Workspace not created');
        }
      } else {
        // Try alternative method - keyboard shortcut or menu
        console.log('  + button not visible, trying alternative methods...');
        
        // Try pressing a keyboard shortcut if available
        await this.page.keyboard.press('Control+N');
        await this.page.waitForTimeout(1000);
        
        const newCount = await this.page.locator('text=/Workspace \\d+/').count();
        if (newCount > initialCount) {
          this.recordTest('Workspace Creation', true, 'Created via keyboard shortcut');
          return true;
        } else {
          this.recordTest('Workspace Creation', false, 'No creation method available');
        }
      }
    } catch (error) {
      this.recordTest('Workspace Creation', false, error.message);
    }
    
    return false;
  }

  async testDeepResearchQuery() {
    console.log('\n🔍 Testing Deep Research Query...');
    
    try {
      // Find the message input field
      const messageInput = await this.page.locator('input[placeholder*="Type your message"], textarea[placeholder*="Type your message"]').first();
      
      if (await messageInput.isVisible()) {
        console.log('  Found message input field');
        
        // Type the research query
        await messageInput.fill(TEST_DATA.researchQuery);
        await this.page.waitForTimeout(500);
        
        // Submit the query (press Enter or click submit button)
        await messageInput.press('Enter');
        
        // Alternative: look for a submit button
        const submitButton = await this.page.locator('button[type="submit"], button:has-text("Send"), button:has-text("Submit")').first();
        if (await submitButton.isVisible()) {
          await submitButton.click();
        }
        
        console.log('  Query submitted, waiting for response...');
        
        // Wait for task to appear
        await this.page.waitForTimeout(3000);
        
        // Check if task appears in the list
        const taskElements = await this.page.locator('[data-task], .task-item, text=/quantum computing/i').count();
        
        if (taskElements > 0) {
          this.recordTest('Research Query Submission', true, 'Task created successfully');
          await this.takeScreenshot('03-research-query-submitted');
          
          // Check for progress indicators
          await this.testProgressTracking();
          
          return true;
        } else {
          this.recordTest('Research Query Submission', false, 'Task not visible');
        }
      } else {
        this.recordTest('Research Query Submission', false, 'Input field not found');
      }
    } catch (error) {
      this.recordTest('Research Query Submission', false, error.message);
    }
    
    return false;
  }

  async testProgressTracking() {
    console.log('\n📊 Testing Progress Tracking...');
    
    try {
      // Look for progress indicators
      const progressIndicators = await this.page.locator(
        '[role="progressbar"], .progress, [class*="progress"], [data-progress], .loading, .spinner'
      ).count();
      
      if (progressIndicators > 0) {
        console.log(`  Found ${progressIndicators} progress indicator(s)`);
        this.recordTest('Progress Indicators', true, `${progressIndicators} indicators found`);
        
        // Wait and check if progress updates
        await this.page.waitForTimeout(2000);
        
        // Check for status updates
        const statusElements = await this.page.locator(
          'text=/processing/i, text=/running/i, text=/complete/i, text=/pending/i'
        ).count();
        
        if (statusElements > 0) {
          this.recordTest('Status Updates', true, 'Status indicators present');
          await this.takeScreenshot('04-progress-tracking');
        }
        
        return true;
      } else {
        this.recordTest('Progress Indicators', false, 'No indicators found');
      }
    } catch (error) {
      this.recordTest('Progress Tracking', false, error.message);
    }
    
    return false;
  }

  async testStatePersistence() {
    console.log('\n💾 Testing State Persistence...');
    
    try {
      // Get current state from localStorage
      const stateBefore = await this.page.evaluate(() => {
        return {
          workspaces: localStorage.getItem('deep-agents-workspaces'),
          activeWorkspace: localStorage.getItem('deep-agents-active-workspace'),
          tasks: localStorage.getItem('deep-agents-tasks'),
          allKeys: Object.keys(localStorage)
        };
      });
      
      console.log(`  Found ${stateBefore.allKeys.length} localStorage keys`);
      
      if (stateBefore.workspaces) {
        const workspaces = JSON.parse(stateBefore.workspaces);
        console.log(`  ${workspaces.length} workspace(s) in storage`);
      }
      
      // Take screenshot before refresh
      await this.takeScreenshot('05-before-refresh');
      
      // Refresh the page
      console.log('  Refreshing browser...');
      await this.page.reload({ waitUntil: 'networkidle' });
      await this.page.waitForTimeout(3000);
      
      // Get state after refresh
      const stateAfter = await this.page.evaluate(() => {
        return {
          workspaces: localStorage.getItem('deep-agents-workspaces'),
          activeWorkspace: localStorage.getItem('deep-agents-active-workspace'),
          tasks: localStorage.getItem('deep-agents-tasks')
        };
      });
      
      // Verify persistence
      if (stateAfter.workspaces === stateBefore.workspaces) {
        this.recordTest('Workspace Persistence', true, 'Workspaces preserved');
        
        // Check if workspaces are displayed correctly
        const workspaceCount = await this.page.locator('text=/Workspace \\d+/').count();
        const storedWorkspaces = JSON.parse(stateAfter.workspaces);
        
        if (workspaceCount === storedWorkspaces.length) {
          this.recordTest('Workspace Display', true, 'All workspaces visible');
        } else {
          this.recordTest('Workspace Display', false, 
            `Mismatch: ${workspaceCount} displayed, ${storedWorkspaces.length} stored`);
        }
      } else {
        this.recordTest('Workspace Persistence', false, 'Data changed after refresh');
      }
      
      // Check for errors
      if (this.errors.length === 0) {
        this.recordTest('Error-free Refresh', true, 'No errors after refresh');
      } else {
        this.recordTest('Error-free Refresh', false, `${this.errors.length} errors found`);
      }
      
      await this.takeScreenshot('06-after-refresh');
      
      return true;
    } catch (error) {
      this.recordTest('State Persistence', false, error.message);
      return false;
    }
  }

  async testFileManagement() {
    console.log('\n📁 Testing File Management...');
    
    try {
      // Click on Files tab
      const filesTab = await this.page.locator('button:has-text("Files"), [role="tab"]:has-text("Files"), text=/Files \\(\\d+\\)/').first();
      
      if (await filesTab.isVisible()) {
        await filesTab.click();
        await this.page.waitForTimeout(1000);
        
        this.recordTest('Files Tab Access', true, 'Files tab accessible');
        
        // Check for file upload or creation options
        const fileOptions = await this.page.locator(
          'button:has-text("Upload"), button:has-text("Add File"), input[type="file"]'
        ).count();
        
        if (fileOptions > 0) {
          this.recordTest('File Operations', true, 'File operations available');
        } else {
          this.recordTest('File Operations', false, 'No file operations found');
        }
        
        await this.takeScreenshot('07-file-management');
        
        // Switch back to Tasks tab
        const tasksTab = await this.page.locator('button:has-text("Tasks"), [role="tab"]:has-text("Tasks"), text=/Tasks \\(\\d+\\)/').first();
        if (await tasksTab.isVisible()) {
          await tasksTab.click();
        }
        
        return true;
      } else {
        this.recordTest('Files Tab Access', false, 'Files tab not found');
      }
    } catch (error) {
      this.recordTest('File Management', false, error.message);
    }
    
    return false;
  }

  async testErrorHandling() {
    console.log('\n⚠️ Testing Error Handling...');
    
    // Check for specific error patterns
    const errorPatterns = [
      'Maximum call stack exceeded',
      'JSON serialization error',
      'TypeError',
      'ReferenceError',
      'NetworkError'
    ];
    
    let errorsFound = [];
    
    for (const pattern of errorPatterns) {
      const found = this.consoleMessages.some(msg => 
        msg.text.includes(pattern) || this.errors.some(err => err.includes(pattern))
      );
      
      if (found) {
        errorsFound.push(pattern);
      }
    }
    
    if (errorsFound.length === 0) {
      this.recordTest('Error Handling', true, 'No critical errors detected');
      
      // Check for error UI elements
      const errorUI = await this.page.locator('.error, [class*="error"], [data-error]').count();
      
      if (errorUI === 0) {
        this.recordTest('Error UI', true, 'No error indicators visible');
      } else {
        this.recordTest('Error UI', false, `${errorUI} error indicators found`);
      }
    } else {
      this.recordTest('Error Handling', false, `Errors found: ${errorsFound.join(', ')}`);
    }
    
    return errorsFound.length === 0;
  }

  async testAdvancedFeatures() {
    console.log('\n🚀 Testing Advanced Features...');
    
    try {
      // Test multiple workspace switching
      const workspaces = await this.page.locator('text=/Workspace \\d+/').all();
      
      if (workspaces.length >= 2) {
        console.log('  Testing workspace switching...');
        
        // Click on different workspace
        await workspaces[0].click();
        await this.page.waitForTimeout(500);
        
        const activeWorkspace1 = await this.page.evaluate(() => 
          localStorage.getItem('deep-agents-active-workspace')
        );
        
        await workspaces[1].click();
        await this.page.waitForTimeout(500);
        
        const activeWorkspace2 = await this.page.evaluate(() => 
          localStorage.getItem('deep-agents-active-workspace')
        );
        
        if (activeWorkspace1 !== activeWorkspace2) {
          this.recordTest('Workspace Switching', true, 'Switching works correctly');
        } else {
          this.recordTest('Workspace Switching', false, 'Active workspace not updating');
        }
      }
      
      // Test real-time updates
      console.log('  Testing real-time capabilities...');
      
      // Check for WebSocket connections or SSE
      const hasRealtime = await this.page.evaluate(() => {
        return window.WebSocket !== undefined || window.EventSource !== undefined;
      });
      
      if (hasRealtime) {
        this.recordTest('Real-time Support', true, 'WebSocket/SSE available');
      }
      
      await this.takeScreenshot('08-advanced-features');
      
    } catch (error) {
      this.recordTest('Advanced Features', false, error.message);
    }
  }

  async takeScreenshot(name) {
    try {
      const path = `${CONFIG.screenshotDir}/${name}.png`;
      await this.page.screenshot({ path, fullPage: true });
      console.log(`  📸 Screenshot saved: ${name}.png`);
    } catch (error) {
      console.error(`  Failed to take screenshot: ${error.message}`);
    }
  }

  recordTest(name, passed, message) {
    const result = { name, passed, message, timestamp: new Date().toISOString() };
    this.testResults.push(result);
    
    const icon = passed ? '✅' : '❌';
    console.log(`  ${icon} ${name}: ${message}`);
  }

  async cleanup() {
    console.log('\n🧹 Cleaning up...');
    
    if (this.browser) {
      await this.browser.close();
    }
  }

  generateReport() {
    console.log('\n' + '='.repeat(80));
    console.log('📊 TEST RESULTS SUMMARY');
    console.log('='.repeat(80));
    
    const passed = this.testResults.filter(t => t.passed).length;
    const failed = this.testResults.filter(t => !t.passed).length;
    const total = this.testResults.length;
    const passRate = ((passed / total) * 100).toFixed(1);
    
    console.log(`\n📈 Overall: ${passed}/${total} tests passed (${passRate}% success rate)\n`);
    
    // Group results by status
    console.log('✅ PASSED TESTS:');
    this.testResults.filter(t => t.passed).forEach(t => {
      console.log(`   • ${t.name}: ${t.message}`);
    });
    
    if (failed > 0) {
      console.log('\n❌ FAILED TESTS:');
      this.testResults.filter(t => !t.passed).forEach(t => {
        console.log(`   • ${t.name}: ${t.message}`);
      });
    }
    
    // Console message summary
    console.log('\n📝 Console Activity:');
    console.log(`   • Total messages: ${this.consoleMessages.length}`);
    console.log(`   • Errors: ${this.errors.length}`);
    
    const successMessages = this.consoleMessages.filter(m => 
      m.text.includes('saved successfully')
    ).length;
    
    if (successMessages > 0) {
      console.log(`   • Success messages: ${successMessages}`);
    }
    
    // Recommendations
    if (failed > 0) {
      console.log('\n💡 RECOMMENDATIONS:');
      
      if (this.testResults.find(t => !t.passed && t.name.includes('Workspace Creation'))) {
        console.log('   • Add data-testid attributes to workspace creation button');
      }
      
      if (this.testResults.find(t => !t.passed && t.name.includes('Research Query'))) {
        console.log('   • Ensure message input is accessible and properly labeled');
      }
      
      if (this.errors.length > 0) {
        console.log('   • Investigate and fix console errors');
      }
    }
    
    console.log('\n' + '='.repeat(80));
    
    return {
      passed,
      failed,
      total,
      passRate,
      results: this.testResults,
      errors: this.errors
    };
  }

  async runAllTests() {
    console.log('=' .repeat(80));
    console.log('🧪 DEEP AGENTS UI - COMPREHENSIVE TEST SUITE');
    console.log('='.repeat(80));
    console.log(`URL: ${CONFIG.url}`);
    console.log(`Time: ${new Date().toISOString()}`);
    console.log('='.repeat(80));
    
    try {
      await this.initialize();
      
      // Core functionality tests
      if (await this.navigateToApp()) {
        await this.testWorkspaceCreation();
        await this.testDeepResearchQuery();
        await this.testStatePersistence();
        await this.testFileManagement();
        await this.testErrorHandling();
        await this.testAdvancedFeatures();
      }
      
      // Generate and return report
      const report = this.generateReport();
      
      // Save report to file
      const fs = require('fs').promises;
      await fs.mkdir(CONFIG.screenshotDir, { recursive: true });
      await fs.writeFile(
        `${CONFIG.screenshotDir}/test-report.json`,
        JSON.stringify(report, null, 2)
      );
      
      console.log(`\n📄 Full report saved to ${CONFIG.screenshotDir}/test-report.json`);
      
      return report;
      
    } catch (error) {
      console.error('\n🔥 Critical test failure:', error);
      return null;
    } finally {
      await this.cleanup();
    }
  }
}

// Run the test suite
async function main() {
  const tester = new DeepAgentsUITester();
  const results = await tester.runAllTests();
  
  // Exit with appropriate code
  if (results && results.failed === 0) {
    process.exit(0);
  } else {
    process.exit(1);
  }
}

main().catch(console.error);