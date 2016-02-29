#!/usr/bin/env python
# -*- coding: utf8 -*-
"""
#########################################################
#
#   output_population.py
#   Author: Dion Häfner (dionhaefner@web.de)
#   
#   Responsible for output and plotting
#   
#   Licensed under BSD 2-Clause License
#
#########################################################
"""

# Import third-party libraries
import numpy as np 
import matplotlib.pyplot as plt 
import pandas as pd
import warnings

# Seaborn makes prettier plots, but is not installed in a fresh Anaconda python
try: 
    import seaborn as sns 
    have_seaborn = True
except ImportError:
    have_seaborn = False

# Import other parts of the project
from animal import Animal
from population import Population
from environment import Environment
from constants import model_constants


def output_population(population,f1,f2,j,k,path,force_plot,t,env):
    """
    Outputs state of the Population. Inputs:
        population: instance of Population to be output, 
        f1: file handle for mean gene file, f2: file handle for standard dev. of genes
        j: current generation counter, k: current population counter,
        path: output path, timeseries: whether complex output should be saved, #???
        t: current time step, env: list of environments
    """
    constants = model_constants
    animals = np.array(population.animals())
    positions = np.array(list(map(lambda x: x.position, animals)))

    nE = len(constants["environments"])
    genes = [list(map(lambda x: x.gene_dict, animals[positions==i])) for i in range(nE)]
    nPerPos = np.array([len(genes[i]) for i in range(nE)])
    data = [pd.DataFrame(genes[i]) for i in range(nE)]
    mean = [pd.DataFrame(data[i].mean()).transpose() for i in range(nE)]
    std = [pd.DataFrame(data[i].std()).transpose() for i in range(nE)]


    for i in range(nE):
        f1.write(str(j)+","+str(i+1)+",") #generation, environment
        f2.write(str(j)+","+str(i+1)+",")

        if nPerPos[i] == 0:
            f1.write("0,0,0,0,0,0,0,0,0")
            f2.write("0,0,0,0,0,0,0,0,0")
        else:
            mean[i].to_csv(f1, header=False, index=False, line_terminator='')
            std[i].to_csv(f2, header=False, index=False, line_terminator='')

        f1.write(","+str(nPerPos[i])) #last number: animals per environment
        f2.write(","+str(nPerPos[i]))

        f1.write("\n")
        f2.write("\n")

    filename = path+'timeseries/pop'+str(k+1)+'_genes_'+str(j)+'.pdf'
    if force_plot:
        plot_situation(t,data,nPerPos,env,filename)
    elif constants["plot_every"] > 0:
        if (j % constants["plot_every"]) == 0: #modulo to plot every n times
            plot_situation(t,data,nPerPos,env,filename)

    return mean, std


def plot_situation(t,data,nPerPos,env,filename):
    constants = model_constants
    if constants["verbose"]:
    	print("\nPlotting ...")

    nE = len(constants["environments"])
    
    plt.figure(figsize=(20,25)) #size adjustment to have axis labels visible
    ax = plt.subplot2grid((5,nE),(0,0),colspan=nE)
    if have_seaborn:
        palette = sns.color_palette("Set2", 4)
        names = np.array(constants["environment_names"])
        if (len(names) != nE):
            warnings.warn("Environment parameter and name arrays have different lengths!\
                Disregarding names.")
            names = ["Environment "+str(q) for q in np.arange(nE)+1]
        pos_data = pd.DataFrame({'env': names, 'val': nPerPos})
        sns.barplot('env','val',data=pos_data,ax=ax,palette=palette,order=names) #animals in environment plot
    else:
        ax.bar(np.array(constants["environment_names"]),nPerPos,0.7)
    ax.set_xlabel("Environments")
    ax.set_ylabel("#Animals")
    ax.set_ylim(0,max(constants["environment_sizes"]))

    for i in range(nE):
        if (nPerPos[i] > 0):
            ax = plt.subplot2grid((5,nE),(1,i),rowspan=2)
        
            if have_seaborn:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    sns.violinplot(data=data[i],ax=ax,scale='width')  #gene plot
            else:
                data[i].boxplot(ax=ax)
        
            ax.set_ylim(-2,2)
            ax.set_xlabel("Genes")
            ax.set_ylabel("Value distribution")

            ax1 = plt.subplot2grid((5,nE),(3,i),rowspan=2)
            scale = 5*constants["L"]*env[i].R #5 whole cycles per plot
            if t <= constants["L"]*constants["generations"]:

                t0 = np.arange(min(max(0,t-scale/2), np.abs(constants["L"]*constants["generations"]-scale)) ,min(constants["L"]*constants["generations"],max(t+scale/2,scale))) #star always in the middle except at beginning and end
            else:
                t0 = np.arange(t-scale/2,t+scale/2)
            ax1.plot(t0,np.array(list(map(env[i].evaluate,t0)))[:,0],color=palette[i]) #plot E(t)
            ax1.scatter(t,env[i].evaluate(t)[0],s=250,color=palette[i],marker='*') #show actual time as *
            ax1.set_ylim(-2,2)
            ax1.set_xlim(t0[0],t0[-1]) 
            ax1.set_xlabel("Time t")
            ax1.set_ylabel("E")#labels und überschriften

    plt.suptitle("The situation at $t = $"+str(t),fontsize=25)
    plt.subplots_adjust(top=0.95)
    plt.savefig(filename)
    plt.close()


def plot_size(path,fi,k): #plots the number of animals in each environment for each generation
    constants = model_constants
    nE = 0
    f = open(fi)
    for (i,row) in enumerate(f):
        if i == 0:
            nE = int(row)  #nE written in first line
        if row[0]=="n":
            data = np.genfromtxt(fi,skip_header=i+1,delimiter=",")
            break

    sizes = data[:,-1].reshape(-1,nE) #[:,-1] gives all elements in the last column (n per position), reshape makes rows corresponding to the generation (nE values per row)
    
    '''to check if total number stays constant'''
#    total=np.arange(constants["generations"])
#    for j in range(constants["generations"]):
#        total[j]=0
#        for i in range(nE):
#            total[j]+=sizes[j,i]
#    print(total)                                            
    plt.figure()
    for i in range(nE):
        plt.plot(sizes[:,i],alpha=0.7,label="Environment "+str(i+1),linewidth=0.5)  #sizes[:,i] gives the elements of the ith column
        plt.legend()
        plt.ylim(0,5000)
        plt.xlabel("Generation")
        plt.ylabel("Number of individuals")
    plt.savefig(str(path)+"sizes_"+str(int(k)+1)+".pdf",bbox_inches='tight')
    plt.close()
