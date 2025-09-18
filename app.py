from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import os
import uuid
import mysql.connector
import datetime
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, 
            static_folder='.', 
            static_url_path='',
            template_folder='.')

app.secret_key = 'vetbooking_secret_key'

# Configuração do banco de dados MySQL
def get_db_connection():
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='usuario',
        database='vetbooking'
    )
    return conn

# Inicialização do banco de dados
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    with open('bdVetBooking.sql') as f:
        sql_script = f.read()
        # Dividir o script em comandos individuais
        commands = sql_script.split(';')
        for command in commands:
            if command.strip():
                cursor.execute(command + ';')
    conn.commit()
    cursor.close()
    conn.close()

# Rotas para as páginas
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/check_login')
def check_login():
    from flask import jsonify
    if 'user_id' in session:
        return jsonify({
            'logged_in': True,
            'user_name': session.get('user_name', 'Usuário'),
            'user_type': session.get('user_type', '')
        })
    else:
        return jsonify({
            'logged_in': False
        })

@app.route('/pages/login.html')
def login_page():
    return render_template('pages/login.html')

@app.route('/pages/login-new.html')
def login_new_page():
    return render_template('pages/login-new.html')

@app.route('/cadastro')
def cadastro():
    return render_template('cadastro.html')
# Rota para gerenciar pets
@app.route('/gerenciar-pets')
def gerenciar_pets():
    if 'user_id' not in session or session['user_type'] != 'tutor':
        flash('Acesso não autorizado')
        return redirect(url_for('login_page'))
    
    user_id = session['user_id']
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Buscar pets do tutor
    cursor.execute('SELECT * FROM pets WHERE tutor_id = %s', (user_id,))
    pets = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('pages/gerenciar-pets.html', pets=pets)


# Configurações para upload de imagens
UPLOAD_FOLDER = 'static/uploads/pets'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

# Certifique-se de que a pasta de uploads existe
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



# Rota para adicionar pet
@app.route('/adicionar-pet', methods=['POST'])
def adicionar_pet():

    if 'user_id' not in session or session['user_type'] != 'tutor':
        return jsonify({'success': False, 'message': 'Acesso não autorizado'}), 403
    
    tutor_id = session['user_id']
    nome_pet = request.form['nome_pet']
    especie = request.form['especie']
    raca = request.form.get('raca', '')
    data_nascimento = request.form.get('data_nascimento')
    sexo = request.form.get('sexo', '')  # Corrigido para usar get()
    peso = request.form.get('peso')
    
    # Processar a foto
    foto = None
    if 'foto' in request.files:
        file = request.files['foto']
        if file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(f"{uuid.uuid4().hex}.{file.filename.rsplit('.', 1)[1].lower()}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            foto = filename

        

    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # VERIFICAÇÃO CRÍTICA: Tutor existe?
        cursor.execute('SELECT 1 FROM tutores WHERE tutor_id = %s', (tutor_id,))
        if not cursor.fetchone():
            return jsonify({
                'success': False, 
                'message': f'Tutor não encontrado (ID: {tutor_id})'
            }), 404
        
        # Inserir pet COM FOTO
        cursor.execute(
            'INSERT INTO pets (nome_pet, especie, raca, data_nascimento, sexo, peso, tutor_id, data_cadastro, foto) '
            'VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), %s)',
            (nome_pet, especie, raca, data_nascimento, sexo, peso, tutor_id, foto)  # Adicionado foto no final
        )
        conn.commit()
        return jsonify({'success': True})
    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({'success': False, 'message': str(err)}), 500
    finally:
        cursor.close()
        conn.close()

# Rota para atualizar pet
@app.route('/atualizar-pet', methods=['POST'])
def atualizar_pet():
    if 'user_id' not in session or session['user_type'] != 'tutor':
        return jsonify({'success': False, 'message': 'Acesso não autorizado'}), 403
    
    pet_id = request.form['pet_id']
    tutor_id = session['user_id']
    nome_pet = request.form['nome_pet']
    especie = request.form['especie']
    raca = request.form.get('raca', '')
    data_nascimento = request.form.get('data_nascimento')
    sexo = request.form.get('sexo', '')  # Corrigido para usar get()
    peso = request.form.get('peso')
    
    # Processar a foto
    foto = None
    if 'foto' in request.files:
        file = request.files['foto']
        if file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(f"{uuid.uuid4().hex}.{file.filename.rsplit('.', 1)[1].lower()}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            foto = filename

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)  # Usar dictionary=True
    
    try:
        # Verificar se o pet pertence ao tutor
        cursor.execute('SELECT tutor_id, foto as old_foto FROM pets WHERE pet_id = %s', (pet_id,))
        pet = cursor.fetchone()
        
        if not pet or pet['tutor_id'] != tutor_id:
            return jsonify({'success': False, 'message': 'Pet não encontrado ou não pertence ao tutor'}), 404
        
        # Manter foto antiga se nova não foi enviada
        if foto is None:
            foto = pet['old_foto']
        
        # Atualizar COM FOTO
        cursor.execute(
            'UPDATE pets SET nome_pet = %s, especie = %s, raca = %s, data_nascimento = %s, sexo = %s, peso = %s, foto = %s '
            'WHERE pet_id = %s',
            (nome_pet, especie, raca, data_nascimento, sexo, peso, foto, pet_id)  # Adicionado foto
        )
        conn.commit()
        return jsonify({'success': True})
    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({'success': False, 'message': str(err)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/agendar-consulta')
def agendar_consulta_page():
    if 'user_id' not in session or session['user_type'] != 'tutor':
        flash('Você precisa estar logado como tutor para agendar uma consulta')
        return redirect(url_for('login_page'))
    
    tutor_id = session['user_id']
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Buscar pets do tutor
    cursor.execute('SELECT * FROM pets WHERE tutor_id = %s', (tutor_id,))
    pets = cursor.fetchall()
    
    # Buscar clínicas disponíveis
    cursor.execute('SELECT * FROM clinicas')
    clinicas = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    # Data de hoje no formato YYYY-MM-DD
    hoje = datetime.date.today().isoformat()
    
    # Gerar horários disponíveis (9:00 às 18:00, a cada 30 minutos)
    horas_disponiveis = []
    for hora in range(9, 19):
        for minuto in [0, 30]:
            horas_disponiveis.append(f"{hora:02d}:{minuto:02d}")
    
    return render_template('pages/agendar-consulta.html', 
                           pets=pets, 
                           clinicas=clinicas,
                           hoje=hoje,
                           horas_disponiveis=horas_disponiveis)

# Rota para buscar profissionais de uma clínica
@app.route('/get-profissionais-da-clinica/<int:clinica_id>')
def get_profissionais_da_clinica(clinica_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute(
        'SELECT p.profissional_id, p.nome_profissional '
        'FROM profissionais p '
        'JOIN profissionais_clinicas pc ON p.profissional_id = pc.profissional_id '
        'WHERE pc.clinica_id = %s',
        (clinica_id,)
    )
    profissionais = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return jsonify(profissionais)

# Rota para salvar o agendamento
@app.route('/salvar-agendamento', methods=['POST'])
def salvar_agendamento():
    if 'user_id' not in session or session['user_type'] != 'tutor':
        return jsonify({'success': False, 'message': 'Acesso não autorizado'}), 403
    
    tutor_id = session['user_id']
    pet_id = request.form['pet_id']
    clinica_id = request.form['clinica_id']
    profissional_id = request.form.get('profissional_id', None)
    data_consulta = request.form['data_consulta']
    hora_consulta = request.form['hora_consulta']
    observacoes = request.form.get('observacoes', '')
    
    # Combinar data e hora
    data_hora = f"{data_consulta} {hora_consulta}:00"
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Verificar se o pet pertence ao tutor
        cursor.execute('SELECT tutor_id FROM pets WHERE pet_id = %s', (pet_id,))
        pet = cursor.fetchone()
        if not pet or pet[0] != tutor_id:
            return jsonify({'success': False, 'message': 'Pet não encontrado ou não pertence ao tutor'}), 404
        
        # Inserir agendamento
        cursor.execute(
            'INSERT INTO agendamentos (data_hora, pet_id, profissional_id, clinica_id, status, observacoes, data_cadastro) '
            'VALUES (%s, %s, %s, %s, "agendado", %s, NOW())',
            (data_hora, pet_id, profissional_id, clinica_id, observacoes)
        )
        conn.commit()
        return jsonify({'success': True, 'message': 'Consulta agendada com sucesso!'})
    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({'success': False, 'message': str(err)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Verificar em todas as tabelas de usuários
    # Tutor
    cursor.execute('SELECT * FROM tutores WHERE email = %s', (email,))
    tutor = cursor.fetchone()
    if tutor and check_password_hash(tutor['senha'], password):
        session['user_id'] = tutor['tutor_id']
        session['user_type'] = 'tutor'
        session['user_name'] = tutor['nome_tutores']
        cursor.close()
        conn.close()
        return redirect(url_for('dashboard'))
    

    
    # Clínica
    cursor.execute('SELECT * FROM clinicas WHERE email = %s', (email,))
    clinica = cursor.fetchone()
    if clinica and check_password_hash(clinica['senha'], password):
        session['user_id'] = clinica['clinica_id']
        session['user_type'] = 'clinica'
        session['user_name'] = clinica['razao_social']
        cursor.close()
        conn.close()
        return redirect(url_for('dashboard'))
    
    conn.close()
    flash('Email ou senha incorretos')
    return redirect(url_for('login_page'))

@app.route('/dashboard')
def dashboard():
    # Verificar se o usuário está logado
    if 'user_id' not in session:
        flash('Você precisa estar logado para acessar esta página')
        return redirect(url_for('login_page'))
    
    user_id = session['user_id']
    user_type = session['user_type']
    user_name = session['user_name']
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Dados comuns para todos os tipos de usuário
    data = {
        'user_name': user_name,
        'user_type': user_type,
        'user_since': datetime.datetime.now().strftime('%d/%m/%Y'),  # Placeholder, será substituído pelo dado real
        'activities': [],  # Lista vazia por padrão
    }
    
    # Definir o texto de exibição do tipo de usuário
    if user_type == 'tutor':
        data['user_type_display'] = 'Tutor de Pet'
        
        # Buscar dados específicos para tutores
        cursor.execute('SELECT * FROM tutores WHERE tutor_id = %s', (user_id,))
        tutor = cursor.fetchone()
        if tutor:
            data['user_since'] = datetime.datetime.strptime(str(tutor['data_cadastro']), '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')
        
        # Contar pets do tutor
        cursor.execute('SELECT COUNT(*) as count FROM pets WHERE tutor_id = %s', (user_id,))
        pets = cursor.fetchone()
        data['pets_count'] = pets['count'] if pets else 0
        
   
        proximas_consultas = cursor.fetchall()
        data['proximas_consultas'] = proximas_consultas
        # Contar favoritos do tutor
        cursor.execute('SELECT COUNT(*) as count FROM favoritos WHERE tutor_id = %s', (user_id,))
        favoritos = cursor.fetchone()
        data['favoritos_count'] = favoritos['count'] if favoritos else 0
        
        # Buscar atividades recentes (últimos agendamentos)
        cursor.execute(
            'SELECT a.data_hora, m.nome_medico as medico_nome, p.nome_pet as pet_nome '
            'FROM agendamentos a '
            'JOIN pets p ON a.pet_id = p.pet_id '
            'JOIN medicos m ON a.medico_id = m.medico_id '
            'WHERE p.tutor_id = %s '
            'ORDER BY a.data_cadastro DESC LIMIT 5', 
            (user_id,)
        )
        recent_activities = cursor.fetchall()
        
        for activity in recent_activities:
            data['activities'].append({
                'icon': 'fas fa-calendar-check',
                'text': f'Consulta agendada para {activity["pet_nome"]} com Dr(a). {activity["medico_nome"]}',
                'date': datetime.datetime.strptime(activity['data_hora'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M')
            })
    
    elif user_type == 'medico':
        data['user_type_display'] = 'Médico Veterinário'
        
        # Buscar dados específicos para médicos
        cursor.execute('SELECT * FROM medicos WHERE medico_id = %s', (user_id,))
        medico = cursor.fetchone()
        if medico:
            data['user_since'] = datetime.datetime.strptime(str(medico['data_cadastro']), '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')
        
        # Contar agendamentos do médico
        cursor.execute(
            'SELECT COUNT(*) as count FROM agendamentos WHERE medico_id = %s AND status = "agendado"', 
            (user_id,)
        )
        agendamentos = cursor.fetchone()
        data['agendamentos_count'] = agendamentos['count'] if agendamentos else 0
        
        # Contar pacientes únicos do médico
        cursor.execute(
            'SELECT COUNT(DISTINCT pet_id) as count FROM agendamentos WHERE medico_id = %s', 
            (user_id,)
        )
        pacientes = cursor.fetchone()
        data['pacientes_count'] = pacientes['count'] if pacientes else 0
        
        # Contar clínicas associadas ao médico
        cursor.execute(
            'SELECT COUNT(*) as count FROM medicos_clinicas WHERE medico_id = %s', 
            (user_id,)
        )
        clinicas = cursor.fetchone()
        data['clinicas_count'] = clinicas['count'] if clinicas else 0
        
        # Buscar atividades recentes (últimos agendamentos)
        cursor.execute(
            'SELECT a.data_hora, p.nome_pet as pet_nome, t.nome_tutores as tutor_nome '
            'FROM agendamentos a '
            'JOIN pets p ON a.pet_id = p.pet_id '
            'JOIN tutores t ON p.tutor_id = t.tutor_id '
            'WHERE a.medico_id = %s '
            'ORDER BY a.data_cadastro DESC LIMIT 5', 
            (user_id,)
        )
        recent_activities = cursor.fetchall()
        
        for activity in recent_activities:
            data['activities'].append({
                'icon': 'fas fa-calendar-check',
                'text': f'Consulta agendada para {activity["pet_nome"]} do tutor {activity["tutor_nome"]}',
                'date': datetime.datetime.strptime(activity['data_hora'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M')
            })
    
    elif user_type == 'clinica':
        data['user_type_display'] = 'Clínica Veterinária'
        
        # Buscar dados específicos para clínicas
        cursor.execute('SELECT * FROM clinicas WHERE clinica_id = %s', (user_id,))
        clinica = cursor.fetchone()
        if clinica:
            data['user_since'] = datetime.datetime.strptime(str(clinica['data_cadastro']), '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')
        
        # Contar agendamentos da clínica
        cursor.execute(
            'SELECT COUNT(*) as count FROM agendamentos WHERE clinica_id = %s AND status = "agendado"', 
            (user_id,)
        )
        agendamentos = cursor.fetchone()
        data['agendamentos_count'] = agendamentos['count'] if agendamentos else 0
        
        # Contar médicos associados à clínica
        cursor.execute(
            'SELECT COUNT(*) as count FROM medicos_clinicas WHERE clinica_id = %s', 
            (user_id,)
        )
        medicos = cursor.fetchone()
        data['medicos_count'] = medicos['count'] if medicos else 0
        
        # Buscar atividades recentes (últimos agendamentos)
        cursor.execute(
            'SELECT a.data_hora, p.nome_pet as pet_nome, m.nome_medico as medico_nome '
            'FROM agendamentos a '
            'JOIN pets p ON a.pet_id = p.pet_id '
            'JOIN medicos m ON a.medico_id = m.medico_id '
            'WHERE a.clinica_id = %s '
            'ORDER BY a.data_cadastro DESC LIMIT 5', 
            (user_id,)
        )
        recent_activities = cursor.fetchall()
        
        for activity in recent_activities:
            data['activities'].append({
                'icon': 'fas fa-calendar-check',
                'text': f'Consulta agendada com Dr(a). {activity["medico_nome"]} para {activity["pet_nome"]}',
                'date': datetime.datetime.strptime(activity['data_hora'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M')
            })
    
    cursor.close()
    conn.close()
    return render_template('pages/dashboard.html', **data)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/editar-perfil.html')
def editar_perfil_page():
    # Verificar se o usuário está logado
    if 'user_id' not in session:
        flash('Você precisa estar logado para acessar esta página')
        return redirect(url_for('login_page'))
    
    user_id = session['user_id']
    user_type = session['user_type']
    user_name = session['user_name']
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Dados comuns para todos os tipos de usuário
    data = {
        'user_name': user_name,
        'user_type': user_type,
        'user_since': datetime.datetime.now().strftime('%d/%m/%Y'),  # Placeholder, será substituído pelo dado real
    }
    
    # Definir o texto de exibição do tipo de usuário
    if user_type == 'tutor':
        data['user_type_display'] = 'Tutor de Pet'
        
        # Buscar dados específicos para tutores
        cursor.execute('SELECT t.*, e.endereco, e.cep FROM tutores t LEFT JOIN endereco e ON t.endereco_id = e.id_endereco WHERE t.tutor_id = %s', (user_id,))
        tutor = cursor.fetchone()
        if tutor:
            if tutor['data_cadastro']:
                data['user_since'] = datetime.datetime.strptime(str(tutor['data_cadastro']), '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')
            data['tutor'] = dict(tutor)
    
    elif user_type == 'medico':
        data['user_type_display'] = 'Médico Veterinário'
        
        # Buscar dados específicos para médicos
        cursor.execute('SELECT * FROM medicos WHERE medico_id = %s', (user_id,))
        medico = cursor.fetchone()
        if medico:
            data['user_since'] = datetime.datetime.strptime(str(medico['data_cadastro']), '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')
            data['medico'] = dict(medico)
    
    elif user_type == 'clinica':
        data['user_type_display'] = 'Clínica Veterinária'
        
        # Buscar dados específicos para clínicas
        cursor.execute('SELECT * FROM clinicas WHERE clinica_id = %s', (user_id,))
        clinica = cursor.fetchone()
        if clinica:
            data['user_since'] = datetime.datetime.strptime(str(clinica['data_cadastro']), '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')
            data['clinica'] = dict(clinica)
    
    cursor.close()
    conn.close()
    return render_template('pages/editar-perfil.html', **data)

@app.route('/pages/cadastro.html')
def cadastro_page():
    return render_template('pages/cadastro.html')

@app.route('/pages/cadastro-new.html')
def cadastro_new_page():
    return render_template('pages/cadastro-new.html')

@app.route('/pages/cadastro-tutor.html')
def cadastro_tutor_page():
    return render_template('pages/cadastro-tutor-new.html')

@app.route('/pages/cadastro-tutor-new.html')
def cadastro_tutor_new_page():
    return render_template('pages/cadastro-tutor-new.html')

@app.route('/submit-tutor', methods=['POST'])
def submit_tutor():
        # Coletar todos os campos do formulário
    nome = request.form['full-name']
    email = request.form['email']
    senha = request.form['password']
    endereco_rua = request.form['address']
    cep = request.form['cep']
    bairro = request.form['bairro']  # Novo campo
    telefone = request.form['phone']  # Novo campo
    cidade = request.form['city']
    uf = request.form['state']
    data_nascimento = request.form['birth-date']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Verificar se o email já existe
    cursor.execute('SELECT * FROM tutores WHERE email = %s', (email,))
    existing_user = cursor.fetchone()
    if existing_user:
        cursor.close()
        conn.close()
        flash('Email já cadastrado')
        return redirect(url_for('cadastro_tutor_page'))
    
    try:
        # 1. Obter ou criar cidade
        cursor.execute('SELECT id_cidade FROM cidade WHERE cidade = %s', (cidade,))
        cidade_row = cursor.fetchone()
        
        if not cidade_row:
            # Se a cidade não existe, criar
            cursor.execute('INSERT INTO cidade (cidade) VALUES (%s)', (cidade,))
            id_cidade = cursor.lastrowid
        else:
            id_cidade = cidade_row['id_cidade']
        
        # 2. Inserir endereço
        cursor.execute(
            'INSERT INTO endereco (endereco, cep, telefone, bairro, id_cidade) '
            'VALUES (%s, %s, %s, %s, %s)',
            (endereco_rua, cep, telefone, bairro, id_cidade)
        )
        endereco_id = cursor.lastrowid
        
        # 3. Inserir tutor
        data_cadastro = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        senha_hash = generate_password_hash(senha)
        
        cursor.execute(
            'INSERT INTO tutores (nome_tutores, email, senha, data_nascimento, data_cadastro, endereco_id) '
            'VALUES (%s, %s, %s, %s, %s, %s)',
            (nome, email, senha_hash, data_nascimento, data_cadastro, endereco_id)
        )
        
        conn.commit()
        flash('Cadastro realizado com sucesso!')
    
        
        conn.commit()
        flash('Cadastro realizado com sucesso!')
    except mysql.connector.Error as err:
        conn.rollback()
        flash(f'Erro ao cadastrar: {err}')
    except Exception as e:
        conn.rollback()
        flash(f'Erro inesperado: {str(e)}')
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('login_page'))

@app.route('/pages/cadastro-MV.html')
def cadastro_mv_page():
    return render_template('pages/cadastro-MV.html')

@app.route('/pages/cadastro-MV-new.html')
def cadastro_mv_new_page():
    return render_template('pages/cadastro-MV-new.html')

@app.route('/submit-MV', methods=['POST'])
def submit_mv():
    nome = request.form['full-name']
    email = request.form['email']
    crmv = request.form['CRMV']
    uf = request.form['state']
    senha = generate_password_hash(request.form['password'])
    
    # Obter outros campos do formulário
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Verificar se o email já existe
    cursor.execute('SELECT * FROM medicos WHERE email = %s', (email,))
    existing_user = cursor.fetchone()
    if existing_user:
        cursor.close()
        conn.close()
        flash('Email já cadastrado')
        return redirect(url_for('cadastro_mv_page'))
    
    # Inserir no banco de dados (ajustar conforme os campos do formulário)
    data_cadastro = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('INSERT INTO medicos (nome_medico, email, crmv, uf, senha, data_cadastro) VALUES (%s, %s, %s, %s, %s, %s)',
                (nome, email, crmv, uf, senha, data_cadastro))
    conn.commit()
    cursor.close()
    conn.close()
    
    flash('Cadastro realizado com sucesso!')
    return redirect(url_for('login_page'))

@app.route('/pages/cadastro-clinica.html')
def cadastro_clinica_page():
    return render_template('pages/cadastro-clinica.html')

@app.route('/submit-estabelecimento', methods=['POST'])
def submit_clinica():
    razao_social = request.form['full-name']
    email = request.form['email']
    senha = request.form['password']
    cep = request.form['cep']
    uf = request.form['state']
    cidade = request.form['city']
    bairro = request.form['neighborhood']  # Campo adicionado
    rua = request.form['street']           # Campo adicionado
    numero = request.form['number']        # Campo adicionado
    telefone = request.form['phone']       # Campo existente
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Verificar se o email já existe
    cursor.execute('SELECT * FROM clinicas WHERE email = %s', (email,))
    existing_user = cursor.fetchone()
    if existing_user:
        cursor.close()
        conn.close()
        flash('Email já cadastrado')
        return redirect(url_for('cadastro_clinica_page'))
    
    data_cadastro = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    senha_hash = generate_password_hash(senha)
    
    # Query atualizada com novos campos
    cursor.execute(
        'INSERT INTO clinicas (razao_social, email, senha, cep, uf, cidade, bairro, rua, numero, telefone, data_cadastro) '
        'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
        (razao_social, email, senha_hash, cep, uf, cidade, bairro, rua, numero, telefone, data_cadastro)
    )
    conn.commit()
    cursor.close()
    conn.close()
    
    flash('Cadastro realizado com sucesso!')
    return redirect(url_for('login_page'))

@app.route('/search', methods=['GET'])
def search():
    search_text = request.args.get('search-text')
    location = request.args.get('Location')
    
    # Implementar lógica de busca no banco de dados
    # Por enquanto, apenas retorna para a página inicial
    return redirect(url_for('index'))

@app.route('/atualizar-tutor', methods=['POST'])
def atualizar_tutor():
    # Verificar se o usuário está logado e é um tutor
    if 'user_id' not in session or session['user_type'] != 'tutor':
        flash('Acesso não autorizado')
        return redirect(url_for('login_page'))
    
    user_id = session['user_id']
    
    # Obter dados do formulário
    nome = request.form['nome']
    email = request.form['email']
    endereco_rua = request.form['endereco']
    cep = request.form['cep']
    data_nascimento = request.form['data_nascimento']
    senha_atual = request.form.get('senha_atual')
    nova_senha = request.form.get('nova_senha')
    confirmar_senha = request.form.get('confirmar_senha')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Verificar se o email já existe (exceto para o próprio usuário)
        cursor.execute('SELECT * FROM tutores WHERE email = %s AND tutor_id != %s', (email, user_id))
        existing_user = cursor.fetchone()
        if existing_user:
            flash('Email já cadastrado por outro usuário')
            return redirect(url_for('editar_perfil_page'))
        
        # Obter dados atuais do usuário
        cursor.execute('SELECT * FROM tutores WHERE tutor_id = %s', (user_id,))
        tutor = cursor.fetchone()
        
        # Verificar senha atual se fornecida
        if senha_atual:
            if not check_password_hash(tutor['senha'], senha_atual):
                flash('Senha atual incorreta')
                return redirect(url_for('editar_perfil_page'))
            
            # Verificar se o tutor já tem um endereço associado
            endereco_id = tutor.get('endereco_id')
            
            if endereco_id:
                # Atualizar o endereço existente
                cursor.execute(
                    'UPDATE endereco SET endereco = %s, cep = %s WHERE id_endereco = %s',
                    (endereco_rua, cep, endereco_id)
                )
            else:
                # Criar um novo endereço
                cursor.execute(
                    'INSERT INTO endereco (endereco, cep) VALUES (%s, %s)',
                    (endereco_rua, cep)
                )
                endereco_id = cursor.lastrowid
                
                # Atualizar o tutor com o novo endereco_id
                cursor.execute(
                    'UPDATE tutores SET endereco_id = %s WHERE tutor_id = %s',
                    (endereco_id, user_id)
                )
            
            # Atualizar senha se nova senha fornecida
            if nova_senha:
                if nova_senha != confirmar_senha:
                    flash('Nova senha e confirmação não coincidem')
                    return redirect(url_for('editar_perfil_page'))
                
                # Atualizar com nova senha
                cursor.execute(
                    'UPDATE tutores SET nome_tutores = %s, email = %s, data_nascimento = %s, senha = %s WHERE tutor_id = %s',
                    (nome, email, data_nascimento, generate_password_hash(nova_senha), user_id)
                )
            else:
                # Atualizar sem mudar a senha
                cursor.execute(
                    'UPDATE tutores SET nome_tutores = %s, email = %s, data_nascimento = %s WHERE tutor_id = %s',
                    (nome, email, data_nascimento, user_id)
                )
        else:
            # Não permitir atualização sem senha atual
            flash('Senha atual é necessária para fazer alterações')
            return redirect(url_for('editar_perfil_page'))
        
        conn.commit()
        # Atualizar o nome na sessão
        session['user_name'] = nome
        flash('Perfil atualizado com sucesso!')
    except mysql.connector.Error as err:
        conn.rollback()
        flash(f'Erro ao atualizar perfil: {err}')
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('dashboard'))

@app.route('/atualizar-medico', methods=['POST'])
def atualizar_medico():
    # Verificar se o usuário está logado e é um médico
    if 'user_id' not in session or session['user_type'] != 'medico':
        flash('Acesso não autorizado')
        return redirect(url_for('login_page'))
    
    user_id = session['user_id']
    
    # Obter dados do formulário
    nome = request.form['nome']
    email = request.form['email']
    crmv = request.form['crmv']
    uf = request.form['uf']
    especialidades = request.form.get('especialidades', '')
    descricao = request.form.get('descricao', '')
    foto = request.form.get('foto', '')
    senha_atual = request.form.get('senha_atual')
    nova_senha = request.form.get('nova_senha')
    confirmar_senha = request.form.get('confirmar_senha')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Verificar se o email já existe (exceto para o próprio usuário)
    cursor.execute('SELECT * FROM medicos WHERE email = %s AND medico_id != %s', (email, user_id))
    existing_user = cursor.fetchone()
    if existing_user:
        cursor.close()
        conn.close()
        flash('Email já cadastrado por outro usuário')
        return redirect(url_for('editar_perfil_page'))
    
    # Obter dados atuais do usuário
    cursor.execute('SELECT * FROM medicos WHERE medico_id = %s', (user_id,))
    medico = cursor.fetchone()
    
    # Verificar senha atual se fornecida
    if senha_atual:
        if not check_password_hash(medico['senha'], senha_atual):
            cursor.close()
            conn.close()
            flash('Senha atual incorreta')
            return redirect(url_for('editar_perfil_page'))
        
        # Atualizar senha se nova senha fornecida
        if nova_senha:
            if nova_senha != confirmar_senha:
                cursor.close()
                conn.close()
                flash('Nova senha e confirmação não coincidem')
                return redirect(url_for('editar_perfil_page'))
            
            # Atualizar com nova senha
            cursor.execute(
                'UPDATE medicos SET nome_medico = %s, email = %s, crmv = %s, uf = %s, especialidades = %s, descricao = %s, foto = %s, senha = %s WHERE medico_id = %s',
                (nome, email, crmv, uf, especialidades, descricao, foto, generate_password_hash(nova_senha), user_id)
            )
        else:
            # Atualizar sem mudar a senha
            cursor.execute(
                'UPDATE medicos SET nome_medico = %s, email = %s, crmv = %s, uf = %s, especialidades = %s, descricao = %s, foto = %s WHERE medico_id = %s',
                (nome, email, crmv, uf, especialidades, descricao, foto, user_id)
            )
    else:
        # Não permitir atualização sem senha atual
        cursor.close()
        conn.close()
        flash('Senha atual é necessária para fazer alterações')
        return redirect(url_for('editar_perfil_page'))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    # Atualizar o nome na sessão
    session['user_name'] = nome
    
    flash('Perfil atualizado com sucesso!')
    return redirect(url_for('dashboard'))

@app.route('/atualizar-clinica', methods=['POST'])
def atualizar_clinica():
    # Verificar se o usuário está logado e é uma clínica
    if 'user_id' not in session or session['user_type'] != 'clinica':
        flash('Acesso não autorizado')
        return redirect(url_for('login_page'))
    
    user_id = session['user_id']
    
    # Obter dados do formulário
    razao_social = request.form['razao_social']
    email = request.form['email']
    cep = request.form['cep']
    uf = request.form['uf']
    cidade = request.form['cidade']
    bairro = request.form['bairro']
    rua = request.form['rua']
    numero = request.form['numero']
    complemento = request.form.get('complemento', '')
    telefone = request.form.get('telefone', '')
    horario_funcionamento = request.form.get('horario_funcionamento', '')
    senha_atual = request.form.get('senha_atual')
    nova_senha = request.form.get('nova_senha')
    confirmar_senha = request.form.get('confirmar_senha')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Verificar se o email já existe (exceto para o próprio usuário)
    cursor.execute('SELECT * FROM clinicas WHERE email = %s AND clinica_id != %s', (email, user_id))
    existing_user = cursor.fetchone()
    if existing_user:
        cursor.close()
        conn.close()
        flash('Email já cadastrado por outro usuário')
        return redirect(url_for('editar_perfil_page'))
    
    # Obter dados atuais do usuário
    cursor.execute('SELECT * FROM clinicas WHERE clinica_id = %s', (user_id,))
    clinica = cursor.fetchone()
    
    # Verificar senha atual se fornecida
    if senha_atual:
        if not check_password_hash(clinica['senha'], senha_atual):
            cursor.close()
            conn.close()
            flash('Senha atual incorreta')
            return redirect(url_for('editar_perfil_page'))
        
        # Atualizar senha se nova senha fornecida
        if nova_senha:
            if nova_senha != confirmar_senha:
                cursor.close()
                conn.close()
                flash('Nova senha e confirmação não coincidem')
                return redirect(url_for('editar_perfil_page'))
            
            # Atualizar com nova senha
            cursor.execute(
                'UPDATE clinicas SET razao_social = %s, email = %s, cep = %s, uf = %s, cidade = %s, bairro = %s, rua = %s, numero = %s, complemento = %s, telefone = %s, horario_funcionamento = %s, senha = %s WHERE clinica_id = %s',
                (razao_social, email, cep, uf, cidade, bairro, rua, numero, complemento, telefone, horario_funcionamento, generate_password_hash(nova_senha), user_id)
            )
        else:
            # Atualizar sem mudar a senha
            cursor.execute(
                'UPDATE clinicas SET razao_social = %s, email = %s, cep = %s, uf = %s, cidade = %s, bairro = %s, rua = %s, numero = %s, complemento = %s, telefone = %s, horario_funcionamento = %s WHERE clinica_id = %s',
                (razao_social, email, cep, uf, cidade, bairro, rua, numero, complemento, telefone, horario_funcionamento, user_id)
            )
    else:
        # Não permitir atualização sem senha atual
        cursor.close()
        conn.close()
        flash('Senha atual é necessária para fazer alterações')
        return redirect(url_for('editar_perfil_page'))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    # Atualizar o nome na sessão
    session['user_name'] = razao_social
    
    flash('Perfil atualizado com sucesso!')
    return redirect(url_for('dashboard'))




@app.route('/api/veterinarios')
def api_veterinarios():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM medicos')
    medicos = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(medicos)

@app.route('/api/clinicas')
def api_clinicas():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM clinicas')
    clinicas = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(clinicas)

# Rota para página de cadastro de veterinários
@app.route('/cadastro-veterinario')
def cadastro_veterinario_page():
    return render_template('pages/cadastro-veterinario.html')

# Rota para processar cadastro de veterinário
@app.route('/submit-veterinario', methods=['POST'])
def submit_veterinario():
    # Coletar dados do formulário
    nome = request.form['nome']
    email = request.form['email']
    cpf = request.form['cpf']
    crmv = request.form['crmv']
    uf = request.form['uf']
    telefone = request.form['telefone']
    data_nascimento = request.form['data_nascimento']
    senha = request.form['senha']
    especialidades = request.form.getlist('especialidades[]')
    descricao = request.form.get('descricao', '')
    
    # Processar upload de documentos
    documentos = []
    if 'documentos' in request.files:
        files = request.files.getlist('documentos')
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(f"{uuid.uuid4().hex}_{file.filename}")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                documentos.append(filename)
    
    # Processar upload de foto de perfil
    foto = None
    if 'foto' in request.files:
        file = request.files['foto']
        if file and allowed_file(file.filename):
            filename = secure_filename(f"{uuid.uuid4().hex}_{file.filename}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            foto = filename
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Verificar se o email já existe
        cursor.execute('SELECT * FROM medicos WHERE email = %s', (email,))
        existing_user = cursor.fetchone()
        if existing_user:
            return jsonify({'success': False, 'message': 'Email já cadastrado'}), 400
        
        # Verificar se o CRMV já existe
        cursor.execute('SELECT * FROM medicos WHERE crmv = %s', (crmv,))
        existing_crmv = cursor.fetchone()
        if existing_crmv:
            return jsonify({'success': False, 'message': 'CRMV já cadastrado'}), 400
        
        # Inserir veterinário no banco de dados
        data_cadastro = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        senha_hash = generate_password_hash(senha)
        especialidades_str = ','.join(especialidades) if especialidades else ''
        documentos_str = ','.join(documentos) if documentos else ''
        
        cursor.execute(
            'INSERT INTO medicos (nome_medico, email, cpf, crmv, uf, telefone, data_nascimento, senha, especialidades, descricao, foto, documentos, data_cadastro, status) '
            'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
            (nome, email, cpf, crmv, uf, telefone, data_nascimento, senha_hash, especialidades_str, descricao, foto, documentos_str, data_cadastro, 'pendente')
        )
        
        medico_id = cursor.lastrowid
        conn.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Cadastro realizado com sucesso! Seu perfil será analisado e ativado em breve.',
            'medico_id': medico_id
        })
        
    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({'success': False, 'message': f'Erro ao cadastrar: {str(err)}'}), 500
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
 app.run(debug=True)
