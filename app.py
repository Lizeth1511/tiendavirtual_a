from flask import Flask, flash, jsonify, render_template, request, redirect, session, url_for
from flask_mysqldb import MySQL
import bcrypt

app = Flask(__name__)
app.secret_key = 'una_clave_supersecreta'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
import os

db_config = {
    'host': os.environ.get('DB_HOST'),
    'user': os.environ.get('DB_USER'),
    'password': os.environ.get('DB_PASSWORD'),
    'database': os.environ.get('DB_NAME')
}

mysql = MySQL(app)

import mysql.connector

# Datos proporcionados por ClearDB o el servicio de tu elección
db_config = {
    'host': 'tu-host-cleardb',
    'user': 'tu-usuario',
    'password': 'tu-contraseña',
    'database': 'tu-base-de-datos'
}

# Conexión a la base de datos
def get_db_connection():
    conn = mysql.connector.connect(**db_config)
    return conn
# Conexión y creación de tablas
def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS usuarios (
        id INT AUTO_INCREMENT PRIMARY KEY,
        correo VARCHAR(100) NOT NULL UNIQUE,
        contrasena VARCHAR(255) NOT NULL
    );
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS productos (
        id INT AUTO_INCREMENT PRIMARY KEY,
        nombre VARCHAR(100) NOT NULL,
        descripcion TEXT,
        precio DECIMAL(10,2),
        stock INT
    );
    ''')

    conn.commit()
    cursor.close()
    conn.close()
class Usuario:
    @staticmethod
    def registrar(correo, contrasena):
        try:
            cursor = mysql.connection.cursor()
            cursor.execute("SELECT correo FROM usuarios WHERE correo = %s", (correo,))
            if cursor.fetchone():
                return False
            
            hashed = bcrypt.hashpw(contrasena.encode('utf-8'), bcrypt.gensalt())
            cursor.execute(
                "INSERT INTO usuarios (correo, contrasena) VALUES (%s, %s)",
                (correo, hashed)
            )
            mysql.connection.commit()
            return True
        except Exception as e:
            print("Error:", e)
            return False

    @staticmethod
    def login(correo, contrasena):
        try:
            cursor = mysql.connection.cursor()
            cursor.execute("SELECT * FROM usuarios WHERE correo = %s", (correo,))
            usuario = cursor.fetchone()
             print("Usuario obtenido de BD:", usuario)
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
    print("Intentando login con:", correo)
    if not correo or not contrasena:
        return redirect('/')
    
    if Usuario.login(correo, contrasena):
        session['logueado'] = True
        session['correo'] = correo
        return redirect('/productos')  
    print("Login fallido")
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

@app.route('/productos')
def productos():
    if 'logueado' not in session:
        return redirect('/')
    
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM productos")
    productos = cursor.fetchall()
    return render_template('productos.html', productos=productos)



#API para los productos
@app.route('/tablas/<id>', methods=['GET'])
def leer_tablas(id):
    try:
        cursor = mysql.connection.cursor()
        sql = "SELECT id, nombre, descripcion, precio, stock FROM productos WHERE id = '{0}'".format(id)
        cursor.execute(sql)
        datos=cursor.fetchone()
        if datos != None:
            producto = {'id': datos[0],'nombre': datos[1],'descripcion': datos[2],'precio': datos[3],'stock': datos[4]}
            return jsonify({'producto': producto, 'mensaje':"Producto encontrado." })
        else:
            return jsonify({'mensaje':"Producto no encontrado." })
    except Exception as ex:
        return jsonify({'mensaje': "Error"})
    

@app.route('/productos', methods=['POST']) 
def registrar_producto():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        precio = request.form.get('precio')
        descripcion = request.form.get('descripcion')
        stock = request.form.get('stock')
        if not nombre :
          return "El campo nombre es obligatorio", 400
        cursor = mysql.connection.cursor()
        cursor.execute(
            """INSERT INTO productos 
            (nombre, precio, descripcion, stock) 
            VALUES ( %s, %s, %s, %s)""",
            (nombre, precio, descripcion, stock))
        mysql.connection.commit()
        return jsonify({'mensaje': 'Producto creado', 'id': cursor.lastrowid}), 201
    else:
        return jsonify({'mensaje': "Error"})    


@app.route('/eliminar_producto/<int:id>')
def eliminar_producto(id):
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM productos WHERE id = %s", (id,))
    mysql.connection.commit()
    flash('Producto eliminado correctamente')
    return redirect(url_for('productos'))


@app.route('/actualizar_producto/<int:id>', methods=['GET', 'POST'])
def actualizar_producto(id):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM productos WHERE id = %s", (id,))
    producto = cursor.fetchone()
    if not producto:
        return "Producto no encontrado", 404

    if request.method == 'POST':
        nombre = request.form['nombre']
        precio = request.form['precio']
        descripcion = request.form['descripcion']
        stock = request.form['stock']
        cursor.execute(
            """UPDATE productos 
            SET nombre = %s, precio = %s, descripcion = %s, stock = %s 
            WHERE id = %s""",
            (nombre, precio, descripcion, stock, id)
        )
        mysql.connection.commit()
        flash('Producto actualizado correctamente')
        return redirect(url_for('productos'))
    return render_template('editar_producto.html', producto=producto)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=False)
