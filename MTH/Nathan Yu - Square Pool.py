N = int(input("Size of yard: "))
T = int(input("Number of Trees: "))
#Create the grid and mark tree locations
yard = [[0] * N for _ in range(N)]
for _ in range(T):
    R, C = map(int, input("Tree Location: ").split())
    yard[R - 1][C - 1] = 1  #mark tree

#Initialize dp array
dp = [[0] * N for _ in range(N)]
max_side = 0

for i in range(N):
    for j in range(N):
        if yard[i][j] == 0:
            if i == 0 or j == 0:
                dp[i][j] = 1
            else:
                dp[i][j] = 1 + min(
                    dp[i - 1][j],     # top
                    dp[i][j - 1],     # left
                    dp[i - 1][j - 1]  # top-left
                )
            max_side = max(max_side, dp[i][j])
        #else dp[i][j] stays 0 (tree)
    
print(max_side)
