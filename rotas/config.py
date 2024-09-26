import os

class Config:
    SECRET_KEY = 'sua-chave-secreta-aqui'
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_USER = os.getenv('MYSQL_USER', 'tcc')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '123')
    MYSQL_DB = os.getenv('MYSQL_DB', 'almoxarifado')
