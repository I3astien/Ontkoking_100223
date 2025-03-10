from flask import Flask, render_template, session, redirect, url_for, request, flash
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'yBggAEEUYOTIJCAEQABgKGIAEMgkIAhAAGAoYgAQyCQgDEAAYChiABDIJCAQQABgKGIAEMgkIBRAAGAoYgAQyCQgGEAAYChiABDIJCAcQABgKGIAEMgkICBAAGAoYgAQyCQgJEAAYChiABNIBCDM0MDhqMGoxqAIAsAIA'

UPLOAD_FOLDER = 'static/images/dishes'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def get_db_connection():
    conn = sqlite3.connect('db.sqlite')
    conn.row_factory = sqlite3.Row
    return conn

def get_recipes(user_id=None, selected_diet_ids=None):
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT r.id, r.name, r.time, r.image, r.ingredients, r.instructions 
        FROM recipes r
    """
    params = []
    
    if user_id:
        query += " WHERE r.user_id = ?"
        params.append(user_id)

    cursor.execute(query, params)
    recipes = cursor.fetchall()
    
    recipes_with_diets = []
    for recipe in recipes:
        cursor.execute("SELECT DietID FROM RecipeDiet WHERE RecipeID = ?", (recipe["id"],))
        diet_ids = [diet[0] for diet in cursor.fetchall()]
        recipes_with_diets.append(dict(recipe, diet_ids=diet_ids))

    conn.close()
    return recipes_with_diets

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dailyhome', methods=['GET', 'POST'])
def dailyhome():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DietID, DietName FROM Diets")
    diets = cursor.fetchall()
    conn.close()

    selected_diet_ids = request.form.getlist('diets') if request.method == 'POST' else None
    recipes = get_recipes(selected_diet_ids=selected_diet_ids)
    return render_template('dailyhome.html', recipes=recipes, diets=diets)

@app.route('/dailyhome2', methods=['GET', 'POST'])
def dailyhome2():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('index'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DietID, DietName FROM Diets")
    diets = cursor.fetchall()
    conn.close()

    selected_diet_ids = request.form.getlist('diets') if request.method == 'POST' else None
    recipes = get_recipes(user_id=user_id, selected_diet_ids=selected_diet_ids)
    return render_template('dailyhome2.html', recipes=recipes, diets=diets)

@app.route('/profiel')
def profiel():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('index'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()

    username = user["username"] if user else 'Guest'
    recipes = get_recipes(user_id)
    return render_template('profiel.html', username=username, recipes=recipes)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, password FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user and user['password'] == password:
            session['user_id'] = user['id']
            return redirect(url_for('profiel'))
        flash('Invalid username or password.')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            user_id = cursor.lastrowid
        
        session['user_id'] = user_id
        return redirect(url_for('profiel'))
    
    return render_template('register.html')

@app.route('/add_recipe', methods=['GET', 'POST'])
def add_recipe():
    if request.method == 'POST':
        user_id = session.get('user_id')
        if not user_id:
            return redirect(url_for('login'))

        name = request.form['name']
        time = request.form['time']
        ingredients = request.form['ingredients']
        instructions = request.form['instructions']
        selected_diets = request.form.getlist('diets')

        file = request.files['image']
        filename = secure_filename(file.filename) if file and file.filename else None
        if filename:
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO recipes (name, time, image, ingredients, instructions, user_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (name, time, filename, ingredients, instructions, user_id))
            recipe_id = cursor.lastrowid

            for diet_id in selected_diets:
                cursor.execute("INSERT INTO RecipeDiet (RecipeID, DietID) VALUES (?, ?)", (recipe_id, diet_id))

        return redirect(url_for('profiel'))

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DietID, DietName FROM Diets")
        diets = cursor.fetchall()

    return render_template('add_recipe.html', diets=diets)

if __name__ == '__main__':
    app.run(debug=True)