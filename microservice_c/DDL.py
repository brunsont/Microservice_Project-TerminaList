create_table = '''CREATE TABLE IF NOT EXISTS groceryLists (
    id INT AUTO_INCREMENT PRIMARY KEY,  
    listName VARCHAR(255) NOT NULL, 
    itemName VARCHAR(255) NOT NULL,
    quantity INT NOT NULL,
    priority VARCHAR(10) NOT NULL,           
    category VARCHAR(255) NOT NULL         
);'''

add_grocery_item = '''INSERT INTO groceryLists (listName, itemName, quantity, priority, category)
                    VALUES(%s, %s, %s, %s, %s);'''

edit_grocery_item ='''UPDATE groceryLists SET itemName=%s, quantity=%s, priority=%s, category=%s 
                        WHERE listName=%s AND itemName=%s; '''

delete_grocery_item = '''DELETE FROM groceryLists 
                            WHERE listName=%s AND itemName=%s;'''

delete_grocery_list = '''DELETE FROM groceryLists
                            WHERE listName=%s'''