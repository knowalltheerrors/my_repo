# import some libraries 
from sqlalchemy import create_engine
import pyodbc
import pandas as pd 
import os 
import psycopg2
import datetime
import pandas as pd
import numpy as np
import binascii
import re
import os
import requests  


# build the MSSQL server connection with below
src = pyodbc.connect(r'DRIVER={SQL Server};'
                     r'SERVER=;'
                     r'DATABASE=;'
                     r'Trusted_Connection=yes;'
                     r'UID=;'
                     r'PWD=')



clean_columns = []

# id = []
# this part builds cursor and execute the SQL query based on the CDC method in order to bring only today's transactions
cursor = src.cursor()

table_names = cursor.execute(""" 
select distinct + 'dbo_' + name + '_CT' from UsedTables where unused = 'used'
""")

table_name_values = table_names.fetchall()
clean_table_names = [x for table_name in table_name_values for x in table_name]


for table_name in clean_table_names:
    print(f'{table_name} is being processed .... :) ... ')
    del clean_columns[:]

    columns_new = cursor.execute(f""" SELECT * FROM [cdc].{table_name}
    WHERE CONVERT(DATE, sys.fn_cdc_map_lsn_to_time(__$start_lsn)) = CONVERT(DATE, GETDATE()) """)
    #stores column names in variable for later use
    column_names = [column[0] for column in cursor.description]
    col_name_test = columns_new.fetchall()


    # the list contains names that can be recognized as a SQL operation
    list_op = ['Close','Group','Status','Order','Update']

    def new_func():
        for name in list_op:
            yield name 

# Some column names are not important so, we exclude them and store them in a variable called clean_columns
    for name in column_names:
        if '$operation' in name:
            clean_columns.append(name)
        if '__$start_lsn' in name:
            clean_columns.append(name)
        elif '$' in name:
            continue
        elif name in [x for x in new_func()]:
            clean_columns.append('[' + name + ']')
        else:
            clean_columns.append(name)

 
    columns = ', '.join(clean_columns)
    columns_new = cursor.execute(f""" SELECT {columns} 
    FROM [cdc].{table_name}
    WHERE CONVERT(DATE, sys.fn_cdc_map_lsn_to_time(__$start_lsn)) = CONVERT(DATE, GETDATE()) """)
    values = columns_new.fetchall()

    def format_datetime(dt):
        return dt.strftime("%Y-%m-%d %H:%M:%S")

# rows = [[convert_none_to_null(value) for value in row] for row in values]

    values_formatted = [tuple([format_datetime(value) if isinstance(value, datetime.datetime) else value for value in row]) for row in values]
                    


    # connection for joining postgres database 
    postgres_connection = psycopg2.connect(user="",
                                password = '',
                                host="",
                                port="",
                                database="")
        
    cursor_postgres = postgres_connection.cursor()



# cursor_postgres.execute("""Select * from xxx""")
# records = cursor_postgres.fetchall()
# postgres_connection.commit()

    cursor_postgres.execute(""" Select transaction_id from "dbo".log_table """)
    data = cursor_postgres.fetchall()
    df = pd.DataFrame(data = data)

    placeholders = ','.join(['%s'] * (len(clean_columns) - 2))

    match = re.search(r"dbo_(.*?)_CT", table_name)
    if match:
        extracted_part = match.group(1).lower()

    try:
        for row in values_formatted:
            if row[1] == 2:
                if df.empty or binascii.hexlify(row[0]).decode() not in df[0].values:
                    insertion = f""" INSERT INTO "{extracted_part}" Values ({placeholders}) """
                    log_insertion = """ INSERT INTO "dbo".log_table Values (%s) """
                    cursor_postgres.execute(insertion, row[2:])
                    cursor_postgres.execute(log_insertion,(binascii.hexlify(row[0]).decode(),))
                    postgres_connection.commit()
                    print('Data inserted successfully')
                else:
                    print('No new data has been detected for insertion')
                    

            
            elif row[1] == 3:
                if df.empty or binascii.hexlify(row[0]).decode() not in df[0].values:
                    print('update before change operation is found')
                # log_update_after = """ INSERT INTO log_table Values (%s) """
                # cursor_postgres.execute(log_update_after,(binascii.hexlify(row[0]).decode(),))
                    update_before_change = list(row)
            
                    def combine_data(column_names, values):
                        data = {}
                        for i in range(len(column_names)):
                            data[column_names[i]] = values[i]
                        return data
            
                    datanew = combine_data(clean_columns, update_before_change)
                    df_update = pd.DataFrame(datanew, index=[0])
                else:
                    print('0 row is found for update....')
            

            elif row[1] == 4:
                if df.empty or binascii.hexlify(row[0]).decode() not in df[0].values:
                    i = 2
                    for col_name in clean_columns:
                        if '_$operation' in col_name:
                            continue
                        elif '__$start_lsn' in col_name:
                            continue 
                
                        else:
                        # update = f"""UPDATE src_dcamera SET "{col_name}" = {'%s'} WHERE "{col_name}" = {'%s'} or "{col_name}" is Null"""
                            if row[i] == None and update_before_change[i] == None:
                                update = f"""UPDATE "{extracted_part}" SET "{col_name.strip('[]')}" = {'%s'} Where "{col_name.strip('[]')}" is {'%s'}"""
                                cursor_postgres.execute(update, (row[i], update_before_change[i]))

                            elif row[i] != None and update_before_change[i] == None:
                                for id in df_update:
                                    if id == 'ID':
                                        unique_value = df_update['ID'].values[0]
                                        unique_col = id                            
                                        update = f"""UPDATE "{extracted_part}" SET "{col_name.strip('[]')}" = {'%s'} Where "{col_name.strip('[]')}" is {'%s'} AND "{unique_col.strip('[]')}" = {unique_value} """
                                        cursor_postgres.execute(update, (row[i], update_before_change[i]))
                    
                            else:
                                for id in df_update:
                                    if id == 'ID':
                                        unique_value = df_update['ID'].values[0]
                                        unique_col = id                           
                                        update = f"""UPDATE "{extracted_part}" SET "{col_name.strip('[]')}" = {'%s'} WHERE "{col_name.strip('[]')}" = {'%s'} AND "{unique_col.strip('[]')}" = {unique_value} """
                                        cursor_postgres.execute(update, (row[i], update_before_change[i]))
                                    

                        
                            postgres_connection.commit()
                            print(f'{i} column is updated')
                            i+=1


                    log_update_after = """ INSERT INTO "dbo".log_table Values (%s) """
                    cursor_postgres.execute(log_update_after,(binascii.hexlify(row[0]).decode(),))
                    postgres_connection.commit()
                else:
                    print('0 row is found for update')


            elif row[1] == 1:
                if df.empty or binascii.hexlify(row[0]).decode() not in df[0].values:
                    print('delete operation is found')
                    # delete_log = """ INSERT INTO dbo.log_table values (%s) """
                    # cursor_postgres.execute(delete_log,(binascii.hexlify(row[0]).decode(),))
                    postgres_connection.commit()
                    delete_operation = list(row)
            
                    def combine_data(column_names, values):
                        data = {}
                        for i in range(len(column_names)):
                            data[column_names[i]] = values[i]
                        return data
            
                    datanew = combine_data(clean_columns, delete_operation)
                    df_deletion = pd.DataFrame(datanew, index=[0])
                    for delete_id in df_deletion:
                        if delete_id == 'ID':
                            unique_id = df_deletion['ID'].values[0]
                            unique_col = delete_id
                            delete = f""" Delete from "{extracted_part}" Where "{unique_col.strip('[]')}" = {unique_id} """
                            delete_log = """ INSERT INTO "dbo".log_table values (%s) """
                            cursor_postgres.execute(delete_log,(binascii.hexlify(row[0]).decode(),))
                            cursor_postgres.execute(delete)
                            postgres_connection.commit()
                            print('The row is successfully deleted')
                else:
                    print('Nothing has been deleted recently')
                
    
    except (Exception,psycopg2.Error) as error: 
            print('Something wrong happened',error)

            
            postgres_connection.rollback()
            error_str = str(error)
            transaction_error = 'Failed transaction'
            query_error_table = """ INSERT INTO "dbo".log_table ("transaction_id","Errored_table","Error_description") values (%s,%s,%s) """   
            cursor_postgres.execute(query_error_table,(transaction_error,table_name,error_str))
            postgres_connection.commit()
            
            message = f"Transaction type: {transaction_error} \n\n Table name: {table_name} \n\n Error description: {error_str}"
            # Sends message to telegram if there is an error 
            base_url = 'https://api.telegram.org/bot6058578643:AAGDS6fTAGMkT6h9Hk0y16OP38xgMPP2Ipk/sendMessage?chat_id=-955334041&text="{}"'.format(message) 
            requests.get(base_url)
            
    finally:
        if postgres_connection:
            cursor_postgres.close()
            postgres_connection.close()
            print('Postgres connection is successfully closed')
            print('------------')