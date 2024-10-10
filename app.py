import os
import uuid
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import mysql.connector
from mysql.connector import Error
# from twilio.rest import Client
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient

# EMAIL
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Carregar variáveis do .env
load_dotenv()

# Inicialização do Flask
app = Flask(__name__)
app.secret_key = 'teste'



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
            session['user_email'] = usuario['email']
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

        # Atualizar consulta para incluir data_atualizacao
        cursor.execute("""
            SELECT r.id, r.quantidade, r.status, m.descricao AS material, u.nome AS usuario, r.data_atualizacao
            FROM requisicoes r
            JOIN materials m ON r.material_id = m.id
            JOIN users u ON r.usuario_id = u.id
            WHERE DATE(r.data_requisicao) = CURDATE()
        """)
        historico_hoje = cursor.fetchall()

    except mysql.connector.Error as err:
        print(f"Erro: {err}")
        estoque_minimo = 0
        produtos_estoque_minimo = []
        historico_hoje = []

    finally:
        cursor.close()
        conexao.close()

    return render_template('index.html', 
                           estoque_minimo=estoque_minimo,
                           produtos_estoque_minimo=produtos_estoque_minimo,
                           historico_hoje=historico_hoje)




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
        # Obtém todos os materiais e calcula a quantidade disponível
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
        print("Erro ao buscar dados")
        materiais = []
        minhas_requisicoes = []

    finally:
        cursor.close()
        conexao.close()

    return render_template('funcoes/requisicao_material.html', materiais=materiais, minhas_requisicoes=minhas_requisicoes)




@app.route('/requisicao_material_admin', methods=['GET'])
def requisicao_material_admin():
    if 'user_cargo' not in session or session['user_cargo'] != 'almoxarifado':
        return redirect(url_for('solicitante'))
    
    conexao = conectar_banco_dados()
    cursor = conexao.cursor(dictionary=True)

    # Consulta para calcular o estoque total de cada material
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

    return render_template('funcoes/requisicao_material_admin.html', requisicoes=requisicoes)








def enviar_email_almoxarifado(destinatario, assunto, corpo):
    remetente = "almoxarifadoinvent@gmail.com"
    senha = "gcormxmospfzsowq"  # Use uma senha de aplicativo se necessário

    mensagem = MIMEMultipart()
    mensagem['From'] = remetente
    mensagem['To'] = destinatario
    mensagem['Subject'] = assunto
    
    # Corpo do email em HTML
    corpo_html = f"""
    <html>
    <body>
        <h2>{assunto}</h2>
        <p>{corpo}</p>
        <p>Atenciosamente,<br>Almoxarifado</p>
    </body>
    </html>
    """
    
    parte_html = MIMEText(corpo_html, 'html')
    mensagem.attach(parte_html)

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
            smtp.starttls()
            smtp.login(remetente, senha)
            smtp.sendmail(remetente, destinatario, mensagem.as_string())
        print("Email enviado com sucesso!")
    except Exception as e:
        print(f"Ocorreu um erro ao enviar o email: {e}")




@app.route('/atualizar_requisicao', methods=['POST']) 
def atualizar_requisicao():
    if 'user_cargo' not in session or session['user_cargo'] != 'almoxarifado':
        return redirect(url_for('solicitante'))

    data = request.get_json()
    requisicao_id = data['requisicao_id']
    acao = data['acao']

    conexao = conectar_banco_dados()
    cursor = conexao.cursor()

    try:
        if acao == 'Solicitado':
            cursor.execute("UPDATE requisicoes SET status = 'Solicitado' WHERE id = %s", (requisicao_id,))
        
        elif acao == 'Disponivel para retirada':
            cursor.execute("UPDATE requisicoes SET status = 'Disponivel para retirada' WHERE id = %s", (requisicao_id,))
        
        elif acao == 'Aguardando reposição':
            cursor.execute("UPDATE requisicoes SET status = 'Aguardando reposição' WHERE id = %s", (requisicao_id,))
        
        elif acao == 'Retirado':
            cursor.execute("UPDATE requisicoes SET status = 'Retirado' WHERE id = %s", (requisicao_id,))
        
        elif acao == 'aprovar':
            cursor.execute("SELECT material_id, quantidade FROM requisicoes WHERE id = %s", (requisicao_id,))
            requisicao = cursor.fetchone()

            if requisicao:
                material_id = requisicao[0]
                quantidade_requisitada = requisicao[1]

                cursor.execute("SELECT quantidade FROM estoque WHERE material_id = %s", (material_id,))
                estoque_atual = cursor.fetchone()

                if estoque_atual and estoque_atual[0] >= quantidade_requisitada:
                    nova_quantidade = estoque_atual[0] - quantidade_requisitada
                    cursor.execute("UPDATE estoque SET quantidade = %s WHERE material_id = %s", (nova_quantidade, material_id))
                    cursor.execute("UPDATE requisicoes SET status = 'aprovada', data_entrega = NOW() WHERE id = %s", (requisicao_id,))
                else:
                    cursor.execute("UPDATE requisicoes SET status = 'pendente' WHERE id = %s", (requisicao_id,))

        conexao.commit()

        # Enviar e-mail após a atualização
        assunto = f'Aviso: Requisição {requisicao_id} atualizada'
        corpo = f'A requisição com ID {requisicao_id} foi atualizada para {acao}.'

        # Tente enviar o e-mail
        try:
            email_usuario = session.get('user_email')  # Certifique-se de que o e-mail do usuário foi salvo na sessão durante o login
            if email_usuario:
                enviar_email_almoxarifado(email_usuario, assunto, corpo)
            else:
                print("E-mail do usuário não encontrado na sessão.")
        except Exception as email_error:
            print(f"Erro ao tentar enviar o e-mail: {email_error}")

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
    
    return render_template('funcoes/estoque_minimo.html', materiais=materiais_abaixo_minimo)


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
    if 'user_cargo' not in session or session['user_cargo'] != 'almoxarifado':
        return redirect(url_for('solicitante'))
    
    relatorio = None
    relatorio_titulo = None
    tipo_relatorio = None

    if request.method == 'POST':
        tipo_relatorio = request.form['tipo_relatorio']

        conexao = conectar_banco_dados()
        cursor = conexao.cursor(dictionary=True)

        try:
            if tipo_relatorio == 'estoque':
                cursor.execute("SELECT m.descricao as Material, SUM(e.quantidade) as Quantidade "
                               "FROM materials m "
                               "LEFT JOIN estoque e ON m.id = e.material_id "
                               "GROUP BY m.id")
                relatorio = cursor.fetchall()
                relatorio_titulo = "Relatório de Estoque"

            elif tipo_relatorio == 'movimentacao':
                cursor.execute("SELECT e.data_movimentacao as Data, m.descricao as Material, e.tipo_movimentacao as Tipo, e.quantidade as Quantidade, u.nome as Usuário "
                               "FROM estoque e "
                               "JOIN materials m ON e.material_id = m.id "
                               "JOIN users u ON e.usuario_id = u.id")
                relatorio = cursor.fetchall()
                relatorio_titulo = "Relatório de Movimentação"

        except mysql.connector.Error as err:
            print(f"Erro ao gerar relatório: {err}")

        finally:
            cursor.close()
            conexao.close()

    return render_template('funcoes/relatorio.html', relatorio=relatorio, relatorio_titulo=relatorio_titulo, tipo_relatorio=tipo_relatorio)


@app.route('/perfil')
def perfil():
    return render_template('funcoes/perfil.html')

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
