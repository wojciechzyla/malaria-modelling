import random

import mesa

from agents import new_uuid, SEIR, HumanAgent, MosquitoAgent, WaterAgent, HouseAgent, LIFE_STAGE


class MalariaInfectionModel(mesa.Model):
    """A model with some number of agents."""

    def __init__(self, width, height, initial_mosquitos, initial_humans, houses, ponds, percentage_of_infected_humans,
                 human_incubation_period, human_infection_period, human_recovery_probability,
                 mosquito_incubation_period, mosquito_life_time, mosquito_larvae_period,human_suspectible_probability, mosquito_daily_steps_available):

        self.schedule = mesa.time.RandomActivation(self)
        self.grid = mesa.space.MultiGrid(width, height, True)
        self.day_count = 0  # number of day
        self.day_step = 0  # each day has 24 simulation steps

        self.datacollector = mesa.DataCollector(
            {
                "Humans": lambda m: sum([1 for agent in m.schedule.agents if isinstance(agent, HumanAgent)]),
                "Mosquitos": lambda m: sum([1 for agent in m.schedule.agents if isinstance(agent, MosquitoAgent)]),
            }
        )

        # Create human agents
        infected_humans = int(percentage_of_infected_humans * initial_humans)
        susceptible_humans = initial_humans - infected_humans
        for _ in range(infected_humans):
            a = HumanAgent(new_uuid(), self, incubation_period=human_incubation_period,
                           infection_period=human_infection_period,
                           recovery_probability=human_recovery_probability,
                           suspectible_probability=human_suspectible_probability, seir=SEIR.INFECTED)
            # Add the agent to a random grid cell
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(a, (x, y))
            self.schedule.add(a)
        for _ in range(susceptible_humans):
            a = HumanAgent(new_uuid(), self, incubation_period=human_incubation_period,
                           infection_period=human_infection_period,
                           recovery_probability=human_recovery_probability,
                           suspectible_probability=human_suspectible_probability, seir=SEIR.SUSCEPTIBLE)
            # Add the agent to a random grid cell
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(a, (x, y))
            self.schedule.add(a)

        # Create mosquito agents
        for _ in range(initial_mosquitos):
            a = MosquitoAgent(new_uuid(), self, life_time=mosquito_life_time,
                              incubation_period=mosquito_incubation_period,
                              daily_steps_available=mosquito_daily_steps_available,
                              larvae_period=mosquito_larvae_period,
                              life_stage=random.choice(list(LIFE_STAGE)), seir=SEIR.SUSCEPTIBLE)
            # Add the agent to a random grid cell
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(a, (x, y))
            self.schedule.add(a)

        # Create house agents
        for _ in range(houses):
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
        for _ in range(ponds):
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
        if self.day_step == 24:
            self.day_step = 0
            self.day_count += 1
            for i, agent in enumerate(self.schedule.agents):
                if agent.type == "Mosquito":
                    agent.reset_steps()
                    agent.reset_eggs()

