#!/usr/bin/env python
# -*- coding: utf8 -*-
"""
#########################################################
#
#    population.py
#    Author: Dion Häfner (dionhaefner@web.de)
#    
#    Implements Population class
#    
#    Licensed under BSD 2-Clause License
#
#########################################################
"""

#import numbers
import numpy as np
import time

from numba import jit


from constants import model_constants # Import model constants
from animal import Animal

    
class Population:
    def __init__(self,size,animals):
        """Takes a population size and a list of Animal as input"""
        if (isinstance(size,int) & (all(isinstance(x,Animal) for x in animals))):
            if (size == len(animals)):
                self._animals     = np.array(animals)
                self._size = size
                self._constants    = model_constants
            else:
                raise ValueError('The size parameter must be equal to the length of the list of animals.')
        else:
            raise TypeError('First argument must be of type int, second of type list of Animals.')

    def animals(self):
        """Returns the ndarray of animals"""
        return self._animals

    def size(self):
        """Returns the current size of the population"""
        return self._size



    def react(self,E,C,evolve_all=False):
        """Calculates the insulation of each Animal in the Population based on cue C and environment E"""                              
        for animal in self._animals:           
            animal.react(E,C,evolve_all)#animal reacts to environment, possibly migrates               

    def breed_constant(self):
        """Iterates the entire Population to a new generation, calculating the number of offspring of each Animal with CONSTANT population size"""
        calc_payoff     = np.vectorize(lambda x: x.lifetime_payoff())
        lifetime_payoff = calc_payoff(self._animals)
        #print(list(lifetime_payoff))
        mean_payoff  = np.mean(lifetime_payoff)
        population_size=self._constants["environment_sizes"]
        if (mean_payoff == 0):
            raise RuntimeError("Mean payoff of population decreased to 0. Check your parameters!")
        else:
            payoff_factor = lifetime_payoff/mean_payoff                                        
        offspring = np.random.poisson(lam=payoff_factor) #number of offspring drawn from Poisson distr for each animal 
    #    print(offspring)
    #    print(payoff_factor)

        d=np.sum(offspring)-population_size
        
        if self._constants["random_choice"]:    
            Ind=np.arange(0,len(offspring)) #all indices
            I=Ind[(offspring>0)] # array of relevant indices to choose from
            if len(I)==0: 
                I=Ind
            if d>0:#if environment overcrowded reduce offspring randomly
                add=-1
            else:#if too few, increase offspring randomly
                add=1
            for i in range(abs(d)):  
                stop=False
                while not stop:
                    m=np.random.choice(I)
                    if  offspring[m]!=0 or sum(offspring)==0: #animals with zero offspring are disregarded unless there is no offspring
                        offspring[m]+=add
                        stop=True
        else:
            pf=np.array(payoff_factor)
            if d>0:#if environment overcrowded let the least fit animals have less offspring
                mx=np.max(pf)
                pf[offspring==0]=mx+1 #to make sure that no animals with offspring 0  are selected
                for i in range(d):                         
                    m=np.argmin(pf)
                    offspring[m]-=1
                    if offspring[m]==0:
                        pf[m]=mx+1
                
            elif d<0:#if too few, clone the fittest animals                
                for i in range(-d):                     
                    m=np.argmax(pf)
                    pf[m]=0 #to ensure that not all additional offspring is from one animal
                    offspring[m]+=1  
    #    print(offspring)                                           
        born_animals = np.repeat(self._animals,offspring) # Create list with offspring repeats for each animal (cloned animals)      
        mutate_pop = np.vectorize(lambda x: Animal(x.mutate(),x.lineage)) #animals are created with mutated genes of their parents
        new_animals = mutate_pop(born_animals) #create and mutate offspring (use mutated genes as parent genes)      
        self._animals = new_animals 
        if self._constants["verbose"]:
            print("Population size: {0}\tMean payoff: {1:.2f}".format(population_size,mean_payoff))
        return d
 #   @jit
    def breed_variable(self):
        """Iterates the entire Population to a new generation, calculating the number of offspring of each Animal with VARIABLE population size"""
        calc_payoff     = np.vectorize(lambda x: x.lifetime_payoff())
        lifetime_payoff = calc_payoff(self._animals)
        payoff_factor=np.array([])
        for j,animal in enumerate(self._animals):
             payoff_factor=np.append(payoff_factor,self._constants["q"]*lifetime_payoff[j])
        offspring     = np.random.poisson(lam=payoff_factor)             
        d=np.sum(offspring)-self._constants["environment_sizes"]    
        if d>0:
            if self._constants["random_choice"]:    
                I=np.arange(0,len(offspring))[offspring>0] # array of relevant indices to choose from  
                for i in range(d):  
                    stop=False
                    while not stop:
                        m=np.random.choice(I)
                        if  offspring[m]!=0: #animals with zero offspring are disregarded 
                            offspring[m]-=1
                            stop=True
            else:
                pf=np.array(payoff_factor)
                if d>0:#if environment overcrowded let the least fit animals have less offspring
                    mx=np.max(pf)
                    pf[offspring==0]=mx+1 #to make sure that no animals with offspring 0 or from other environment are selected
                    for i in range(d):                         
                        m=np.argmin(pf)
                        offspring[m]-=1
                        if offspring[m]==0:
                            pf[m]=mx+1
        born_animals   = np.repeat(self._animals,offspring)
        try: # check if all animals are dead yet
            born_animals[0]
        except IndexError:
            self._size = 0
            return
        mutate_pop = np.vectorize(lambda x: Animal(x.mutate(),x.lineage))
        new_animals = mutate_pop(born_animals)
        self._animals = new_animals        
        N = len(new_animals)
        self._size=N
        if self._constants["verbose"]:
            print("Population size: {0}".format(N))
        return d          
    def lineage(self):
        '''Returns the lineage of each animal'''
        fun = np.vectorize(lambda x: x.lineage)
        lin = fun(self._animals)
        return np.array(lin,ndmin=1) 

