import mysql.connector
import os

def create_database():
    print('Criando/Verificando banco de dados VetBooking...')
    
    # Conectar ao MySQL sem especificar um banco de dados
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='usuario'
        )
        cursor = conn.cursor()
        
        # Verificar se o banco de dados já existe
        cursor.execute("SHOW DATABASES LIKE 'vetbooking'")
        result = cursor.fetchone()
        
        if result:
            print("O banco de dados 'vetbooking' já existe.")
        else:
            # Criar o banco de dados
            cursor.execute("CREATE DATABASE vetbooking")
            print("Banco de dados 'vetbooking' criado com sucesso!")
        
        # Fechar a conexão inicial
        cursor.close()
        conn.close()
        
        # Reconectar ao banco de dados vetbooking
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='usuario',
            database='vetbooking'
        )
        cursor = conn.cursor()
        
        # Criar as tabelas
        print("Verificando e criando tabelas...")
        
        # Tabela pais
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS pais (
          id_pais int NOT NULL AUTO_INCREMENT,
          pais varchar(255) DEFAULT NULL,
          ultima_atualizacao timestamp NULL DEFAULT NULL,
          PRIMARY KEY (id_pais)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
        """)
        
        # Tabela cidade
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS cidade (
          id_cidade int NOT NULL AUTO_INCREMENT,
          cidade varchar(255) DEFAULT NULL,
          ultima_atualizacao timestamp NULL DEFAULT NULL,
          id_pais int DEFAULT NULL,
          PRIMARY KEY (id_cidade),
          KEY fk_id_pais (id_pais),
          CONSTRAINT fk_id_pais FOREIGN KEY (id_pais) REFERENCES pais (id_pais)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
        """)
        
        # Tabela endereco
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS endereco (
          id_endereco int NOT NULL AUTO_INCREMENT,
          endereco varchar(255) DEFAULT NULL,
          cep varchar(255) DEFAULT NULL,
          telefone varchar(255) DEFAULT NULL,
          bairro varchar(255) DEFAULT NULL,
          id_cidade int DEFAULT NULL,
          PRIMARY KEY (id_endereco),
          KEY fk_id_cidade (id_cidade),
          CONSTRAINT fk_id_cidade FOREIGN KEY (id_cidade) REFERENCES cidade (id_cidade)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
        """)
        
        # Tabela tutores
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS tutores (
          tutor_id int NOT NULL AUTO_INCREMENT,
          nome_tutores varchar(255) DEFAULT NULL,
          email varchar(255) DEFAULT NULL,
          senha varchar(255) DEFAULT NULL,
          data_nascimento timestamp NULL DEFAULT NULL,
          data_cadastro timestamp NULL DEFAULT NULL,
          endereco_id int DEFAULT NULL,
          PRIMARY KEY (tutor_id),
          KEY fk_tutor_endereco (endereco_id),
          CONSTRAINT fk_tutor_endereco FOREIGN KEY (endereco_id) REFERENCES endereco (id_endereco)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
        """)
        
        # Tabela medicos
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS medicos (
          medico_id int NOT NULL AUTO_INCREMENT,
          nome_medico varchar(255) DEFAULT NULL,
          email varchar(255) DEFAULT NULL,
          senha varchar(255) DEFAULT NULL,
          crmv varchar(255) DEFAULT NULL,
          uf varchar(255) DEFAULT NULL,
          especialidades varchar(255) DEFAULT NULL,
          descricao varchar(255) DEFAULT NULL,
          foto text,
          data_cadastro timestamp NULL DEFAULT NULL,
          PRIMARY KEY (medico_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
        """)
        
        # Tabela clinicas (ATUALIZADA COM IMAGEM E DESCRICAO)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS clinicas (
          clinica_id int NOT NULL AUTO_INCREMENT,
          razao_social varchar(255) DEFAULT NULL,
          email varchar(255) DEFAULT NULL,
          senha varchar(255) DEFAULT NULL,
          cep varchar(255) DEFAULT NULL,
          uf varchar(255) DEFAULT NULL,
          cidade varchar(255) DEFAULT NULL,
          bairro varchar(255) DEFAULT NULL,
          rua varchar(255) DEFAULT NULL,
          numero varchar(255) DEFAULT NULL,
          complemento varchar(255) DEFAULT NULL,
          telefone varchar(255) DEFAULT NULL,
          horario_funcionamento datetime DEFAULT NULL,
          imagem varchar(255) DEFAULT NULL, -- COLUNA NOVA
          descricao text DEFAULT NULL,      -- COLUNA NOVA
          data_cadastro timestamp NULL DEFAULT NULL,
          PRIMARY KEY (clinica_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
        """)
        
        # Tabela pets
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS pets (
          pet_id int NOT NULL AUTO_INCREMENT,
          nome_pet varchar(255) DEFAULT NULL,
          especie varchar(255) DEFAULT NULL,
          raca varchar(255) DEFAULT NULL,
          data_nascimento datetime DEFAULT NULL,
          sexo char(1) DEFAULT NULL,
          peso double DEFAULT NULL,
          tutor_id int DEFAULT NULL,
          foto varchar(255) DEFAULT NULL,                  
          data_cadastro timestamp NULL DEFAULT NULL,
          PRIMARY KEY (pet_id),
          KEY fk_pet_tutor (tutor_id),
          CONSTRAINT fk_pet_tutor FOREIGN KEY (tutor_id) REFERENCES tutores (tutor_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
        """)
        
        # Tabela medicos_clinicas
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS medicos_clinicas (
          id int NOT NULL AUTO_INCREMENT,
          medico_id int DEFAULT NULL,
          clinica_id int DEFAULT NULL,
          data_cadastro timestamp NULL DEFAULT NULL,
          PRIMARY KEY (id),
          KEY fk_medicos_clinicas_medico (medico_id),
          KEY fk_medicos_clinicas_clinica (clinica_id),
          CONSTRAINT fk_medicos_clinicas_medico FOREIGN KEY (medico_id) REFERENCES medicos (medico_id),
          CONSTRAINT fk_medicos_clinicas_clinica FOREIGN KEY (clinica_id) REFERENCES clinicas (clinica_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
        """)
        
        # Tabela agendamentos
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS agendamentos (
          agendamento_id int NOT NULL AUTO_INCREMENT,
          data_hora datetime DEFAULT NULL,
          pet_id int DEFAULT NULL,
          medico_id int DEFAULT NULL,
          clinica_id int DEFAULT NULL,
          status enum('agendado','cancelado','concluido') DEFAULT NULL,
          observacoes varchar(255) DEFAULT NULL,
          foto varchar(255) DEFAULT NULL,             
          data_cadastro timestamp NULL DEFAULT NULL,
          PRIMARY KEY (agendamento_id),
          KEY fk_agendamento_pet (pet_id),
          KEY fk_agendamento_medico (medico_id),
          KEY fk_agendamentos_clinica (clinica_id),
          CONSTRAINT fk_agendamento_clinica FOREIGN KEY (clinica_id) REFERENCES clinicas (clinica_id),
          CONSTRAINT fk_agendamento_medico FOREIGN KEY (medico_id) REFERENCES medicos (medico_id),
          CONSTRAINT fk_agendamento_pet FOREIGN KEY (pet_id) REFERENCES pets (pet_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
        """)
        
        # Tabela favoritos
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS favoritos (
          favorito_id int NOT NULL AUTO_INCREMENT,
          tutor_id int DEFAULT NULL,
          medico_id int DEFAULT NULL,
          data_cadastro timestamp NULL DEFAULT NULL,
          PRIMARY KEY (favorito_id),
          KEY fk_favorito_tutor (tutor_id),
          KEY fk_favorito_medico (medico_id),
          CONSTRAINT fk_favorito_medico FOREIGN KEY (medico_id) REFERENCES medicos (medico_id),
          CONSTRAINT fk_favorito_tutor FOREIGN KEY (tutor_id) REFERENCES tutores (tutor_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
        """)

        # --- SEÇÃO DE ATUALIZAÇÃO DE TABELAS EXISTENTES (ALTER TABLE) ---
        print("\nVerificando atualizações de colunas (ALTER TABLE)...")
        
        # Tentar adicionar 'imagem' em clinicas (caso não exista)
        try:
            cursor.execute("ALTER TABLE clinicas ADD COLUMN imagem VARCHAR(255) DEFAULT NULL")
            print("- Coluna 'imagem' adicionada à tabela 'clinicas'.")
        except mysql.connector.Error as err:
            if err.errno == 1060: # Código de erro para "Duplicate column name"
                print("- Coluna 'imagem' já existe em 'clinicas'.")
            else:
                print(f"Aviso ao alterar clinicas (imagem): {err}")

        # Tentar adicionar 'descricao' em clinicas (caso não exista)
        try:
            cursor.execute("ALTER TABLE clinicas ADD COLUMN descricao TEXT DEFAULT NULL")
            print("- Coluna 'descricao' adicionada à tabela 'clinicas'.")
        except mysql.connector.Error as err:
            if err.errno == 1060:
                print("- Coluna 'descricao' já existe em 'clinicas'.")
            else:
                print(f"Aviso ao alterar clinicas (descricao): {err}")

        # Commit das alterações
        conn.commit()
        
        # Verificar tabelas criadas
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        print("\nEstrutura do banco de dados verificada com sucesso!")
        
        cursor.close()
        conn.close()
        return True
    
    except mysql.connector.Error as err:
        print(f"Erro fatal: {err}")
        return False

def check_database_connection():
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='usuario',
            database='vetbooking'
        )
        cursor = conn.cursor()
        
        # Verificar tabelas existentes
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        print("\nTabelas encontradas no banco de dados:")
        for table in tables:
            print(f"- {table[0]}")
        
        # Verificar contagem de registros nas tabelas principais
        table_names = [table[0] for table in tables]
        
        if 'tutores' in table_names:
            cursor.execute("SELECT COUNT(*) FROM tutores")
            tutor_count = cursor.fetchone()[0]
            print(f"  > Tutores cadastrados: {tutor_count}")
        
        if 'clinicas' in table_names:
            cursor.execute("SELECT COUNT(*) FROM clinicas")
            clinica_count = cursor.fetchone()[0]
            print(f"  > Clínicas cadastradas: {clinica_count}")
            
            # Verificar se as colunas novas existem mesmo
            cursor.execute("DESCRIBE clinicas")
            columns = [col[0] for col in cursor.fetchall()]
            if 'imagem' in columns and 'descricao' in columns:
                print("  > [OK] Tabela clinicas possui colunas 'imagem' e 'descricao'.")
            else:
                print("  > [ATENÇÃO] Tabela clinicas NÃO possui as novas colunas!")
        
        cursor.close()
        conn.close()
        
        print("\nConexão com o banco de dados realizada com sucesso!")
        return True
    
    except mysql.connector.Error as err:
        print(f"\nErro ao conectar ao banco de dados: {err}")
        return False

if __name__ == '__main__':
    print("=== Criação e Atualização do Banco de Dados VetBooking ===")
    create_database()
    print("\n=== Verificando conexão e estrutura ===")
    check_database_connection()