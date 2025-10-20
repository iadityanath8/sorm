# example_usage.py
from template.template import CREATE_TABLE_TEMPLATE

# Table name to replace
table_name = ""

# Columns definition
columns = "id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, age INTEGER DEFAULT 0"

# Replace placeholders using str.format()
sql_query = CREATE_TABLE_TEMPLATE.format(
    table_name=table_name,
    columns=columns
)

print(sql_query)
