get_list_names = '''SELECT DISTINCT listName AS 'List Name' FROM groceryLists'''

get_list_items = '''SELECT itemName AS 'item', quantity, priority, category FROM groceryLists WHERE listName=%s ORDER BY category ASC'''

