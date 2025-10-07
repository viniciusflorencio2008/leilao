from flask import Flask, request, jsonify, send_from_directory, g
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import sqlite3
import os
from PIL import Image
import io
import base64

# Configuração
DB = "bancodedadosleilao.sql"
UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

app = Flask(__name__, static_folder="static", static_url_path="/static")
CORS(app)

# JWT Configuração
app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "your-secret-key-here")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
jwt = JWTManager(app)

# diretorio
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# bancode dados
class DatabaseError(Exception):
    pass

def get_conn():
    if 'db' not in g:
        g.db = sqlite3.connect(DB)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON;")
    return g.db

@app.teardown_appcontext
def close_conn(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        conn = get_conn()
        with app.open_resource('schema.sql', mode='r') as f:
            conn.executescript(f.read().decode('utf8'))
        conn.commit()

# autenticação de rota 
@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data or "email" not in data or "senha" not in data:
        return jsonify({"error": "Email e senha são obrigatórios"}), 400

    try:
        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT * FROM Usuario WHERE email = ?", (data["email"],))
        user = c.fetchone()

        if user and check_password_hash(user["senha"], data["senha"]):
            # Check if user is admin
            c.execute("SELECT * FROM Admin WHERE id_usuario = ?", (user["id_usuario"],))
            is_admin = bool(c.fetchone())

            access_token = create_access_token(identity={
                "user_id": user["id_usuario"],
                "is_admin": is_admin
            })
            return jsonify({"token": access_token}), 200
        return jsonify({"error": "Credenciais inválidas"}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# manejamento do usuario
@app.route("/api/users/register", methods=["POST"])
def register_user():
    data = request.get_json()
    required = ["nome", "sobrenome", "email", "senha", "tipo"]
    if not all(k in data for k in required):
        return jsonify({"error": "Campos obrigatórios faltando"}), 400

    try:
        conn = get_conn()
        c = conn.cursor()

        # check do e-mail
        c.execute("SELECT id_usuario FROM Usuario WHERE email = ?", (data["email"],))
        if c.fetchone():
            return jsonify({"error": "Email já cadastrado"}), 409

        # criação do usuario
        c.execute("""
            INSERT INTO Usuario (nome, sobrenome, email, senha, data_cadastro)
            VALUES (?, ?, ?, ?, ?)
        """, (
            data["nome"],
            data["sobrenome"],
            data["email"],
            generate_password_hash(data["senha"]),
            datetime.utcnow().isoformat()
        ))
        user_id = c.lastrowid

        # tipos de usuario 
        if data["tipo"].lower() == "admin":
            c.execute("INSERT INTO Admin (id_usuario, nivel_acesso) VALUES (?, ?)",
                     (user_id, "básico"))
        else:
            c.execute("INSERT INTO Cliente (id_usuario, status) VALUES (?, ?)",
                     (user_id, "ativo"))

        conn.commit()
        return jsonify({"id_usuario": user_id}), 201

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/api/auctions", methods=["GET"])
def list_auctions():
    try:
        status = request.args.get("status")
        categoria = request.args.get("categoria")
        search = request.args.get("search")

        query = """
            SELECT 
                l.*, 
                c.nome AS carro_nome,
                c.marca,
                c.modelo,
                c.ano,
                c.preco_inicial,
                cat.nome AS categoria_nome,
                (SELECT COUNT(*) FROM Lance WHERE id_leilao = l.id_leilao) as total_lances,
                (SELECT MAX(valor) FROM Lance WHERE id_leilao = l.id_leilao) as lance_atual,
                (SELECT url_imagem FROM Imagem_Carro WHERE id_carro = c.id_carro AND principal = 1 LIMIT 1) as imagem_principal
            FROM Leilao l
            LEFT JOIN Carro c ON l.id_carro = c.id_carro
            LEFT JOIN Categoria cat ON c.id_categoria = cat.id_categoria
            WHERE 1=1
        """
        params = []

        if status:
            query += " AND l.status = ?"
            params.append(status)
        if categoria:
            query += " AND cat.id_categoria = ?"
            params.append(categoria)
        if search:
            query += " AND (c.nome LIKE ? OR c.marca LIKE ? OR c.modelo LIKE ?)"
            search_term = f"%{search}%"
            params.extend([search_term] * 3)

        query += " ORDER BY l.data_inicio DESC"

        conn = get_conn()
        c = conn.cursor()
        c.execute(query, params)
        auctions = [dict(row) for row in c.fetchall()]

        return jsonify(auctions), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/auctions/<int:auction_id>", methods=["GET"])
def get_auction(auction_id):
    try:
        conn = get_conn()
        c = conn.cursor()

        # Obter detalhes do leilão com informações relacionadas
        c.execute("""
            SELECT 
                l.*,
                c.*,
                cat.nome AS categoria_nome,
                (SELECT COUNT(*) FROM Lance WHERE id_leilao = l.id_leilao) as total_lances,
                (SELECT MAX(valor) FROM Lance WHERE id_leilao = l.id_leilao) as lance_atual,
                (SELECT json_group_array(json_object(
                    'id_lance', id_lance,
                    'valor', valor,
                    'data_hora', data_hora,
                    'id_cliente', id_cliente
                )) FROM Lance WHERE id_leilao = l.id_leilao ORDER BY valor DESC LIMIT 5) as ultimos_lances,
                (SELECT json_group_array(url_imagem) FROM Imagem_Carro WHERE id_carro = c.id_carro) as imagens
            FROM Leilao l
            LEFT JOIN Carro c ON l.id_carro = c.id_carro
            LEFT JOIN Categoria cat ON c.id_categoria = cat.id_categoria
            WHERE l.id_leilao = ?
        """, (auction_id,))

        auction = c.fetchone()
        if not auction:
            return jsonify({"error": "Leilão não encontrado"}), 404

        return jsonify(dict(auction)), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/auctions", methods=["POST"])
@jwt_required()
def create_auction():
    current_user = get_jwt_identity()
    if not current_user.get("is_admin"):
        return jsonify({"error": "Acesso não autorizado"}), 403

    try:
        data = request.form.to_dict()
        required = ["titulo", "descricao", "preco_minimo", "data_inicio", "data_fim"]
        if not all(k in data for k in required):
            return jsonify({"error": "Campos obrigatórios faltando"}), 400

        # Lidar com a criação do carro primeiro
        car_data = {
            "nome": data["carro_nome"],
            "marca": data["marca"],
            "modelo": data["modelo"],
            "ano": int(data["ano"]),
            "preco_inicial": float(data["preco_inicial"]),
            "id_categoria": int(data["id_categoria"]),
            "id_admin": current_user["user_id"]
        }

        conn = get_conn()
        c = conn.cursor()

        
        c.execute("""
            INSERT INTO Carro (nome, marca, modelo, ano, preco_inicial, id_categoria, id_admin)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            car_data["nome"], car_data["marca"], car_data["modelo"],
            car_data["ano"], car_data["preco_inicial"],
            car_data["id_categoria"], car_data["id_admin"]
        ))
        car_id = c.lastrowid

        # upload das imagenss
        images = request.files.getlist("images")
        for i, image in enumerate(images):
            if image and allowed_file(image.filename):
                # Process and save image
                filename = secure_filename(f"car_{car_id}_img_{i}.jpg")
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                
                # salvar imagem
                img = Image.open(image)
                img.thumbnail((800, 800))
                img.save(filepath, "JPEG", quality=85)

                
                c.execute("""
                    INSERT INTO Imagem_Carro (id_carro, url_imagem, principal)
                    VALUES (?, ?, ?)
                """, (car_id, f"/static/uploads/{filename}", 1 if i == 0 else 0))

     
        c.execute("""
            INSERT INTO Leilao (
                titulo, descricao, id_carro, data_inicio, data_fim,
                preco_minimo, incremento_minimo, status, id_admin
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data["titulo"],
            data["descricao"],
            car_id,
            data["data_inicio"],
            data["data_fim"],
            float(data["preco_minimo"]),
            float(data.get("incremento_minimo", 100.0)),
            "agendado",
            current_user["user_id"]
        ))

        conn.commit()
        return jsonify({"id_leilao": c.lastrowid}), 201

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/api/bids", methods=["POST"])
@jwt_required()
def place_bid():
    current_user = get_jwt_identity()
    
    try:
        data = request.get_json()
        if not data or "id_leilao" not in data or "valor" not in data:
            return jsonify({"error": "Campos obrigatórios faltando"}), 400

        conn = get_conn()
        c = conn.cursor()

       
        c.execute("SELECT id_cliente FROM Cliente WHERE id_usuario = ?", 
                 (current_user["user_id"],))
        client = c.fetchone()
        if not client:
            return jsonify({"error": "Usuário não é um cliente"}), 403

        
        c.execute("""
            SELECT l.*, 
                   (SELECT MAX(valor) FROM Lance WHERE id_leilao = l.id_leilao) as maior_lance
            FROM Leilao l 
            WHERE l.id_leilao = ?
        """, (data["id_leilao"],))
        
        auction = c.fetchone()
        if not auction:
            return jsonify({"error": "Leilão não encontrado"}), 404

        
        now = datetime.utcnow()
        if now < datetime.fromisoformat(auction["data_inicio"]):
            return jsonify({"error": "Leilão ainda não começou"}), 400
        if now > datetime.fromisoformat(auction["data_fim"]):
            return jsonify({"error": "Leilão já encerrado"}), 400
        if auction["status"] not in ["agendado", "aberto"]:
            return jsonify({"error": "Leilão não está aberto para lances"}), 400

        
        bid_value = float(data["valor"])
        current_highest = auction["maior_lance"] or auction["preco_minimo"]
        min_increment = float(auction["incremento_minimo"])

        if bid_value < current_highest + min_increment:
            return jsonify({
                "error": f"Lance deve ser pelo menos {min_increment} maior que o lance atual"
            }), 400

        
        c.execute("""
            INSERT INTO Lance (id_leilao, id_cliente, valor, status)
            VALUES (?, ?, ?, ?)
        """, (data["id_leilao"], client["id_cliente"], bid_value, "válido"))

       
        if auction["status"] == "agendado":
            c.execute("""
                UPDATE Leilao SET status = 'aberto'
                WHERE id_leilao = ?
            """, (data["id_leilao"],))

        conn.commit()
        return jsonify({"message": "Lance registrado com sucesso"}), 201

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Recurso não encontrado"}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({"error": "Erro interno do servidor"}), 500

# iniciar
if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)