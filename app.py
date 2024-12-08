import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import mysql.connector
from mysql.connector import Error
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Mail, Message
import secrets
from datetime import datetime, timedelta
from contextlib import closing
# from twilio.rest import Client
# from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient

import hashlib
import threading

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




def conectar_banco_dados():
    try:
        print("Tentando conectar ao banco de dados remoto...")
        conexao = mysql.connector.connect(
            host='inventcc.mysql.database.azure.com',
            user='invent@inventcc',
            password='SENAI2024.',
            database='almoxarifado',
            # host='localhost',
            # user='tcc',
            # password='123',
            # database='almoxarifado',
        )
        print("Conexão estabelecida com sucesso!")
        return conexao
    except Error as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        raise


@app.route('/')
def solicitante():
    return render_template('banner.html')


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
            if usuario['cargo'].endswith('-nao-verificado'):
                return redirect(url_for('espera'))
            
            session['logged_in'] = True
            session['user_id'] = usuario['id']
            session['user_sn'] = usuario['sn']
            session['user_email'] = usuario['email']
            session['user_cargo'] = usuario['cargo']

            # Redireciona de acordo com o cargo
            if usuario['cargo'] == 'admin':
                return redirect(url_for('admin'))
            elif usuario['cargo'] == 'almoxarifado':
                return redirect(url_for('pg_inicial'))
            else:
                return redirect(url_for('requisicao_material'))
        else:
            flash('Credenciais inválidas. Por favor, tente novamente.', 'error')
            return redirect(url_for('login'))

    return render_template('login/login.html')

@app.route('/pg_inicial')
def pg_inicial():
    # Conectando ao banco de dados
    conexao = conectar_banco_dados()
    usuario_id = session.get('user_id')  # Obtendo o ID do usuário da sessão

    if usuario_id:
        # Buscando informações do usuário no banco de dados
        cursor = conexao.cursor(dictionary=True)  # Usando 'dictionary=True' para obter resultados como dicionário
        cursor.execute("SELECT * FROM users WHERE id = %s", (usuario_id,))
        usuario = cursor.fetchone()
        
        if usuario:
            # Caso o usuário exista no banco de dados, envia as informações para o template
            return render_template('index.html', usuario=usuario)
        else:
            flash('Usuário não encontrado.', 'error')
            return redirect(url_for('login'))
    else:
        flash('Você precisa estar logado para acessar esta página.', 'error')
        return redirect(url_for('login'))

    # Fechando o cursor e a conexão com o banco de dados
    cursor.close()
    conexao.close()



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
        nome = request.form['nome']
        email = request.form['email']
        senha_atual = request.form['senha_atual']
        nova_senha = request.form['senha']
        confirmar_senha = request.form['confirmar_senha']

        cursor = conexao.cursor()

        # Valida se a senha atual está correta, caso o usuário esteja tentando trocá-la
        if nova_senha:
            cursor.execute("SELECT senha FROM users WHERE id = %s", (usuario_id,))
            senha_bd = cursor.fetchone()[0]

            # Verifica a senha atual
            if not senha_atual or senha_atual != senha_bd:
                flash('A senha atual está incorreta.', 'error')
                cursor.close()
                conexao.close()
                return redirect(url_for('editar_perfil'))

            # Verifica se a nova senha tem pelo menos 8 caracteres
            if len(nova_senha) < 8:
                flash('A nova senha deve ter pelo menos 8 caracteres.', 'error')
                cursor.close()
                conexao.close()
                return redirect(url_for('editar_perfil'))

            # Verifica se a nova senha coincide com a confirmação
            if nova_senha != confirmar_senha:
                flash('As novas senhas não coincidem.', 'error')
                cursor.close()
                conexao.close()
                return redirect(url_for('editar_perfil'))

            # Atualiza a senha no banco de dados
            cursor.execute("UPDATE users SET nome = %s, email = %s, senha = %s WHERE id = %s", 
                           (nome, email, nova_senha, usuario_id))
        else:
            # Atualiza somente o nome e o email, sem mudar a senha
            cursor.execute("UPDATE users SET nome = %s, email = %s WHERE id = %s", 
                           (nome, email, usuario_id))

        conexao.commit()
        flash('Perfil atualizado com sucesso!', 'success')
        cursor.close()
        conexao.close()
        return redirect(url_for('editar_perfil'))

    cursor = conexao.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE id = %s", (usuario_id,))
    usuario = cursor.fetchone()
    cursor.close()
    conexao.close()
    
    return render_template('editar_perfil.html', usuario=usuario)

def gerar_hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()


@app.route('/cadastrar_usuario', methods=['POST'])
def cadastrar_usuario():
    dados = request.json
    sn = dados.get('sn')
    nome = dados.get('nome')

    if not sn or not nome:
        flash('SN e Nome são obrigatórios.', 'error')
        return jsonify({'success': False})

    conexao = conectar_banco_dados()
    if conexao:
        try:
            cursor = conexao.cursor()

            # Verificar se o SN já existe
            query_verificar = "SELECT COUNT(*) FROM users WHERE sn = %s"
            cursor.execute(query_verificar, (sn,))
            if cursor.fetchone()[0] > 0:
                flash('SN já cadastrado. Escolha outro.', 'error')
                return jsonify({'success': False})

            # Inserir o novo usuário
            query_inserir = "INSERT INTO users (sn, nome) VALUES (%s, %s)"
            cursor.execute(query_inserir, (sn, nome))
            conexao.commit()

            flash('Usuário cadastrado com sucesso!', 'success')
            return jsonify({'success': True})
        except Error as e:
            print(f"Erro ao cadastrar usuário: {e}")
            flash('Erro ao cadastrar usuário. Tente novamente.', 'error')
            return jsonify({'success': False})
        finally:
            cursor.close()
            conexao.close()
    else:
        flash('Falha na conexão com o banco de dados.', 'error')
        return jsonify({'success': False})




@app.route('/cadastrar_usuario', methods=['POST'])
def cadastrar_usuario_endpoint():
    try:
        data = request.get_json()
        sn = data.get("sn")
        nome = data.get("nome")


        # Chamar função de cadastro
        mensagem = cadastrar_usuario(sn, nome)

        return jsonify({"mensagem": mensagem}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 400


@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        # Obtém os dados do formulário
        nome = request.form['nome']  # Agora obtendo o nome
        sn = request.form['sn']
        email = request.form['email']  # Você pode manter o email, mas não usá-lo para verificação
        senha = request.form['senha']
        area = request.form['areas-senai']  # Agora obtendo a variável 'area'

        # Conecta ao banco de dados
        conexao = conectar_banco_dados()
        cursor = conexao.cursor(dictionary=True)

        # Insere os dados diretamente no banco, incluindo o nome, área (cargo), e senha
        query_insert = """
            INSERT INTO users (nome, sn, email, cargo, senha) 
            VALUES (%s, %s, %s, %s, %s)
        """
        # Aqui estamos inserindo o nome, sn, email, cargo (que vem de 'area' no frontend), e senha
        cursor.execute(query_insert, (nome, sn, email, area, senha))
        conexao.commit()

        cursor.close()
        conexao.close()

        flash('Cadastro realizado com sucesso!', 'success')
        return redirect(url_for('login'))

    return render_template('login/cadastro.html')




# ---------------------------------------------------- FIM DO LOGIN ----------------------------------------------------

# ---------------------------------------------------- TELA INICIAL ----------------------------------------------------


@app.route('/autenticacao')
def verificar_autenticacao():
    if 'user_id' in session:
        return jsonify({'autenticado': True})
    else:
        return jsonify({'autenticado': False})

@app.route('/historico')
def historico():
    if 'user_id' not in session:
        flash('Você precisa estar logado para acessar essa página.', 'error')
        return redirect(url_for('login'))

    user_id = session['user_id']
    conexao = conectar_banco_dados()
    cursor = conexao.cursor(dictionary=True)

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

        # Contar todas as requisições com status 'Retirado' hoje
        cursor.execute("""
            SELECT COUNT(*) AS total_retirados
            FROM requisicoes r
            WHERE r.status = 'Retirado' AND DATE(r.data_requisicao) = CURDATE()
        """)
        requisicoes_retiradas = cursor.fetchone()
        total_retirados = requisicoes_retiradas['total_retirados'] if requisicoes_retiradas else 0

        # Atualizar consulta para incluir data_atualizacao (se necessário)
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
        total_retirados = 0

    finally:
        cursor.close()
        conexao.close()

    return render_template('historico.html', 
                           estoque_minimo=estoque_minimo,
                           produtos_estoque_minimo=produtos_estoque_minimo,
                           historico_hoje=historico_hoje,
                           usuario=usuario,
                           total_retirados=total_retirados)  # Passando o total de retirados para o template






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

    # Listar categorias disponíveis
    categorias = ['consumiveis', 'ferramentas', 'equipamentos', 'materiais_de_escritorio', 
                  'limpeza', 'tecnologia', 'marcenaria', 'papelaria', 'seguranca']

    # Modificar cada categoria para ter a primeira letra maiúscula e espaços no lugar de underscores
    categorias_formatadas = [categoria.replace('_', ' ').capitalize() for categoria in categorias]

    if request.method == 'POST':
        descricao = request.form['descricao_produto']
        categoria = request.form['categoria']
        estoque_minimo = int(request.form['estoque_minimo'] or 0)
        codigo_produto = int(request.form['codigo_produto'] or 0)

        try:
            # Inserção na tabela com os campos corretos
            query_insert = ("INSERT INTO materials (descricao, categoria, estoque_minimo, codigo_produto) "
                            "VALUES (%s, %s, %s, %s)")
            cursor.execute(query_insert, (descricao, categoria, estoque_minimo, codigo_produto))
            conexao.commit()

            flash('Material cadastrado com sucesso!', 'success')
            return redirect(url_for('cadastro_material'))

        except mysql.connector.Error as err:
            flash('Erro ao cadastrar material: {}'.format(err), 'error')

    cursor.close()
    conexao.close()

    return render_template(
        'funcoes/cadastro_material.html',
        usuario=usuario,
        categorias=categorias_formatadas
    )




# ---------------------------------------------------- FIM CADASTRO MATERIAL ----------------------------------------------------


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if 'user_cargo' not in session or session['user_cargo'] not in ['almoxarifado', 'admin', '']:
        flash('Acesso negado. Você não tem permissão para acessar esta página.', 'error')
        return redirect(url_for('solicitante'))

    conexao = conectar_banco_dados()
    cursor = conexao.cursor(dictionary=True)

        # Buscar todos os usuários
    cursor.execute("SELECT * FROM users")
    usuarios = cursor.fetchall()

    # Obter o nome do usuário logado
    cursor.execute("SELECT nome FROM users WHERE id = %s", (session['user_id'],))
    usuario_logado = cursor.fetchone()

    if request.method == 'POST':
        user_id = request.form.get('user_id')
        nome = request.form.get('nome')
        email = request.form.get('email')
        sn = request.form.get('sn', '')
        cargo = request.form.get('cargo')
        senha = request.form.get('senha')

        if session['user_cargo'] == 'admin':
            query_update = "UPDATE users SET nome = %s, email = %s, sn = %s, cargo = %s, senha = %s WHERE id = %s"
            cursor.execute(query_update, (nome, email, sn, cargo, senha, user_id))
        else:
            query_update = "UPDATE users SET nome = %s, email = %s, senha = %s WHERE id = %s"
            cursor.execute(query_update, (nome, email, senha, user_id))
        
        conexao.commit()
        flash('Usuário atualizado com sucesso!', 'success')



    cursor.close()
    conexao.close()

    return render_template('admin/admin.html', usuarios=usuarios, usuario=usuario_logado)

@app.route('/aprovar_usuario', methods=['POST'])
def aprovar_usuario():
    user_id = request.form['user_id']
    conexao = conectar_banco_dados()
    cursor = conexao.cursor()

    # Obtém o cargo atual do usuário
    query_select = "SELECT cargo FROM users WHERE id = %s"
    cursor.execute(query_select, (user_id,))
    cargo_atual = cursor.fetchone()[0]

    # Remove o sufixo '-nao-verificado' do cargo
    novo_cargo = cargo_atual.replace('-nao-verificado', '')

    # Atualiza o cargo do usuário para o novo valor
    query_update = "UPDATE users SET cargo = %s WHERE id = %s"
    cursor.execute(query_update, (novo_cargo, user_id))
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
        # Remover referências nas tabelas relacionadas
        query_delete_lembretes = "DELETE FROM lembretes WHERE destinatario = %s"
        cursor.execute(query_delete_lembretes, (user_id,))

        query_delete_requisicoes = "DELETE FROM requisicoes WHERE usuario_id = %s"
        cursor.execute(query_delete_requisicoes, (user_id,))

        query_delete_estoque = "DELETE FROM estoque WHERE usuario_id = %s"
        cursor.execute(query_delete_estoque, (user_id,))

        # Executar exclusão do usuário
        query_delete_user = "DELETE FROM users WHERE id = %s"
        cursor.execute(query_delete_user, (user_id,))
        conexao.commit()

        return jsonify({'success': True, 'message': 'Usuário excluído com sucesso!'})

    except mysql.connector.errors.IntegrityError as e:
        flash('Não é possível excluir o usuário. Existem registros associados.', 'error')
        conexao.rollback()
        return jsonify({'success': False, 'message': 'Não é possível excluir o usuário. Existem registros associados.'})
    except Exception as e:
        print(f"Erro inesperado: {e}")  # Log do erro
        flash('Erro ao excluir o usuário.', 'error')
        conexao.rollback()
        return jsonify({'success': False, 'message': 'Erro ao excluir o usuário.'})
    finally:
        cursor.close()
        conexao.close()




@app.route('/editar_usuario', methods=['POST'])
def editar_usuario():
    try:
        user_id = request.form['user_id']  # Obtém o ID do usuário a ser editado

        # Conectar ao banco de dados
        conexao = conectar_banco_dados()
        cursor = conexao.cursor(dictionary=True)

        # Captura os dados atualizados do formulário de edição
        nome = request.form.get('nome')
        email = request.form.get('email')
        sn = request.form.get('sn', '')  # Atribui um valor vazio caso o SN não seja enviado
        cargo = request.form.get('cargo')  # Se o campo cargo existir, inclua
        senha = request.form.get('senha')  # Se o campo senha existir, inclua

        # Verifique se todos os dados necessários foram fornecidos
        if not nome or not email or not sn:
            flash('Todos os campos obrigatórios devem ser preenchidos.', 'danger')
            return redirect(url_for('editar_usuario', user_id=user_id))

        # Atualiza as informações do usuário no banco de dados
        query_update = "UPDATE users SET nome = %s, email = %s, sn = %s WHERE id = %s"
        cursor.execute(query_update, (nome, email, sn, user_id))

        # Verifique se a linha foi realmente alterada
        if cursor.rowcount == 0:
            flash('Nenhum usuário encontrado para atualizar com esse ID.', 'danger')
        else:
            flash('Usuário atualizado com sucesso!', 'success')

        conexao.commit()

        # Fechar a conexão
        cursor.close()
        conexao.close()

    except Exception as e:
        flash(f'Ocorreu um erro: {str(e)}', 'danger')

    # Redireciona de volta para a página de edição, para que o usuário veja a mensagem
    return redirect(url_for('editar_usuario', user_id=user_id))





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
        # Obtain all materials and calculate available quantity, including codigo_produto
        cursor.execute(""" 
            SELECT 
                m.id, 
                m.descricao, 
                m.codigo_produto,  -- Including the product code
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
                m.descricao AS material,
                r.quantidade,
                COALESCE((SELECT SUM(quantidade) FROM estoque WHERE material_id = m.id AND tipo_movimentacao = 'entrada'), 0) -
                COALESCE((SELECT SUM(quantidade) FROM estoque WHERE material_id = m.id AND tipo_movimentacao = 'saida'), 0) AS quantidade_estoque,
                u.nome AS usuario,
                r.status,
                r.data_atualizacao,
                r.observacao,
                DATE_FORMAT(r.data_atualizacao, '%Y-%m-%d %H:%i:%s') AS data_atualizacao
            FROM requisicoes r
            JOIN materials m ON r.material_id = m.id
            JOIN users u ON r.usuario_id = u.id
            WHERE r.status != 'aprovada'
            ORDER BY r.data_atualizacao DESC
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
            r.data_atualizacao
        FROM requisicoes r
        JOIN materials m ON r.material_id = m.id
        WHERE r.usuario_id = %s
        """, (usuario_id,))
        minhas_requisicoes = cursor.fetchall()

        # Formatação de data no JSON
        for requisicao in minhas_requisicoes:
            requisicao['data_atualizacao'] = (datetime.strptime(requisicao['data_atualizacao'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M') 
                                              if requisicao['data_atualizacao'] else 'N/A')

    except Exception as e:
        print(f"Erro ao buscar requisições do usuário: {e}")
        return jsonify([]), 500

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
        quantidade = request.form.get('quantidade')
        observacao = request.form.get('observacao')

        # Verificar se quantidade está vazia ou nula
        if not quantidade:
            flash('Por favor, preencha o campo de quantidade.', 'error')
            return redirect(url_for('requisicao_material'))

        try:
            quantidade = int(quantidade)  # Conversão segura para inteiro
        except ValueError:
            flash('Quantidade inválida. Por favor, insira um número.', 'error')
            return redirect(url_for('requisicao_material'))

        cursor = conexao.cursor()
        try:
            inserir = "INSERT INTO requisicoes (material_id, usuario_id, quantidade, observacao) VALUES (%s, %s, %s, %s)"
            cursor.execute(inserir, (material_id, usuario_id, quantidade, observacao))
            conexao.commit()
            flash('Requisição de material enviada com sucesso!', 'success')

            # Obter a descrição do material requisitado
            cursor.execute("SELECT descricao FROM materials WHERE id = %s", (material_id,))
            material = cursor.fetchone()
            nome_produto = material[0] if material else "Produto não encontrado"  # Acessando o valor corretamente pela tupla

            # Obter os e-mails de todos os usuários com cargo "almoxarifado"
            cursor.execute("SELECT email FROM users WHERE cargo = 'almoxarifado'")
            emails_almoxarifado = cursor.fetchall()

            # Enviar e-mails de forma assíncrona
            if emails_almoxarifado:
                assunto = f'Aviso: Nova Requisição Criada - {nome_produto}'
                corpo = f"""
                <p>Olá,</p>
                <p>Uma nova requisição foi registrada no sistema:</p>
                <ul>
                    <li><strong>Produto:</strong> {nome_produto}</li>
                    <li><strong>Quantidade:</strong> {quantidade}</li>
                    <li><strong>Observação:</strong> {observacao}</li>
                </ul>
                <p>Por favor, acesse o sistema para visualizar os detalhes e tomar as ações necessárias.</p>
                """
                enviar_emails_assincronos(emails_almoxarifado, assunto, corpo)  # Chama a função para enviar os e-mails de forma assíncrona

            else:
                print("Nenhum usuário com cargo 'almoxarifado' encontrado para envio de e-mails.")

        except Exception as e:
            print("Erro ao criar requisição:", e)
            flash('Ocorreu um erro ao enviar a requisição. Por favor, tente novamente mais tarde.', 'error')
        finally:
            cursor.close()
            conexao.close()
        return redirect(url_for('requisicao_material'))

    # Lógica para exibir o formulário e as requisições do usuário
    cursor = conexao.cursor(dictionary=True)
    try:
        cursor.execute(""" 
            SELECT 
                m.id, 
                m.descricao, 
                m.codigo_produto, 
                COALESCE(SUM(CASE WHEN e.tipo_movimentacao = 'entrada' THEN e.quantidade ELSE 0 END), 0) AS total_entrada,
                COALESCE(SUM(CASE WHEN e.tipo_movimentacao = 'saida' THEN e.quantidade ELSE 0 END), 0) AS total_saida,
                COALESCE(SUM(CASE WHEN e.tipo_movimentacao = 'entrada' THEN e.quantidade ELSE 0 END), 0) - 
                COALESCE(SUM(CASE WHEN e.tipo_movimentacao = 'saida' THEN e.quantidade ELSE 0 END), 0) AS quantidade_disponivel
            FROM materials m
            LEFT JOIN estoque e ON m.id = e.material_id
            GROUP BY m.id
            ORDER BY m.descricao ASC
        """)
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
                    r.data_atualizacao
                FROM requisicoes r
                JOIN materials m ON r.material_id = m.id
                WHERE r.usuario_id = %s
            """, (usuario_id,))
            minhas_requisicoes = cursor.fetchall()

            # Formatar a data de entrega antes de passar para o template
            for requisicao in minhas_requisicoes:
                if requisicao['data_atualizacao']:
                    # Verifica se é uma string ou objeto datetime e formata
                    if isinstance(requisicao['data_atualizacao'], str):
                        # Se for string, converte para datetime
                        try:
                            requisicao['data_atualizacao'] = datetime.strptime(requisicao['data_atualizacao'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M')
                        except ValueError:
                            requisicao['data_atualizacao'] = 'Data inválida'
                    else:
                        requisicao['data_atualizacao'] = requisicao['data_atualizacao'].strftime('%d/%m/%Y %H:%M')
                else:
                    requisicao['data_atualizacao'] = 'N/A'  # Caso a data não esteja disponível

        else:
            minhas_requisicoes = []

    except Exception as e:
        print("Erro ao buscar dados:", e)
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
                r.data_atualizacao,
                r.observacao,
                DATE_FORMAT(r.data_atualizacao, '%H:%i') AS data_atualizacao
            FROM requisicoes r
            JOIN materials m ON r.material_id = m.id
            JOIN users u ON r.usuario_id = u.id
            WHERE r.status != 'aprovada' AND r.data_atualizacao >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
            ORDER BY r.status DESC 
        """)

        requisicoes = cursor.fetchall()

    cursor.close()
    conexao.close()

    return render_template('funcoes/requisicao_material_admin.html', requisicoes=requisicoes, usuario=usuario)




def enviar_emails_assincronos(emails, assunto, corpo):
    def enviar():
        if isinstance(emails, str):  # Caso só tenha um email
            enviar_email_almoxarifado(emails, assunto, corpo)
        else:
            for email_data in emails:
                enviar_email_almoxarifado(email_data[0], assunto, corpo)  # Envia os e-mails

    # Cria um thread para enviar os e-mails de forma assíncrona
    thread = threading.Thread(target=enviar)
    thread.start()




def enviar_email_almoxarifado(destinatario, assunto, corpo, tipo="requisicao"):
    remetente = "almoxarifadoinvent@gmail.com"
    senha = "gcormxmospfzsowq"  # Use uma senha de aplicativo se necessário

    # Corpo do e-mail em formato HTML simples
    corpo_html = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
                text-align: center;
            }}
            .container {{
                width: 100%;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
                background-color: #ffffff;
                border-radius: 8px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }}
            .header {{
                text-align: center;
                padding-bottom: 20px;
            }}
            .header img {{
                max-width: 120px;  /* Ajuste a largura máxima da logo */
                height: auto;
            }}
            h2 {{
                color: #465E8C;
                margin-bottom: 20px;
            }}
            p {{
                font-size: 16px;
                color: #333333;
                margin-bottom: 10px;
            }}
            .strong-text {{
                font-weight: bold;
            }}
            .button {{
                display: inline-block;
                padding: 10px 20px;
                background-color: #384773;
                color: #ffffff;
                text-decoration: none;
                border-radius: 5px;
                margin-top: 20px;
            }}
            .footer {{
                font-size: 12px;
                color: #999999;
                margin-top: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <!-- Logo -->
                <img src="https://inventmais.blob.core.windows.net/arquivos/inventmais.png" alt="Logo Almoxarifado">
            </div>
            <h2>{assunto}</h2>
            <p>{corpo}</p>
    """

    if tipo == "senha":
        corpo_html += f"""
            <a href="{corpo}" class="button">Redefinir Senha</a>
        """
    elif tipo == "requisicao":
        corpo_html += f"""
            <p>Por favor, verifique as informações da sua requisição no sistema.</p>
        """
    
    corpo_html += f"""
            <p class="footer">Atenciosamente,<br>Equipe Almoxarifado</p>
        </div>
    </body>
    </html>
    """

    # Criar a mensagem do e-mail
    mensagem = MIMEMultipart()
    mensagem['From'] = remetente
    mensagem['To'] = destinatario
    mensagem['Subject'] = assunto

    parte_html = MIMEText(corpo_html, 'html', "ANSI")
    mensagem.attach(parte_html)

    try:
        # Conectar e enviar o e-mail
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
    flash_message = None  # Variável para armazenar a mensagem de flash

    if request.method == 'POST':
        sn_ou_email = request.form.get('sn_email')  # Captura o SN ou e-mail do formulário

        # Conecte-se ao banco de dados
        conn = mysql.connector.connect(user='tcc', password='123', database='almoxarifado')
        cursor = conn.cursor()

        # Verifique se o SN ou o e-mail existe
        cursor.execute("SELECT email FROM users WHERE sn = %s OR email = %s", (sn_ou_email, sn_ou_email))
        result = cursor.fetchone()

        if result:
            email = result[0]
            print(f"Usuário encontrado: {email}")  # Depuração
            token, expires_at = gerar_token(email)

            # Armazene o token e a data de expiração no banco de dados
            cursor.execute("INSERT INTO senha_resetada (email, token, expires_at) VALUES (%s, %s, %s)",
                           (email, token, expires_at))
            conn.commit()

            if cursor.rowcount > 0:
                print("Token inserido com sucesso.")
            else:
                print("Falha ao inserir o token.")

            # Envie o e-mail com o link de redefinição de senha
            link_redefinicao = f"http://localhost:5000/redefinir_senha?token={token}"  # Use localhost
            corpo_email = f"Clique no seguinte link para redefinir sua senha: {link_redefinicao}"
            enviar_email_almoxarifado(email, "Redefinição de Senha", corpo_email)

            # Definir a mensagem de sucesso
            flash_message = "E-mail de redefinição de senha enviado com sucesso!"
        else:
            # Definir a mensagem de erro
            flash_message = "Usuário não encontrado."

        cursor.close()
        conn.close()

        # Redireciona para a mesma página, passando a mensagem flash
        return render_template('recuperacao_senha.html', flash_message=flash_message)

    return render_template('recuperacao_senha.html', flash_message=flash_message)





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

            # Flash de sucesso
            flash("Senha redefinida com sucesso! Você pode agora fazer login.", "success")
            return redirect(url_for('login'))  # Redireciona para a página de login
        else:
            cursor.close()
            conn.close()

            # Flash de erro
            flash("Token inválido ou expirado.", "error")
            return redirect(url_for('redefinir_senha', token=token))  # Redireciona de volta para o formulário
        
        
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
        # Obter material, quantidade e usuário da requisição
        cursor.execute("SELECT material_id, quantidade, usuario_id FROM requisicoes WHERE id = %s", (requisicao_id,))
        requisicao = cursor.fetchone()

        if requisicao:
            material_id = requisicao[0]
            quantidade_requisitada = requisicao[1]
            usuario_id = requisicao[2]  # ID do usuário que fez a requisição

            # Calcula o estoque atual disponível para o material solicitado
            cursor.execute(""" 
                SELECT SUM(quantidade) FROM estoque 
                WHERE material_id = %s AND tipo_movimentacao = 'entrada' 
            """, (material_id,))
            total_entradas = cursor.fetchone()[0] or 0  # Se não houver entradas, usa 0

            cursor.execute(""" 
                SELECT SUM(quantidade) FROM estoque 
                WHERE material_id = %s AND tipo_movimentacao = 'saida' 
            """, (material_id,))
            total_saidas = cursor.fetchone()[0] or 0  # Se não houver saídas, usa 0

            estoque_atual = total_entradas - total_saidas

            # Atualizar o status conforme a ação
            if acao == 'Solicitado':
                cursor.execute("UPDATE requisicoes SET status = 'Solicitado' WHERE id = %s", (requisicao_id,))
                flash('Material solicitado e estoque atualizado com sucesso!', 'success')

            elif acao == 'Disponivel para retirada':
                if estoque_atual >= quantidade_requisitada:
                    # Atualiza o status da requisição
                    cursor.execute("UPDATE requisicoes SET status = 'Disponivel para retirada' WHERE id = %s", (requisicao_id,))

                    # Registra a saída do material (movimentação de saída)
                    cursor.execute(""" 
                        INSERT INTO estoque (material_id, quantidade, tipo_movimentacao, usuario_id) 
                        VALUES (%s, %s, 'saida', %s) 
                    """, (material_id, quantidade_requisitada, usuario_id))

                    flash('Material disponível para retirada e estoque atualizado com sucesso!', 'success')
                else:
                    flash('Estoque insuficiente para esta ação. Verifique a quantidade disponível.', 'error')

            elif acao == 'Retirado':
                if estoque_atual >= quantidade_requisitada:
                    # Atualiza o status da requisição para "Retirado"
                    cursor.execute("UPDATE requisicoes SET status = 'Retirado' WHERE id = %s", (requisicao_id,))

                    flash('Material retirado e estoque atualizado com sucesso!', 'success')
                else:
                    flash('Estoque insuficiente para esta ação. Verifique a quantidade disponível.', 'error')
                    return jsonify({
                        'error': 'Estoque insuficiente para retirar o material.',
                        'estoque_atual': estoque_atual,
                        'quantidade_requisitada': quantidade_requisitada
                    }), 400

            elif acao == 'Aguardando reposição':
                cursor.execute("UPDATE requisicoes SET status = 'Aguardando reposição' WHERE id = %s", (requisicao_id,))

            elif acao == 'aprovar':
                cursor.execute("SELECT quantidade FROM estoque WHERE material_id = %s", (material_id,))
                estoque_atual = cursor.fetchone()
                if estoque_atual and estoque_atual[0] >= quantidade_requisitada:
                    nova_quantidade = estoque_atual[0] - quantidade_requisitada
                    cursor.execute("UPDATE estoque SET quantidade = %s WHERE material_id = %s", (nova_quantidade, material_id))
                    cursor.execute("UPDATE requisicoes SET status = 'aprovada', data_atualizacao = NOW() WHERE id = %s", (requisicao_id,))
                else:
                    cursor.execute("UPDATE requisicoes SET status = 'pendente' WHERE id = %s", (requisicao_id,))

            conexao.commit()

            # Recuperar o nome do produto e e-mail do usuário que fez a requisição
            cursor.execute("SELECT email FROM users WHERE id = %s", (usuario_id,))
            usuario = cursor.fetchone()
            if usuario:
                cursor.execute("SELECT descricao FROM materials WHERE id = %s", (material_id,))
                material = cursor.fetchone()
                nome_produto = material[0] if material else "Produto não encontrado"
                email_usuario = usuario[0]
                assunto = f'Aviso: Atualização de Requisição - {nome_produto}'
                corpo = f"""
                <p>A requisição referente ao produto <span class="strong-text">"{nome_produto}"</span> foi atualizada para <span class="strong-text">"{acao}"</span>.</p>
                """
                enviar_emails_assincronos(email_usuario, assunto, corpo)  # Envia e-mail de forma assíncrona
            else:
                print("Usuário não encontrado para a requisição.")

            return jsonify({'message': 'Requisição atualizada com sucesso'}), 200

    except Exception as e:
        conexao.rollback()
        return jsonify({'error': str(e)}), 500

    finally:
        cursor.close()
        conexao.close()














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
            rh.data_aprovacao as data_atualizacao  # Use a data de aprovação como data de entrega
        FROM requisicoes_historico rh
        JOIN materials m ON rh.material_id = m.id
        JOIN users u ON rh.usuario_id = u.id
    """)
    requisicoes_historico = cursor.fetchall()
    cursor.close()
    conexao.close()

    return render_template('historico_requisicoes.html', requisicoes=requisicoes_historico)

meses_portugues = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho",
    7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
}

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
                    ORDER BY m.descricao ASC  -- Ordena os materiais em ordem alfabética
                """)
                relatorio = cursor.fetchall()
                relatorio_titulo = "Relatório de Estoque"

            elif tipo_relatorio == 'movimentacao':
                cursor.execute("""
                    SELECT e.data_movimentacao AS Data, m.descricao AS Material, 
                           e.tipo_movimentacao AS Tipo, COALESCE(e.quantidade, 0) AS Quantidade, 
                           u.nome AS Usuario
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
                
                # Converte os números dos meses para nome em português
                for item in relatorio:
                    mes_numero = item['Mes']
                    item['Mes'] = meses_portugues.get(mes_numero, str(mes_numero))  # Converte para português ou mantém o número caso não haja

        except mysql.connector.Error as err:
            flash(f"Erro ao gerar relatório: {err}", 'error')

        finally:
            cursor.close()
            conexao.close()

    return render_template('funcoes/relatorio.html', 
                           relatorio=relatorio, 
                           relatorio_titulo=relatorio_titulo, 
                           tipo_relatorio=tipo_relatorio, 
                           usuario=usuario)











@app.route('/logout')
def logout():
    # Limpa a sessão do usuário
    session.clear()
    # Redireciona para a página de login após o logout
    flash('Você foi desconectado com sucesso.', 'success')
    return redirect(url_for('login'))



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
