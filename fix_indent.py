with open('server.py', 'r') as f:
    c = f.read()

# Find and remove the broken block
broken_start = c.find('# ============ WEBSOCKET NOTIFICATIONS ============')
if broken_start != -1:
    broken_end = c.find('# ============ CONTRACT TEMPLATES DATA ============')
    if broken_end != -1:
        c = c[:broken_start] + c[broken_end:]
        print("Fixed indentation error")

with open('server.py', 'w') as f:
    f.write(c)

print("Done!")
