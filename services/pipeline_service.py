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
        self.redcap_data_cache = {}


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

    async def add_metadata_one_image(self, image_pk: int):
        halolink_image = await self.halolink_connection.get_image_by_pk(image_pk)
        image_metadata = await self.get_metadata_for_image(halolink_image, "CureGN")
        await self.halolink_connection.set_image_fields(halolink_image["id"], image_metadata.get_halolink_updates())

    async def get_metadata_for_image(self, halolink_image: dict, default_study: str) -> ImageMetadata:
        image_name = halolink_image["image"]["tag"]
        image_barcode = halolink_image["image"]["barcode"]
        biopsy_id = parse_biopsy_id(image_name)
        image_metadata = ImageMetadata(RedcapMetadata(biopsy_id))
        if biopsy_id not in self.redcap_data_cache:
            redcap_data = self.redcap_service.get_image_metadata_by_biopsy_id(biopsy_id)
            self.redcap_data_cache[biopsy_id] = redcap_data
        else:
            redcap_data = self.redcap_data_cache[biopsy_id]

        is_wsi = all(extension not in image_name for extension in ['jpg', 'JPG', 'tif', 'JPEG'])
        for image_field in halolink_image["image"]["fieldValues"]:
            if "Disease" in image_field["systemField"]["name"]:
                image_metadata.in_error = True
                image_metadata.error_message = "WARNING: Metadata already exists."
                return image_metadata

        # Get the study ID from the Uploader database. If it's blank, use the default.
        if not redcap_data["parent_metadata"].study_id:
            study = self.uploader_connection.get_study_id_by_file_name(image_name)
            if study == "":
                study = default_study
            redcap_data["parent_metadata"].study_id = study

        if is_wsi:
            # WSIs have additional metadata.
            if "barcode" in halolink_image["image"]:
                if image_barcode in redcap_data["wsi_images"]:
                    image_metadata = redcap_data["wsi_images"][image_barcode]
                else:
                    # Just use the parent metadata if the barcode can't be found.
                    image_metadata = ImageMetadata(redcap_data["parent_metadata"])
                    image_metadata.image_type = "WSImage"
                    image_metadata.in_error = True
                    image_metadata.error_message = "WARNING: Barcode " + str(image_barcode) + " not found for biopsy " + biopsy_id + "."
            else:
                image_metadata.in_error = True
                image_metadata.error_message = "WARNING: Barcode is blank."
        else:
            # EMs just use their parent metadata.
            image_metadata = ImageMetadata(redcap_data[biopsy_id]["parent_metadata"])
            image_metadata.image_type = "EMImage"
        self.redcap_data_cache[biopsy_id] = redcap_data
        return image_metadata

    async def get_metadata_for_images_in_study(self, study_id: int, default_study: str) -> dict:
        images = await self.halolink_connection.get_images_in_study(study_id)
        image_metadata = {}
        for image in images:
            metadata_exists = False
            current_image_metadata = ImageMetadata(RedcapMetadata(""))
            # Check to see if the metadata has already been set.
            for image_field in image["image"]["fieldValues"]:
                if "Disease" in image_field["systemField"]["name"]:
                    metadata_exists = True
                    current_image_metadata.in_error = True
                    current_image_metadata.error_message = "WARNING: Metadata already exists."
                    break
            if not metadata_exists:
                current_image_metadata = await self.get_metadata_for_image(image, default_study)
            image_metadata[image["image"]["tag"]] = current_image_metadata
            print(image["image"]["tag"] + "," + current_image_metadata.get_metadata_update_string_plain())
        return image_metadata


