# write a program to print the fibonacci series using recursion


def fibonacci(n):
    # Base case: If n is less than or equal to 0, return 0 as the Fibonacci sequence starts from 0.
    if n <= 0:
        return 0
    # Base case: If n is 1, return 1 as the Fibonacci sequence has 1 as its second number.
    elif n == 1:
        return 1
    # Recursive case: For n greater than 1, the Fibonacci number is the sum of the two preceding ones.
    else:
        # This line calculates the nth Fibonacci number by recursively calling the fibonacci function
        # for the two preceding numbers in the sequence (n-1 and n-2) and summing their results.
        # For example, if we want to find fibonacci(4), it will calculate fibonacci(3) and fibonacci(2),
        # then add their results together. fibonacci(3) will calculate fibonacci(2) and fibonacci(1),
        # and fibonacci(2) will calculate fibonacci(1) and fibonacci(0). This process continues
        # until it reaches the base cases (n <= 0 or n == 1), at which point it starts returning
        # values back up the call stack.
        return fibonacci(n-1) + fibonacci(n-2)



print(fibonacci(5))

