import sqlite3

conn = sqlite3.connect('instance/hospital_demo.db')
rows = conn.execute('SELECT * FROM login_logs ORDER BY log_id DESC').fetchall()
conn.close()

if not rows:
    print("No login logs yet. Run the attack scripts first.")
else:
    print(f"{'ID':<5} {'Timestamp':<22} {'Username':<20} {'IP':<15} {'OK':<5} {'Role':<12} {'Note'}")
    print('-' * 95)
    for r in rows:
        print(f"{r[0]:<5} {r[1]:<22} {r[2]:<20} {str(r[3]):<15} {r[4]:<5} {str(r[5]):<12} {str(r[6])}")
