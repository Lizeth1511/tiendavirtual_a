from flask import Flask, flash, jsonify, render_template, request, redirect, session, url_for
import psycopg2
import psycopg2.extras
import bcrypt
import os

app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY", "fallback_clave_insegura")

# Configuración PostgreSQL
DATABASE_URL = os.environ.get("DATABASE_URL")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)

class Usuario:
    @staticmethod
    def registrar(correo, contrasena):
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT correo FROM usuarios WHERE correo = %s", (correo,))
            if cur.fetchone():
                return False
            
            hashed = bcrypt.hashpw(contrasena.encode('utf-8'), bcrypt.gensalt())
            cur.execute("INSERT INTO usuarios (correo, contrasena) VALUES (%s, %s)", (correo, hashed))
            conn.commit()
            cur.close()
            conn.close()
            return True
        except Exception as e:
            print("Error:", e)
            return False

    @staticmethod
    def login(correo, contrasena):
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT * FROM usuarios WHERE correo = %s", (correo,))
            usuario = cur.fetchone()
            cur.close()
            conn.close()
            if usuario and bcrypt.checkpw(contrasena.encode('utf-8'), usuario['contrasena'].encode('utf-8')):
                return True
        except Exception as e:
            print("Error:", e)
        return False

@app.route('/')
def inicio():
    if 'logueado' in session:
        return redirect('/productos')
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    correo = request.form['correo'].strip()
    contrasena = request.form['contrasena'].strip()

    if not correo or not contrasena:
          print("Correo o contraseña vacíos")
        
    if Usuario.login(correo, contrasena):
        session['logueado'] = True
        session['correo'] = correo
        return redirect('/productos')
    return redirect('/')

@app.route('/registro', methods=['POST'])
def registro():
    correo = request.form['correo'].strip()
    contrasena = request.form['contrasena'].strip()

    if not correo or not contrasena:
        return redirect('/')

    if Usuario.registrar(correo, contrasena):
        return redirect('/')
    return redirect('/')

@app.route('/tablas/<id>', methods=['GET'])
def leer_tablas(id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, nombre, descripcion, precio, stock FROM productos WHERE id = %s", (id,))
        datos = cur.fetchone()
        cur.close()
        conn.close()
        if datos:
            return jsonify({'producto': datos, 'mensaje': "Producto encontrado."})
        else:
            return jsonify({'mensaje': "Producto no encontrado."})
    except Exception as ex:
        return jsonify({'mensaje': "Error"})

@app.route('/productos', methods=['POST'])
def registrar_producto():
    nombre = request.form.get('nombre')
    precio = request.form.get('precio')
    descripcion = request.form.get('descripcion')
    stock = request.form.get('stock')

    if not nombre:
        return "El campo nombre es obligatorio", 400

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO productos (nombre, precio, descripcion, stock) VALUES (%s, %s, %s, %s)",
                (nombre, precio, descripcion, stock))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'mensaje': 'Producto creado'}), 201

@app.route('/eliminar_producto/<int:id>')
def eliminar_producto(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM productos WHERE id = %s", (id,))
    conn.commit()
    cur.close()
    conn.close()
    flash('Producto eliminado correctamente')
    return redirect(url_for('productos'))

@app.route('/actualizar_producto/<int:id>', methods=['GET', 'POST'])
def actualizar_producto(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM productos WHERE id = %s", (id,))
    producto = cur.fetchone()

    if not producto:
        return "Producto no encontrado", 404

    if request.method == 'POST':
        nombre = request.form['nombre']
        precio = request.form['precio']
        descripcion = request.form['descripcion']
        stock = request.form['stock']
        cur.execute("UPDATE productos SET nombre = %s, precio = %s, descripcion = %s, stock = %s WHERE id = %s",
                    (nombre, precio, descripcion, stock, id))
        conn.commit()
        flash('Producto actualizado correctamente')
        return redirect(url_for('productos'))

    cur.close()
    conn.close()
    return render_template('editar_producto.html', producto=producto)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=False)
