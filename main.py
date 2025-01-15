from flask import Flask, request, jsonify
from flask_cors import CORS
from crewai import Crew
from agents import TravelAgents
from tasks import TravelTasks
from dotenv import load_dotenv
import datetime
import os

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configure CORS - replace with your frontend URL in production
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "http://localhost:3000",  # React development server
            "http://localhost:5173",  # Vite development server
            "https://your-frontend-domain.com"  # Add your deployed frontend URL
        ],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

class TripCrew:
    def __init__(self, origin, cities, date_range, interests, currency, budget):
        self.origin = origin
        self.cities = cities
        self.date_range = date_range
        self.interests = interests
        self.budget = budget
        self.currency=currency

    def run(self):
        agents = TravelAgents()
        tasks = TravelTasks()

        expert_travel_agent = agents.expert_travel_agent()
        city_selection_expert = agents.city_selection_expert()
        local_tour_guide = agents.local_tour_guide()

        plan_itinerary = tasks.plan_itinerary(
            expert_travel_agent,
            self.cities,
            self.date_range,
            self.interests,
            self.budget,
            self.currency
        )

        identify_city = tasks.identify_city(
            city_selection_expert,
            self.origin,
            self.cities,
            self.interests,
            self.date_range,
            self.budget,
            self.currency

        )

        gather_city_info = tasks.gather_city_info(
            local_tour_guide,
            self.cities,
            self.date_range,
            self.interests,
            self.budget,
            self.currency
        )

        crew = Crew(
            agents=[expert_travel_agent, city_selection_expert, local_tour_guide],
            tasks=[plan_itinerary, identify_city, gather_city_info],
            verbose=True,
        )

        result = crew.kickoff()
        return str(result)

@app.route('/api/plan-trip', methods=['POST'])
def plan_trip():
    try:
        # Validate input
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': 'Content-Type must be application/json'
            }), 400

        data = request.get_json()
        required_fields = ['origin', 'cities', 'date_range', 'interests', 'budget']
        
        # Check for missing fields
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({
                'success': False,
                'error': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400

        # Create and run trip crew
        trip_crew = TripCrew(
            data['origin'],
            data['cities'],
            data['date_range'],
            data['interests'],
            data['budget'],
            data['currency']
        )
        
        result = trip_crew.run()
        
        return jsonify({
            'success': True,
            'result': result,
            'timestamp': datetime.datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.datetime.now().isoformat()
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'version': '1.0.0',
        'env': os.getenv('FLASK_ENV', 'production'),
        'timestamp': datetime.datetime.now().isoformat()
    })

# New endpoint to check API configuration
@app.route('/api/config', methods=['GET'])
def get_config():
    return jsonify({
        'maxRequestSize': '10mb',
        'timeout': 300,  # 5 minutes
        'supportedBudgetRanges': ['low', 'medium', 'high'],
        'version': '1.0.0'
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)