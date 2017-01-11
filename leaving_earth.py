#!/usr/bin/env python

import argparse
import math
import sys

ROCKETS = [("Juno", 1, 4, 1), ("Atlas", 4, 27, 5), ("Proton", 6, 70, 12), ("Soyuz", 9, 80, 8), ("Saturn", 20, 200, 15)]

class Stage(object):
    def __init__(self, difficulty, payload, thrusters=[]):
        self.difficulty = difficulty
        self.payload = payload
        self.thrusters = thrusters

    def addThrusters(self, thrusters):
        self.thrusters += thrusters

    def getMass(self):
        return self.payload + self.getThrustersMass()

    def getThrustersMass(self):
        result = 0
        for thruster in self.thrusters:
            result += thruster[1]
        return result

    def getCost(self):
        cost = 0
        for thruster in self.thrusters:
            cost += thruster[3]
        return cost

    def getThrust(self):
        thrust = 0
        for thruster in self.thrusters:
            thrust += thruster[2]
        return thrust

    def getUnusedPayload(self):
        return (self.getThrust() - self.getMass()*self.difficulty) / self.difficulty if self.difficulty != 0 else self.difficulty

    def thrustersToString(self):
        thrusters = {}
        for thruster in self.thrusters:
            name = thruster[0]
            if name in thrusters:
                thrusters[name] += 1
            else:
                thrusters[name] = 1
        result=""
        for name in thrusters.keys():
            result += "{} {} ".format(thrusters[name], name)
        return result

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "Difficulty:{:2} Payload:{:2} Total mass:{:2} Cost:{} {}".format(self.difficulty, self.payload, self.getMass(), self.getCost(), self.thrustersToString())

def selectRockets(difficulty, payload, cheapest=True, max_mass=1000000):
    results = []
    for rocket in ROCKETS:
        (name, mass, thrust, price) = rocket
        thrust_left = thrust - difficulty * mass
        if thrust_left <= 0 or mass > max_mass:
            continue
        rocket_count = math.ceil(payload * difficulty / thrust_left)
        stage = Stage(difficulty, payload, (rocket,)*rocket_count)
        if rocket_count > 1 and stage.getUnusedPayload() >= 1: # try to replace last rocket with something lighter/cheaper
            stage1 = Stage(difficulty, payload, (rocket,) * (rocket_count-1))
            stage2_payload = - (stage1.getUnusedPayload())
            stage2 = selectRockets(difficulty, stage2_payload, cheapest, mass)
            if stage2.getThrustersMass() < mass:
                stage1.addThrusters(stage2.thrusters)
                stage = stage1
        #print(stage)
        results.append(stage)
    return selectBest(results, cheapest)

def selectBest(stages, cheapest=False):
    best_cost = 1000000
    best_mass = 1000000
    result = None
    if cheapest:
        for stage in stages:
            mass = stage.getMass()
            cost = stage.getCost()
            if cost < best_cost or (cost == best_cost and mass < best_mass):
                best_cost = cost
                best_mass = mass
                result = stage
    else:
        for stage in stages:
            mass = stage.getMass()
            cost = stage.getCost()
            if mass < best_mass or (mass == best_mass and cost < best_cost):
                best_cost = cost
                best_mass = mass
                result = stage
    return result

def planRoute(payload, *difficulties, cheapest=True):
    total_cost = 0
    for difficulty in difficulties[::-1]:
        stage=selectRockets(difficulty, payload, cheapest)
        print(stage)
        payload = stage.getMass()
        total_cost += stage.getCost()
    print("Total mission cost:", total_cost)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('payload', type=int, help='Payload mass')
    parser.add_argument('difficulty', type=int, nargs="+", help='Maneuver difficulty')
    parser.add_argument('--light', dest="cheapest", default=True, action="store_false", help='Optimize mass')
    args = parser.parse_args()
    planRoute(args.payload, *args.difficulty, cheapest=args.cheapest)
