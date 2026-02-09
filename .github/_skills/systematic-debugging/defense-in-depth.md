# Defense in Depth

## Overview

After finding and fixing a root cause, add validation at multiple system layers to prevent similar bugs and catch issues early.

**Core principle:** Don't just fix the bug—make the entire system more resilient by adding defensive checks at appropriate boundaries.

## When to Use

Use defense in depth AFTER you've:
- ✅ Completed root cause investigation
- ✅ Fixed the actual root cause
- ✅ Verified the fix works

Then add defensive layers to:
- Catch similar issues earlier in development
- Provide better error messages
- Prevent cascading failures
- Make debugging easier next time

## The Multi-Layer Approach

### Layer 1: Input Validation (Earliest Catch)

Validate at system boundaries:
- API endpoints
- User input forms
- External data sources
- Configuration files

**Example:**
```javascript
// API endpoint - first line of defense
router.post('/api/users', (req, res) => {
  // Validate required fields
  if (!req.body.email) {
    return res.status(400).json({ error: 'Email is required' });
  }
  
  if (!isValidEmail(req.body.email)) {
    return res.status(400).json({ error: 'Invalid email format' });
  }
  
  createUser(req.body);
});
```

### Layer 2: Function Preconditions (Contract Enforcement)

Check assumptions at function entry:
- Required parameters
- Type expectations
- Valid ranges or formats

**Example:**
```javascript
// Function precondition - enforce contract
function processUserData(userData) {
  if (!userData || typeof userData !== 'object') {
    throw new Error('processUserData requires a user object');
  }
  
  if (!userData.id) {
    throw new Error('User data must have an id');
  }
  
  // Now safe to proceed
  const result = transformUserData(userData);
  return result;
}
```

### Layer 3: Data Transformation Validation (Integrity Checks)

Verify transformations preserve required properties:

**Example:**
```javascript
// After transformation - verify output
function transformUserData(userData) {
  const transformed = {
    userId: userData.id,
    displayName: formatName(userData.firstName, userData.lastName)
  };
  
  // Defensive check on transformation
  if (!transformed.userId || !transformed.displayName) {
    throw new Error('User transformation failed - missing required fields');
  }
  
  return transformed;
}
```

### Layer 4: Persistence Validation (Storage Integrity)

Verify data before and after storage operations:

**Example:**
```javascript
// Before database write
function saveUser(user) {
  // Validate before persisting
  if (!user.id || !user.email) {
    throw new Error('Cannot save invalid user to database');
  }
  
  const result = database.insert('users', user);
  
  // Verify after persisting
  if (!result.success || !result.insertedId) {
    throw new Error('Database insertion failed');
  }
  
  return result;
}
```

## Choosing the Right Layers

### Don't Over-Defend

❌ **Wrong:** Duplicate checks everywhere
```javascript
function a(data) {
  if (!data) throw new Error(); // Check 1
  return b(data);
}

function b(data) {
  if (!data) throw new Error(); // Redundant check
  return c(data);
}

function c(data) {
  if (!data) throw new Error(); // Redundant check
  return process(data);
}
```

✅ **Right:** Strategic layer checks
```javascript
// Entry point - validate once
function a(data) {
  if (!data) throw new Error('Data required'); // Check at boundary
  return b(data);
}

function b(data) {
  // No check - trusts caller
  return c(data);
}

function c(data) {
  // No check - trusts caller
  return process(data);
}
```

### Strategic Validation Points

Add checks at:
- **System boundaries** (APIs, file I/O, network)
- **Component boundaries** (between major modules)
- **Critical operations** (database writes, external API calls)
- **After complex transformations** (parsing, serialization)

Don't add checks at:
- Every function in a call chain
- Internal helper functions
- Pure utility functions with clear contracts

## Example: Full Defense Strategy

**Original bug:** User registration crashed when email was undefined

**Root cause fix:**
```javascript
// Fixed: Added body parser middleware
app.use(express.json());
```

**Defense in depth additions:**

```javascript
// Layer 1: API endpoint validation
router.post('/api/register', (req, res) => {
  // Validate at entry point
  if (!req.body || !req.body.email || !req.body.password) {
    return res.status(400).json({ 
      error: 'Email and password are required' 
    });
  }
  
  registerUser(req.body);
});

// Layer 2: Service function precondition
function registerUser(userData) {
  // Enforce contract
  if (!userData.email || !userData.password) {
    throw new Error('registerUser requires email and password');
  }
  
  const hashedPassword = hashPassword(userData.password);
  const user = createUserRecord(userData.email, hashedPassword);
  
  return saveUser(user);
}

// Layer 3: Database function validation
function saveUser(user) {
  // Validate before persistence
  if (!user.email || !user.hashedPassword) {
    throw new Error('Invalid user record - missing required fields');
  }
  
  return database.insert('users', user);
}
```

**Result:**
- Original bug: Fixed at root (middleware)
- Future bugs: Caught early with clear error messages
- Debugging: Much easier with validation at each layer

## Validation vs. Error Handling

### Validation (Use for Programmer Errors)

Catch bugs in your own code:
```javascript
// This should NEVER happen if code is correct
if (!userId) {
  throw new Error('BUG: userId is required');
}
```

### Error Handling (Use for External Failures)

Handle expected failures from external sources:
```javascript
// This CAN happen due to network, user input, etc.
try {
  const response = await fetch(externalAPI);
  return await response.json();
} catch (error) {
  logger.error('External API call failed:', error);
  return null;
}
```

## Common Patterns

### Pattern 1: Required Fields

**Layer 1 (Entry):**
```javascript
if (!data.requiredField) {
  return error('Missing required field');
}
```

**Layer 2 (Processing):**
```javascript
assert(data.requiredField, 'Processing requires field to be set');
```

### Pattern 2: Type Validation

**Layer 1 (Entry):**
```javascript
if (typeof userId !== 'string') {
  return error('userId must be a string');
}
```

**Layer 2 (Processing):**
```javascript
assert(typeof userId === 'string', 'BUG: userId type changed');
```

### Pattern 3: Range Validation

**Layer 1 (Entry):**
```javascript
if (age < 0 || age > 150) {
  return error('Age must be between 0 and 150');
}
```

**Layer 2 (Storage):**
```javascript
assert(age >= 0 && age <= 150, 'BUG: Invalid age reached storage');
```

## Testing Your Defenses

After adding defensive layers:

1. **Test with invalid input** at each boundary
2. **Verify error messages** are clear and actionable
3. **Ensure failures are caught** at the earliest layer
4. **Confirm no cascading errors** - failures stop cleanly

## Integration with Systematic Debugging

Defense in depth is applied AFTER completing all four phases of systematic debugging:

1. Phase 1: Root Cause Investigation ✓
2. Phase 2: Pattern Analysis ✓
3. Phase 3: Hypothesis and Testing ✓
4. Phase 4: Implementation ✓
5. **THEN:** Add defensive layers

Don't add defensive layers INSTEAD of finding root cause. That's just masking the bug.

See main `SKILL.md` for the complete debugging process.
