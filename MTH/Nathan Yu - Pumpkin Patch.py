R = int(input("Number of Rows: "))
C = int(input("Number of Columns: "))
earning = 0
field = []
for r in range(R):
    row = input("Row: ")
    field.append(list(row))
A = int(input("Starting Row: "))
B = int(input("Starting Colomn: "))

def move(A, B):
    global earning
    if A >= R or A < 0 or B >= C or B < 0 or field[A][B]=="*":
        return
    if field[A][B] == "L":
        earning += 10
    elif field[A][B] == "M":
        earning += 5
    elif field[A][B] == "S":
        earning += 1
    field[A][B] = "*"
    move(A+1, B)
    move(A-1, B)
    move(A, B+1)
    move(A, B-1)
move(A, B)
print(f"The farmer earns {earning} dollars.")
