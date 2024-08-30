from flask import Flask, render_template, request, redirect, url_for, session,jsonify 
import mysql.connector

app = Flask(__name__)

def conectar_banco_dados():

    conexao = mysql.connector.connect(
        host='localhost',
        user='tcc',
        password='123',
        database='almoxarifado',
    )
    return conexao

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        entrada = request.form['rn']
        senha = request.form['password']

        conexao = conectar_banco_dados()
        cursor = conexao.cursor(dictionary=True)

        cursor.execute("SELECT * FROM users WHERE (rn = %s OR email = %s) AND senha = %s", (entrada, entrada, senha))
        usuario = cursor.fetchone()

        cursor.close()
        conexao.close()

        if usuario:
            session['logged_in'] = True
            session['user_id'] = usuario['id']
            session['user_rn'] = usuario['rn']
            session['user_cargo'] = usuario['cargo']

            if usuario['cargo'] == 'almoxarifado':
                return redirect(url_for('dashboard'))
            else:
                return redirect(url_for('requisicao_material'))
        else:
            print('Credenciais inválidas. Por favor, tente novamente.', 'error')

    return render_template('login/login.html')
