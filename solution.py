import pandas as pd
import numpy as np
import gurobipy as gp
from gurobipy import GRB

test = ''

# # # Wczytywanie danych
def read_bounds():
    bounds = pd.read_csv(test + 'bounds.csv')
    return bounds.B[0]


def read_employees():
    employees = pd.read_csv(test + 'employees.csv')
    return dict(zip(employees.id_employee, employees.b))


def read_jobs():
    jobs = pd.read_csv(test + 'jobs.csv')
    job_id = jobs.id_job
    return (dict(zip(job_id, jobs.c)), dict(zip(job_id, jobs.l)))

def read_bipartite():
    bipartite = pd.read_csv(test + 'bipartite.csv')
    employees = bipartite.id_employee
    jobs = bipartite.id_job

    table = bipartite.groupby(['id_employee'])
    map_employee_to_jobs_list = table['id_job'].apply(list).to_dict()

    table = bipartite.groupby(['id_job'])
    map_job_to_employees_list = table['id_employee'].apply(list).to_dict()
    return list(zip(employees, jobs)), np.unique(jobs), np.unique(employees), map_employee_to_jobs_list, map_job_to_employees_list
# # #

# edges - lista par (id_employee, id_job)
# jobs - lista id zadań, które jakiś pracownik może wykonywać
# employees - lista pracowników, którzy mogą wykonywać jakieś zadania
# map_employee_to_jobs_list - słownik (id_employee, lista zadań, które może wykonywać dany pracownik)
# map_job_to_employees_list - słownik (id_job, lista pracowników, którzy mogą wykonywać dane zadanie)
edges, jobs, employees, map_employee_to_jobs_list, map_job_to_employees_list = read_bipartite()

b = read_employees() # wektor maksymalnych obciążeń pracowników
B = read_bounds() # ograniczenie na liczbę zadań
c, l = read_jobs() # c - wektor zysku, l - wektor minimalnej liczby pracowników wykonujących zadanie

n = len(employees)
m = len(jobs)
 
model = gp.Model("maximum profit task distribution")

# 0 jeśli nikt nie wykonuje danego zadaniea, wpp. 1/x[j] == ile pracowników wykonuje dane zadanie
x = model.addVars([job for job in jobs], vtype=GRB.CONTINUOUS, name='x')

# 1 jeśli do j-tego zadania przypisanych jest i pracowników, 0 jeśli przydzielono do niego inną liczbę pracowników.
delta = model.addVars([(j, i) for i in range(1,n+1) for j in jobs], vtype=GRB.BINARY, name='d')

# warunek zapewnia, że x[j] \in {0, 1/2, 1/3, ..., 1/n} (co najwyżej jedno \delta różne od zera)
model.addConstrs(x[j] == sum(delta[(j, i)]/i for i in range(1, n+1)) for j in jobs)

# czy zadanie jest wykonywane
z = model.addVars([job for job in jobs], vtype=GRB.BINARY, name='z')
# dla danego j, dla każdego i, tylko jedna ze zmiennych delta_ij powinna być równa 1, bądź równa 0, jeśli zadanie nie jest wykonywane
model.addConstrs(z[j] == sum(delta[(j, i)] for i in range(1,n+1)) for j in jobs)
# liczba wykonywanych zadań ograniczona przez B
model.addConstr(sum(z[j] for j in jobs) <= B)


p = model.addVars([e for e in edges], vtype=GRB.BINARY, name='p')

# liczba pracowników wykonujących dane zadanie j musi być równa 1/x[j] lub zero, jeśli zadanie nie jest wykonywane
model.addConstrs(sum(p[(emp, job)] for emp in map_job_to_employees_list[job]) == sum(delta[(job, i)]*i for i in range(1,n)) for job in jobs)

# liczba pracowników wykonujących zadanie j musi być >= l[j] o ile zadanie jest w ogóle wykonywane
model.addConstrs(sum(p[(emp, job)] for emp in map_job_to_employees_list[job]) >= l[job] * z[job] for job in map_job_to_employees_list)

# w[(i, j)] <- jaką część zadania j wykonuje pracownik i 
w = model.addVars([e for e in edges], vtype=GRB.CONTINUOUS, name='w')

# ograniczenia, gwarantujące, że w[(i,j)] = x[j] <=> p[(i,j)] == 1 i  w[(i,j)] = 0 <=> p[(i,j)] == 0
# model.addConstrs(w[e] <= p[e] for e in edges)
# model.addConstrs(w[e] <= x[e[1]] for e in edges)
# model.addConstrs(w[e] >= 0 for e in edges)
# model.addConstrs(w[e] >= p[e] - 1 + x[e[1]] for e in edges)
# powyższe warunki można zapisać prościej korzystając z funkcji z gurobi
for e in edges:
    model.addGenConstrIndicator(p[e], 1, w[e] == x[e[1]])

# dla każdego pracownika suma obciążeń ze wszystkich zadań musi być mniejsze niż określone dla niego max obciążenie
for emp in map_employee_to_jobs_list:
    model.addConstr(sum(w[(emp, job)] for job in map_employee_to_jobs_list[emp]) <= b[emp])


# funkcja celu, maksymalizacja zysku z wykonywanych zadań
model.setObjective(sum(c[j] * z[j] for j in jobs), GRB.MAXIMIZE)

model.params.MIPGap = 0.003

model.optimize()

# wypisanie wyniku
print(int(model.getObjective().getValue()))

for j in c:
    if (j in z):
        if (z[j].X != 0):
            print(int(1/x[j].X), end=" ")
            emp_list = [str(emp) for emp in map_job_to_employees_list[j] if p[(emp, j)].X != 0]
            print(' '.join(emp_list))
        else:
            print("0")
    else:
        print("0")    
