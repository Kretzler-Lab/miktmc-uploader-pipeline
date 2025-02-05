from array import array

from lib.halolink_connection import HalolinkConnection
from model.image_metadata import ImageMetadata

CUREGN_INBOX_ID = 9783
ESCROW_1_ID = 9735

class HalolinkService:

    def __init__(self, halolink_connection: HalolinkConnection):
        self.halolink_connection = halolink_connection


    async def get_curegn_inbox_images_by_biopsy_id(self, biopsy_id: str) -> list:
        return await self.get_images_by_biopsy_id(CUREGN_INBOX_ID, biopsy_id)

    async def get_escrow_1_images_by_biopsy_id(self, biopsy_id: str) -> list:
        return await self.get_images_by_biopsy_id(ESCROW_1_ID, biopsy_id, True)

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
