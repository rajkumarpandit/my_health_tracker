from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
import openai
import chromadb
import os
import json
from datetime import datetime
from app.models import db, UserMeal, FoodNutrient
from slugify import slugify 
from chromadb.config import Settings

bp = Blueprint('meal', __name__)

# Initialize OpenAI API key

print("Openai version:", openai.__version__)
print("Chromadb version:", chromadb.__version__)
print("Flask Environment:", os.getenv('FLASK_ENV'))
print("ChromaDB Path:", os.getenv('CHROMADB_PATH'))
client = openai.OpenAI(
  api_key=os.getenv('OPENAI_API_KEY')
)

def get_chroma_client():
    persist_directory = os.getenv('CHROMADB_PATH')
    chroma_client = chromadb.Client(Settings(
        persist_directory=persist_directory,
        is_persistent=True
    ))
    return chroma_client

def parse_meal_text(meal_text):
    """Parse meal text using OpenAI to extract food details."""
    # print("Inside parse_meal_text-->", meal_text)

    prompt = f"""Parse the following meal text and extract:
    1. Food name (e.g., 'boiled chicken')
    2. Quantity (e.g., '250')
    3. Unit type (e.g., 'gram' or 'piece')
    4. Measurement type ('weight' or 'count')
    The quantity could be in words, for example two for 2 or three for 3.
    
    Text: "{meal_text}"
    
    Return as JSON format:
    {{
        "food_name": "food name here",
        "quantity": number,
        "unit": "unit here",
        "measurement_type": "weight or count"
    }}"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            store=True,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that parses meal text into structured data. Only respond with valid JSON."},
                {"role": "user", "content": prompt}
            ]
        )
        # print('Came here')
        # print("OpenAI response:", response)
        return json.loads(response.choices[0].message.content)

    except Exception as e:
        print(f"[parse_meal_text] Error parsing meal text: {e}")
        return None


def get_nutrition_info(food_name, quantity, unit, measurement_type):
    """Get nutrition information for a food item."""
    print("\n" + "="*50)
    print("CHROMADB SEARCH DEBUG")
    print("="*50)
    
    try:
        # chroma_client = chromadb.Client()
        chroma_client = get_chroma_client()
        collection = chroma_client.get_or_create_collection(name="food_nutrients")
        
        # Standardize the food name for lookup
        food_id = food_name.lower().replace(" ", "_")
        print(f"Input food_name: {food_name}")
        print(f"Generated food_id: {food_id}")
        
        # First try exact match using get()
        try:
            print("\nAttempting exact match lookup...")
            results = collection.get(
                ids=[food_id],
                include=["documents", "metadatas"]
            )
            print(f"Exact match results: {results}")
            if results and results['documents'] and len(results['documents']) > 0:
                unit_nutrition_data = json.loads(results['documents'][0])
                print("Found exact match in ChromaDB:", unit_nutrition_data)
                return unit_nutrition_data
        except Exception as e:
            print(f"Exact match lookup failed: {e}")
        
        # If exact match fails, try similarity search
        try:
            print("\nAttempting similarity search...")
            results = collection.query(
                query_texts=[food_name],
                n_results=1,
                include=["documents", "metadatas", "distances"]
            )
            print(f"Similarity search raw results: {results}")

            if (results and results['documents'] and len(results['documents']) > 0):
                distance = float(results['distances'][0][0])
                print(f"\nSimilarity distance: {distance}")
                
                if distance < 0.5:
                    unit_nutrition_data = json.loads(results['documents'][0][0])
                    print("\nFound similar match in ChromaDB:", unit_nutrition_data)
                    return unit_nutrition_data
                else:
                    print(f"\tDistance {distance} exceeds threshold 0.5")
            
        except Exception as e:
            print(f"Similarity search failed: {e}")
            print(f"Results structure: {results if 'results' in locals() else 'No results'}")
        
        print("-"*50)    
        print("No matching food found in ChromaDB")
        print("-"*50)    
    except Exception as e:
        print(f"ChromaDB access error: {e}")

    # If no data found in ChromaDB, proceed with OpenAI call
    print(f"\nFetching nutrition data for {food_name} from OpenAI...\n")
    print("-"*50)    
    prompt = f"""Act as a professional nutritionist providing USDA-standard nutritional data for {food_name}. 
        The measurement type provided is: {measurement_type} (weight or count).

        Requirements:
        1. IF measurement_type is 'weight':
            - MUST use base_unit="grams"
            - MUST use base_quantity=100
        2. IF measurement_type is 'count':
            - MUST use base_unit="pieces"
            - MUST use base_quantity=1
            - Use standard edible portions (e.g., 1 slice for bread, 1 medium for fruits)

        Provide this nutritional data per base quantity:
        - Calories (kcal)
        - Protein (g)
        - Fat (g)
        - Carbohydrates (g)

        Return JSON response with this exact structure:
        {{
            "calories": <number|null>,
            "protein": <number|null>,
            "fat": <number|null>,
            "carbs": <number|null>,
            "base_quantity": <100 if weight, 1 if count>,
            "base_unit": <"grams" if weight, "pieces" if count>
        }}

        Example valid responses:
        For bread measured by count (per slice):
        {{
            "calories": 82,
            "protein": 3.2,
            "fat": 1.1,
            "carbs": 15.0,
            "base_quantity": 1,
            "base_unit": "pieces"
        }}

        For chicken breast measured by weight (per 100g):
        {{
            "calories": 165,
            "protein": 31.0,
            "fat": 3.6,
            "carbs": null,
            "base_quantity": 100,
            "base_unit": "grams"
        }}"""
    
    # print("Nutrition info fetching Prompt for OpenAI:", prompt)
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a nutrition expert. Provide accurate nutrition information in JSON format."},
                {"role": "user", "content": prompt}
            ]
        )
        raw_content = response.choices[0].message.content
        # print("Raw content before stripping:", raw_content)
        if raw_content.startswith("```") and raw_content.endswith("```"):
            raw_content = raw_content.strip("```").strip("json").strip()
            # print("Raw content after stripping:", raw_content)
        unit_nutrition_data = json.loads(raw_content)
        print("-"*50)
        print("Unit Nutrition data fetched from OpenAI:\n", unit_nutrition_data, "\n")

        
        return unit_nutrition_data
    except Exception as e:
        print(f"OpenAI error: {e}")
        return None

@bp.route('/record_meal', methods=['GET', 'POST'])
@login_required
def record_meal():
    if request.method == 'POST':
        meal_text = request.form.get('meal_text')
        if not meal_text:
            flash('Please enter what you ate.', 'error')
            return render_template('meal/record.html')

        parsed_data = parse_meal_text(meal_text)
        if not parsed_data:
            flash('Could not understand the meal description. Please try again.', 'error')
            return render_template('meal/record.html', meal_text=meal_text)  # Keep the meal_text

        # Step 2: Fetch unit nutrition data
        unit_nutrition_data = get_nutrition_info(
            parsed_data['food_name'],
            parsed_data['quantity'],
            parsed_data['unit'],
            parsed_data['measurement_type']
        )
        if not unit_nutrition_data:
            flash('Could not get nutrition information. Please try again.', 'error')
            return render_template('meal/record.html')

        # Step 3: Calculate scaled nutrition data
        factor = parsed_data['quantity'] / unit_nutrition_data['base_quantity']
        scaled_nutrition_data = {
            'calories': unit_nutrition_data['calories'] * factor,
            'protein': unit_nutrition_data['protein'] * factor,
            'fat': unit_nutrition_data['fat'] * factor,
            'carbs': unit_nutrition_data['carbs'] * factor,
        }

        # Render the tables for user confirmation
        return render_template(
            'meal/record.html',
            parsed_data=parsed_data,
            unit_nutrition_data=unit_nutrition_data,
            scaled_nutrition_data=scaled_nutrition_data,
            meal_text=meal_text  # Pass the meal_text back
        )

    elif request.method == 'GET' and 'calculate' in request.args:
        try:
            parsed_data = json.loads(request.args.get('parsed_data'))
            # Get meal_text directly from request args
            meal_text = request.args.get('meal_text', '')
            unit_nutrition_data = {
                'calories': float(request.args.get('calories')),
                'protein': float(request.args.get('protein')),
                'fat': float(request.args.get('fat')),
                'carbs': float(request.args.get('carbs')),
                'base_quantity': float(request.args.get('base_quantity')),
                'base_unit': request.args.get('base_unit')
            }
            
            # Calculate scaled values
            factor = parsed_data['quantity'] / unit_nutrition_data['base_quantity']
            scaled_nutrition_data = {
                'calories': unit_nutrition_data['calories'] * factor,
                'protein': unit_nutrition_data['protein'] * factor,
                'fat': unit_nutrition_data['fat'] * factor,
                'carbs': unit_nutrition_data['carbs'] * factor
            }

            return render_template('meal/record.html',
                                parsed_data=parsed_data,
                                unit_nutrition_data=unit_nutrition_data,
                                scaled_nutrition_data=scaled_nutrition_data,
                                meal_text=meal_text)  # Pass meal_text back to template
                                
        except json.JSONDecodeError as e:
            flash('Error processing form data', 'error')
            return redirect(url_for('meal.record_meal'))

    elif request.method == 'GET' and 'confirm' in request.args:
        # Initialize unit_nutrition_data outside the try block
        unit_nutrition_data = {}
        
        try:
            food_name = request.args.get('food_name')
            quantity = float(request.args.get('quantity'))
        
            
            # Safely convert values to float or None
            def safe_float(value):
                try:
                    if value in [None, 'null', '', 'None']:
                        return None
                    return float(value)
                except (ValueError, TypeError):
                    return None

            # Handle potential null values in nutrition data
            unit_nutrition_data = {
                'calories': safe_float(request.args.get('unit_calories')),  # New field for unit values
                'protein': safe_float(request.args.get('unit_protein')),   # New field for unit values
                'fat': safe_float(request.args.get('unit_fat')),          # New field for unit values
                'carbs': safe_float(request.args.get('unit_carbs')),      # New field for unit values
                'base_quantity': safe_float(request.args.get('base_quantity')),
                'base_unit': request.args.get('base_unit')
            }  
            factor = quantity / unit_nutrition_data['base_quantity']
            scaled_nutrition_data = {
                'calories': unit_nutrition_data['calories'] * factor if unit_nutrition_data['calories'] else None,
                'protein': unit_nutrition_data['protein'] * factor if unit_nutrition_data['protein'] else None,
                'fat': unit_nutrition_data['fat'] * factor if unit_nutrition_data['fat'] else None,
                'carbs': unit_nutrition_data['carbs'] * factor if unit_nutrition_data['carbs'] else None,
            } 
            
            # Standardize the food ID
            food_id = food_name.lower().replace(" ", "_")
            
            # Convert None to null for JSON serialization
            json_nutrition_data = {
                k: v if v is not None else "null"
                for k, v in unit_nutrition_data.items()
            }
            
            # Add debug print
            print("-"*50)
            print(f"Attempting to save to ChromaDB unit_nutrition_data...")
            print(f"{unit_nutrition_data}")
            print(f"{json_nutrition_data}")
            print("-"*50)
            # Save to ChromaDB
            # chroma_client = chromadb.Client()
            chroma_client = get_chroma_client()
            collection = chroma_client.get_or_create_collection(name="food_nutrients")
            collection.upsert(
                documents=[json.dumps(json_nutrition_data)],
                metadatas=[{"food_name": food_name}],
                ids=[food_id]
            )
            print(f"Successfully saved nutrition data for {food_name} (id: {food_id}) to ChromaDB", "\n","-"*30)
            
            # Then save the meal with scaled values to the database
            meal = UserMeal(
                user_id=current_user.id,
                food_name=request.args.get('food_name'),
                # quantity=float(request.args.get('quantity')),
                quantity=quantity,
                unit=request.args.get('unit'),
                measurement_type=request.args.get('measurement_type'),
                calories=scaled_nutrition_data['calories'],
                protein=scaled_nutrition_data['protein'],
                fat=scaled_nutrition_data['fat'],
                carbs=scaled_nutrition_data['carbs'],
                date_recorded=datetime.now()
            )
            try:
                db.session.add(meal)
                db.session.commit()
                flash('Meal recorded successfully!', 'success')
            except Exception as e:
                db.session.rollback()
                flash('Error recording meal. Please try again.', 'error')
                print(f"Database error: {e}")
            return redirect(url_for('meal.record_meal'))
        except Exception as e:
            print(f"Error saving to ChromaDB: {e}")
            print(f"Debug - request args: {request.args}")
            print(f"Debug - unit_nutrition_data: {unit_nutrition_data}")  # unit_nutrition_data is now always defined

    return render_template('meal/record.html')


if __name__ == '__main__':
    # import openai
    # print(openai.__version__)
    pass