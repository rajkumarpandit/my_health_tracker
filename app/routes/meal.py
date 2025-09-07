from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
import openai
import chromadb
import os
import json
from datetime import datetime
from app.models import UserMeal
from app.extensions import db
from app.models.daily_target import DailyTarget  # Add this line
from slugify import slugify 
from chromadb.config import Settings
from app.models.exercise import UserExercise
from app.models.daily_target import DailyTarget
from app.models.supplement import UserSupplement
from app.models.nutrition_cache import NutritionCache

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
    """Get ChromaDB client with proper configuration."""
    # Disable ChromaDB in production to avoid deployment issues
    if os.getenv('FLASK_ENV') == 'production':
        print("🔧 ChromaDB disabled in production - using PostgreSQL cache only")
        return None
    
    try:
        import chromadb
        from chromadb.config import Settings
        
        # Use environment variable or default path
        chroma_path = os.getenv('CHROMA_DB_PATH', 'instance/chromadb')
        os.makedirs(chroma_path, exist_ok=True)
        
        client = chromadb.PersistentClient(
            path=chroma_path,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        return client
        
    except ImportError:
        print("ℹ️ ChromaDB not available - using PostgreSQL cache only")
        return None
    except Exception as e:
        print(f"⚠️ ChromaDB setup failed: {e}")
        return None

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
    """
    Get nutrition information with branched search:
    1. PostgreSQL cache
    2. ChromaDB 
    3. OpenAI API call
    """
    print("\n" + "="*50)
    print("NUTRITION SEARCH - BRANCHED APPROACH")
    print("="*50)
    
    # Standardize the food name for lookup
    food_id = food_name.lower().replace(" ", "_")
    print(f"Input food_name: {food_name}")
    print(f"Generated food_id: {food_id}")
    
    # STEP 1: Check PostgreSQL cache first
    print("\n1. Checking PostgreSQL cache...")
    try:
        cached_nutrition = NutritionCache.query.filter_by(food_id=food_id).first()
        if cached_nutrition:
            print(f"✅ Found in PostgreSQL cache: {food_name}")
            return cached_nutrition.nutrition_data
        else:
            print(f"❌ Not found in PostgreSQL cache")
    except Exception as e:
        print(f"❌ PostgreSQL cache error: {e}")
    
    # STEP 2: Check ChromaDB
    print("\n2. Checking ChromaDB...")
    unit_nutrition_data = None
    try:
        chroma_client = get_chroma_client()
        collection = chroma_client.get_or_create_collection(name="food_nutrients")
        
        # Try exact match first
        try:
            print("   Attempting exact match in ChromaDB...")
            results = collection.get(
                ids=[food_id],
                include=["documents", "metadatas"]
            )
            
            if results and results['documents'] and len(results['documents']) > 0:
                unit_nutrition_data = json.loads(results['documents'][0])
                print(f"✅ Found exact match in ChromaDB: {food_name}")
            else:
                print("   No exact match found")
        except Exception as e:
            print(f"   Exact match failed: {e}")
        
        # If no exact match, try similarity search
        if not unit_nutrition_data:
            try:
                print("   Attempting similarity search in ChromaDB...")
                results = collection.query(
                    query_texts=[food_name],
                    n_results=1,
                    include=["documents", "metadatas", "distances"]
                )
                
                if (results and results['documents'] and len(results['documents']) > 0 
                    and len(results['documents'][0]) > 0):
                    distance = float(results['distances'][0][0])
                    print(f"   Similarity distance: {distance}")
                    
                    if distance < 0.5:  # Threshold for similarity
                        unit_nutrition_data = json.loads(results['documents'][0][0])
                        print(f"✅ Found similar match in ChromaDB: {food_name}")
                    else:
                        print(f"   Distance {distance} exceeds threshold 0.5")
                else:
                    print("   No similar matches found")
            except Exception as e:
                print(f"   Similarity search failed: {e}")
        
        if not unit_nutrition_data:
            print("❌ Not found in ChromaDB")
            
    except Exception as e:
        print(f"❌ ChromaDB access error: {e}")
    
    # If found in ChromaDB, save to PostgreSQL for faster future access
    if unit_nutrition_data:
        print("\n💾 Saving ChromaDB result to PostgreSQL cache...")
        try:
            save_to_postgresql_cache(food_id, food_name, unit_nutrition_data)
        except Exception as e:
            print(f"Failed to save to PostgreSQL: {e}")
        return unit_nutrition_data
    
    # STEP 3: Call OpenAI API
    print("\n3. Calling OpenAI API...")
    unit_nutrition_data = call_openai_for_nutrition(food_name, measurement_type)
    
    if unit_nutrition_data:
        print(f"✅ Got nutrition data from OpenAI: {food_name}")
        
        # Save to PostgreSQL cache
        print("💾 Saving OpenAI result to PostgreSQL cache...")
        try:
            save_to_postgresql_cache(food_id, food_name, unit_nutrition_data)
        except Exception as e:
            print(f"Failed to save to PostgreSQL: {e}")
        
        # Also save to ChromaDB for similarity search
        print("💾 Saving OpenAI result to ChromaDB...")
        try:
            save_to_chromadb(food_id, food_name, unit_nutrition_data)
        except Exception as e:
            print(f"Failed to save to ChromaDB: {e}")
            
        return unit_nutrition_data
    else:
        print("❌ Failed to get nutrition data from OpenAI")
        return None

def save_to_postgresql_cache(food_id, food_name, nutrition_data):
    """Save nutrition data to PostgreSQL cache."""
    try:
        # Check if already exists (upsert behavior)
        existing = NutritionCache.query.filter_by(food_id=food_id).first()
        
        if existing:
            # Update existing record
            existing.nutrition_data = nutrition_data
            existing.updated_at = datetime.utcnow()
            print(f"Updated existing PostgreSQL cache entry for: {food_name}")
        else:
            # Create new record
            cache_entry = NutritionCache(
                food_id=food_id,
                food_name=food_name,
                nutrition_data=nutrition_data
            )
            db.session.add(cache_entry)
            print(f"Created new PostgreSQL cache entry for: {food_name}")
        
        db.session.commit()
        print(f"Successfully saved to PostgreSQL cache: {food_name}")
        
    except Exception as e:
        db.session.rollback()
        print(f"Error saving to PostgreSQL cache: {e}")
        raise e

def save_to_chromadb(food_id, food_name, nutrition_data):
    """Save nutrition data to ChromaDB."""
    if os.getenv('FLASK_ENV') == 'production':
        return  # Skip in production
    
    try:
        chroma_client = get_chroma_client()
        if not chroma_client:
            return
        
        # Convert None to "null" for JSON serialization
        json_nutrition_data = {
            k: v if v is not None else "null"
            for k, v in nutrition_data.items()
        }
        
        collection = chroma_client.get_or_create_collection(name="food_nutrients")
        
        collection.upsert(
            documents=[json.dumps(json_nutrition_data)],
            metadatas=[{"food_name": food_name}],
            ids=[food_id]
        )
        print(f"✅ Successfully saved to ChromaDB: {food_name}")
        
    except Exception as e:
        print(f"⚠️ ChromaDB save failed: {e}")
        # Don't raise the error - just log it since PostgreSQL cache worked

def call_openai_for_nutrition(food_name, measurement_type):
    """Extract OpenAI API call logic to separate function."""
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
        }}"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a nutrition expert. Provide accurate nutrition information in JSON format."},
                {"role": "user", "content": prompt}
            ]
        )
        raw_content = response.choices[0].message.content
        
        if raw_content.startswith("```") and raw_content.endswith("```"):
            raw_content = raw_content.strip("```").strip("json").strip()
            
        unit_nutrition_data = json.loads(raw_content)
        print("Unit Nutrition data fetched from OpenAI:", unit_nutrition_data)
        
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
            return render_template('meal/record.html', meal_text=meal_text)

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

        # Ensure all nutrition values are either a number or 0.0
        unit_nutrition_data = {
            'calories': 0.0 if unit_nutrition_data.get('calories') is None else unit_nutrition_data['calories'],
            'protein': 0.0 if unit_nutrition_data.get('protein') is None else unit_nutrition_data['protein'],
            'fat': 0.0 if unit_nutrition_data.get('fat') is None else unit_nutrition_data['fat'],
            'carbs': 0.0 if unit_nutrition_data.get('carbs') is None else unit_nutrition_data['carbs'],
            'base_quantity': unit_nutrition_data['base_quantity'],
            'base_unit': unit_nutrition_data['base_unit']
        }

        # Scale the values
        scaled_nutrition_data = {
            'calories': unit_nutrition_data['calories'] * factor,
            'protein': unit_nutrition_data['protein'] * factor,
            'fat': unit_nutrition_data['fat'] * factor,
            'carbs': unit_nutrition_data['carbs'] * factor,
        }

        return render_template(
            'meal/record.html',
            parsed_data=parsed_data,
            unit_nutrition_data=unit_nutrition_data,
            scaled_nutrition_data=scaled_nutrition_data,
            meal_text=meal_text
        )

    elif request.method == 'GET' and 'calculate' in request.args:
        try:
            parsed_data = json.loads(request.args.get('parsed_data'))
            meal_text = request.args.get('meal_text', '')
            
            # Get the UPDATED unit nutrition data from the form (user's modifications)
            unit_nutrition_data = {
                'calories': float(request.args.get('calories')),
                'protein': float(request.args.get('protein')),
                'fat': float(request.args.get('fat')),
                'carbs': float(request.args.get('carbs')),
                'base_quantity': float(request.args.get('base_quantity')),
                'base_unit': request.args.get('base_unit')
            }
            
            print(f"\n🔄 RECALCULATE - User modified nutrition data:")
            print(f"📊 Updated unit nutrition: {unit_nutrition_data}")
            
            # ✅ UPDATE THE NUTRITION CACHE with user's modified data
            food_name = parsed_data['food_name']
            food_id = food_name.lower().replace(" ", "_")
            
            try:
                print(f"💾 Updating nutrition cache with modified data for: {food_name}")
                
                # Save/Update the modified unit nutrition data to PostgreSQL cache
                save_to_postgresql_cache(food_id, food_name, unit_nutrition_data)
                print(f"✅ Successfully updated PostgreSQL nutrition cache with user modifications")
                
            except Exception as cache_error:
                print(f"❌ Error updating nutrition cache: {cache_error}")
            
            # ✅ ALSO UPDATE CHROMADB with user's modified data
            try:
                print("💾 Updating ChromaDB with modified nutrition data...")
                save_to_chromadb(food_id, food_name, unit_nutrition_data)
                print(f"✅ Successfully updated ChromaDB with user modifications")
            except Exception as chromadb_error:
                print(f"⚠️ ChromaDB update failed: {chromadb_error}")
            
            # Calculate scaled nutrition with the updated data
            factor = parsed_data['quantity'] / unit_nutrition_data['base_quantity']
            scaled_nutrition_data = {
                'calories': unit_nutrition_data['calories'] * factor,
                'protein': unit_nutrition_data['protein'] * factor,
                'fat': unit_nutrition_data['fat'] * factor,
                'carbs': unit_nutrition_data['carbs'] * factor
            }
            
            print(f"📊 Recalculated scaled nutrition with updated data: {scaled_nutrition_data}")

            return render_template('meal/record.html',
                                parsed_data=parsed_data,
                                unit_nutrition_data=unit_nutrition_data,
                                scaled_nutrition_data=scaled_nutrition_data,
                                meal_text=meal_text)
                                
        except json.JSONDecodeError as e:
            print(f"❌ JSON decode error: {e}")
            flash('Error processing form data', 'error')
            return redirect(url_for('meal.record_meal'))
        except Exception as e:
            print(f"❌ Error in recalculate: {e}")
            flash('Error recalculating nutrition data', 'error')
            return redirect(url_for('meal.record_meal'))

    elif request.method == 'GET' and 'confirm' in request.args:
        print("\n🔥 CONFIRM ROUTE - Starting meal save process...")
    
        try:
            food_name = request.args.get('food_name')
            quantity = float(request.args.get('quantity'))
            unit = request.args.get('unit')
            measurement_type = request.args.get('measurement_type')
            
            # Safely convert values to float or 0.0 (not None)
            def safe_float(value):
                try:
                    if value in [None, 'null', '', 'None']:
                        return 0.0  # ✅ Return 0.0 instead of None
                    return float(value)
                except (ValueError, TypeError):
                    return 0.0  # ✅ Return 0.0 instead of None

            # Get unit nutrition data
            unit_nutrition_data = {
                'calories': safe_float(request.args.get('unit_calories')),
                'protein': safe_float(request.args.get('unit_protein')),
                'fat': safe_float(request.args.get('unit_fat')),
                'carbs': safe_float(request.args.get('unit_carbs')),
                'base_quantity': safe_float(request.args.get('base_quantity')),
                'base_unit': request.args.get('base_unit')
            }
            
            # Calculate scaled nutrition
            factor = quantity / unit_nutrition_data['base_quantity']
            scaled_nutrition_data = {
                'calories': unit_nutrition_data['calories'] * factor,
                'protein': unit_nutrition_data['protein'] * factor,
                'fat': unit_nutrition_data['fat'] * factor,
                'carbs': unit_nutrition_data['carbs'] * factor,
            }
            
            print(f"📊 Calculated nutrition: {scaled_nutrition_data}")
            
            # ✅ SAVE TO DATABASE FIRST (most important)
            print("💾 Saving to user_meals table...")
            meal = UserMeal(
                user_id=current_user.id,
                food_name=food_name,
                quantity=quantity,
                unit=unit,
                measurement_type=measurement_type,
                calories=scaled_nutrition_data['calories'],
                protein=scaled_nutrition_data['protein'],
                fat=scaled_nutrition_data['fat'],
                carbs=scaled_nutrition_data['carbs'],
                date_recorded=datetime.now()
            )
            
            db.session.add(meal)
            db.session.commit()
            print(f"✅ Successfully saved meal to database: {food_name}")
            
            # ✅ NOW TRY TO SAVE TO CHROMADB (optional - don't fail if this fails)
            try:
                print("💾 Attempting to save to ChromaDB...")
                food_id = food_name.lower().replace(" ", "_")
                
                # Convert None to "null" for JSON serialization
                json_nutrition_data = {
                    k: v if v is not None else "null"
                    for k, v in unit_nutrition_data.items()
                }
                
                chroma_client = get_chroma_client()
                collection = chroma_client.get_or_create_collection(name="food_nutrients")
                
                collection.upsert(
                    documents=[json.dumps(json_nutrition_data)],
                    metadatas=[{"food_name": food_name}],
                    ids=[food_id]
                )
                print(f"✅ Successfully saved to ChromaDB: {food_name}")
                
            except Exception as chromadb_error:
                print(f"⚠️ ChromaDB save failed (but meal was saved): {chromadb_error}")
                # Don't fail the whole operation - meal is already saved!
            
            flash('Meal recorded successfully!', 'success')
            return redirect(url_for('meal.today_consumption'))
            
        except Exception as e:
            print(f"❌ Error in confirm route: {e}")
            db.session.rollback()
            flash('Error recording meal. Please try again.', 'error')
            return redirect(url_for('meal.record_meal'))

    return render_template('meal/record.html')

# Add this new route below your existing record_meal route
@bp.route('/record_meal_advanced', methods=['POST'])
@login_required
def record_meal_advanced():
    try:
        # Extract data from the form
        food_name = request.form.get('food_name')
        quantity = float(request.form.get('quantity'))
        unit = request.form.get('unit')
        calories = float(request.form.get('calories') or 0)
        protein = float(request.form.get('protein') or 0)
        fat = float(request.form.get('fat') or 0)
        carbs = float(request.form.get('carbs') or 0)
        
        print(f"\n🔥 ADVANCED MEAL ENTRY - Processing: {food_name}")
        print(f"📊 User Input: {quantity} {unit} = {calories} cal, {protein}g protein, {fat}g fat, {carbs}g carbs")
        
        # Determine measurement type based on unit
        if unit.lower() in ['grams', 'gram', 'g', 'ml', 'milliliter', 'kg', 'kilogram', 'oz', 'ounce']:
            measurement_type = 'weight'
            base_unit = 'grams'
            base_quantity = 100  # Per 100g standard
        else:
            measurement_type = 'count'
            base_unit = 'pieces'
            base_quantity = 1  # Per piece standard
        
        print(f"🔄 Detected measurement_type: {measurement_type}")
        
        # Convert entered nutrition to unit nutrition (per base quantity)
        if measurement_type == 'weight':
            # For weight: Convert to per 100g
            # User entered: 250g = 500 calories → Per 100g = 200 calories
            conversion_factor = base_quantity / quantity  # 100g / 250g = 0.4
            unit_nutrition_data = {
                'calories': calories * conversion_factor,
                'protein': protein * conversion_factor,
                'fat': fat * conversion_factor,
                'carbs': carbs * conversion_factor,
                'base_quantity': base_quantity,
                'base_unit': base_unit
            }
            print(f"🔄 Weight conversion: {quantity}g → {base_quantity}g (factor: {conversion_factor})")
            
        else:
            # For count: Convert to per piece
            # User entered: 4 pieces = 400 calories → Per 1 piece = 100 calories
            conversion_factor = base_quantity / quantity  # 1 piece / 4 pieces = 0.25
            unit_nutrition_data = {
                'calories': calories * conversion_factor,
                'protein': protein * conversion_factor,
                'fat': fat * conversion_factor,
                'carbs': carbs * conversion_factor,
                'base_quantity': base_quantity,
                'base_unit': base_unit
            }
            print(f"🔄 Count conversion: {quantity} {unit} → {base_quantity} {base_unit} (factor: {conversion_factor})")
        
        print(f"💾 Unit nutrition data for cache: {unit_nutrition_data}")
        
        # Save to nutrition cache for future use (per unit data)
        food_id = food_name.lower().replace(" ", "_")
        print(f"💾 Saving to nutrition cache with food_id: {food_id}")
        
        try:
            # Check if already exists in PostgreSQL cache
            existing_cache = NutritionCache.query.filter_by(food_id=food_id).first()
            
            if existing_cache:
                # Update existing record
                existing_cache.nutrition_data = unit_nutrition_data
                existing_cache.updated_at = datetime.utcnow()
                print(f"✅ Updated existing nutrition cache entry for: {food_name}")
            else:
                # Create new record
                cache_entry = NutritionCache(
                    food_id=food_id,
                    food_name=food_name,
                    nutrition_data=unit_nutrition_data
                )
                db.session.add(cache_entry)
                print(f"✅ Created new nutrition cache entry for: {food_name}")
            
            # Commit the cache entry
            db.session.commit()
            print(f"✅ Successfully saved to PostgreSQL nutrition cache: {food_name}")
            
        except Exception as cache_error:
            print(f"❌ Error saving to nutrition cache: {cache_error}")
            db.session.rollback()
            # Don't fail the whole operation, just log the error
        
        # Save to ChromaDB for similarity search (per unit data)
        try:
            print("💾 Saving unit nutrition data to ChromaDB...")
            save_to_chromadb(food_id, food_name, unit_nutrition_data)
            print(f"✅ Successfully saved to ChromaDB: {food_name}")
        except Exception as chromadb_error:
            print(f"⚠️ ChromaDB save failed: {chromadb_error}")
            # Don't fail the whole operation
        
        # Create and save the meal to user_meals table (actual consumed amounts)
        print("💾 Saving actual consumed meal to user_meals table...")
        meal = UserMeal(
            user_id=current_user.id,
            food_name=food_name,
            quantity=quantity,  # Actual quantity consumed (e.g., 4 pieces)
            unit=unit,
            measurement_type=measurement_type,
            calories=calories,  # Total calories consumed (e.g., 400 cal for 4 pieces)
            protein=protein,    # Total protein consumed
            fat=fat,           # Total fat consumed
            carbs=carbs,       # Total carbs consumed
            date_recorded=datetime.now()
        )
        
        db.session.add(meal)
        db.session.commit()
        print(f"✅ Successfully saved meal to database: {food_name}")
        
        flash(f'Successfully added {food_name} to your meal log and nutrition cache.', 'success')
        return redirect(url_for('meal.today_consumption'))
        
    except ValueError as e:
        print(f"❌ ValueError in advanced meal entry: {e}")
        flash('Please enter valid numeric values for all nutrition fields.', 'error')
        return redirect(url_for('meal.record_meal'))
    except Exception as e:
        print(f"❌ Error in advanced meal entry: {e}")
        db.session.rollback()
        flash(f'Error recording meal: {str(e)}', 'error')
        return redirect(url_for('meal.record_meal'))

@bp.route('/today_consumption', methods=['GET'])
@login_required
def today_consumption():
    # Get today's date
    today = datetime.now().date()
    
    # Fetch today's meals for the current user
    meals = UserMeal.query.filter(
        UserMeal.user_id == current_user.id,
        db.func.date(UserMeal.date_recorded) == today
    ).order_by(UserMeal.date_recorded).all()
    
    # Calculate nutrition totals
    totals = {
        'calories': sum(meal.calories for meal in meals) if meals else 0,
        'protein': sum(meal.protein for meal in meals) if meals else 0,
        'carbs': sum(meal.carbs for meal in meals) if meals else 0,
        'fat': sum(meal.fat for meal in meals) if meals else 0
    }
    
    # Get user's daily targets
    # from app.models.daily_target import DailyTarget
    target = DailyTarget.query.filter_by(user_id=current_user.id).first()
    
    # Set default targets if none exists
    targets = {
        'calories': target.calories if target else 2000,
        'protein': target.protein if target else 150,
        'carbs': target.carbs if target else 200,
        'fat': target.fat if target else 70
    }
    
    # Get today's exercise data
    exercise = UserExercise.query.filter_by(
        user_id=current_user.id,
        date_recorded=today
    ).first()
    
    calories_burned = 0
    step_count = 0
    if exercise:
        calories_burned = exercise.total_calories
        step_count = exercise.step_count
    
    # Get today's supplements
    # from app.models.supplement import UserSupplement
    supplements = UserSupplement.query.filter_by(
        user_id=current_user.id,
        date_taken=today
    ).order_by(UserSupplement.created_at).all()
    
    # Pass all necessary data to template
    return render_template(
        'meal/today_consumption.html', 
        meals=meals, 
        totals=totals,
        targets=targets,
        calories_burned=calories_burned,
        supplements=supplements,
        step_count=step_count
    )

if __name__ == '__main__':
    # import openai
    # print(openai.__version__)
    pass