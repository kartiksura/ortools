# Solve people calendars conflicts.
  sequence_phase = solver.Phase(all_calendars, solver.SEQUENCE_DEFAULT)
  # Schedule meeting at the earliest possible time.
  meeting_phase = solver.Phase([meeting], solver.INTERVAL_DEFAULT)
  # And compose.
  main_phase = solver.Compose([sequence_phase, vars_phase, meeting_phase])

  solution = solver.Assignment()
  solution.Add(meeting_location)
  solution.Add(people_count)
  solution.Add([all_people_presence[p] for p in all_people])
  solution.Add(meeting)

  collector = solver.LastSolutionCollector(solution)

  search_log = solver.SearchLog(100, people_count)

  solver.Solve(main_phase, [collector, search_log, objective])
