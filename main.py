import asyncio
from pprint import pprint

from lib.redcap_connection import RedcapConnection
from lib.halolink_connection import HalolinkConnection, HLField
from model.image_metadata import ImageMetadata
from services.halolink_service import HalolinkService
from services.pipeline_service import PipelineService
import argparse

from services.redcap_service import RedcapService


class Main:
    def __init__(self):
        self.redcap_connection = RedcapConnection()
        self.halolink_connection = HalolinkConnection()
        self.halolink_service = HalolinkService(self.halolink_connection)
        self.pipeline_service = PipelineService(self.halolink_connection, self.redcap_connection)
        self.redcap_service = RedcapService(self.redcap_connection)

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

    async def print_set_image_fields_result(self, image_id: str):
        await self.connect_to_halolink()
        updates = [{"field_enum": HLField.STUDY_ID, "value": "TestStudy"},
                   {"field_enum": HLField.DISEASE, "value": "CKD"}]
        result = await self.halolink_connection.set_image_fields(image_id, updates, "ZTestStudy")
        print(result)

    async def print_move_image_result(self, image_id: str, src_study_id: str, dest_study_id: str):
        await self.connect_to_halolink()
        result = await self.halolink_connection.move_image(image_id, src_study_id, dest_study_id)
        print(result)

    async def print_halolink_schema(self):
        await self.connect_to_halolink()
        print(self.halolink_connection.get_schema())

    def print_redcap_data_biopsy_id(self, biopsy_id: str):
        redcap_metadata = self.redcap_service.get_image_metadata_by_biopsy_id(biopsy_id)
        pprint(vars(redcap_metadata["parent_metadata"]))
        for slide in redcap_metadata["images"]:
            pprint(vars(slide))
            pprint(slide.get_halolink_updates())

    async def verify_slide_counts(self, biopsy_id: str):
        await self.connect_to_halolink()
        result = await self.pipeline_service.compare_slide_counts(biopsy_id)
        print("Slide counts match") if result else print("Slide counts do not match")

    async def update_stain(self, image_id: str, stain: str):
        await self.connect_to_halolink()
        result = await self.halolink_connection.update_stain(image_id, stain)
        print(result)


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
        "-c",
        "--count",
        required=False,
        action='store_true'
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
    if args.api_source == "redcap":
        if args.count:
            asyncio.run(main.verify_slide_counts(args.biopsy_id))
        else:
            main.print_redcap_data_biopsy_id(args.biopsy_id)
    elif args.api_source == "halolink":
        if args.image_id:
            asyncio.run(main.print_halolink_image_info(int(args.image_id)))
        elif args.count:
            asyncio.run(main.verify_slide_counts(args.biopsy_id))
        elif args.biopsy_id:
            asyncio.run(main.print_curegn_inbox_images_by_biopsy_id(args.biopsy_id))
        elif args.print_token:
            asyncio.run(main.connect_to_halolink())
            print(main.halolink_connection.access_token)
        else:
            asyncio.run(main.print_halolink_schema())
