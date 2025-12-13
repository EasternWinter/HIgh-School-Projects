J = int(input("Number of Jerseys: "))
A = int(input("Number of Athletes: "))
available = []
for j in range(J):
    size = input("Size of this jersey: ")
    available.append(size)
possible = 0
chosen = []
for a in range(A):
    req = input("Requested size and number: ").split()
    ind = int(req[1]) - 1
    #Since L<M<S in the alphabet, then if the available size's letter appears earlier in the alphabet, then it is larger.
    if available[ind] <= req[0] and ind not in chosen:
        possible += 1
        chosen.append(ind)
print(f"There are {possible} maximum possible requests that can be sdatisfied.")
