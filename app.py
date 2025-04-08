from flask import Flask, render_template, request, redirect, url_for, flash, session
import os
import sqlite3
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
        return redirect(url_for('index'))
    
    # Médico Veterinário
    medico = conn.execute('SELECT * FROM medicos WHERE email = ?', (email,)).fetchone()
    if medico and check_password_hash(medico['senha'], password):
        session['user_id'] = medico['id']
        session['user_type'] = 'medico'
        session['user_name'] = medico['nome']
        conn.close()
        return redirect(url_for('index'))
    
    # Clínica
    clinica = conn.execute('SELECT * FROM clinicas WHERE email = ?', (email,)).fetchone()
    if clinica and check_password_hash(clinica['senha'], password):
        session['user_id'] = clinica['id']
        session['user_type'] = 'clinica'
        session['user_name'] = clinica['razao_social']
        conn.close()
        return redirect(url_for('index'))
    
    conn.close()
    flash('Email ou senha incorretos')
    return redirect(url_for('login_page'))

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
    return render_template('pages/cadastro-tutor.html')

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