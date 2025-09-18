# PetBooking - Documentação do Backend

## Índice
1. [Visão Geral](#visão-geral)
2. [Requisitos do Sistema](#requisitos-do-sistema)
3. [Configuração do Ambiente](#configuração-do-ambiente)
4. [Estrutura do Banco de Dados](#estrutura-do-banco-de-dados)
5. [Rotas da API](#rotas-da-api)
6. [Autenticação](#autenticação)
7. [Modelos de Dados](#modelos-de-dados)
8. [Tratamento de Erros](#tratamento-de-erros)

## Visão Geral
O backend do PetBooking é construído em Python utilizando o framework Flask, com um banco de dados MySQL para persistência dos dados. O sistema gerencia o agendamento de consultas, cadastro de usuários (tutores e clínicas) e gerenciamento de pets.

## Requisitos do Sistema
- Python 3.8 ou superior
- MySQL 8.0 ou superior
- pip (gerenciador de pacotes Python)

### Dependências Principais
```
Flask==2.0.1
MySQL-connector-python==8.0.26
Werkzeug==2.0.1
PyJWT==2.1.0
```

## Configuração do Ambiente

### 1. Instalação das Dependências
```bash
pip install -r requirements.txt
```

### 2. Configuração do Banco de Dados
1. Crie um banco de dados MySQL
2. Execute o script de criação das tabelas:
```bash
python create_db.py
```

### 3. Variáveis de Ambiente
Configure as seguintes variáveis no arquivo de ambiente ou diretamente no sistema:
- `DB_HOST`: Host do banco de dados
- `DB_USER`: Usuário do banco de dados
- `DB_PASSWORD`: Senha do banco de dados
- `DB_NAME`: Nome do banco de dados
- `SECRET_KEY`: Chave secreta para sessões e tokens

### 4. Inicialização do Servidor
```bash
python app.py
```

## Estrutura do Banco de Dados

### Tabelas Principais

#### usuarios
- `id` (INT): Identificador único
- `nome` (VARCHAR): Nome completo
- `email` (VARCHAR): Email único
- `senha` (VARCHAR): Senha criptografada
- `tipo` (VARCHAR): Tipo de usuário (tutor, clinica)

#### pets
- `id` (INT): Identificador único
- `nome` (VARCHAR): Nome do pet
- `especie` (VARCHAR): Espécie do animal
- `raca` (VARCHAR): Raça
- `idade` (INT): Idade em anos
- `tutor_id` (INT): ID do tutor responsável



#### clinicas
- `id` (INT): Identificador único
- `usuario_id` (INT): ID do usuário associado
- `cnpj` (VARCHAR): CNPJ da clínica
- `endereco` (VARCHAR): Endereço completo
- `servicos` (TEXT): Serviços oferecidos

#### consultas
- `id` (INT): Identificador único
- `pet_id` (INT): ID do pet
- `profissional_id` (INT): ID do profissional
- `clinica_id` (INT): ID da clínica
- `data_hora` (DATETIME): Data e hora da consulta
- `status` (VARCHAR): Status da consulta

## Rotas da API

### Autenticação
- `POST /login`: Login de usuário
  - Corpo: `{"email": "string", "senha": "string"}`
  - Retorno: Token de autenticação

### Usuários
- `POST /cadastro`: Cadastro de novo usuário
  - Corpo: `{"nome": "string", "email": "string", "senha": "string", "tipo": "string"}`

### Pets
- `GET /pets`: Lista pets do tutor
- `POST /pets`: Cadastra novo pet
- `PUT /pets/<id>`: Atualiza informações do pet
- `DELETE /pets/<id>`: Remove pet



### Clínicas
- `GET /api/clinicas`: Lista todas as clínicas
- `GET /clinicas/<id>`: Obtém detalhes da clínica
- `PUT /clinicas/<id>`: Atualiza informações da clínica

### Consultas
- `POST /consultas`: Agenda nova consulta
  - Corpo: `{"pet_id": "int", "profissional_id": "int", "clinica_id": "int", "data_hora": "datetime"}`
- `GET /consultas`: Lista consultas do usuário
- `PUT /consultas/<id>`: Atualiza status da consulta

## Autenticação
O sistema utiliza autenticação baseada em sessão para manter o estado do usuário. Após o login bem-sucedido, um ID de sessão é gerado e armazenado em um cookie seguro.

### Middleware de Autenticação
O middleware verifica a presença e validade da sessão em rotas protegidas. Rotas públicas são configuradas através de uma lista de exceções.

## Modelos de Dados

### Formato de Resposta Padrão
```json
{
    "success": true,
    "data": {},
    "message": "string"
}
```

### Códigos de Status HTTP
- 200: Sucesso
- 201: Criado com sucesso
- 400: Erro de validação
- 401: Não autorizado
- 404: Recurso não encontrado
- 500: Erro interno do servidor

## Tratamento de Erros
O sistema implementa um tratamento de erros centralizado que captura exceções e retorna respostas formatadas adequadamente:

```python
{
    "success": false,
    "error": {
        "code": "string",
        "message": "string"
    }
}
```

### Tipos de Erro Comuns
- `ValidationError`: Erro de validação de dados
- `AuthenticationError`: Erro de autenticação
- `ResourceNotFound`: Recurso não encontrado
- `DatabaseError`: Erro de banco de dados

---

