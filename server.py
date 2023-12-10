import mesa

from agents import HumanAgent, HouseAgent, MosquitoAgent, WaterAgent
from model import MalariaInfectionModel

def agents_portrayal(agent):
    if agent is None:
        return

    portrayal = {}

    if type(agent) is HumanAgent:
        portrayal["Shape"] = "./images/human.png"
        portrayal["scale"] = 0.9
        portrayal["Layer"] = 1
        portrayal["text"] = str(agent.seir)[5:8]
        portrayal["text_color"] = ["#84e184", "#adebad", "#d6f5d6"]
    elif type(agent) is MosquitoAgent:
        portrayal["Shape"] = "./images/mosquito.png"
        portrayal["scale"] = 0.9
        portrayal["Layer"] = 1
        portrayal["text"] = str(agent.seir)[5:8]
        portrayal["Color"] = ["#84e184", "#adebad", "#d6f5d6"]
    elif type(agent) is HouseAgent:
        portrayal["Shape"] = "./images/house.png"
        portrayal["scale"] = 0.9
        portrayal["Layer"] = 0
    elif type(agent) is WaterAgent:
        portrayal["Shape"] = "./images/lake.png"
        portrayal["Filled"] = "true"
        portrayal["Layer"] = 0
        portrayal["w"] = 1
        portrayal["h"] = 1
    return portrayal

model_params = {
    "title": mesa.visualization.StaticText("Parameters:"),
    "width": 10, "height": 10, 
    "initial_mosquitos": mesa.visualization.Slider("Initial Mosquitos", 5, 1, 200), 
    "initial_humans": mesa.visualization.Slider("Initial Humans", 5, 1, 200),  
    "houses": mesa.visualization.Slider("Initial Houses", 3, 1, 50), 
    "ponds": mesa.visualization.Slider("Initial Ponds", 5, 1, 50), 
    "percentage_of_infected_humans": 0.5, "human_incubation_period": 20, "human_infection_period": 30,
    "human_recovery_probability": 0.3, "mosquito_incubation_period": 15, "mosquito_life_time": 100,
    "mosquito_larvae_period": 20, "mosquito_probability_of_exposition": 0.2, "human_suspectible_probability": 0.1}

grid = mesa.visualization.CanvasGrid(agents_portrayal, 10, 10, 500, 500)
chart_component = mesa.visualization.ChartModule([
    {"Label": "Humans", "Color": "#AA0000"},
    {"Label": "Mosquitos", "Color": "#666666"},
])

server = mesa.visualization.ModularServer(
    MalariaInfectionModel, [grid, chart_component], "Spread of Malaria - model", model_params)
server.port = 8521
server.launch()