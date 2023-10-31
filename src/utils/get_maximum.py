import numpy as np


def pt_from(origin, angle, distance):
    """
    compute the point [x, y] that is 'distance' apart from the origin point
    perpendicular
    """
    x = origin[1] + np.sin(angle) * distance
    y = origin[0] + np.cos(angle) * distance
    return np.array([int(y), int(x)])
def find_edge(p1, p2, angle_radians, edges):
    distance = 0
    save = []
    while True:
        # as we want the width of the "start", we choose p1
        x, y = pt_from(p1, angle_radians, distance)
        if x < 0 or x >= edges.shape[0] or y < 0 or y >= edges.shape[1]:
            break
        hit_zone = edges[x, y] == 255
        if np.any(hit_zone):
            save.append((y, x))
            break
        distance += 0.01
    return save


def get_points(start, end):
    p1 = start[0:2]
    p1 = np.array([p1[1], p1[0]])
    p2 = end[0:2]
    p2 = np.array([p2[1], p2[0]])
    return np.array([p1, p2])


def get_max_approx(top_arr, bottom_arr):
    if len(top_arr) != len(bottom_arr):
        print("error not the same nbr of pts")
        return
    vector = np.array(top_arr) - np.array(bottom_arr)
    norms = np.linalg.norm(vector, axis=1)
    max_norm = norms[0]
    save_index = 0
    for i in range(len(top_arr)):
        if norms[i] > max_norm:
            if norms[i] > norms[0] * 1.5:
                break
            max_norm = norms[i]
            save_index = i
    return save_index


def vector_angle_plus(p1, p2):
    vector = np.array([p2[0] - p1[0], p2[1] - p1[1]])
    return np.arctan2(vector[1], vector[0]) + np.pi / 2


def vector_angle_minus(p1, p2):
    vector = np.array([p2[0] - p1[0], p2[1] - p1[1]])
    angle_radians = np.arctan2(vector[1], vector[0]) - np.pi / 2
    return angle_radians


def get_maximum_range(angle_radians, result, edges):
    save = []
    # for all the points between p1 and p2
    for point in result:
        distance = 0
        while True:

            x, y = pt_from(point, angle_radians, distance)
            if x < 0 or x >= edges.shape[0] or y < 0 or y >= edges.shape[1]:
                break

            # Check if we've found an edge pixel
            # hit_zone = edges[y-1:y+2, x-1:x+2] == 255# 3 x 3
            hit_zone = edges[x, y] == 255
            if np.any(hit_zone):
                save.append((y, x))
                break

            distance += 0.01
    return save

def _get_maximum(start, end, edges, angle, is_start):

    p1, p2 = get_points(start, end)
    vector = np.array([p2[0] - p1[0], p2[1] - p1[1]])
    angle_radians = np.arctan2(vector[1], vector[0]) - angle
    max1 = find_edge(p1, p2, angle_radians, edges)
    angle_radians = (np.arctan2(vector[1], vector[0]) + angle) * is_start
    max2 = find_edge(p1, p2, angle_radians, edges)
    return np.linalg.norm(np.array(max1) - np.array(max2))

def get_maximum_line(start, end, edges):
    return _get_maximum(start, end, edges, 0, -1)

def get_maximum_start(start, end, edges):
    return _get_maximum(start, end, edges, np.pi / 2, 1)

def get_maximum_point(start, end, edges):

    # get the maximums for calf and forearm
    p1, p2 = get_points(start, end)
    # create an array with 100 points between start and end
    x_values = np.linspace(p1[1], p2[1], 100)
    y_values = np.linspace(p1[0], p2[0], 100)
    result = [(y, x) for x, y in zip(x_values, y_values)]
    # set the angle in the direction of the edges
    angle_radians = vector_angle_plus(p1, p2)
    r_side = get_maximum_range(angle_radians, result, edges)
    # set the angle in the direction of other side
    angle_radians = vector_angle_minus(p1, p2)
    l_side = get_maximum_range(angle_radians, result, edges)
    # get the index of the max
    index = get_max_approx(r_side, l_side)
    return result[index][::-1]

def get_maximum_pit(start, edges):

    point = start[0:2]
    point = np.array([point[1], point[0]])
    point2 = np.array([point[0] + 5, point[1]])
    vector = np.array([point2[0] - point[0], point2[1] - point[1]])
    angle_radians = np.arctan2(vector[1], vector[0])
    max_save = find_edge(point, point2, angle_radians, edges)
    angle_radians_left = angle_radians
    angle_radians_right = angle_radians
    max_save_right = max_save
    max_save_left = max_save

    while True:
        angle_radians_left += 0.01
        max_last_right = find_edge(point, point2, angle_radians_left, edges)
        if (np.linalg.norm(max_last_right) < np.linalg.norm(max_save_right)):
            break
        max_save_right = max_last_right
    while True:
        angle_radians_right -= 0.01
        max_last_left = find_edge(point, point2, angle_radians_right, edges)
        if (np.linalg.norm(max_last_left) < np.linalg.norm(max_save_left)):
            break
        max_save_left = max_last_left
    delta = np.linalg.norm(abs(np.array(max_last_left) - np.array(max_last_right)))
    distance = np.linalg.norm(max(max_save_left, max_last_right))
    point = max(max_save_left, max_last_right)
    #if distance * 0.05 < delta:
    #    return 0, 0
    return point[0], int(distance)