def get_moving_averages(array, window_size):
    i = 0
    moving_averages = []

    while i < len(array) - window_size + 1:
        window = array[i: i + window_size]
        window_average = round(sum(window) / window_size, 2)
        moving_averages.append(window_average)
        i += 1

    return moving_averages
