from lib.redcap_connection import RedcapConnection
import argparse

class Main:
    def __init__(self):
        self.redcap_connection = RedcapConnection()

    def print_redcap_data_biopsy_id(self, biopsy_id: str):
        print(self.redcap_connection.get_by_biopsy_id(biopsy_id))


if __name__ == "__main__":
    main = Main()
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-a",
        "--api_source",
        choices=["redcap"],
        required=True,
    )
    parser.add_argument(
        "-b",
        "--biopsy_id",
        required=True,
    )
    args = parser.parse_args()

    if args.api_source == "redcap":
        main.print_redcap_data_biopsy_id(args.biopsy_id)