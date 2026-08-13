#!/usr/bin/env python3.11
"""
AgentShield Outreach Send Pipeline
Reads state.json, sends approved emails via Resend API.
30-minute spacing between sends. BCC sales@sipiteno.com.

Usage:
  python3.11 send_pipeline.py --dry-run    # Preview what would be sent
  python3.11 send_pipeline.py              # Send approved emails
"""
import json, os, sys, time, subprocess

STATE_PATH = os.path.expanduser('~/agentshield/outreach/state.json')

def load_state():
    with open(STATE_PATH) as f:
        return json.load(f)

def save_state(state):
    with open(STATE_PATH, 'w') as f:
        json.dump(state, f, indent=2)

def send_email(to, subject, body, dry_run=False):
    """Send via Resend curl."""
    # Load API key from vault
    # The vault decryption requires the portfolio venv
    vault_script = os.path.expanduser('~/portfolio/.venv/bin/python')
    
    cmd = [
        vault_script, '-c',
        f"""
import json, os
from cryptography.fernet import Fernet
key = open(os.path.expanduser('~/portfolio/config/.vault_key')).read().strip()
cipher = Fernet(key)
with open(os.path.expanduser('~/portfolio/config/vault_local.json')) as f:
    vault = json.load(f)
encrypted = vault.get('global:RESEND_API_KEY', {{}}).get('value_encrypted', '')
if encrypted:
    print(cipher.decrypt(encrypted.encode()).decode())
"""
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        api_key = result.stdout.strip()
    except:
        api_key = os.environ.get('RESEND_API_KEY', '')
    
    if not api_key:
        print("ERROR: No Resend API key found")
        return False
    
    # Send via curl
    payload = json.dumps({
        "from": "AgentShield <adrian@agentshield.fly.dev>",
        "to": [to],
        "bcc": ["sales@sipiteno.com"],
        "subject": subject,
        "text": body
    })
    
    if dry_run:
        print(f"  DRY RUN → {to}")
        print(f"  Subject: {subject}")
        print(f"  Body: {body[:100]}...")
        return True
    
    cmd = [
        'curl', '-s', '-X', 'POST', 'https://api.resend.com/emails',
        '-H', f'Authorization: Bearer {api_key}',
        '-H', 'Content-Type: application/json',
        '-d', payload
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    success = '"id"' in result.stdout
    
    # SECURITY: Never print the API key
    # Mask it in logs
    safe_output = result.stdout[:50].replace(api_key, '[REDACTED]') if api_key else result.stdout[:50]
    print(f"  {'✅' if success else '❌'} {to}: {safe_output}")
    
    return success

def main():
    dry_run = '--dry-run' in sys.argv
    
    state = load_state()
    emails = state.get('emails', [])
    
    # Only send emails with status 'approved'
    to_send = [e for e in emails if e.get('status') == 'approved']
    
    if not to_send:
        # Show drafts
        drafts = [e for e in emails if e.get('status') == 'draft']
        print(f"No approved emails to send.")
        print(f"Drafts awaiting approval: {len(drafts)}")
        print(f"To approve: edit {STATE_PATH} and change status from 'draft' to 'approved'")
        return
    
    print(f"Sending {len(to_send)} emails with 30-min spacing...")
    
    for i, email in enumerate(to_send):
        to = email['to']
        subject = email['subject']
        
        body = f"""{email['hook']}

{email['story']}

{email['offer']}

Try the risk calculator (no signup): {email.get('link', 'https://agentshield.fly.dev/tools/risk-calculator/')}

- Adrian
AgentShield | agentshield.fly.dev
"""
        
        print(f"\n[{i+1}/{len(to_send)}] Sending to {to}...")
        success = send_email(to, subject, body, dry_run)
        
        if success:
            email['status'] = 'sent'
            email['sent_at'] = time.strftime('%Y-%m-%d %H:%M')
        else:
            email['status'] = 'failed'
            email['error_at'] = time.strftime('%Y-%m-%d %H:%M')
        
        save_state(state)
        
        # 30 min spacing
        if i < len(to_send) - 1 and not dry_run:
            print("Waiting 30 minutes before next send...")
            time.sleep(1800)
    
    print("\nDone.")

if __name__ == '__main__':
    main()
