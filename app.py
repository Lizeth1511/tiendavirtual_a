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
# Ruta de productos
productos = [
    {"id": 1, "nombre": "Laptop", "precio": 1200.50, "stock": 10},
    {"id": 2, "nombre": "Mouse", "precio": 25.99, "stock": 50}
]

@app.route('/productos')
def mostrar_productos():
     productos = Producto.query.all()
    return render_template('productos.html', productos=productos)
    app.run(host='dpg-d02v0sjuibrs73b8u6u0-a', port=5432)
    
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

@app.route('/productos/<id>', methods=['GET'])
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

@app.route('/agregar_producto', methods=['POST'])
def agregar_producto():
    if request.method == 'POST':
        try:
            nuevo_producto = Producto(
                nombre=request.form['nombre'],
                precio=float(request.form['precio']),
                descripcion=request.form['descripcion'],
                stock=int(request.form['stock'])
            )
            db.session.add(nuevo_producto)
            db.session.commit()
            flash('Producto agregado exitosamente', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al agregar producto: {str(e)}', 'error')
    return redirect(url_for('mostrar_productos'))

@app.route('/editar_producto/<int:id>', methods=['GET', 'POST'])
def editar_producto(id):
    producto = Producto.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            producto.nombre = request.form['nombre']
            producto.precio = float(request.form['precio'])
            producto.descripcion = request.form['descripcion']
            producto.stock = int(request.form['stock'])
            db.session.commit()
            flash('Producto actualizado exitosamente', 'success')
            return redirect(url_for('mostrar_productos'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar: {str(e)}', 'error')
    
    return render_template('productos.html', producto=producto)

@app.route('/eliminar-producto/<int:id>', methods=['POST'])
def eliminar_producto(id):
    producto = Producto.query.get_or_404(id)
    try:
        db.session.delete(producto)
        db.session.commit()
        flash('Producto eliminado exitosamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar: {str(e)}', 'error')
    return redirect(url_for('mostrar_productos'))
    cur.close()
    conn.close()
    return render_template('editar_producto.html', producto=producto)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=False)
