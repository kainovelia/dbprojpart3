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
from collections import Counter

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

#matching function
def match_level(pantry_ingredients, recipe_ingredients):
    pantry_counter = Counter(pantry_ingredients)
    recipe_counter = Counter(recipe_ingredients)
    
    common_ingredients = pantry_counter & recipe_counter
    pantry_missing = recipe_counter - pantry_counter
    
    if len(common_ingredients) == len(recipe_counter):
        return 'exact match'
    elif len(common_ingredients) > 0:
        return 'close match'
    else:
        return 'not-as-close match'
	
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
    select_query = "SELECT * FROM recipes"
    cursor = g.conn.execute(text(select_query))

    rows = []
    for row in cursor:
        rows.append(row)
    cursor.close()

    context = dict(data = rows)
    return render_template("index.html", **context)

@app.route('/ingredient')
def ingredient():
    return render_template("ingredient.html")

@app.route('/recipe')
def recipe():
    return render_template("recipe.html")

@app.route('/recipe/searchby', methods=['POST'])
def recipe_search():

    searchby = request.form['show']

    if searchby=="Show All Recipes":
        select_query = "SELECT * FROM recipes"
        cursor = g.conn.execute(text(select_query))

        rows = []
        for row in cursor:
            rows.append(row)
        cursor.close()

        context = dict(data = rows)
        return render_template("recipe.html", **context, search='all')
    elif searchby=="Search by Contributor":
        return render_template("recipe.html", search='contributor')
    elif searchby=="Search by Name":
        return render_template("recipe.html", search='name')
    elif searchby=="Search by Cuisine":
        return render_template("recipe.html", search='cuisine')

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
	
    exact_match_recipes = []
    close_match_recipes = []
    not_as_close_match_recipes = []

    for row in results:
	    recipe_id, recipe_name = row
	    recipe_ingredients = [] #get recipe ingredients!!
    #gotta fix above, finish sorting
    results.close()
	
    # Pass the recipe names to the search results template
    return render_template('search_results.html', recipes=recipe_names)

@app.route('/search', methods=['POST'])
def search():
    return redirect("/")

@app.route('/search_contributor', methods=['POST'])
def contributor():

    cont_name = request.form['name']

    id_query= f"""
    SELECT contributor_id FROM contributors
    WHERE name='{cont_name}'
    """

    cursor = g.conn.execute(text(id_query)) 
    cont_id=[]

    for row in cursor:
        cont_id.append(row[0])

    try:
        result_query = f"""
        SELECT * FROM recipes
        WHERE contributor_id='{cont_id[0]}'
        """

        cursor = g.conn.execute(text(result_query))

        rows = []

        for row in cursor:
            rows.append(row)
        cursor.close()
        context=dict(data=rows)
    except:

        context=dict(data=cont_id)
    
    return render_template("recipe.html", **context, search='contributor')
    
 







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

