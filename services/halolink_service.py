from array import array

from lib.halolink_connection import HalolinkConnection


class HalolinkService:

    def __init__(self, halolink_connection: HalolinkConnection):
        self.halolink_connection = halolink_connection

    async def get_images_by_biopsy_id(self, study_pk: int, biopsy_id: str) -> list:
        images = await self.halolink_connection.get_images_in_study(study_pk)
        filtered_images = []
        for image in images:
            if biopsy_id + "_" in image['image']['tag']:
                filtered_images.append(image)
        return filtered_images
