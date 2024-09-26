from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from conexao import conectar_banco_dados
from app import app


@app.route('/requisicao_material', methods=['GET', 'POST'])
def requisicao_material():
    if request.method == 'POST':
        material_id = request.form['material_id']
        quantidade = int(request.form['quantidade'])
        usuario_id = session['user_id']
        observacao = request.form.get('observacao')  # Observação pode ser opcional

        conexao = conectar_banco_dados()
        cursor = conexao.cursor()

        try:
            # Insere a requisição no banco de dados
            inserir = "INSERT INTO requisicoes (material_id, usuario_id, quantidade, observacao) VALUES (%s, %s, %s, %s)"
            cursor.execute(inserir, (material_id, usuario_id, quantidade, observacao))
            conexao.commit()

            print('Requisição de material enviada com sucesso!', 'success')

        except:
            print("Erro ao criar requisição")
            print('Ocorreu um erro ao enviar a requisição. Por favor, tente novamente mais tarde.', 'error')

        finally:
            cursor.close()
            conexao.close()

        return redirect(url_for('requisicao_material')) 

    # Lógica para exibir o formulário e as requisições do usuário
    conexao = conectar_banco_dados()
    cursor = conexao.cursor(dictionary=True)
    try:
        cursor.execute("SELECT m.id, m.descricao, SUM(e.quantidade) as quantidade "
                       "FROM materials m "
                       "LEFT JOIN estoque e ON m.id = e.material_id "
                       "GROUP BY m.id")
        materiais = cursor.fetchall()

        minhas_requisicoes = []
        if 'user_id' in session:
            usuario_id = session['user_id']
            cursor.execute("""
                SELECT 
                    r.id,
                    m.descricao as material,
                    r.quantidade,
                    r.status,
                    r.data_entrega 
                FROM requisicoes r
                JOIN materials m ON r.material_id = m.id
                WHERE r.usuario_id = %s
            """, (usuario_id,))
            minhas_requisicoes = cursor.fetchall()

    except:
        print(f"Erro ao buscar dados")
        materiais = []
        minhas_requisicoes = []

    finally:
        cursor.close()
        conexao.close()

    return render_template('funcoes/requisicao_material.html', materiais=materiais, minhas_requisicoes=minhas_requisicoes)

@app.route('/api/requisicoes_admin')
def api_requisicoes_admin():
    if 'user_cargo' not in session or session['user_cargo'] != 'almoxarifado':
        return jsonify([])

    conexao = conectar_banco_dados()
    cursor = conexao.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT 
                r.id,
                m.descricao as material,
                r.quantidade,
                u.nome as usuario, 
                r.status,
                r.data_entrega,
                r.observacao
            FROM requisicoes r
            JOIN materials m ON r.material_id = m.id
            JOIN users u ON r.usuario_id = u.id 
            WHERE r.status != 'aprovada'  
            ORDER BY r.status DESC 
        """)
        requisicoes = cursor.fetchall()
    except:
        print(f'Erro ao buscar requisições')
        return

    finally:
        cursor.close()
        conexao.close()

    return jsonify(requisicoes) 

@app.route('/api/minhas_requisicoes')
def api_minhas_requisicoes():
    if 'user_id' not in session:
        return jsonify([])

    conexao = conectar_banco_dados()
    cursor = conexao.cursor(dictionary=True)

    try:
        usuario_id = session['user_id']
        cursor.execute("""
            SELECT 
                r.id,
                m.descricao as material,
                r.quantidade,
                r.status,
                r.data_entrega 
            FROM requisicoes r
            JOIN materials m ON r.material_id = m.id
            WHERE r.usuario_id = %s AND r.status = 'pendente' 
        """, (usuario_id,))
        minhas_requisicoes = cursor.fetchall()

    except:
        print(f"Erro ao buscar requisições do usuário")
        return

    finally:
        cursor.close()
        conexao.close()

    return jsonify(minhas_requisicoes)