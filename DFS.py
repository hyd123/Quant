
def dfs(matrix, start, end, now, count):
    if now[0] < 0 or now[1] < 0 or now[0] > len(matrix) - 1 or now[1] > len(matrix[0]) - 1:
        return False
    if matrix[now[0]][now[1]] == 1:
        return False
    count = count + 1
    if now == end:
        if count == len(matrix) * len(matrix[0]):
            return True
        return False
    matrix[now[0]][now[1]] = 1
    moves = [[0, -1], [0, 1], [-1, 0], [1, 0]]
    is_ok = False
    for move in moves:
        if dfs(matrix, start, end, [now[0] + move[0], now[1] + move[1]], count):
            is_ok = True
            break
    matrix[now[0]][now[1]] = 0
    return is_ok

matrix = [[0] * 6 for i in range(3)]
start = [0, 0]
end = [2, 0]

print(dfs(matrix, start, end, [0, 0], 0))




