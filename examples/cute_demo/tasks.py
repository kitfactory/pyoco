import time
import random
from pyoco.dsl.syntax import task

@task
def gather_ingredients(ctx):
    print("  🥕 Gathering carrots...")
    time.sleep(0.5)
    print("  🥔 Gathering potatoes...")
    time.sleep(0.5)
    return ["carrot", "potato", "onion"]

@task
def chop_vegetables(ctx, ingredients):
    print(f"  🔪 Chopping {', '.join(ingredients)}...")
    time.sleep(1.0)
    return "chopped_veggies"

@task
def boil_water(ctx):
    print("  🔥 Boiling water...")
    time.sleep(1.5)
    return "boiling_water"

@task
def make_curry(ctx, veggies, water):
    print("  🍲 Simmering curry...")
    time.sleep(2.0)
    return "delicious_curry"

@task
def cook_rice(ctx):
    print("  🍚 Cooking rice...")
    time.sleep(2.0)
    return "steaming_rice"

@task
def serve(ctx, curry, rice):
    print("  🍽️  Serving curry and rice!")
    return "Happy Meal"
