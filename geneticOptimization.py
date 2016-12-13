import numpy as np
import evaluation
import constants
import random
import visualization
from trafficSim import TrafficSim

class GeneticOptimization(object):
    """
    Contains methods for the optimization of a given fitness function.
    The algorithm works as follows
    1. Randomly create individuals with different properties (parameters)
    2. Selectively cull the population such that only fit individuals survive
    3. Create a new generation of individuals by mutation (randomly adjusting parameters)
    and by crossover between different individuals (mixing of parameters)
    Step 2. and 3. are then iterated a number of generations until (hopefully)
    a "steady-state" is reached.

    This algorithm works for a generalized class of individuals 
    which can be generated by a factory method and provide
    the methods
    1. mutate
    2. crossover
    3. fitness
    """
    def __init__(self, individualFactory):
        self.individualFactory = individualFactory
        # Constants
        self.numIndividuals = 100
        self.numAfterCulling = 10
        self.proportionGeneratedThroughMutation = 1.0
        self.mutationParameter = 0.9
        self.numIterations = 10000
        self.numGeneration = 0
        self.generation = [self.individualFactory() for n in range(self.numIndividuals)]

    def iterate(self):
        self.generation.sort(key=lambda x : x.fitness, reverse=True)
        self.generation = self.generation[:self.numAfterCulling]
        self.outputInfo()
        numToReplenish = self.numIndividuals - self.numAfterCulling
        newIndividuals = [self.getNewIndividual() for i in range(numToReplenish)]
        self.generation = self.generation + newIndividuals
        assert len(self.generation) == self.numIndividuals

    def getNewIndividual(self):
        if random.random() < self.proportionGeneratedThroughMutation:
            randomIndividual = random.choice(self.generation)
            return randomIndividual.mutate(self.mutationParameter)

    def optimize(self):
        for self.numGeneration in range(self.numIterations):
            self.iterate()
    
    def outputInfo(self):
        if self.numGeneration % 100 == 0:
            print("Fittest individual: {}".format(max(self.generation, key=lambda individual:individual.fitness)))
        if self.numGeneration % 1000 == 0:
            visualization.showTrajectory([individual.sim.log for individual in self.generation])

class StrategyDriver(object):
    def __init__(self, acceleration):
        self.acceleration = iter(acceleration)
        
    def act(self, pos, vel, time):
        return next(self.acceleration)

class Strategy(object):
    """
    Contains a generic strategy for approaching a traffic-light
    which is given by a discretized function a(t)
    """
    def __init__(self, acceleration, trafficLight):
        self.acceleration = acceleration
        self.trafficLight = trafficLight
        # Determine fitness by running the simulation
        driver = StrategyDriver(self.acceleration)
        self.sim = TrafficSim(driver, self.trafficLight.maxTime, logging=True)
        self.sim.run()
        self.fitness = evaluation.totalPerformance(self.sim, self.trafficLight)

    def mutate(self, mutationParameter):
        """Create a new strategy by changing each value with probability
        mutationParameter. The changes are uniformly distributed between
        -maxChange and maxChange.
        (mutationParameter = 1 -> All values are changed
         mutationParameter = 0 -> No values are changed)
        Afterwards, truncate each value to physically 
        plausible values (between MIN_ACC and MAX_ACC)"""
        maxChange = 1.0
        doChange = np.random.binomial(n=1, p=mutationParameter, size=len(self.acceleration))
        changeAmount = np.random.uniform(low=-maxChange, high=maxChange, size=len(self.acceleration))
        effectiveChange = doChange * changeAmount
        newValues = self.acceleration + effectiveChange
        truncated = np.clip(newValues, a_min=constants.MIN_ACC, a_max=constants.MAX_ACC)
        return Strategy(truncated, self.trafficLight)

    def __str__(self):
        return str(self.fitness)

def optimize(trafficLight):
    def strategyFactory():
        acceleration = np.random.uniform(
                low = 0, 
                high = constants.MAX_ACC,
                size = constants.NUM_STEPS
            )
        return Strategy(acceleration, trafficLight)
    opt = GeneticOptimization(strategyFactory)
    opt.optimize()
