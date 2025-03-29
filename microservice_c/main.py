import mysql.connector
import credentials
import zmq
import ports
import DDL


def upload_grocery_item(mydb, cursor, list_name, row):
    """Uploads the grocery list row to the database"""
    try:     
        query_data = (list_name, row['item'],row['quantity'],row['priority'],row['category'])
        cursor.execute(DDL.add_grocery_item,query_data)
        mydb.commit()
        print(f"Uploaded: {query_data}")
    except mysql.connector.Error as e:
        print("Failed to upload list item: {}".format(e))

def update_grocery_item(mydb, cursor, list_name, item_name, data):
    """Updates a grocery lists row in the database"""
    try:     
        query_data = (data['item'],data['quantity'],data['priority'],data['category'], list_name, item_name)
        cursor.execute(DDL.edit_grocery_item,query_data)
        mydb.commit()
        print(f"Edited: {query_data}")
    except mysql.connector.Error as e:
        print("Failed to update list item: {}".format(e))

def create_table(mydb, cursor):
    """Creates a grocery lists table if it doesnt exist already"""
    try:
        cursor.execute(DDL.create_table)
        mydb.commit()
        print("Grocery Lists table created.")
    except mysql.connector.Error as e:
        print("Failed to create table: {}".format(e))

def delete_grocery_item(mydb, cursor, list_name, item_name):
    """Deletes a grocery item from the database"""
    try:
        query_data = (list_name,item_name)
        cursor.execute(DDL.delete_grocery_item, query_data)
        mydb.commit()
        print(f"Deleted: {item_name}")
    except mysql.connector.Error as e:
        print("Failed to delete list item: {}".format(e))

def delete_grocery_list(mydb, cursor, query_data):
    """Deletes an entire grocery list from the database"""
    try:
        cursor.execute(DDL.delete_grocery_list, [query_data])
        mydb.commit()
        print(f"Succesfully deleted {query_data}")
    except mysql.connector.Error as e:
        print("Failed to delete Grocery List: {}".format(e))

def main():
    try:
        context = zmq.Context()
        socket = context.socket(zmq.REP)
        socket.bind(ports.main_program)
    except zmq.ZMQError as e:
        print(f"Unable to connect to the client: {e}")
        return
    try:
        print("Connecting to MySQL server...")
        mydb = mysql.connector.connect(**credentials.db_config)
        cursor = mydb.cursor()
        print("Connection successful!")
    except mysql.connector.Error as e:
        print(f"Failed to connect to MySQL server: {e}")
    else:
        print("\nCreating groceryLists table...")
        create_table(mydb, cursor)
        try:
            while True:
                try:
                    print("\nMicroservice C Ready...")
                    work_code = socket.recv_string()
                    list_name = socket.recv_string()
                    print(f"List name received.")
                    if mydb.is_connected() == False:
                        print("Lost connection. Attemping reconnect...")
                        mydb = mysql.connector.connect(**credentials.db_config)
                        cursor = mydb.cursor()
                        print("Reconnect successful")
                   
                    if work_code == "ADD":
                        new_row = socket.recv_json()
                        print(f"New row data received.")
                        upload_grocery_item(mydb, cursor, list_name, new_row)
                        socket.send_string("0")
                    
                    elif work_code == "UPDATE":
                        item_name = socket.recv_string()
                        print(f"Received item name to edit: {item_name}")
                        updated_row = socket.recv_json()
                        print("Received new row data.")
                        update_grocery_item(mydb, cursor, list_name, item_name,updated_row)
                        socket.send_string('0')
                    
                    elif work_code == 'DELETE':
                        item_name = socket.recv_string()
                        print(f"Received item to delete: {item_name}")
                        delete_grocery_item(mydb, cursor, list_name, item_name)
                        socket.send_string('0')

                    elif work_code == 'WIPE':
                        delete_grocery_list(mydb, cursor, list_name)
                        socket.send_string('0')
                except zmq.ZMQError as e:
                    print(f"Failed to receive or send data. Error: {e}")
                except mysql.connector.Error as e:
                    print(f"MySQL error: {e}")

        except KeyboardInterrupt:
            context.destroy()
            cursor.close()
            mydb.close()
            print("\nServer shut down.")

if __name__ == "__main__":
    main()
