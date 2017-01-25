#!/usr/bin/env python

import argparse
import math
import sys

class Thruster(object):
    def __init__(self, name, mass, thrust, price, ion=False):
        self.name = name
        self.mass = mass
        self.thrust = thrust
        self.price = price
        self.ion = ion

    def getName(self):
        return self.name

    def getThrust(self, duration=0):
        return self.thrust

    def getMass(self):
        return self.mass

    def getPrice(self):
        return self.price

    def isIon(self):
        return self.ion

class Juno(Thruster):
    def __init__(self):
        super().__init__("Juno", 1, 4, 1)

class Atlas(Thruster):
    def __init__(self):
        super().__init__("Atlas", 4, 27, 5)

class Proton(Thruster):
    def __init__(self):
        super().__init__("Proton", 6, 70, 12)

class Soyuz(Thruster):
    def __init__(self):
        super().__init__("Soyuz", 9, 80, 8)

class Saturn(Thruster):
    def __init__(self):
        super().__init__("Saturn", 20, 200, 15)

class IonThruster(Thruster):
    def __init__(self):
        super().__init__("Ion Thruster", 1, 5, 10, True)

    def getThrust(self, duration=0):
        return self.thrust * duration

THRUSTERS = [Juno(), Atlas(), Proton(), Soyuz(), Saturn(), IonThruster()]

class Stage(object):
    def __init__(self, difficulty, payload, upperStage=None, duration=0, thrusters=[]):
        self.difficulty = difficulty
        self.payload = payload
        self.upperStage = upperStage
        self.duration = duration
        self.thrusters = thrusters

    def addThrusters(self, thrusters):
        self.thrusters += thrusters

    def getMass(self):
        mass = self.payload + self.getThrustersMass()
        if self.upperStage:
            mass += self.upperStage.getMass()
        return mass

    def getThrustersMass(self):
        result = 0
        for thruster in self.thrusters:
            result += thruster.getMass()
        return result

    def getCost(self):
        cost = 0
        for thruster in self.thrusters:
            cost += thruster.getPrice()
        return cost

    def getTotalCost(self):
        if self.upperStage:
            return self.getCost() + self.upperStage.getTotalCost()
        else:
            return self.getCost()

    def getIonThrust(self, duration):
        thrust = 0
        for thruster in self.thrusters:
            if thruster.isIon():
                thrust += thruster.getThrust(duration)
        if self.upperStage:
            thrust += self.upperStage.getIonThrust(duration)
        return thrust

    def getIonThrusterCount(self):
        count = 0
        for thruster in self.thrusters:
            if thruster.isIon():
                count += 1
        if self.upperStage:
            count += self.upperStage.getIonThrusterCount()
        return count

    def getThrust(self):
        thrust = 0
        for thruster in self.thrusters:
            if not thruster.isIon():
                thrust += thruster.getThrust(self.duration)
        if self.duration > 0:
            thrust += self.getIonThrust(self.duration)
        return thrust

    def getUnusedPayload(self):
        return (self.getThrust() - self.getMass()*self.difficulty) / self.difficulty if self.difficulty != 0 else self.difficulty

    def thrustersToString(self):
        thrusters = {}
        for thruster in self.thrusters:
            if thruster in thrusters:
                thrusters[thruster] += 1
            else:
                thrusters[thruster] = 1
        result=""
        for thruster in thrusters.keys():
            result += "{} {} ".format(thrusters[thruster], thruster.getName())

        if self.duration > 0 and self.upperStage:
            ionsCount = self.upperStage.getIonThrusterCount()
            if ionsCount > 0:
                result += "(+ {} Ion Thruster) ".format(ionsCount)
        
        return result

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        payload = self.payload
        if self.upperStage:
            payload += self.upperStage.getMass()
        return "Difficulty:{:2} Payload:{:2} Total mass:{:2} Cost:{} {}{}".format(self.difficulty, payload, self.getMass(), self.getCost(), self.thrustersToString(), ("duration:{}Y".format(self.duration) if self.duration else ""))

def selectRockets(difficulty, payload, upperStage=None, cheapest=True, duration=0, max_mass=1000000):
    results = []
    ionThrust = 0
    totalPayload = payload
    if upperStage:
        ionThrust = upperStage.getIonThrust(duration)
        totalPayload += upperStage.getMass()
        totalPayload -= ionThrust / difficulty
        if totalPayload <= 0:
            return Stage(difficulty, payload, upperStage, duration)

    for thruster in THRUSTERS:
        thrust = thruster.getThrust(duration)
        mass = thruster.getMass()
        thrust_left = thrust - difficulty * mass
        if thrust_left <= 0 or mass > max_mass:
            continue
        thruster_count = math.ceil(totalPayload * difficulty / thrust_left)
        stage = Stage(difficulty, payload, upperStage, duration, [thruster,]*thruster_count)
        if thruster_count > 1 and stage.getUnusedPayload() >= 1: # try to replace last rocket with something lighter/cheaper
            stage1 = Stage(difficulty, payload, upperStage, duration, [thruster,] * (thruster_count-1))
            stage2_payload = - (stage1.getUnusedPayload())
            stage2 = selectRockets(difficulty, stage2_payload, None, cheapest, duration, mass)
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

def planRoute(payload, difficulties, durations, cheapest=True):
    total_cost = 0
    stage = None
    for i in range(len(difficulties)-1, -1, -1):
        difficulty = difficulties[i]
        if durations and len(durations) > i:
            duration = durations[i]
        else:
            duration = 0
        stage=selectRockets(difficulty, payload, stage, cheapest, duration)
        payload = 0
        print(stage)
    print("Total mission cost:", stage.getTotalCost())

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('payload', type=int, help='Payload mass')
    parser.add_argument('difficulty', type=int, nargs="+", help='Maneuver difficulty')
    parser.add_argument('--duration', type=int, nargs="+", help='Maneuver duration')
    parser.add_argument('--light', dest="cheapest", default=True, action="store_false", help='Optimize mass')
    args = parser.parse_args()
    planRoute(args.payload, args.difficulty, args.duration, cheapest=args.cheapest)
