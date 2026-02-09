# Condition-Based Waiting

## Overview

Replace arbitrary timeouts (`sleep(5)`, `setTimeout(1000)`) with condition-based polling that waits for actual state changes.

**Core principle:** Wait for the condition you actually need, not an arbitrary amount of time.

## The Problem with Timeouts

**Anti-pattern:**
```javascript
// Start background process
startBackgroundJob();

// Wait "long enough" for it to finish
await sleep(5000); // 5 seconds - guess!

// Assume it's done
const result = getJobResult();
```

**Why this fails:**
- ❌ Too short → Race condition, intermittent failures
- ❌ Too long → Wastes time in tests and production
- ❌ Unpredictable → Works on fast machine, fails on slow CI
- ❌ Not explicit → Doesn't communicate what you're waiting for

## The Condition-Based Solution

**Correct pattern:**
```javascript
// Start background process
startBackgroundJob();

// Wait for the ACTUAL condition
await waitUntil(() => isJobComplete(), {
  timeout: 10000,
  interval: 100
});

// Now we KNOW it's done
const result = getJobResult();
```

**Why this works:**
- ✅ Explicit → Clear what we're waiting for
- ✅ Fast → Returns immediately when ready
- ✅ Robust → Works on any machine speed
- ✅ Safe → Has timeout for failure cases

## Implementation

### Basic Wait Function

```javascript
/**
 * Wait until condition returns true
 * @param {Function} condition - Function that returns true when ready
 * @param {Object} options - { timeout: ms, interval: ms }
 */
async function waitUntil(condition, options = {}) {
  const timeout = options.timeout || 10000; // 10 second default
  const interval = options.interval || 100;  // Check every 100ms
  const startTime = Date.now();
  
  while (true) {
    // Check condition
    if (await condition()) {
      return true; // Success!
    }
    
    // Check timeout
    if (Date.now() - startTime > timeout) {
      throw new Error(`Timeout waiting for condition after ${timeout}ms`);
    }
    
    // Wait before next check
    await sleep(interval);
  }
}

// Helper
function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}
```

### With Better Error Messages

```javascript
async function waitUntil(condition, options = {}) {
  const timeout = options.timeout || 10000;
  const interval = options.interval || 100;
  const description = options.description || 'condition';
  const startTime = Date.now();
  
  while (true) {
    const result = await condition();
    
    if (result) {
      return true;
    }
    
    if (Date.now() - startTime > timeout) {
      throw new Error(
        `Timeout after ${timeout}ms waiting for: ${description}`
      );
    }
    
    await sleep(interval);
  }
}

// Usage with description
await waitUntil(
  () => fileExists('/path/to/file'),
  { 
    timeout: 5000,
    description: 'file to be created'
  }
);
```

## Common Use Cases

### 1. File System Operations

❌ **Wrong:**
```javascript
fs.writeFileSync('output.txt', data);
await sleep(100); // Hope it's written?
const content = fs.readFileSync('output.txt');
```

✅ **Right:**
```javascript
fs.writeFileSync('output.txt', data);
await waitUntil(
  () => fs.existsSync('output.txt'),
  { description: 'output.txt to exist' }
);
const content = fs.readFileSync('output.txt');
```

### 2. Database Operations

❌ **Wrong:**
```javascript
database.insert(record);
await sleep(500); // Wait for replication?
const found = database.find(record.id);
```

✅ **Right:**
```javascript
database.insert(record);
await waitUntil(
  async () => {
    const found = await database.find(record.id);
    return found !== null;
  },
  { description: 'record to be replicated' }
);
```

### 3. UI Testing

❌ **Wrong:**
```javascript
button.click();
await sleep(1000); // Wait for dialog?
const dialog = document.querySelector('.dialog');
```

✅ **Right:**
```javascript
button.click();
await waitUntil(
  () => document.querySelector('.dialog') !== null,
  { description: 'dialog to appear' }
);
const dialog = document.querySelector('.dialog');
```

### 4. API Polling

❌ **Wrong:**
```javascript
const jobId = await startAsyncJob();

// Poll with fixed delays
for (let i = 0; i < 10; i++) {
  await sleep(1000);
  const status = await checkJobStatus(jobId);
  if (status === 'complete') break;
}
```

✅ **Right:**
```javascript
const jobId = await startAsyncJob();

await waitUntil(
  async () => {
    const status = await checkJobStatus(jobId);
    return status === 'complete';
  },
  { 
    timeout: 30000,
    interval: 1000,
    description: 'async job to complete'
  }
);
```

### 5. Process Startup

❌ **Wrong:**
```javascript
const server = startServer();
await sleep(2000); // Hope server is ready?
await fetch('http://localhost:3000/health');
```

✅ **Right:**
```javascript
const server = startServer();

await waitUntil(
  async () => {
    try {
      const response = await fetch('http://localhost:3000/health');
      return response.ok;
    } catch {
      return false; // Not ready yet
    }
  },
  { 
    timeout: 10000,
    description: 'server to be ready'
  }
);
```

## Choosing Good Conditions

### ✅ Good Conditions

**Explicit state checks:**
```javascript
() => jobStatus === 'complete'
() => fileExists(path)
() => element.isDisplayed()
() => queue.isEmpty()
```

**Measurable properties:**
```javascript
() => array.length > 0
() => counter >= expectedValue
() => response.status === 200
```

### ❌ Bad Conditions

**Arbitrary time:**
```javascript
() => Date.now() - start > 5000 // Just use sleep() instead!
```

**Unreliable checks:**
```javascript
() => Math.random() > 0.5 // Non-deterministic
```

## Timeout Values

Choose timeouts based on:

- **Normal operation:** 2-3x expected duration
- **Network calls:** 5-10 seconds
- **File I/O:** 1-5 seconds  
- **Process startup:** 10-30 seconds
- **Tests:** Be generous (avoid flaky tests)

**Example:**
```javascript
// File usually takes 100ms to write
await waitUntil(
  () => fileExists(path),
  { timeout: 1000 } // 10x normal time
);

// API call usually takes 2 seconds
await waitUntil(
  () => jobComplete(),
  { timeout: 10000 } // 5x normal time
);
```

## Integration with Testing Frameworks

### Jest/Vitest

```javascript
test('background job completes', async () => {
  const jobId = await startJob();
  
  await waitUntil(
    async () => {
      const status = await getJobStatus(jobId);
      return status === 'complete';
    },
    { timeout: 5000 }
  );
  
  const result = await getJobResult(jobId);
  expect(result).toBe('success');
}, 10000); // Jest timeout should be > waitUntil timeout
```

### Browser Testing (Playwright/Puppeteer)

Most browser testing frameworks have built-in waiting:

```javascript
// Playwright already does condition-based waiting!
await page.waitForSelector('.dialog', { timeout: 5000 });
await page.waitForFunction(() => window.jobComplete === true);

// But you can still use custom conditions
await waitUntil(
  async () => {
    const text = await page.textContent('.status');
    return text === 'Ready';
  }
);
```

## When Timeouts Are Acceptable

**Legitimate uses of sleep/timeout:**

1. **Rate limiting:**
   ```javascript
   await sleep(1000); // Respect API rate limit
   ```

2. **Intentional delays (UX):**
   ```javascript
   await sleep(300); // Let animation complete
   ```

3. **Retry backoff:**
   ```javascript
   await sleep(retryCount * 1000); // Exponential backoff
   ```

**Not legitimate:**
- Waiting for async operations to complete
- Waiting for state changes
- "Making sure" something happened

## Common Mistakes

### ❌ Mistake 1: Checking Too Frequently

```javascript
// Wasteful - checks every 10ms
await waitUntil(condition, { interval: 10 });
```

**Fix:** Use reasonable intervals (100-500ms for most cases)

### ❌ Mistake 2: No Description

```javascript
await waitUntil(complexCondition, { timeout: 5000 });
// Error: "Timeout after 5000ms waiting for: condition"
// What condition?? 
```

**Fix:** Always add description for debugging

### ❌ Mistake 3: Synchronous Condition Doing Async Work

```javascript
// WRONG - condition should be async
await waitUntil(
  () => fetch(url), // Returns Promise, not boolean!
  { timeout: 5000 }
);
```

**Fix:** Make condition async:
```javascript
await waitUntil(
  async () => {
    try {
      await fetch(url);
      return true;
    } catch {
      return false;
    }
  }
);
```

## Integration with Systematic Debugging

Use condition-based waiting to:
- **Replace flaky timeout-based code** you discover during debugging
- **Add robust waiting** after finding race conditions
- **Make tests deterministic** when debugging test failures

This is a supporting technique used during **Phase 4: Implementation** of systematic debugging.

See main `SKILL.md` for the complete debugging process.
