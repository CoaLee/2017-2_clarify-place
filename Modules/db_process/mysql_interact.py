import MySQLdb
import acct
import warnings
import os

"""
'mysql_interact':
    1. log type is either search or action.
    2. you don't need to care about table names. it's abstracted. 
    3. public functions: 
        [init/exit]_db_conn()
        insert_data(log_type, data)
        update_datum_where(log_type, datum, where='')
        add_column(log_type, name_and_attr) 
        select_columns_where(log_type, columns=['*'], where='')
        next_id(log_type)
    4. usage example: 
        [this_module.]init_db_conn()
        [this_module.]insert_data('search', data)
        [this_module.]add_column('action', ['new_column', 'VARCHAR(50)']
        [this_module.]exit_db_conn()
"""

MODE_BIG_DATA = True
DIRECT_LOAD = True

DB_NAME = 'clarify_pplace'
CHUNK_SIZE = 50000      # size unit of dividing large data
SELECT_CHOP_SIZE = 1000
chop_pos = {'search': 1579000, 'action': 1551000}

# global variables. db & cursor managed in module-wise scope
db = None
cursor = None

# (obsolete) anatomy represents the structure & attribute of logs
anatomy = {'search': [], 'action': []}   

# Path to containing directory.
COMMON_PATH = os.path.commonprefix([os.getcwd(), __file__])
FULL_PATH = __file__ if COMMON_PATH != '' else '{}/{}'.format(os.getcwd(), __file__) 
FILE_DIR = FULL_PATH[:FULL_PATH.rfind('/')]

def init_db_conn():
    global db, cursor
    db = MySQLdb.connect("localhost", acct.ID, acct.PW, database=DB_NAME, charset='utf8')
    cursor = db.cursor()
    _load_anatomy()

def exit_db_conn():
    global db, cursor
    cursor.close()
    db.commit()
    db.close()

# insert values into table
# arg 'data': [key_list, [val_list, val_list2, ...]]
def insert_data(log_type, data):
    key_list = data[0]
    val_lists = data[1]

    keys = '({})'.format(', '.join(key_list)) 
    values = '({})'.format('), ('.join(\
            ['"{}"'.format('", "'.join(val_list)) for val_list in val_lists]))

    query_insert_values = 'INSERT INTO {} {} VALUES {}'.format(log_type+'_log', keys, values)
    print(query_insert_values[:100])
    cursor.execute(query_insert_values)

# arg 'data': [col_name, val]
# arg 'where': sql condition 
def update_datum_where(log_type, datum, where=''):
    query_update = 'UPDATE {} SET {}="{}"'.format(log_type+'_log', datum[0], datum[1])
    if where != '':
        query_update += ' WHERE {};'.format(where)
    print(query_update)
    cursor.execute(query_update)
    db.commit()

# arg 'name_and_attr' example: ['search_date', 'DATETIME']
def add_column(log_type, name_and_attr):
    query_add_column = 'ALTER TABLE {} '.format(log_type+'_log')
    query_add_column += 'ADD COLUMN {} {};'.format(name_and_attr[0], name_and_attr[1])
    print(query_add_column)
    try:
        cursor.execute(query_add_column)
    except MySQLdb.OperationalError:
        # it already exists
        pass
        
# arg 'where': sql condition like 'id < 5' or 'query = "busan"'
# return: retrived rows in tuple of tuples 
# if MODE_BIG_DATA is True, return some part of rows instead of the whole.
def select_columns_where(log_type, columns=['*'], where='', chopping=False):
    query_select_from = 'SELECT {} FROM {}'.format(', '.join(columns), log_type+'_log')
    if where != '':
        query_select_from += ' WHERE {};'.format(where)
    elif chopping is True:
        global chop_pos
        query_select_from += ' WHERE id BETWEEN {} AND {};'\
                .format(chop_pos[log_type], chop_pos[log_type]+SELECT_CHOP_SIZE - 1)
        chop_pos[log_type] += SELECT_CHOP_SIZE
    cursor.execute(query_select_from)
    return cursor.fetchall()

def rewind_select(log_type, pos_mem):
    global chop_pos
    chop_pos[log_type] = pos_mem

# return next auto_incremented id, may be used to calculate the number of rows
def next_id(log_type):
    query_next_id = 'SELECT AUTO_INCREMENT FROM INFORMATION_SCHEMA.TABLES\
            WHERE TABLE_SCHEMA = "{}" AND TABLE_NAME = "{}_log";'.format(DB_NAME, log_type)
    cursor.execute(query_next_id)
    return cursor.fetchall()[0][0]

"""Below functions with leading '_' character are for internal process"""
# (obsolete) read anatomy information from files. 
def _load_anatomy():
    global anatomy
    if anatomy['search'] == []:
        with open(FILE_DIR+'/sr_table.anatomy', 'r') as ana_file:
            for line in ana_file:
                if line[0] == '#' or line[0] == '\n':
                    continue
                anatomy['search'].append(line.strip().split(','))

        with open(FILE_DIR+'/cr_table.anatomy', 'r') as ana_file:
            for line in ana_file:
                if line[0] == '#' or line[0] == '\n':
                    continue
                anatomy['action'].append(line.strip().split(','))

# extract data matching an anatomy from csv to list of two lists: [ [..], [[..], ..] ]
def _extract_data_from_csvlog(log_type, csv_fname):
    csv_file = open(csv_fname, 'r', encoding='utf-8')

    columns = []
    indices = []

    for (column, _, index) in anatomy[log_type]:
        columns.append(column)
        indices.append(int(index))

    tmp = [raw_line.split(',') for raw_line in csv_file]
    values = [[tmp_list[i] for i in indices] for tmp_list in tmp]

    csv_file.close()
    return [columns, values]

# using the providied function, divide and proceed data to save memory. 
# that is, func(extract_...(fname)) == extract_...(fname, func_to_run=func)
def _extract_data_in_chunk(log_type, csv_fname, func_to_run):
    csv_file = open(csv_fname, 'r', encoding='utf-8')

    columns = []
    indices = []
    
    for (column, _, index) in anatomy[log_type]:
        columns.append(column)
        indices.append(int(index))

    file_pos = 0
    # function to remove unexpected '"' from log. c is 'csv_line'
    _parse_csv = lambda c: (c[:c.find('"')] + c[c.find('"')+1:]).split(',')

    # divide in chunk size and process a function on it
    while True:
        csv_file_chunk = [csv_file.readline() for i in range(0, CHUNK_SIZE)]
        file_pos = csv_file.tell()
        if csv_file.readline() == '':
            csv_file_chunk.append('')
            csv_file_chunk = csv_file_chunk[:csv_file_chunk.index('')]
        else:
            csv_file.seek(file_pos)

        # tmp = [raw_line.split(',') for raw_line in csv_file_chunk]
        tmp = [_parse_csv(raw_line) for raw_line in csv_file_chunk]
        values = [[tmp_list[i] for i in indices] for tmp_list in tmp]
        func_to_run(log_type, [columns, values])
        if len(csv_file_chunk) < CHUNK_SIZE:
            break

    csv_file.close()

# create foreign key constraint
def _create_foreign_key(table_parent, col_parent, table_child, col_child):
    query_foreign = 'ALTER TABLE'.format(table_child)
    query_foreign += 'ADD FOREIGN KEY ({}) REFERENCES {}({});'\
            .format(col_child, table_parent, col_parent)
    cursor.execute(query_foreign)

# create database
def _create_db():
    db = MySQLdb.connect("localhost", acct.ID, acct.PW, charset='utf8')
    query_create_db = 'CREATE DATABASE IF NOT EXISTS {} CHARACTER SET utf8'.format(DB_NAME)
    db.send_query(query_create_db)
    db.commit()
    db.close()

# drop database
def _drop_db():
    db = MySQLdb.connect("localhost", acct.ID, acct.PW, charset='utf8')
    query_clear_db = 'DROP DATABASE IF EXISTS {}'.format(DB_NAME)
    db.send_query(query_clear_db)
    db.close()

# create a table using provided 'table_struct'.
# arg 'table_struct': [[col1, attr1], [col2, attr2], ...]
def _create_table(log_type, table_struct):
    query_create_table = 'CREATE TABLE IF NOT EXISTS {}_log '.format(log_type)
    query_create_table += '(id INT NOT NULL AUTO_INCREMENT, '
    for (col_name, attr) in table_struct:
        query_create_table += '{} {}, '.format(col_name, attr)
    query_create_table += 'PRIMARY KEY (id))'

    # to suppress warning when it already exists
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        cursor.execute(query_create_table)
    
# drop the table
def _drop_table(log_type):
    query_drop_table = "DROP TABLE IF EXISTS {}_log;".format(log_type)

    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        cursor.execute(query_drop_table);

    # to suppress warning when it already exists
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        cursor.execute(query_drop_table);

# create table, load data and sort it
def _direct_initial_table_setting():
    # create tables
    query_create_search_log = 'CREATE TABLE IF NOT EXISTS search_log \
            (id INT AUTO_INCREMENT PRIMARY KEY, \
            session_id VARCHAR(64), \
            keyword VARCHAR(64), \
            date_text VARCHAR(32), \
            ip_address VARCHAR(32), \
            query VARCHAR(256), \
            device VARCHAR(32), \
            os VARCHAR(16), \
            lpa INT(1), \
            att INT(1), \
            otregion INT(1), \
            F_action VARCHAR(10), \
            F_naver VARCHAR(10), \
            coord_x VARCHAR(16), \
            coord_y VARCHAR(16));'
    query_create_action_log = 'CREATE TABLE IF NOT EXISTS action_log \
            (id INT AUTO_INCREMENT PRIMARY KEY, \
            session_id VARCHAR(64), \
            date_text VARCHAR(32), \
            action_type VARCHAR(32), \
            res_ids VARCHAR(64), \
            keyword VARCHAR(128), \
            res_row INT(2), \
            url VARCHAR(1024));'
    # create raw tables(before sorting)
    query_create_raw_search = 'CREATE TABLE raw_search_log LIKE search_log;'
    query_create_raw_action = 'CREATE TABLE raw_action_log LIKE action_log;'
    # load csvs into raw tables
    query_load_search_csv = "LOAD DATA INFILE '/var/lib/mysql-files/sr.csv/' \
            INTO TABLE 'raw_search_log' FIELDS TERMINATED BY ',' LINES TERMINATD BY '\n' \
            (session_id, keyword, date_text, ip_address, query, device, os);"
    query_load_action_csv = "LOAD DATA INFILE '/var/lib/mysql-files/cr.csv/' \
            INTO TABLE 'raw_action_log' FIELDS TERMINATED BY ',' LINES TERMINATD BY '\n' \
            (session_id, date_text, action_type, res_ids, keyword, res_row, url);"
    # sort data into log tables
    query_sort_into_search = 'INSERT INTO search_log \
            (session_id, keyword, date_text, ip_address, query, device, os) \
            (SELECT session_id, keyword, date_text, ip_address, query, device, os \
            FROM raw_search_log ORDER BY session_id);'
    query_sort_into_action = 'INSERT INTO action_log \
            (session_id, date_text, action_type, res_ids, keyword, res_row, url) \
            (SELECT session_id, date_text, action_type, res_ids, keyword, res_row, url \
            FROM raw_action_log ORDER BY session_id);'
    # drop raw tables
    query_drop_raw_search = 'DROP TABLE raw_search_log;'
    query_drop_raw_action = 'DROP TABLE raw_action_log;'

    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        cursor.execute(query_create_search_log)
        cursor.execute(query_create_action_log)
        cursor.execute(query_create_raw_search)
        cursor.execute(query_create_raw_action)
        cursor.execute(query_load_search_csv)
        cursor.execute(query_load_action_csv )
        cursor.execute(query_sort_into_search)
        cursor.execute(query_sort_into_action)
        cursor.execute(query_drop_raw_search)
        cursor.execute(query_drop_raw_action)

# create database, check connection, create tables
def main(): 
    _create_db()
    init_db_conn()

    if DIRECT_LOAD:
        _direct_initial_table_setting()
    else:
        _create_table('search', [[col, attr] for [col, attr, _] in anatomy['search']])
        if MODE_BIG_DATA == False:
            insert_data('search', _extract_data_from_csvlog('../../data/sr.csv'))
        else:
            _extract_data_in_chunk('search', '../../data/sr.csv', func_to_run=insert_data)

        _create_table('action', [[col, attr] for [col, attr, _] in anatomy['action']])
        if MODE_BIG_DATA == False:
            insert_data('action', _extract_data_from_csvlog('../../data/cr.csv'))
        else:
            _extract_data_in_chunk('action', '../../data/cr.csv', func_to_run=insert_data)

    exit_db_conn()

if __name__ == '__main__':
    main()
    
