"""Compact a saved Figma get_design_context payload.

The MCP writes oversized responses to a JSON file of {type,text} parts. This
pulls the biggest part (the JSX), prints the asset constants, then prints the
markup with the noisiest attributes stripped so the structure is readable.

    python _build/ctx.py <saved-file> [--full] [--grep TEXT]
"""
import json
import re
import sys

path = sys.argv[1]
full = '--full' in sys.argv
grep = sys.argv[sys.argv.index('--grep') + 1] if '--grep' in sys.argv else None

parts = json.load(open(path, encoding='utf-8'))
jsx = max((p.get('text', '') for p in parts), key=len)

consts = re.findall(r'const (\w+) = "([^"]+)"', jsx)
for k, v in consts:
    print('CONST %-14s %s' % (k, v))
print('--- %d consts' % len(consts))

body = jsx[jsx.index('export default'):] if 'export default' in jsx else jsx
if not full:
    body = re.sub(r'data-node-id="[^"]*"', '', body)
    body = re.sub(r'\s+style=\{\{ fontVariationSettings[^}]*\}\}', '', body)
    body = re.sub(r'font-\[family-name:[^\]]*\]\s*', '', body)
    body = re.sub(r'\[word-break:break-word\]\s*', '', body)
    body = re.sub(r'(content-stretch|shrink-0|relative|max-w-none|block|inset-0|size-full|min-h-px|leading-\[0\]|text-\[0px\]) ', '', body)
    body = re.sub(r'className=""', '', body)
    body = re.sub(r'[ ]{2,}', ' ', body)
    body = re.sub(r'\n\s*\n', '\n', body)

if grep:
    for i, ln in enumerate(body.split('\n')):
        if grep.lower() in ln.lower():
            print(i, ln.strip()[:400])
else:
    print(body)
