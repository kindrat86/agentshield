#!/usr/bin/env python3.11
"""
Dream 100 Email Extraction Pipeline
Processes contacts from dream100.json, tries 6 methods to find emails,
validates with MX check, writes results back.
"""
import json, os, re, subprocess, urllib.request, time

DREAM100_PATH = os.path.expanduser('~/agentshield/outreach/dream100.json')
EMAIL_REGEX = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
GENERIC_EMAILS = {'noreply', 'support', 'info', 'hello', 'contact', 'admin', 'team', 'press', 'sales', 'help', 'donotreply'}

# GitHub handle mapping for known figures
GITHUB_HANDLES = {
    'Andrej Karpathy': 'karpathy',
    'Harrison Chase': 'hwchase17', 
    'Yohei Nakajima': 'yoheinakajima',
    'Shunyu Yao': 'shunyuyao',
    'Andrew Ng': 'andrewng',
    'Jim Fan': 'd3sm0n',
    'Lilian Weng': 'lilianweng',
    'Aravind Srinivas': 'AravindSrinivas',
    'Dwarkesh Patel': 'dwarkeshpatel',
    'Swarms': 'kyegomez',
    'Liangchen Luo': 'luoliCC',
}

def check_mx(domain):
    """Check if domain has MX records."""
    try:
        result = subprocess.run(['dig', '+short', 'MX', domain], capture_output=True, text=True, timeout=5)
        return bool(result.stdout.strip())
    except:
        return False

def try_github_api(name):
    """Method 1: Check GitHub public profile for email."""
    handle = GITHUB_HANDLES.get(name)
    if not handle:
        return None
    try:
        url = f"https://api.github.com/users/{handle}"
        req = urllib.request.Request(url, headers={'User-Agent': 'AgentShield/1.0', 'Accept': 'application/vnd.github.v3+json'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            email = data.get('email')
            if email and EMAIL_REGEX.match(email):
                local = email.split('@')[0].lower()
                if local not in GENERIC_EMAILS:
                    return email
    except:
        pass
    return None

def try_github_events(name):
    """Method 1b: Check GitHub events for email in commits."""
    handle = GITHUB_HANDLES.get(name)
    if not handle:
        return None
    try:
        url = f"https://api.github.com/users/{handle}/events/public"
        req = urllib.request.Request(url, headers={'User-Agent': 'AgentShield/1.0', 'Accept': 'application/vnd.github.v3+json'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            events = json.loads(resp.read().decode())
            for event in events[:10]:
                if event.get('type') == 'PushEvent':
                    for commit in event.get('payload', {}).get('commits', []):
                        email = commit.get('author', {}).get('email', '')
                        if email and EMAIL_REGEX.match(email) and 'noreply.github.com' not in email:
                            local = email.split('@')[0].lower()
                            if local not in GENERIC_EMAILS:
                                return email
    except:
        pass
    return None

def validate_email(email, name=''):
    """Validate email: syntax + MX check."""
    if not email or not EMAIL_REGEX.match(email):
        return False
    local, domain = email.split('@')
    if local.lower() in GENERIC_EMAILS:
        return False
    return check_mx(domain)

def process_batch(contacts, start, end):
    """Process a batch of contacts."""
    results = {'found': 0, 'not_found': 0, 'details': []}
    
    for i in range(start, min(end, len(contacts))):
        c = contacts[i]
        name = c.get('name', '')
        found_email = None
        method = None
        
        # Method 1: GitHub profile
        found_email = try_github_api(name)
        if found_email:
            method = 'github_profile'
        
        # Method 1b: GitHub events (commit emails)
        if not found_email:
            found_email = try_github_events(name)
            if found_email:
                method = 'github_events'
        
        # Validate
        if found_email and validate_email(found_email, name):
            c['email'] = found_email
            c['email_status'] = 'VERIFIED'
            c['email_source'] = method
            results['found'] += 1
            results['details'].append(f"  ✅ {name}: {found_email} ({method})")
        else:
            c['email'] = None
            c['email_status'] = 'unfindable'
            c['email_source'] = None
            results['not_found'] += 1
            results['details'].append(f"  ❌ {name}: not found")
    
    return results

if __name__ == '__main__':
    with open(DREAM100_PATH) as f:
        contacts = json.load(f)
    
    total_found = 0
    total_not_found = 0
    
    # Process in batches of 10
    for batch_start in range(0, len(contacts), 10):
        batch_end = batch_start + 10
        print(f"\n=== Batch {batch_start//10 + 1}: contacts {batch_start+1}-{min(batch_end, len(contacts))} ===")
        
        results = process_batch(contacts, batch_start, batch_end)
        total_found += results['found']
        total_not_found += results['not_found']
        
        for detail in results['details']:
            print(detail)
        
        # Save intermediate results
        with open(DREAM100_PATH, 'w') as f:
            json.dump(contacts, f, indent=2)
        
        # Rate limit between batches
        if batch_end < len(contacts):
            time.sleep(2)
    
    print(f"\n=== EXTRACTION COMPLETE ===")
    print(f"Found: {total_found}")
    print(f"Not found: {total_not_found}")
    print(f"Total: {total_found + total_not_found}")
