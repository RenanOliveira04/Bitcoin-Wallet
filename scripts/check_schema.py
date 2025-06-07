from sqlalchemy import create_engine, inspect
from app.config import DATABASE_URL

def check_schema():
    print("Connecting to database...")
    print(f"Database URL: {DATABASE_URL}")
    
    engine = create_engine(DATABASE_URL)
    inspector = inspect(engine)
    
    print("\nTables in database:")
    for table_name in inspector.get_table_names():
        print(f"\nTable: {table_name}")
        print("Columns:")
        for column in inspector.get_columns(table_name):
            print(f"  - {column['name']}: {column['type']} {'(nullable)' if column['nullable'] else '(not null)'}")

if __name__ == "__main__":
    check_schema()
