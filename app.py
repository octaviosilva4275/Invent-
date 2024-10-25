import os
import uuid
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import mysql.connector
from mysql.connector import Error
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Mail, Message
import jwt
import hashlib
import time
import secrets
from datetime import datetime, timedelta

# from twilio.rest import Client
# from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient

# EMAIL
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


import secrets
from datetime import datetime, timedelta

# Carregar variáveis do .env
# load_dotenv()

# Inicialização do Flask
app = Flask(__name__)
app.secret_key = 'teste'

EMAIL_USER = os.getenv('EMAIL_USER')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')

# Código para autenticação
# account_sid = "ACc1f8fd89246833c6ec94946e9addeb12"
# auth_token = "72fd4f9768bcbe85fbbe65d0093280af"



# client = Client(account_sid, auth_token)


# Codigo para autentificação

# account_sid = "ACc1f8fd89246833c6ec94946e9addeb12"

# auth_token = "72fd4f9768bcbe85fbbe65d0093280af"
# client = Client(account_sid, auth_token)

# message = client.messages.create(
#     to="+5516992360708",
#     from_="+12542216778",
#     body=f'Mensagem enviada')
# print(message.sid)

# def verificar_tabela():
#     try:
#         conexao = mysql.connector.connect(
#             host=os.getenv('MYSQL_HOST'),
#             user=os.getenv('MYSQL_USER'),
#             password=os.getenv('MYSQL_PASSWORD'),
#             database=os.getenv('MYSQL_DB'),
#             port=int(os.getenv('MYSQL_PORT'))
#         )
#         cursor = conexao.cursor()
#         cursor.execute("SHOW TABLES")
#         tables = cursor.fetchall()
#         print("Tabelas no banco de dados:")
#         for table in tables:
#             print(table[0])
#         cursor.close()
#         conexao.close()
#     except mysql.connector.Error as err:
#         print(f"Erro: {err}")

# verificar_tabela()

def conectar_banco_dados():
    # use_remote_db = os.getenv('USE_REMOTE_DB', 'False').lower() == 'true'
    # print(f"USE_REMOTE_DB: {use_remote_db}")
    
    try:
        # if use_remote_db:
        #     print("Tentando conectar ao banco de dados remoto...")
        #     conexao = mysql.connector.connect(
        #         host=os.getenv('MYSQL_HOST'),
        #         user=os.getenv('MYSQL_USER'),
        #         password=os.getenv('MYSQL_PASSWORD'),
        #         database=os.getenv('MYSQL_DB'),
        #         port=int(os.getenv('MYSQL_PORT'))
        #     )
        # else:
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
        entrada = request.form['entrada']
        senha = request.form['senha']

        cursor = conexao.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE (sn = %s OR email = %s) AND senha = %s", (entrada, entrada, senha))
        usuario = cursor.fetchone()
        cursor.close()
        conexao.close()

        if usuario:
            if usuario['cargo'] == 'almoxarifado-nao-verificado':
                return redirect(url_for('espera'))  # Redireciona para a tela de espera
            
            session['logged_in'] = True
            session['user_id'] = usuario['id']
            session['user_sn'] = usuario['sn']
            session['user_email'] = usuario['email']
            session['user_cargo'] = usuario['cargo']

            # Redireciona de acordo com o cargo
            if usuario['cargo'] == 'admin':
                return redirect(url_for('admin'))
            elif usuario['cargo'] == 'almoxarifado':
                return redirect(url_for('dashboard'))
            else:
                return redirect(url_for('requisicao_material'))
        else:
            flash('Credenciais inválidas. Por favor, tente novamente.', 'error')
            return redirect(url_for('solicitante'))

    return render_template('login/login.html')







@app.route('/espera')
def espera():
    return render_template('espera.html')


@app.route('/perfil')
def perfil():
    return render_template('funcoes/perfil.html')

@app.route('/editar_perfil', methods=['GET', 'POST'])
def editar_perfil():
    conexao = conectar_banco_dados()
    usuario_id = session.get('user_id')

    if request.method == 'POST':
        sn = request.form['sn']  # O código SN
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        confirmar_senha = request.form['confirmar_senha']

        cursor = conexao.cursor()
        
        if senha and senha != confirmar_senha:  # Verifica se as senhas coincidem
            flash('As senhas não coincidem. Tente novamente.', 'error')
            cursor.close()
            conexao.close()
            return redirect(url_for('editar_perfil'))

        try:
            if senha:  # Se a senha foi fornecida, atualiza
                cursor.execute("UPDATE users SET nome = %s, email = %s, senha = %s WHERE id = %s", (nome, email, senha, usuario_id))
            else:  # Se a senha não foi fornecida, não atualiza
                cursor.execute("UPDATE users SET nome = %s, email = %s WHERE id = %s", (nome, email, usuario_id))
            
            conexao.commit()
            flash('Perfil atualizado com sucesso!', 'success')

        except Exception as e:
            print(f"Erro ao atualizar perfil: {e}")
            flash('Erro ao atualizar o perfil. Tente novamente.', 'error')

        finally:
            cursor.close()
            conexao.close()

        return redirect(url_for('editar_perfil'))

    cursor = conexao.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE id = %s", (usuario_id,))
    usuario = cursor.fetchone()
    cursor.close()
    conexao.close()
    
    return render_template('editar_perfil.html', usuario=usuario)






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

    return render_template('login/cadastro.html')



# ---------------------------------------------------- FIM DO LOGIN ----------------------------------------------------

# ---------------------------------------------------- TELA INICIAL ----------------------------------------------------


@app.route('/autenticacao')
def verificar_autenticacao():
    if 'user_id' in session:
        return jsonify({'autenticado': True})
    else:
        return jsonify({'autenticado': False})

@app.route('/dashboard')
def dashboard():

    if 'user_id' in session:
        user_id = session['user_id']

    if 'user_id' not in session:
        flash('Você precisa estar logado para acessar essa página.', 'error')
        return redirect(url_for('login'))

    conexao = conectar_banco_dados()
    cursor = conexao.cursor(dictionary=True)
    if 'user_id' in session:
        user_id = session['user_id']
        try:
            # Obter detalhes dos produtos abaixo do estoque mínimo
            cursor.execute("""
                SELECT m.id, m.descricao, m.estoque_minimo, 
                    COALESCE(SUM(CASE WHEN e.tipo_movimentacao = 'entrada' THEN e.quantidade ELSE 0 END) - 
                                SUM(CASE WHEN e.tipo_movimentacao = 'saida' THEN e.quantidade ELSE 0 END), 0) AS quantidade_atual
                FROM materials m
                LEFT JOIN estoque e ON m.id = e.material_id
                GROUP BY m.id 
                HAVING quantidade_atual <= m.estoque_minimo
            """)
            produtos_estoque_minimo = cursor.fetchall()
            estoque_minimo = len(produtos_estoque_minimo)

            # Atualizar consulta para incluir data_atualizacao
            cursor.execute("""
                SELECT r.id, r.quantidade, r.status, m.descricao AS material, u.nome AS usuario, r.data_atualizacao
                FROM requisicoes r
                JOIN materials m ON r.material_id = m.id
                JOIN users u ON r.usuario_id = u.id
                WHERE DATE(r.data_requisicao) = CURDATE()
            """)
            historico_hoje = cursor.fetchall()

            # Obter nome do usuário logado
            cursor.execute("SELECT nome FROM users WHERE id = %s", (session['user_id'],))
            usuario = cursor.fetchone()

        except mysql.connector.Error as err:
            print(f"Erro: {err}")
            estoque_minimo = 0
            produtos_estoque_minimo = []
            historico_hoje = []
            usuario = None

        finally:
            cursor.close()
            conexao.close()

        return render_template('index.html', 
                            estoque_minimo=estoque_minimo,
                            produtos_estoque_minimo=produtos_estoque_minimo,
                            historico_hoje=historico_hoje,
                            usuario=usuario,
                            )  # Passando o usuário para o template






# ---------------------------------------------------- FIM DA TELA INICIAL ----------------------------------------------------


# ---------------------------------------------------- CADASTRO MATERIAL ----------------------------------------------------
@app.route('/cadastro_material', methods=['GET', 'POST'])
def cadastro_material():
    if 'user_cargo' not in session or session['user_cargo'] not in ['almoxarifado', 'admin']:
        return redirect(url_for('solicitante'))

    conexao = conectar_banco_dados()
    cursor = conexao.cursor(dictionary=True)

    # Obter informações do usuário logado
    usuario = None
    if 'user_id' in session:
        cursor.execute("SELECT nome FROM users WHERE id = %s", (session['user_id'],))
        usuario = cursor.fetchone()
    if 'user_id' in session:
        user_id = session['user_id']
        if request.method == 'POST':
            descricao = request.form['descricao']
            categoria = request.form['categoria']

            estoque_minimo = int(request.form['estoque_minimo'] or 0)
            estoque_maximo = int(request.form['estoque_maximo'] or 0)

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

    cursor.close()
    conexao.close()

    return render_template('funcoes/cadastro_material.html', usuario=usuario)



# ---------------------------------------------------- FIM CADASTRO MATERIAL ----------------------------------------------------


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if 'user_cargo' not in session or session['user_cargo'] not in ['almoxarifado', 'admin']:
        flash('Acesso negado. Você não tem permissão para acessar esta página.', 'error')
        return redirect(url_for('solicitante'))

    conexao = conectar_banco_dados()
    cursor = conexao.cursor(dictionary=True)

    # Obter o nome do usuário logado
    cursor.execute("SELECT nome FROM users WHERE id = %s", (session['user_id'],))
    usuario_logado = cursor.fetchone()
    if 'user_id' in session:
        user_id = session['user_id']
        if request.method == 'POST':
            # Capturar os dados do formulário
            user_id = request.form.get('user_id')
            nome = request.form.get('nome')
            email = request.form.get('email')
            sn = request.form.get('sn', '')  # Atribui um valor padrão vazio se 'sn' não estiver presente
            cargo = request.form.get('cargo')
            senha = request.form.get('senha')

            # Verificar se o usuário tem permissão para mudar cargos (somente admins)
            if session['user_cargo'] == 'admin':
                query_update = "UPDATE users SET nome = %s, email = %s, sn = %s, cargo = %s, senha = %s WHERE id = %s"
                cursor.execute(query_update, (nome, email, sn, cargo, senha, user_id))
            else:
                query_update = "UPDATE users SET nome = %s, email = %s, senha = %s WHERE id = %s"
                cursor.execute(query_update, (nome, email, senha, user_id))
            
            conexao.commit()
            flash('Usuário atualizado com sucesso!', 'success')

    # Buscar todos os usuários
    cursor.execute("SELECT * FROM users")
    usuarios = cursor.fetchall()

    cursor.close()
    conexao.close()

    return render_template('admin/admin.html', usuarios=usuarios, usuario=usuario_logado)








@app.route('/aprovar_usuario', methods=['POST'])
def aprovar_usuario():
    user_id = request.form['user_id']
    conexao = conectar_banco_dados()
    cursor = conexao.cursor()

    # Atualiza o cargo do usuário
    query_update = "UPDATE users SET cargo = 'almoxarifado' WHERE id = %s"
    cursor.execute(query_update, (user_id,))
    conexao.commit()

    cursor.close()
    conexao.close()

    flash('Usuário aprovado com sucesso!', 'success')
    return redirect(url_for('admin'))


@app.route('/excluir_usuario', methods=['POST'])
def excluir_usuario():
    user_id = request.form['user_id']
    print(f"Tentando excluir usuário com ID: {user_id}")  # Log para debug
    conexao = conectar_banco_dados()
    cursor = conexao.cursor()

    try:
        # Remover referências na tabela requisicoes
        query_delete_requisicoes = "DELETE FROM requisicoes WHERE usuario_id = %s"
        cursor.execute(query_delete_requisicoes, (user_id,))

        # Remover referências na tabela estoque
        query_delete_estoque = "DELETE FROM estoque WHERE usuario_id = %s"
        cursor.execute(query_delete_estoque, (user_id,))
        
        # Executar exclusão do usuário
        query_delete_user = "DELETE FROM users WHERE id = %s"
        cursor.execute(query_delete_user, (user_id,))
        conexao.commit()

        flash('Usuário excluído com sucesso!', 'success')
    except mysql.connector.errors.IntegrityError as e:
        print(f"Erro de integridade: {e}")  # Log do erro
        flash('Não é possível excluir o usuário. Existem registros associados.', 'error')
        conexao.rollback()
    except Exception as e:
        print(f"Erro inesperado: {e}")  # Log do erro
        flash('Erro ao excluir o usuário.', 'error')
        conexao.rollback()
    finally:
        cursor.close()
        conexao.close()

    return redirect(url_for('admin'))






# ---------------------------------------------------- CONTROLE DE ESTOQUE ----------------------------------------------------

@app.route('/controle_estoque')
def controle_estoque():
    if 'user_cargo' not in session or session['user_cargo'] not in ['almoxarifado', 'admin']:
        return redirect(url_for('solicitante'))

    conexao = conectar_banco_dados()
    cursor = conexao.cursor(dictionary=True)

    usuario = None
    usuario_id = session.get('user_id')
  
    if usuario_id:
        cursor.execute("SELECT * FROM users WHERE id = %s", (usuario_id,))
        usuario = cursor.fetchone()

    try:
        # Obtain all materials and calculate available quantity
        cursor.execute(""" 
            SELECT 
                m.id, 
                m.descricao, 
                COALESCE(SUM(CASE WHEN e.tipo_movimentacao = 'entrada' THEN e.quantidade ELSE 0 END), 0) AS total_entrada,
                COALESCE(SUM(CASE WHEN e.tipo_movimentacao = 'saida' THEN e.quantidade ELSE 0 END), 0) AS total_saida,
                COALESCE(SUM(CASE WHEN e.tipo_movimentacao = 'entrada' THEN e.quantidade ELSE 0 END), 0) - 
                COALESCE(SUM(CASE WHEN e.tipo_movimentacao = 'saida' THEN e.quantidade ELSE 0 END), 0) AS quantidade_disponivel
            FROM materials m
            LEFT JOIN estoque e ON m.id = e.material_id
            GROUP BY m.id
            ORDER BY m.descricao ASC  -- Sort materials A-Z
        """)
        materiais = cursor.fetchall()

    except Exception as e:
        print(f"Erro ao buscar dados: {e}")
        materiais = []

    finally:
        cursor.close()
        conexao.close()

    return render_template('funcoes/controle_estoque.html', materiais=materiais, usuario=usuario)




@app.route('/registrar_entrada', methods=['POST'])
def registrar_entrada():
    if 'user_cargo' not in session or session['user_cargo'] not in ['almoxarifado', 'admin']:
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
            
            flash('Entrada registrada com sucesso!', 'success')  # Adicionando flash aqui
        except Exception as e:
            print(f"Erro ao registrar entrada: {e}")
            flash('Erro ao registrar entrada.', 'error')
        finally:
            cursor.close()
            conexao.close()

        return redirect(url_for('controle_estoque'))




@app.route('/registrar_saida', methods=['POST'])
def registrar_saida():
    if 'user_cargo' not in session or session['user_cargo'] not in ['almoxarifado', 'admin']:
        return redirect(url_for('solicitante'))

    if request.method == 'POST':
        material_id = request.form['material_id']
        quantidade = int(request.form['quantidade'])
        usuario_id = session['user_id'] 

        conexao = conectar_banco_dados()
        cursor = conexao.cursor()

        try:
            # Verifica o estoque atual do material
            cursor.execute("SELECT SUM(quantidade) FROM estoque WHERE material_id = %s", (material_id,))
            estoque_atual = cursor.fetchone()[0] or 0

            if estoque_atual >= quantidade:
                query_insert = "INSERT INTO estoque (material_id, quantidade, tipo_movimentacao, usuario_id) VALUES (%s, %s, 'saida', %s)"
                cursor.execute(query_insert, (material_id, quantidade, usuario_id))
                conexao.commit()
                flash('Saída registrada com sucesso!', 'success')
            else:
                flash('Estoque insuficiente para registrar a saída.', 'error')

        except Exception as e:
            print(f"Erro ao registrar saída: {e}")
            flash('Erro ao registrar saída.', 'error')

        finally:
            cursor.close()
            conexao.close()

        return redirect(url_for('controle_estoque'))









# ---------------------------------------------------- FIM CONTROLE DE ESTOQUE ----------------------------------------------------


# ---------------------------------------------------- RELATORIO ----------------------------------------------------





# ---------------------------------------------------- FIM RELATORIO ----------------------------------------------------

# ---------------------------------------------------- REQUISICAO ----------------------------------------------------

@app.route('/api/requisicoes_admin')
def api_requisicoes_admin():
    if 'user_cargo' not in session or session['user_cargo'] not in ['almoxarifado', 'admin']:
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
                r.data_atualizacao,
                r.observacao
            FROM requisicoes r
            JOIN materials m ON r.material_id = m.id
            JOIN users u ON r.usuario_id = u.id 
            WHERE r.status != 'aprovada'  
            ORDER BY r.status DESC 
        """)
        requisicoes = cursor.fetchall()
    except:
        print('Erro ao buscar requisições')
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
            r.data_entrega,
            r.data_atualizacao
        FROM requisicoes r
        JOIN materials m ON r.material_id = m.id
        WHERE r.usuario_id = %s
        """, (usuario_id,))
        minhas_requisicoes = cursor.fetchall()

    except:
        print("Erro ao buscar requisições do usuário")
        return jsonify([]), 500  # Retorna uma lista vazia em caso de erro

    finally:
        cursor.close()
        conexao.close()

    return jsonify(minhas_requisicoes)




@app.route('/requisicao_material', methods=['GET', 'POST'])
def requisicao_material():
    conexao = conectar_banco_dados()
    usuario_id = session.get('user_id')
    usuario = None

    if request.method == 'POST':
        material_id = request.form['material_id']
        quantidade = int(request.form['quantidade'])
        observacao = request.form.get('observacao')

        cursor = conexao.cursor()
        try:
            inserir = "INSERT INTO requisicoes (material_id, usuario_id, quantidade, observacao) VALUES (%s, %s, %s, %s)"
            cursor.execute(inserir, (material_id, usuario_id, quantidade, observacao))
            conexao.commit()
            flash('Requisição de material enviada com sucesso!', 'success')
        except:
            print("Erro ao criar requisição")
            flash('Ocorreu um erro ao enviar a requisição. Por favor, tente novamente mais tarde.', 'error')
        finally:
            cursor.close()
            conexao.close()
        return redirect(url_for('requisicao_material'))

    # Lógica para exibir o formulário e as requisições do usuário
    cursor = conexao.cursor(dictionary=True)
    try:
        cursor.execute("SELECT m.id, m.descricao, SUM(e.quantidade) as quantidade "
                       "FROM materials m "
                       "LEFT JOIN estoque e ON m.id = e.material_id "
                       "GROUP BY m.id")
        materiais = cursor.fetchall()

        if usuario_id:
            cursor.execute("SELECT * FROM users WHERE id = %s", (usuario_id,))
            usuario = cursor.fetchone()

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
        else:
            minhas_requisicoes = []

    except:
        print("Erro ao buscar dados")
        materiais = []
        minhas_requisicoes = []

    finally:
        cursor.close()
        conexao.close()

    return render_template('funcoes/requisicao_material.html', 
                           materiais=materiais, 
                           minhas_requisicoes=minhas_requisicoes, 
                           usuario=usuario)





@app.route('/requisicao_material_admin', methods=['GET'])
def requisicao_material_admin():
    if 'user_cargo' not in session or session['user_cargo'] not in ['almoxarifado', 'admin']:
        return redirect(url_for('solicitante'))
    
    conexao = conectar_banco_dados()
    cursor = conexao.cursor(dictionary=True)

    # Fetch user information
    usuario_id = session.get('user_id')
    usuario = None
    if usuario_id:
        cursor.execute("SELECT * FROM users WHERE id = %s", (usuario_id,))
        usuario = cursor.fetchone()

    # Query for requisitions
    cursor.execute("""  
        SELECT 
            r.id,
            m.descricao AS material,
            r.quantidade,
            COALESCE((SELECT SUM(quantidade) FROM estoque WHERE material_id = m.id AND tipo_movimentacao = 'entrada'), 0) -
            COALESCE((SELECT SUM(quantidade) FROM estoque WHERE material_id = m.id AND tipo_movimentacao = 'saida'), 0) AS quantidade_estoque,
            u.nome AS usuario,
            r.status,
            r.data_entrega,
            r.observacao,
            DATE_FORMAT(r.data_atualizacao, '%H:%i') AS data_atualizacao
        FROM requisicoes r
        JOIN materials m ON r.material_id = m.id
        JOIN users u ON r.usuario_id = u.id
        WHERE r.status != 'aprovada' AND DATE(r.data_atualizacao) = CURDATE()
        ORDER BY r.status DESC 
    """)

    requisicoes = cursor.fetchall()

    cursor.close()
    conexao.close()

    return render_template('funcoes/requisicao_material_admin.html', requisicoes=requisicoes, usuario=usuario)









def enviar_email_almoxarifado(destinatario, assunto, corpo):
    remetente = "almoxarifadoinvent@gmail.com"
    senha = "gcormxmospfzsowq"  # Use uma senha de aplicativo se necessário

    mensagem = MIMEMultipart()
    mensagem['From'] = remetente
    mensagem['To'] = destinatario
    mensagem['Subject'] = assunto

    corpo_html = f"""
    <html>
    <body>
        <h2>{assunto}</h2>
        <p>{corpo}</p>
        <p>Atenciosamente,<br>Almoxarifado</p>
    </body>
    </html>
    """

    # Debug para verificar o conteúdo
    print(f"Corpo do e-mail: {corpo}")
    print(f"Corpo HTML: {corpo_html}")

    parte_html = MIMEText(corpo_html, 'html',"ANSI")
    mensagem.attach(parte_html)

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
            smtp.starttls()
            smtp.login(remetente, senha)
            smtp.sendmail(remetente, destinatario, mensagem.as_string())
        print("Email enviado com sucesso!")
    except Exception as e:
        print(f"Ocorreu um erro ao enviar o email: {e}")




def gerar_token(email):
    token = secrets.token_urlsafe(16)  # Gera um token seguro
    expires_at = datetime.now() + timedelta(hours=1)  # Define a expiração para 1 hora
    return token, expires_at

@app.route('/esquecer_senha', methods=['GET', 'POST'])
def esquecer_senha():
    if request.method == 'POST':
        data = request.form  # Use request.form para receber dados do formulário
        sn = data.get('sn')

        # Conecte-se ao banco de dados
        conn = mysql.connector.connect(user='tcc', password='123', database='almoxarifado')
        cursor = conn.cursor()

        # Verifique se o usuário existe
        cursor.execute("SELECT email FROM users WHERE sn = %s", (sn,))
        result = cursor.fetchone()

        if result:
            email = result[0]
            print(f"Usuário encontrado: {email}")  # Depuração
            token, expires_at = gerar_token(email)

            # Armazene o token e a data de expiração no banco de dados
            cursor.execute("INSERT INTO senha_resetada (email, token, expires_at) VALUES (%s, %s, %s)",
                           (email, token, expires_at))
            conn.commit()

            # Verifique se a inserção foi bem-sucedida
            if cursor.rowcount > 0:
                print("Token inserido com sucesso.")
            else:
                print("Falha ao inserir o token.")

            # Envie o e-mail com o link de redefinição de senha
            link_redefinicao = f"http://localhost:5000/redefinir_senha?token={token}"  # Use localhost
            corpo_email = f"Clique no seguinte link para redefinir sua senha: {link_redefinicao}"
            enviar_email_almoxarifado(email, "Redefinição de Senha", corpo_email)

            cursor.close()
            conn.close()
            return jsonify({"mensagem": "E-mail de redefinição de senha enviado com sucesso!"}), 200

        cursor.close()
        conn.close()
        return jsonify({"mensagem": "Usuário não encontrado."}), 404

    return render_template('recuperacao_senha.html')  # Para o método GET, retorne o formulário

@app.route('/redefinir_senha', methods=['GET', 'POST'])
def redefinir_senha():
    if request.method == 'GET':
        token = request.args.get('token')
        # Retorne um formulário de redefinição de senha ou uma página informativa
        return render_template('redefinicao_senha.html', token=token)

    if request.method == 'POST':
        token = request.args.get('token')  # Obtendo o token da URL
        nova_senha = request.form.get('nova_senha')  # Obtendo a nova senha do formulário

        # Conecte-se ao banco de dados
        conn = mysql.connector.connect(user='tcc', password='123', database='almoxarifado')
        cursor = conn.cursor()

        # Verifique se o token é válido
        cursor.execute("SELECT email FROM senha_resetada WHERE token = %s AND expires_at > NOW()", (token,))
        result = cursor.fetchone()

        if result:
            email = result[0]

            # Atualize a senha do usuário
            cursor.execute("UPDATE users SET senha = %s WHERE email = %s", (nova_senha, email))
            conn.commit()

            # Remova o token usado
            cursor.execute("DELETE FROM senha_resetada WHERE token = %s", (token,))
            conn.commit()

            cursor.close()
            conn.close()

            return redirect(url_for('login'))
        else:
            cursor.close()
            conn.close()
            return jsonify({"mensagem": "Token inválido ou expirado."}), 400
        
@app.route('/atualizar_requisicao', methods=['POST']) 
def atualizar_requisicao():
    if 'user_cargo' not in session or session['user_cargo'] not in ['almoxarifado', 'admin']:
        return redirect(url_for('solicitante'))

    data = request.get_json()
    requisicao_id = data['requisicao_id']
    acao = data['acao']

    conexao = conectar_banco_dados()
    cursor = conexao.cursor()

    try:
        # Obter material e quantidade da requisição
        cursor.execute("SELECT material_id, quantidade FROM requisicoes WHERE id = %s", (requisicao_id,))
        requisicao = cursor.fetchone()

        if requisicao:
            material_id = requisicao[0]
            quantidade_requisitada = requisicao[1]

        if acao == 'Solicitado':
            cursor.execute("UPDATE requisicoes SET status = 'Solicitado' WHERE id = %s", (requisicao_id,))
        
        elif acao == 'Disponivel para retirada':
            # Verifica o estoque antes de atualizar
            cursor.execute("SELECT quantidade FROM estoque WHERE material_id = %s", (material_id,))
            estoque_atual = cursor.fetchone()

            if estoque_atual and estoque_atual[0] >= quantidade_requisitada:
                cursor.execute("UPDATE requisicoes SET status = 'Disponivel para retirada' WHERE id = %s", (requisicao_id,))
            else:
                return jsonify({'error': 'Estoque insuficiente para marcar como disponível para retirada.'}), 400
        
        elif acao == 'Aguardando reposição':
            cursor.execute("UPDATE requisicoes SET status = 'Aguardando reposição' WHERE id = %s", (requisicao_id,))
        
        elif acao == 'Retirado':
            if requisicao:
                quantidade_retirada = requisicao[1]

                # Verifica o estoque antes de atualizar
                if estoque_atual and estoque_atual[0] >= quantidade_retirada:
                    cursor.execute("UPDATE requisicoes SET status = 'Retirado' WHERE id = %s", (requisicao_id,))
                    nova_quantidade = estoque_atual[0] - quantidade_retirada
                    cursor.execute("UPDATE estoque SET quantidade = %s WHERE material_id = %s", (nova_quantidade, material_id))
                else:
                    return jsonify({'error': 'Estoque insuficiente para retirar o material.'}), 400

        elif acao == 'aprovar':
            if requisicao:
                cursor.execute("SELECT quantidade FROM estoque WHERE material_id = %s", (material_id,))
                estoque_atual = cursor.fetchone()

                if estoque_atual and estoque_atual[0] >= quantidade_requisitada:
                    nova_quantidade = estoque_atual[0] - quantidade_requisitada
                    cursor.execute("UPDATE estoque SET quantidade = %s WHERE material_id = %s", (nova_quantidade, material_id))
                    cursor.execute("UPDATE requisicoes SET status = 'aprovada', data_entrega = NOW() WHERE id = %s", (requisicao_id,))
                else:
                    cursor.execute("UPDATE requisicoes SET status = 'pendente' WHERE id = %s", (requisicao_id,))

        conexao.commit()

        # Enviar e-mail após a atualização (ignore erros)
        assunto = f'Aviso: Requisição {requisicao_id} atualizada'
        corpo = f'A requisição com ID {requisicao_id} foi atualizada para {acao}.'

        # Tente enviar o e-mail
        try:
            email_usuario = session.get('user_email')
            if email_usuario:
                enviar_email_almoxarifado(email_usuario, assunto, corpo)
            else:
                print("E-mail do usuário não encontrado na sessão.")
        except Exception as email_error:
            print(f"Erro ao tentar enviar o e-mail: {email_error}")  # Ignora erro de envio

    except Exception as e:
        print('Erro ao atualizar requisição:', e)
        return jsonify({'error': 'Erro ao atualizar requisição'}), 500
    finally:
        cursor.close()
        conexao.close()

    return jsonify({'success': 'Status atualizado com sucesso'})












# ---------------------------------------------------- FIM REQUISICAO ----------------------------------------------------

@app.route('/estoque_minimo')
def estoque_minimo():
    conexao = conectar_banco_dados()
    cursor = conexao.cursor(dictionary=True)
    
    # Inicializar usuario
    usuario = None

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

        # Fetch user information
        usuario_id = session.get('user_id')
        if usuario_id:
            cursor.execute("SELECT * FROM users WHERE id = %s", (usuario_id,))
            usuario = cursor.fetchone()

    except mysql.connector.Error as err:
        print(f"Erro ao buscar dados de estoque mínimo: {err}")
        materiais_abaixo_minimo = []

    finally:
        cursor.close()
        conexao.close()
    
    return render_template('funcoes/estoque_minimo.html', materiais=materiais_abaixo_minimo, usuario=usuario)



@app.route('/historico_requisicoes')
def historico_requisicoes():
    conexao = conectar_banco_dados()
    cursor = conexao.cursor(dictionary=True)
    cursor.execute("""
        SELECT 
            rh.id,
            m.descricao as material,
            rh.quantidade,
            u.nome as usuario,
            rh.data_aprovacao as data_entrega  # Use a data de aprovação como data de entrega
        FROM requisicoes_historico rh
        JOIN materials m ON rh.material_id = m.id
        JOIN users u ON rh.usuario_id = u.id
    """)
    requisicoes_historico = cursor.fetchall()
    cursor.close()
    conexao.close()

    return render_template('historico_requisicoes.html', requisicoes=requisicoes_historico)

@app.route('/relatorio', methods=['GET', 'POST'])
def relatorios():
    if 'user_cargo' not in session or session['user_cargo'] not in ['almoxarifado', 'admin']:
        return redirect(url_for('solicitante'))

    relatorio = None
    relatorio_titulo = None
    tipo_relatorio = None

    usuario = None
    conexao = conectar_banco_dados()
    cursor = conexao.cursor(dictionary=True)

    # Obter informações do usuário logado
    if 'user_id' in session:
        cursor.execute("SELECT nome FROM users WHERE id = %s", (session['user_id'],))
        usuario = cursor.fetchone()

    if request.method == 'POST':
        tipo_relatorio = request.form['tipo_relatorio']

        try:
            if tipo_relatorio == 'estoque':
                cursor.execute("""
                    SELECT m.descricao AS Material, COALESCE(SUM(e.quantidade), 0) AS Quantidade
                    FROM materials m
                    LEFT JOIN estoque e ON m.id = e.material_id
                    GROUP BY m.id
                """)
                relatorio = cursor.fetchall()
                relatorio_titulo = "Relatório de Estoque"

            elif tipo_relatorio == 'movimentacao':
                cursor.execute("""
                    SELECT e.data_movimentacao AS Data, m.descricao AS Material, 
                           e.tipo_movimentacao AS Tipo, COALESCE(e.quantidade, 0) AS Quantidade, 
                           u.nome AS Usuário
                    FROM estoque e
                    JOIN materials m ON e.material_id = m.id
                    JOIN users u ON e.usuario_id = u.id
                """)
                relatorio = cursor.fetchall()
                relatorio_titulo = "Relatório de Movimentação"

            elif tipo_relatorio == 'solicitacoes_usuario':
                cursor.execute("""
                    SELECT u.nome AS Usuario, COUNT(r.id) AS TotalSolicitacoes
                    FROM requisicoes r
                    JOIN users u ON r.usuario_id = u.id
                    GROUP BY u.id
                """)
                relatorio = cursor.fetchall()
                relatorio_titulo = "Total de Solicitações por Usuário"

            elif tipo_relatorio == 'movimentacao_mensal':
                cursor.execute("""
                    SELECT MONTH(e.data_movimentacao) AS Mes,
                           SUM(CASE WHEN e.tipo_movimentacao = 'entrada' THEN e.quantidade ELSE 0 END) AS TotalEntrada,
                           SUM(CASE WHEN e.tipo_movimentacao = 'saida' THEN e.quantidade ELSE 0 END) AS TotalSaida
                    FROM estoque e
                    GROUP BY MONTH(e.data_movimentacao)
                """)
                relatorio = cursor.fetchall()
                relatorio_titulo = "Movimentação Mensal"

        except mysql.connector.Error as err:
            print(f"Erro ao gerar relatório: {err}")

        finally:
            cursor.close()
            conexao.close()

    return render_template('funcoes/relatorio.html', relatorio=relatorio, relatorio_titulo=relatorio_titulo, tipo_relatorio=tipo_relatorio, usuario=usuario)










@app.route('/logout')
def logout():
    # Limpa a sessão do usuário
    session.clear()
    # Redireciona para a página de login após o logout
    flash('Você foi desconectado com sucesso.', 'success')
    return redirect(url_for('solicitante'))



@app.route('/upload')
def upload():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_file2():

    file = request.files['file']
    link_arquivo = upload_file(file)

    return link_arquivo, 200


if __name__ == "__main__":
    app.run(debug=True)
