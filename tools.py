import sqlite3
import os

def setup_db():
    """Initialize SQLite DB with mock inventory."""
    if os.path.exists('inventory.db'):
        os.remove('inventory.db')
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE inventory (item_name TEXT PRIMARY KEY, stock INTEGER)''')
    # Mock data
    c.execute("INSERT INTO inventory VALUES ('GadgetX', 100)")
    c.execute("INSERT INTO inventory VALUES ('WidgetY', 50)")
    c.execute("INSERT INTO inventory VALUES ('ThingZ', 0)")
    conn.commit()
    conn.close()

def query_inventory(item_name: str) -> int:
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    c.execute("SELECT stock FROM inventory WHERE item_name = ?", (item_name,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else -1

def mock_payment(vendor: str, amount: float) -> Dict:
    print(f"[MOCK PAY] Processing payment of ${amount} to {vendor}...")
    return {"status": "success", "transaction_id": "mock_tx_123"}
