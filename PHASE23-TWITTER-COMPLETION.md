# MISSION: Complete the Twitter Thread via Safari do JavaScript

## ⚠️ YOUR SINGLE KPI: Post tweets 4-8 as replies to tweet 3

Tweets 1-3 are live from @sipiteno. Tweets 4-8 are in `content/twitter-thread.md`. Post them using Safari's `do JavaScript` AppleScript bridge — the EXACT method that successfully posted the HN comment in Phase 22.

---

## RULE ZERO
Zero fabrication. Every tweet posted must be verified via the X API or a fresh Safari capture. Never mention cron. Never touch memory. Sign as "Maryan K."

---

## THE BREAKTHROUGH METHOD

In Phase 22, the agent successfully posted an HN comment using this pattern:
```bash
osascript -e 'tell application "Safari" to do JavaScript "..."'
```

This works because Safari's `do JavaScript` command doesn't have the Chrome `execute` quoting bug. Safari is also logged into X.com (or can be).

**The approach:**
1. Open X.com in Safari
2. Navigate to tweet 3 (the last posted tweet)
3. Use `do JavaScript` to click the reply button
4. Use `do JavaScript` with native setter + dispatchEvent to fill the reply textarea
5. Use `do JavaScript` to click the reply submit button
6. Wait 2 seconds, verify the tweet appeared
7. Repeat for tweets 5-8

This is the same React native-setter technique documented in the `macos-browser-driving` skill Section 12 — it bypasses all React form validation by writing directly to the DOM element's value property and dispatching synthetic events.

---

## STEP-BY-STEP EXECUTION

### Step 1: Read the thread content
```bash
read_file path="/Users/sipi/agentshield/content/twitter-thread.md"
```
Extract tweets 4, 5, 6, 7, and 8.

### Step 2: Enable Safari JavaScript from Apple Events (if not already enabled)

The HN comment was posted successfully, so this is likely already enabled. But verify:

```bash
osascript -e 'tell application "Safari" to do JavaScript "document.title" in document 1' 2>&1
```

If this returns a title → JS bridge is active. Proceed to Step 3.

If this returns an error like "Not authorized to send Apple events to Safari" → the setting needs to be toggled in Safari → Settings → Advanced → "Allow JavaScript from Apple Events". This is a one-time human toggle. Document it for Maryan if needed.

### Step 3: Open X.com in Safari

```bash
open -a Safari "https://x.com/sipiteno"
```
Wait 3 seconds.

### Step 4: Find tweet 3

We need the URL of tweet 3 to navigate to it. If we don't know it, search for it:

```bash
osascript -e 'tell application "Safari" to do JavaScript "
var tweets = document.querySelectorAll('article[data-testid=\"tweet\"]');
var result = '';
for (var i = 0; i < Math.min(tweets.length, 5); i++) {
    var text = tweets[i].innerText.substring(0, 100);
    result += i + ': ' + text + '\\n';
}
result;
" in document 1' 2>&1
```

This returns the first 100 chars of the first 5 tweets on the profile. Identify which one is tweet 3 (it should start with something like "I tried everything" or similar based on the thread content).

### Step 5: Navigate to tweet 3's individual page

Find the tweet 3 permalink. Click on it, or construct the URL:

```bash
osascript -e 'tell application "Safari" to do JavaScript "
var tweets = document.querySelectorAll('article[data-testid=\"tweet\"]');
var links = document.querySelectorAll('a[href*=\"/status/\"]');
var urls = [];
for (var i = 0; i < Math.min(links.length, 10); i++) {
    var href = links[i].href;
    if (href.includes('/status/') && !urls.includes(href)) {
        urls.push(href);
    }
}
urls.join('\\n');
" in document 1' 2>&1
```

Navigate to tweet 3's URL:
```bash
open -a Safari "TWEET3_URL"
```
Wait 3 seconds.

### Step 6: Click the reply button on tweet 3

```bash
osascript -e 'tell application "Safari" to do JavaScript "
var replyBtn = document.querySelector('[data-testid=\"reply\"]');
if (replyBtn) {
    replyBtn.click();
    'clicked reply';
} else {
    'reply button not found';
}
" in document 1' 2>&1
```

Wait 2 seconds.

### Step 7: Fill the reply textarea with tweet 4

This is the critical step. X.com uses a React-controlled `contenteditable` div for the compose box, NOT a standard textarea. The `macos-browser-driving` skill Section 12 documents the native setter technique for React inputs, but for `contenteditable` divs, we need a different approach:

```bash
# First, find the compose box
osascript -e 'tell application "Safari" to do JavaScript "
var composeBox = document.querySelector('[data-testid=\"tweetTextarea_0\"]') || 
                 document.querySelector('[contenteditable=\"true\"]');
if (composeBox) {
    composeBox.className;
} else {
    'compose box not found';
}
" in document 1' 2>&1
```

If the compose box is found, inject text. For `contenteditable` divs, the approach is:

```bash
osascript -e 'tell application "Safari" to do JavaScript "
var composeBox = document.querySelector('[data-testid=\"tweetTextarea_0\"]') || 
                 document.querySelector('[contenteditable=\"true\"]');
if (composeBox) {
    // Focus the element
    composeBox.focus();
    
    // Set content via execCommand (deprecated but still works in WebKit)
    document.execCommand('selectAll', false, null);
    document.execCommand('insertText', false, 'TWEET 4 TEXT HERE');
    
    'text inserted';
} else {
    'compose box not found';
}
" in document 1' 2>&1
```

**IMPORTANT:** Replace `TWEET 4 TEXT HERE` with the actual text from tweet 4 in `content/twitter-thread.md`.

### Step 8: Submit the reply

```bash
osascript -e 'tell application "Safari" to do JavaScript "
// Find and click the reply/post button
var buttons = document.querySelectorAll('[data-testid=\"tweetButton\"]');
if (buttons.length > 0) {
    buttons[buttons.length - 1].click();
    'clicked post';
} else {
    // Try the reply-specific button
    var replyBtn = document.querySelector('[data-testid=\"tweetButtonInline\"]');
    if (replyBtn) {
        replyBtn.click();
        'clicked inline reply';
    } else {
        'post button not found';
    }
}
" in document 1' 2>&1
```

Wait 3 seconds.

### Step 9: Verify the tweet was posted

```bash
osascript -e 'tell application "Safari" to do JavaScript "
var tweets = document.querySelectorAll('article[data-testid=\"tweet\"]');
var first = tweets[0] ? tweets[0].innerText.substring(0, 200) : 'none';
first;
" in document 1' 2>&1
```

If the first tweet on the page contains the text of tweet 4 → success.

### Step 10: Repeat for tweets 5-8

For each remaining tweet:
1. The newly posted tweet should now be visible — navigate to it or find its reply button
2. Click reply on the newly posted tweet
3. Fill with the next tweet's content
4. Submit
5. Verify

**CRITICAL:** After each tweet, wait 3 seconds for the DOM to settle before attempting the next one.

---

## FALLBACK: If Safari do JavaScript fails

### Fallback A: Use `xurl` (requires one-time OAuth setup)

Check xurl auth:
```bash
xurl auth status 2>&1
```

If `my-app` still has `oauth2: (none)`:
- xurl needs the user to complete OAuth2 ONE TIME
- Document the exact setup steps (from the xurl skill):
  ```
  XURL SETUP (5 min, one time):
  1. Go to https://developer.x.com/en/portal/dashboard
  2. Create/open an app
  3. Set redirect URI to http://localhost:8080/callback
  4. Copy Client ID and Client Secret
  5. Run (OUTSIDE agent session):
     xurl auth apps add my-app --client-id YOUR_ID --client-secret YOUR_SECRET
     xurl auth oauth2 --app my-app
     xurl auth default my-app
  6. Verify: xurl auth status && xurl whoami
  ```

If xurl IS authenticated (after user completes setup):
```bash
# Find tweet 3's ID
xurl search "from:sipiteno" -n 5 2>&1

# Post tweet 4 as reply to tweet 3
xurl reply TWEET3_ID "TWEET 4 TEXT" 2>&1

# Post tweet 5 as reply to tweet 4
xurl reply TWEET4_ID "TWEET 5 TEXT" 2>&1

# Continue for tweets 6-8
```

### Fallback B: Use Safari foreground typing (simpler than do JavaScript)

1. Open X.com → navigate to tweet 3
2. Use `computer_use` to click the reply button (by element index from `mode='som'` capture)
3. Use foreground `type` to type the tweet text into the compose box
4. Use `computer_use` to click the post button

This is what worked for tweets 1-3 in Phase 21. It's context-heavy (600+ elements per capture) but proven. Use `max_elements=50` to limit context.

### Fallback C: Accept the limitation

If all approaches fail after 2 attempts each:
- Save the remaining tweets with clear instructions
- Report honestly: "Safari do JavaScript attempted. Failed because [reason]. Maryan needs to post tweets 4-8 manually from content/twitter-thread.md (3 minutes)."

---

## FINAL VERIFICATION

After posting (or attempting to post) all remaining tweets:

```bash
# Check the profile to see how many tweets are visible
osascript -e 'tell application "Safari" to do JavaScript "
var tweets = document.querySelectorAll('article[data-testid=\"tweet\"]');
tweets.length + ' tweets visible on profile';
" in document 1' 2>&1

# Product health
curl -s https://agentshield.fly.dev/health
curl -s https://agentshield.fly.dev/eval | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'{d[\"passed\"]}/{d[\"total\"]}')"

# DNS still works
dig agentshield.sipiteno.com A +short

# Commit
cd /Users/sipi/agentshield && git add -A && git commit -m "Phase 23: Twitter thread completion via Safari do JavaScript"
git log --oneline -3
```

---

## REPORT FORMAT

```
## Phase 23 — Twitter Thread Completion Report

### Method Used
[ ] Safari do JavaScript (execCommand insertText)
[ ] Safari foreground typing (computer_use type)
[ ] xurl CLI (if OAuth completed)
[ ] Manual fallback documented for Maryan

### Tweets Posted
| Tweet # | Content (first 50 chars) | Posted? | Verification |
|---------|--------------------------|---------|--------------|
| 4 | ... | YES/NO | tweet text found on page |
| 5 | ... | YES/NO | ... |
| 6 | ... | YES/NO | ... |
| 7 | ... | YES/NO | ... |
| 8 | ... | YES/NO | ... |

### Thread Status
- Total tweets live: [count]/8
- Thread complete: [YES / NO]

### Errors Encountered
[Any errors from Safari do JavaScript, compose box not found, post button not found, etc.]

### Quality
- Health: [ok/error]
- DNS: [resolves / not resolving]
- Git: [hash]

### Maryan Actions Required
- [ONLY if tweets couldn't be posted: exact 3-minute manual steps]
```

---

## HARD RULES

1. **KPI: Post tweets 4-8.** Use Safari `do JavaScript` first (it worked for HN). Fall back to foreground typing or xurl if needed.

2. **The execCommand insertText approach is the key technique.** X.com uses a `contenteditable` div, not a standard input. The standard native setter technique won't work. `document.execCommand('insertText', false, 'TEXT')` is the proven way to programmatically insert text into a contenteditable div in WebKit/Safari.

3. **Wait between tweets.** React needs time to process state updates. 3 seconds between each tweet.

4. **Verify every tweet after posting.** Don't assume success — check the DOM.

5. **Never mention cron. Never touch memory. Never fabricate.**

6. **If Safari do JavaScript is not authorized**, the toggle is: Safari → Settings → Advanced → "Allow JavaScript from Apple Events". This was already enabled for the HN comment in Phase 22, so it should still be active.
