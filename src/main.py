from cli import cli


def main() -> None:
    try:
        args = cli.get_user_input()

        for i in range(int(args.get("num_pts", 0))):
            print(f"Calibrating pt {i}")

    except KeyboardInterrupt:
        print("Exiting...")


if __name__ == "__main__":
    main()
