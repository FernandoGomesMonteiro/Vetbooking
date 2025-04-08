import os
import sqlite3

def check_database():
    print('Verificando banco de dados...')
    print(f'O arquivo database.db existe: {os.path.exists("database.db")}')
    
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        # Verificar tabelas existentes
        cursor.execute('SELECT name FROM sqlite_master WHERE type="table";')
        tables = cursor.fetchall()
        print('\nTabelas encontradas no banco de dados:')
        for table in tables:
            print(f'- {table[0]}')
        
        # Verificar contagem de registros nas tabelas principais
        if 'tutores' in [table[0] for table in tables]:
            cursor.execute('SELECT COUNT(*) FROM tutores')
            tutor_count = cursor.fetchone()[0]
            print(f'\nNúmero de tutores cadastrados: {tutor_count}')
            
            if tutor_count > 0:
                cursor.execute('SELECT id, nome, email FROM tutores LIMIT 3')
                tutores = cursor.fetchall()
                print('Exemplo de tutores cadastrados:')
                for tutor in tutores:
                    print(f'  ID: {tutor[0]}, Nome: {tutor[1]}, Email: {tutor[2]}')
        
        if 'medicos' in [table[0] for table in tables]:
            cursor.execute('SELECT COUNT(*) FROM medicos')
            medico_count = cursor.fetchone()[0]
            print(f'\nNúmero de médicos cadastrados: {medico_count}')
            
            if medico_count > 0:
                cursor.execute('SELECT id, nome, email, crmv FROM medicos LIMIT 3')
                medicos = cursor.fetchall()
                print('Exemplo de médicos cadastrados:')
                for medico in medicos:
                    print(f'  ID: {medico[0]}, Nome: {medico[1]}, Email: {medico[2]}, CRMV: {medico[3]}')
        
        if 'clinicas' in [table[0] for table in tables]:
            cursor.execute('SELECT COUNT(*) FROM clinicas')
            clinica_count = cursor.fetchone()[0]
            print(f'\nNúmero de clínicas cadastradas: {clinica_count}')
            
            if clinica_count > 0:
                cursor.execute('SELECT id, razao_social, email FROM clinicas LIMIT 3')
                clinicas = cursor.fetchall()
                print('Exemplo de clínicas cadastradas:')
                for clinica in clinicas:
                    print(f'  ID: {clinica[0]}, Razão Social: {clinica[1]}, Email: {clinica[2]}')
        
        conn.close()
        print('\nConexão com o banco de dados realizada com sucesso!')
        return True
    except Exception as e:
        print(f'\nErro ao conectar ao banco de dados: {e}')
        return False

if __name__ == '__main__':
    check_database()