from secret import dict_cur

def check_insert(values_wanted, database_name, colnames=(), values=()):
        results = select(values_wanted, database_name, colnames, values)
        if results == []:
            insert(database_name, colnames, values)
        return

def check_insert_select(values_wanted, database_name, colnames=(), values=()):
    results = select(values_wanted, database_name, colnames, values)
    if results == []:
        insert(database_name, colnames, values)
        results = select(values_wanted, database_name, colnames, values)
    return results

def select(values_wanted, database_name, colnames=(), values=()):
    select_string="SELECT {} from {} ".format(values_wanted, database_name)
    if colnames:
        select_string=select_string+"WHERE "
        for colname,value in zip(colnames,values):
            select_string=select_string+str(colname)+" = '"+ str(value) +"' AND "
        select_string=select_string[:-4]
    select_string=select_string+";"
    #print select_string
    dict_cur.execute(select_string)
    results=dict_cur.fetchall()

    return results

def insert(database_name, colnames, values):
    if len(colnames)==1:
        colnames="({})".format(colnames[0])
    insert_string="INSERT INTO "+ database_name+" "+str(colnames).replace("'","")+" values ( "
    for value in values:
        value=str(value).replace("'","")
        insert_string=insert_string+"%s, "
    insert_string=insert_string[:-2]+")"

    #print insert_string
    dict_cur.execute(insert_string, values)