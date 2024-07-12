from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_mysqldb import MySQL
import bcrypt

app = Flask(__name__)
app.secret_key = '123'

# Configurando o MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'db_lsp'
mysql = MySQL(app)

# Listas de treinos por categoria
trainings = {
    'Peito': ['Supino Reto', 'Supino Inclinado', 'Crucifixo', 'Flexão de Braço', 'Pull Over', 'Peck Deck', 'Supino Declinado', 'Cross Over', 'Flexão Diamante', 'Supino com Halteres'],
    'Costas': ['Remada Curvada', 'Puxada Frontal', 'Remada Unilateral', 'Levantamento Terra', 'Barra Fixa', 'Pulldown', 'Remada Cavalinho', 'Puxada Inversa', 'Remada Alta', 'Pullover Costas'],
    'Ombros': ['Desenvolvimento com Halteres', 'Elevação Lateral', 'Elevação Frontal', 'Desenvolvimento Arnold', 'Encolhimento', 'Elevação Lateral Inclinado', 'Elevação Posterior', 'Desenvolvimento Militar', 'Crucifixo Invertido', 'Press Arnold'],
    'Braços': ['Rosca Direta', 'Rosca Martelo', 'Tríceps Testa', 'Tríceps Pulley', 'Rosca Concentrada', 'Rosca Scott', 'Rosca Inversa', 'Tríceps Corda', 'Rosca Alternada', 'Tríceps Francês'],
    'Abdômen': ['Crunch', 'Abdominal Reverso', 'Prancha', 'Bicicleta no Ar', 'Elevação de Pernas', 'Russian Twist', 'Abdominal Oblíquo', 'Abdominal com Bola', 'Abdominal V-up', 'Abdominal Infra'],
    'Pernas': ['Agachamento Livre', 'Leg Press', 'Afundo', 'Extensão de Pernas', 'Flexão de Pernas', 'Stiff', 'Levantamento Terra', 'Agachamento Sumô', 'Passada', 'Panturrilha em Pé']
}

# Rota principal
@app.route('/')
def index():
    return render_template('login.html')

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password'].encode('utf-8')

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM user WHERE email = %s", (email,))
        user = cur.fetchone()
        cur.close()

        if user:
            if bcrypt.checkpw(password, user[3].encode('utf-8')):
                session['email'] = email
                return redirect(url_for('dashboard'))
            else:
                flash('Senha incorreta', 'error')
                return render_template('login.html')
        else:
            flash('E-mail não registrado', 'error')
            return render_template('login.html')

    return render_template('login.html')

#Perfil
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'email' in session:
        email = session['email']
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM user WHERE email = %s", (email,))
        user = cur.fetchone()
        cur.close()

        if user:
            success = False
            if request.method == 'GET':
                # Exibir o formulário de edição de perfil
                return render_template('profile.html', user=user, success=success)
            elif request.method == 'POST':
                # Atualizar os dados do perfil
                name = request.form['name']
                peso = request.form['peso']
                altura = request.form['altura']
                idade = request.form['idade']
                tipo_sanguineo = request.form['tipo_sanguineo']
                medida_biceps = request.form['medida_biceps']
                medida_cintura = request.form['medida_cintura']
                medida_panturrilhas = request.form['medida_panturrilhas']
                medida_ombros = request.form['medida_ombros']
    

                cur = mysql.connection.cursor()
                cur.execute("""
                    UPDATE user
                    SET name = %s, peso = %s, altura = %s, idade = %s, tipo_sanguineo = %s, medida_biceps = %s, medida_cintura = %s, medida_panturrilhas = %s, medida_ombros = %s
                    WHERE email = %s
                """, (name, peso, altura, idade, tipo_sanguineo, medida_biceps, medida_cintura, medida_panturrilhas, medida_ombros, email))
                mysql.connection.commit()
                cur.close()

                # Definir a variável de sucesso como True
                success = True

                # Redirecionar de volta para a página de perfil com a mensagem de sucesso
                return redirect(url_for('profile', success=success))
        else:
            return jsonify({"message": "User not found"}), 404
    else:
        return jsonify({"message": "User not logged in"}), 401

# Registro
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['text']
        email = request.form['email']
        password = request.form['password'].encode('utf-8')

        terms_accepted = 'terms' in request.form

        if not terms_accepted:
            flash('Você deve aceitar os termos e condições!', 'error')
            return redirect(url_for('register'))

        # Verificar se o e-mail já está registrado
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM user WHERE email = %s", (email,))
        existing_user = cur.fetchone()
        
        if existing_user:
            cur.close()
            flash("O e-mail já está registrado", "error")
            return redirect(url_for('register'))

        # Hash da senha
        hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())

        # Inserir o novo usuário
        cur.execute("INSERT INTO user (name, email, password) VALUES (%s, %s, %s)", (name, email, hashed_password))
        mysql.connection.commit()
        cur.close()

        # Definir a sessão do usuário
        session['email'] = email
        return redirect(url_for('dashboard'))

    return render_template('register.html')

# Dashboard
@app.route('/dashboard')
def dashboard():
    if 'email' not in session:
        return redirect(url_for('login'))
    else:
        return render_template('dashboard.html')

# Deslogar
@app.route('/logout')
def logout():
    session.pop('email', None)
    return redirect(url_for('login'))

# Termos
@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/criar_treino', methods=['GET', 'POST'])
def criar_treino():
    if request.method == 'POST':
        selected_trainings = []
        for category in trainings.keys():
            selected_exercises = request.form.getlist(category)
            for exercise in selected_exercises:
                # Consultar o banco de dados para obter detalhes do exercício
                cur = mysql.connection.cursor()
                cur.execute("SELECT name, description, image_url FROM exercises WHERE name = %s", (exercise,))
                exercise_data = cur.fetchone()
                cur.close()

                if exercise_data:
                    selected_trainings.append({
                        'name': exercise_data[0],
                        'description': exercise_data[1],
                        'image_url': exercise_data[2]
                    })

        return render_template('selected_trainings.html', selected_trainings=selected_trainings)
    
    return render_template('criar_treino.html', trainings=trainings)


@app.route('/desafio7d')
def desafio7d():
    return render_template('desafio7d.html')

@app.route('/desafio15d')
def desafio15d():
    return render_template('desafio15d.html')

@app.route('/desafio20d')
def desafio20d():
    return render_template('desafio20d.html')

@app.route('/desafio30d')
def desafio30d():
    return render_template('desafio30d.html')

@app.route('/desafios')
def desafios():
    return render_template('desafios.html')

@app.route('/evolucao', methods=['GET', 'POST'])
def evolucao():
    if 'email' not in session:
        return redirect(url_for('login'))
    else:
        email = session['email']
        cur = mysql.connection.cursor()
        cur.execute("SELECT mes, biceps, panturilha, ombro, cintura FROM evolution_progress WHERE email = %s ORDER BY mes ASC", (email,))
        data = cur.fetchall()
        cur.close()

        meses = []
        biceps = []
        panturilha = []
        ombro = []
        cintura = []

        for row in data:
            meses.append(row[0])
            biceps.append(row[1])
            panturilha.append(row[2])
            ombro.append(row[3])
            cintura.append(row[4])

        return render_template('evolucao.html', meses=meses, biceps=biceps, panturilha=panturilha, ombro=ombro, cintura=cintura)

@app.route('/salvar_medidas', methods=['POST'])
def salvar_medidas():
    if 'email' not in session:
        return redirect(url_for('login'))
    else:
        email = session['email']
        mes = request.form['mes']
        biceps = request.form['biceps']
        panturilha = request.form['panturilha']
        ombro = request.form['ombro']
        cintura = request.form['cintura']

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO evolution_progress (email, mes, biceps, panturilha, ombro, cintura) VALUES (%s, %s, %s, %s, %s, %s)", (email, mes, biceps, panturilha, ombro, cintura))
        mysql.connection.commit()
        cur.close()

        return redirect(url_for('evolucao'))

if __name__ == '__main__':
    app.run(debug=True)
