from __future__ import print_function
from ortools.constraint_solver import pywrapcp
from math import pow

class SchedulingSolver:
    """
    Class for Scheduling problems
    v 1.1 by Marc Farras
    """

    #TODO:  Cost to assign a task for a worker (soft)

    # Creates the solver.
    solver = pywrapcp.Solver("schedule_shifts_tasks")

    # Global Variables
    num_workers = 0
    num_days = 0
    nameShifts = []
    num_shifts = 0
    nameTasks = []
    num_tasks = 0
    nameWorkers = []
    allWorkers = []
    dayRequirements = []
    NShifts = []

    # Global internal
    nconstraints = 0  #used to count the number of Soft constraints add to the system

    _maxsoftconstraints = 1000  # max number of soft constraints reserved space (can be updated)
    _implementedsoftconstraints = 10 # number of implemented SOFT constraints on this solver version class
    _time_limit = 5000 # time limit for the solver in ms




    def __init__(self):

        # Ortools solver Vars

        self.db = None
        self.objective = None
        self.shifts = {}
        self.workers = {}
        self.tasks = {}
        self.shifts_flat = []
        self.works_shift = {}
        self.cost = self.solver.IntVar(0, 1000, "cost")

        self.brkconstraints = {}
        self.brkconstraints_cost = []
        self.brkconstraints_where = {}

        self.p = None
        self.n = None

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


    def space(self, n):
        """
        Returns a string of n spaces inside

        :param n:
        :return: string
        """
        s = ""
        for i in range(n):
            s = str(s) + " "
        return str(s)


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

        return self.solver.IsEqualCstVar((varexp1 * varexp2), 1)


    def loadData(self):
        """
        Load the data to the solver

        :return:
        """
        #Load the shifts
        self.nameShifts = ['-', 'M', 'T', 'N']  #shift 0 must be as non working shift
        self.num_shifts = len(self.nameShifts)  # worker assigned to shift 0 means not working that day.

        #Load the tasks
        self.nameTasks = ['-','Operario','Supervisor', 'Revisor']
        self.num_tasks = len(self.nameTasks)

        #Load all the workers
        self.allWorkers =[{'Name': 'Ope1', 'ATasks': [0, 1], 'AShifts': [0, 1, 2]},
                          {'Name': 'Ope2', 'ATasks': [0, 1], 'AShifts': [0, 1, 2]},
                          {'Name': 'Ope3', 'ATasks': [0, 1, 3], 'AShifts': [0, 1, 2, 3]},
                          {'Name': 'Ope4', 'ATasks': [0, 3], 'AShifts': [0, 2, 3]},
                          {'Name': 'Sup1', 'ATasks': [0, 2, 3], 'AShifts': [0, 1, 2, 3]},
                          {'Name': 'Sup2', 'ATasks': [0, 1, 2], 'AShifts': [0, 1, 2, 3]},
                          {'Name': 'Sup3', 'ATasks': [0, 2], 'AShifts': [0, 3]}]

        #Set the workers for the problem
        self.nameWorkers = self.allWorkers[:6]
        self.num_workers = len(self.nameWorkers)

        #Set the requirements for the tasks
        #   For a specify day and shift,
        #--------------------------------------------------
        #   {'Operario': [2, 1, 0], 'Supervisor': [1, 1, 0], 'Revisor': [0, 0, 0]} = {[2, 1, 0],[1, 1, 0], [0, 0, 0]}
        #   Day0 = 'Operario': [2, 1, 0]  -> Sets 2 workers for task 'Operario' on shift 1, 1 worker on shift 2 and none on the 3rd shift
        #
        #   ([2OM,1OT,0ON],[1SM,1ST,0SN],[0RM,0RT,0RN]) = DAY 0-5
        #     .
        #     .
        #   ([2OM,2OT,1ON],[1SM,1ST,0SN],[0RM,ORT,1RN]) = DAY 6-7
        #

        self.dayRequirements = [([2, 1, 0], [1, 1, 0], [0, 0, 0]),
                                ([2, 1, 0], [1, 1, 0], [0, 0, 0]),
                                ([2, 1, 0], [1, 1, 0], [0, 0, 0]),
                                ([2, 1, 0], [1, 1, 0], [0, 0, 0]),
                                ([2, 1, 0], [1, 1, 0], [0, 0, 0]),
                                ([2, 2, 1], [1, 1, 0], [0, 0, 1]),
                                ([2, 2, 1], [1, 1, 0], [0, 0, 1])]

        self.num_days = len(self.dayRequirements)
        self.num_days = 2

        #Generating the totallizers
        # NTurnos = {ShiftTipe, day} The number of shiftTipe for each day

        #for i in range(self.num_days):
        #    for j in range(self.num_shifts)
        #        self.NShifts.append()
        #        self.NShifts[j, i]


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

        # tasks[(worker, day)]
        self.tasks = {}

        for j in range(self.num_workers):
            for i in range(self.num_days):
                self.tasks[(j, i)] = self.solver.IntVar(0, self.num_tasks - 1, "tasks(%i,%i)" % (j, i))
        self.tasks_flat = [self.tasks[(j, i)] for j in range(self.num_workers) for i in range(self.num_days)]
        """
        # Set relationships between shifts and workers.
        for day in range(self.num_days):
            workers_for_day = [self.workers[(j, day)] for j in range(self.num_shifts)]
            for j in range(self.num_workers):
                s = self.shifts[(j, day)]
                self.solver.Add(s.IndexOf(workers_for_day) == j)
        """
        # Initialize list of broken constraints
        for i in range(self._maxsoftconstraints):
            self.brkconstraints[i] = self.solver.IntVar(0,1000,"brk %i" % i)
            self.brkconstraints_where[i] = self.solver.IntVar(0, 10000000, "brkw %i" %i)
            self.brkconstraints_cost.append(0)

    def hardConstraints(self):
        """
        Define de Hard constraints for the problem, solver will search the feasible solutions
        only;
        :return: void
        """
        # HARD CONSTRAINTS


        #TODO: Why the assignation to 4 OM and 2 SM does not work with 6 workers and unique hard constraint?
        # self.addHardWorkersMustBeAssignedToAllowedTasks()

        # Set all the allowed tasks for all the workers as hard constraints
        for w in range(self.num_workers):
            self.addHardAllowedTasksForWorker(w, self.nameWorkers[w]['ATasks'])

        # Set the scheduling min requirements
        self.addHardMinRequired_TaskForShift_onDay(2, 1, 1 ,0)

        # Set the scheduling number of working days from the requirement
        # Each worker works 5 or 6 days in a week.

        #self.addHardMaxWorkingDays(5, 6)


    def addHardMinRequired_TaskForShift_onDay(self, nworkers, rtask, rshift, iday):
        """
        Set the Minumum required workers to do the task in the specified shift for a day
            * Shifts are not hard constraints so it will be assignet to a worker for a penalty cost

        :param rworkers: Required number of workers to assign
        :param rtasks: Required task array for a day
        :param rshifts: Required shifts for the tasks
        :param iday: The index for the assignment day
        :return: void
        """

        #print ("debug.Assigning %i workers to day %i doint task %s for shift %s" %(nworkers, iday,
        #        self.nameTasks[rtask], self.nameShifts[rshift]))

        exp = [(self.tasks[(w, iday)] == rtask) * (self.shifts[(w, iday)] == rshift) for w in range(self.num_workers)]
        self.solver.Add(self.solver.Sum(exp) >= nworkers)

    def addHardAllowedTasksForWorker(self, iworker, atasks):
        """
        Set the allowed tasks for a especific worker
        :param iworker:  The worker index
        :param atasks: The tasks array to set
        :return: void
        """

        #print ("debug.Setting allowed tasks for worker %s are %s" %(self.nameWorkers[iworker]['Name'], str(atasks)))

        for i in range(self.num_days):
            exp = [self.tasks[iworker, i] == atasks[t] for t in range(len(atasks))]
            self.solver.Add(self.solver.Max(exp) == 1)


    def addHardWorkersMustBeAssignedToAllowedTasks(self):
        """
        Set the assignments of the workers at those who has allowed taks

        :return:
        """
        #Example:
        #At least 2 M shifts must be set on day 0
        #exp1 = [self.shifts[(w, 0)] == 1 for w in range(self.num_workers)]
        #self.solver.Add(self.solver.Sum(exp1) >= 3)
        #numero de supervisores assignados =1 en turno manana
        #exp2 = [self.tasks[(w, 0)] == 1 for w in range(self.num_workers)]
        #self.solver.Add(self.solver.Sum(exp2) == 1)

        exp1 = [(self.tasks[(w, 0)] == 1) * (self.shifts[(w, 0)] == 1) for w in range(self.num_workers)]
        exp2 = [(self.tasks[(w, 0)] == 2) * (self.shifts[(w, 0)] == 1) for w in range(self.num_workers)]
        #print (exp3)
        self.solver.Add(self.solver.Sum(exp1) >= 4)
        self.solver.Add(self.solver.Sum(exp2) >= 2)


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
        #SOFT CONSTRAINTS EXAMPLE
        # worker = 1 penalize 30 cost if work on day = 0
        #   shifts[(1, 0)] != 0  (worker 1 on day 0) !=0 (working, 0 mean working)
        #solver.Add(solver.IsDifferentCstVar(shifts[(1, 0)],0))


        #---Define the Soft constraints to use on the problem-----
        #self.addSoft_ShiftForworkerOnDay_NotEqualTo(2, 2, 2, 30)
        #self.addSoft_ShiftForworkerOnDay_NotEqualTo(3, 6, 0, 30)
        #self.addSoft_ShiftForworkerOnADay_EqualTo(1, 1, 0, 90)
        #self.addSoft_AfterAShiftForworkerNextShift_NotEqualTo(1, 1, 0, 80)

        #Load soft constraints for the allowed Shifts of the workers
        """
        for w in range(self.num_workers):
            print ("debug.Setting Allowed shift for %s are %s" %(self.nameWorkers[w]['Name'],self.nameWorkers[w]['AShifts']))
            self.addSoft_AllowedShiftsToWorker(w, self.nameWorkers[w]['AShifts'], 40 )
        """
        #------
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


    def addSoft_AllowedShiftsToWorker(self, iworker, ashift, penalty):
        """
        Set for a set of alloweds shifts

        :param iworker: index for the worker
        :param ashift: a list of allowed shifts indexes
        :param penalty: the cost for to broke this constraint
        :return: void
        """
        thisSoftConstraint = 2  # internal index code constraint on the solver, must be > 0
        num_ashifts = len(ashift)

        for i in range(self.num_days):
            temp = [self.shifts[iworker, i] == ashift[s] for s in range(num_ashifts)]
            #print ("Debug.Day %i Debug.temp=%s " % (i,temp))
            self.solver.Add(self.brkconstraints[self.nconstraints] == 1 * (self.solver.Max(temp) == 0))
            self.solver.Add(self.brkconstraints_where[self.nconstraints] == self.brkconstraints[self.nconstraints] *
                        self._brkWhereSet(iworker, i, thisSoftConstraint))
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

        thisSoftConstraint = 3  # internal index code constraint on the solver, must be > 0

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
        thisSoftConstraint = 4  # internal index code constraint on the solver, must be > 0

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
        vars = self.shifts_flat + self.tasks_flat
        self.db = self.solver.Phase(vars, self.solver.ASSIGN_MIN_VALUE, self.solver.CHOOSE_FIRST_UNBOUND)

        #TODO : Create composed db for both assignment problems shefts and tasks


    def searchSolutionsCollector(self, dsol):
        """
        Search solutions using collector

        :return: dsol: solution number to display
        """

        # Create a solution collector.

        collector = self.solver.LastSolutionCollector()
        collector.Add(self.shifts_flat)
        collector.Add(self.tasks_flat)
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
            shift_str = self.nameWorkers[j]['Name'] + self.space(9)
            for i in range(self.num_days):
                if collector is None:
                    shift_str = shift_str + str(self.nameShifts[self.shifts[(j, i)].Value()]) + "     "
                else:
                    shift_str = shift_str + str(self.nameTasks[collector.Value(dsoln, self.tasks[(j, i)])])[0]  + \
                                str(self.nameShifts[collector.Value(dsoln, self.shifts[(j, i)])]) + "    "

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
                print ("#%i breaked %s with cost %i" % (n+1, self._brkWhereGet(where),
                        self.brkconstraints_cost[n]) )
        if self.nconstraints == 0:
            perc=0
        else:
            perc = 100*cons_count/self.nconstraints
        print("Breaked soft constraints: %i of %i inserted constraints (%.1f%%)\n" %
              (cons_count, self.nconstraints, perc))

        if collector is None:
            r = input("Desea que busque otra solucion? (Y/n)")
            if r.capitalize() == 'N':
                return(0)


def main():

    mysched = SchedulingSolver()

    mysched.loadData()
    mysched.definedModel()
    mysched.hardConstraints()
    mysched.softConstraints()
    mysched.createDecisionBuilderPhase()
    mysched.searchSolutionsCollector(0)

    exit(0)

if __name__ == "__main__":
    main()