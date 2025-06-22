import mysql.connector

def init_db():
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='usuario',
        database='vetbooking'
    )
    cursor = conn.cursor()
    with open('bdVetBooking.sql', encoding='utf-8') as f:
        script = f.read()
        commands = script.split(';')
        for cmd in commands:
            if cmd.strip():
                cursor.execute(cmd + ';')
    conn.commit()
    cursor.close()
    conn.close()
    print("Banco de dados inicializado com sucesso!")

if __name__ == '__main__':
    init_db()