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
os.makedirs('static/uploads/medicos', exist_ok=True)
os.makedirs('static/uploads/documentos', exist_ok=True)
os.makedirs('static/uploads/clinicas', exist_ok=True)

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
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': 'Sessão expirada'}), 401
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
        'user_name': session.get('user_name'),
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

            cursor.execute('SELECT COUNT(*) as count FROM pets WHERE tutor_id = %s', (user_id,))
            data['pets_count'] = cursor.fetchone()['count']
            
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

            cursor.execute('SELECT COUNT(*) as count FROM agendamentos WHERE medico_id = %s AND status = "agendado"', (user_id,))
            data['agendamentos_count'] = cursor.fetchone()['count']
            
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
            cursor.execute('SELECT data_cadastro, razao_social FROM clinicas WHERE clinica_id = %s', (user_id,))
            res = cursor.fetchone()
            if res and res.get('data_cadastro'):
                data['user_since'] = res['data_cadastro'].strftime('%d/%m/%Y')

            # número total de agendamentos agendados para a clínica
            cursor.execute('SELECT COUNT(*) as count FROM agendamentos WHERE clinica_id = %s AND status = "agendado"', (user_id,))
            data['agendamentos_count'] = cursor.fetchone()['count']

            # número de médicos vinculados
            cursor.execute('SELECT COUNT(*) as count FROM medicos_clinicas WHERE clinica_id = %s', (user_id,))
            medicos_cnt_row = cursor.fetchone()
            data['medicos_count'] = medicos_cnt_row['count'] if medicos_cnt_row else 0

            # listar médicos vinculados (para mostrar e editar)
            cursor.execute('''
                SELECT m.medico_id, m.nome_medico
                FROM medicos m
                JOIN medicos_clinicas mc ON m.medico_id = mc.medico_id
                WHERE mc.clinica_id = %s
                ORDER BY m.nome_medico
            ''', (user_id,))
            data['medicos'] = cursor.fetchall()

            # buscar próximos agendamentos da clínica (com pet, tutor e médico)
            cursor.execute('''
                SELECT a.agendamento_id as id, a.data_hora, p.nome_pet, t.nome_tutores, m.nome_medico
                FROM agendamentos a
                JOIN pets p ON a.pet_id = p.pet_id
                JOIN tutores t ON p.tutor_id = t.tutor_id
                LEFT JOIN medicos m ON a.medico_id = m.medico_id
                WHERE a.clinica_id = %s AND a.status = 'agendado'
                ORDER BY a.data_hora ASC LIMIT 50
            ''', (user_id,))
            data['proximas_consultas'] = cursor.fetchall()

    except Exception as e:
        app.logger.error(f"Erro dashboard: {e}")
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
        endereco = request.form.get('address')
        cep = request.form.get('cep')
        telefone = request.form.get('phone')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT 1 FROM tutores WHERE email = %s', (email,))
        if cursor.fetchone():
            flash('Email já cadastrado')
            return redirect(url_for('cadastro_tutor_new_page'))

        endereco_id = None
        if endereco:
            cursor.execute(
                'INSERT INTO endereco (endereco, cep, telefone) VALUES (%s, %s, %s)',
                (endereco, cep, telefone)
            )
            endereco_id = cursor.lastrowid
        
        senha_hash = generate_password_hash(senha)
        
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
        
        foto = None
        if 'foto' in request.files:
            f = request.files['foto']
            if f and allowed_file(f.filename):
                foto = secure_filename(f"med_{uuid.uuid4().hex}.{f.filename.rsplit('.',1)[1]}")
                f.save(os.path.join('static/uploads/medicos', foto))

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT 1 FROM medicos WHERE email = %s', (email,))
        if cursor.fetchone(): 
            return jsonify({'success': False, 'message': 'Email já cadastrado'})

        cursor.execute(
            'INSERT INTO medicos (nome_medico, email, senha, crmv, uf, especialidades, descricao, foto, data_cadastro) '
            'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())',
            (nome, email, senha_hash, crmv, uf, especialidades_str, descricao, foto)
        )
        medico_id = cursor.lastrowid
        
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

        # Converter strings vazias para None se necessário, ou manter vazias
        if not nasc: nasc = None
        if not peso: peso = None

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
    especie = request.form['especie']
    raca = request.form.get('raca', '')
    nasc = request.form.get('data_nascimento')
    sexo = request.form.get('sexo', '')
    peso = request.form.get('peso')
    
    if not nasc: nasc = None
    if not peso: peso = None

    foto = None
    if 'foto' in request.files:
        f = request.files['foto']
        if f and allowed_file(f.filename):
            foto = secure_filename(f"pet_{uuid.uuid4().hex}.{f.filename.rsplit('.',1)[1]}")
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], foto))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Verifica dono e pega foto antiga
        cursor.execute('SELECT tutor_id, foto FROM pets WHERE pet_id = %s', (pet_id,))
        pet = cursor.fetchone()
        
        if not pet or pet['tutor_id'] != session['user_id']:
            return jsonify({'success': False, 'message': 'Permissão negada'}), 403
        
        # Mantém foto antiga se não enviou nova
        if not foto: foto = pet['foto']
        
        cursor.execute(
            'UPDATE pets SET nome_pet=%s, especie=%s, raca=%s, data_nascimento=%s, sexo=%s, peso=%s, foto=%s WHERE pet_id=%s',
            (nome, especie, raca, nasc, sexo, peso, foto, pet_id)
        )
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()

@app.route('/excluir-pet', methods=['POST'])
@login_required
def excluir_pet():
    try:
        data = request.get_json()
        pet_id = data.get('pet_id')
        tutor_id = session['user_id']

        conn = get_db_connection()
        cursor = conn.cursor()

        # Verifica se o pet pertence mesmo ao usuário logado
        cursor.execute('SELECT foto FROM pets WHERE pet_id = %s AND tutor_id = %s', (pet_id, tutor_id))
        pet = cursor.fetchone()

        if not pet:
            return jsonify({'success': False, 'message': 'Pet não encontrado ou não autorizado'}), 403

        # Remove agendamentos futuros para não dar erro de chave estrangeira
        cursor.execute('DELETE FROM agendamentos WHERE pet_id = %s', (pet_id,))
        
        # Remove o pet
        cursor.execute('DELETE FROM pets WHERE pet_id = %s', (pet_id,))
        conn.commit()

        return jsonify({'success': True})

    except Exception as e:
        if 'conn' in locals(): conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if 'conn' in locals(): conn.close()

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
        medico_id = request.form.get('profissional_id') or None 
        data = request.form.get('data_consulta')
        hora = request.form.get('hora_consulta')
        obs = request.form.get('observacoes', '')
        
        data_hora_str = f"{data} {hora}"
        dt = datetime.datetime.strptime(data_hora_str, "%Y-%m-%d %H:%M")
        if dt <= datetime.datetime.now():
            return jsonify({'success': False, 'message': 'Data deve ser futura'})

        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT 1 FROM agendamentos WHERE clinica_id=%s AND data_hora=%s AND status != 'cancelado'", 
            (clinica_id, data_hora_str)
        )
        if cursor.fetchone():
             return jsonify({'success': False, 'message': 'Horário indisponível'})

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

@app.route('/api/clinicas')
def api_clinicas():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute('''
            SELECT clinica_id, razao_social, cidade, uf, telefone, cep, 
                   imagem, descricao 
            FROM clinicas
        ''')
        
        rows = cursor.fetchall()
        lista = []
        
        for r in rows:
            cidade = r.get('cidade') or ''
            uf = r.get('uf')
            localizacao = f"{cidade}, {uf}" if uf else cidade

            imagem_nome = r.get('imagem')
            if imagem_nome and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'].replace('pets', 'clinicas'), imagem_nome)):
                imagem_url = f"/static/uploads/clinicas/{imagem_nome}"
            else:
                imagem_url = "/static/img/default-clinic.jpg"

            lista.append({
                'id': r.get('clinica_id'),
                'nome': r.get('razao_social'),
                'localizacao': localizacao,
                'telefone': r.get('telefone'),
                'preco': "Sob consulta",
                'avaliacao': 4.5,
                'imagem': imagem_url,
                'caracteristicas': r.get('descricao') or 'Clínica veterinária completa.'
            })
            
        cursor.close()
        conn.close()
        return jsonify(lista)
        
    except Exception as e:
        app.logger.error(f"Erro API /api/clinicas: {e}")
        return jsonify({'error': 'Erro interno'}), 500

@app.route('/clinica/<int:clinica_id>')
def clinica_page(clinica_id):
    # Passa apenas o ID para o template, o JS busca os dados na API
    return render_template('pages/clinica.html', clinica_id=clinica_id)

@app.route('/api/medicos')
def api_medicos():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        if session.get('user_type') == 'clinica' and session.get('user_id'):
            cursor.execute('''
                SELECT m.medico_id, m.nome_medico, m.crmv, m.especialidades, m.descricao, m.foto
                FROM medicos m
                JOIN medicos_clinicas mc ON m.medico_id = mc.medico_id
                WHERE mc.clinica_id = %s
                ORDER BY m.nome_medico
            ''', (session['user_id'],))
        else:
            cursor.execute('SELECT medico_id, nome_medico, crmv, especialidades, descricao, foto FROM medicos ORDER BY nome_medico')

        rows = cursor.fetchall()
        lista = []
        for r in rows:
            lista.append({
                'id': r.get('medico_id'),
                'nome': r.get('nome_medico'),
                'crmv': r.get('crmv'),
                'especialidades': r.get('especialidades') or '',
                'descricao': r.get('descricao') or '',
                'foto': (f"/static/uploads/medicos/{r.get('foto')}" if r.get('foto') else "/static/img/default-user.jpg")
            })
        cursor.close()
        conn.close()
        return jsonify(lista)
    except Exception as e:
        app.logger.error(f"Erro API /api/medicos: {e}")
        return jsonify([]), 500

@app.route('/pages/veterinario.html')
def veterinario_page():
    return render_template('pages/veterinario.html')

@app.route('/editar-veterinario/<int:medico_id>', methods=['GET', 'POST'])
@login_required
def editar_veterinario(medico_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        if request.method == 'POST':
            nome = request.form.get('nome_medico')
            crmv = request.form.get('crmv')
            especialidades = request.form.get('especialidades', '')
            descricao = request.form.get('descricao', '')

            foto_nome = None
            if 'foto' in request.files:
                f = request.files['foto']
                if f and allowed_file(f.filename):
                    foto_nome = secure_filename(f"med_{uuid.uuid4().hex}.{f.filename.rsplit('.',1)[1]}")
                    f.save(os.path.join('static/uploads/medicos', foto_nome))

            partes = ['nome_medico=%s','crmv=%s','especialidades=%s','descricao=%s']
            valores = [nome, crmv, especialidades, descricao]
            if foto_nome:
                partes.append('foto=%s')
                valores.append(foto_nome)
            valores.append(medico_id)
            sql = f"UPDATE medicos SET {', '.join(partes)} WHERE medico_id = %s"
            cursor.execute(sql, tuple(valores))
            conn.commit()
            return redirect(url_for('veterinario_page'))

        cursor.execute('SELECT medico_id, nome_medico, crmv, especialidades, descricao, foto FROM medicos WHERE medico_id = %s', (medico_id,))
        medico = cursor.fetchone()
        if not medico:
            return "Médico não encontrado", 404
        return render_template('pages/editar-veterinario.html', medico=medico)
    except Exception as e:
        app.logger.error(f"Erro editar_veterinario: {e}")
        return "Erro interno", 500
    finally:
        cursor.close()
        conn.close()

@app.route('/pages/editar-perfil.html')
@login_required
def editar_perfil_page():
    user_id = session.get('user_id')
    user_type = session.get('user_type')
    data = {
        'user_name': session.get('user_name'),
        'user_type': user_type,
        'user_type_display': '',
        'user_since': datetime.datetime.now().strftime('%d/%m/%Y')
    }

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        if user_type == 'tutor':
            cursor.execute('SELECT tutor_id, nome_tutores, email, data_cadastro, endereco_id, data_nascimento FROM tutores WHERE tutor_id = %s', (user_id,))
            tutor = cursor.fetchone() or {}
            data['user_type_display'] = 'Tutor de Pet'
            if tutor.get('data_cadastro'):
                data['user_since'] = tutor['data_cadastro'].strftime('%d/%m/%Y')

            endereco = None
            if tutor.get('endereco_id'):
                cursor.execute('SELECT endereco, cep, telefone FROM endereco WHERE id_endereco = %s', (tutor['endereco_id'],))
                endereco = cursor.fetchone()
            
            tutor['endereco'] = endereco.get('endereco') if endereco else ''
            tutor['cep'] = endereco.get('cep') if endereco else ''
            tutor['telefone'] = endereco.get('telefone') if endereco else ''
            data['tutor'] = tutor

        elif user_type == 'clinica':
            cursor.execute('SELECT * FROM clinicas WHERE clinica_id = %s', (user_id,))
            clinica = cursor.fetchone() or {}
            data['user_type_display'] = 'Clínica Veterinária'
            if clinica.get('data_cadastro'):
                data['user_since'] = clinica['data_cadastro'].strftime('%d/%m/%Y')
            data['clinica'] = clinica

        else:  # medico
            cursor.execute('SELECT medico_id, nome_medico, email, data_cadastro FROM medicos WHERE medico_id = %s', (user_id,))
            medico = cursor.fetchone() or {}
            data['user_type_display'] = 'Médico Veterinário'
            if medico.get('data_cadastro'):
                data['user_since'] = medico['data_cadastro'].strftime('%d/%m/%Y')
            data['medico'] = medico

    finally:
        cursor.close()
        conn.close()

    return render_template('pages/editar-perfil.html', **data)

@app.route('/editar-perfil', methods=['POST'])
@login_required
def editar_perfil_submit():
    user_id = session.get('user_id')
    user_type = session.get('user_type')
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        display_name = None
        email = request.form.get('email')

        if user_type == 'tutor':
            nome = request.form.get('nome')
            data_nascimento = request.form.get('data_nascimento') or None
            # Logica para endereco se necessario
            cursor.execute(
                'UPDATE tutores SET nome_tutores=%s, email=%s, data_nascimento=%s WHERE tutor_id=%s',
                (nome, email, data_nascimento, user_id)
            )
            display_name = nome

        elif user_type == 'clinica':
            razao = request.form.get('razao_social')
            telefone = request.form.get('telefone')
            cep = request.form.get('cep')
            cidade = request.form.get('cidade')
            uf = request.form.get('uf')
            cursor.execute(
                'UPDATE clinicas SET razao_social=%s, email=%s, telefone=%s, cep=%s, cidade=%s, uf=%s WHERE clinica_id=%s',
                (razao, email, telefone, cep, cidade, uf, user_id)
            )
            display_name = razao

        else:  # medico
            nome_medico = request.form.get('nome_medico')
            crmv = request.form.get('crmv')
            especialidades = request.form.get('especialidades')
            descricao = request.form.get('descricao')
            cursor.execute(
                'UPDATE medicos SET nome_medico=%s, email=%s, crmv=%s, especialidades=%s, descricao=%s WHERE medico_id=%s',
                (nome_medico, email, crmv, especialidades, descricao, user_id)
            )
            display_name = nome_medico

        conn.commit()

        if display_name:
            session['user_name'] = display_name

        return jsonify({'success': True, 'redirect': url_for('dashboard')})
    except Exception as e:
        if conn: conn.rollback()
        app.logger.error(f"Erro ao salvar perfil: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@app.route('/api/consultas')
@login_required
def api_consultas():
    user_id = session.get('user_id')
    user_type = session.get('user_type')
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        if user_type == 'tutor':
            cursor.execute('''
                SELECT a.agendamento_id AS id, a.data_hora, a.status, a.observacoes,
                       p.pet_id, p.nome_pet,
                       c.clinica_id, c.razao_social AS clinica_nome, c.cidade, c.uf, c.cep, c.telefone,
                       m.medico_id, m.nome_medico
                FROM agendamentos a
                JOIN pets p ON a.pet_id = p.pet_id
                JOIN clinicas c ON a.clinica_id = c.clinica_id
                LEFT JOIN medicos m ON a.medico_id = m.medico_id
                WHERE p.tutor_id = %s
                ORDER BY a.data_hora DESC
            ''', (user_id,))
        elif user_type == 'medico':
            cursor.execute('''
                SELECT a.agendamento_id AS id, a.data_hora, a.status, a.observacoes,
                       p.pet_id, p.nome_pet,
                       c.clinica_id, c.razao_social AS clinica_nome, c.cidade, c.uf, c.cep, c.telefone,
                       t.tutor_id, t.nome_tutores
                FROM agendamentos a
                JOIN pets p ON a.pet_id = p.pet_id
                JOIN clinicas c ON a.clinica_id = c.clinica_id
                JOIN tutores t ON p.tutor_id = t.tutor_id
                WHERE a.medico_id = %s
                ORDER BY a.data_hora DESC
            ''', (user_id,))
        else:  # clinica
            cursor.execute('''
                SELECT a.agendamento_id AS id, a.data_hora, a.status, a.observacoes,
                       p.pet_id, p.nome_pet,
                       t.tutor_id, t.nome_tutores,
                       m.medico_id, m.nome_medico,
                       c.clinica_id, c.razao_social AS clinica_nome, c.cidade, c.uf, c.cep, c.telefone
                FROM agendamentos a
                JOIN pets p ON a.pet_id = p.pet_id
                JOIN tutores t ON p.tutor_id = t.tutor_id
                LEFT JOIN medicos m ON a.medico_id = m.medico_id
                JOIN clinicas c ON a.clinica_id = c.clinica_id
                WHERE a.clinica_id = %s
                ORDER BY a.data_hora DESC
            ''', (user_id,))

        rows = cursor.fetchall()
        lista = []
        for r in rows:
            cidade = r.get('cidade') or ''
            uf = r.get('uf') or ''
            cep = r.get('cep') or ''
            localizacao = f"{cidade}{', ' + uf if uf else ''}"
            if cep:
                localizacao = f"{localizacao} — CEP {cep}" if localizacao else f"CEP {cep}"

            lista.append({
                'id': r.get('id'),
                'data_hora': r.get('data_hora').strftime('%Y-%m-%d %H:%M') if r.get('data_hora') else None,
                'status': r.get('status'),
                'observacoes': r.get('observacoes') or '',
                'nome_pet': r.get('nome_pet'),
                'pet_id': r.get('pet_id'),
                'clinica_id': r.get('clinica_id'),
                'clinica_nome': r.get('clinica_nome'),
                'clinica_endereco': localizacao,
                'clinica_telefone': r.get('telefone'),
                'nome_medico': r.get('nome_medico'),
                'tutor_nome': r.get('nome_tutores') or None,
            })
        cursor.close()
        conn.close()
        return jsonify(lista)
    except Exception as e:
        app.logger.error(f"Erro API /api/consultas: {e}")
        return jsonify([]), 500

if __name__ == '__main__':
    app.run(debug=True)