def main():
    with open("input.txt", "r") as f:
        output = solve(f.read())
    with open("output.txt", "w") as w:
        w.write(output)

if __name__ == '__main__':
    main()