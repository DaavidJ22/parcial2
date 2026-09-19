from flask import Flask, flash, redirect, render_template, request, url_for
from psycopg2.errors import UniqueViolation
from psycopg2.extras import RealDictCursor

from db import get_connection


app = Flask(__name__)
app.secret_key = "clave-para-mensajes-flash"


@app.route("/")
def inicio():
    return render_template("inicio.html")


@app.route("/productos")
def productos():
    buscar = request.args.get("buscar", "").strip()
    connection = get_connection()
    cursor = connection.cursor(cursor_factory=RealDictCursor)
    try:
        if buscar:
            patron = f"%{buscar}%"
            cursor.execute(
                """SELECT * FROM productos
                   WHERE codigo ILIKE %s OR nombre ILIKE %s OR categoria ILIKE %s
                   ORDER BY id DESC""",
                (patron, patron, patron),
            )
        else:
            cursor.execute("SELECT * FROM productos ORDER BY id DESC")
        registros = cursor.fetchall()
    finally:
        cursor.close()
        connection.close()
    return render_template("productos.html", productos=registros, buscar=buscar)


@app.route("/productos/nuevo", methods=["GET", "POST"])
def producto_nuevo():
    if request.method == "POST":
        datos = {
            "codigo": request.form.get("codigo", "").strip(),
            "nombre": request.form.get("nombre", "").strip(),
            "categoria": request.form.get("categoria", "").strip(),
            "precio": request.form.get("precio") or "0",
            "existencia": request.form.get("existencia") or "0",
            "activo": "activo" in request.form,
        }
        if not datos["codigo"] or not datos["nombre"]:
            flash("El código y el nombre son obligatorios.", "error")
            return render_template("producto_form.html", producto=None, datos=datos)

        connection = get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute(
                """INSERT INTO productos (codigo, nombre, categoria, precio, existencia, activo)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (datos["codigo"], datos["nombre"], datos["categoria"],
                 datos["precio"], datos["existencia"], datos["activo"]),
            )
            connection.commit()
        except UniqueViolation:
            connection.rollback()
            flash("Ese código ya existe. Ingresa uno diferente.", "error")
            return render_template("producto_form.html", producto=None, datos=datos)
        finally:
            cursor.close()
            connection.close()

        flash("Producto registrado correctamente.", "exito")
        return redirect(url_for("productos"))

    return render_template("producto_form.html", producto=None)


@app.route("/productos/editar/<int:id>", methods=["GET", "POST"])
def producto_editar(id):
    if request.method == "POST":
        datos = {
            "codigo": request.form.get("codigo", "").strip(),
            "nombre": request.form.get("nombre", "").strip(),
            "categoria": request.form.get("categoria", "").strip(),
            "precio": request.form.get("precio") or "0",
            "existencia": request.form.get("existencia") or "0",
            "activo": "activo" in request.form,
        }
        if not datos["codigo"] or not datos["nombre"]:
            flash("El código y el nombre son obligatorios.", "error")
            return render_template("producto_form.html", producto={"id": id}, datos=datos)

        connection = get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute(
                """UPDATE productos
                   SET codigo=%s, nombre=%s, categoria=%s, precio=%s,
                       existencia=%s, activo=%s
                   WHERE id=%s""",
                (datos["codigo"], datos["nombre"], datos["categoria"],
                 datos["precio"], datos["existencia"], datos["activo"], id),
            )
            actualizado = cursor.rowcount > 0
            connection.commit()
        except UniqueViolation:
            connection.rollback()
            flash("Ese código ya existe. Ingresa uno diferente.", "error")
            return render_template("producto_form.html", producto={"id": id}, datos=datos)
        finally:
            cursor.close()
            connection.close()

        flash("Producto actualizado correctamente." if actualizado else "Producto no encontrado.",
              "exito" if actualizado else "error")
        return redirect(url_for("productos"))

    connection = get_connection()
    cursor = connection.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("SELECT * FROM productos WHERE id=%s", (id,))
        producto = cursor.fetchone()
    finally:
        cursor.close()
        connection.close()

    if producto is None:
        flash("Producto no encontrado.", "error")
        return redirect(url_for("productos"))
    return render_template("producto_form.html", producto=producto)


@app.route("/productos/eliminar/<int:id>", methods=["POST"])
def producto_eliminar(id):
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("DELETE FROM productos WHERE id=%s", (id,))
        eliminado = cursor.rowcount > 0
        connection.commit()
    finally:
        cursor.close()
        connection.close()

    flash("Producto eliminado correctamente." if eliminado else "Producto no encontrado.",
          "exito" if eliminado else "error")
    return redirect(url_for("productos"))


if __name__ == "__main__":
    app.run(debug=True)
