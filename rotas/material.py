from flask import render_template, request, redirect, url_for, session, flash
from conexao import conectar_banco_dados
from app import app

@app.route('/cadastro_material', methods=['GET', 'POST'])
def cadastro_material():
    if 'user_cargo' not in session or session['user_cargo'] != 'almoxarifado':
        return redirect(url_for('solicitante'))

    if request.method == 'POST':
        descricao = request.form['descricao']
        categoria = request.form['categoria']

        estoque_minimo = int(request.form['estoque_minimo'] or 0)
        estoque_maximo = int(request.form['estoque_maximo'] or 0)

        conexao = conectar_banco_dados()
        cursor = conexao.cursor()

        try:
            query_insert = ("INSERT INTO materials (descricao, categoria, estoque_minimo, estoque_maximo) "
                            "VALUES (%s, %s, %s, %s)")
            cursor.execute(query_insert, (descricao, categoria, estoque_minimo, estoque_maximo))
            conexao.commit()

            flash('Material cadastrado com sucesso!', 'success')
            return redirect(url_for('cadastro_material'))

        except:
            flash('Erro ao cadastrar material:', 'error')
            return redirect(url_for('cadastro_material'))

        finally:
            cursor.close()
            conexao.close()

    return render_template('funcoes/cadastro_material.html')




@app.route('/controle_estoque')
def controle_estoque():
    if 'user_cargo' not in session or session['user_cargo'] != 'almoxarifado':
        return redirect(url_for('solicitante'))
    conexao = conectar_banco_dados()
    cursor = conexao.cursor(dictionary=True)

    
    cursor.execute("SELECT m.id, m.descricao, SUM(e.quantidade) as quantidade "
                    "FROM materials m "
                    "LEFT JOIN estoque e ON m.id = e.material_id "
                    "GROUP BY m.id")
    materiais = cursor.fetchall()

    cursor.close()
    conexao.close()


    return render_template('funcoes/controle_estoque.html', materiais=materiais)

@app.route('/registrar_entrada', methods=['POST'])
def registrar_entrada():
    if 'user_cargo' not in session or session['user_cargo'] != 'almoxarifado':
        return redirect(url_for('solicitante'))
    if request.method == 'POST':
        material_id = request.form['material_id']
        quantidade = int(request.form['quantidade'])
        usuario_id = session['user_id'] 

        conexao = conectar_banco_dados()
        cursor = conexao.cursor()

        try:

            query_insert = "INSERT INTO estoque (material_id, quantidade, tipo_movimentacao, usuario_id) VALUES (%s, %s, 'entrada', %s)"
            cursor.execute(query_insert, (material_id, quantidade, usuario_id))
            conexao.commit()
            
            cursor.close()
            conexao.close()


            return redirect(url_for('controle_estoque'))
        except:
            cursor.close()
            conexao.close()
            

            return redirect(url_for('controle_estoque'))





@app.route('/registrar_saida', methods=['POST'])
def registrar_saida():
    if 'user_cargo' not in session or session['user_cargo'] != 'almoxarifado':
        return redirect(url_for('solicitante'))
    

    if request.method == 'POST':
        material_id = request.form['material_id']
        quantidade = int(request.form['quantidade'])
        usuario_id = session['user_id'] 

        conexao = conectar_banco_dados()
        cursor = conexao.cursor()

        try:

            query_insert = "INSERT INTO estoque (material_id, quantidade, tipo_movimentacao, usuario_id) VALUES (%s, %s, 'saida', %s)"
            cursor.execute(query_insert, (material_id, -quantidade, usuario_id))
            conexao.commit()
            
            cursor.close()
            conexao.close()


            return redirect(url_for('controle_estoque'))
        except:
            cursor.close()
            conexao.close()
            

            return redirect(url_for('controle_estoque'))