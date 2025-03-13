from lib.redcap_connection import RedcapConnection
from lib.halolink_connection import HalolinkConnection, HLField
from lib.uploader_connection import UploaderConnection
from model.image_metadata import ImageMetadata
from model.redcap_metadata import RedcapMetadata
from services.halolink_service import HalolinkService, parse_biopsy_id
from services.redcap_service import RedcapService

class PipelineService:
    def __init__(self, halolink_connection: HalolinkConnection, redcap_connection: RedcapConnection, uploader_connection: UploaderConnection):
        self.halolink_connection = halolink_connection
        self.redcap_connection = redcap_connection
        self.halolink_service = HalolinkService(self.halolink_connection)
        self.redcap_service = RedcapService(self.redcap_connection)
        self.uploader_connection = uploader_connection
        
    async def compare_slide_counts(self, biopsy_id: str):
        halolink_slides = await self.halolink_service.get_incoming_curegn_images_by_biopsy_id(biopsy_id)
        redcap_slides = self.redcap_connection.get_by_biopsy_id(biopsy_id)
        numbarcodes = int(redcap_slides[0]['numbarcodes']) if redcap_slides[0]['numbarcodes'] else 0
        return len(halolink_slides) == numbarcodes

    async def compare_em_slide_counts(self, biopsy_id: str):
        halolink_slides = await self.halolink_service.get_escrow_1_images_by_biopsy_id(biopsy_id)
        redcap_slides = self.redcap_connection.get_by_biopsy_id(biopsy_id)
        numems = int(redcap_slides[0]['numems_qc']) if redcap_slides[0]['numems_qc'] else 0
        return len(halolink_slides) == numems

    async def get_metadata_for_images_in_study(self, study_id: int, default_study: str):
        images = await self.halolink_connection.get_images_in_study(study_id)
        redcap_data = {}
        image_metadata = {}
        for image in images:
            metadata_exists = False
            biopsy_id = parse_biopsy_id(image["image"]["tag"])
            current_image_metadata = ImageMetadata(RedcapMetadata(biopsy_id))
            is_wsi = all(extension not in image['image']['tag'] for extension in ['jpg', 'JPG', 'tif', 'JPEG'])
            # Check to see if the metadata has already been set.
            for image_field in image["image"]["fieldValues"]:
                if "Disease" in image_field["systemField"]["name"]:
                    metadata_exists = True
                    current_image_metadata.in_error = True
                    current_image_metadata.error_message = "WARNING: Metadata already exists."
                    break
            if not metadata_exists:
                if biopsy_id not in redcap_data:
                    redcap_data[biopsy_id] = self.redcap_service.get_image_metadata_by_biopsy_id(biopsy_id)

                if redcap_data[biopsy_id]:
                    # Get the study ID from the Uploader database. If it's blank, use the default
                    if not redcap_data[biopsy_id]["parent_metadata"].study_id:
                        study = self.uploader_connection.get_study_id_by_file_name(image["image"]["tag"])
                        if study == "":
                            study = default_study
                        redcap_data[biopsy_id]["parent_metadata"].study_id = study
                    if is_wsi:
                        if "barcode" in image["image"]:
                            if image["image"]["barcode"] in redcap_data[biopsy_id]["wsi_images"]:
                                current_image_metadata = redcap_data[biopsy_id]["wsi_images"][image["image"]["barcode"]]
                            else:
                                current_image_metadata = ImageMetadata(redcap_data[biopsy_id]["parent_metadata"])
                                current_image_metadata.image_type = "WSImage"
                                current_image_metadata.in_error = True
                                current_image_metadata.error_message = "WARNING: Barcode " + str(image["image"]["barcode"]) + " not found for biopsy " + biopsy_id + "."
                        else:
                            current_image_metadata.in_error = True
                            current_image_metadata.error_message = "WARNING: Barcode is blank."
                    else:
                        current_image_metadata = ImageMetadata(redcap_data[biopsy_id]["parent_metadata"])
                        current_image_metadata.image_type = "EMImage"
                else:
                    current_image_metadata.in_error = True
                    current_image_metadata.error_message = "WARNING: Biopsy ID " + biopsy_id + " not found."

            image_metadata[image["image"]["tag"]] = current_image_metadata
        return image_metadata


