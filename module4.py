def main():
    N = int(input("Enter a positive integer N: "))

    numbers = []

    for i in range(N):
        num = int(input(f"Enter number {i + 1}: "))
        numbers.append(num)

    X = int(input("Enter an integer X: "))

    if X in numbers:
        index = numbers.index(X) + 1
        print(index)
    else:
        print(-1)

if __name__ == "__main__":
    main()
