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
    return render_template("ingredient_search.html")

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
    elif searchby=="Search by Rating":
        return render_template("recipe.html", search='rating')

    
#adding ingredient-specific search	
@app.route('/ingredient_search')
def ingr_search_page():
    return render_template("ingredient_search.html")

@app.route('/ingredient_search', methods=['POST'])
def ingredient_search():
    ingredient_name = request.form.get('ingredient_name')

    ingredients_list = [ingredient.strip() for ingredient in ingredient_name.split(',')]

    ingredient_ids = []

    for ingredient in ingredients_list:

        ingr_id_query = f"""
        SELECT ingredient_id FROM ingredients
        WHERE name = '{ingredient}'
        """
        cursor = g.conn.execute(text(ingr_id_query))
        for row in cursor:
            ingredient_ids.append(row)


    recipe_query_list =[]
    for item in ingredient_ids: 
        recipe_query = f"""
        (SELECT recipe_id, ingredient_id FROM uses_ingredients
        WHERE ingredient_id='{item[0]}')
        """
        recipe_query_list.append(recipe_query)
    
    join_query = "SELECT recipe_id, count(*) FROM ("

    join_query = join_query + recipe_query_list.pop()

    results_id = []

    for query in recipe_query_list:

        join_query = join_query + "UNION" + query

    join_query = join_query + ") GROUP BY recipe_id ORDER BY count(*) DESC"

    cursor = g.conn.execute(text(join_query))
        
    for row in cursor:
        results_id.append(row[0])

    final_rows = []
    for item in results_id:
        final_query = f"""
        SELECT * FROM recipes
        WHERE recipe_id = '{item}'
        """

        cursor = g.conn.execute(text(final_query))
        for row in cursor:
            final_rows.append(row)

    context=dict(data=final_rows)

    return render_template("/ingredient_search.html", **context)

@app.route('/search_contributor', methods=['POST'])
def contributor():

    cont_name = request.form['name']

    name = cont_name

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
    
    return render_template("recipe.html", **context, search='contributor', name='{cont_name}')
    
@app.route('/search_name', methods=['POST'])
def recipe_name():

    recipe_name = request.form['name']

    recipe_query= f"""
    SELECT * FROM recipes
    WHERE name='{recipe_name}'
    """

    cursor = g.conn.execute(text(recipe_query))

    rows = []

    for row in cursor:
        rows.append(row)
    cursor.close()
    context=dict(data=rows)

    return render_template("recipe.html", **context, search='name')

@app.route('/search_cuisine', methods=['POST'])
def cuisine():

    cuisine_name = request.form['name']

    cuisine_query= f"""
    SELECT * FROM recipes
    WHERE cuisine ='{cuisine_name}'
    """

    cursor = g.conn.execute(text(cuisine_query))

    rows = []

    for row in cursor:
        rows.append(row)
    cursor.close()
    context=dict(data=rows)

    return render_template("recipe.html", **context, search='cuisine')

@app.route('/search_rating', methods=['POST'])
def rating():
    rating = request.form['rating']

    recipe_id_query= f"""
    SELECT * FROM rate
    WHERE rating='{rating}'
    """

    cursor = g.conn.execute(text(recipe_id_query))

    recipe_id=[]

    for row in cursor:
        recipe_id.append(row[0])

    try:
        result_query = f"""
        SELECT * FROM recipes
        WHERE recipe_id='{recipe_id[0]}'
        """
        cursor = g.conn.execute(text(result_query))

        rows = []

        for row in cursor:
            rows.append(row)
        cursor.close()
        context=dict(data=rows)
    except:

        context=dict(data=recipe_id)

    return render_template("recipe.html", **context, search='rating')

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

