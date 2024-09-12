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

# ---------------------------------------------------- LOGIN ----------------------------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        entrada = request.form['rn']
        senha = request.form['password']

        conexao = conectar_banco_dados()
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

            if usuario['cargo'] == 'almoxarifado':
                return redirect(url_for('dashboard'))
            else:
                return redirect(url_for('requisicao_material'))
        else:
            print('Credenciais inválidas. Por favor, tente novamente.', 'error')

    return render_template('login/login.html')



@app.route('/primeiro_login', methods=['GET', 'POST'])
def primeiro_login():
    if request.method == 'POST':
        sn = request.form['sn']
        email = request.form['email']
        area = request.form['areas-senai']
        senha = request.form['password']

        conexao = conectar_banco_dados()
        cursor = conexao.cursor(dictionary=True)


        cursor.execute("SELECT * FROM users WHERE sn = %s", (sn,))
        usuario_existente = cursor.fetchone()

        if usuario_existente:
            query_update = "UPDATE users SET email = %s, cargo = %s, senha = %s WHERE sn = %s"
            cursor.execute(query_update, (email, area, senha, sn))
            conexao.commit()

        else:

            print('Usuario inexistente')

        cursor.close()
        conexao.close()


    return render_template('login/primeiro_login.html') 


# ---------------------------------------------------- FIM DO LOGIN ----------------------------------------------------

# ---------------------------------------------------- TELA INICIAL ----------------------------------------------------


@app.route('/dashboard') 
def dashboard():
    if 'user_cargo' not in session or session['user_cargo'] != 'almoxarifado':

        return redirect(url_for('solicitante'))  # Redireciona para a página de solicitante ou outra página adequada

    conexao = conectar_banco_dados()
    cursor = conexao.cursor(dictionary=True)

    try:
        # Quantidade de materiais com estoque mínimo atingido
        cursor.execute("""
            SELECT COUNT(*) AS estoque_minimo 
            FROM materials m
            JOIN estoque e ON m.id = e.material_id
            WHERE e.quantidade <= 6
        """)
        estoque_minimo = cursor.fetchone()['estoque_minimo']

    except:
        print("Erro ao buscar dados do dashboard")

        estoque_minimo = 0

    finally:
        cursor.close()
        conexao.close()

    return render_template('index.html', estoque_minimo=estoque_minimo)

# ---------------------------------------------------- FIM DA TELA INICIAL ----------------------------------------------------


# ---------------------------------------------------- CADASTRO MATERIAL ----------------------------------------------------

# ---------------------------------------------------- FIM CADASTRO MATERIAL ----------------------------------------------------



# ---------------------------------------------------- CONTROLE DE ESTOQUE ----------------------------------------------------

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

    return render_template('controle_estoque.html', materiais=materiais)

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
            # Verifica a quantidade em estoque
            cursor.execute("SELECT quantidade FROM estoque WHERE material_id = %s", (material_id,))
            estoque_atual = cursor.fetchone()
            if estoque_atual and estoque_atual[0] >= quantidade:
                # Atualiza a quantidade em estoque (subtrai a quantidade de saída)
                cursor.execute("""
                    UPDATE estoque 
                    SET quantidade = quantidade - %s 
                    WHERE material_id = %s
                """, (quantidade, material_id))

                # Insere um novo registro de saída no estoque
                inserir = "INSERT INTO estoque (material_id, quantidade, tipo_movimentacao, usuario_id) VALUES (%s, %s, 'saida', %s)"
                cursor.execute(inserir, (material_id, -quantidade, usuario_id))

                conexao.commit()

                return redirect(url_for('controle_estoque'))
            else:
                print('Estoque insuficiente para atender a requisição.', 'error') 
        except mysql.connector.Error as err:
            print(f'Erro ao registrar saída: {err}')

        finally:
            cursor.close()
            conexao.close()

    return redirect(url_for('controle_estoque'))

@app.route('/estoque_minimo')
def estoque_minimo():
    conexao = conectar_banco_dados()
    cursor = conexao.cursor(dictionary=True)
    
    try:
        # Consulta para obter materiais com estoque mínimo atingido
        cursor.execute("""
            SELECT m.id, m.descricao, m.estoque_minimo, 
                   COALESCE(SUM(CASE WHEN e.tipo_movimentacao = 'entrada' THEN e.quantidade ELSE 0 END) - 
                            SUM(CASE WHEN e.tipo_movimentacao = 'saida' THEN e.quantidade ELSE 0 END), 0) AS quantidade_atual
            FROM materials m
            LEFT JOIN estoque e ON m.id = e.material_id
            GROUP BY m.id 
            HAVING quantidade_atual <= m.estoque_minimo;
        """)
        materiais_abaixo_minimo = cursor.fetchall()
    
    except mysql.connector.Error as err:
        print(f"Erro ao buscar dados de estoque mínimo: {err}")
        materiais_abaixo_minimo = []

    finally:
        cursor.close()
        conexao.close()
    
    return render_template('estoque_minimo.html', materiais=materiais_abaixo_minimo)

# ---------------------------------------------------- FIM CONTROLE DE ESTOQUE ----------------------------------------------------
