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

  def __init__(self, solver, var1, var2):
    pywrapcp.SearchMonitor.__init__(self, solver)
    self._var1 = var1
    self._var2 = var2
    print ("y = " + str(self._var2))
    #self._solver = solver

  def BeginInitialPropagation(self):
    print( self._var1)

  def EndInitialPropagation(self):
    print("End propagation " + str(self._var1))

  def ExitSearch(self):
    print ("Exiting search! %s %s" %(str(self._var1), str(self._var2 )))

  def EnterSearch(self):
    print ("Entering Search")

  def BeginNextDecision(self, b):
    print ("Begin next decision: " + str(b))


def test_search_monitor():
  print( '-->test_search_monitor')
  solver = pywrapcp.Solver('test search_monitor')
  x = {}
  w = solver.IntVar(1, 5, 'w')
  d = solver.IntVar(1, 5, 'd')

  for a in range(5):
    for b in range(5):
      x[(a,b)] = solver.IntVar(1, 10, 'x[%i%i]' %(a,b))

  variables = [x[(a,b)] for a in range(5) for b in range(5)]

  y = solver.IntVar(1,50, 'y')
  ct = (y == 2 * x[(1, 2)])
  #ct2 = (x !=1)
  solver.Add(ct)
  #solver.Add(ct2)
  db = solver.Phase(variables, solver.CHOOSE_FIRST_UNBOUND, solver.ASSIGN_MIN_VALUE)
  monitor = SearchMonitorTest(solver, x, y)
  objetivo = solver.Maximize(y, 1)
  solver.Solve(db, [objetivo, monitor])

  solver.NewSearch(db)
  print(' 2 * x == y')
  while solver.NextSolution():
    for a in range(5):
      for b in range(5):
        print( ' 2 * x[%i,%i](%i)== %i' % (a,b,x[(a,b)].Value(), y.Value()))
    s=""
    s=input("show next (Y/n)")
    if s.upper()=="" or s.upper()=="N":
      break
  solver.EndSearch()


def main():

  test_search_monitor()

if __name__ == '__main__':
  main()