from __future__ import print_function
from ortools.constraint_solver import pywrapcp
from enum import Enum

class ChooseTypeDb(Enum):
    CHOOSE_RANDOM = 2
    CHOOSE_FIRST_UNBOUND = 2
    CHOOSE_MIN_SIZE_HIGHEST_MAX = 7
    CHOOSE_MIN_SIZE_HIGHEST_MIN = 5
    CHOOSE_MIN_SIZE_LOWEST_MAX = 6
    CHOOSE_MIN_SIZE_LOWEST_MIN = 4


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
    allowedtasks = []
    allowedshifts= []
    nameWorkers = []
    allWorkers = []
    dayRequirements = []
    NShifts = []

    # Global internal
    nconstraints = 0  #used to count the number of Soft constraints add to the system

    C_MAXWORKERSTASKDAY = 99    # max number of scheduled workers for a single task in a day
    C_MAXSOFTCONSTRAINTS = 200  # max number of soft constraints reserved space (can be updated)
    C_IMPLEMENTEDSOFTCONSTRAINTS = 10 # number of implemented SOFT constraints on this solver version class
    C_TIMELIMIT = 10000 # time limit for the solver in ms


    def __init__(self):

        # Ortools solver Vars

        self.db = None
        self.objective = None
        self.shift = {}
        self.num_workers_task_day= {}
        self.workers_task_day = {}
        self.assigned_worker = {}
        self.tot_workers_day = {}
        self.assigned ={}
        self.task = {}
        self.shifts_flat = []
        self.tasks_flat = []
        self.works_shift = []
        self.workers_flat = []
        self.assignations = []
        self.cost = self.solver.IntVar(0, 5000, "cost")

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
        _str = "SoftConstraint %i with worker %i (%s) in day %i," % (_con, _fil,self.nameWorkers[int(_fil)]['Name'], _col)
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


    def _loadDbChooseTypes(self):
        """
        Load the CHOOSE types for the decision builder

        :return:
        """
        types = []
        types.append(self.solver.CHOOSE_RANDOM)
        types.append(self.solver.CHOOSE_FIRST_UNBOUND)
        types.append(self.solver.CHOOSE_MIN_SIZE_HIGHEST_MAX)
        types.append(self.solver.CHOOSE_MIN_SIZE_HIGHEST_MIN)
        types.append(self.solver.CHOOSE_MIN_SIZE_LOWEST_MAX)
        types.append(self.solver.CHOOSE_MIN_SIZE_LOWEST_MIN)

        return types


    def loadData(self):
        """
        Load the data to the solver

        :return:
        """
        #Load the shifts
        self.nameShifts = ['MAN', 'TAR', 'NOC']
        self.num_shifts = len(self.nameShifts)
        self.allowedshifts = list(range(self.num_shifts))

        #Load the tasks
        self.nameTasks = ['Operario','Supervisor', 'Revisor']
        self.num_tasks = len(self.nameTasks)
        self.allowedtasks = list(range(self.num_tasks))

        #Load all the workers
        self.allWorkers =[{'ID':'001','Name': '---', 'ATasks': [0, 1, 2], 'AShifts': [0, 1, 2]},
                          {'ID':'002','Name': 'Op1', 'ATasks': [0], 'AShifts': [0, 1]},
                          {'ID':'003','Name': 'Op2', 'ATasks': [0], 'AShifts': [0, 1]},
                          {'ID':'004','Name': 'Op3', 'ATasks': [0], 'AShifts': [0, 1, 2]},
                          {'ID':'005','Name': 'Op4', 'ATasks': [0, 2], 'AShifts': [0, 1, 2]},
                          {'ID':'006','Name': 'Op5', 'ATasks': [0], 'AShifts': [0, 1]},
                          {'ID':'007','Name': 'Re1', 'ATasks': [0, 2], 'AShifts': [0, 2]},
                          {'ID':'008','Name': 'Su1', 'ATasks': [1], 'AShifts': [0, 1, 2]},
                          {'ID':'009','Name': 'Su2', 'ATasks': [1], 'AShifts': [0, 1, 2]},
                          {'ID':'010','Name': 'Su3', 'ATasks': [1, 2], 'AShifts': [0, 2]}]

        #Set the workers for the problem
        self.nameWorkers = self.allWorkers
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

        self.allRequirements = [([2, 1, 0], [1, 1, 0], [0, 0, 0]),
                                ([1, 1, 0], [1, 1, 0], [0, 0, 0]),
                                ([2, 1, 0], [1, 1, 0], [0, 0, 0]),
                                ([2, 1, 0], [1, 1, 0], [0, 0, 1]),
                                ([2, 1, 0], [1, 1, 0], [0, 0, 0]),
                                ([3, 1, 1], [1, 1, 0], [0, 0, 1]),
                                ([2, 1, 1], [1, 1, 0], [0, 1, 1])]

        self.dayRequirements = self.allRequirements[0:7]
        self.num_days = len(self.dayRequirements)


    def definedModel(self):
        """
        Define de model, initialice Ortools vars
        :return: void
        """
        # [START]
        # assigned[(worker, task, shift, day)] = 0/1 Assigned or not assigned worker
        self.assigned = {}

        for w in range(self.num_workers):  #worker 0 is reserved for a Non Assigned worker
            for t in range(self.num_tasks):
                for s in range(self.num_shifts):
                    for d in range(self.num_days):
                        self.assigned[(w, t, s, d)] = self.solver.IntVar(0, 1, "assigned(%i,%i,%i,%i)" % (w, t, s, d))

        self.assignations = [self.assigned[(w, t, s, d)] for w in range(self.num_workers)
                                                         for t in range(self.num_tasks)
                                                         for s in range(self.num_shifts)
                                                         for d in range(self.num_days)]

        #--COMPLEMENTARI ---------------------------------------------------------------------------------------------

        # num_workers_task_day[(task, shift, day)] = num workers
        self.num_workers_task_day = {}

        for t in range(self.num_tasks):
            for s in range(self.num_shifts):
                for d in range(self.num_days):
                    self.num_workers_task_day[(t, s, d)] = self.solver.IntVar(0, self.C_MAXWORKERSTASKDAY, "worker(%i,%i,%i)" % (t, s, d))


        # set workers_task_day from assignements
        for d in range(self.num_days):
            for t in range(self.num_tasks):
                for s in range(self.num_shifts):
                    a = self.num_workers_task_day[(t, s, d)]
                    self.solver.Add(self.solver.SumEquality([self.assigned[(w, t, s, d)] == 1 for w in range(1,self.num_workers)], a))

        # tot_workers_day[(day)] = Sum total number of workers assigned for a day
        self.tot_workers_day = {}

        for d in range(self.num_days):
            self.tot_workers_day[d] = self.solver.IntVar(0, self.C_MAXWORKERSTASKDAY, "totalworkersday(%i)" % d)

        for d in range(self.num_days):
            a = self.tot_workers_day[d]
            self.solver.Add(self.solver.SumEquality([self.assigned[(w, t, s, d)] == 1 for w in range(1, self.num_workers)
                                                                                      for t in range(self.num_tasks)
                                                                                      for s in range(self.num_shifts)], a))

        # workers_task_day[(worker, task, shift, day)] = worker
        self.workers_task_day = {}

        for w in range(1,self.num_workers):
            for t in range(self.num_tasks):
                for s in range(self.num_shifts):
                    for d in range(self.num_days):
                        self.workers_task_day[(w, t, s, d)] = self.solver.IntVar(0, self.num_workers -1, "worker(%i,%i,%i,%i)" % (w, t, s, d))

        for w in range(1,self.num_workers):
            for t in range(self.num_tasks):
                for s in range(self.num_shifts):
                    for d in range(self.num_days):
                        a=self.workers_task_day[(w, t, s, d)]
                        self.solver.Add(a == w*self.assigned[(w,t,s,d)])

        self.workers_task_day_flat = [self.workers_task_day[(w, t, s, d)] for w in range(1,self.num_workers)
                                                                     for t in range(self.num_tasks)
                                                                     for s in range(self.num_shifts)
                                                                     for d in range(self.num_days)]

        # isworkingday[(worker,day)] = 1/0  is or is not a working day for this worker
        self.isworkingday = {}

        for w in range(self.num_workers):  #worker 0 is reserved for a Non Assigned worker
            for d in range(self.num_days):
                self.isworkingday[(w, d)] = self.solver.IntVar(0, 1, "isworkingday(%i,%i)" % (w, d))

        for w in range(self.num_workers):
            for d in range(self.num_days):
                a = self.isworkingday[(w, d)]
                self.solver.Add(a == self.solver.Max([self.assigned[(w,t,s,d)] for t in range(self.num_tasks) for s in range(self.num_shifts)]))

        # -----------------------------------------------------------------------------------------------------------
        # Set vars for soft solving
        for i in range(self.C_MAXSOFTCONSTRAINTS):
            self.brkconstraints[i] = self.solver.IntVar(0,1,"brk %i" % i)
            self.brkconstraints_where[i] = self.solver.IntVar(0, 10000000, "brkw %i" %i)
            self.brkconstraints_cost.append(0)

        self.mShowWorkers = []


    def hardConstraints(self):
        """
        Define de Hard constraints for the problem, solver will search the feasible solutions
        only;
        :return: void
        """
        # HARD CONSTRAINTS
        print ("Implementing hard constraints...")
        # All workers for a day must be different for to do the task+shift
        self.addHardAllDifferentWorkers_OnDay()

        # Set all the allowed tasks for all the workers as hard constraints
        for w in range(self.num_workers):
            self.addHardAllowedTasksForWorker(w,self.nameWorkers[w]['ATasks'])

        #self.addHardMinRequired_Task_onDay(2, 0, 2, 0)
        #self.addHardMinRequired_Task_onDay(3, 1, 1, 0)
        #self.addHardMinRequired_Task_onDay(2, 2, 1, 0)
        #self.addHardTotalWorkers_OnDay(7, 0)

        # Load the scheduled requirements for all the days
        for d in range(self.num_days):
            self.addHardAssignDayRequirements(d)


        # Set the scheduling number of working days from the requirement
        # Each worker works 5 or 6 days in a week.

        #self.addHard_MaxConsecutiveWorkingDays(5)

        #self.addHard_MinNonWorkingDays(2, 7)

    def addHardAllDifferentWorkers_OnDay(self):
        """
        Constraint to ensure that a task+shift is assigned to a different worker for a Day

        :return: void
        """
        # All workers for a day must be different except the scape value (0) *None* to do the task on shift
        print ("Setup HARD: All workers for a day must be different.")
        for d in range(self.num_days):
            temp = [self.workers_task_day[(w, t, s, d)] for w in range(1,self.num_workers) for t in range(self.num_tasks) for s in range(self.num_shifts)]
            self.solver.Add(self.solver.AllDifferentExcept(temp,0))


    def addHardAssignDayRequirements(self, iday):
        """
        Load and set the requirements for task/shifts on a day in the contraints motor

        :param iday: The index day to load requirements from and assign constraints
        :return: error number , 0 means no error
        """
        _total = 0
        for t in range(self.num_tasks):
            for s in range(self.num_shifts):
                _nworkers = self.dayRequirements[iday][t][s]
                _total += _nworkers
                self.addHardMinRequired_Task_onDay(_nworkers, t, s, iday )
        # Opcional Total Workers debe coincidir siempre si estan asignados como debe ser
        self.addHardTotalWorkers_OnDay(_total, iday)


    def addHardTotalWorkers_OnDay(self, nworkers, iday):
        """
        Set de Total number of workers (for all the tasks and shifts) on a day

        :param nworkers: Total number of workers to set
        :param iday: Index of the day to set
        :return: void
        """

        if nworkers > (self.num_workers-1):
            print ("More workers are required to assign on day %i,required at least %i." %(iday, nworkers))
            exit(0)

        if nworkers > 0:
            #print("debug.Assigning %i total workers to day %i." % (nworkers, iday ))
            # set the number os tasks to do on this day
            self.solver.Add(self.tot_workers_day[iday] == nworkers)


    def addHardMinRequired_Task_onDay(self, nworkers, rtask, rshift, iday):
        """
        Set the Minumum required workers to do the task in the specified shift for a day
            * Shifts are not hard constraints so it will be assignet to a worker for a penalty cost

        :param rworkers: Required number of workers to assign
        :param rtasks: Required task number for a day
        :param rshift: Required shift number for a day
        :param iday: The index for the assignment day
        :return: void
        """

        print ("debug.Assigning %i workers to day %i at task %s and shift %s" %(nworkers, iday, self.nameTasks[rtask], self.nameShifts[rshift]))

        # set the number os tasks to do on this day
        self.solver.Add(self.num_workers_task_day[(rtask, rshift, iday)] == nworkers)


    def addHardAllowedTasksForWorker(self, iworker, atasks):
        """
        Set the allowed tasks for a especific worker
        :param iworker:  The worker index
        :param atasks: The tasks array to set
        :return: void
        """
        if iworker == 0:
            return

        #print ("debug.Setting allowed tasks for worker %s are %s" %(self.nameWorkers[iworker]['Name'], str(atasks)))
        #Example:
        """
            #not allowed task = [2,3]
            r=[2,3]
            for s in r:
                exp = self.assigned[4,1,s,0] == 0
                print (exp)
                self.solver.Add(exp)
        """
        # create a list with not allowed tasks
        _notallowed = self.allowedtasks.copy()
        for n in atasks:
            _notallowed.remove(n)

        strNotAllowedNames = []
        for i in _notallowed:
            strNotAllowedNames.append(str(self.nameTasks[i]))
        print ("Setup HARD: Worker %i, not allowed to tasks=%s" %(iworker,strNotAllowedNames))

        if len(_notallowed) == 0:
            return 0

        for t in _notallowed:
            for s in range(self.num_shifts):
                for d in range(self.num_days):
                    self.solver.Add(self.assigned[iworker,t,s,d] == 0)


    def addHard_MaxConsecutiveWorkingDays(self, maxwdays):
        """
        Set the max working days for the problem on a hard constraint (only search for feasible solutions)

        :param maxwdays:
        :return:
        """
        # Each worker works max consecutive days
        #for w in range(1, self.num_workers):
        #print (" days=" + str(self.num_days))
        for w in range(1, self.num_workers):
            #print ("debug.Hard: Assigning %i max consecutive working days for worker %i" %(maxwdays,w))
            for dini in range(self.num_days - maxwdays +1):
                if (dini+maxwdays) < self.num_days:
                    r = [self.isworkingday[(w, dini + d)] for d in range(maxwdays+1)]
                    self.solver.Add(self.solver.Sum(r) <= maxwdays)


    def addHard_MinNonWorkingDays(self, minnwdays, lapse_days):
        """
        Set the min non-working days for the scheduler on a Hard constraint (only search for feasible solutions)

        :param minnwdays: min non-working days that have to be assigned consecutively
        :param lapse_days: number of days for the time lapse to compute
        :return:
        """


        if lapse_days < 2:
            print ("Day time lapse too short!, can't add Hard constraint")

        lapse_days= lapse_days -1

        if lapse_days > self.num_days:
            lapse_days = self.num_days

        for w in range(1, 1):
            print("debug.Hard: Assigning %i min non working days for worker %i for every %i days scheduled" %(minnwdays, w, lapse_days+1))
            dini=0
            regla = [self.isworkingday[(w, dini + d)] == 0 for d in range(lapse_days + 1)]
            self.solver.Add(self.solver.Sum(regla) < minnwdays)

            """
            for dini in range(self.num_days - lapse_days + 1):
                if (dini + lapse_days) < self.num_days:
                    print("debug.Hard-> From day %i, to day %i" %(dini, (dini + lapse_days)))
                    temp = [self.isworkingday[(w, dini + d)] == 0 for d in range(lapse_days + 1)]
                    self.solver.Add(self.solver.Sum(temp) < minnwdays)
            """


    def softConstraints(self):
        """
        Define Soft Constraints for the problem, it points the cost penalization for
        the contraint incompliment, giving a total cost for the problem

        :return: void
        """

        print ("Implementing soft constraints...")
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
        for w in range(1, self.num_workers):
            #print ("debug.Soft: Setting the shift for %s to %s" %(self.nameWorkers[w]['Name'],self.nameWorkers[w]['AShifts']))
            self.addSoft_AllowedShiftsToWorker(w, self.nameWorkers[w]['AShifts'], 40 )

        #------
        # Add max consecutive working days constraint
        #self.addSoft_MaxConsecutiveWorkingDays(5, 200)

        # Add min non-working days inside a time lapse
        self.addSoft_MinNonWorkingDays(2, 7, 95)

        #the last constraint is to calculate the final cost  //extern now
        #self.calculateCost()


    def calculateCost(self):
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
                        self.solver.IsEqualCstVar(self.shift[(iworker, iday)], ine_shift))

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

        # create a list with not allowed tasks
        _notallowed = self.allowedshifts.copy()
        for n in ashift:
            _notallowed.remove(n)

        if len(_notallowed) == 0:
            return 0

        for i in range(self.num_days):
            temp = [self.assigned[iworker, t, _notallowed[s], i] == 1 for s in range(len(_notallowed))
                                                                      for t in range(self.num_tasks)]
            #temp = [self.shift[iworker, i] == ashift[s] for s in range(num_ashifts)]
            #print ("Debug.Day %i Debug.temp=%s " % (i,temp))
            self.solver.Add(self.brkconstraints[self.nconstraints] == 1 * (self.solver.Max(temp) == 1))
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
                        self.solver.IsDifferentCstVar(self.shift[iworker, iday], ie_shift))

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
                            self.solver.IsEqualCstVar(self.solver.IsEqualCstVar(self.shift[(iworker, iday)], ishift) +
                                                      self.solver.IsEqualCstVar(self.shift[(iworker, iday + 1)], ine_shift), 2))
            self.solver.Add(self.brkconstraints_where[self.nconstraints] == self.brkconstraints[self.nconstraints] *
                        self._brkWhereSet(iworker, iday, thisSoftConstraint))
            self.brkconstraints_cost[self.nconstraints] = penalty
            self.nconstraints += 1


    def addSoft_MaxConsecutiveWorkingDays(self, maxwdays, penalty):
        """
        Set the max consecutive working days for the problem on a soft constraint (only search for feasible solutions)

        :param maxwdays:
        :return:
        """

        thisSoftConstraint = 5  # internal index code constraint on the solver, must be > 0

        for w in range(1, self.num_workers):
            #print("debug.Soft: Assigning %i max consecutive working days for worker %i" % (maxwdays, w))
            for dini in range(self.num_days - maxwdays + 1):
                if (dini + maxwdays) < self.num_days:
                    temp = [self.isworkingday[(w, dini + d)] for d in range(maxwdays + 1)]

                    self.solver.Add(self.brkconstraints[self.nconstraints] == 1 * (self.solver.Sum(temp) > maxwdays))
                    self.solver.Add(self.brkconstraints_where[self.nconstraints] == self.brkconstraints[self.nconstraints] *
                                    self._brkWhereSet(w, dini, thisSoftConstraint))
                    self.brkconstraints_cost[self.nconstraints] = penalty
                    self.nconstraints += 1


    def addSoft_MinNonWorkingDays(self, minnwdays, lapse_days, penalty):
        """
        Set the min non-working days for the scheduler on a soft constraint (only search for feasible solutions)

        :param minnwdays: min non-working days that have to be assigned consecutively
        :param lapse_days: number of days for the time lapse to compute
        :return:
        """


        thisSoftConstraint = 6  # internal index code constraint on the solver, must be > 0

        if lapse_days < 2:
            print ("Day time lapse too short!, can't add soft constraint")

        lapse_days= lapse_days -1

        if lapse_days > self.num_days:
            lapse_days = self.num_days

        for w in range(1, self.num_workers):
            #print("debug.Soft: Assigning %i min consecutive non working days for worker %i for every %i days scheduled" %(minnwdays, w, lapse_days+1))
            for dini in range(self.num_days - lapse_days + 1):
                if (dini + lapse_days) < self.num_days:
                    temp = [self.isworkingday[(w, dini + d)] == 0 for d in range(lapse_days + 1)]

                    self.solver.Add(self.brkconstraints[self.nconstraints] == 1 * (self.solver.Sum(temp) < minnwdays))
                    self.solver.Add(self.brkconstraints_where[self.nconstraints] == self.brkconstraints[self.nconstraints] *
                                    self._brkWhereSet(w, dini, thisSoftConstraint))
                    self.brkconstraints_cost[self.nconstraints] = penalty
                    self.nconstraints += 1


    def ComposeDb(self):
        """
          first_solution = solver.Assignment()
          first_solution.Add(x)
          first_solution.AddObjective(objective_var)
          store_db = solver.StoreAssignment(first_solution)
          first_solution_db = solver.Compose([assign_db, store_db])
          print('searching for initial solution,', end=' ')
          solver.Solve(first_solution_db)
          print('initial cost =', first_solution.ObjectiveValue())
        """


    def createDecisionBuilderPhase(self, choose_type=solver.CHOOSE_RANDOM):

        # Create the decision builder.
        #vars = self.tasks_flat + self.shifts_flat
        variables = self.assignations
        self.db = self.solver.Phase(variables, self.solver.ASSIGN_MIN_VALUE, choose_type)


        #TODO : Create composed db for both assignment problems shefts and tasks


    def searchSolutionsCollector(self, dsol, toScreen=True):
        """
        Search solutions using collector

        :return: dsol: solution number to display
        """

        # Create a solution collector.
        if toScreen: print ("Searching solutions for max %i seconds..." %(self.C_TIMELIMIT/1000))

        collector = self.solver.LastSolutionCollector()
        collector.Add(self.assignations)
        collector.Add(self.workers_task_day_flat)
        #collector.Add(self.assigned_worker_flat)

        #collector.Add(self.workers_flat)

        for c in range(self.nconstraints):
            collector.Add(self.brkconstraints[c])
            collector.Add(self.brkconstraints_where[c])

        # Add the objective and solve

        self.objective = self.solver.Minimize(self.cost, 1)
        collector.AddObjective(self.cost)

        #solution_limit = self.solver.SolutionsLimit(1000)
        self.time_limit = self.solver.TimeLimit(self.C_TIMELIMIT)

        self.solver.Solve(self.db, [self.objective, self.time_limit, collector] )

        found = collector.SolutionCount()
        if found >0:
            cost = collector.ObjectiveValue(0)
        else:
            cost = -1

        if toScreen==False:
            return cost;

        print("Solutions found:", found)
        print("Time:", self.solver.WallTime(), "ms")
        print()

        if found > 0:
            best_solution = collector.SolutionCount() - 1
            self.showSolutionWorkersToScreen(dsol, collector.ObjectiveValue(best_solution), collector)
            self.showSolutionToScreen(dsol, collector.ObjectiveValue(best_solution), collector)
        else:
            print ("No solutions found on time limit ", (self.C_TIMELIMIT / 1000), " sec, try to revise hard constraints.")

        return cost


    def showSolutionToScreen(self, dsoln, dcost,collector=None):
        """
        Show a solution scheduler to the screen

        :param
            dsoln: number of the solution to display
            dcost: cost of the solution found
        :return: exit code  0: stop search manually
                            1: no solutions found
        """
        day_str = " "
        shf_str = ""
        linea = "_______________"
        barra = ""
        print("Solution number ", str(dsoln), "Cost=", str(dcost), '\n')

        for i in range(self.num_days):
            day_str = day_str + "Day" + str(i) + "    |     "
            for s in range(self.num_shifts):
                shf_str = shf_str + self.nameShifts[s][:3] + " "
            shf_str = shf_str + "| "
            barra += linea
        print("             ", day_str)
        print("          ", shf_str)
        print(barra)

        for j in range(self.num_tasks):
            shift_str = self.nameTasks[j][:7] + self.space(5)
            for d in range(self.num_days):
                for s in range(self.num_shifts):
                    n=0
                    for w in range(1,self.num_workers):
                        a = collector.Value(dsoln, self.assigned[w,j,s,d])
                        if (a>0):
                            #print ("assigned [%i,%i,%i,%i]" %(w,j,s,d))
                            n += 1
                    shift_str = shift_str + str(n)
                    if s < self.num_shifts-1:
                        shift_str += self.space(3)
                    else:
                        shift_str += self.space(2)
                shift_str = shift_str + "|"+ self.space(2)

            print(shift_str)

        # show braked constraints (soft)

        """
        for w in range(self.num_workers):
           for t in range(self.num_tasks):
                for s in range(self.num_shifts):
                    v = collector.Value(dsoln, self.assigned_worker[w,t,s])
                    if v > 0:
                        print ("Debug Task %i, Shift %i, worker = %i on day(%i)" %(t,s,w,v))
        """
        # show braked constraints (soft)
        print("---------------------------------------------------------------------------")
        cons_count = 0
        for n in range (self.nconstraints):
            cons=collector.Value(dsoln, self.brkconstraints[n])
            where=collector.Value(dsoln, self.brkconstraints_where[n])
            #print (where)

            if cons == 1:
                cons_count = cons_count +1
                print ("%i. Breaked %s with cost %i" % (cons_count, self._brkWhereGet(where),
                        self.brkconstraints_cost[n]) )
        if self.nconstraints == 0:
            perc=0
        else:
            perc = 100*cons_count/self.nconstraints
        print("Breaked soft constraints: %i of %i inserted constraints (%.1f%%)\n" %
              (cons_count, self.nconstraints, perc))
        """
        while(True):
            r = input("Do you want to show workers for task on day? (Y/N)")
            if r.capitalize() == 'N' or r=="" :
                return(0)
            else:
                for d in range(self.num_days):
                    for w in range(1,self.num_workers):
                        for t in range(self.num_tasks):
                            for s in range(self.num_shifts):
                                a = collector.Value(dsoln, self.assigned[w, t, s, d])
                                if a > 0:
                                    print("[worker %i (%s), task= %i (%s), shift= %i (%s) ,day %i]" %
                                          (w, self.nameWorkers[w]['Name'], t, self.nameTasks[t], s, self.nameShifts[s], d))
                # ---debug max consecutive days worker for worker
                c = 0
                w = 1
                m = 0
                ld = -1
                for d in range(self.num_days):
                    for t in range(self.num_tasks):
                        for s in range(self.num_shifts):
                            a = collector.Value(dsoln, self.assigned[w, t, s, d])
                            if a > 0 and ld != d:
                                c += 1
                                ld = d
                                if c > m:
                                    m = c
                            if a == 0 and ld != d:
                                c = 0
                print ("Worker %i, has %i consecutive days" %(w,m))

                return (0)
        """


    def showSolutionWorkersToScreen(self, dsoln, dcost,collector=None):
        """

        Show the workers scheduling setup

        :return: void
        """

        day_str = " "
        shf_str = ""
        linea = "________________"
        barra = ""
        print("Solution number ", str(dsoln), "Cost=", str(dcost), '\n')

        for i in range(self.num_days):
            day_str = day_str + "Day" + str(i) + "    |     "
            for s in range(self.num_shifts):
                shf_str = shf_str + self.nameShifts[s][:3] + " "
            shf_str = shf_str + "| "
            barra += linea
        print("             ", day_str)
        print("          ", shf_str)
        print(barra)

        for j in range(self.num_tasks):
            mt = 0
            for d in range(self.num_days):
                for s in range(self.num_shifts):
                    n = 0
                    for w in range(1, self.num_workers):
                        a = collector.Value(dsoln, self.assigned[w, j, s, d])
                        if (a > 0):
                            # print ("assigned [%i,%i,%i,%i]" %(w,j,s,d))
                            n += 1
                            mt = max(mt,n)
            # then now we know the max number of task to create (mt)
            for m in range(1, mt+1):
                shift_str = self.nameTasks[j][:7] + "[" + str(m) + "] "
                for d in range(self.num_days):
                    for s in range(self.num_shifts):
                        strw= self._findWorker(m,d,s,j, dsoln,collector)
                        shift_str += strw+ self.space(1)
                    shift_str += "|" + self.space(1)
                print(shift_str)


    def _findWorker(self, num, d, s, t, dsoln, collector=None):
        """
        Find num (firths, second,.. ) from the day, shift, and task assigned to work

        :param num:
        :param d:
        :param s:
        :param t:
        :param dsoln:
        :param collector:
        :return:
        """
        encontrado = False
        strw = "---"
        n = 0
        for w in range(1, self.num_workers):
            a = collector.Value(dsoln, self.assigned[w, t, s, d])
            if (a > 0):
                encontrado = True
                n += 1
                if n == num:
                    strw = self.nameWorkers[w]['Name']
                    break
        return strw

def main():

    cost =0

    #TODO: Falta procedimiento de Carga de empleados y planificaciones externas

    mysched = SchedulingSolver()
    choose_types = ChooseTypeDb

    mysched.loadData()
    mysched.definedModel()
    mysched.hardConstraints()
    # mysched.softConstraints()
    mysched.calculateCost()
    mysched.createDecisionBuilderPhase(choose_types.CHOOSE_MIN_SIZE_LOWEST_MIN.value)
    cost=mysched.searchSolutionsCollector(0)

    exit(0)

if __name__ == "__main__":
    main()