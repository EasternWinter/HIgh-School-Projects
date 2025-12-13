M = int(input("Rows: "))
N = int(input("Columns: "))
room = []
for m in range(M):
    row = list(map(int, input("Row: ").split()))
    room.append(row)
