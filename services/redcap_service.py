from lib.redcap_connection import RedcapConnection
from model.image_metadata import ImageMetadata
from model.redcap_metadata import RedcapMetadata


class RedcapService:
    def __init__(self, redcap_connection: RedcapConnection):
        self.redcap_connection = redcap_connection

    def get_image_metadata_by_biopsy_id(self, biopsy_id: str) -> dict:
        redcap_result = self.redcap_connection.get_by_biopsy_id(biopsy_id)[0]
        redcap_metadata = RedcapMetadata(biopsy_id)
        redcap_metadata.fill_with_redcap_result(redcap_result)
        slides = []
        if redcap_result["numbarcodes"]:
            num_slides = int(redcap_result["numbarcodes"])
            for i in range(1, num_slides + 1):
                slide = ImageMetadata(biopsy_id)
                slide.fill_with_redcap_result(redcap_result, i)
                slide.parent_metadata = redcap_metadata
                slides.append(slide)
        return {"parent_metadata": redcap_metadata, "images": slides}


