from array import array

from lib.halolink_connection import HalolinkConnection
from model.image_metadata import ImageMetadata

INCOMING_CUREGN_ID = 9783
ESCROW_1_ID = 9735
ANNOTATION_TEST_ID = 9586
COLLEEN_TEST_ID = 9580


def parse_biopsy_id(image_name: str):
    split_image = image_name.split("_")
    return split_image[0] + "_" + split_image[1]


class HalolinkService:

    def __init__(self, halolink_connection: HalolinkConnection):
        self.halolink_connection = halolink_connection

    async def get_images_by_biopsy_id(self, study_pk: int, biopsy_id: str, EM: bool = False) -> list:
        images = await self.halolink_connection.get_images_in_study(study_pk)
        filtered_images = []
        for image in images:
            if biopsy_id + "_" in image['image']['tag'] and EM == ('.jpg' in image['image']['tag']):
                filtered_images.append(image)
        return filtered_images

    async def update_image_metadata(self, image_id: str, image_metadata: ImageMetadata):
        results = [await self.halolink_connection.update_stain(image_id, image_metadata.slide_stain),
                   await self.halolink_connection.set_image_fields(image_id, image_metadata.get_halolink_updates())]
        return results
