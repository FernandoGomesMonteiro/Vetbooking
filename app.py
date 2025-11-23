from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import os
import uuid
import mysql.connector
import datetime
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__, 
            static_folder='.', 
            static_url_path='',
            template_folder='.')

app.secret_key = 'vetbooking_secret_key'

# --- CONFIGURAÇÕES DE UPLOAD ---
UPLOAD_FOLDER = 'static/uploads/pets'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

# Garantir que pastas existem
os.makedirs('static/uploads/pets', exist_ok=True)
os.makedirs('static/uploads/medicos', exist_ok=True) # Alterado para 'medicos'
os.makedirs('static/uploads/documentos', exist_ok=True)

# --- BANCO DE DADOS ---

def get_db_connection():
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='usuario',
        database='vetbooking'
    )
    return conn

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- LOGIN E AUTENTICAÇÃO ---

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Você precisa estar logado para acessar esta página')
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated

@app.route('/check_login')
def check_login():
    if 'user_id' in session:
        return jsonify({
            'logged_in': True,
            'user_name': session.get('user_name', 'Usuário'),
            'user_type': session.get('user_type', '')
        })
    else:
        return jsonify({'logged_in': False})

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # 1. Verificar Tabela TUTORES
        cursor.execute('SELECT * FROM tutores WHERE email = %s', (email,))
        tutor = cursor.fetchone()
        if tutor and check_password_hash(tutor['senha'], password):
            session['user_id'] = tutor['tutor_id']
            session['user_type'] = 'tutor'
            session['user_name'] = tutor['nome_tutores']
            return redirect(url_for('dashboard'))
        
        # 2. Verificar Tabela MEDICOS
        cursor.execute('SELECT * FROM medicos WHERE email = %s', (email,))
        medico = cursor.fetchone()
        if medico and check_password_hash(medico['senha'], password):
            session['user_id'] = medico['medico_id']
            session['user_type'] = 'medico'
            session['user_name'] = medico['nome_medico']
            return redirect(url_for('dashboard'))

        # 3. Verificar Tabela CLINICAS
        cursor.execute('SELECT * FROM clinicas WHERE email = %s', (email,))
        clinica = cursor.fetchone()
        if clinica and check_password_hash(clinica['senha'], password):
            session['user_id'] = clinica['clinica_id']
            session['user_type'] = 'clinica'
            session['user_name'] = clinica['razao_social']
            return redirect(url_for('dashboard'))
        
        flash('Email ou senha incorretos')
        return redirect(url_for('login_page'))
        
    finally:
        cursor.close()
        conn.close()

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# --- ROTAS DE PÁGINAS ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/pages/login.html')
def login_page():
    return render_template('pages/login.html')

@app.route('/pages/login-new.html')
def login_new_page():
    return render_template('pages/login-new.html')

@app.route('/cadastro')
def cadastro():
    return render_template('cadastro.html')

@app.route('/pages/cadastro.html')
def cadastro_page():
    return render_template('pages/cadastro.html')

@app.route('/pages/cadastro-tutor-new.html')
def cadastro_tutor_new_page():
    return render_template('pages/cadastro-tutor-new.html')

@app.route('/pages/cadastro-clinica.html')
def cadastro_clinica_page():
    return render_template('pages/cadastro-clinica.html')

@app.route('/pages/cadastro-MV-new.html')
def cadastro_mv_new_page():
    return render_template('pages/cadastro-MV-new.html')

# --- DASHBOARD ---

@app.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user_id']
    user_type = session['user_type']
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    data = {
        'user_name': session['user_name'],
        'user_type': user_type,
        'user_since': datetime.datetime.now().strftime('%d/%m/%Y'),
        'activities': [],
        'proximas_consultas': []
    }
    
    try:
        if user_type == 'tutor':
            data['user_type_display'] = 'Tutor de Pet'
            cursor.execute('SELECT data_cadastro FROM tutores WHERE tutor_id = %s', (user_id,))
            res = cursor.fetchone()
            if res and res['data_cadastro']: 
                data['user_since'] = res['data_cadastro'].strftime('%d/%m/%Y')

            # Contar pets
            cursor.execute('SELECT COUNT(*) as count FROM pets WHERE tutor_id = %s', (user_id,))
            data['pets_count'] = cursor.fetchone()['count']
            
            # Buscar próximas consultas (tabela agendamentos)
            cursor.execute('''
                SELECT a.data_hora, c.razao_social as clinica_nome, p.nome_pet, m.nome_medico
                FROM agendamentos a
                JOIN clinicas c ON a.clinica_id = c.clinica_id
                JOIN pets p ON a.pet_id = p.pet_id
                LEFT JOIN medicos m ON a.medico_id = m.medico_id
                WHERE p.tutor_id = %s AND a.status = 'agendado'
                ORDER BY a.data_hora ASC LIMIT 5
            ''', (user_id,))
            data['proximas_consultas'] = cursor.fetchall()

        elif user_type == 'medico':
            data['user_type_display'] = 'Médico Veterinário'
            cursor.execute('SELECT data_cadastro FROM medicos WHERE medico_id = %s', (user_id,))
            res = cursor.fetchone()
            if res and res['data_cadastro']:
                 data['user_since'] = res['data_cadastro'].strftime('%d/%m/%Y')

            # Contar agendamentos
            cursor.execute('SELECT COUNT(*) as count FROM agendamentos WHERE medico_id = %s AND status = "agendado"', (user_id,))
            data['agendamentos_count'] = cursor.fetchone()['count']
            
            # Consultas do médico
            cursor.execute('''
                SELECT a.data_hora, p.nome_pet, t.nome_tutores
                FROM agendamentos a
                JOIN pets p ON a.pet_id = p.pet_id
                JOIN tutores t ON p.tutor_id = t.tutor_id
                WHERE a.medico_id = %s AND a.status = 'agendado'
                ORDER BY a.data_hora ASC LIMIT 5
            ''', (user_id,))
            consultas = cursor.fetchall()
            for c in consultas:
                data['activities'].append({
                    'text': f"Atendimento: {c['nome_pet']} (Tutor: {c['nome_tutores']})",
                    'date': c['data_hora'].strftime('%d/%m/%Y %H:%M')
                })

        elif user_type == 'clinica':
            data['user_type_display'] = 'Clínica Veterinária'
            cursor.execute('SELECT data_cadastro FROM clinicas WHERE clinica_id = %s', (user_id,))
            res = cursor.fetchone()
            if res and res['data_cadastro']:
                data['user_since'] = res['data_cadastro'].strftime('%d/%m/%Y')

            # Agendamentos da clínica
            cursor.execute('SELECT COUNT(*) as count FROM agendamentos WHERE clinica_id = %s AND status = "agendado"', (user_id,))
            data['agendamentos_count'] = cursor.fetchone()['count']

            # Médicos associados (Via tabela medicos_clinicas)
            cursor.execute('SELECT COUNT(*) as count FROM medicos_clinicas WHERE clinica_id = %s', (user_id,))
            medicos = cursor.fetchone()
            data['medicos_count'] = medicos['count'] if medicos else 0

    except Exception as e:
        print(f"Erro dashboard: {e}")
    finally:
        cursor.close()
        conn.close()
    
    return render_template('pages/dashboard.html', **data)

# --- CADASTROS ---

@app.route('/submit-tutor', methods=['POST'])
def submit_tutor():
    try:
        nome = request.form['full-name']
        email = request.form['email']
        senha = request.form['password']
        # Campos opcionais para endereço
        endereco = request.form.get('address')
        cep = request.form.get('cep')
        telefone = request.form.get('phone')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar email duplicado
        cursor.execute('SELECT 1 FROM tutores WHERE email = %s', (email,))
        if cursor.fetchone():
            flash('Email já cadastrado')
            return redirect(url_for('cadastro_tutor_new_page'))

        # Lógica de Endereço (se fornecido)
        endereco_id = None
        if endereco:
            cursor.execute(
                'INSERT INTO endereco (endereco, cep, telefone) VALUES (%s, %s, %s)',
                (endereco, cep, telefone)
            )
            endereco_id = cursor.lastrowid
        
        senha_hash = generate_password_hash(senha)
        
        # Inserir Tutor
        cursor.execute(
            'INSERT INTO tutores (nome_tutores, email, senha, endereco_id, data_cadastro) VALUES (%s, %s, %s, %s, NOW())',
            (nome, email, senha_hash, endereco_id)
        )
        conn.commit()
        flash('Cadastro realizado com sucesso!')
        return redirect(url_for('login_page'))
    
    except Exception as e:
        if conn: conn.rollback()
        flash(f'Erro: {str(e)}')
        return redirect(url_for('cadastro_tutor_new_page'))
    finally:
        if conn: conn.close()

@app.route('/submit-estabelecimento', methods=['POST'])
def submit_clinica():
    try:
        razao = request.form['full-name']
        email = request.form['email']
        senha = request.form['password']
        cep = request.form.get('cep')
        uf = request.form.get('state')
        cidade = request.form.get('city')
        telefone = request.form.get('phone')

        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT 1 FROM clinicas WHERE email = %s', (email,))
        if cursor.fetchone():
            flash('Email já cadastrado')
            return redirect(url_for('cadastro_clinica_page'))
            
        senha_hash = generate_password_hash(senha)
        
        cursor.execute(
            'INSERT INTO clinicas (razao_social, email, senha, cep, uf, cidade, telefone, data_cadastro) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())',
            (razao, email, senha_hash, cep, uf, cidade, telefone)
        )
        conn.commit()
        flash('Clínica cadastrada!')
        return redirect(url_for('login_page'))
    except Exception as e:
        flash(f'Erro: {e}')
        return redirect(url_for('cadastro_clinica_page'))
    finally:
        if conn: conn.close()

# Rota para página de cadastro de médico (pode ser acessada pelo dashboard da clínica)
@app.route('/pages/cadastro-veterinario.html')
def cadastro_veterinario_page():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT clinica_id, razao_social FROM clinicas')
    clinicas = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('pages/cadastro-veterinario.html', clinicas=clinicas)

@app.route('/cadastrar-veterinario', methods=['POST'])
def cadastrar_veterinario():
    conn = None
    try:
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        crmv = request.form['crmv']
        uf = request.form.get('uf_crmv')
        clinica_id = request.form.get('clinica_id')
        especialidades = request.form.getlist('especialidades[]')
        descricao = request.form.get('descricao', '')
        
        especialidades_str = ','.join(especialidades)
        senha_hash = generate_password_hash(senha)
        
        # Upload Foto
        foto = None
        if 'foto' in request.files:
            f = request.files['foto']
            if f and allowed_file(f.filename):
                foto = secure_filename(f"med_{uuid.uuid4().hex}.{f.filename.rsplit('.',1)[1]}")
                f.save(os.path.join('static/uploads/medicos', foto))

        conn = get_db_connection()
        cursor = conn.cursor()

        # Verifica email na tabela medicos
        cursor.execute('SELECT 1 FROM medicos WHERE email = %s', (email,))
        if cursor.fetchone(): 
            return jsonify({'success': False, 'message': 'Email já cadastrado'})

        # Inserir na tabela MEDICOS
        cursor.execute(
            'INSERT INTO medicos (nome_medico, email, senha, crmv, uf, especialidades, descricao, foto, data_cadastro) '
            'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())',
            (nome, email, senha_hash, crmv, uf, especialidades_str, descricao, foto)
        )
        medico_id = cursor.lastrowid
        
        # Vincular à Clínica na tabela MEDICOS_CLINICAS
        if clinica_id:
            cursor.execute(
                'INSERT INTO medicos_clinicas (medico_id, clinica_id, data_cadastro) VALUES (%s, %s, NOW())',
                (medico_id, clinica_id)
            )
        
        conn.commit()
        return jsonify({'success': True, 'message': 'Médico cadastrado com sucesso!', 'redirect': url_for('login_page')})

    except Exception as e:
        if conn: conn.rollback()
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'})
    finally:
        if conn: conn.close()

# --- GESTÃO DE PETS ---

@app.route('/gerenciar-pets')
@login_required
def gerenciar_pets():
    if session['user_type'] != 'tutor':
        flash('Acesso restrito a tutores')
        return redirect(url_for('dashboard'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM pets WHERE tutor_id = %s', (session['user_id'],))
    pets = cursor.fetchall()
    conn.close()
    return render_template('pages/gerenciar-pets.html', pets=pets)

@app.route('/adicionar-pet', methods=['POST'])
@login_required
def adicionar_pet():
    if session['user_type'] != 'tutor':
        return jsonify({'success': False}), 403
    
    try:
        tutor_id = session['user_id']
        nome = request.form['nome_pet']
        especie = request.form['especie']
        raca = request.form.get('raca', '')
        nasc = request.form.get('data_nascimento')
        sexo = request.form.get('sexo', '')
        peso = request.form.get('peso')

        foto = None
        if 'foto' in request.files:
            f = request.files['foto']
            if f and allowed_file(f.filename):
                foto = secure_filename(f"pet_{uuid.uuid4().hex}.{f.filename.rsplit('.',1)[1]}")
                f.save(os.path.join(app.config['UPLOAD_FOLDER'], foto))

        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'INSERT INTO pets (nome_pet, especie, raca, data_nascimento, sexo, peso, tutor_id, foto, data_cadastro) '
            'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())',
            (nome, especie, raca, nasc, sexo, peso, tutor_id, foto)
        )
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if 'conn' in locals(): conn.close()

@app.route('/atualizar-pet', methods=['POST'])
@login_required
def atualizar_pet():
    pet_id = request.form['pet_id']
    nome = request.form['nome_pet']
    # Recuperar outros campos...
    especie = request.form['especie']
    raca = request.form.get('raca')
    nasc = request.form.get('data_nascimento')
    sexo = request.form.get('sexo')
    peso = request.form.get('peso')
    
    foto = None
    if 'foto' in request.files:
        f = request.files['foto']
        if f and allowed_file(f.filename):
            foto = secure_filename(f"pet_{uuid.uuid4().hex}.{f.filename.rsplit('.',1)[1]}")
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], foto))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Verifica dono
        cursor.execute('SELECT tutor_id, foto FROM pets WHERE pet_id = %s', (pet_id,))
        pet = cursor.fetchone()
        
        if not pet or pet['tutor_id'] != session['user_id']:
            return jsonify({'success': False, 'message': 'Permissão negada'}), 403
        
        if not foto: foto = pet['foto']
        
        cursor.execute(
            'UPDATE pets SET nome_pet=%s, especie=%s, raca=%s, data_nascimento=%s, sexo=%s, peso=%s, foto=%s WHERE pet_id=%s',
            (nome, especie, raca, nasc, sexo, peso, foto, pet_id)
        )
        conn.commit()
        return jsonify({'success': True})
    finally:
        conn.close()

# --- AGENDAMENTOS ---

@app.route('/agendar-consulta')
@app.route('/pages/agendar-consulta.html')
@login_required
def agendar_consulta_page():
    if session['user_type'] != 'tutor':
        flash('Faça login como tutor')
        return redirect(url_for('login_page'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute('SELECT * FROM pets WHERE tutor_id = %s', (session['user_id'],))
    pets = cursor.fetchall()
    
    cursor.execute('SELECT * FROM clinicas')
    clinicas = cursor.fetchall()
    
    horas = [f"{h:02d}:{m:02d}" for h in range(8, 19) for m in [0, 30] if not (h==18 and m==30)]
    hoje = datetime.datetime.now().strftime('%Y-%m-%d')
    
    cursor.close()
    conn.close()
    
    return render_template('pages/agendar-consulta.html', pets=pets, clinicas=clinicas, horas_disponiveis=horas, hoje=hoje)

@app.route('/get-profissionais-da-clinica/<int:clinica_id>')
def get_profissionais_da_clinica(clinica_id):
    if 'user_id' not in session: return jsonify([]), 401
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # JOIN para pegar médicos vinculados à clínica via tabela medicos_clinicas
    cursor.execute('''
        SELECT m.medico_id as profissional_id, m.nome_medico as nome_profissional
        FROM medicos m
        JOIN medicos_clinicas mc ON m.medico_id = mc.medico_id
        WHERE mc.clinica_id = %s
    ''', (clinica_id,))
    
    medicos = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return jsonify(medicos)

@app.route('/salvar-agendamento', methods=['POST'])
@login_required
def salvar_agendamento():
    try:
        pet_id = request.form.get('pet_id')
        clinica_id = request.form.get('clinica_id')
        medico_id = request.form.get('profissional_id') or None # Pode ser nulo
        data = request.form.get('data_consulta')
        hora = request.form.get('hora_consulta')
        obs = request.form.get('observacoes', '')
        
        # Validar data futura
        data_hora_str = f"{data} {hora}"
        dt = datetime.datetime.strptime(data_hora_str, "%Y-%m-%d %H:%M")
        if dt <= datetime.datetime.now():
            return jsonify({'success': False, 'message': 'Data deve ser futura'})

        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Validar disponibilidade na tabela AGENDAMENTOS
        cursor.execute(
            "SELECT 1 FROM agendamentos WHERE clinica_id=%s AND data_hora=%s AND status != 'cancelado'", 
            (clinica_id, data_hora_str)
        )
        if cursor.fetchone():
             return jsonify({'success': False, 'message': 'Horário indisponível'})

        # Inserir
        cursor.execute(
            'INSERT INTO agendamentos (pet_id, clinica_id, medico_id, data_hora, observacoes, status, data_cadastro) '
            'VALUES (%s, %s, %s, %s, %s, "agendado", NOW())',
            (pet_id, clinica_id, medico_id, data_hora_str, obs)
        )
        conn.commit()
        return jsonify({'success': True, 'message': 'Agendamento realizado!'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if 'conn' in locals(): conn.close()

if __name__ == '__main__':
    app.run(debug=True)