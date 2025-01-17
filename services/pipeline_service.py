from lib.redcap_connection import RedcapConnection
from lib.halolink_connection import HalolinkConnection, HLField
from services.halolink_service import HalolinkService

class PipelineService:
    def __init__(self, halolink_connection: HalolinkConnection, redcap_connection: RedcapConnection):
        self.halolink_connection = halolink_connection
        self.redcap_connection = redcap_connection
        self.halolink_service = HalolinkService(self.halolink_connection)
        
    async def compare_slide_counts(self, biopsy_id: str):
        halolink_slides = await self.halolink_service.get_curegn_inbox_images_by_biopsy_id(biopsy_id)
        redcap_slides = self.redcap_connection.get_by_biopsy_id(biopsy_id)
        numbarcodes = int(redcap_slides[0]['numbarcodes']) if redcap_slides[0]['numbarcodes'] else 0
        return len(halolink_slides) == numbarcodes

