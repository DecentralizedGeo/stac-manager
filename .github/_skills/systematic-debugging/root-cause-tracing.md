# Root Cause Tracing

## Overview

When debugging deep call stacks or complex data flow, trace backward from the symptom to find where the problem originates. Fix at the source, not at the symptom.

## The Backward Tracing Technique

### Step 1: Identify the Symptom

Start where the error manifests:
- What is the exact error or unexpected behavior?
- What value is wrong?
- Where does it fail?

**Example:**
```
Error: Cannot parse undefined as JSON at line 42
function processData(data) {
  return JSON.parse(data); // ← Crashes here, data is undefined
}
```

### Step 2: Ask "Where Did This Come From?"

For each bad value, trace one step backward:
- What function/module passed this value?
- What variable or parameter held this value?
- Where was it set or computed?

**Example:**
```
function handleRequest(request) {
  const rawData = request.body;
  processData(rawData); // ← rawData is undefined, came from request.body
}
```

### Step 3: Continue Tracing Up

Keep asking "where did THIS come from?" until you find:
- The original source of the bad value
- Where it should have been set but wasn't
- Where it was set incorrectly

**Example:**
```
router.post('/api/data', (req, res) => {
  handleRequest(req); // ← req.body is undefined
});

// Missing middleware!
// Should have: app.use(express.json())
```

**Root cause found:** Missing body parser middleware means `req.body` is never populated.

### Step 4: Fix at the Source

Once you've traced to the origin:
- Fix where the value should have been set
- Don't add checks at every layer to handle undefined
- Don't fix the symptom (adding `if (data)` checks everywhere)

**Correct fix:**
```
// Add the missing middleware at app setup
app.use(express.json());
```

**Wrong fix (symptom treatment):**
```
// DON'T do this - treats symptom, not cause
function processData(data) {
  if (!data) return null; // Band-aid!
  return JSON.parse(data);
}
```

## Tracing Checklist

For each step in your trace:

1. **Document the trail:**
   - Write down each function/location in the chain
   - Note what the value is at each step
   - Identify where it changes from correct to incorrect

2. **Add temporary logging if needed:**
   ```javascript
   console.log('At step A, value is:', value);
   console.log('At step B, value is:', value);
   console.log('At step C, value is:', value);
   ```

3. **Don't assume:**
   - Verify actual values at each step
   - Don't guess what "should" be there
   - Check your assumptions with evidence

4. **Stop when you find the source:**
   - The first place where the value becomes wrong
   - The place where it should have been set but wasn't
   - The configuration or initialization that's missing

## Common Patterns

### Pattern 1: Uninitialized Variables

**Symptom:** Variable is undefined deep in code

**Trace to:** Where variable should have been initialized but wasn't

**Fix:** Add proper initialization at source

### Pattern 2: Incorrect Data Transformation

**Symptom:** Data has wrong format or structure

**Trace to:** The transform/map/parse function that changed it incorrectly

**Fix:** Correct the transformation logic

### Pattern 3: Missing Configuration

**Symptom:** Feature doesn't work, values are missing

**Trace to:** Configuration file, environment variable, or setup step

**Fix:** Add the missing configuration at initialization

### Pattern 4: Wrong Assumptions About Input

**Symptom:** Code fails on certain inputs

**Trace to:** Where input is received and assumptions are made

**Fix:** Validate/handle input correctly at entry point

## When to Stop Tracing

You've found the root cause when:

✅ You understand WHY the value is wrong at this specific location

✅ Fixing it here would prevent the problem from occurring

✅ This is the EARLIEST point in the flow where the issue occurs

❌ DON'T stop at:
- Places where you could "work around" the issue
- Middle layers that are just passing bad data through
- Symptom locations where you could add defensive checks

## Example: Full Trace

**Problem:** User dashboard crashes with "Cannot read property 'name' of undefined"

```javascript
// Symptom location (Layer 4)
function renderUserProfile(user) {
  return `<div>${user.name}</div>`; // ← user is undefined HERE
}

// Trace back to Layer 3
function getUserProfile(userId) {
  const user = database.findUser(userId);
  renderUserProfile(user); // ← user is undefined, came from database
}

// Trace back to Layer 2
database.findUser = function(id) {
  return this.users[id]; // ← returns undefined, users[id] doesn't exist
}

// Trace back to Layer 1 (ROOT CAUSE)
database.users = {}; // ← Empty! Users were never loaded

// The actual problem
function initializeDatabase() {
  database.users = {};
  // Missing: database.users = loadUsersFromFile();
}
```

**Fix at the source (Layer 1):**
```javascript
function initializeDatabase() {
  database.users = loadUsersFromFile(); // ← FIX HERE
}
```

**Wrong fixes (treating symptoms):**
```javascript
// DON'T do these:

// Layer 4 - Band-aid
function renderUserProfile(user) {
  if (!user) return '<div>Unknown user</div>'; // Masks the real problem
  return `<div>${user.name}</div>`;
}

// Layer 3 - Band-aid  
function getUserProfile(userId) {
  const user = database.findUser(userId);
  if (!user) user = { name: 'Unknown' }; // Fake data!
  renderUserProfile(user);
}
```

## Integration with Systematic Debugging

Root cause tracing is a technique used in **Phase 1: Root Cause Investigation** of systematic debugging.

After tracing to the source:
- Proceed to Phase 2 (Pattern Analysis)
- Then Phase 3 (Hypothesis and Testing)
- Finally Phase 4 (Implementation with test)

See main `SKILL.md` for the complete four-phase process.
