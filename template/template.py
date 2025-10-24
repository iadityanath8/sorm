
# Table creation

CREATE_TABLE_TEMPLATE = """
CREATE TABLE IF NOT EXISTS {table_name} (
    {columns}
);
"""


# Insert record

INSERT_TEMPLATE = """
INSERT INTO {table_name} ({fields})
VALUES ({placeholders});
"""


# Select all records

SELECT_ALL_TEMPLATE = """
SELECT * FROM {table_name};
"""


# Filtered select

FILTER_TEMPLATE = """
SELECT * FROM {table_name} WHERE {conditions};
"""

# Delete records 

DELETE_TEMPLATE = """
DELETE FROM {table_name} WHERE {conditions};
"""


# Update record 

UPDATE_TEMPLATE = """
UPDATE {table_name}
SET {set_clause}
WHERE {conditions};
"""

# Inner Join
INNER_JOIN_TEMPLATE = """
SELECT {select_fields}
FROM {left_table}
INNER JOIN {right_table}
ON {join_condition}
{where_clause};
"""

#  Left Join
LEFT_JOIN_TEMPLATE = """
SELECT {select_fields}
FROM {left_table}
LEFT JOIN {right_table}
ON {join_condition}
{where_clause};
"""

# Right Join
RIGHT_JOIN_TEMPLATE = """
SELECT {select_fields}
FROM {left_table}
RIGHT JOIN {right_table}
ON {join_condition}
{where_clause};
"""
# Full outer jion
FULL_OUTER_JOIN_TEMPLATE = """
SELECT {select_fields}
FROM {left_table}
FULL OUTER JOIN {right_table}
ON {join_condition}
{where_clause};
"""
# Cross join
CROSS_JOIN_TEMPLATE = """
SELECT {select_fields}
FROM {left_table}
CROSS JOIN {right_table}
{where_clause};
"""
# Self join
SELF_JOIN_TEMPLATE = """
SELECT {select_fields}
FROM {table_name} AS t1
INNER JOIN {table_name} AS t2
ON {join_condition}
{where_clause};
"""