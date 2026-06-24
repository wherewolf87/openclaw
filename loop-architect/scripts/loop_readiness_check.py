#!/usr/bin/env python3
"""Check whether a loop contract has the minimum controls for safe recurring agent work.

Usage:
  python3 loop_readiness_check.py path/to/loop-contract.md
  python3 loop_readiness_check.py --strict path/to/loop-contract.md
  python3 loop_readiness_check.py --strict path/to/loop-contract.md --verify-manifest references/source-evidence-manifest.md --state-template templates/state-file.md
"""
import argparse
import hashlib
import os
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

REQUIRED_HEADINGS = [
    'Plain English Job', 'Loop Type', 'Suitability', 'State', 'Sources',
    'Permissions', 'Runbook Per Wake', 'Verifier', 'Budget', 'Escalation',
    'Rollback / Stop', 'Logs / Proof', 'Review Council / Consensus',
    'Launch Prompt', 'First 3 Runs', 'Graduation Criteria',
]
REVIEW_ROLES = ['planner', 'builder', 'skeptic', 'verifier']
VALID_VERDICTS = {'APPROVED', 'CHANGES_NEEDED', 'BLOCKED'}
CONSENSUS_APPROVALS = {'UNANIMOUS APPROVED'}
RISKY_ACTIONS = {
    'deploy': ['deploy', 'deploying', 'deployed', 'deployment', 'release', 'releasing', 'released', 'ship', 'shipping', 'shipped', 'push', 'pushing', 'git push', 'push to origin', 'sync upstream', 'sync branch upstream', 'sync the branch upstream', 'synchronize upstream'],
    'merge': ['merge', 'merging', 'merged', 'merge pr', 'merge pull request', 'merge pull requests', 'land pr', 'land the pr', 'landing pr', 'land pull request', 'landing pull request', 'land the branch', 'sync branch', 'sync the branch', 'sync upstream', 'sync the branch upstream', 'synchronize branch', 'synchronize upstream', 'upstream branch'],
    'spend': ['spend', 'payment', 'purchase', 'money', 'paid', 'pay', 'pays', 'pay invoice', 'charge', 'charges', 'charged', 'charging', 'bill', 'bills', 'billed', 'billing', 'buy', 'checkout', 'credit card', 'debit card', 'paypal', 'venmo', 'zelle', 'crypto', 'bitcoin', 'btc', 'eth', 'ethereum', 'usdc', 'stablecoin', 'swift', 'sepa', 'iban', 'interac', 'giro', 'wire', 'wires', 'wire funds', 'wire transfer', 'wiretransfer', 'wire-transfer', 'wireout', 'western union', 'moneygram', 'cashapp', 'cash app', 'revolut', 'stripe', 'bank transfer', 'banktransfer', 'transfer', 'transfers', 'transfer funds', 'transfer money', 'transfer balance', 'transfer the balance', 'balance transfer', 'funds', 'refund', 'drain', 'top up', 'top-up', 'settle', 'settlement', 'remit', 'remits', 'remittance', 'disburse', 'disburses', 'disbursement', 'payout', 'payouts', 'withdraw', 'withdraws', 'withdrawal', 'withdraw balance', 'ach', 'invoice', 'invoices', 'payable', 'cash out', 'cashout', 'cash-out', 'vendor payment'],
    'send': ['send', 'sending', 'outbound message', 'external message', 'message', 'messages', 'messaging', 'msg', 'msgs', 'msging', 'pm', 'p m', 'im', 'i m', 'message customer', 'message customers', 'messaging customer', 'messaging customers', 'email', 'emails', 'emailing', 'reply to leads', 'notify', 'notifies', 'notifying', 'notification', 'dm', 'dms', 'dming', 'd m', 'direct message', 'broadcast', 'broadcasts', 'broadcasting', 'blast', 'blasts', 'shoot a note', 'shoot note', 'shoot a line', 'drop a note', 'drop a line', 'nudge', 'nudges', 'ping', 'pings', 'pinging', 'ring', 'rings', 'ringing', 'ring customer', 'ring the customer', 'page', 'pages', 'paging', 'pager', 'pagerduty', 'call', 'calls', 'calling', 'phone', 'text', 'texts', 'texting', 'sms', 'slack', 'slacking', 'whatsapp', 'whatsapping', 'chat', 'chats', 'chatting', 'chat with', 'reach out', 'outreach', 'contact via', 'message via', 'escalate to customer', 'escalate to customers', 'raise with customer', 'raise with customers', 'loop in customer', 'loop in customers', 'transmit', 'transmits', 'forward', 'forwards', 'dispatch', 'dispatches', 'relay', 'relays', 'hand off', 'handoff', 'contact', 'contacts', 'contacting', 'contact lead', 'contact customer', 'contact customers', 'fax', 'faxing', 'telegram', 'telegramming', 'signal', 'imessage', 'intercom', 'conversation', 'conversations', 'customer conversation', 'customer conversations', 'open conversation', 'open customer conversation', 'linkedin', 'support ticket', 'support tickets', 'open ticket', 'open support ticket', 'opening support ticket', 'zendesk', 'jira', 'service desk', 'servicedesk', 'helpdesk', 'discord'],
    'credential_edit': ['credential', 'credentials', 'credential edit', 'editing credentials', 'secret', 'secrets', 'api key', 'api keys', 'token', 'tokens', 'rotate credential', 'rotate credentials', 'rotating credentials'],
    'routing': ['routing', 'route', 'routes', 'reroute', 'rerouting', 'redirect', 'redirecting', 'dns', 'webhook target'],
    'delete': ['delete', 'deleting', 'remove data', 'rm -rf', 'destructive', 'wipe', 'wiping', 'purge', 'purging', 'truncate', 'truncating', 'drop', 'dropping', 'drop database', 'drop table', 'destroy records'],
    'production': ['production', 'prod', 'live', 'go live', 'going live', 'live customer', 'customer-facing'],
    'trade': ['trade', 'trading', 'buy stock', 'sell stock', 'swap'],
    'public_post': ['post publicly', 'public post', 'publish', 'publishing', 'posting', 'public action', 'tweet', 'tweeting'],
    'data_export': ['data export', 'export data', 'exporting data', 'export private data', 'exporting private data', 'export customer', 'exporting customer', 'export all customer', 'customer pii', 'pii', 'private data', 'customer records', 'external bucket', 'dump customer', 'dumping customer', 'exfiltrate', 'exfiltrating', 'exfiltration', 'paste customer data', 'paste data', 'upload customer data', 'upload data', 'share customer data', 'share data', 'google drive', 'drive', 'dropbox', 'sharepoint', 'transmit records', 'transmit customer data', 'forward customer data', 'forward records', 'hand off records', 'relay records', 'sftp', 'scp', 'rsync', 'ftp'],
}
RISKY_ACTION_IDS = list(RISKY_ACTIONS)
RISK_CONTROL_VALUES = {'forbidden', 'approval_required', 'allowed_after_approval'}
PLACEHOLDER_RE = re.compile(r'(\bTBD\b|\bTODO\b|\[[^\]]+\]|<[^>]+>)', re.IGNORECASE)
HEADING_RE = re.compile(r'^##\s+(.+?)\s*$', re.MULTILINE)
ROLE_LINE_RE = re.compile(r'^\s*(?:[-*]\s*)?(planner|builder|skeptic|verifier)\s*:\s*([^\n]+)', re.IGNORECASE | re.MULTILINE)
CONSENSUS_RE = re.compile(r'consensus\s+status\s*:\s*([^\n]+)', re.IGNORECASE)
REVIEW_TIMESTAMP_RE = re.compile(r'^\s*review\s+timestamp\s*:\s*([0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z)\s*$', re.IGNORECASE | re.MULTILINE)
FRESHNESS_TTL_RE = re.compile(r'^\s*freshness\s+ttl\s*:\s*([0-9]+)\s*(minute|minutes|hour|hours|day|days)\s*$', re.IGNORECASE | re.MULTILINE)
CONTROL_LINE_RE = re.compile(
    r'^\s*(?:[-*]\s*)?(deploy|merge|spend|send|credential[_ -]edit|routing|delete|production|trade|public[_ -]post|data[_ -]export)\s*:\s*([A-Za-z_ -]+)\s*$',
    re.IGNORECASE | re.MULTILINE,
)
LAUNCH_GATE_LINE_RE = re.compile(
    r'^\s*(?:[-*]\s*)?(consensus_required|on_missing_consensus|on_stale_consensus|on_not_unanimous_approved)\s*:\s*(.+?)\s*$',
    re.IGNORECASE | re.MULTILINE,
)
MANIFEST_HASH_RE = re.compile(r'(?:sha256(?: recorded in assessment)?): `([0-9a-f]{64})`', re.IGNORECASE)
MANIFEST_PATH_RE = re.compile(r'`((?:/|reports/)[^`]+)`')
PROOF_PATH_RE = re.compile(r'`?((?:/|reports/|\.{1,2}/|[A-Za-z0-9._@:+-]+/)[A-Za-z0-9._/@:+-][^`\s,;)]*)`?')
VERSIONED_PROOF_RE = re.compile(r'^v([0-9]+)-verification-summary\.md$')
ALLOWED_PROOF_ROOTS = [Path('/root/.openclaw/workspace/reports').resolve()]
REVIEWER_ID_RE = re.compile(r'^\s*(?:[-*]\s*)?(planner|builder|skeptic|verifier)_reviewer_id\s*:\s*([A-Za-z0-9_. -]+)\s*$', re.IGNORECASE | re.MULTILINE)
REQUIRED_REVIEWER_IDS = {'planner': 'OpenClaw', 'builder': 'Cody', 'skeptic': 'Sandy', 'verifier': 'Gemmy'}
MAX_FRESHNESS_TTL = timedelta(days=90)
LEET_TRANS = str.maketrans({'0': 'o', '1': 'i', '3': 'e', '4': 'a', '5': 's', '7': 't', '$': 's', '@': 'a'})
LAUNCH_OVERRIDE_RE = re.compile(r'\b(ignore|override|disregard|bypass|regardless|anyway)\b.{0,140}\b(gate|consensus|forbidden|approval|authority|deploy|merge|send|spend|trade|export data|export private data|publish|delete)\b|\b(deploy|merge|send|spend|trade|export data|export private data|publish|delete)\b.{0,80}\b(anyway|regardless|override|bypass)\b', re.IGNORECASE | re.DOTALL)
LAUNCH_CONDITIONAL_WIDEN_RE = re.compile(r'\b(consensus|receipt|gate|approval)\b.{0,80}\b(missing|stale|not approved|not unanimous|not unanimous approved)\b.{0,120}\b(proceed|continue|act|execute|perform|run|useful actions|deploy|merge|send|spend|trade|export data|export private data|publish|delete)\b|\b(missing|stale|not approved|not unanimous|not unanimous approved)\b.{0,80}\b(consensus|receipt|gate|approval)\b.{0,120}\b(proceed|continue|act|execute|perform|run|useful actions|deploy|merge|send|spend|trade|export data|export private data|publish|delete)\b', re.IGNORECASE | re.DOTALL)
LAUNCH_ACTION_RE = re.compile(r'\b(deploy|deploys|deploying|deployed|deployment|merge|merges|merging|merged|land|lands|land pr|land the pr|send|sends|sending|reply|replies|message|messages|messaging|msg|msgs|msging|pm|p\s*m|im|i\s*m|message customer|message customers|messaging customer|messaging customers|reach out|reach out to customer|reach out to customers|email|emails|emailing|notify|notifying|notifies|notification|notifications|dm|dms|direct message|direct messages|broadcast|broadcasts|ping|pings|ring|rings|ringing|call|calls|calling|phone|text|texts|texting|sms|slack|slacking|whatsapp|whatsapping|fax|faxing|telegram|telegramming|signal|imessage|chat|chats|chatting|contact|contacting|contacts|contact customer|contact customers|open support ticket|open ticket|zendesk|jira|service desk|servicedesk|helpdesk|support ticket|support tickets|ticket externally|discord|charge|charges|charging|bill|bills|billing|venmo|zelle|paypal|cashapp|revolut|moneygram|stripe|swift|sepa|ach|iban|interac|giro|bitcoin|ethereum|usdc|stablecoin|spend|payment|purchase|purchasing|refund|refunding|wire|wires|wiring|withdraw|withdraws|withdrawing|pay|pays|paying|transfer|transfers|transferring|remit|remits|remitting|disburse|disburses|disbursing|payout|payouts|invoice|invoices|trade|publish|publishes|public post|public posts|post|posts|export data|exports data|exporting data|export private data|exports private data|exporting private data|data export|sftp|scp|rsync|ftp|private data|customer pii|pii|customer records|delete|deletes|deleting|wipe|wiping|purge|purging|truncate|truncating|drop|dropping|push|pushes|pushing|git push|push to origin|release|releases|releasing|released|ship|ships|shipping|shipped|go live|goes live|going live|production|prod|live|reroute|reroutes|rerouting|route|routes|routing|redirect|redirects|redirecting|dns|webhook target|rotate|rotates|rotating|credential|credentials|api key|api keys|secret|secrets|token|tokens|commit|commits|committing|touch|touches|touching|touch file|touch files|update repository|update repository files|update repo|update repo files|repository files|repo files|write|writes|writing|update files|updates files|updating files|file update|file updates|patch|patches|patching|apply patch|applying patch|edit|editing|edits|modify|modifies|modifying|create|creates|creating|open pr|pull request|merge request|code change|code changes|file edit|file edits|change files|execute|act|proceed|continue|run|perform)\b', re.IGNORECASE)
LAUNCH_GRANT_RE = re.compile(r'\b(may|can|allowed|permitted|authorized|optional|go ahead|free to|still|anyway|regardless|skip|just|autonomously|directly|freely|empowered|encouraged)\b|\b(?:welcome|cleared|clear|good|ok|okay|free|entitled)\s+to\b|\bat\s+liberty\s+to\b|\bat\s+will\b|\bwithout\s+waiting\b|\bwithout\s+(?:review|council|consensus)\b|\bno\s+need\s+to\s+wait\b|\btreat all actions as permitted\b|\bdo\s+not\s+hesitate\s+to\b|\bdon[\'’]?t\s+hesitate\s+to\b|\bmust\s+not\s+delay\b|\bstop\s+second-guessing\b|\bapproval\s+(?:is\s+)?(?:not\s+needed|not\s+required|unnecessary|optional)\b|\bno\s+approval\s+(?:needed|required)\b|\bapproval\s+isn[\'’]?t\s+required\b|\bno\s+need\s+for\s+approval\b', re.IGNORECASE)
LAUNCH_NEGATIVE_CONSENSUS_RE = re.compile(r'\b(missing|stale|absent|expired|not approved|never approved|without approval|not unanimous|not unanimous approved)\b|\bapproval\s+(?:is\s+|be\s+)?lacking\b|\blacking\s+approval\b|\bapproval\s+missing\b|\bno\s+receipt(?:\s+exists)?\b|\bno\s+consensus\b|\bgate\s+is\s+absent\b|\bcouncil\s+has\s+not\s+approved\b|\bapproval\s+(?:is\s+)?(?:not\s+needed|not\s+required|unnecessary|optional)\b|\bno\s+approval\s+(?:needed|required)\b|\bapproval\s+isn[\'’]?t\s+required\b|\bno\s+need\s+for\s+approval\b', re.IGNORECASE)
LAUNCH_PROHIBITION_RE = re.compile(r"\b(never\s+(?:perform|do|execute|act|deploy|merge|send|spend|trade|export data|export private data|publish|delete|push|release|ship|use|touch|change)|do not|don\'t|must not|may not|cannot|can\'t|shall not|stop|stay report-only|forbidden|request review|approval_required)\b", re.IGNORECASE)
LAUNCH_SAFE_APPROVAL_RE = re.compile(r'\b(after|with|requires|required|explicit)\s+approval\b|\bapproval\s+required\b|\bapproval_required\b|\ballowed_after_approval\b', re.IGNORECASE)
LAUNCH_EXTERNAL_ACTION_INTENT_RE = re.compile(r'\b(?:open|start|begin|create|launch|initiate|continue|handle|reply to|respond to|contact via|outreach|message via|send via|escalate|escalating|raise with|loop in|page|paging|transmit|forward|dispatch|relay|hand off|handoff|ring|msg|pm|p\s*m|im|i\s*m|shoot|drop|nudge|blast|paste|upload|share|sync|syncing|synchronize|synchronizing)\b.{0,120}\b(?:intercom|customer|customers|lead|leads|prospect|prospects|client|clients|conversation|conversations|thread|threads|inbox|inboxes|chat|chats|dm|dms|email|emails|linkedin|ticket|tickets|pagerduty|records|data|partner|vendor|newsletter|note|line|contract|google drive|drive|dropbox|sharepoint|branch|branches|upstream|repo|repository|pull request|pr)\b|\b(?:outreach|contact via|message via|send via|escalate|escalating|raise with|loop in|page|paging|transmit|forward|dispatch|relay|hand off|handoff|ring|msg|pm|p\s*m|im|i\s*m|shoot|drop|nudge|blast|paste|upload|share|sync|syncing|synchronize|synchronizing)\b.{0,80}\b(?:customer|customers|lead|leads|intercom|linkedin|pagerduty|records|data|partner|vendor|newsletter|note|line|contract|google drive|drive|dropbox|sharepoint|branch|branches|upstream|repo|repository|pull request|pr)\b|\bd\s*m\b.{0,80}\b(?:customer|customers|lead|leads|client|clients|prospect|prospects)\b', re.IGNORECASE)
LAUNCH_ACTION_GRANT_RE = re.compile(r'\b(may|can|still|just|go ahead|proceed|continue|act|execute|perform|run|deploy|deploying|merge|merging|land|send|sending|message|messages|messaging|msg|msgs|msging|pm|p\s*m|im|i\s*m|message customer|message customers|messaging customer|messaging customers|reach out|reach out to customer|reach out to customers|reply|notify|dm|broadcast|ping|ring|call|phone|text|sms|slack|whatsapp|chat|contact|open support ticket|support ticket|discord|charge|charges|charging|bill|bills|billing|venmo|zelle|paypal|cashapp|revolut|moneygram|stripe|swift|sepa|ach|iban|interac|giro|bitcoin|ethereum|usdc|stablecoin|spend|refund|wire|withdraw|pay|transfer|remit|disburse|payout|invoice|trade|export data|export private data|publish|delete|wipe|purge|truncate|drop|push|release|ship|commit|write|update files|file update|patch|apply patch|edit|modify|create|permitted|authorized|allowed|optional)\b', re.IGNORECASE)
LAUNCH_RISKY_ACTION_WORDS = r'(deploy|deploys|deploying|deployed|merge|merges|merging|merged|land|lands|land pr|land the pr|send|sends|message|messages|messaging|msg|msgs|msging|pm|p\s*m|im|i\s*m|message customer|message customers|messaging customer|messaging customers|reach out|reach out to customer|reach out to customers|reply|replies|email|emails|emailing|notify|notifying|notifies|dm|dms|broadcast|broadcasts|ping|pings|ring|rings|ringing|call|calls|calling|phone|text|texts|texting|sms|slack|slacking|whatsapp|whatsapping|fax|faxing|telegram|telegramming|signal|imessage|chat|chats|chatting|contact|contacting|contacts|contact customer|contact customers|open support ticket|open ticket|zendesk|jira|service desk|servicedesk|helpdesk|support ticket|support tickets|ticket externally|discord|charge|charges|charging|bill|bills|billing|venmo|zelle|paypal|cashapp|revolut|moneygram|stripe|swift|sepa|ach|iban|interac|giro|bitcoin|ethereum|usdc|stablecoin|spend|pay|pays|purchase|refund|wire|wires|withdraw|withdraws|transfer|transfers|remit|remits|disburse|disburses|payout|payouts|invoice|invoices|trade|publish|publishes|post|posts|delete|deletes|deleting|wipe|wiping|purge|purging|truncate|truncating|drop|dropping|push|pushes|pushing|git push|push to origin|release|releases|releasing|released|ship|ships|shipping|shipped|go live|goes live|going live|production|prod|live|reroute|reroutes|rerouting|route|routes|routing|redirect|redirects|redirecting|dns|webhook target|rotate|rotates|rotating|credential|credentials|api key|api keys|secret|secrets|token|tokens|commit|commits|committing|touch|touches|touching|touch file|touch files|update repository|update repository files|update repo|update repo files|repository files|repo files|write|writes|writing|update files|updates files|updating files|file update|file updates|patch|patches|patching|apply patch|applying patch|edit|editing|edits|modify|modifies|modifying|create|creates|creating|open pr|pull request|merge request|code change|code changes|file edit|file edits|change files)'
LAUNCH_SAFE_PROHIBITION_RE = re.compile(r"^\s*(?:never|do\s+not|don'?t|dont|must\s+not|may\s+not|cannot|can'?t|cant|shall\s+not)\b.{0,120}\b" + LAUNCH_RISKY_ACTION_WORDS + r"\b.{0,100}\b(?:without|unless|until)\s+(?:explicit\s+|human\s+|council\s+|unanimous\s+)?approval\b", re.IGNORECASE)
LAUNCH_STOP_UNTIL_ACTION_RE = re.compile(r"\b(?:never|do\s+not|don'?t|dont|must\s+not)\s+(?:stop|pause|halt|quit)\b.{0,100}\b(?:until|before)\b.{0,100}\b" + LAUNCH_RISKY_ACTION_WORDS + r"\b", re.IGNORECASE)
LAUNCH_IMPERATIVE_GRANT_RE = re.compile(r'^\s*(?:please\s+)?(?:\w+\s+){0,4}(?:and\s+)?' + LAUNCH_RISKY_ACTION_WORDS + r'\b', re.IGNORECASE)
LAUNCH_TEMPORAL_IMPERATIVE_RE = re.compile(r'(?:^|\b)(?:(?:each|every)\s+\w+|then|always|once\b[^,]*,?|after\b[^,]*,?|when\b[^,]*,?|whenever\b[^,]*,?)\s+(?:\w+\s+){0,5}?' + LAUNCH_RISKY_ACTION_WORDS + r'\b', re.IGNORECASE)
LAUNCH_SUBJECT_GRANT_RE = re.compile(r'\b(?:you|the agent|the worker|the loop|agent|worker|loop|it)\s+(?:will|shall|should|must|ought\s+to|(?:is|are)\s+expected\s+to|expected\s+to|(?:is|are)\s+going\s+to|going\s+to)\b.{0,100}\b' + LAUNCH_RISKY_ACTION_WORDS + r'\b', re.IGNORECASE)
LAUNCH_THIRD_PERSON_ACTION_RE = re.compile(r'\b(?:the agent|the worker|the loop|agent|worker|loop|it)\s+(?:deploys|deploying|merges|merging|lands|commits|committing|pushes|pushing|edits|editing|updates files|updating files|sends|notifies|notifying|dms|dming|broadcasts|broadcasting|pings|pinging|rings|ringing|calls|calling|texts|texting|slacks|slacking|chats|chatting|contacts|contacting|touches|touching|pays|paying|wires|wiring|withdraws|withdrawing|transfers|transferring|rotates|rotating|goes live|going live|replies|writes|writing|patches|patching|publishes|publishing|deletes|deleting)\b', re.IGNORECASE)
LAUNCH_WRITE_INTENT_RE = re.compile(r'\b(commit|commits|touch|touches|touch file|touch files|push|pushes|write|writes|writing|update files|updates files|updating files|file update|file updates|patch|patches|patching|apply patch|applying patch|edit|editing|edits|modify|modifies|modifying|create|creates|creating|code change|code changes|file edit|file edits|change files|merge request|open pr|pull request)\b', re.IGNORECASE)
LAUNCH_FORBIDDEN_ENUM_ITEMS = {
    'merge', 'deploy', 'delete', 'spend', 'trade', 'email', 'public post', 'post',
    'credential edit', 'credential change', 'routing change', 'production change',
    'outbound message', 'message', 'send', 'publish', 'money', 'purchase',
    'comment', 'comments', 'ticket', 'tickets', 'email', 'emails', 'webpage',
    'webpages', 'file', 'files', 'tool output', 'tool outputs', 'payload',
    'payloads', 'external payload', 'external payloads', 'source', 'sources',
    'event', 'events', 'webhook', 'webhooks', 'support ticket', 'support tickets',
    'zendesk ticket', 'jira issue', 'helpdesk ticket', 'service desk ticket',
}
RECEIPT_ROW_RE = re.compile(r'^\s*(?:[-*]\s*)?(planner|builder|skeptic|verifier)\s*/\s*(APPROVED|CHANGES_NEEDED|BLOCKED)\s*/\s*([^/\n]+)\s*/\s*([^/\n]+)\s*/\s*(\S.+?)\s*$', re.IGNORECASE | re.MULTILINE)
NONFINAL_COUNCIL_RE = re.compile(r'\b(changes[_ -]+needed|blocked|rejected|majority|partial|pending|approved\s+if|approved\s+pending|approval\s+pending|unanimous\s+approved\s+if|never\s+approved|not\s+approved|no\s+consensus|missing\s+consensus|no\s+receipt|receipt\s+missing|gate\s+absent)\b', re.IGNORECASE)


def sections(text):
    matches = list(HEADING_RE.finditer(text))
    result = {}
    for i, match in enumerate(matches):
        title = match.group(1).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        result[title] = text[start:end].strip()
    return result


def meaningful(value):
    lines = [line.strip() for line in value.splitlines()]
    lines = [line for line in lines if line and not line.startswith('<!--')]
    joined = '\n'.join(lines)
    return len(joined) >= 12 and not PLACEHOLDER_RE.fullmatch(joined)


def strip_fenced_blocks(text):
    kept = []
    in_fence = False
    fence = None
    for line in text.splitlines():
        stripped = line.lstrip()
        if in_fence:
            if stripped.startswith(fence):
                in_fence = False
                fence = None
            continue
        if stripped.startswith('```') or stripped.startswith('~~~'):
            in_fence = True
            fence = stripped[:3]
            continue
        if line.startswith('    ') or line.startswith('\t'):
            continue
        kept.append(line)
    return '\n'.join(kept)


def normalize_verdict(raw):
    value = re.sub(r'[^A-Za-z_ ]', ' ', raw)
    value = re.sub(r'\s+', ' ', value).strip().upper()
    if value in VALID_VERDICTS:
        return value
    if value in CONSENSUS_APPROVALS:
        return 'UNANIMOUS APPROVED'
    if value.startswith('REJECTED'):
        return 'REJECTED'
    if value.startswith('PENDING'):
        return 'PENDING'
    if value.startswith('APPROVED BY MAJORITY') or value.startswith('MAJORITY APPROVED'):
        return 'MAJORITY APPROVED'
    return value or 'MISSING'


def normalize_action_id(raw):
    return re.sub(r'[^a-z0-9]+', '_', raw.lower()).strip('_')


def normalize_control_value(raw):
    value = re.sub(r'[^a-z_ ]', ' ', raw.lower())
    value = re.sub(r'\s+', ' ', value).strip()
    if 'forbidden' in value or value == 'forbid':
        return 'forbidden'
    if 'approval' in value or 'approve' in value:
        if 'allow' in value:
            return 'allowed_after_approval'
        return 'approval_required'
    if value in {'allowed_after_approval', 'allowed after approval'}:
        return 'allowed_after_approval'
    if 'allowed' in value or value == 'allow':
        return 'allowed'
    return value.replace(' ', '_') or 'missing'


def parse_council(council):
    clean_council = strip_fenced_blocks(council)
    roles = {}
    role_counts = {}
    for role, verdict in ROLE_LINE_RE.findall(clean_council):
        role = role.lower()
        role_counts[role] = role_counts.get(role, 0) + 1
        roles.setdefault(role, normalize_verdict(verdict))
    consensus_match = CONSENSUS_RE.search(clean_council)
    consensus = normalize_verdict(consensus_match.group(1)) if consensus_match else 'MISSING'
    reviewer_ids = {}
    reviewer_counts = {}
    for role, value in REVIEWER_ID_RE.findall(clean_council):
        role = role.lower()
        reviewer_counts[role] = reviewer_counts.get(role, 0) + 1
        reviewer_ids.setdefault(role, value.strip())
    return roles, role_counts, consensus, reviewer_ids, reviewer_counts


def review_receipt_block(clean_council, label):
    pattern = re.compile(r'^\s*' + re.escape(label) + r'\s*:\s*(.*?)(?=^\s*(?:Plan review receipt|Final review receipt|Consensus status|Review timestamp|Freshness TTL|Reviewer identities)\s*:|\Z)', re.IGNORECASE | re.MULTILINE | re.DOTALL)
    match = pattern.search(clean_council)
    return match.group(1).strip() if match else ''


def is_relative_to(path, root):
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def proof_path_allowed(candidate):
    try:
        resolved = candidate.resolve()
    except OSError:
        return False
    return any(is_relative_to(resolved, root) for root in ALLOWED_PROOF_ROOTS)


def versioned_proof_is_current(candidate):
    match = VERSIONED_PROOF_RE.match(candidate.name)
    if not match:
        return True
    versions = []
    for peer in candidate.parent.glob('v*-verification-summary.md'):
        peer_match = VERSIONED_PROOF_RE.match(peer.name)
        if peer_match and peer.is_file():
            versions.append(int(peer_match.group(1)))
    return not versions or int(match.group(1)) == max(versions)


def proof_path_exists(proof, base_dirs):
    matches = PROOF_PATH_RE.findall(proof)
    if not matches:
        return False
    for match in matches:
        candidate = resolve_aux_path(match, base_dirs)
        if not (candidate.exists() and candidate.is_file() and proof_path_allowed(candidate)):
            return False
        if not versioned_proof_is_current(candidate):
            return False
    return True


def validate_review_receipts(council, base_dirs=None):
    errors = []
    base_dirs = base_dirs or [Path.cwd(), Path('/root/.openclaw/workspace')]
    clean_council = strip_fenced_blocks(council)
    for label in ['Plan review receipt', 'Final review receipt']:
        block = review_receipt_block(clean_council, label)
        if not block or not meaningful(block):
            errors.append(f'Review Council / Consensus missing non-placeholder {label}')
            continue
        rows = {}
        counts = {}
        for role, verdict, finding, fix, proof in RECEIPT_ROW_RE.findall(block):
            role = role.lower()
            counts[role] = counts.get(role, 0) + 1
            rows.setdefault(role, (verdict.upper(), finding.strip(), fix.strip(), proof.strip()))
        duplicate_roles = [role for role, count in counts.items() if count != 1]
        if duplicate_roles:
            errors.append(f'{label} receipt rows must appear exactly once per role: ' + ', '.join(sorted(duplicate_roles)))
        missing = [role for role in REVIEW_ROLES if role not in rows]
        if missing:
            errors.append(f'{label} must include structured rows for each role: ' + ', '.join(missing))
        for role, (verdict, finding, fix, proof) in rows.items():
            if verdict != 'APPROVED':
                errors.append(f'{label} role {role} is {verdict}, not APPROVED')
            if not all([finding, fix, proof]):
                errors.append(f'{label} role {role} must include finding, fix, and proof fields')
            elif not proof_path_exists(proof, base_dirs):
                errors.append(f'{label} role {role} proof path must resolve to an existing approved proof artifact')
    return errors


def has_nonfinal_council_language(council):
    clean_council = strip_fenced_blocks(council)
    safe_prefixes = (
        'plan review receipt', 'final review receipt', 'review timestamp',
        'freshness ttl', 'reviewer identities', 'required roles and final verdicts',
        'planner_reviewer_id', 'builder_reviewer_id', 'skeptic_reviewer_id',
        'verifier_reviewer_id',
    )
    for raw_line in clean_council.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        normalized = line.lower().lstrip('-* ')
        if normalized.startswith(safe_prefixes):
            continue
        if RECEIPT_ROW_RE.match(line):
            continue
        if NONFINAL_COUNCIL_RE.search(line):
            return True
    return False


def validate_reviewer_ids(reviewer_ids, reviewer_counts):
    errors = []
    missing = [role for role in REVIEW_ROLES if role not in reviewer_ids]
    duplicate_roles = [role for role, count in reviewer_counts.items() if count != 1]
    if duplicate_roles:
        errors.append('Review Council reviewer identity fields must appear exactly once per role: ' + ', '.join(sorted(duplicate_roles)))
    if missing:
        errors.append('Review Council / Consensus missing reviewer identity fields: ' + ', '.join(missing))
    seen = {}
    for role, expected in REQUIRED_REVIEWER_IDS.items():
        actual = reviewer_ids.get(role)
        if not actual:
            continue
        if actual != expected:
            errors.append(f'Review Council reviewer id for {role} must be {expected}')
        if actual in seen:
            errors.append(f'Review Council reviewer id {actual} is reused by {seen[actual]} and {role}')
        seen[actual] = role
    return errors


def permission_buckets(permissions):
    buckets = {'allowed': [], 'forbidden': [], 'approval': [], 'other': []}
    current = 'other'
    for raw_line in permissions.splitlines():
        line = raw_line.strip().lower()
        if not line:
            continue
        if line.startswith('allowed'):
            current = 'allowed'
            continue
        if line.startswith('forbidden'):
            current = 'forbidden'
            continue
        if 'approval' in line and ('required' in line or line.endswith(':')):
            current = 'approval'
            continue
        if line.startswith('risky action controls'):
            current = 'other'
            continue
        buckets[current].append(line)
    return {key: '\n'.join(lines) for key, lines in buckets.items()}


def deobfuscate_match_text(value):
    return value.lower().translate(LEET_TRANS)


def normalize_match_text(value):
    normalized = re.sub(r'[^a-z0-9]+', ' ', deobfuscate_match_text(value))
    return re.sub(r'\s+', ' ', normalized).strip()


def compact_match_text(value):
    return re.sub(r'[^a-z0-9]+', '', deobfuscate_match_text(value))


def has_action(text, terms):
    normalized_text = normalize_match_text(text)
    compact_text = compact_match_text(text)
    if not normalized_text:
        return False
    for term in terms:
        normalized_term = normalize_match_text(term)
        if normalized_term and re.search(r'\b' + re.escape(normalized_term) + r'\b', normalized_text):
            return True
        compact_term = compact_match_text(term)
        if len(compact_term) >= 4 and compact_term in compact_text:
            return True
    return False


def parse_risky_action_controls(permissions):
    controls = {}
    for action, value in CONTROL_LINE_RE.findall(permissions):
        controls[normalize_action_id(action)] = normalize_control_value(value)
    return controls


def validate_risky_permissions(full_text, permissions):
    errors = []
    buckets = permission_buckets(permissions)
    controlled = buckets['forbidden'] + '\n' + buckets['approval']
    allowed = buckets['allowed']
    controls = parse_risky_action_controls(permissions)
    missing_controls = [action for action in RISKY_ACTION_IDS if action not in controls]
    if missing_controls:
        errors.append('Risky action controls missing required action ids: ' + ', '.join(missing_controls))
    for action, value in controls.items():
        if action not in RISKY_ACTIONS:
            errors.append(f'unknown risky action control id: {action}')
            continue
        if value not in RISK_CONTROL_VALUES:
            errors.append(f'risky action {action} control must be forbidden, approval_required, or allowed_after_approval')
        if value == 'allowed':
            errors.append(f'risky action {action} cannot be allowed without approval')
    for action, terms in RISKY_ACTIONS.items():
        if not has_action(full_text, terms):
            continue
        action_label = action.replace('_', ' ')
        if has_action(allowed, terms) and action not in controls:
            errors.append(f'risky action {action_label} appears allowed without a matching structured control')
        if has_action(allowed, terms) and controls.get(action) == 'forbidden':
            errors.append(f'risky action {action_label} appears allowed but structured control says forbidden')
        if has_action(allowed, terms) and controls.get(action) not in {'approval_required', 'allowed_after_approval'}:
            errors.append(f'risky action {action_label} appears allowed without approval_required or allowed_after_approval control')
        elif action in controls and controls[action] in {'approval_required', 'allowed_after_approval', 'forbidden'}:
            continue
        elif not has_action(controlled, terms):
            errors.append(f'risky action {action_label} appears without per-action forbidden or approval control')
    return errors


def parse_launch_gate(launch):
    gate = {}
    for key, value in LAUNCH_GATE_LINE_RE.findall(launch):
        gate[key.lower()] = re.sub(r'\s+', ' ', value.strip().lower())
    return gate


def launch_fails_closed_on_council(launch):
    gate = parse_launch_gate(launch)
    allowed_failure_action = 'stay report-only, stop non-report-only authority, and request review'
    if gate.get('consensus_required', '').upper() != 'UNANIMOUS APPROVED':
        return False
    for key in ['on_missing_consensus', 'on_stale_consensus', 'on_not_unanimous_approved']:
        if gate.get(key, '') != allowed_failure_action:
            return False
    return True


def launch_sentences(launch):
    return [part.strip() for part in re.split(r'(?<=[.!?])\s+|\n+', launch) if part.strip()]


def launch_clauses(sentence):
    splitter = r'[;:]|,(?=\s)|\s+but\s+|\s+however\s+|\s+yet\s+|\s+and\s+(?=(?:you|the agent|agent|loop)\s+(?:may|can|are|is|will|should|must|go))'
    return [part.strip() for part in re.split(splitter, sentence, flags=re.IGNORECASE) if part.strip()]


def launch_bare_forbidden_item(clause):
    value = re.sub(r'^\s*(?:and|or)\s+', '', clause.strip().lower())
    value = re.sub(r'[^a-z0-9 ]+', ' ', value)
    value = re.sub(r'\s+', ' ', value).strip()
    return value in LAUNCH_FORBIDDEN_ENUM_ITEMS


LAUNCH_COMPACT_ACTION_TERMS = [
    'deploy', 'merge', 'send', 'message', 'email', 'notify', 'call', 'text',
    'slack', 'whatsapp', 'telegram', 'intercom', 'spend', 'payment',
    'purchase', 'refund', 'wire', 'withdraw', 'transfer', 'trade',
    'publish', 'post', 'delete', 'wipe', 'purge', 'truncate', 'drop',
    'push', 'release', 'ship', 'production', 'prod', 'live', 'reroute',
    'route', 'redirect', 'dns', 'rotate', 'credential', 'secret', 'token',
    'commit', 'touch', 'write', 'patch', 'edit', 'modify', 'create',
    'sync', 'synchronize', 'upstream', 'page', 'pager', 'pagerduty',
    'transmit', 'forward', 'dispatch', 'relay', 'handoff', 'shoot',
    'drop', 'nudge', 'blast', 'paste', 'upload', 'share', 'drive',
    'dropbox', 'sharepoint', 'ring', 'charge', 'bill', 'venmo',
    'zelle', 'paypal', 'cashapp', 'revolut', 'moneygram', 'stripe',
    'swift', 'sepa', 'iban', 'interac', 'giro', 'bitcoin', 'ethereum',
    'usdc', 'stablecoin', 'western',
]


def launch_has_compact_action(clause):
    compact = compact_match_text(clause)
    if not compact:
        return False
    for term in LAUNCH_COMPACT_ACTION_TERMS:
        compact_term = compact_match_text(term)
        if len(compact_term) >= 4 and compact_term in compact:
            return True
    return False


def launch_has_risky_action_term(clause):
    return any(has_action(clause, terms) for terms in RISKY_ACTIONS.values())


def launch_has_authority_widening(launch):
    for sentence in launch_sentences(launch):
        clauses = launch_clauses(sentence)
        sentence_has_negative_consensus = any(LAUNCH_NEGATIVE_CONSENSUS_RE.search(clause) for clause in clauses)
        for clause in clauses:
            has_action = LAUNCH_ACTION_RE.search(clause) or LAUNCH_EXTERNAL_ACTION_INTENT_RE.search(clause) or launch_has_compact_action(clause) or launch_has_risky_action_term(clause)
            if not has_action:
                continue
            if launch_bare_forbidden_item(clause):
                continue
            if LAUNCH_OVERRIDE_RE.search(clause) or LAUNCH_CONDITIONAL_WIDEN_RE.search(clause) or LAUNCH_STOP_UNTIL_ACTION_RE.search(clause):
                return True
            if LAUNCH_SAFE_PROHIBITION_RE.search(clause):
                continue
            has_grant = LAUNCH_GRANT_RE.search(clause)
            has_negative_consensus = LAUNCH_NEGATIVE_CONSENSUS_RE.search(clause) or sentence_has_negative_consensus
            has_action_grant = LAUNCH_ACTION_GRANT_RE.search(clause)
            has_unapproved_action = (
                LAUNCH_IMPERATIVE_GRANT_RE.search(clause)
                or LAUNCH_TEMPORAL_IMPERATIVE_RE.search(clause)
                or LAUNCH_SUBJECT_GRANT_RE.search(clause)
                or LAUNCH_THIRD_PERSON_ACTION_RE.search(clause)
            )
            if LAUNCH_PROHIBITION_RE.search(clause) and not has_grant:
                if has_unapproved_action and not LAUNCH_SAFE_APPROVAL_RE.search(clause):
                    return True
                continue
            if LAUNCH_SAFE_APPROVAL_RE.search(clause) and not has_negative_consensus and not has_grant:
                continue
            if has_negative_consensus and not LAUNCH_SAFE_APPROVAL_RE.search(clause):
                return True
            if has_grant:
                return True
            if has_negative_consensus and (has_action_grant or LAUNCH_WRITE_INTENT_RE.search(clause)):
                return True
            if has_unapproved_action and not LAUNCH_SAFE_APPROVAL_RE.search(clause):
                return True
    return False


def parse_review_timestamp(value):
    return datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)


def validate_review_freshness(council, now=None):
    errors = []
    now = now or datetime.now(timezone.utc)
    clean_council = strip_fenced_blocks(council)
    timestamp_match = REVIEW_TIMESTAMP_RE.search(clean_council)
    ttl_match = FRESHNESS_TTL_RE.search(clean_council)
    if not timestamp_match:
        errors.append('Review Council / Consensus must include machine-readable Review timestamp: YYYY-MM-DDTHH:MM:SSZ')
        return errors
    if not ttl_match:
        errors.append('Review Council / Consensus must include machine-readable Freshness TTL, for example: Freshness TTL: 30 days')
        return errors
    try:
        reviewed_at = parse_review_timestamp(timestamp_match.group(1))
    except ValueError:
        errors.append('Review Council / Consensus Review timestamp is invalid RFC3339 UTC')
        return errors
    amount = int(ttl_match.group(1))
    unit = ttl_match.group(2).lower()
    if unit.startswith('minute'):
        ttl = timedelta(minutes=amount)
    elif unit.startswith('hour'):
        ttl = timedelta(hours=amount)
    else:
        ttl = timedelta(days=amount)
    if reviewed_at - now > timedelta(minutes=5):
        errors.append('Review Council / Consensus timestamp is in the future')
    if ttl > MAX_FRESHNESS_TTL:
        errors.append('Review Council / Consensus Freshness TTL must be 90 days or less')
    if reviewed_at + ttl < now:
        errors.append('Review Council / Consensus receipt is stale according to Freshness TTL')
    return errors


def manifest_entries(manifest_text):
    entries = []
    unpaired = []
    for match in MANIFEST_HASH_RE.finditer(manifest_text):
        digest = match.group(1).lower()
        window = manifest_text[max(0, match.start() - 600):match.start()]
        paths = MANIFEST_PATH_RE.findall(window)
        if paths:
            entries.append((paths[-1], digest))
        else:
            unpaired.append(digest)
    return entries, unpaired


def resolve_aux_path(input_path, base_dirs):
    path = Path(input_path)
    if path.is_absolute():
        return path
    for base_dir in base_dirs:
        candidate = Path(base_dir) / path
        if candidate.exists():
            return candidate
    return Path(base_dirs[0]) / path


def verify_manifest(manifest_path, base_dirs):
    errors = []
    warnings = []
    manifest_path = resolve_aux_path(manifest_path, base_dirs)
    if not manifest_path.exists():
        return [f'evidence manifest not found: {manifest_path}'], warnings
    entries, unpaired = manifest_entries(manifest_path.read_text(encoding='utf-8', errors='ignore'))
    if unpaired:
        errors.extend(f'evidence manifest sha256 has no paired artifact path: {digest}' for digest in unpaired)
    if not entries:
        return [f'evidence manifest has no parseable sha256 entries: {manifest_path}'], warnings
    seen = set()
    for rel_path, expected in entries:
        key = (rel_path, expected)
        if key in seen:
            continue
        seen.add(key)
        artifact = resolve_aux_path(rel_path, base_dirs)
        if not artifact.exists():
            errors.append(f'evidence artifact missing: {rel_path}')
            continue
        if not proof_path_allowed(artifact):
            errors.append(f'evidence artifact path must be under approved proof roots: {rel_path}')
            continue
        if not artifact.is_file():
            errors.append(f'evidence artifact path must be a file: {rel_path}')
            continue
        actual = hashlib.sha256(artifact.read_bytes()).hexdigest()
        if actual != expected:
            errors.append(f'evidence artifact hash mismatch: {rel_path}')
    return errors, warnings


def validate_state_template(state_template_path, base_dirs=None):
    errors = []
    warnings = []
    base_dirs = base_dirs or [Path.cwd()]
    state_template_path = resolve_aux_path(state_template_path, base_dirs)
    if not state_template_path.exists():
        return [f'state template not found: {state_template_path}'], warnings
    text = state_template_path.read_text(encoding='utf-8', errors='ignore')
    yaml_text = text.split('\n## Run Log', 1)[0]
    yaml_lines = []
    for line in yaml_text.splitlines():
        if line.startswith('#') or not line.strip():
            continue
        yaml_lines.append(line)
        key_match = re.match(r'^([^\s:#][^:#]*):', line)
        if key_match and not key_match.group(1).isascii():
            errors.append(f'state template has non-ASCII key: {key_match.group(1)}')
    payload = '\n'.join(yaml_lines)
    try:
        import yaml
        parsed = yaml.safe_load(payload) or {}
    except Exception as exc:
        errors.append(f'state template YAML parse failed: {exc}')
        parsed = {}
    def visit_keys(value, path='root'):
        if isinstance(value, dict):
            for key, child in value.items():
                key_text = str(key)
                if not key_text.isascii():
                    errors.append(f'state template has non-ASCII key: {path}.{key_text}')
                visit_keys(child, f'{path}.{key_text}')
        elif isinstance(value, list):
            for index, child in enumerate(value):
                visit_keys(child, f'{path}[{index}]')

    required = [
        'loop_name', 'owner', 'mode', 'current_goal', 'sources',
        'untrusted_input_rule', 'allowed_actions', 'forbidden_actions',
        'verifier', 'harness', 'review_council', 'budget',
    ]
    if isinstance(parsed, dict):
        visit_keys(parsed)
        missing = [key for key in required if key not in parsed]
        if missing:
            errors.append('state template missing required keys: ' + ', '.join(missing))
    else:
        errors.append('state template YAML root must be a mapping')
    return errors, warnings


def validate_contract(path, strict):
    text = path.read_text(encoding='utf-8', errors='ignore')
    lower = text.lower()
    found = sections(text)
    errors = []
    warnings = []
    if strict and not text.isascii():
        errors.append('Strict mode requires ASCII-only contract text to prevent Unicode homoglyph or zero-width bypasses')

    for heading in REQUIRED_HEADINGS:
        if heading not in found:
            errors.append(f'missing required section: {heading}')
        elif not meaningful(found[heading]):
            errors.append(f'section is empty or placeholder-only: {heading}')

    permissions = found.get('Permissions', '')
    launch = found.get('Launch Prompt', '')
    launch_lower = launch.lower()
    state = found.get('State', '')
    verifier = found.get('Verifier', '')
    budget = found.get('Budget', '')
    sources = found.get('Sources', '')
    council = found.get('Review Council / Consensus', '')

    if 'forbidden' not in permissions.lower():
        errors.append('Permissions must list forbidden actions explicitly')
    if 'approval' not in permissions.lower() and 'approve' not in permissions.lower():
        errors.append('Permissions must name approval gates explicitly')
    errors.extend(validate_risky_permissions(text, permissions))

    if PLACEHOLDER_RE.search(state):
        errors.append('State contains placeholders; use an exact path/system/field')
    if PLACEHOLDER_RE.search(verifier):
        errors.append('Verifier contains placeholders; use exact pass/fail checks')
    if PLACEHOLDER_RE.search(budget):
        warnings.append('Budget contains placeholders; replace with concrete limits before launch')
    if 'untrusted' not in sources.lower():
        errors.append('Sources must describe untrusted input handling')

    roles, role_counts, consensus, reviewer_ids, reviewer_counts = parse_council(council)
    missing_roles = [role for role in REVIEW_ROLES if role not in roles]
    if missing_roles:
        errors.append('Review Council / Consensus missing required role verdicts: ' + ', '.join(missing_roles))
    duplicate_role_verdicts = [role for role, count in role_counts.items() if count != 1]
    if duplicate_role_verdicts:
        errors.append('Review Council role verdict lines must appear exactly once per role: ' + ', '.join(sorted(duplicate_role_verdicts)))
    for role in REVIEW_ROLES:
        verdict = roles.get(role)
        if verdict and verdict != 'APPROVED':
            errors.append(f'Review Council role {role} is {verdict}, not APPROVED')
    if consensus != 'UNANIMOUS APPROVED':
        errors.append('Review Council final consensus must be exactly UNANIMOUS APPROVED')
    errors.extend(validate_reviewer_ids(reviewer_ids, reviewer_counts))
    errors.extend(validate_review_receipts(council, [path.parent, Path.cwd(), Path('/root/.openclaw/workspace')]))
    if has_nonfinal_council_language(council):
        errors.append('Review Council / Consensus contains non-final, conditional, or non-unanimous language')
    errors.extend(validate_review_freshness(council))

    if 'never' not in launch_lower and 'forbidden' not in launch_lower:
        errors.append('Launch Prompt must restate forbidden actions or use a Never rule')
    if 'state' not in launch_lower:
        errors.append('Launch Prompt must instruct the agent to read/update state')
    if 'verifier' not in launch_lower and 'verify' not in launch_lower:
        errors.append('Launch Prompt must instruct the agent to verify results')
    if 'council' not in launch_lower and 'consensus' not in launch_lower:
        errors.append('Launch Prompt must enforce Review Council / Consensus before non-report-only authority')
    if not launch_fails_closed_on_council(launch):
        errors.append('Launch Prompt must include structured Launch gate fields that fail closed for missing, stale, or not UNANIMOUS APPROVED consensus')
    if launch_has_authority_widening(launch):
        errors.append('Launch Prompt contains override or authority-widening language that conflicts with fail-closed gates')
    if 'untrusted' not in launch_lower or not any(term in launch_lower for term in ['external', 'payload', 'source', 'event', 'tool output', 'email', 'webhook']):
        errors.append('Launch Prompt must treat external/tool/source payload instructions as untrusted data')

    if 'report-only' not in lower and 'report only' not in lower:
        warnings.append('Consider starting new loops in report-only mode')
    if not any(term in lower for term in ['harness', 'test', 'lint', 'ci', 'screenshot', 'reviewer', 'policy check', 'human approval']):
        warnings.append('Contract should name a cheap verifier or harness surface')
    if 'rollback' not in lower and 'stop' not in lower:
        errors.append('Contract must explain rollback or stop path')
    if 'proof' not in lower and 'log' not in lower:
        warnings.append('Contract should name proof/log location')

    return errors, warnings


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('contract', nargs='?')
    parser.add_argument('--strict', action='store_true')
    parser.add_argument('--verify-manifest', action='append', default=[])
    parser.add_argument('--state-template')
    args = parser.parse_args()

    errors = []
    warnings = []
    script_root = Path(__file__).resolve().parent.parent
    workspace_candidates = [
        os.environ.get('OPENCLAW_WORKSPACE'),
        os.environ.get('CLAUDE_PROJECT_DIR'),
        os.environ.get('PWD'),
        '/root/.openclaw/workspace',
    ]
    base_dirs = [Path.cwd(), script_root] + [Path(item) for item in workspace_candidates if item]

    if not args.contract and not args.verify_manifest and not args.state_template:
        print(json.dumps({'status': 'fail', 'score': 0, 'errors': ['contract path, --verify-manifest, or --state-template is required'], 'warnings': []}, indent=2))
        return 2

    if args.strict:
        if not args.contract:
            errors.append('strict mode requires a contract path for proof integrity')
        if not args.verify_manifest:
            errors.append('strict mode requires --verify-manifest for proof integrity')
        if not args.state_template:
            errors.append('strict mode requires --state-template for proof integrity')

    if args.contract:
        path = Path(args.contract)
        if not path.exists():
            print(json.dumps({'status': 'fail', 'score': 0, 'errors': [f'file not found: {path}'], 'warnings': []}, indent=2))
            return 2
        contract_errors, contract_warnings = validate_contract(path, args.strict)
        errors.extend(contract_errors)
        warnings.extend(contract_warnings)
        base_dirs.insert(1, path.parent)

    for manifest in args.verify_manifest:
        manifest_errors, manifest_warnings = verify_manifest(manifest, base_dirs)
        errors.extend(manifest_errors)
        warnings.extend(manifest_warnings)

    if args.state_template:
        state_errors, state_warnings = validate_state_template(args.state_template, base_dirs)
        errors.extend(state_errors)
        warnings.extend(state_warnings)

    score = max(0, 100 - 12 * len(errors) - 4 * len(warnings))
    status = 'pass' if score >= 85 and not errors and (not args.strict or not warnings) else 'warn' if not errors else 'fail'
    print(json.dumps({'status': status, 'score': score, 'errors': errors, 'warnings': warnings}, indent=2, sort_keys=True))
    return 0 if status == 'pass' else 1


if __name__ == '__main__':
    raise SystemExit(main())
