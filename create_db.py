import mysql.connector
import os

def create_database():
    print('Criando banco de dados VetBooking...')
    
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
        
        # Criar as tabelas manualmente em vez de usar o arquivo SQL
        print("Criando tabelas no banco de dados...")
        
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
        
        # Tabela clinicas
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
          foto varchar(255) DEFAULT NULL,  -- COLUNA ADICIONADA                  
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
          foto varchar(255) DEFAULT NULL,  -- COLUNA ADICIONADA             
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
          data_cadastro timestamp NULL DEFAULT NULL,
          foto varchar(255) DEFAULT NULL,  -- COLUNA ADICIONADA
          PRIMARY KEY (pet_id),
          KEY fk_pet_tutor (tutor_id),
          CONSTRAINT fk_pet_tutor FOREIGN KEY (tutor_id) REFERENCES tutores (tutor_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
        """)
        
        print("Todas as tabelas foram criadas com sucesso!")
        
        # Commit das alterações
        conn.commit()
        
        # Verificar tabelas criadas
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        print("\nTabelas criadas no banco de dados:")
        for table in tables:
            print(f"- {table[0]}")
        
        cursor.close()
        conn.close()
        
        print("\nBanco de dados configurado com sucesso!")
        return True
    
    except mysql.connector.Error as err:
        print(f"Erro: {err}")
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
            print(f"\nNúmero de tutores cadastrados: {tutor_count}")
        
        if 'medicos' in table_names:
            cursor.execute("SELECT COUNT(*) FROM medicos")
            medico_count = cursor.fetchone()[0]
            print(f"\nNúmero de médicos cadastrados: {medico_count}")
        
        if 'clinicas' in table_names:
            cursor.execute("SELECT COUNT(*) FROM clinicas")
            clinica_count = cursor.fetchone()[0]
            print(f"\nNúmero de clínicas cadastradas: {clinica_count}")
        
        cursor.close()
        conn.close()
        
        print("\nConexão com o banco de dados realizada com sucesso!")
        return True
    
    except mysql.connector.Error as err:
        print(f"\nErro ao conectar ao banco de dados: {err}")
        return False

if __name__ == '__main__':
    print("=== Criação e Verificação do Banco de Dados VetBooking ===")
    create_database()
    print("\n=== Verificando conexão com o banco de dados ===")
    check_database_connection()