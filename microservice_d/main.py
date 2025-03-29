import mysql.connector
import zmq
import credentials
import ports
import DDL

def get_list_names(cursor):
    """Retrieves the names of all the lists on the database"""
    try:
        cursor.execute(DDL.get_list_names)
        print("Query Successful: Get List Names")
        result = cursor.fetchall()
        final = []
        for list in result:
            if list[0]:
                final.append(list[0])
        return final
    except mysql.connector.Error as e:
        print(f"Failed to get grocery list names: {e}")

def get_list_items(cursor, lName):
    """Retrieves all the items on a database list"""
    try:
        cursor.execute(DDL.get_list_items, [lName])
        print(f"Query Successful: Get items from: {lName}")
        listItem = {}
        for row in cursor:
            listItem = dict(zip(cursor.column_names, row))
            listItem['quantity'] = str(listItem['quantity'])
        return listItem
    except mysql.connector.Error as e:
        print(f"Failed to get grocery list names: {e}")

def cleanup(context, cursor, mydb):
    context.destroy()
    cursor.close()
    mydb.close()
    print("Server shut down.")

def main():
    try:
        print("Setting up environment...")
        context = zmq.Context()
        socket = context.socket(zmq.REP)
        socket.bind(ports.main_program)
        print("Connected to the client.")
    except zmq.ZMQError as e:
        print(f"Unable to connect to the client: {e}")
        return
    
    try:
        mydb = mysql.connector.connect(**credentials.db_config)
        cursor = mydb.cursor()
        print("Connected to MySQL Server")
    except mysql.connector.Error as e:
        print(f"Failed to connect to MySQL server: {e}")
    else:
        try:
            while True:
                try:
                    print("\nMicroservice D ready...")
                    work_code = socket.recv_string()
                    print(f"Received Work code: {work_code}")
                    if mydb.is_connected() == False:
                        print("\nLost connection. Attempting reconnect...")
                        mydb = mysql.connector.connect(**credentials.db_config)
                        print("Reconnect successful\n")

                    if work_code == "NAMES":
                        result = get_list_names(cursor)
                        socket.send_json(result)
                        print("Sent all list names.")
                    
                    if work_code == "ITEMS":
                        lName = socket.recv_string()
                        print(f"Received List Name: {lName}")
                        result = get_list_items(cursor, lName)
                        socket.send_json(result)
                        print(f"Sent all items on list: {lName}")
                except zmq.ZMQError as e:
                    print(f"Failed to receive or send data. Error: {e}")
                except mysql.connector.Error as e:
                    print(f"MySQL error: {e}")

        except KeyboardInterrupt:
            cleanup(context, cursor, mydb) 



if __name__ == "__main__":
    main()
