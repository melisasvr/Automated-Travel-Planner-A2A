# Travel Planner-Agent-to-Agent Communication System

An AI-powered travel planning system that uses Agent-to-Agent (A2A) communication protocol to orchestrate comprehensive travel itineraries. The system employs specialized agents that collaborate to find flights, hotels, and activities for your travel needs.

## 🌟 Features

### Core Functionality
- **Multi-Destination Planning**: Create itineraries for trips spanning multiple cities (e.g., New York → Paris → Rome).
- **Roundtrip Support**: Automatically includes return flights to your departure city.
- **Asynchronous Processing**: Leverages asyncio for efficient, concurrent task execution.
- **Budget Allocation**: Allocates budget across flights (40%), hotels (40%), and activities (20%).
- **Customizable Preferences**: Supports filters like minimum hotel ratings or preferred activity types (e.g., cultural, culinary).
- **Robust Error Handling**: Includes logging and exception management for reliable operation.

### Agent Types
- **Master Agent**: Orchestrates the entire travel planning process. 
- **Flight Agent**: Handles flight search and booking options.
- **Hotel Agent**: Manages accommodation searches and recommendations. 
- **Activities Agent**: Finds local activities and experiences.

## 🏗️ Architecture

### A2A Protocol
The system uses a custom Agent-to-Agent communication protocol that enables:
- Agent registration and discovery
- Message passing between agents
- Asynchronous request/response handling
- Correlation tracking for complex workflows

### Message Types
- `DISCOVER`: Agent discovery requests
- `REQUEST`: Service requests between agents
- `RESPONSE`: Agent responses with results
- `ERROR`: Error handling and reporting

## 📋 Requirements

```python
# Core Dependencies
asyncio
json
uuid
datetime
dataclasses
typing
enum
logging
```

## 🚀 Installation & Setup

1. **Clone or download the travel planner script**
   ```bash
   # Save the code as travel_planner.py
   ```

2. **Ensure Python 3.7+ is installed**
   ```bash
   python --version  # Should be 3.7 or higher
   ```

3. **Run the system**
   ```bash
   python travel_planner.py
   ```

No additional dependencies required - uses only Python standard library!

## 💻 Usage
- Run the Application:
- Execute the main script to generate a sample itinerary:
- `python travel_planner.py`
- Sample Input:
- The default configuration plans a roundtrip from New York, NY to Paris, France, and Rome, Italy:
```
travel_request = TravelRequest(
    destinations=["Paris, France", "Rome, Italy"],
    departure_city="New York, NY",
    start_date="2024-07-15",
    end_date="2024-07-22",
    budget=3000.0,
    travelers=2,
    preferences={
        "hotel": {"rating_min": 4.0},
        "activities": {"types": ["cultural", "culinary"]}
    },
    is_roundtrip=True
)
```
- Customize Input:
- Edit the travel_request in the main() function of travel_planner.py to modify:
- destinations: List of cities to visit.
- departure_city: Starting city.
- start_date and end_date: Trip dates in YYYY-MM-DD format.
- budget: Total budget in USD.
- travelers: Number of travelers.
- preferences: Hotel and activity preferences.
- is_roundtrip: Set to False for one-way trips.


## 📊 Sample Output

```
🌍 Starting Automated Travel Planning...
Destinations: Paris, France, Rome, Italy
Roundtrip: True
Dates: 2024-07-15 to 2024-07-22
Budget: $3000.0
Travelers: 2

==================================================

✈️ COMPLETE TRAVEL ITINERARY
==================================================
Destinations: Paris, France, Rome, Italy
Travel Dates: 2024-07-15 to 2024-07-22
Number of Travelers: 2

🛫 FLIGHT ITINERARY:
  1. AirLine One from New York, NY to Paris, France - $450.0
     Departure: 08:00 | Duration: 4h 00m
  2. Sky Express from New York, NY to Paris, France - $380.0
     Departure: 14:30 | Duration: 4h 15m
  3. AirLine One from Paris, France to Rome, Italy - $450.0
     Departure: 08:00 | Duration: 4h 00m
  4. Sky Express from Paris, France to Rome, Italy - $380.0
     Departure: 14:30 | Duration: 4h 15m
  5. AirLine One from Rome, Italy to New York, NY - $450.0
     Departure: 08:00 | Duration: 4h 00m
  6. Sky Express from Rome, Italy to New York, NY - $380.0
     Departure: 14:30 | Duration: 4h 15m

📍 Paris, France
  🏨 HOTEL OPTIONS:
    1. Grand Plaza Hotel - $150.0/night
       Rating: 4.5⭐ | Location: Downtown
    2. Comfort Inn - $95.0/night
       Rating: 4.0⭐ | Location: City Center
  🎯 ACTIVITY OPTIONS:
    1. City Walking Tour - $25.0
       Type: Cultural | Duration: 3 hours | Rating: 4.7⭐
    2. Food Tour - $65.0
       Type: Culinary | Duration: 4 hours | Rating: 4.8⭐

📍 Rome, Italy
  🏨 HOTEL OPTIONS:
    1. Grand Plaza Hotel - $150.0/night
       Rating: 4.5⭐ | Location: Downtown
    2. Comfort Inn - $95.0/night
       Rating: 4.0⭐ | Location: City Center
  🎯 ACTIVITY OPTIONS:
    1. City Walking Tour - $25.0
       Type: Cultural | Duration: 3 hours | Rating: 4.7⭐
    2. Food Tour - $65.0
       Type: Culinary | Duration: 4 hours | Rating: 4.8⭐

💰 ESTIMATED TOTAL COST: $2430.00
Generated at: 2025-05-27T13:40:19.406851
```

## How It Works
1. **MasterAgent**:
- Receives user input (destinations, dates, budget, etc.).
- Delegates tasks to specialized agents via the A2A protocol.
- Compiles responses into a cohesive itinerary.
2. **Specialized Agents**:
- FlightAgent: Simulates flight searches for each trip segment (e.g., New York → Paris → Rome → New York).
- HotelAgent: Provides hotel options for each destination.
- ActivitiesAgent: Suggests activities based on user preferences.
3. **A2A Protocol**:
- Facilitates asynchronous communication between agents using a message queue.
- Supports agent discovery and reliable message passing.
4. **Itinerary Compilation**:
- Combines flight, hotel, and activity options into a structured itinerary.
- Estimates total cost using the first option for flights, hotels (3 nights per destination), and top two activities per destination.


## 🔮 Future Enhancements
- API Integration: Connect to travel APIs for real-time flight, hotel, and activity data.
- Custom Day Allocation: Allow users to specify days per destination.
- Budget Optimization: Select options to maximize value within the budget.
- User Interface: Develop a GUI or CLI for easier input.
- Cost Breakdown: Display detailed costs for flights, hotels, and activities.


## 🤝 Contributing
- Contributions are welcome! To contribute:
- Fork the repository.
- Create a new branch (git checkout -b feature/your-feature).
- Make changes and commit (git commit -m "Add your feature").
- Push to your branch (git push origin feature/your-feature).
- Open a pull request.
- Ensure code adheres to PEP 8 style guidelines and includes logging for debugging.


## 📄 License
- This travel planner is provided as-is for educational and development purposes. Integrate with real travel APIs responsibly and by their terms of service.
