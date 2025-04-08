from flask import Flask, render_template, request, redirect, url_for, flash, session
import os
import sqlite3
import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, 
            static_folder='.', 
            static_url_path='',
            template_folder='.')

app.secret_key = 'vetbooking_secret_key'

# Configuração do banco de dados
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# Inicialização do banco de dados
def init_db():
    conn = get_db_connection()
    with open('schema.sql') as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()

# Rotas para as páginas
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

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']
    
    conn = get_db_connection()
    
    # Verificar em todas as tabelas de usuários
    # Tutor
    tutor = conn.execute('SELECT * FROM tutores WHERE email = ?', (email,)).fetchone()
    if tutor and check_password_hash(tutor['senha'], password):
        session['user_id'] = tutor['id']
        session['user_type'] = 'tutor'
        session['user_name'] = tutor['nome']
        conn.close()
        return redirect(url_for('dashboard'))
    
    # Médico Veterinário
    medico = conn.execute('SELECT * FROM medicos WHERE email = ?', (email,)).fetchone()
    if medico and check_password_hash(medico['senha'], password):
        session['user_id'] = medico['id']
        session['user_type'] = 'medico'
        session['user_name'] = medico['nome']
        conn.close()
        return redirect(url_for('dashboard'))
    
    # Clínica
    clinica = conn.execute('SELECT * FROM clinicas WHERE email = ?', (email,)).fetchone()
    if clinica and check_password_hash(clinica['senha'], password):
        session['user_id'] = clinica['id']
        session['user_type'] = 'clinica'
        session['user_name'] = clinica['razao_social']
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
        tutor = conn.execute('SELECT * FROM tutores WHERE id = ?', (user_id,)).fetchone()
        if tutor:
            data['user_since'] = datetime.datetime.strptime(tutor['data_cadastro'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')
        
        # Contar pets do tutor
        pets = conn.execute('SELECT COUNT(*) as count FROM pets WHERE tutor_id = ?', (user_id,)).fetchone()
        data['pets_count'] = pets['count'] if pets else 0
        
        # Contar agendamentos do tutor
        agendamentos = conn.execute(
            'SELECT COUNT(*) as count FROM agendamentos a '
            'JOIN pets p ON a.pet_id = p.id '
            'WHERE p.tutor_id = ? AND a.status = "agendado"', 
            (user_id,)
        ).fetchone()
        data['agendamentos_count'] = agendamentos['count'] if agendamentos else 0
        
        # Contar favoritos do tutor
        favoritos = conn.execute('SELECT COUNT(*) as count FROM favoritos WHERE tutor_id = ?', (user_id,)).fetchone()
        data['favoritos_count'] = favoritos['count'] if favoritos else 0
        
        # Buscar atividades recentes (últimos agendamentos)
        recent_activities = conn.execute(
            'SELECT a.data_hora, m.nome as medico_nome, p.nome as pet_nome '
            'FROM agendamentos a '
            'JOIN pets p ON a.pet_id = p.id '
            'JOIN medicos m ON a.medico_id = m.id '
            'WHERE p.tutor_id = ? '
            'ORDER BY a.data_cadastro DESC LIMIT 5', 
            (user_id,)
        ).fetchall()
        
        for activity in recent_activities:
            data['activities'].append({
                'icon': 'fas fa-calendar-check',
                'text': f'Consulta agendada para {activity["pet_nome"]} com Dr(a). {activity["medico_nome"]}',
                'date': datetime.datetime.strptime(activity['data_hora'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M')
            })
    
    elif user_type == 'medico':
        data['user_type_display'] = 'Médico Veterinário'
        
        # Buscar dados específicos para médicos
        medico = conn.execute('SELECT * FROM medicos WHERE id = ?', (user_id,)).fetchone()
        if medico:
            data['user_since'] = datetime.datetime.strptime(medico['data_cadastro'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')
        
        # Contar agendamentos do médico
        agendamentos = conn.execute(
            'SELECT COUNT(*) as count FROM agendamentos WHERE medico_id = ? AND status = "agendado"', 
            (user_id,)
        ).fetchone()
        data['agendamentos_count'] = agendamentos['count'] if agendamentos else 0
        
        # Contar pacientes únicos do médico
        pacientes = conn.execute(
            'SELECT COUNT(DISTINCT pet_id) as count FROM agendamentos WHERE medico_id = ?', 
            (user_id,)
        ).fetchone()
        data['pacientes_count'] = pacientes['count'] if pacientes else 0
        
        # Contar clínicas associadas ao médico
        clinicas = conn.execute(
            'SELECT COUNT(*) as count FROM medicos_clinicas WHERE medico_id = ?', 
            (user_id,)
        ).fetchone()
        data['clinicas_count'] = clinicas['count'] if clinicas else 0
        
        # Buscar atividades recentes (últimos agendamentos)
        recent_activities = conn.execute(
            'SELECT a.data_hora, p.nome as pet_nome, t.nome as tutor_nome '
            'FROM agendamentos a '
            'JOIN pets p ON a.pet_id = p.id '
            'JOIN tutores t ON p.tutor_id = t.id '
            'WHERE a.medico_id = ? '
            'ORDER BY a.data_cadastro DESC LIMIT 5', 
            (user_id,)
        ).fetchall()
        
        for activity in recent_activities:
            data['activities'].append({
                'icon': 'fas fa-calendar-check',
                'text': f'Consulta agendada para {activity["pet_nome"]} do tutor {activity["tutor_nome"]}',
                'date': datetime.datetime.strptime(activity['data_hora'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M')
            })
    
    elif user_type == 'clinica':
        data['user_type_display'] = 'Clínica Veterinária'
        
        # Buscar dados específicos para clínicas
        clinica = conn.execute('SELECT * FROM clinicas WHERE id = ?', (user_id,)).fetchone()
        if clinica:
            data['user_since'] = datetime.datetime.strptime(clinica['data_cadastro'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')
        
        # Contar agendamentos da clínica
        agendamentos = conn.execute(
            'SELECT COUNT(*) as count FROM agendamentos WHERE clinica_id = ? AND status = "agendado"', 
            (user_id,)
        ).fetchone()
        data['agendamentos_count'] = agendamentos['count'] if agendamentos else 0
        
        # Contar médicos associados à clínica
        medicos = conn.execute(
            'SELECT COUNT(*) as count FROM medicos_clinicas WHERE clinica_id = ?', 
            (user_id,)
        ).fetchone()
        data['medicos_count'] = medicos['count'] if medicos else 0
        
        # Buscar atividades recentes (últimos agendamentos)
        recent_activities = conn.execute(
            'SELECT a.data_hora, p.nome as pet_nome, m.nome as medico_nome '
            'FROM agendamentos a '
            'JOIN pets p ON a.pet_id = p.id '
            'JOIN medicos m ON a.medico_id = m.id '
            'WHERE a.clinica_id = ? '
            'ORDER BY a.data_cadastro DESC LIMIT 5', 
            (user_id,)
        ).fetchall()
        
        for activity in recent_activities:
            data['activities'].append({
                'icon': 'fas fa-calendar-check',
                'text': f'Consulta agendada com Dr(a). {activity["medico_nome"]} para {activity["pet_nome"]}',
                'date': datetime.datetime.strptime(activity['data_hora'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M')
            })
    
    conn.close()
    return render_template('pages/dashboard.html', **data)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

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
    nome = request.form['full-name']
    email = request.form['email']
    senha = generate_password_hash(request.form['password'])
    endereco = request.form['address']
    cep = request.form['cep']
    data_nascimento = request.form['birth-date']
    
    conn = get_db_connection()
    
    # Verificar se o email já existe
    existing_user = conn.execute('SELECT * FROM tutores WHERE email = ?', (email,)).fetchone()
    if existing_user:
        conn.close()
        flash('Email já cadastrado')
        return redirect(url_for('cadastro_tutor_page'))
    
    conn.execute('INSERT INTO tutores (nome, email, senha, endereco, cep, data_nascimento) VALUES (?, ?, ?, ?, ?, ?)',
                (nome, email, senha, endereco, cep, data_nascimento))
    conn.commit()
    conn.close()
    
    flash('Cadastro realizado com sucesso!')
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
    
    # Obter outros campos do formulário
    
    conn = get_db_connection()
    
    # Verificar se o email já existe
    existing_user = conn.execute('SELECT * FROM medicos WHERE email = ?', (email,)).fetchone()
    if existing_user:
        conn.close()
        flash('Email já cadastrado')
        return redirect(url_for('cadastro_mv_page'))
    
    # Inserir no banco de dados (ajustar conforme os campos do formulário)
    conn.execute('INSERT INTO medicos (nome, email, crmv, uf) VALUES (?, ?, ?, ?)',
                (nome, email, crmv, uf))
    conn.commit()
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
    senha = generate_password_hash(request.form['password'])
    cep = request.form['cep']
    uf = request.form['state']
    cidade = request.form['city']
    bairro = request.form['neighborhood']
    rua = request.form['street']
    numero = request.form['number']
    
    conn = get_db_connection()
    
    # Verificar se o email já existe
    existing_user = conn.execute('SELECT * FROM clinicas WHERE email = ?', (email,)).fetchone()
    if existing_user:
        conn.close()
        flash('Email já cadastrado')
        return redirect(url_for('cadastro_clinica_page'))
    
    conn.execute('INSERT INTO clinicas (razao_social, email, senha, cep, uf, cidade, bairro, rua, numero) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (razao_social, email, senha, cep, uf, cidade, bairro, rua, numero))
    conn.commit()
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

if __name__ == '__main__':
    # Verificar se o banco de dados existe, se não, inicializá-lo
    if not os.path.exists('database.db'):
        init_db()
    app.run(debug=True)