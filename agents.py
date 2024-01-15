import mesa
import uuid
from enum import Enum
from mesa.model import Model
import random
from copy import copy


def new_uuid():
    # Generate a UUID
    unique_id = uuid.uuid4()

    # Convert the UUID to an integer
    int_uuid = int(unique_id.int)

    return int_uuid


class SEIR(Enum):
    SUSCEPTIBLE = 1
    EXPOSED = 2
    INFECTED = 3
    RECOVERED = 4


class LIFE_STAGE(Enum):
    LARVAE = 1
    ADULT = 2


class HumanAgent(mesa.Agent):
    """
    If a mosquito bites a human, then the MosquitoAgent is responsible for changing human's seir to EXPOSED. After incubation period
    human's state is changed to INFECTED. After infection_period human has recovery_probability of changing to RECOVERED. If human
    is not recovered then it dies
    """

    def __init__(self, unique_id, model, seir: SEIR = SEIR.SUSCEPTIBLE, **kwargs):
        super().__init__(unique_id, model)
        self.incubation_period = random.randint(kwargs["human_incubation_period_range"][0],
                                                kwargs["human_incubation_period_range"][1])
        self.recovery_probability = kwargs["human_recovery_probability_multiplier"]
        self.susceptible_probability = kwargs["human_susceptible_probability_multiplier"]

        self.time_exposed = 0
        self.time_infected = 0
        self.time_recovered = 0
        self.prev_day = copy(model.day_count)
        self.day_of_infection = None if seir == SEIR.SUSCEPTIBLE or seir == SEIR.RECOVERED else copy(model.day_count)
        self.day_of_recovery = None if seir != SEIR.RECOVERED else copy(model.day_count)
        self.seir = seir
        self.type = "Human"

    def move(self):
        possible_steps = self.model.grid.get_neighborhood(
            self.pos, moore=True, include_center=False)
        new_position = self.random.choice(list(possible_steps))
        self.model.grid.move_agent(self, new_position)

    def check_seir(self):
        dead = False
        if self.seir == SEIR.EXPOSED:
            if self.time_exposed < self.incubation_period:
                if self.prev_day != self.model.day_count:
                    self.time_exposed += 1
            else:
                self.seir = SEIR.INFECTED
                self.time_exposed = 0
                self.day_of_infection = copy(self.model.day_count)
                self.time_infected = 0
        elif self.seir == SEIR.INFECTED:
            # if self.time_infected < self.infection_period:
            #     if self.prev_day != self.model.day_count:
            #         self.time_infected += 1
            # else:
            #     if random.random() < self.recovery_probability * (self.model.day_count - self.day_of_infection):
            #         self.time_infected = 0
            #         self.seir = SEIR.RECOVERED
            #         self.day_of_recovery = copy(self.model.day_count)
            #     else:
            #         self.die()
            #         dead = True
            if self.prev_day != self.model.day_count:
                self.time_infected += 1
                if random.random() < self.recovery_probability * self.time_infected:
                    self.time_infected = 0
                    self.time_recovered = 0
                    self.seir = SEIR.RECOVERED
                    self.day_of_recovery = copy(self.model.day_count)
        elif self.seir == SEIR.RECOVERED:
            if random.random() < self.susceptible_probability * self.time_recovered:
                self.seir = SEIR.SUSCEPTIBLE
                self.time_recovered = 0
            else:
                if self.prev_day != self.model.day_count:
                    self.time_recovered += 1
        return dead

    def die(self):
        self.model.schedule.remove(self)
        self.model.grid.remove_agent(self)
        self.model.remove_agent(self)


    def step(self):
        if self.check_seir():
            return
        self.move()
        self.prev_day = copy(self.model.day_count)


class MosquitoAgent(mesa.Agent):
    """
    Mosquitos can be in one of two life stages LARVAE or ADULT. Only adult mosquitos can move and be malaria vectors.

    If self.looking_for_water is equal to False, then mosquito is looking for a human. When mosquito is looking for a human it moves one cell
    in random direction until it lands in one cell with a human. After biting a human, mosquito changes self.looking_for_water to True.
    Now it is moving in random direction to find a water source and it doesn't care about humans.

    If it finds a cell with other agent of type "Water" it creates some number of new LARVAE mosquitos in this cell. After
    creating new larves, mosquito changes self.looking_for_water again to False and again searches for human. 

    If mosquito is in one cell with an agent of type "House" and the house has net or spray, it has some chance of being repelled 
    (if mosquito is repelled it doesn't die and doesn't bite, just continues to move). If it wasn't repelled then there is a chance of
    killing a mosquito. If mosquito both isn't repelled and doesn't die, then it can still bite a human if the human is also present in 
    this cell

    """

    def __init__(self, unique_id, model, life_stage: LIFE_STAGE = LIFE_STAGE.ADULT, seir: SEIR = SEIR.SUSCEPTIBLE,
                 **kwargs):
        super().__init__(unique_id, model)
        self.kwargs_from_init = kwargs # safe kwargs in order to pass them while creating eggs
        # Life stages
        self.life_stage = life_stage
        self.larvae_period = random.randint(kwargs["mosquito_larvae_period_range"][0],
                                            kwargs["mosquito_larvae_period_range"][1])
        if life_stage == LIFE_STAGE.ADULT:
            self.current_life_step = self.larvae_period
        else:
            self.current_life_step = 0
        self.life_time = self.larvae_period + random.randint(kwargs["mosquito_adult_life_range"][0],
                                                             kwargs["mosquito_adult_life_range"][1])

        # Reproduction
        self.daily_min_eggs_laid = kwargs["mosquito_daily_min_eggs_laid"]
        self.daily_max_eggs_laid = kwargs["mosquito_daily_max_eggs_laid"]
        self.lifetime_max_eggs = kwargs["mosquito_lifetime_max_eggs"]
        self.eggs_laid_during_day = 0
        self.total_eggs_laid = 0

        # Incubation and infections
        self.time_exposed = 0
        self.seir = seir
        self.incubation_period = random.randint(kwargs["mosquito_incubation_period_range"][0],
                                                kwargs["mosquito_incubation_period_range"][1])
        self.probability_of_exposition = kwargs["mosquito_probability_of_exposition"]
        self.probability_of_infecting_human = kwargs["mosquito_probability_of_infecting_human"]

        # Movement
        self.daily_steps_available = kwargs["mosquito_daily_steps"]
        self.remaining_steps = kwargs["mosquito_daily_steps"]

        self.type = "Mosquito"
        self.looking_for_water = False
        self.prev_day = copy(model.day_count)

    def move(self):
        if self.life_stage == LIFE_STAGE.ADULT and self.remaining_steps > 0:
            possible_steps = self.model.grid.get_neighborhood(
                self.pos, moore=True, include_center=False)
            new_position = self.random.choice(possible_steps)
            self.remaining_steps -= 1
            self.model.grid.move_agent(self, new_position)

    def reset_steps(self):
        self.remaining_steps = self.daily_steps_available

    def reset_eggs(self):
        self.eggs_laid_during_day = 0

    def bite(self, human: HumanAgent):
        txt = f"before bite m={self.seir}, h={human.seir}"
        if human.seir == SEIR.INFECTED and self.seir == SEIR.SUSCEPTIBLE:
            if random.random() < self.probability_of_exposition:
                self.seir = SEIR.EXPOSED
        elif self.seir == SEIR.INFECTED and human.seir == SEIR.SUSCEPTIBLE:
            if random.random() < self.probability_of_infecting_human:
                human.seir = SEIR.EXPOSED
        txt += f" | after bite m={self.seir}, h={human.seir}"

    def die(self):
        self.model.remove_agent(self)
        self.model.grid.remove_agent(self)


    def check_life_stage(self):
        dead_or_larvae = False
        if self.life_stage == LIFE_STAGE.LARVAE and self.current_life_step < self.larvae_period:
            dead_or_larvae = True
        elif self.life_stage == LIFE_STAGE.LARVAE and self.current_life_step >= self.larvae_period:
            # change from larvae to adult
            self.life_stage = LIFE_STAGE.ADULT
        elif self.life_stage == LIFE_STAGE.ADULT and self.current_life_step >= self.life_time:
            self.die()
            dead_or_larvae = True
        return dead_or_larvae

    def check_seir(self):
        if self.seir == SEIR.EXPOSED:
            if self.time_exposed < self.incubation_period:
                if self.prev_day != self.model.day_count:
                    self.time_exposed += 1
            else:
                self.seir = SEIR.INFECTED
                self.time_exposed = 0

    def lay_eggs(self):
        number_of_eggs = random.randint(self.daily_min_eggs_laid, self.daily_max_eggs_laid)
        for _ in range(number_of_eggs):
            if self.eggs_laid_during_day >= self.daily_max_eggs_laid:
                break
            a = MosquitoAgent(new_uuid(), self.model, life_stage=LIFE_STAGE.LARVAE,
                              seir=self.seir, **self.kwargs_from_init)
            self.eggs_laid_during_day += 1
            self.total_eggs_laid += 1
            self.model.new_mosquitos.append((a, self.pos))

    def bite_or_eggs(self):
        cellmates = self.model.grid.get_cell_list_contents([self.pos])
        if self.looking_for_water and self.total_eggs_laid < self.lifetime_max_eggs:
            for c in cellmates:
                if c.type == "Water":
                    self.lay_eggs()
                    self.looking_for_water = False
                    break
        else:
            for c in cellmates:
                if c.type == "Human":
                    self.bite(c)
                    if self.total_eggs_laid < self.lifetime_max_eggs:
                        self.looking_for_water = True
                    break

    def check_house_net(self):
        dead_or_repelled = False
        cellmates = self.model.grid.get_cell_list_contents([self.pos])
        house = None
        for c in cellmates:
            if c.type == "House":
                house = c
                break
        if house is not None:
            action = "enter"
            if house.mosquito_spray:
                action = random.choice(["repel", "kill", "enter"])
            if action == "kll":
                dead_or_repelled = True
                self.die()
            elif action == "repel":
                dead_or_repelled = True
                self.move()
        return dead_or_repelled

    def check_house_spray(self):
        dead_or_repelled = False
        cellmates = self.model.grid.get_cell_list_contents([self.pos])
        house = None
        for c in cellmates:
            if c.type == "House":
                house = c
                break
        if house is not None:
            action = "enter"
            if house.mosquito_net:
                action = random.choice(["repel", "kill", "enter"])
            if action == "kill":
                dead_or_repelled = True
                self.die()
            elif action == "repel":
                dead_or_repelled = True
                self.move()
        return dead_or_repelled

    def step(self):
        if self.prev_day != self.model.day_count:
            self.current_life_step += 1
            self.reset_steps()
            self.reset_eggs()
        if self.check_life_stage():
            self.prev_day = copy(self.model.day_count)
            return
        self.check_seir()
        self.move()
        if self.check_house_net():
            self.prev_day = copy(self.model.day_count)
            return
        self.bite_or_eggs()
        self.check_house_spray()
        self.prev_day = copy(self.model.day_count)


class HouseAgent(mesa.Agent):
    """Agent representing a house. It doesn't move"""

    def __init__(self, unique_id, model, mosquito_net: bool, mosquito_spray: bool):
        super().__init__(unique_id, model)
        self.mosquito_net = mosquito_net
        self.mosquito_spray = mosquito_spray
        self.type = "House"

    def step(self):
        pass


class WaterAgent(mesa.Agent):
    """Agent representing a water source. It doesn't move and doesn't have any extra properties"""

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.type = "Water"

    def step(self):
        pass
