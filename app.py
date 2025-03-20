from flask import Flask, render_template, request, redirect, session
from flask_socketio import SocketIO, emit
import sqlite3
from datetime import datetime
from database import verify_login, init_db, add_user
import os

app = Flask(__name__)
app.secret_key = "chave_secreta_123"
socketio = SocketIO(app, cors_allowed_origins="*")

with app.app_context():
    init_db()

def calcular_sla(data_abertura, prazo, status, data_fechamento=None):
    if status == 'fechado' and data_fechamento:
        data_fechamento = datetime.strptime(data_fechamento, "%Y-%m-%d %H:%M:%S")
        prazo = datetime.strptime(prazo, "%Y-%m-%d")
        return 0, "green" if data_fechamento.date() <= prazo.date() else "red"
    
    data_abertura = datetime.strptime(data_abertura, "%Y-%m-%d %H:%M:%S")
    prazo = datetime.strptime(prazo, "%Y-%m-%d")
    hoje = datetime.now()
    tempo_total = (prazo - data_abertura).days
    tempo_decorrido = (hoje - data_abertura).days
    tempo_restante = (prazo - hoje).days
    porcentagem_restante = (tempo_restante / tempo_total) * 100 if tempo_total > 0 else 0

    if tempo_restante < 0:
        cor = "red"
    elif porcentagem_restante > 50:
        cor = "green"
    elif porcentagem_restante > 10:
        cor = "yellow"
    else:
        cor = "red"
    
    return max(tempo_restante, 0), cor

@app.route("/minha_conta")
def minha_conta():
    if "username" not in session:
        return redirect("/login")
    conn = sqlite3.connect('chamados.db')
    c = conn.cursor()
    c.execute("SELECT username, nome_completo, telefone_contato, setor, regiao, role FROM users WHERE username=?", (session["username"],))
    user = c.fetchone()
    conn.close()
    return render_template("minha_conta.html", user=user)

@app.route("/editar_conta", methods=["GET", "POST"])
def editar_conta():
    if "username" not in session:
        return redirect("/login")
    conn = sqlite3.connect('chamados.db')
    c = conn.cursor()
    if request.method == "POST":
        nome_completo = request.form.get("nome_completo")
        telefone_contato = request.form.get("telefone_contato")
        setor = request.form.get("setor")
        regiao = request.form.get("regiao")
        c.execute("UPDATE users SET nome_completo=?, telefone_contato=?, setor=?, regiao=? WHERE username=?",
                  (nome_completo, telefone_contato, setor, regiao, session["username"]))
        conn.commit()
        conn.close()
        return redirect("/minha_conta")
    c.execute("SELECT nome_completo, telefone_contato, setor, regiao FROM users WHERE username=?", (session["username"],))
    user = c.fetchone()
    conn.close()
    return render_template("editar_conta.html", user=user)

@app.route("/")
def root():
    return redirect("/login")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        role = verify_login(username, password)
        if role:
            session["username"] = username
            session["role"] = role
            return redirect("/dashboard")
        return "Usuário ou senha inválidos", 401
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/primeiro_acesso")
def primeiro_acesso():
    return render_template("primeiro_acesso.html")

@app.route("/cadastro_usuario", methods=["GET", "POST"])
def cadastro_usuario():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        nome_completo = request.form.get("nome_completo")
        telefone_contato = request.form.get("telefone_contato")
        setor = request.form.get("setor")
        regiao = request.form.get("regiao")
        role = "solicitador"  # Por padrão, novos usuários são solicitadores
        add_user(username, password, role, nome_completo, telefone_contato, setor, regiao)
        return redirect("/login")
    return render_template("cadastro_usuario.html")

@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect("/login")
    role = session["role"]
    conn = sqlite3.connect('chamados.db')
    c = conn.cursor()
    
    if role == "solicitador":
        c.execute("SELECT id, categoria, tipo_chamado, descricao, setor, regiao, data_abertura, prazo, status FROM chamados WHERE solicitador_id=? AND status='aberto'", (session["username"],))
        chamados_abertos = c.fetchall()
        chamados_abertos_com_sla = [(chamado + calcular_sla(chamado[6], chamado[7], chamado[8])) for chamado in chamados_abertos]
        
        c.execute("SELECT id, categoria, tipo_chamado, descricao, setor, regiao, data_abertura, data_fechamento, status FROM chamados WHERE solicitador_id=? AND status='fechado'", (session["username"],))
        chamados_fechados = c.fetchall()
        chamados_fechados_com_sla = [(chamado + calcular_sla(chamado[6], "2025-03-26", chamado[8], chamado[7])) for chamado in chamados_fechados]
        
        conn.close()
        return render_template("solicitador.html", username=session["username"], chamados_abertos=chamados_abertos_com_sla, chamados_fechados=chamados_fechados_com_sla)
    
    elif role == "tecnico":
        c.execute("SELECT id, solicitador_id, categoria, setor, regiao, prazo, status, data_abertura, descricao FROM chamados WHERE status='aberto'")
        chamados = c.fetchall()
        chamados_com_sla = [(chamado + calcular_sla(chamado[7], chamado[5], chamado[6])) for chamado in chamados]
        
        c.execute("SELECT id, solicitador_id, categoria, setor, regiao, data_abertura, data_fechamento, status, solucao_tecnico, tratativa_tecnico, troca_pecas, qual_peca, nome_marca_peca FROM chamados WHERE status='fechado'")
        chamados_fechados = c.fetchall()
        chamados_fechados_com_sla = [(chamado + calcular_sla(chamado[5], "2025-03-26", chamado[7], chamado[6])) for chamado in chamados_fechados]
        
        conn.close()
        return render_template("tecnico.html", chamados=chamados_com_sla, chamados_fechados=chamados_fechados_com_sla)

@app.route("/abrir_chamado", methods=["GET", "POST"])
def abrir_chamado():
    if "role" not in session or session["role"] != "solicitador":
        return redirect("/login")
    if request.method == "POST":
        nome_solicitante = request.form.get("nome_solicitante")
        telefone_contato = request.form.get("telefone_contato")
        setor = request.form.get("setor")
        regiao = request.form.get("regiao")
        categoria = request.form.get("categoria")
        tipo_chamado = request.form.get("tipo_chamado")
        descricao = request.form.get("descricao")
        anexo = request.files.get("anexo")
        anexo_data = anexo.read() if anexo else None
        
        conn = sqlite3.connect('chamados.db')
        c = conn.cursor()
        c.execute("INSERT INTO chamados (solicitador_id, nome_solicitante, telefone_contato, setor, regiao, categoria, tipo_chamado, descricao, data_abertura, prazo, status, anexo) VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), '2025-03-26', 'aberto', ?)",
                  (session["username"], nome_solicitante, telefone_contato, setor, regiao, categoria, tipo_chamado, descricao, anexo_data))
        conn.commit()
        
        c.execute("SELECT last_insert_rowid()")
        chamado_id = c.fetchone()[0]
        c.execute("SELECT id, solicitador_id, categoria, setor, regiao, data_abertura FROM chamados WHERE id=?", (chamado_id,))
        chamado = c.fetchone()
        conn.close()
        
        socketio.emit('novo_chamado', {'id': chamado[0], 'solicitador_id': chamado[1], 'categoria': chamado[2], 'setor': chamado[3], 'regiao': chamado[4], 'data_abertura': chamado[5]}, namespace='/tecnico')
        return redirect("/dashboard")
    return render_template("abrir_chamado.html")

@app.route("/fechar_chamado/<int:chamado_id>", methods=["POST"])
def fechar_chamado(chamado_id):
    if "role" not in session or session["role"] != "solicitador":
        return redirect("/login")
    solucao = request.form.get("solucao")
    conn = sqlite3.connect('chamados.db')
    c = conn.cursor()
    c.execute("UPDATE chamados SET fechado_solicitador=1, solucao_solicitador=?, data_fechamento_solicitador=datetime('now') WHERE id=? AND solicitador_id=?",
              (solucao, chamado_id, session["username"]))
    c.execute("SELECT fechado_tecnico FROM chamados WHERE id=?", (chamado_id,))
    if c.fetchone()[0]:
        c.execute("UPDATE chamados SET status='fechado', data_fechamento=datetime('now') WHERE id=?", (chamado_id,))
    conn.commit()
    conn.close()
    return redirect("/dashboard")

@app.route("/fechar_chamado_tecnico/<int:chamado_id>", methods=["POST"])
def fechar_chamado_tecnico(chamado_id):
    if "role" not in session or session["role"] != "tecnico":
        return redirect("/login")
    tratativa = request.form.get("tratativa")
    troca_pecas = request.form.get("troca_pecas")
    qual_peca = request.form.get("qual_peca", "")
    nome_marca_peca = request.form.get("nome_marca_peca", "")
    fluxo_errado = 1 if request.form.get("fluxo_errado") == "on" else 0
    
    conn = sqlite3.connect('chamados.db')
    c = conn.cursor()
    c.execute("UPDATE chamados SET fechado_tecnico=1, tratativa_tecnico=?, troca_pecas=?, qual_peca=?, nome_marca_peca=?, fluxo_errado=?, data_fechamento_tecnico=datetime('now') WHERE id=?",
              (tratativa, troca_pecas, qual_peca, nome_marca_peca, fluxo_errado, chamado_id))
    c.execute("SELECT fechado_solicitador FROM chamados WHERE id=?", (chamado_id,))
    if c.fetchone()[0]:
        c.execute("UPDATE chamados SET status='fechado', data_fechamento=datetime('now') WHERE id=?", (chamado_id,))
    conn.commit()
    conn.close()
    return redirect("/dashboard")

if __name__ == "__main__":
    socketio.run(app, host="localhost", port=5000, debug=True)