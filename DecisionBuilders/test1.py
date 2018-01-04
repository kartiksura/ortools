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


class SearchMonitorTest(pywrapcp.SearchMonitor):

  def __init__(self, solver, var1, var2):
    pywrapcp.SearchMonitor.__init__(self, solver)
    self._var1 = var1
    self._var2 = var2
    print ("_s = " + str(self._var2))
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
  x = solver.IntVar(1, 10, 'x')
  y = solver.IntVar(1,4, 'y')
  ct = (y == 2*x)
  solver.Add(ct)
  db = solver.Phase([x], solver.CHOOSE_FIRST_UNBOUND, solver.ASSIGN_MIN_VALUE)
  monitor = SearchMonitorTest(solver, x, y)
  solver.Solve(db, monitor)

  solver.NewSearch(db)
  while solver.NextSolution():
    print( ' 2 * %i == %i' % (x.Value(), y.Value()))
  solver.EndSearch()
def main():


  test_search_monitor()



if __name__ == '__main__':
  main()