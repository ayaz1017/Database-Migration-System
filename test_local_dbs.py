from backend.services.discovery_service import DiscoveryService

def test_local_dbs():
    service = DiscoveryService()
    
    print("Testing MSSQL...")
    try:
        mssql_schema = service.connect_and_discover(
            host="127.0.0.1",
            port=1433,
            username="sa",
            password="Ayaz@123",
            db_type="mssql",
            database="migrated_sql"
        )
        print("MSSQL Success! Discovered databases:", mssql_schema["databases"])
    except Exception as e:
        print("MSSQL Error:", e)

    print("\nTesting MySQL...")
    try:
        mysql_schema = service.connect_and_discover(
            host="127.0.0.1",
            port=3306,
            username="root",
            password="Ayaz@123",
            db_type="mysql",
            database=None
        )
        print("MySQL Success! Discovered databases:", mysql_schema["databases"])
    except Exception as e:
        print("MySQL Error:", e)

    print("\nTesting PostgreSQL...")
    try:
        pg_schema = service.connect_and_discover(
            host="127.0.0.1",
            port=5432,
            username="postgres",
            password="Ayaz@123",
            db_type="postgres",
            database="postgres"
        )
        print("PostgreSQL Success! Discovered databases:", pg_schema["databases"])
    except Exception as e:
        print("PostgreSQL Error:", e)

if __name__ == "__main__":
    test_local_dbs()
