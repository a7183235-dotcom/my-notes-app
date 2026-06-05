from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt
import MySQLdb.cursors

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# MySQL Config
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Root@1234'  # നിങ്ങളുടെ MySQL password
app.config['MYSQL_DB'] = 'notesdb'

mysql = MySQL(app)
bcrypt = Bcrypt(app)

# ------------------- AUTH -------------------

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, 'user')", (username, password))
        mysql.connection.commit()
        cur.close()
        flash('Account created! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()
        if user and bcrypt.check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            return redirect(url_for('dashboard'))
        flash('Invalid credentials!', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ------------------- DASHBOARD -------------------

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if request.method == 'POST':
        content = request.form['content']
        cur.execute("INSERT INTO notes (user_id, content) VALUES (%s, %s)", (session['user_id'], content))
        mysql.connection.commit()
    cur.execute("SELECT * FROM notes WHERE user_id = %s", (session['user_id'],))
    notes = cur.fetchall()
    cur.close()
    return render_template('dashboard.html', notes=notes)

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if request.method == 'POST':
        content = request.form['content']
        cur.execute("UPDATE notes SET content = %s WHERE id = %s AND user_id = %s", (content, id, session['user_id']))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('dashboard'))
    cur.execute("SELECT * FROM notes WHERE id = %s AND user_id = %s", (id, session['user_id']))
    note = cur.fetchone()
    cur.close()
    return render_template('edit.html', note=note)

@app.route('/delete/<int:id>')
def delete(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM notes WHERE id = %s AND user_id = %s", (id, session['user_id']))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('dashboard'))

# ------------------- ADMIN -------------------

@app.route('/admin')
def admin():
    if session.get('role') != 'admin':
        return redirect(url_for('dashboard'))
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM users")
    users = cur.fetchall()
    cur.execute("SELECT * FROM notes")
    notes = cur.fetchall()
    cur.close()
    return render_template('admin.html', users=users, notes=notes)

@app.route('/admin/delete_user/<int:id>')
def delete_user(id):
    if session.get('role') != 'admin':
        return redirect(url_for('dashboard'))
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM notes WHERE user_id = %s", (id,))
    cur.execute("DELETE FROM users WHERE id = %s", (id,))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('admin'))

# ------------------- HEALTH -------------------

@app.route('/health')
def health():
    return {'status': 'healthy', 'version': '1.0.0'}

if __name__ == '__main__':
    app.run(debug=True)