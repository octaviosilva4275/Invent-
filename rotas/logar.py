from flask import render_template, request, redirect, url_for, session, flash
from conexao import conectar_banco_dados
from app import app

@app.route('/')
def solicitante():
    return render_template('login/login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    conexao = conectar_banco_dados()
    if request.method == 'POST':
        entrada = request.form['sn']
        senha = request.form['password']

        cursor = conexao.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE (sn = %s OR email = %s) AND senha = %s", (entrada, entrada, senha))
        usuario = cursor.fetchone()
        cursor.close()
        conexao.close()

        if usuario:
            session['logged_in'] = True
            session['user_id'] = usuario['id']
            session['user_sn'] = usuario['sn']
            session['user_cargo'] = usuario['cargo']
            return redirect(url_for('dashboard')) if usuario['cargo'] == 'almoxarifado' else redirect(url_for('requisicao_material'))
        else:
            flash('Credenciais inválidas. Por favor, tente novamente.', 'error')
            return redirect(url_for('solicitante'))

    return render_template('login/login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('solicitante'))
