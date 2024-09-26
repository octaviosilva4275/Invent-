import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()  # Carregar variáveis do .env

def verificar_tabela():
    try:
        conexao = mysql.connector.connect(
            host=os.getenv('MYSQL_HOST'),
            user=os.getenv('MYSQL_USER'),
            password=os.getenv('MYSQL_PASSWORD'),
            database=os.getenv('MYSQL_DB'),
            port=int(os.getenv('MYSQL_PORT'))
        )
        cursor = conexao.cursor()
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print("Tabelas no banco de dados:")
        for table in tables:
            print(table[0])
        cursor.close()
        conexao.close()
    except mysql.connector.Error as err:
        print(f"Erro: {err}")

def conectar_banco_dados():
    use_remote_db = os.getenv('USE_REMOTE_DB', 'False').lower() == 'true'
    print(f"USE_REMOTE_DB: {use_remote_db}")
    
    try:
        if use_remote_db:
            print("Tentando conectar ao banco de dados remoto...")
            conexao = mysql.connector.connect(
                host=os.getenv('MYSQL_HOST'),
                user=os.getenv('MYSQL_USER'),
                password=os.getenv('MYSQL_PASSWORD'),
                database=os.getenv('MYSQL_DB'),
                port=int(os.getenv('MYSQL_PORT'))
            )
        else:
            print("Tentando conectar ao banco de dados local...")
            conexao = mysql.connector.connect(
                host='localhost',
                user='tcc',
                password='123',
                database='almoxarifado',
            )
        print("Conexão estabelecida com sucesso!")
        return conexao
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
