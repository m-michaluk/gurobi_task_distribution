My solution  of integer linear programming exercise for Algorithimcs course, with implementation using Gurobi.

The task was to distribute tasks between employees.

Input:
 - bipartite graph, where one group of nodes represent employees, second group represent nodes and edges represent ability of employee to perform given task
 - for every employee, maximum load of work he can do
 - for every task, profit and minimum employees that should work on this task
 - maximum number of tasks that can be performed
 - additional requirment - every employee should perform the same part of the task

Output:
 - maximize profit
