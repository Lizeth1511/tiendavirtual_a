from flask import Flask, flash, jsonify, render_template, request, redirect, session, url_for
import psycopg2
import psycopg2.extras
import bcrypt
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "fallback_clave_insegura")

# Configuración PostgreSQL (Render)
DATABASE_URL = "postgresql://mi_db_tienda_user:B4hlIBoTMql6XLr3pz02BdPmx0bHtE7L@dpg-d02v0sjuibrs73b8u6u0-a.ohio-postgres.render.com/mi_db_tienda"

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)

def create_tables():
    """Crear tablas si no existen"""
    commands = (
        """
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            correo VARCHAR(255) UNIQUE NOT NULL,
            contrasena VARCHAR(255) NOT NULL,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS productos (
            id SERIAL PRIMARY KEY,
            nombre VARCHAR(255) NOT NULL,
            descripcion TEXT,
            precio DECIMAL(10, 2) NOT NULL,
            stock INTEGER NOT NULL,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            usuario_id INTEGER REFERENCES usuarios(id)
        )
        """
    )
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        for command in commands:
            cur.execute(command)
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error al crear tablas: {e}")

class Usuario:
    @staticmethod
    def registrar(correo, contrasena):
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT correo FROM usuarios WHERE correo = %s", (correo,))
            if cur.fetchone():
                return False
            
            hashed = bcrypt.hashpw(contrasena.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            cur.execute(
                "INSERT INTO usuarios (correo, contrasena) VALUES (%s, %s) RETURNING id", 
                (correo, hashed)
            )
            user_id = cur.fetchone()['id']
            conn.commit()
            cur.close()
            conn.close()
            return user_id
        except Exception as e:
            print("Error al registrar:", e)
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
                return usuario
        except Exception as e:
            print("Error al iniciar sesión:", e)
        return None

class Producto:
    @staticmethod
    def obtener_todos(usuario_id=None):
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            
            if usuario_id:
                cur.execute("SELECT * FROM productos WHERE usuario_id = %s ORDER BY id", (usuario_id,))
            else:
                cur.execute("SELECT * FROM productos ORDER BY id")
                
            productos = cur.fetchall()
            cur.close()
            conn.close()
            return productos
        except Exception as e:
            print("Error al obtener productos:", e)
            return []

    @staticmethod
    def obtener_por_id(id):
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT * FROM productos WHERE id = %s", (id,))
            producto = cur.fetchone()
            cur.close()
            conn.close()
            return producto
        except Exception as e:
            print("Error al obtener producto:", e)
            return None

    @staticmethod
    def crear(nombre, descripcion, precio, stock, usuario_id):
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                """INSERT INTO productos (nombre, descripcion, precio, stock, usuario_id) 
                VALUES (%s, %s, %s, %s, %s) RETURNING id""",
                (nombre, descripcion, precio, stock, usuario_id)
            )
            producto_id = cur.fetchone()['id']
            conn.commit()
            cur.close()
            conn.close()
            return producto_id
        except Exception as e:
            print("Error al crear producto:", e)
            return False

    @staticmethod
    def actualizar(id, nombre, descripcion, precio, stock):
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                """UPDATE productos 
                SET nombre = %s, descripcion = %s, precio = %s, stock = %s 
                WHERE id = %s""",
                (nombre, descripcion, precio, stock, id)
            )
            conn.commit()
            cur.close()
            conn.close()
            return True
        except Exception as e:
            print("Error al actualizar producto:", e)
            return False

    @staticmethod
    def eliminar(id):
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM productos WHERE id = %s", (id,))
            conn.commit()
            cur.close()
            conn.close()
            return True
        except Exception as e:
            print("Error al eliminar producto:", e)
            return False

# Rutas de la aplicación
@app.route('/')
def inicio():
    # Mostrar login/registro si no está autenticado
    if 'logueado' in session:
        return redirect('/productos')
    return render_template('login.html')  

@app.route('/login', methods=['GET', 'POST'])  # Agregar método GET
def login():
    if request.method == 'GET':
      return render_template('login.html')
    
    # El resto del código POST existente...

@app.route('/registro', methods=['GET', 'POST'])  # Agregar método GET
def registro():
    if request.method == 'GET':
        return render_template('login.html')  

@app.route('/nuevo_producto')
def nuevo_producto():
    if 'logueado' not in session:
        return redirect('/login')
    return render_template('nuevo_producto.html')

@app.route('/productos')
def mostrar_productos():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM productos")
        productos = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        print("Error al obtener productos:", e)
        productos = []
    
    return render_template('productos.html', productos=productos)

@app.route('/agregar_producto', methods=['POST'])
def agregar_producto():
    if 'logueado' not in session:
        flash('Debes iniciar sesión para realizar esta acción', 'error')
        return redirect(url_for('inicio'))
    
    nombre = request.form['nombre'].strip()
    descripcion = request.form['descripcion'].strip()
    precio = request.form['precio'].strip()
    stock = request.form['stock'].strip()
    usuario_id = session['usuario_id']

    # Validaciones
    if not nombre or not precio or not stock:
        flash('Todos los campos requeridos deben estar llenos', 'error')
        return redirect(url_for('mostrar_productos'))

    try:
        precio = float(precio)
        stock = int(stock)
        if precio <= 0 or stock < 0:
            raise ValueError
    except ValueError:
        flash('Datos numéricos inválidos', 'error')
        return redirect(url_for('mostrar_productos'))

    if Producto.crear(nombre, descripcion, precio, stock, usuario_id):
        flash('Producto creado exitosamente', 'success')
    else:
        flash('Error al crear el producto', 'error')
    
    return redirect(url_for('mostrar_productos'))


@app.route('/editar_producto/<int:id>', methods=['GET', 'POST'])
def editar_producto(id):
    if 'logueado' not in session:
        return redirect('/')
    
    producto = Producto.obtener_por_id(id)
    
    if not producto:
        flash('Producto no encontrado', 'error')
        return redirect('/productos')
    
    if request.method == 'POST':
        nombre = request.form['nombre'].strip()
        descripcion = request.form['descripcion'].strip()
        precio = float(request.form['precio'])
        stock = int(request.form['stock'])

        if not nombre or not precio or stock < 0:
            flash('Datos del producto inválidos', 'error')
            return redirect(f'/editar_producto/{id}')

        if Producto.actualizar(id, nombre, descripcion, precio, stock):
            flash('Producto actualizado exitosamente', 'success')
            return redirect('/productos')
        else:
            flash('Error al actualizar producto', 'error')
    
    return render_template('editar_producto.html', producto=producto)

@app.route('/eliminar_producto/<int:id>', methods=['POST'])
def eliminar_producto(id):
    if 'logueado' not in session:
        return redirect('/')
    
    if Producto.eliminar(id):
        flash('Producto eliminado exitosamente', 'success')
    else:
        flash('Error al eliminar producto', 'error')
    
    return redirect('/productos')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    create_tables()
    app.run(debug=False)
