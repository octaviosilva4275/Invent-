from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import mysql.connector
from mysql.connector import Error
import os
# from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()  # Carregar variáveis do .env

app = Flask(__name__)

app.secret_key = 'sua-chave-secreta-aqui'


app.secret_key = 'teste'


# Codigo para autentificação

# account_sid = "ACc1f8fd89246833c6ec94946e9addeb12"

# auth_token = "72fd4f9768bcbe85fbbe65d0093280af"
# client = Client(account_sid, auth_token)

# message = client.messages.create(
#     to="+5516992360708",
#     from_="+12542216778",
#     body=f'Mensagem enviada')
# print(message.sid)

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

verificar_tabela()

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
    except Error as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        raise



@app.route('/')
def solicitante():
    return render_template('login/login.html')


# ---------------------------------------------------- LOGIN ----------------------------------------------------

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
            if usuario['cargo'] == 'almoxarifado':
                return redirect(url_for('dashboard'))
            else:
                return redirect(url_for('requisicao_material'))
        else:
            flash('Credenciais inválidas. Por favor, tente novamente.', 'error')
            return redirect(url_for('solicitante'))  # Redireciona para garantir que o erro seja exibido

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
            flash('Cadastro realizado com sucesso!', 'success')
        else:
            flash('Usuário inexistente.', 'error')

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

        except mysql.connector.Error as err:
            flash('Erro ao cadastrar material: {}'.format(err), 'error')
            return redirect(url_for('cadastro_material'))

        finally:
            cursor.close()
            conexao.close()

    return render_template('funcoes/cadastro_material.html')


# ---------------------------------------------------- FIM CADASTRO MATERIAL ----------------------------------------------------



# ---------------------------------------------------- CONTROLE DE ESTOQUE ----------------------------------------------------

@app.route('/controle_estoque')
def controle_estoque():
    if 'user_cargo' not in session or session['user_cargo'] != 'almoxarifado':
        return redirect(url_for('solicitante'))

    conexao = conectar_banco_dados()
    cursor = conexao.cursor(dictionary=True)

    try:
        # Obtém todos os materiais e suas quantidades
        cursor.execute("""
            SELECT m.id, m.descricao, COALESCE(SUM(e.quantidade), 0) AS quantidade
            FROM materials m
            LEFT JOIN estoque e ON m.id = e.material_id
            GROUP BY m.id
        """)
        materiais = cursor.fetchall()

    except Exception as e:
        print(f"Erro ao buscar dados: {e}")
        materiais = []

    finally:
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

        try:
            with conexao.cursor() as cursor:
                # Verifica a quantidade em estoque
                cursor.execute("SELECT quantidade FROM estoque WHERE material_id = %s", (material_id,))
                estoque_atual = cursor.fetchone()

                if estoque_atual and estoque_atual[0] >= quantidade:
                    # Atualiza a quantidade em estoque (subtrai a quantidade de saída)
                    cursor.execute("""UPDATE estoque 
                                      SET quantidade = quantidade - %s 
                                      WHERE material_id = %s""", (quantidade, material_id))

                    # Insere um novo registro de saída no estoque
                    inserir = """INSERT INTO estoque (material_id, quantidade, tipo_movimentacao, usuario_id) 
                                  VALUES (%s, %s, 'saida', %s)"""
                    cursor.execute(inserir, (material_id, -quantidade, usuario_id)) 

                    conexao.commit()
                    flash('Saída registrada com sucesso!', 'success')
                    return redirect(url_for('controle_estoque'))
                else:
                    flash('Estoque insuficiente para atender a requisição.', 'error')
        except mysql.connector.Error as err:
            print(f'Erro ao registrar saída: {err}')
            flash('Erro ao registrar saída.', 'error')
        finally:
            conexao.close()

    return redirect(url_for('controle_estoque'))







# ---------------------------------------------------- FIM CONTROLE DE ESTOQUE ----------------------------------------------------

# ---------------------------------------------------- REQUISICAO ----------------------------------------------------

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

        except mysql.connector.Error as err:
            print(f"Erro ao criar requisição: {err}")
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

    except mysql.connector.Error as err:
        print(f"Erro ao buscar dados: {err}")
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
    except mysql.connector.Error as err:
        print(f'Erro ao buscar requisições: {err}')
        return jsonify([]), 500 

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

    except mysql.connector.Error as err:
        print(f"Erro ao buscar requisições do usuário: {err}")
        return jsonify([]), 500

    finally:
        cursor.close()
        conexao.close()

    return jsonify(minhas_requisicoes)


# ---------------------------------------------------- FIM REQUISICAO ----------------------------------------------------


@app.route('/cadastro_material')
def cadastro_material_page():
    return render_template('funcoes/cadastro_material.html')

@app.route('/relatorio')
def relatorios():
    return render_template('funcoes/relatorio.html')

@app.route('/requisicao_material_admin')
def requisicao_material_admin():
    return render_template('funcoes/requisicao_material_admin.html')

@app.route('/perfil')
def perfil():
    return render_template('funcoes/perfil.html')

@app.route('/logout')
def logout():
    return render_template('funcoes/logout.html')


if __name__ == "__main__":
    app.run(debug=True)
