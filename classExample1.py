from __future__ import print_function
from ortools.constraint_solver import pywrapcp

class SchedulingSolver:
    """
    Class for Scheduling problems
    v 0.2 by Marc Farras
    """

    # Creates the solver.
    solver = pywrapcp.Solver("schedule_shifts")

    # Global Variables
    num_nurses = 4
    num_shifts = 4  # Nurse assigned to shift 0 means not working that day.
    num_days = 7

    # Ortools solver Vars
    shifts = {}
    nurses = {}
    shifts_flat =[]
    works_shift = {}
    cost = solver.IntVar(0, 1000, "cost")

    # extra variables, visualize, easy use, etc..
    turnos = ('-', 'M', 'T', 'N')

#    def __init__(self):


    def definedModel(self):
        """
        Define de model, initialice Ortools vars
        :return: void
        """
        # [START]
        # Create shift variables.
        self.shifts = {}

        for j in range(self.num_nurses):
            for i in range(self.num_days):
                self.shifts[(j, i)] = self.solver.IntVar(0, self.num_shifts - 1, "shifts(%i,%i)" % (j, i))
        self.shifts_flat = [self.shifts[(j, i)] for j in range(self.num_nurses) for i in range(self.num_days)]

        # Create nurse variables.
        self.nurses = {}

        for j in range(self.num_shifts):
            for i in range(self.num_days):
                self.nurses[(j, i)] = self.solver.IntVar(0, self.num_nurses - 1, "shift%d day%d" % (j, i))

        # Set relationships between shifts and nurses.
        for day in range(self.num_days):
            nurses_for_day = [self.nurses[(j, day)] for j in range(self.num_shifts)]
            for j in range(self.num_nurses):
                s = self.shifts[(j, day)]
                self.solver.Add(s.IndexOf(nurses_for_day) == j)


    def hardConstraints(self):
        """
        Define de Hard constraints for the problem, solver will search the feasible solutions
        only;
        :return: void
        """
        # HARD CONSTRAINTS
        # Make assignments different on each day
        for i in range(self.num_days):
            self.solver.Add(self.solver.AllDifferent([self.shifts[(j, i)] for j in range(self.num_nurses)]))
            self.solver.Add(self.solver.AllDifferent([self.nurses[(j, i)] for j in range(self.num_shifts)]))

        # Each nurse works 5 or 6 days in a week.
        for j in range(self.num_nurses):
            self.solver.Add(self.solver.Sum([self.shifts[(j, i)] > 0 for i in range(self.num_days)]) >= 5)
            self.solver.Add(self.solver.Sum([self.shifts[(j, i)] > 0 for i in range(self.num_days)]) <= 6)

        # Create works_shift variables. works_shift[(i, j)] is True if nurse
        # i works shift j at least once during the week.
        self.works_shift = {}

        for i in range(self.num_nurses):
            for j in range(self.num_shifts):
                self.works_shift[(i, j)] = self.solver.BoolVar('shift%d nurse%d' % (i, j))

        for i in range(self.num_nurses):
            for j in range(self.num_shifts):
                self.solver.Add(self.works_shift[(i, j)] == self.solver.Max([self.shifts[(i, k)] == j
                    for k in range(self.num_days)]))

    def softContraints(self):
        """
        Define Soft Constraints for dthe problem, it points the cost penalization for
        the contraint incompliment, giving a total cost for the problem

        :return: void
        """
        #SOFT CONSTRAINTS
        # Nurse = 1 penalize 30 cost if work on day = 0
        #   shifts[(1, 0)] != 0  (nurse 1 on day 0) !=0 (working, 0 mean working)
        #solver.Add(solver.IsDifferentCstVar(shifts[(1, 0)],0))

        self.objective = self.solver.Add(self.cost== 30* self.solver.IsDifferentCstVar(self.shifts[(3, 6)],0))
        self.solver.Minimize(self.cost, 1)

    def createDecisionBuilderPhase(self):

        # Create the decision builder.
        self.db = self.solver.Phase(self.shifts_flat, self.solver.CHOOSE_FIRST_UNBOUND,
                          self.solver.ASSIGN_MIN_VALUE)

     def displaySolutions(self):
        """
        Display to the console solutions for the problem, using a next solution strategy.

        :return:
        """

        # Looking up solutions
        self.solver.NewSearch(self.db)

        soln = 0

        while self.solver.NextSolution():
            # show solutions on console
            soln = soln + 1
            day_str =""
            print("Solution number ", str(soln), "Cost=", str(self.cost.Value()), '\n')
            for i in range(self.num_days):
                day_str = day_str + "Day" + str(i) + "  "
            print( "          " ,day_str)

            for j in range(self.num_nurses):
                shift_str = "Nurse %s      " %j
                for i in range(self.num_days):
                    shift_str = shift_str +  str(self.turnos[self.shifts[(j, i)].Value()]) + "     "
                print( shift_str)
            r = input ("Desea que busque otra soluvcion? (Y/n)")
            if r.capitalize()=='N':
                break

        if not(self.solver.NextSolution()):
            print("No se han encontrado soluciones!")
        self.solver.EndSearch()


def main():

    mysched = SchedulingSolver()

    mysched.definedModel()
    mysched.hardConstraints()
    mysched.softContraints()
    mysched.createDecisionBuilderPhase()
    mysched.displaySolutions()


"""
    # Create the decision builder.
    db = solver.Phase(shifts_flat, solver.CHOOSE_FIRST_UNBOUND,
                    solver.ASSIGN_MIN_VALUE)
    # Create a solution collector.
    collector = solver.FirstSolutionCollector(db)
    # Add the decision variables.
    solution = solver.Assignment()
    solution.Add(shifts_flat)
    # Add the objective.
    collector.AddObjective(objective)
    solver.Solve(db, [objective, collector] )
    print("Solutions found:", collector.SolutionCount())
    print("Time:", solver.WallTime(), "ms")
    print()
    """
if __name__ == "__main__":
    main()