import mysql.connector

class DatabaseUtil:

    def __init__(self, db_config):
        self.db_config = db_config
        self.connection = None
        
        try: 
            self.connection = mysql.connector.connect(**db_config) 
        except Exception as e:
            print(f"Error connecting to the database: {e}")

    def schema_details(self, database_name):
        schema_info_context = ""
        
        # Ensure connection is active before proceeding
        if not self.connection or not self.connection.is_connected():
            self.connection = mysql.connector.connect(**self.db_config)
            
        cursor = self.connection.cursor()

        schema_info_context = f"Database Schema: {database_name}\n"

        try: 
            # In MySQL, table_schema is the database name
            cursor.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = %s;", 
                (database_name,)
            )
            tables_list = cursor.fetchall()

            for table in tables_list:
                table_name = table[0]
                schema_info_context += f"\nTable: {table_name}\n"

                # Adding Columns & Data Types (Filtered by database_name to prevent cross-db duplicates)
                cursor.execute(
                    "SELECT column_name, data_type FROM information_schema.columns WHERE table_schema = %s AND table_name = %s;", 
                    (database_name, table_name)
                )
                columns_list = cursor.fetchall()

                for column in columns_list:
                    column_name = column[0]
                    data_type = column[1]
                    schema_info_context += f"  Column: {column_name}, Data Type: {data_type}\n"

                # Adding Sample Data
                cursor.execute(f"SELECT * FROM {database_name}.{table_name} LIMIT 5;")
                sample_data = cursor.fetchall()
                schema_info_context += "  Sample Data:\n"
                for row in sample_data:
                    schema_info_context += f"    {row}\n"

        except Exception as e:
            print(f"Error fetching schema details: {e}")
            schema_info_context = f"Error fetching schema details: {e}"

        finally:
            if cursor:
                cursor.close()
        
        return schema_info_context

    def execute_sql(self, query):
        try:
            if not self.connection or not self.connection.is_connected():
                self.connection = mysql.connector.connect(**self.db_config)
                
            cursor = self.connection.cursor()
            cursor.execute(query)
            
            # Fetch results if it's a SELECT query
            if cursor.description is not None:
                result = cursor.fetchall()
            else:
                result = f"Affected rows: {cursor.rowcount}"
                
            self.connection.commit()
            return str(result)
        except Exception as e:
            print(f"Error executing query: {e}")
            return None
        finally:
            if cursor:
                cursor.close()

    def close(self):
        """Safely close the database connection when completely done."""
        if self.connection and self.connection.is_connected():
            self.connection.close()


# ============================================================
# USAGE
# ============================================================

if __name__ == "__main__":
    
    # Note: MySQL uses 'database' instead of 'dbname'
    obj = DatabaseUtil({
        "host": "localhost",
        "port": 3306,
        "user": "root",               # Replace with your MySQL username
        "password": "",  # Replace with your MySQL password
        "database": "data_agent"   # Replace with your database name
    })

    # Pass your database name to extract the schema
    result = obj.schema_details("data_agent")

    with open("test_schema_details.txt", "w", encoding="utf-8") as f:
        f.write(result)
        
    print("Schema details saved to test_schema_details.txt")

    # Safely close the connection once all operations are complete
    obj.close()