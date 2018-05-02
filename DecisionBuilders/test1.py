# Copyright 2010-2017 Google
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Unit tests for python/constraint_solver.swig. Not exhaustive."""
from __future__ import print_function

import sys


from ortools.constraint_solver import model_pb2
from ortools.constraint_solver import pywrapcp



class SolverTest(pywrapcp.Solver):



  def NextSolution(self):
      print ("Next Solution")


class SearchMonitorTest(pywrapcp.SearchMonitor):

  def __init__(self, solver, var1, var2, var3):
      pywrapcp.SearchMonitor.__init__(self, solver)
      self._var1 = var1
      self._var2 = var2
      self._var3 = var3
      print ("cost = " + str(self._var3))
      #self._solver = solver

  def BeginInitialPropagation(self):
      print("Begin initial propagation " + str(self._var1))

  def EndInitialPropagation(self):
      print("End initial propagation " + str(self._var1))

  def ExitSearch(self):
      print ("Exiting search! %s %s" %(str(self._var1), str(self._var2 )))

  def EnterSearch(self):
      print ("Entering search! %s %s" % (str(self._var1), str(self._var2 )))

  def BeginNextDecision(self, b):
      print ("Begin next decision: " + str(b))


def test_search_monitor():
    print( '-->test_search_monitor')
    solver = pywrapcp.Solver('test search_monitor')

    #---Variables
    x = solver.IntVar(1, 10, 'x')
    y = solver.IntVar(1,20, 'y')
    cost = solver.IntVar(0,100, 'cost')
    a = solver.IntVar(0,1, 'a')  # is a softconstraint assigned


    #---Constraints
    ct = (y == 2*x)
    ct2 = (cost == a*20+y)
    ct3 = ( cost<99 )

    solver.Add(ct)
    solver.Add(a == (x <= 3))
    solver.Add(ct2)
    solver.Add(ct3)

    #---Motor solver
    search_phase = solver.Phase([cost], solver.CHOOSE_FIRST_UNBOUND, solver.ASSIGN_MIN_VALUE)
    cost_phase = solver.Phase([cost], solver.CHOOSE_FIRST_UNBOUND, solver.ASSIGN_MIN_VALUE)

    #final_phase = solver.Compose([search_phase,cost_phase])

    monitor = SearchMonitorTest(solver, x, y, cost)
    #objetivo = solver.Minimize(cost, 1)
    #solver.Solve(search_phase, [objetivo, monitor])
    solver.Solve(search_phase, [monitor])
    solver.NewSearch(search_phase)
    print(' 2 * x == y')

    while solver.NextSolution():
        print( ' 2 * %i == %i ' % (x.Value(), y.Value()), end='')
        print( 'cost = %i, a = %i' % (cost.Value(),a.Value()))
        i = "n"
        #i = input("Salir? (y/N)")
        if i.upper() == "Y":
            break
        #else:
        #    solver.AssignVariableValue(b,10)
    solver.EndSearch()


def main():

  test_search_monitor()

if __name__ == '__main__':
  main()