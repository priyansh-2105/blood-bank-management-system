from flask import Blueprint, jsonify, request
from app.utils.helpers import get_cities, get_hospitals_by_city

api_bp = Blueprint('api', __name__)

@api_bp.route('/cities')
def cities():
    """Get list of cities for autocomplete"""
    cities_list = get_cities()
    return jsonify({'cities': cities_list})

@api_bp.route('/hospitals/<city>')
def hospitals_by_city(city):
    """Get hospitals by city for autocomplete"""
    hospitals = get_hospitals_by_city(city)
    hospital_list = []
    
    for hospital in hospitals:
        hospital_list.append({
            'id': hospital.id,
            'name': hospital.user.name,
            'address': hospital.address,
            'phone': hospital.phone
        })
    
    return jsonify({'hospitals': hospital_list})

@api_bp.route('/search/cities')
def search_cities():
    """Search cities with query parameter"""
    query = request.args.get('q', '').lower()
    cities_list = get_cities()
    
    if query:
        filtered_cities = [city for city in cities_list if query in city.lower()]
    else:
        filtered_cities = cities_list[:10]  # Limit to first 10 if no query
    
    return jsonify({'cities': filtered_cities}) 