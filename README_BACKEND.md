# Backend Flask para VetBooking

Este é o backend em Python usando Flask para o projeto VetBooking, que conecta as páginas HTML existentes e implementa a lógica de negócio para o sistema de agendamento veterinário.

## Estrutura do Projeto

O backend foi estruturado da seguinte forma:

- `app.py`: Arquivo principal da aplicação Flask com todas as rotas e lógica de negócio
- `schema.sql`: Definição do esquema do banco de dados SQLite
- `requirements.txt`: Lista de dependências do projeto

## Requisitos

Antes de executar o projeto, você precisa ter o Python instalado no seu sistema. Recomendamos a versão 3.8 ou superior.

### Instalação do Python

1. Baixe o Python do [site oficial](https://www.python.org/downloads/)
2. Durante a instalação, marque a opção "Add Python to PATH"
3. Verifique a instalação abrindo o Prompt de Comando e digitando: `python --version`

## Configuração do Ambiente

Siga estes passos para configurar e executar o backend:

1. Abra o Prompt de Comando na pasta do projeto (VetBooking)

2. Crie um ambiente virtual (opcional, mas recomendado):
   ```
   python -m venv venv
   venv\Scripts\activate
   ```

3. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```

4. Execute a aplicação:
   ```
   python app.py
   ```

5. Acesse a aplicação no navegador: http://localhost:5000

## Funcionalidades Implementadas

O backend implementa as seguintes funcionalidades:

- Rotas para todas as páginas HTML existentes
- Sistema de autenticação e login
- Cadastro de tutores, médicos veterinários e clínicas
- Banco de dados SQLite para armazenamento de dados

## Banco de Dados

O banco de dados SQLite é criado automaticamente na primeira execução da aplicação. Ele contém as seguintes tabelas:

- `tutores`: Armazena informações dos donos de pets
- `medicos`: Armazena informações dos médicos veterinários
- `clinicas`: Armazena informações das clínicas veterinárias
- `pets`: Armazena informações dos pets cadastrados
- `medicos_clinicas`: Relaciona médicos com as clínicas onde trabalham
- `agendamentos`: Armazena os agendamentos de consultas
- `favoritos`: Armazena os médicos favoritos de cada tutor

## Próximos Passos

- Implementar a página de cadastro de pets
- Implementar a lista de pets
- Implementar o sistema de agendamento
- Implementar o perfil de usuário
- Implementar a lista de favoritos