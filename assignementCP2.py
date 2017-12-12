from __future__ import print_function
from ortools.constraint_solver import pywrapcp

def main():
  # Instantiate a cp solver.
  solver = pywrapcp.Solver("transportation_with_sizes")

  group1 = [[0, 0, 1, 1],  # Workers 2, 3
            [0, 1, 0, 1],  # Workers 1, 3
            [0, 1, 1, 0],  # Workers 1, 2
            [1, 1, 0, 0],  # Workers 0, 1
            [1, 0, 1, 0]]  # Workers 0, 2

  group2 = [[0, 0, 1, 1],  # Workers 6, 7
            [0, 1, 0, 1],  # Workers 5, 7
            [0, 1, 1, 0],  # Workers 5, 6
            [1, 1, 0, 0],  # Workers 4, 5
            [1, 0, 0, 1]]  # Workers 4, 7

  group3 = [[0, 0, 1, 1],  # Workers 10, 11
            [0, 1, 0, 1],  # Workers 9, 11
            [0, 1, 1, 0],  # Workers 9, 10
            [1, 0, 1, 0],  # Workers 8, 10
            [1, 0, 0, 1]]  # Workers 8, 11

  cost = [[90, 76, 75, 70, 50, 74, 12, 68],
          [35, 85, 55, 65, 48, 101, 70, 83],
          [125, 95, 90, 105, 59, 120, 36, 73],
          [45, 110, 95, 115, 104, 83, 37, 71],
          [60, 105, 80, 75, 59, 62, 93, 88],
          [45, 65, 110, 95, 47, 31, 81, 34],
          [38, 51, 107, 41, 69, 99, 115, 48],
          [47, 85, 57, 71, 92, 77, 109, 36],
          [39, 63, 97, 49, 118, 56, 92, 61],
          [47, 101, 71, 60, 88, 109, 52, 90]]


  sizes = [10, 7, 3, 12, 15, 4, 11, 5]
  total_size_max = 15
  num_workers = len(cost)
  num_tasks = len(cost[1])

  # Variables
  total_cost = solver.IntVar(0, 1000, "total_cost")
  x = []
  for i in range(num_workers):
    t = []
    for j in range(num_tasks):
      t.append(solver.IntVar(0, 1, "x[%i,%i]" % (i, j)))
    x.append(t)
  x_array = [x[i][j] for i in range(num_workers) for j in range(num_tasks)]

  # Constraints

  solver.Add(solver.AllowedAssignments([work[0], work[1], work[2], work[3]], group1))
  solver.Add(solver.AllowedAssignments([work[4], work[5], work[6], work[7]], group2))
  solver.Add(solver.AllowedAssignments([work[8], work[9], work[10], work[11]], group3))

  # Each task is assigned to at least one worker.
  [solver.Add(solver.Sum(x[i][j] for i in range(num_workers)) >= 1)
  for j in range(num_tasks)]

  # Total task size for each worker is at most total_size_max

  [solver.Add(solver.Sum(sizes[j] * x[i][j] for j in range(num_tasks)) <= total_size_max)

  for i in range(num_workers)]
  # Total cost
  solver.Add(
      total_cost == solver.Sum(
          [solver.ScalProd(x_row, cost_row) for (x_row, cost_row) in zip(x, cost)]))
  objective = solver.Minimize(total_cost, 1)

  db = solver.Phase(x_array,
                    solver.CHOOSE_FIRST_UNBOUND,
                    solver.ASSIGN_MIN_VALUE)

  # Create a solution collector.
  collector = solver.LastSolutionCollector()
  # Add decision variables
  #collector.Add(x_array)

  for i in range(num_workers):
    collector.Add(x[i])

  # Add objective
  collector.AddObjective(total_cost)
  solver.Solve(db, [objective, collector])

  if collector.SolutionCount() > 0:
    best_solution = collector.SolutionCount() - 1
    print("Total cost = ", collector.ObjectiveValue(best_solution))
    print()

    for i in range(num_workers):

      for j in range(num_tasks):

        if collector.Value(best_solution, x[i][j]) == 1:
          print('Worker ', i, ' assigned to task ', j, '  Cost = ', cost[i][j])

    print()
    print("Time = ", solver.WallTime(), "milliseconds")

if __name__ == '__main__':
  main()