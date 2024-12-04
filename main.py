import asyncio
from lib.redcap_connection import RedcapConnection
from lib.halolink_connection import HalolinkConnection
from services.halolink_service import HalolinkService
import argparse


class Main:
    def __init__(self):
        self.redcap_connection = RedcapConnection()
        self.halolink_connection = HalolinkConnection()
        self.halolink_service = HalolinkService(self.halolink_connection)

    async def connect_to_halolink(self):
        await self.halolink_connection.request_access_token()
        await self.halolink_connection.create_client_session()

    async def print_halolink_image_info(self, image_id: int):
        await self.connect_to_halolink()
        image = await self.halolink_connection.get_image_by_pk(image_id)
        print(image)

    async def print_halolink_images(self, study_id: int):
        await self.connect_to_halolink()
        study = await self.halolink_connection.get_images_in_study(study_id)
        print(study)

    async def print_study_info(self, study_id: int):
        await self.connect_to_halolink()
        study = await self.halolink_connection.get_study_info(study_id)
        print(study)

    async def print_curegn_inbox_images_by_biopsy_id(self, biopsy_id: str):
        await self.connect_to_halolink()
        images = await self.halolink_service.get_curegn_inbox_images_by_biopsy_id(biopsy_id)
        print(images)

    async def print_move_image_result(self, image_id: str, src_study_id: str, dest_study_id: str):
        await self.connect_to_halolink()
        result = await self.halolink_connection.move_image(image_id, src_study_id, dest_study_id)
        print(result)

    async def print_halolink_schema(self):
        await self.connect_to_halolink()
        print(self.halolink_connection.get_schema())

    def print_redcap_data_biopsy_id(self, biopsy_id: str):
        print(self.redcap_connection.get_by_biopsy_id(biopsy_id))


if __name__ == "__main__":
    main = Main()
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-a",
        "--api_source",
        choices=["redcap", "halolink"],
        required=True,
    )
    parser.add_argument(
        "-b",
        "--biopsy_id",
        required=False,
    )
    parser.add_argument(
        "-i",
        "--image_id",
        required=False,
    )
    parser.add_argument(
        "-s",
        "--study_id",
        required=False,
    )
    parser.add_argument(
        "-t",
        "--print_token",
        required=False,
        action='store_true'
    )
    args = parser.parse_args()

    asyncio.run(main.print_move_image_result('SW1hZ2U6NjA3NDI=', 'U3R1ZHk6OTU4MA==', 'U3R1ZHk6OTU3NQ=='))

    #asyncio.run(main.print_study_info(9575))

    # if args.api_source == "redcap":
    #     main.print_redcap_data_biopsy_id(args.biopsy_id)
    # elif args.api_source == "halolink":
    #     if args.image_id:
    #         asyncio.run(main.print_halolink_image_info(int(args.image_id)))
    #     elif args.biopsy_id:
    #         asyncio.run(main.print_curegn_inbox_images_by_biopsy_id(args.biopsy_id))
    #     elif args.print_token:
    #         asyncio.run(main.connect_to_halolink())
    #         print(main.halolink_connection.access_token)
    #     else:
    #         asyncio.run(main.print_halolink_schema())
