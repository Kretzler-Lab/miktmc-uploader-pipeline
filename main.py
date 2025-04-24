import asyncio
from pprint import pprint
import time
from lib.redcap_connection import RedcapConnection
from lib.halolink_connection import HalolinkConnection, HLField, HLStudy
from lib.uploader_connection import UploaderConnection
from services.halolink_service import parse_biopsy_id, HalolinkService
from model.image_metadata import ImageMetadata
from model.redcap_metadata import RedcapMetadata
from services.pipeline_service import PipelineService
import argparse

from services.redcap_service import RedcapService


class Main:
    def __init__(self):
        self.redcap_connection = RedcapConnection()
        self.halolink_connection = HalolinkConnection()
        self.uploader_connection = UploaderConnection()
        self.uploader_connection.get_mongo_connection()
        self.halolink_service = HalolinkService(self.halolink_connection)
        self.pipeline_service = PipelineService(self.halolink_connection, self.redcap_connection, self.uploader_connection)
        self.redcap_service = RedcapService(self.redcap_connection)

    async def connect_to_halolink(self):
        await self.halolink_connection.request_access_token()
        await self.halolink_connection.create_client_session()

    async def print_halolink_image_info(self, image_id: int):
        await self.connect_to_halolink()
        image = await self.halolink_connection.get_image_by_pk(image_id)
        print(image)

    async def print_study_info(self, study_pk: int):
        await self.connect_to_halolink()
        study = await self.halolink_connection.get_study_info(study_pk)
        print(study)

    def print_redcap_data_biopsy_id(self, biopsy_id: str):
        redcap_metadata = self.redcap_service.get_image_metadata_by_biopsy_id(biopsy_id)
        pprint(vars(redcap_metadata["parent_metadata"]))
        for slide in redcap_metadata["images"]:
            pprint(vars(slide))
            pprint(slide.get_halolink_updates())

    async def verify_slide_counts(self, biopsy_id: str, slide_type: str):
        await self.connect_to_halolink()
        if slide_type == "EM":
            result = await self.pipeline_service.compare_em_slide_counts(biopsy_id)
        else:
            result = await self.pipeline_service.compare_slide_counts(biopsy_id)
        print("Slide counts match") if result else print("Slide counts do not match")

    async def curegn_incoming_metadata_dry_run(self):
        await self.connect_to_halolink()
        await self.pipeline_service.get_metadata_for_images_in_study(HLStudy.INCOMING_CUREGN, "CureGN", True)

    async def curegn_escrow_1_metadata_dry_run(self):
        await self.connect_to_halolink()
        await self.pipeline_service.get_metadata_for_images_in_study(HLStudy.CUREGN_ESCROW_1,"CureGN", True)

    async def curegn_diabetes_incoming_metadata_dry_run(self):
        await self.connect_to_halolink()
        self.redcap_connection.connect_curegn_diabetes()
        await self.pipeline_service.get_metadata_for_images_in_study(HLStudy.INCOMING_CUREGN_DIABETES,"CureGN Diabetes", True)

    async def curegn_diabetes_escrow_1_metadata_dry_run(self):
        await self.connect_to_halolink()
        self.redcap_connection.connect_curegn_diabetes()
        await self.pipeline_service.get_metadata_for_images_in_study(HLStudy.CUREGN_DIABETES_ESCROW_1, "CureGN Diabetes", True)

    async def neptune_incoming_metadata_dry_run(self):
        self.redcap_connection.connect_neptune()
        await self.connect_to_halolink()
        await self.pipeline_service.get_metadata_for_images_in_study(HLStudy.INCOMING_NEPTUNE, "Neptune", True)

    async def neptune_escrow_1_metadata_dry_run(self):
        await self.connect_to_halolink()
        self.redcap_connection.connect_neptune()
        await self.pipeline_service.get_metadata_for_images_in_study(HLStudy.NEPTUNE_ESCROW_1, "Neptune", True)

    async def attach_curegn_incoming_metadata(self):
        await self.connect_to_halolink()
        await self.pipeline_service.get_metadata_for_images_in_study(HLStudy.INCOMING_CUREGN, "CureGN", False)

    async def attach_curegn_escrow_1_metadata(self):
        await self.connect_to_halolink()
        await self.pipeline_service.get_metadata_for_images_in_study(HLStudy.CUREGN_ESCROW_1, "CureGN", False)

    async def attach_curegn_diabetes_incoming_metadata(self):
        self.redcap_connection.connect_curegn_diabetes()
        await self.connect_to_halolink()
        await self.pipeline_service.get_metadata_for_images_in_study(HLStudy.INCOMING_CUREGN_DIABETES, "CureGN Diabetes", False)

    async def attach_curegn_diabetes_escrow_1_metadata(self):
        self.redcap_connection.connect_curegn_diabetes()
        await self.connect_to_halolink()
        await self.pipeline_service.get_metadata_for_images_in_study(HLStudy.CUREGN_DIABETES_ESCROW_1, "CureGN Diabetes", False)

    async def attach_neptune_incoming_metadata(self):
        await self.connect_to_halolink()
        self.redcap_connection.connect_neptune()
        await self.pipeline_service.get_metadata_for_images_in_study(HLStudy.INCOMING_NEPTUNE, "Neptune", False)

    async def attach_neptune_escrow_1_metadata(self):
        await self.connect_to_halolink()
        self.redcap_connection.connect_neptune()
        await self.pipeline_service.get_metadata_for_images_in_study(HLStudy.NEPTUNE_ESCROW_1, "Neptune", False)


if __name__ == "__main__":
    main = Main()
    parser = argparse.ArgumentParser(
        prog='MiKTMC Image Pipeline',
        description='Queries the HALOLink and REDCap APIs and allows the attaching of metadata and movement of HALOLink images for final ingestion.',
    )
    parser.add_argument(
        "-d",
        "--dry_run",
        choices=["CI", "CE1", "E1", "CDI", "CDE1", "NI", "NE1"],
        help='Execute a dry run of attaching metadata and moving images. Prints metadata and final action. Options are the source folder.',
        required=False,
    )
    parser.add_argument(
        "-a",
        "--attach",
        help='Attach REDCap metadata to all HALOLink images in source folder and move images to appropriate escrow folder. Options are the source folder. Prints metadata and action taken.',
        choices=["CI", "CE1", "E1", "CDI", "CDE1", "NI", "NE1"],
        required=False,
    )
    parser.add_argument(
        "-b",
        "--biopsy_id",
        help='Print biopsy information from REDCap',
        required=False,
    )
    parser.add_argument(
        "-c",
        "--count",
        choices=["EM", "WSI"],
        help='Verifies the number of image in HALOLink match the number of images from REDCap. Requires biopsy_id option.',
        required=False,
    )
    parser.add_argument(
        "-i",
        "--image_id",
        help='Prints image information from HALOLink.',
        required=False,
    )
    parser.add_argument(
        "-s",
        "--study_pk",
        help='Given a study PK, prints study/folder information from HALOLink. Useful for getting the ID from the PK.',
        required=False,
    )
    parser.add_argument(
        "-t",
        "--print_token",
        required=False,
        help='Prints a HALOLink access token. (e.g. to use in a graphQL client)',
        action='store_true'
    )
    args = parser.parse_args()
    if args.dry_run:
        if args.dry_run == "CE1" or args.dry_run == "E1":
            asyncio.run(main.curegn_escrow_1_metadata_dry_run())
        elif args.dry_run == "CI":
            asyncio.run(main.curegn_incoming_metadata_dry_run())
        elif args.dry_run == "CDI":
            asyncio.run(main.curegn_diabetes_incoming_metadata_dry_run())
        elif args.dry_run == "CDE1":
            asyncio.run(main.curegn_diabetes_escrow_1_metadata_dry_run())
        elif args.dry_run == "NI":
            asyncio.run(main.neptune_incoming_metadata_dry_run())
        elif args.dry_run == "NE1":
            asyncio.run(main.neptune_escrow_1_metadata_dry_run())
    elif args.attach:
        if args.attach == "CE1" or args.dry_run == "E1":
            asyncio.run(main.attach_curegn_escrow_1_metadata())
        elif args.attach == "CI":
            asyncio.run(main.attach_curegn_incoming_metadata())
        elif args.attach == "CDI":
            asyncio.run(main.attach_curegn_diabetes_incoming_metadata())
        elif args.attach == "CDE1":
            asyncio.run(main.attach_curegn_diabetes_escrow_1_metadata())
        elif args.attach == "NI":
            asyncio.run(main.attach_neptune_incoming_metadata())
        elif args.attach == "NE1":
            asyncio.run(main.attach_neptune_escrow_1_metadata())
    elif args.count:
        asyncio.run(main.verify_slide_counts(args.biopsy_id, args.count))
    elif args.biopsy_id:
        main.print_redcap_data_biopsy_id(args.biopsy_id)
    elif args.image_id:
        asyncio.run(main.print_halolink_image_info(int(args.image_id)))
    elif args.study_pk:
        asyncio.run(main.print_study_info(int(args.study_pk)))
    elif args.print_token:
        asyncio.run(main.connect_to_halolink())
        print(main.halolink_connection.access_token)
    else:
        print("Please choose an option. Run with --help for a list of options.")
