import random

import mesa

from agents import new_uuid, SEIR, HumanAgent, MosquitoAgent, WaterAgent, HouseAgent, LIFE_STAGE


class MalariaInfectionModel(mesa.Model):
    """A model with some number of agents."""
    def __init__(self, **kwargs):

        self.schedule = mesa.time.RandomActivation(self)
        self.grid = mesa.space.MultiGrid(kwargs["width"], kwargs["height"], True)
        self.day_count = 0  # number of day
        self.day_step = 0  # each day has 24 simulation steps
        self.initial_humans = kwargs["initial_humans"]
        self.new_mosquitos = []  # list for storing new mosquitos to add

        self.datacollector = mesa.DataCollector(
            {
                "Humans": lambda m: sum([1 for agent in m.schedule.agents if isinstance(agent, HumanAgent)]),
                "Mosquitos": lambda m: sum([1 for agent in m.schedule.agents if isinstance(agent, MosquitoAgent)]),
            }
        )

        # Create human agents
        infected_humans = int(kwargs["percentage_of_infected_humans"] * kwargs["initial_humans"])
        susceptible_humans = kwargs["initial_humans"] - infected_humans
        for _ in range(infected_humans):
            a = HumanAgent(new_uuid(), self, seir=SEIR.INFECTED, **kwargs)
            # Add the agent to a random grid cell
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(a, (x, y))
            self.schedule.add(a)
        for _ in range(susceptible_humans):
            a = HumanAgent(new_uuid(), self, seir=SEIR.SUSCEPTIBLE, **kwargs)
            # Add the agent to a random grid cell
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(a, (x, y))
            self.schedule.add(a)

        # Create mosquito agents
        infected_mosquitos = int(kwargs["percentage_of_infected_mosquitos"] * kwargs["initial_mosquitos"])
        susceptible_mosquitos = kwargs["initial_mosquitos"] - infected_mosquitos
        for _ in range(infected_mosquitos):
            a = MosquitoAgent(new_uuid(), self, life_stage=random.choice(list(LIFE_STAGE)),
                              seir=SEIR.INFECTED, **kwargs)
            # Add the agent to a random grid cell
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(a, (x, y))
            self.schedule.add(a)
        for _ in range(susceptible_mosquitos):
            a = MosquitoAgent(new_uuid(), self, life_stage=random.choice(list(LIFE_STAGE)),
                              seir=SEIR.SUSCEPTIBLE, **kwargs)
            # Add the agent to a random grid cell
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(a, (x, y))
            self.schedule.add(a)

        # Create house agents
        for _ in range(kwargs["houses"]):
            a = HouseAgent(new_uuid(), self, random.choice([True, False]), random.choice([True, False]))

            collision_with_house_or_water = True

            while collision_with_house_or_water:
                x = self.random.randrange(self.grid.width)
                y = self.random.randrange(self.grid.height)
                cellmates = self.grid.get_cell_list_contents([(x, y)])
                if all(c.type != "House" and c.type != "Water" for c in cellmates):
                    collision_with_house_or_water = False

            self.grid.place_agent(a, (x, y))
            self.schedule.add(a)

        # Create water agents
        for _ in range(kwargs["ponds"]):
            a = WaterAgent(new_uuid(), self)

            collision_with_house_or_water = True

            while collision_with_house_or_water:
                x = self.random.randrange(self.grid.width)
                y = self.random.randrange(self.grid.height)
                cellmates = self.grid.get_cell_list_contents([(x, y)])
                if all(c.type != "House" and c.type != "Water" for c in cellmates):
                    collision_with_house_or_water = False

            self.grid.place_agent(a, (x, y))
            self.schedule.add(a)

    def step(self):
        self.schedule.step()
        self.datacollector.collect(self)
        self.day_step += 1
        for m in self.new_mosquitos:
            self.grid.place_agent(m[0], m[1])
            self.schedule.add(m[0])
        self.new_mosquitos = []  # clear the list for the next step
        if self.day_step == 24:
            self.day_step = 0
            self.day_count += 1

    def count_infected_humans(self):
        return sum(1 for agent in self.schedule.agents if isinstance(agent, HumanAgent) and agent.seir == SEIR.INFECTED)

    def count_susceptible_humans(self):
        return sum(
            1 for agent in self.schedule.agents if isinstance(agent, HumanAgent) and agent.seir == SEIR.SUSCEPTIBLE)

    def count_exposed_humans(self):
        return sum(1 for agent in self.schedule.agents if isinstance(agent, HumanAgent) and agent.seir == SEIR.EXPOSED)

    def count_recovered_humans(self):
        return sum(
            1 for agent in self.schedule.agents if isinstance(agent, HumanAgent) and agent.seir == SEIR.RECOVERED)

    def count_infected_mosquitos(self):
        return sum(
            1 for agent in self.schedule.agents if isinstance(agent, MosquitoAgent) and agent.seir == SEIR.INFECTED)

    def count_susceptible_mosquitos(self):
        return sum(
            1 for agent in self.schedule.agents if isinstance(agent, MosquitoAgent) and agent.seir == SEIR.SUSCEPTIBLE)

    def count_exposed_mosquitos(self):
        return sum(
            1 for agent in self.schedule.agents if isinstance(agent, MosquitoAgent) and agent.seir == SEIR.EXPOSED)

    def count_adult_mosquitos(self):
        return sum(1 for agent in self.schedule.agents if
                   isinstance(agent, MosquitoAgent) and agent.life_stage == LIFE_STAGE.ADULT)

    def count_humans(self):
        human_counter = 0
        for agent in self.schedule.agents:
            if isinstance(agent, HumanAgent):
                human_counter += 1
        return human_counter

    def count_deaths(self):
        actual_humans = self.count_humans()
        deaths = self.initial_humans - actual_humans
        return deaths


