import json
from os import system, name
import os.path
import questionary
from questionary import Validator, ValidationError, unsafe_prompt, Separator
import time
import zmq 
import ports


def load_list():
    """Loads the list from a local JSON file. """
    try:
        with open("../microservice-a/shopping_lists.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}   # Returns an empty dictionary if the file does not exist
    
def save_list(shoppingList):
    """Saves the list to a local JSON file"""
    with open("../microservice-a/shopping_lists.json", "w") as f:
        json.dump(shoppingList, f, indent=4)

def count_lists(shoppingLists):
    """Counts the number of lists within the shopping list"""
    count = 1
    if shoppingLists != {}:
        for _ in shoppingLists:  
            count += 1
    return count

def startup():
    """Displays the Start Up Menu seen at launch"""
    clear()
    with open("text_files/launch_page.txt") as f:
        fContents = f.read()
        print(fContents)
    questionary.press_any_key_to_continue().ask()

def select_list(shoppingList):
    """Selects which list to work with"""
    clear()
    print("Select List")

    choices = []
    for lists in shoppingList:  # Loops through the list to create an array of the list names
        choices.append(str(lists))
    createNewListOption = "[Create New List]"
    importListOption = "[Import List]"
    sep = '-'*len(createNewListOption)
    choices.extend([Separator(sep), createNewListOption, importListOption])

    # cloudLists = import_cloud_list_names()
    questions =[ 
        {'type': 'select', 'name': 'selectedList', 'message':'Select which list to view: ', 'choices': choices, 'use_shortcuts':True},
        {'type':'select', 'name':'selectedImport','message':'Select a list to import from the cloud:\n(Caution: This action may overwrite the local copy of a list.)\n', 
         'choices':import_cloud_list_names(),'when': lambda input: input['selectedList'] == importListOption, 'use_shortcuts':True}]
    try:
        responses = unsafe_prompt(questions)
    except KeyboardInterrupt:
        return    
    selection = responses['selectedList']
    if responses['selectedList'] == createNewListOption:
        responses['selectedList'] = create_list(shoppingList)
    if responses.get('selectedImport'):
        responses['selectedList'] = import_cloud_list(shoppingList, responses['selectedImport'])
    return responses['selectedList']   # Returns the name of the selected list

def print_table_title(shoppingList, name):
    """Prints the name of the list as the table's title"""
    if len(shoppingList[name]) == 0:
        print(f"\n--- {name} ---")
        return
    longestItemWidth = get_min_column_width(shoppingList, name)
    header = "Item Name" + ' ' * longestItemWidth + 'quantity ' + 'priority ' + 'category'
    headerWidth = len(header)
    side_spaces = (headerWidth - len(name)) // 2
    print('-'*side_spaces,' ',name,' ','-'*side_spaces, sep='')    

def view_list(shoppingList, name):
    """Displays the shopping list"""
    if len(shoppingList[name]) == 0:
        print_table_title(shoppingList,name)
        print("This list is empty.\n")
        return -1
    
    minColWidth = get_min_column_width(shoppingList, name)
    doubleSpace = '  '
    i = 0
    print_table_title(shoppingList,name)
    # Creates a basic table
    print(add_blankspaces_to_word("Item Name", minColWidth), end='')
    print(add_blankspaces_to_word("Quantity", len("Quantity")), end=doubleSpace)
    print(add_blankspaces_to_word("Priority", len("Priority")), end=doubleSpace)
    print("Category")

    while (i < len(shoppingList[name])):
        print(add_blankspaces_to_word(shoppingList[name][i]['item'], minColWidth), end='')
        print(add_blankspaces_to_word(shoppingList[name][i]['quantity'], len('quantity')), end=doubleSpace)
        print(add_blankspaces_to_word(shoppingList[name][i]['priority'], len('priority')), end=doubleSpace)
        print(shoppingList[name][i]['category'])
        i += 1
    print("\n")

def get_min_column_width(shoppingList,listName):
    """Returns the character length of the longest item name in the list"""
    characters = 16
    for name in shoppingList[listName]:
        if len(name) > 16:
            characters = len(name)
    return characters

def add_blankspaces_to_word(word, spaces):
    """ Prints the word followed by a set of blankspaces"""
    space_length = spaces - len(word)
    blankSpaces = word
    for _ in range(space_length):
        blankSpaces += ' '
    return blankSpaces

def clear():
    """Clears/Resets the Terminal"""
    """
    This code is adapted from GeeksforGeeks article, How to clear screen in python? 
    Author: mohit_negi
    Source: https://www.geeksforgeeks.org/clear-screen-python/
    """
    # for windows
    if name == 'nt':
        _ = system('cls')

    # for mac and linux(here, os.name is 'posix')
    else:
        _ = system('clear')

class NumberValidator(Validator):
    """
    This code is adapted from the Questionary Python library documentation
    Authors: Tom Bocklisch and Kian Cross
    Source: https://questionary.readthedocs.io/en/stable/pages/advanced.html#validation
    """
    def validate(self, doc):
        try:
             int(doc.text)
        except ValueError:
            raise ValidationError(
                message='Please enter a number.',
                cursor_position=len(doc.text))
        if int(doc.text) < 0:
            raise ValidationError(
                message='Please enter a positive number.',
                cursor_position=len(doc.text))
        
def item_exists(shoppingList, listName, itemName):
    """Confirms if the item name is exists in the list"""
    i = 0
    size = len(shoppingList[listName])
    while i < size: 
        if shoppingList[listName][i]['item'] == itemName:   
            return True
        i += 1
    return False

def validate_item_name(shoppingList, listName, itemName):
    """Returns True if the itemName argument is not blank and if it's unique within the respective list"""
    if itemName == '':  # Blank item names are not allowed
        return False
    
    if item_exists(shoppingList, listName, itemName):   # If the itemName is a duplicate, return False
        return False
    
    return True

def create_list(shoppingList):
    """Create a new list"""
    clear()
    print("Create List")
    print("Create a new TerminaList to begin tracking your items.\n")
    listName = questionary.text("Enter a name for your list (Optional):", default='').ask()

    if listName == '':  # By default the list will be named based on how many lists already exist
        listName = f'Shopping List {count_lists(shoppingList)}'     

    shoppingList[listName] = []
    save_list(shoppingList)
    return listName

def add_item(shoppingList, name):
    """Adds an item to a shopping list """
    clear()
    print("Add Item to List")
    view_list(shoppingList, name)

    print("Follow the prompts to add a new item to your list.")
    print("(CTRL+C to cancel.)")

    questions = [
        {'type': 'text', 'name': 'item_name', 'message': 'Item name: ', 
        'validate': lambda txt:(True if validate_item_name(shoppingList, name, txt) else "Invalid: Item names must be unqique and cannot be blank.")},
        {'type': 'text', 'name': 'quantity', 'message': 'Quantity: ', 'validate': NumberValidator},
        {'type': 'select', 'name': 'priority', 'message': 'Select the Priority:', 'choices': ['Low', 'Normal', 'High'], 'default': 'Normal','use_shortcuts': True},
        {'type': 'confirm', 'message': 'Submit? ', 'name': 'submit', 'default': True}
    ]

    try:
        answers = unsafe_prompt(questions)
    except KeyboardInterrupt: 
        return
    else:    
        try:
            itemCategory = categorize_item(answers['item_name'])
        except KeyboardInterrupt:
            return
        package = {"item": answers['item_name'], "quantity": answers['quantity'], "priority": answers['priority'], "category": itemCategory}
        shoppingList[name].append(package)
        cloud_upload_item(name, package)

def edit_item(shoppingList, name):
    """Allows the user to select a list item to edit"""
    clear()
    print("Edit Item")
    view_list(shoppingList, name)

    choices = ["[Enter Manually]"]
    choices2 = []
    size = 0
    idx = 0
    # Creates an array of all the items on the list
    for items in shoppingList[name]:
        choices.append(str(items['item']))
        choices2.append(str(items['item']))
        size  += 1

    selectItems = [{'type': 'select', 'name': 'item_name', 'message': 'Select an item to edit: ', 'choices': choices, 'use_shortcuts': True},
                   {'type': 'autocomplete', 'name':'item_name', 'message': "Enter item name (case-sensitive): ", 
                    'choices':choices2, 'when': lambda x: x['item_name'] == "[Enter Manually]",
                     'validate': lambda input: item_exists(shoppingList, name, input) }]
    
    try:
        answer = unsafe_prompt(selectItems)
    except KeyboardInterrupt:
        return
    while idx < size: # This loop determines where in the list array the user's choice is located
        if shoppingList[name][idx]['item'] == answer['item_name']:
            break
        idx += 1
    
    questions = [
        {'type': 'text', 'name': 'item_name', 'message': 'Item name: ', 'default': shoppingList[name][idx]['item'], 
        'validate': lambda txt:(True if txt == shoppingList[name][idx]['item'] else validate_item_name(shoppingList, name, txt))},
        {'type': 'text', 'name': 'quantity', 'message': 'Quantity: ', 'default':shoppingList[name][idx]['quantity'], 'validate': NumberValidator},
        {'type': 'select', 'name': 'priority', 'message': 'Select the Priority:', 
         'choices': ['Low', 'Normal', 'High'], 'default': shoppingList[name][idx]['priority'], 'use_shortcuts': True},
        {'type': 'confirm', 'message': 'Submit? ', 'name': 'submit', 'default': True}
    ]

    try:
        print(f"Follow the prompts to Edit: {answer['item_name']}.")
        print("(Enter CTRL+C to cancel)")
        new_answers = unsafe_prompt(questions)
    except KeyboardInterrupt:
        return
    if new_answers['submit'] is False:
        return  
    if shoppingList[name][idx]['item'] is not new_answers['item_name']:
        shoppingList[name][idx]['category'] = categorize_item(new_answers['item_name'])
    try:
        if questionary.confirm("Edit category?").ask():
            new_category = edit_item_category(new_answers['item_name'])
            shoppingList[name][idx].update({"category": new_category})
    except KeyboardInterrupt:
        return

    shoppingList[name][idx].update({"item": new_answers['item_name'], "quantity": new_answers['quantity'], "priority": new_answers['priority']})
    package = {"item": new_answers['item_name'], "quantity": new_answers['quantity'], 
               "priority": new_answers['priority'],"category": shoppingList[name][idx]['category']}
    cloud_edit_item(name, answer['item_name'], package)

def category_sort(listName):
    """ Sorts the list by category in ascending order"""
    listName.sort(key= lambda item: item['category'])

def delete_item(shoppingList, listName):
    """Deletes a list item that the user selects"""
    clear()
    print("Delete Item")

    view_list(shoppingList, listName)

    choices = ["[Enter Manually]"]
    choices2 = []
    size = 0
    idx = 0
    # Creates an array of all the items on the list
    for items in shoppingList[listName]:
        choices.append(str(items['item']))
        choices2.append(str(items['item']))
        size  += 1
    
    selectItems = [{'type': 'select', 'name': 'item_name', 'message': 'Select an item to edit: ', 'choices': choices, 'use_shortcuts': True},
                   {'type': 'autocomplete', 'name':'item_name', 'message': "Enter item name (case-sensitive): ", 
                    'choices':choices2, 'when': lambda x: x['item_name'] == "[Enter Manually]" }]

    try:
        answer = unsafe_prompt(selectItems)
    except KeyboardInterrupt:
        return
    while idx < size: # This loop determines what index of the list the user's edit choice can be found
        if shoppingList[listName][idx]['item'] == answer['item_name']:
            break
        idx += 1
    
    try:
        newAnswerBool = questionary.confirm(f"Are you sure you want to delete {answer['item_name']} from the list? (This action cannot be undone.) ", default=False).ask()
    except KeyboardInterrupt:
        return
    
    if newAnswerBool:
        try:
            shoppingList[listName].pop(idx)
            cloud_delete_item(listName, answer['item_name'])
        except:
            transition_menu(f"Failed to delete {answer['item_name']} from the list")
    else:
        return

class ChangeActiveList(Exception):
    """Custom signal raised when the active list must be changed"""
    pass

def delete_grocery_list(shoppingLists, listName):
    """Deletes a grocery list"""
    print("\t\tWARNING!!")
    print("Deleting a List CANNOT be undone.")
    try:
        readyStatus = questionary.press_any_key_to_continue().ask()
        delete_confirmation = questionary.confirm(f"'{listName}' will be deleted. Proceed?",default=False).ask()
    except KeyboardInterrupt:
        return
    if delete_confirmation:
        del shoppingLists[listName]
        save_list(shoppingLists)
        cloud_delete_list(listName)
        raise ChangeActiveList("Error: No list selected")
    return 
    
def help_menu():
    """Displays the Help Menu"""
    clear()
    print("Help\n")
    with open("text_files/help.txt") as f:
        fContents = f.read()
        print(fContents)
    try:
        answer = questionary.select("Select an option: ", choices = ['More Information', 'Exit'], use_shortcuts=True).ask()
    except KeyboardInterrupt:
        return
    if answer == 'More Information':
        more_info_menu()
    elif answer == 'Exit':
        return

def more_info_menu():
    """Displays the More Information Menu"""
    clear()
    print("More Information\n")
    with open("text_files/more_info.txt") as f:
        fContents = f.read()
        print(fContents)
    
    questionary.select("Select an option: ", choices = ['Exit'], use_shortcuts=True).ask()

def transition_menu(mssg, timeout=3):
    """Displays a menu with a custom message for a set time then returns to the main menu"""
    clear()
    print(mssg)
    print(f"Returning to main menu in {timeout} seconds")
    time.sleep(timeout)

def manage_list_menu(shoppingList, listName):
    """Displays the additional options available to manage the list"""
    clear()    
    print("Viewing Your List")
    view_list(shoppingList, listName)

    exportOption ='Export List To Text File'
    resetCategoryOption = "Reset Category Personalizations to Default"
    deleteListOption = "Delete List"
    changeList = 'Switch to another List'
    exitOption = 'Exit'
    choices = [exportOption, resetCategoryOption, deleteListOption, changeList,exitOption]
    answer = questionary.select("Select an option: ",choices, use_shortcuts=True).ask()

    if answer == exportOption:
        export_to_text(listName)
    elif answer == resetCategoryOption:
        reset_categories()
    elif answer == deleteListOption:
        delete_grocery_list(shoppingList,listName)
    elif answer == changeList:
        raise ChangeActiveList("Select a new list")
    elif answer == exitOption:
        return
    

####
# Microservice A: Export to Text File
# The following function is used to communicate with 
#

def export_to_text(listName):
    """Exports the list to a text file"""
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect(ports.microservice_a)

    # Send request
    socket.send_string(listName)

    # Wait for response
    message = socket.recv()
    if message.decode('utf-8') == "JSON exported successfully.":
        fileLocation = os.path.abspath(f"../microservice-a/text_files/{listName}.txt")
        print("Your list has been successfully exported to a text file.")
        print(f"The file is located here: \n{fileLocation}")
        questionary.press_any_key_to_continue().ask()
    else:
        print("Error received, unable to print.")
        questionary.press_any_key_to_continue().ask()
 
    context.destroy()

### 
# Microservice B: Auto-Categorizer
# The following functions are used to communicate with Microservice B
# to automatically apply a category label to each item
#

def categorize_item(itemName):
    """ Determines the category of the given item"""
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect(ports.microservice_b)
    
    code = "CATEGORIZE"
    socket.send_string(code, flags=zmq.SNDMORE)
    socket.send_string(itemName)

    category = socket.recv_json()
    
    category = choose_category(category, itemName, socket)

    context.destroy()
    return category

def get_categories(socket):
    """Returns a list of the available item category options from a server"""
    code = "GET"
    socket.send_string(code)    
    return socket.recv_json()

def choose_category(options, itemName, socket):
    """Selects the appropriate category from the options provided."""
    categoryOptions = get_categories(socket)
   
    questions = [
        {'type': 'select', 'name':'category', 'message': f'\n{itemName} applies to multiple categories.\nSelect a category:',
         'choices': options, 'use_shortcuts': True},
        {'type': 'select', 'name': 'category', 'message': 'Select a category:', 
         'choices': categoryOptions, 'when': lambda choice: choice['category'] == "[Other]"}]
    try:
        if options[0] == "Unknown":
            print(f"\nCategory for {itemName} is Unknown.")
            answer = questionary.select(f'Select a category for {itemName}',categoryOptions,use_shortcuts=True).ask()
            finalCategory = answer
        elif len(options) > 1:
            options.append('[Other]')
            answer = unsafe_prompt(questions)
            finalCategory = answer['category']
        else:
            finalCategory = options[0]
            return finalCategory
    except KeyboardInterrupt:
        return
    result = update_category(finalCategory, itemName, socket)
    return finalCategory

def update_category(newCategory, itemName, socket):
    """Sends the server the new category for a given item"""
    code = "UPDATE"
    socket.send_string(code, zmq.SNDMORE)
    socket.send_string(itemName, zmq.SNDMORE)
    socket.send_string(newCategory)
    result = socket.recv_string()
    return result

def edit_item_category(itemName):
    """Takes user input to change an item's category and send the updates to the server"""
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect(ports.microservice_b)
    
    categoryList = get_categories(socket)

    try:
        new_category = questionary.select("Select a new category: ", choices= categoryList, use_shortcuts= True).ask()
    except KeyboardInterrupt:
        return
    update_category(new_category,itemName,socket)
    context.destroy()
    return new_category

def reset_categories():
    """Removes all changes made to the default item categories"""
    print("After resetting the categories, new items added to your lists will be applied to their default category.")
    print("This action cannot be undone.")
    answer = questionary.confirm("Do you want to proceed?", default=False).ask()
    if not answer:
        return
    
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect(ports.microservice_b)

    code = "RESET"
    socket.send_string(code)
    result = socket.recv_string()
    if result == "Reset successful":
        print("Custom category changes have been reset.")
        questionary.press_any_key_to_continue().ask()
    else:
        print("Unable to reset categories. Try again later")
        questionary.press_any_key_to_continue().ask()     


###
# Microservice C: Upload to Cloud
# The following functions are used to communicate with Microservice C 
# to upload the active list to the cloud database
###


def cloud_upload_item(listName, itemData):
    """Uploads the item to the online database"""
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect(ports.microservice_c)

    code = "ADD"
    socket.send_string(code, flags=zmq.SNDMORE)
    socket.send_string(listName, flags=zmq.SNDMORE)
    socket.send_json(itemData)

    socket.recv_string()
    
    context.destroy()

def cloud_edit_item(listName, itemToEdit, itemData):
    """Edits the item's values in the cloud database"""
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect(ports.microservice_c)

    code = "UPDATE"
    socket.send_string(code, flags=zmq.SNDMORE)
    socket.send_string(listName, flags=zmq.SNDMORE)
    socket.send_string(itemToEdit, flags=zmq.SNDMORE)
    socket.send_json(itemData)

    socket.recv_string()

    context.destroy()

def cloud_delete_item(listName, itemName):
    """Deletes the list item from the cloud database"""
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect(ports.microservice_c)

    code = "DELETE"
    socket.send_string(code, flags=zmq.SNDMORE)
    socket.send_string(listName, flags=zmq.SNDMORE)
    socket.send_string(itemName)

    socket.recv_string()

    context.destroy()

def cloud_delete_list(listName):
    """Deletes the entire list from the cloud database"""
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect(ports.microservice_c)

    code = "WIPE"
    socket.send_string(code, flags=zmq.SNDMORE)
    socket.send_string(listName)

    socket.recv_string()

    context.destroy()

###
# 
# Microservice D: Cloud Sync
# 

def import_cloud_list(shoppingLists, listName):
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect(ports.microservice_d)

    code = "ITEMS"
    socket.send_string(code, flags=zmq.SNDMORE)
    socket.send_string(listName)
    
    cloudListItems = socket.recv_json()
    if shoppingLists.get(listName):
        shoppingLists.pop(listName)
    
    shoppingLists[listName] = [cloudListItems]
    context.destroy()
    return listName

def import_cloud_list_names():
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect(ports.microservice_d)

    code = "NAMES"
    socket.send_string(code)

    cloudLists = socket.recv_json()
    context.destroy()
    return cloudLists

###

def main():
    """Main function to run the app."""
    startup()
    shoppingList = load_list()
    listName = select_list(shoppingList)

    while True:
        clear()
        print("Viewing Your List")
        isEmpty = view_list(shoppingList, listName)

        choices = ["Add item","Edit item","Delete Item", "Manage Lists", "Help", "Quit"]        
        answer = questionary.select("Select an option: ", choices, use_shortcuts=True).ask()

        if answer == "Add item":
            add_item(shoppingList, listName)
        elif answer == "Edit item":
            if isEmpty:
                transition_menu("Unable to Edit: This list is empty")
            else:
                edit_item(shoppingList, listName)
        elif answer == "Delete Item":
            if isEmpty:
                transition_menu("Unable to Delete: This list is empty")
            else:
                delete_item(shoppingList, listName)
        elif answer == "Help":
            help_menu()
        elif answer == "Manage Lists":
            try:
                manage_list_menu(shoppingList, listName)
            except ChangeActiveList:
                listName = select_list(shoppingList)

        elif answer == "Quit":
            return
        category_sort(shoppingList[listName])
        save_list(shoppingList)

if __name__ == "__main__":
    main()



