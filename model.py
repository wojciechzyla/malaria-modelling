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


        self.human_agents = set()
        self.mosquito_agents = set()
        self.house_agents = set()
        self.water_agents = set()
        # Initialize sets for each state
        self.infected_humans = set()
        self.susceptible_humans = set()
        self.exposed_humans = set()
        self.recovered_humans = set()

        self.infected_mosquitos = set()
        self.susceptible_mosquitos = set()
        self.exposed_mosquitos = set()
        self.adult_mosquitos = set()

        self.datacollector = mesa.DataCollector(
            {
                "Humans": lambda m: len(m.human_agents),
                "Mosquitos": lambda m: len(m.mosquito_agents),
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
            self.add_agent(a)
        for _ in range(susceptible_humans):
            a = HumanAgent(new_uuid(), self, seir=SEIR.SUSCEPTIBLE, **kwargs)
            # Add the agent to a random grid cell
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(a, (x, y))
            self.add_agent(a)

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
            self.add_agent(a)
        for _ in range(susceptible_mosquitos):
            a = MosquitoAgent(new_uuid(), self, life_stage=random.choice(list(LIFE_STAGE)),
                              seir=SEIR.SUSCEPTIBLE, **kwargs)
            # Add the agent to a random grid cell
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(a, (x, y))
            self.add_agent(a)

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
            self.add_agent(a)

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
            self.add_agent(a)

    def step(self):
        self.schedule.step()
        self.datacollector.collect(self)
        self.day_step += 1
        for m in self.new_mosquitos:
            self.grid.place_agent(m[0], m[1])
            self.add_agent(m[0])
        self.new_mosquitos.clear()  # clear the list for the next step
        if self.day_step == 24:
            self.day_step = 0
            self.day_count += 1
    def add_agent(self, agent):
        if isinstance(agent, HumanAgent):
            self.human_agents.add(agent)
            if agent.seir == SEIR.INFECTED:
                self.infected_humans.add(agent)
            elif agent.seir == SEIR.SUSCEPTIBLE:
                self.susceptible_humans.add(agent)
            elif agent.seir == SEIR.EXPOSED:
                self.exposed_humans.add(agent)
            elif agent.seir == SEIR.RECOVERED:
                self.recovered_humans.add(agent)
        elif isinstance(agent, MosquitoAgent):
            self.mosquito_agents.add(agent)
            if agent.seir == SEIR.INFECTED:
                self.infected_mosquitos.add(agent)
            elif agent.seir == SEIR.SUSCEPTIBLE:
                self.susceptible_mosquitos.add(agent)
            elif agent.seir == SEIR.EXPOSED:
                self.exposed_mosquitos.add(agent)
            if agent.life_stage == LIFE_STAGE.ADULT:
                self.adult_mosquitos.add(agent)
        elif isinstance(agent, HouseAgent):
            self.house_agents.add(agent)
        elif isinstance(agent, WaterAgent):
            self.water_agents.add(agent)
        self.schedule.add(agent)

    def remove_agent(self, agent):
        if isinstance(agent, HumanAgent):
            self.human_agents.discard(agent)
            self.infected_humans.discard(agent)
            self.susceptible_humans.discard(agent)
            self.exposed_humans.discard(agent)
            self.recovered_humans.discard(agent)
        elif isinstance(agent, MosquitoAgent):
            self.mosquito_agents.discard(agent)
            self.infected_mosquitos.discard(agent)
            self.susceptible_mosquitos.discard(agent)
            self.exposed_mosquitos.discard(agent)
            self.adult_mosquitos.discard(agent)
        elif isinstance(agent, HouseAgent):
            self.house_agents.discard(agent)
        elif isinstance(agent, WaterAgent):
            self.water_agents.discard(agent)
        self.schedule.remove(agent)

    def count_infected_humans(self):
        return len(self.infected_humans)

    def count_susceptible_humans(self):
        return len(self.susceptible_humans)

    def count_exposed_humans(self):
        return len(self.exposed_humans)

    def count_recovered_humans(self):
        return len(self.recovered_humans)

    def count_infected_mosquitos(self):
        return len(self.infected_mosquitos)

    def count_susceptible_mosquitos(self):
        return len(self.susceptible_mosquitos)

    def count_exposed_mosquitos(self):
        return len(self.exposed_mosquitos)

    def count_adult_mosquitos(self):
        return len(self.adult_mosquitos)

    def count_humans(self):
        return sum(1 for agent in self.schedule.agents if isinstance(agent, HumanAgent))

    def count_deaths(self):
        actual_humans = self.count_humans()
        deaths = self.initial_humans - actual_humans
        return deaths