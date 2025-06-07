import time
import shutil
from pathlib import Path
from sqlalchemy import create_engine, inspect, text
from app.database.models import Base
from app.config import DATABASE_URL

print("Starting database reset...")

db_path = Path(DATABASE_URL.replace("sqlite:///", "").replace("//", "/"))
print(f"Database path: {db_path}")

if db_path.exists():
    backup_path = db_path.parent / f"{db_path.stem}_backup_{int(time.time())}.db"
    print(f"Creating backup at: {backup_path}")
    try:
        shutil.copy2(db_path, backup_path)
        print("Backup created successfully")
    except Exception as e:
        print(f"Warning: Could not create backup: {e}")

db_path.parent.mkdir(parents=True, exist_ok=True)

print("\nSetting up database...")
try:
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        print("Dropping existing tables...")
        Base.metadata.drop_all(bind=conn, checkfirst=True)
    
    print("Creating new tables...")
    Base.metadata.create_all(bind=engine)
    
    with engine.connect() as conn:
        inspector = inspect(engine)
        columns = inspector.get_columns('wallets')
        private_key_col = next((col for col in columns if col['name'] == 'private_key'), None)
        
        if private_key_col and private_key_col['nullable'] is False:
            print("\n[WARNING] private_key column is still NOT NULL. Fixing...")
            conn.execute(text("DROP TABLE IF EXISTS wallets"))
            Base.metadata.tables['wallets'].create(bind=engine)
            print("Recreated wallets table with correct schema")
    
    # Verify tables were created
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    print("\nSuccessfully created tables:")
    for table in tables:
        columns = inspector.get_columns(table)
        print(f"\n- {table}:")
        for col in columns:
            print(f"  - {col['name']}: {col['type']} {'(nullable)' if col['nullable'] else '(not null)'}")
    
    print("\n[SUCCESS] Database reset completed successfully!")
    
except Exception as e:
    print(f"\n[ERROR] Error setting up database: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
