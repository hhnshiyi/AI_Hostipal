import pymysql.cursors
import json
from tqdm import tqdm
# 数据库连接参数
class DB:
    def __init__(self, host, user, password, database):
        self.db_config = {
            'host': host,
            'user': user,
            'password': password,
            'database': database,
            'charset': 'utf8mb4',
            'cursorclass': pymysql.cursors.DictCursor
        }

    def execute_query(self,query, params=None):
        connection = pymysql.connect(**self.db_config)
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                connection.commit()
                return cursor.fetchall()
        finally:
            connection.close()
    #检查数据是否存在：
    def check_data_exist(self,department_id,table):
        # 检查记录是否存在
        check_query = f"""
                SELECT count(department_id)
                FROM {table}
                WHERE department_id = %s
                """
        check_params = (department_id,)
        result = self.execute_query(check_query, check_params)
        return result[0]["count(department_id)"]

    # 插入数据
    def insert_record(self,fact, accusation, plaintiff, defendant, extraction_content,classified_info,buli,youli,zhongli,table):

        query = f"""
        INSERT INTO {table} (fact, accusation, plaintiff, defendant,  extraction_content,classified_info,buli,youli,zhongli)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s,%s)
        """
        params = (fact, accusation, plaintiff, defendant, extraction_content,classified_info,buli,youli,zhongli)
        self.execute_query(query, params)

    def insert_or_update_record_to_direct(self, department_id, question_anwser, table):

        # 检查数据是否存在
        result = self.check_data_exist(department_id, table)
        print(table)

        if result > 0:
            # 如果记录存在，则更新记录
            update_query = f"""
            UPDATE {table}
            SET question_anwser = %s
            WHERE department_id = %s
            """
            update_params = (question_anwser, department_id)
            self.execute_query(update_query, update_params)
        else:
            # 如果记录不存在，则插入新记录
            insert_query = f"""
            INSERT INTO {table} (department_id, question_anwser)
            VALUES (%s, %s)
            """
            insert_params = (department_id, question_anwser)
            self.execute_query(insert_query, insert_params)


    # 删除数据
    def delete_record(self,record_id,table):
        query = f"DELETE FROM {table} WHERE id = %s"
        params = (record_id,)
        self.execute_query(query, params)


    # 查询数据
    def fetch_records(self,column_name,table):
        query = f"SELECT {column_name} FROM {table}"
        return self.execute_query(query)
        # 增加字段并赋值

    # 根据字段id查询数据
    def fetch_record_by_name(self, column_name, table, department):
        query = f"SELECT {column_name} FROM {table} WHERE department = %s"
        return self.execute_query(query, (department,))

    #检查字段是否存在
    def check_column_existence(self, table, column_name):
        query = f"""
        SELECT COUNT(*) AS column_count
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = '{self.db_config['database']}'
          AND TABLE_NAME = '{table}'
          AND COLUMN_NAME = '{column_name}'
        """
        result = self.execute_query(query)
        column_count = result[0]['column_count']
        return column_count > 0

    def add_column_and_update(self, table, new_column_name, values,type,id):
        # 字段不存在增加新字段
        if not self.check_column_existence(table, new_column_name):
            add_column_sql = f"""
               ALTER TABLE {table}
               ADD COLUMN {new_column_name} {type};
               """
            self.execute_query(add_column_sql)
        # 否则更新字段值
        update_column_sql = f"""
           UPDATE {table}
           SET {new_column_name} = %s
           WHERE id = %s;
           """
        self.execute_query(update_column_sql, (values, id))

if __name__ == '__main__':
    db = DB(host='localhost', user='root', password='1230', database='ai_follow-up_system')
    messages = db.fetch_records("question_anwser","hospital_department")
    print(messages)



