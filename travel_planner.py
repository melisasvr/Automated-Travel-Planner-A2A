import asyncio
import json
import uuid
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
from enum import Enum
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MessageType(Enum):
    DISCOVER = "discover"
    REQUEST = "request"
    RESPONSE = "response"
    ERROR = "error"

class AgentType(Enum):
    MASTER = "master"
    FLIGHT = "flight"
    HOTEL = "hotel"
    ACTIVITIES = "activities"

@dataclass
class A2AMessage:
    id: str
    sender: str
    receiver: str
    message_type: MessageType
    payload: Dict[str, Any]
    timestamp: datetime
    correlation_id: Optional[str] = None

@dataclass
class TravelRequest:
    destinations: List[str]
    departure_city: str
    start_date: str
    end_date: str
    budget: float
    travelers: int
    preferences: Dict[str, Any]
    is_roundtrip: bool = True

@dataclass
class FlightOption:
    airline: str
    departure_city: str
    destination_city: str
    departure_time: str
    arrival_time: str
    price: float
    duration: str

@dataclass
class HotelOption:
    name: str
    rating: float
    price_per_night: float
    amenities: List[str]
    location: str
    city: str

@dataclass
class ActivityOption:
    name: str
    type: str
    price: float
    duration: str
    rating: float
    city: str

class A2AProtocol:
    def __init__(self):
        self.agents: Dict[str, 'BaseAgent'] = {}
        self.message_queue: asyncio.Queue = asyncio.Queue()
    
    def register_agent(self, agent: 'BaseAgent'):
        self.agents[agent.agent_id] = agent
        logger.info(f"Agent {agent.agent_id} registered")
    
    async def send_message(self, message: A2AMessage):
        if message.receiver in self.agents:
            await self.agents[message.receiver].receive_message(message)
        else:
            logger.error(f"Agent {message.receiver} not found")
    
    async def discover_agents(self, agent_type: AgentType) -> List[str]:
        return [agent_id for agent_id, agent in self.agents.items() 
                if agent.agent_type == agent_type]

class BaseAgent:
    def __init__(self, agent_id: str, agent_type: AgentType, a2a_protocol: A2AProtocol):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.a2a = a2a_protocol
        self.a2a.register_agent(self)
    
    async def receive_message(self, message: A2AMessage):
        logger.info(f"{self.agent_id} received message from {message.sender}")
        if message.message_type == MessageType.REQUEST:
            try:
                response = await self.process_request(message.payload)
                response_msg = A2AMessage(
                    id=str(uuid.uuid4()),
                    sender=self.agent_id,
                    receiver=message.sender,
                    message_type=MessageType.RESPONSE,
                    payload=response,
                    timestamp=datetime.now(),
                    correlation_id=message.id
                )
                await self.a2a.send_message(response_msg)
            except Exception as e:
                logger.error(f"Error processing request in {self.agent_id}: {str(e)}")
                response_msg = A2AMessage(
                    id=str(uuid.uuid4()),
                    sender=self.agent_id,
                    receiver=message.sender,
                    message_type=MessageType.ERROR,
                    payload={"error": str(e), "request_id": message.payload.get("request_id")},
                    timestamp=datetime.now(),
                    correlation_id=message.id
                )
                await self.a2a.send_message(response_msg)
    
    async def process_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

class MasterAgent(BaseAgent):
    def __init__(self, a2a_protocol: A2AProtocol):
        super().__init__("master_agent", AgentType.MASTER, a2a_protocol)
        self.active_requests: Dict[str, Dict] = {}
    
    async def plan_travel(self, travel_request: TravelRequest) -> Dict[str, Any]:
        request_id = str(uuid.uuid4())
        logger.info(f"Starting travel planning for request {request_id}")
        
        # Initialize responses dictionary
        responses = {dest: {} for dest in travel_request.destinations}
        if travel_request.is_roundtrip:
            responses[travel_request.departure_city] = {}  # For return flight
        
        self.active_requests[request_id] = {
            "travel_request": travel_request,
            "responses": responses,
            "status": "in_progress"
        }
        
        tasks = []
        flight_agents = await self.a2a.discover_agents(AgentType.FLIGHT)
        hotel_agents = await self.a2a.discover_agents(AgentType.HOTEL)
        activity_agents = await self.a2a.discover_agents(AgentType.ACTIVITIES)
        
        # Calculate duration per destination
        try:
            start_date = datetime.strptime(travel_request.start_date, "%Y-%m-%d")
            end_date = datetime.strptime(travel_request.end_date, "%Y-%m-%d")
            total_days = (end_date - start_date).days
            if total_days <= 0:
                raise ValueError("End date must be after start date")
            days_per_destination = total_days // len(travel_request.destinations)
        except ValueError as e:
            logger.error(f"Invalid date format or range: {str(e)}")
            return {"error": f"Invalid date format or range: {str(e)}"}
        
        # Request flights
        if flight_agents:
            cities = [travel_request.departure_city] + travel_request.destinations
            if travel_request.is_roundtrip:
                cities.append(travel_request.departure_city)
            num_flight_segments = len(cities) - 1
            for i in range(num_flight_segments):
                departure = cities[i]
                destination = cities[i + 1]
                flight_date = (start_date + timedelta(days=i * days_per_destination)).strftime("%Y-%m-%d")
                tasks.append(self._request_flights(
                    flight_agents[0], travel_request, request_id, departure, destination, flight_date
                ))
        
        # Request hotels and activities for each destination
        for i, dest in enumerate(travel_request.destinations):
            check_in = (start_date + timedelta(days=i * days_per_destination)).strftime("%Y-%m-%d")
            check_out = (start_date + timedelta(days=(i + 1) * days_per_destination)).strftime("%Y-%m-%d")
            if hotel_agents:
                tasks.append(self._request_hotels(hotel_agents[0], travel_request, request_id, dest, check_in, check_out))
            if activity_agents:
                tasks.append(self._request_activities(activity_agents[0], travel_request, request_id, dest, check_in, check_out))
        
        try:
            await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            logger.error(f"Error gathering tasks: {str(e)}")
            return {"error": f"Failed to gather responses: {str(e)}"}
        
        itinerary = self._compile_itinerary(request_id)
        del self.active_requests[request_id]
        return itinerary
    
    async def _request_flights(self, flight_agent_id: str, travel_request: TravelRequest, request_id: str, 
                             departure_city: str, destination_city: str, flight_date: str):
        message = A2AMessage(
            id=str(uuid.uuid4()),
            sender=self.agent_id,
            receiver=flight_agent_id,
            message_type=MessageType.REQUEST,
            payload={
                "request_id": request_id,
                "departure_city": departure_city,
                "destination": destination_city,
                "flight_date": flight_date,
                "travelers": travel_request.travelers,
                "budget": travel_request.budget * 0.4 / (len(travel_request.destinations) + (1 if travel_request.is_roundtrip else 0))
            },
            timestamp=datetime.now()
        )
        await self.a2a.send_message(message)
    
    async def _request_hotels(self, hotel_agent_id: str, travel_request: TravelRequest, request_id: str, 
                             destination: str, check_in: str, check_out: str):
        message = A2AMessage(
            id=str(uuid.uuid4()),
            sender=self.agent_id,
            receiver=hotel_agent_id,
            message_type=MessageType.REQUEST,
            payload={
                "request_id": request_id,
                "destination": destination,
                "check_in": check_in,
                "check_out": check_out,
                "travelers": travel_request.travelers,
                "budget": travel_request.budget * 0.4 / len(travel_request.destinations),
                "preferences": travel_request.preferences.get("hotel", {})
            },
            timestamp=datetime.now()
        )
        await self.a2a.send_message(message)
    
    async def _request_activities(self, activity_agent_id: str, travel_request: TravelRequest, request_id: str, 
                                destination: str, start_date: str, end_date: str):
        message = A2AMessage(
            id=str(uuid.uuid4()),
            sender=self.agent_id,
            receiver=activity_agent_id,
            message_type=MessageType.REQUEST,
            payload={
                "request_id": request_id,
                "destination": destination,
                "start_date": start_date,
                "end_date": end_date,
                "travelers": travel_request.travelers,
                "budget": travel_request.budget * 0.2 / len(travel_request.destinations),
                "preferences": travel_request.preferences.get("activities", {})
            },
            timestamp=datetime.now()
        )
        await self.a2a.send_message(message)
    
    async def receive_message(self, message: A2AMessage):
        if message.message_type == MessageType.RESPONSE:
            request_id = message.payload.get("request_id")
            if request_id in self.active_requests:
                sender_type = message.sender.split("_")[0]
                destination = message.payload.get("destination")
                if destination in self.active_requests[request_id]["responses"]:
                    self.active_requests[request_id]["responses"][destination][sender_type] = message.payload
                    logger.info(f"Received {sender_type} response for {destination} in request {request_id}")
                else:
                    logger.warning(f"Received response for unexpected destination {destination} in request {request_id}")
        elif message.message_type == MessageType.ERROR:
            logger.error(f"Received error from {message.sender}: {message.payload.get('error')}")
    
    def _compile_itinerary(self, request_id: str) -> Dict[str, Any]:
        responses = self.active_requests[request_id]["responses"]
        travel_request = self.active_requests[request_id]["travel_request"]
        
        itinerary = {
            "destinations": travel_request.destinations,
            "is_roundtrip": travel_request.is_roundtrip,
            "dates": f"{travel_request.start_date} to {travel_request.end_date}",
            "travelers": travel_request.travelers,
            "flights": [],
            "itinerary": {},
            "total_estimated_cost": 0.0,
            "generated_at": datetime.now().isoformat()
        }
        
        # Collect all flights
        cities = [travel_request.departure_city] + travel_request.destinations
        if travel_request.is_roundtrip:
            cities.append(travel_request.departure_city)
        for i in range(len(cities) - 1):
            destination = cities[i + 1]
            if destination in responses and "flight" in responses.get(destination, {}):
                flight_options = responses[destination]["flight"].get("options", [])
                itinerary["flights"].extend(flight_options)
            else:
                logger.warning(f"No flight options found for destination {destination}")
        
        # Organize hotels and activities by destination
        for dest in travel_request.destinations:
            itinerary["itinerary"][dest] = {
                "hotels": responses.get(dest, {}).get("hotel", {}).get("options", []),
                "activities": responses.get(dest, {}).get("activities", {}).get("options", [])
            }
        
        itinerary["total_estimated_cost"] = self._calculate_total_cost(responses, travel_request)
        return itinerary
    
    def _calculate_total_cost(self, responses: Dict, travel_request: TravelRequest) -> float:
        total = 0.0
        cities = travel_request.destinations + ([travel_request.departure_city] if travel_request.is_roundtrip else [])
        for dest in cities:
            if "flight" in responses.get(dest, {}) and responses[dest]["flight"].get("options"):
                total += responses[dest]["flight"]["options"][0]["price"]
        for dest in travel_request.destinations:
            if "hotel" in responses.get(dest, {}) and responses[dest]["hotel"].get("options"):
                hotel = responses[dest]["hotel"]["options"][0]
                nights = 3  # Simplified
                total += hotel["price_per_night"] * nights
            if "activities" in responses.get(dest, {}) and responses[dest]["activities"].get("options"):
                for activity in responses[dest]["activities"]["options"][:2]:
                    total += activity["price"]
        return total

class FlightAgent(BaseAgent):
    def __init__(self, a2a_protocol: A2AProtocol):
        super().__init__("flight_agent", AgentType.FLIGHT, a2a_protocol)
    
    async def process_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Processing flight request from {payload['departure_city']} to {payload['destination']}")
        await asyncio.sleep(1)
        
        flights = [
            FlightOption(
                airline="AirLine One",
                departure_city=payload["departure_city"],
                destination_city=payload["destination"],
                departure_time="08:00",
                arrival_time="12:00",
                price=450.0,
                duration="4h 00m"
            ),
            FlightOption(
                airline="Sky Express",
                departure_city=payload["departure_city"],
                destination_city=payload["destination"],
                departure_time="14:30",
                arrival_time="18:45",
                price=380.0,
                duration="4h 15m"
            )
        ]
        
        return {
            "request_id": payload["request_id"],
            "destination": payload["destination"],
            "status": "success",
            "options": [asdict(flight) for flight in flights]
        }

class HotelAgent(BaseAgent):
    def __init__(self, a2a_protocol: A2AProtocol):
        super().__init__("hotel_agent", AgentType.HOTEL, a2a_protocol)
    
    async def process_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Processing hotel request for {payload['destination']}")
        await asyncio.sleep(1.2)
        
        hotels = [
            HotelOption(
                name="Grand Plaza Hotel",
                rating=4.5,
                price_per_night=150.0,
                amenities=["WiFi", "Pool", "Gym"],
                location="Downtown",
                city=payload["destination"]
            ),
            HotelOption(
                name="Comfort Inn",
                rating=4.0,
                price_per_night=95.0,
                amenities=["WiFi", "Breakfast"],
                location="City Center",
                city=payload["destination"]
            )
        ]
        
        return {
            "request_id": payload["request_id"],
            "destination": payload["destination"],
            "status": "success",
            "options": [asdict(hotel) for hotel in hotels]
        }

class ActivitiesAgent(BaseAgent):
    def __init__(self, a2a_protocol: A2AProtocol):
        super().__init__("activities_agent", AgentType.ACTIVITIES, a2a_protocol)
    
    async def process_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Processing activities request for {payload['destination']}")
        await asyncio.sleep(0.8)
        
        activities = [
            ActivityOption(
                name="City Walking Tour",
                type="Cultural",
                price=25.0,
                duration="3 hours",
                rating=4.7,
                city=payload["destination"]
            ),
            ActivityOption(
                name="Food Tour",
                type="Culinary",
                price=65.0,
                duration="4 hours",
                rating=4.8,
                city=payload["destination"]
            )
        ]
        
        return {
            "request_id": payload["request_id"],
            "destination": payload["destination"],
            "status": "success",
            "options": [asdict(activity) for activity in activities]
        }

async def main():
    a2a = A2AProtocol()
    master = MasterAgent(a2a)
    flight_agent = FlightAgent(a2a)
    hotel_agent = HotelAgent(a2a)
    activities_agent = ActivitiesAgent(a2a)
    
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
    
    print("🌍 Starting Automated Travel Planning...")
    print(f"Destinations: {', '.join(travel_request.destinations)}")
    print(f"Roundtrip: {travel_request.is_roundtrip}")
    print(f"Dates: {travel_request.start_date} to {travel_request.end_date}")
    print(f"Budget: ${travel_request.budget}")
    print(f"Travelers: {travel_request.travelers}")
    print("\n" + "="*50)
    
    itinerary = await master.plan_travel(travel_request)
    
    if "error" in itinerary:
        print(f"\n❌ Error: {itinerary['error']}")
        return
    
    print("\n✈️ COMPLETE TRAVEL ITINERARY")
    print("="*50)
    print(f"Destinations: {', '.join(itinerary['destinations'])}")
    print(f"Travel Dates: {itinerary['dates']}")
    print(f"Number of Travelers: {itinerary['travelers']}")
    
    print("\n🛫 FLIGHT ITINERARY:")
    for i, flight in enumerate(itinerary["flights"], 1):
        print(f"  {i}. {flight['airline']} from {flight['departure_city']} to {flight['destination_city']} - ${flight['price']}")
        print(f"     Departure: {flight['departure_time']} | Duration: {flight['duration']}")
    
    for dest in itinerary["itinerary"]:
        print(f"\n📍 {dest}")
        print("  🏨 HOTEL OPTIONS:")
        for i, hotel in enumerate(itinerary["itinerary"][dest]["hotels"], 1):
            print(f"    {i}. {hotel['name']} - ${hotel['price_per_night']}/night")
            print(f"       Rating: {hotel['rating']}⭐ | Location: {hotel['location']}")
        
        print("  🎯 ACTIVITY OPTIONS:")
        for i, activity in enumerate(itinerary["itinerary"][dest]["activities"], 1):
            print(f"    {i}. {activity['name']} - ${activity['price']}")
            print(f"       Type: {activity['type']} | Duration: {activity['duration']} | Rating: {activity['rating']}⭐")
    
    print(f"\n💰 ESTIMATED TOTAL COST: ${itinerary['total_estimated_cost']:.2f}")
    print(f"Generated at: {itinerary['generated_at']}")

if __name__ == "__main__":
    asyncio.run(main())