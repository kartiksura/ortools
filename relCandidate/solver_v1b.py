from __future__ import print_function
from ortools.constraint_solver import pywrapcp
from math import pow

class SchedulingSolver:
    """
    Class for Scheduling problems
    v 1.0 by Marc Farras
    """

    # Creates the solver.
    solver = pywrapcp.Solver("schedule_shifts")

    # Global Variables
    num_workers = 4
    num_days = 7
    num_shifts = 4
    nameShifts = ('-', 'M', 'T', 'N')

    # Global internal
    nconstraints = 0  #used to count the number of Soft constraints add to the system
    _maxsoftconstraints = 10  # max number of soft constraints implemented in the solver version class
    _time_limit = 10000 # time limit for the solver in ms




    def __init__(self):

        # Ortools solver Vars

        self.db = None
        self.objective = None
        self.shifts = {}
        self.workers = {}
        self.shifts_flat = []
        self.works_shift = {}
        self.cost = self.solver.IntVar(0, 1000, "cost")

        self.brkconstraints = {}
        self.brkconstraints_cost = []
        self.brkconstraints_where = {}

        self.p = None
        self.n = None
        for i in range(self._maxsoftconstraints):
            self.brkconstraints_cost.append(0)

    def _brkWhereSet(self, worker, day, constraint):
        """
        Returns the code for a given broken constraint
        :param worker:
        :param day:
        :param constraint:
        :return: integer with the code of the worker x day broken
        """
        #code = xxx00000 + worker*days + day  / xxx the soft constraint index broken
        return int(pow(10,5)) * constraint + (worker * self.num_days) + day


    def _brkWhereGet(self, code):
        """

        :param code: integer with the code to get worker and day broken
        :return: String format like "(worker,day)"
        """
        _con = code / int(pow(10,5))
        code = int(str(code)[-5:])
        _fil = code/self.num_days
        _col = (code % self.num_days)
        _str = "SoftConstraint %i in (%i,%i)" % (_con, _fil, _col)
        return str(_str)


    def _ifexp1Andxp2(self, exp1, exp2):
        """
        Eval if (exp1 AND exp2) are true
        Helper to the solving constraints

        :param exp1: String expression to eval (expression must eval to true or false)
        :param exp2: String expression to eval (expression must eval to true or false)
        :return: Bool
        """
        varexp1 = eval(exp1)
        varexp2 = eval(exp2)

        return self.solver.IsEqualCstVar((varexp1 + varexp2), 2)


    def definedModel(self):
        """
        Define de model, initialice Ortools vars
        :return: void
        """
        # [START]
        # Create shift variables.

        # shifts[(workers, day)]
        self.shifts = {}

        for j in range(self.num_workers):
            for i in range(self.num_days):
                self.shifts[(j, i)] = self.solver.IntVar(0, self.num_shifts - 1, "shifts(%i,%i)" % (j, i))
        self.shifts_flat = [self.shifts[(j, i)] for j in range(self.num_workers) for i in range(self.num_days)]

        # Create worker variables.
        # workers[(shift, day)]
        self.workers = {}

        for j in range(self.num_shifts):
            for i in range(self.num_days):
                self.workers[(j, i)] = self.solver.IntVar(0, self.num_workers - 1, "shift%d day%d" % (j, i))

        # Set relationships between shifts and workers.
        for day in range(self.num_days):
            workers_for_day = [self.workers[(j, day)] for j in range(self.num_shifts)]
            for j in range(self.num_workers):
                s = self.shifts[(j, day)]
                self.solver.Add(s.IndexOf(workers_for_day) == j)

        # Create works_shift variables. works_shift[(i, j)] is True if worker
        # i works shift j at least once during the week.
        self.works_shift = {}

        for i in range(self.num_workers):
            for j in range(self.num_shifts):
                self.works_shift[(i, j)] = self.solver.BoolVar('shift%d worker%d' % (i, j))

        for i in range(self.num_workers):
            for j in range(self.num_shifts):
                self.solver.Add(self.works_shift[(i, j)] == self.solver.Max([self.shifts[(i, k)] == j
                                                                             for k in range(self.num_days)]))

        # Initialize list of broken constraints
        for i in range(self._maxsoftconstraints):
            self.brkconstraints[i] = self.solver.IntVar(0,1000,"brk %i" % i)
            self.brkconstraints_where[i] = self.solver.IntVar(0, 10000000, "brkw %i" %i)


    def hardConstraints(self):
        """
        Define de Hard constraints for the problem, solver will search the feasible solutions
        only;
        :return: void
        """
        # HARD CONSTRAINTS
        # Make assignments different on each day
        for i in range(self.num_days):
            self.solver.Add(self.solver.AllDifferent([self.shifts[(j, i)] for j in range(self.num_workers)]))
            self.solver.Add(self.solver.AllDifferent([self.workers[(j, i)] for j in range(self.num_shifts)]))

        # Each worker works 5 or 6 days in a week.
        self.addHardMaxWorkingDays(5, 6)


    def addHardMaxWorkingDays(self, minwdays, maxwdays):
        """
        Set the min and max working days for the problem on a hard constraint (only search for feasible solutions)

        :param minwdays:
        :param maxwdays:
        :return:
        """
        # Each worker works between min and max days in a week.
        #   tip: shift[(j,i)] = 0 is a not working shift
        for j in range(self.num_workers):
            self.solver.Add(self.solver.Sum([self.shifts[(j, i)] > 0 for i in range(self.num_days)]) >= minwdays)
            self.solver.Add(self.solver.Sum([self.shifts[(j, i)] > 0 for i in range(self.num_days)]) <= maxwdays)


    def softConstraints(self):
        """
        Define Soft Constraints for the problem, it points the cost penalization for
        the contraint incompliment, giving a total cost for the problem

        :return: void
        """
        #SOFT CONSTRAINTS
        # worker = 1 penalize 30 cost if work on day = 0
        #   shifts[(1, 0)] != 0  (worker 1 on day 0) !=0 (working, 0 mean working)
        #solver.Add(solver.IsDifferentCstVar(shifts[(1, 0)],0))


        self.addSoft_ShiftForworkerOnDay_NotEqualTo(2, 2, 2, 30)
        self.addSoft_ShiftForworkerOnDay_NotEqualTo(3, 6, 0, 30)
        self.addSoft_ShiftForworkerOnADay_EqualTo(1, 1, 0, 90)
        self.addSoft_AfterAShiftForworkerNextShift_NotEqualTo(1, 1, 0, 80)

        #the last constraint is to calculate the final cost
        self.calculateSoftCost()


    def calculateSoftCost(self):
        """
        Calculate the total cost of the broken constraints

        :return: void
        """
        self.solver.Add(self.solver.Sum((self.brkconstraints[i] * self.brkconstraints_cost[i])
                                            for i in range(self.nconstraints)) == self.cost)


    def addSoft_ShiftForworkerOnDay_NotEqualTo(self, iworker, iday, ine_shift, penalty):
        """
            Add a soft constraint where a Shift for a worker on a single Day can't be equal to ne_shift
        :param iworker: The worker index
        :param iday: The day index number
        :param ine_shift: The index shift
        :param penalty: The penalty cost for this constraint (int)
        :return:
        """
        #IsDifferentCstCar(intExp*, int) = intVar*
        #self.solver.Add(self.cost== 30* self.solver.IsDifferentCstVar(self.shifts[(3, 6)],0))

        thisSoftConstraint = 1  # internal index code constraint on the solver, must be > 0

        self.solver.Add(self.brkconstraints[self.nconstraints] == 1 *
                        self.solver.IsEqualCstVar(self.shifts[(iworker, iday)], ine_shift))

        self.solver.Add(self.brkconstraints_where[self.nconstraints] == self.brkconstraints[self.nconstraints] *
                        self._brkWhereSet(iworker, iday, thisSoftConstraint))

        self.brkconstraints_cost[self.nconstraints] = penalty
        self.nconstraints += 1


    def addSoft_ShiftForworkerOnADay_EqualTo(self, iworker, iday, ie_shift, penalty):
        """
        Assing an specific shift to a worker in a day, e.g assign a not working day (shift==0)
        to a worker in a specific day

        :param iworker: the index number for the worker
        :iday: the day index to assign the shift
        :param ie_shift: the shift index number
        :param penalty: the pensalty cost to broke this constraint
        :return: void
        """

        thisSoftConstraint = 2  # internal index code constraint on the solver, must be > 0

        self.solver.Add(self.brkconstraints[self.nconstraints] == 1 *
                        self.solver.IsDifferentCstVar(self.shifts[iworker, iday], ie_shift))

        self.solver.Add(self.brkconstraints_where[self.nconstraints] == self.brkconstraints[self.nconstraints] *
                        self._brkWhereSet(iworker, iday, thisSoftConstraint))

        self.brkconstraints_cost[self.nconstraints] = penalty
        self.nconstraints += 1


    def addSoft_AfterAShiftForworkerNextShift_NotEqualTo(self, ishift, iworker, ine_shift, penalty):
        """

        :param n: Number of shifts to count
        :param ishift: The index shift to watch
        :param iworker: The worker index
        :param ine_shift: The index Not Equal to shift
        :param penalty: The penalty cost for this constraint (int)
        :return:

        we can use also expressions like :

        self.solver.Add(self.brkconstraints[self.nconstraints] == 1 *
                        self.solver.IsEqualCstVar((self.shifts[(iworker, 0)] == ishift) +
                                                  (self.shifts[(iworker, 1)] == ine_shift), 2))
        """
        thisSoftConstraint = 3  # internal index code constraint on the solver, must be > 0

        for iday in range(self.num_days - 1):
            self.solver.Add(self.brkconstraints[self.nconstraints] == 1 *
                        self.solver.IsEqualCstVar(self.solver.IsEqualCstVar(self.shifts[(iworker, iday)], ishift) +
                                                  self.solver.IsEqualCstVar(self.shifts[(iworker, iday +1)], ine_shift), 2))
            self.solver.Add(self.brkconstraints_where[self.nconstraints] == self.brkconstraints[self.nconstraints] *
                        self._brkWhereSet(iworker, iday, thisSoftConstraint))
            self.brkconstraints_cost[self.nconstraints] = penalty
            self.nconstraints += 1


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
        for c in range(self.nconstraints):
            collector.Add(self.brkconstraints[c])
            collector.Add(self.brkconstraints_where[c])

        # Add the objective and solve

        self.objective = self.solver.Minimize(self.cost, 1)
        collector.AddObjective(self.cost)

        #solution_limit = self.solver.SolutionsLimit(1000)
        self.time_limit = self.solver.TimeLimit(self._time_limit)

        self.solver.Solve(self.db, [self.objective, self.time_limit, collector] )

        found = collector.SolutionCount()
        print("Solutions found:", found)
        print("Time:", self.solver.WallTime(), "ms")
        print()

        if found > 0:
            best_solution = collector.SolutionCount() - 1
            self.showSolutionToScreen(dsol, collector.ObjectiveValue(best_solution), collector)
        else:
            print ("No solutions found on time limit ", (self._time_limit/1000), " sec, try to revise hard constraints.")


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


    def showSolutionToScreen(self, dsoln, dcost,collector=None):
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

        for j in range(self.num_workers):
            shift_str = "worker %s      " % j
            for i in range(self.num_days):
                if collector is None:
                    shift_str = shift_str + str(self.nameShifts[self.shifts[(j, i)].Value()]) + "     "
                else:
                    shift_str = shift_str + str(self.nameShifts[collector.Value(dsoln, self.shifts[(j, i)])]) + "     "

            print(shift_str)

        # show braked constraints (soft)
        print("---------------------------------------------------------------------------")
        cons_count = 0
        for n in range (self.nconstraints):
            if collector is None:
                cons=self.brkconstraints[n].Value()
                where = self.brkconstraints_where[n].Value()
            else:
                cons=collector.Value(dsoln, self.brkconstraints[n])
                where=collector.Value(dsoln, self.brkconstraints_where[n])
                #print (where)

            if cons == 1:
                cons_count = cons_count +1
                print ("#%i breaked %s with cost %i" % (n, self._brkWhereGet(where),
                        self.brkconstraints_cost[n]) )

        print("Breaked soft constraints: %i of %i inserted constraints (%.1f%%)\n" %
              (cons_count, self.nconstraints, 100*cons_count/self.nconstraints))

        if collector is None:
            r = input("Desea que busque otra solucion? (Y/n)")
            if r.capitalize() == 'N':
                return(0)


def main():

    mysched = SchedulingSolver()

    mysched.definedModel()
    mysched.hardConstraints()
    mysched.softConstraints()
    mysched.createDecisionBuilderPhase()
    #mysched.searchSolutions()
    mysched.searchSolutionsCollector(0)

    exit(0)

if __name__ == "__main__":
    main()