with open('server.py', 'r') as f:
    c = f.read()

# 1. Remove duplicate ConnectionManager (second occurrence)
first = c.find('class ConnectionManager:')
if first != -1:
    second = c.find('class ConnectionManager:', first + 1)
    if second != -1:
        # Find end of second class
        next_pos = c.find('\n\n', second + 1)
        if next_pos == -1:
            next_pos = len(c)
        c = c[:second] + c[next_pos:]
        print("Removed duplicate ConnectionManager")

# 2. Replace datetime.utcnow()
count = c.count('datetime.utcnow()')
c = c.replace('datetime.utcnow()', 'datetime.now(timezone.utc)')
print(f"Replaced {count} datetime.utcnow()")

# 3. Replace db: Session in Admin/Blog/Contract APIs
# Simple replacement for now
c = c.replace('db: Session = Depends(get_db),', 'db: AsyncSession = Depends(get_db),')
c = c.replace('db: Session = Depends(get_db)\n', 'db: AsyncSession = Depends(get_db)\n')
print("Replaced db: Session -> db: AsyncSession")

with open('server.py', 'w') as f:
    f.write(c)

print("v6.3 applied!")
