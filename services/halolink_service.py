from array import array

from lib.halolink_connection import HalolinkConnection

CUREGN_INBOX_ID = 9783

class HalolinkService:

    def __init__(self, halolink_connection: HalolinkConnection):
        self.halolink_connection = halolink_connection


    async def get_curegn_inbox_images_by_biopsy_id(self, biopsy_id: str) -> list:
        return await self.get_images_by_biopsy_id(CUREGN_INBOX_ID, biopsy_id)


    async def get_images_by_biopsy_id(self, study_pk: int, biopsy_id: str) -> list:
        images = await self.halolink_connection.get_images_in_study(study_pk)
        filtered_images = []
        for image in images:
            if biopsy_id + "_" in image['image']['tag']:
                filtered_images.append(image)
        return filtered_images
