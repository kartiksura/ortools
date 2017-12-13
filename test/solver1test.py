from __future__ import print_function
from ortools.constraint_solver import pywrapcp

class SchedulingSolver:
    """
    Class for Scheduling problems
    v 0.3 by Marc Farras
    """

    # Creates the solver.
    solver = pywrapcp.Solver("schedule_shifts")

    # Global Variables
    num_nurses = 4
    num_shifts = 4  # Nurse assigned to shift 0 means not working that day.
    num_days = 7
    nconstraints = 1  #used only to display the number of Soft constraints to count

    # extra variables, visualize, easy use, etc..
    turnos = ('-', 'M', 'T', 'N')

    def __init__(self):

        # Ortools solver Vars

        self.db = None
        self.objective = None
        self.shifts = {}
        self.nurses = {}
        self.shifts_flat = []
        self.works_shift = {}
        self.cost = self.solver.IntVar(0, 1000, "cost")
        # self.cost2 = self.solver.IntVar(0, 1000, "cost2")
        # self.totalcost = self.solver.IntVar(0, 1000, "totalcost")
        self.brkconstraints = {}
        self.brkcons_flat = []
        self.brkconstraintscost = [30, 40, 50, 60]

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

        # Initialize list of broken constraints
        for i in range(self.nconstraints):
            self.brkconstraints[i] = self.solver.IntVar(0,1,"brk %i" % i)

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

        #IsDifferentCstCar(intExp*, int) = intVar*
        #self.solver.Add(self.cost== 30* self.solver.IsDifferentCstVar(self.shifts[(3, 6)],0))
        self.solver.Add(self.brkconstraints[0] == 1 * self.solver.IsDifferentCstVar(self.shifts[(3, 6)],0))

        self.solver.Add(self.cost == self.brkconstraintscost[0] * self.brkconstraints[0])


    """
    def AddSoftConstraint( self):
        
        Adds a contraint to the solver, but in soft mode with a penalization value of cost

        :param constraint: Contraint to insert
        :param cost: Penalization value if constraint is found
        :return: void
        

    """
    def createDecisionBuilderPhase(self):

        # Create the decision builder.
        self.db = self.solver.Phase(self.shifts_flat, self.solver.ASSIGN_MIN_VALUE, self.solver.CHOOSE_FIRST_UNBOUND)


    def searchSolutionsCollector(self, dsol):
        """
        Search solutions using collector

        :return: dsol: solution number to display
        """

        # Create a solution collector.

        collector = self.solver.LastSolutionCollector()
        collector.Add(self.shifts_flat)

        # Add the objective and solve

        self.objective = self.solver.Maximize(self.cost, 1)
        collector.AddObjective(self.cost)

        #solution_limit = self.solver.SolutionsLimit(1000)

        self.solver.Solve(self.db, [self.objective, collector] )

        print("Solutions found:", collector.SolutionCount())
        print("Time:", self.solver.WallTime(), "ms")
        print()
        best_solution = collector.SolutionCount() - 1

        self.showSolutionToScreen(dsol, collector.ObjectiveValue(best_solution), self.shifts, collector)

    def searchSolutions(self):
        """
        Search a solution using a next solution strategy.

        :return:
        """

        # Looking up solutions
        self.solver.NewSearch(self.db)

        soln = 0

        while self.solver.NextSolution():
            # show solutions on console
            soln = soln + 1
            r= self.showSolutionToScreen(soln, self.cost.Value(), self.shifts)
            if (r == 0):
                break
        if not(self.solver.NextSolution()):
            print("No se han encontrado soluciones!")
        self.solver.EndSearch()

    def showSolutionToScreen(self, dsoln, dcost, dshifts, collector=None):
        """
        Show a solution scheduler to the screen

        :param
            dsoln: number of the solution to display
            dcost: cost of the solution found
        :return: exit code  0: stop search manually
                            1: no solutions found
        """
        day_str = ""
        print("Solution number ", str(dsoln), "Cost=", str(dcost), '\n')
        for i in range(self.num_days):
            day_str = day_str + "Day" + str(i) + "  "
        print("          ", day_str)

        for j in range(self.num_nurses):
            shift_str = "Nurse %s      " % j
            for i in range(self.num_days):
                if collector is None:
                    shift_str = shift_str + str(self.turnos[dshifts[(j, i)].Value()]) + "     "
                else:
                    shift_str = shift_str + str(self.turnos[collector.Value(dsoln, dshifts[(j, i)])]) + "     "

            print(shift_str)
        print ("Breaked constraints: ")

        #print ("Cons0=", str(self.brkconstraints[0].Value()))

        if collector is None:
            r = input("Desea que busque otra solucion? (Y/n)")
            if r.capitalize() == 'N':
                return(0)


def main():

    mysched = SchedulingSolver()

    mysched.definedModel()
    mysched.hardConstraints()
    mysched.softContraints()
    mysched.createDecisionBuilderPhase()
    #mysched.searchSolutions()
    mysched.searchSolutionsCollector(0)

    exit(0)

if __name__ == "__main__":
    main()