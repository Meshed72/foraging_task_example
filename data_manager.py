from sqlite3 import Timestamp
import time
from Labtoolz_app.easydb_utils import execute_sql
import pdb


def update_tool_timestamp(account_id, tool_id):   
    sql = f"UPDATE `{account_id}_tb_tool_exp` SET `timestamp` = {int(time.time())} WHERE `tool_id` = {tool_id};"
    execute_sql(sql)
    
    