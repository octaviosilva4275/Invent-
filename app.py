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

@app.route('/cadastro_material', methods=['GET', 'POST'])
def cadastro_material():
    if 'user_cargo' not in session or session['user_cargo'] != 'almoxarifado':
        return redirect(url_for('solicitante'))
    if request.method == 'POST':
        descricao = request.form['descricao']
        categoria = request.form['categoria']
        localizacao = request.form['localizacao']
        estoque_minimo = int(request.form['estoque_minimo'] or 0)  # Converte para int, 0 se vazio
        estoque_maximo = int(request.form['estoque_maximo'] or 0)



        conexao = conectar_banco_dados()
        cursor = conexao.cursor()

        try:
            # Insere o novo material no banco de dados
            query_insert = ("INSERT INTO materials (descricao, categoria, localizacao, estoque_minimo, estoque_maximo) "
                            "VALUES (%s, %s, %s, %s, %s)")
            cursor.execute(query_insert, (descricao, categoria, localizacao, estoque_minimo, estoque_maximo))            
            conexao.commit()

            # Redireciona para a mesma página com uma mensagem de sucesso (opcional)
            return redirect(url_for('cadastro_material',))

        except:
            print("Erro ao cadastrar material")
            return redirect(url_for('cadastro_material'))
        finally:
            cursor.close()
            conexao.close()

    # Se for GET ou ocorrer algum erro, exibe o formulário
    conexao = conectar_banco_dados()
    cursor = conexao.cursor(dictionary=True)

    cursor.close()
    conexao.close()

    return render_template('cadastro_material.html')

# ---------------------------------------------------- FIM CADASTRO MATERIAL ----------------------------------------------------