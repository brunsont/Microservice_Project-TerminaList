import json
import zmq

def categorize_item(item_name, default_db_path = "category_db.json", custom_db_path = "custom_category_db.json"):
    """ Returns the category of the given item by cross referencing the default category file and custom category file"""
    with open(custom_db_path) as custom_db_file:
        with open(default_db_path) as default_db_file:
            default_category_db = json.load(default_db_file)
            custom_category_db = json.load(custom_db_file)
            # Checks the file of customized categories for the item, then, if found, returns it
            category = find_category(item_name, custom_category_db)
            if category:
                return category
            
            # Checks the default category file for the item
            category = find_category(item_name, default_category_db)
            if not category:
                # Item was not found in any category
                category.append("Unknown")
            return category 
        
def find_category(item_name, db):
    """Checks the given database for the category the given item falls under """
    item_name_lower = item_name.lower()
    matching_categories = []

    for category, item in db.items():
        for name in item:
            if item_name_lower in name.lower():
                matching_categories.append(category)
                break
    return matching_categories

def update_category(item_to_update, new_category, db_path = "custom_category_db.json"):
    """ Places the given item in the given category and removes the item from any previous category"""
    with open(db_path) as file:
        category_db = json.load(file)
    
    for category, items in category_db.items():
        # Removes the item from current category
        for name in items:
            if item_to_update == name:
                items.remove(item_to_update)
        # Adds the item to the new category
        if category == new_category:
            items.append(item_to_update)
            break
    
    # Saves the changes to the custom categories file 
    with open(db_path, "w") as file:
        json.dump(category_db, file)

def reset_categories():
    """" Clears all the custom catergories-items"""
    with open("custom_category_db.json", "w") as custom_file, open("empty_categories.json") as empty_file:
        json.dump(json.load(empty_file),custom_file)

def get_category_names():
    """ Returns a list of all the available categories"""
    with open("custom_category_db.json") as file:
        categories = json.load(file)
    category_names = []
    for name in categories:
        category_names.append(name)
    return category_names
        

def main():
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    try:
        socket.bind("tcp://*:2222")
    except zmq.ZMQError as e:
        print(f"Error binding socket: {e}")
        return

    while True:
        print("\nMicroservice B: Grocery Item Categorizer ready...")
        try:
            work_code = socket.recv_string()
            print(f"Work Code Received: {work_code}")
        except zmq.ZMQError as e:
            print(f"Error receiving work code: {e}")
            continue

        if work_code == 'Q':
            print("Quit code received.")
            break
        elif work_code == "RESET":
            reset_categories()
            print("Reset all custom categories.")
            try:
                socket.send_string("Reset successful")
                print("Custom Category reset successful")
            except zmq.ZMQError as e:
                print(f"Error sending reset successful message.")
            finally:
                continue
        elif work_code == "GET":
            category_names = get_category_names()
            try:
                socket.send_json(category_names)
                print("Sending a list of all category names.")
            except zmq.ZMQError as e:
                print(f"Error sending list of category names: {e}")
            finally:
                continue

        try:
            item_name = socket.recv_string()
            print(f"Item received: {item_name}")
        except zmq.ZMQError as e:
            print(f"Error receiving item name: {e}")
            continue

        if work_code == "CATEGORIZE":
            print(f"Categorizing {item_name}...")
            category = categorize_item(item_name)
            try:
                socket.send_json(category)
                print(f"Category is: {category}")
            except zmq.ZMQError as e:
                print(f"Error sending category to client: {e}")
                continue
        elif work_code == "UPDATE":
            try:
                new_category = socket.recv_string()
                print(f"New category is: {new_category}")
            except zmq.ZMQError as e:
                print(f"Error receiving new category: {e}")
                continue
            update_category(item_name, new_category)
            print("Category update successful.")
            try:
                socket.send_string("Success")
            except zmq.ZMQError as e:
                print(f"Error sending update success message to client: {e}")
    context.destroy()
    print("Server shut down.")

if __name__ == "__main__":
    main()