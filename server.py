"""
COMS4111 - Intro to Databases
Project Part 3 
by Karin Novelia (kn2596)
and Gianna Cilluffo (gpc2128)
"""

import os
  # accessible as a variable in index.html:
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)

#Database Information
DATABASE_USERNAME = "kn2596"
DATABASE_PASSWRD = "930421"
DATABASE_HOST = "35.212.75.104"
DATABASEURI = f"postgresql://kn2596:930421@35.212.75.104/proj1part2"

#Database engine
engine = create_engine(DATABASEURI)

with engine.connect() as conn:
	create_table_command = """
	CREATE TABLE IF NOT EXISTS input (
		name text
	)
	"""
	res = conn.execute(text(create_table_command))
	conn.commit()
	
@app.before_request
def before_request():
    try:
        g.conn = engine.connect()
    except:
        print("uh oh, problem connecting to database")
        import traceback; traceback.print_exc()
        g.conn = None

@app.teardown_request
def teardown_request(exception):
    try:
        g.conn.close()
    except Exception as e:
        pass

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/ingredient')
def ingredient():
    return render_template("ingredient.html")

@app.route('/recipe')
def recipe():

    count_query = "SELECT count(*) FROM input"
    cursor = g.conn.execute(text(count_query))

    res = cursor.fetchone()
    
    count = []
    for result in res:
        count.append(result)

    if count[0] > 0:
        select_query = "SELECT name from input"
        cursor = g.conn.execute(text(select_query))
    elif count[0] <= 0:
        select_query = "SELECT name from recipes"
        cursor = g.conn.execute(text(select_query))

    names = []

    for result in cursor:
        names.append(result[0])
    cursor.close()

    context = dict(data = names)

    return render_template("recipe.html", **context)
	
#adding ingredient-specific search	
@app.route('/ingredient_search')
def ingr_search_page():
    return render_template("ingredient_search.html")

@app.route('/ingredient_search', methods=['POST'])
def ingredient_search():
    ingredient_name = request.form.get('ingredient_name')

    #search for recipes based on ingredient
    query = """
    SELECT r.name 
    FROM recipes r 
    JOIN recipe_ingredients ri ON r.recipe_id = ri.recipe_id
    JOIN ingredients i ON ri.ingredient_id = i.ingredient_id
    WHERE i.name ILIKE :ingredient_name
    """
    results = g.conn.execute(text(query), ingredient_name='%{}%'.format(ingredient_name))
    recipe_names = [row[0] for row in results]
    results.close()

    # Pass the recipe names to the search results template
    return render_template('search_results.html', recipes=recipe_names)


@app.route('/search', methods=['POST'])
def search():

    # clearing previous inputs
    empty_input = """
    DELETE FROM input
    """
    g.conn.execute(text(empty_input))
    g.conn.commit()
    # accessing form inputs from user
    name = request.form['name']

    # passing params in for each variable into query
    params = {}
    params["new_name"] = name
    g.conn.execute(text('INSERT INTO input(name) VALUES (:new_name)'), params)
    g.conn.commit()

    match_query = """
    SELECT name FROM recipes, input
    WHERE recipes.name = input.name
    """
    cursor = g.conn.execute(text(match_query))

    matches = []
    for result in cursor:
        matches.append(result[0])
    cursor.close()

    context = dict(data = names)

    return redirect("recipe.html", **context)

if __name__ == "__main__":
	import click

	@click.command()
	@click.option('--debug', is_flag=True)
	@click.option('--threaded', is_flag=True)
	@click.argument('HOST', default='0.0.0.0')
	@click.argument('PORT', default=8111, type=int)
	def run(debug, threaded, host, port):
		"""
		This function handles command line parameters.
		Run the server using:

			python server.py

		Show the help text using:

			python server.py --help

		"""

		HOST, PORT = host, port
		print("running on %s:%d" % (HOST, PORT))
		app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)

run()

