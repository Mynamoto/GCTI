import sqlite3

def init_db():
    conn = sqlite3.connect('chamados.db')
    c = conn.cursor()
    
    # Criar tabela de usuários
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                 username TEXT PRIMARY KEY,
                 password TEXT NOT NULL,
                 role TEXT NOT NULL,
                 nome_completo TEXT,
                 telefone_contato TEXT,
                 setor TEXT,
                 regiao TEXT
                 )''')
    
    # Criar tabela de chamados
    c.execute('''CREATE TABLE IF NOT EXISTS chamados (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 solicitador_id TEXT,
                 nome_solicitante TEXT,
                 telefone_contato TEXT,
                 setor TEXT,
                 regiao TEXT,
                 categoria TEXT,
                 tipo_chamado TEXT,
                 descricao TEXT,
                 data_abertura TEXT,
                 prazo TEXT,
                 status TEXT,
                 data_fechamento TEXT,
                 solucao TEXT,
                 anexo BLOB
                 )''')
    
    # Migrações para colunas adicionais
    migrations = [
        ("fechado_solicitador", "INTEGER DEFAULT 0"),
        ("fechado_tecnico", "INTEGER DEFAULT 0"),
        ("solucao_solicitador", "TEXT"),
        ("solucao_tecnico", "TEXT"),
        ("data_fechamento_solicitador", "TEXT"),
        ("data_fechamento_tecnico", "TEXT"),
        ("tratativa_tecnico", "TEXT"),
        ("troca_pecas", "TEXT"),
        ("qual_peca", "TEXT"),
        ("nome_marca_peca", "TEXT"),
        ("solicitacao_info", "TEXT"),
        ("fluxo_errado", "INTEGER DEFAULT 0"),
        ("tipo_chamado", "TEXT")  # Adicionando a nova coluna
    ]
    
    for column, column_type in migrations:
        try:
            c.execute(f"ALTER TABLE chamados ADD COLUMN {column} {column_type}")
        except sqlite3.OperationalError:
            pass
    
    # Opcional: Renomear subcategoria para tipo_chamado se ela existir
    try:
        c.execute("ALTER TABLE chamados RENAME COLUMN subcategoria TO tipo_chamado")
    except sqlite3.OperationalError:
        pass
    
    conn.commit()
    conn.close()

def add_user(username, password, role, nome_completo, telefone_contato, setor, regiao):
    conn = sqlite3.connect('chamados.db')
    c = conn.cursor()
    c.execute("INSERT INTO users (username, password, role, nome_completo, telefone_contato, setor, regiao) VALUES (?, ?, ?, ?, ?, ?, ?)",
              (username, password, role, nome_completo, telefone_contato, setor, regiao))
    conn.commit()
    conn.close()

def verify_login(username, password):
    conn = sqlite3.connect('chamados.db')
    c = conn.cursor()
    c.execute("SELECT role FROM users WHERE username=? AND password=?", (username, password))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None