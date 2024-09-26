from flask import render_template, redirect, url_for, session
from conexao import conectar_banco_dados
from app import app

@app.route('/dashboard') 
def dashboard():
    if 'user_cargo' not in session or session['user_cargo'] != 'almoxarifado':
        return redirect(url_for('solicitante'))

    conexao = conectar_banco_dados()
    cursor = conexao.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT COUNT(*) AS estoque_minimo 
            FROM materials m
            JOIN estoque e ON m.id = e.material_id
            WHERE e.quantidade <= 6
        """)
        estoque_minimo = cursor.fetchone()['estoque_minimo']
    except Exception as e:
        print("Erro ao buscar dados do dashboard", e)
        estoque_minimo = 0
    finally:
        cursor.close()
        conexao.close()

    return render_template('index.html', estoque_minimo=estoque_minimo)
