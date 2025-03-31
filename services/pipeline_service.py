from lib.redcap_connection import RedcapConnection
from lib.halolink_connection import HalolinkConnection, HLStudy
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
        await self.halolink_connection.update_stain(halolink_image["id"], image_metadata.slide_stain)

    async def get_metadata_for_image(self, halolink_image: dict, default_study: str) -> ImageMetadata:
        image_name = halolink_image["image"]["tag"]
        image_barcode = halolink_image["image"]["barcode"]
        biopsy_id = parse_biopsy_id(image_name)
        image_metadata = ImageMetadata(RedcapMetadata(biopsy_id))
        if biopsy_id not in self.redcap_data_cache:
            redcap_data = self.redcap_service.get_image_metadata_by_biopsy_id(biopsy_id)
        else:
            redcap_data = self.redcap_data_cache[biopsy_id]

        if redcap_data:
            is_wsi = all(extension not in image_name for extension in ['jpg', 'JPG', 'tif', 'JPEG'])
            for image_field in halolink_image["image"]["fieldValues"]:
                if "Disease" in image_field["systemField"]["name"]:
                    image_metadata.error_message = "WARNING: Some metadata already exists. "

            if is_wsi:
                # WSIs have additional metadata.
                if "barcode" in halolink_image["image"]:
                    if image_barcode in redcap_data["wsi_images"]:
                        image_metadata = redcap_data["wsi_images"][image_barcode]
                    else:
                        # Just use the parent metadata if the barcode can't be found.
                        image_metadata = ImageMetadata(redcap_data["parent_metadata"])
                        image_metadata.image_type = "WSImage"
                        image_metadata.missing_metadata = True
                        image_metadata.error_message = "WARNING: Barcode " + str(image_barcode) + " not found for biopsy " + biopsy_id + ". "
                else:
                    image_metadata.missing_metadata = True
                    image_metadata.error_message = "WARNING: Barcode is blank. "
            else:
                # EMs and Slide Copy just use their parent metadata.
                image_metadata = ImageMetadata(redcap_data["parent_metadata"])

            # Get information from the Uploader database. If it's blank, use the default.
            uploader_info = self.uploader_connection.get_record_by_file_name(image_name)
            if uploader_info is not None:
                redcap_data["parent_metadata"].study_id = uploader_info["study"]
                if uploader_info["packageType"] == "Slide Copy":
                    image_metadata.image_type = "SCUImage"
                elif uploader_info["packageType"] == "Electron Microscopy Imaging":
                    image_metadata.image_type = "EMImage"
            else:
                # Almost all non-WSI images are EMIMages
                if not is_wsi:
                    image_metadata.image_type = "EMImage"
                redcap_data["parent_metadata"].study_id = default_study

            image_metadata.validate_metadata()
        else:
            image_metadata.in_error = True
            image_metadata.error_message = "ERROR: Biopsy ID " + biopsy_id + " not found."
        self.redcap_data_cache[biopsy_id] = redcap_data
        return image_metadata

    async def get_metadata_for_images_in_study(self, study: HLStudy, default_study: str, dry_run: bool = True) -> dict:
        images = await self.halolink_connection.get_images_in_study(study.value["pk"])
        image_metadata = {}
        count = 0
        print("Filename," + ImageMetadata(RedcapMetadata("")).get_metadata_header_string() + ",Action")
        for image in images:
            action = ""
            current_image_metadata = await self.get_metadata_for_image(image, default_study)
            image_metadata[image["image"]["tag"]] = current_image_metadata
            if current_image_metadata.in_error:
                action = "Left in current folder."
            elif current_image_metadata.missing_metadata:
                if not dry_run:
                    field_update_result = await self.halolink_service.update_image_metadata(image["image"]["id"], current_image_metadata)
                    if study != HLStudy.ESCROW_1:
                        move_result = await self.halolink_connection.move_image(image["image"]["id"], study.value["id"], HLStudy.ESCROW_1.value["id"])
                action = "Attached available metadata and moved/left in Escrow 1"
            else:
                if not dry_run:
                    field_update_result = await self.halolink_service.update_image_metadata(image["image"]["id"], current_image_metadata)
                    move_result = await self.halolink_connection.move_image(image["image"]["id"], study.value["id"], HLStudy.ESCROW_2.value["id"])
                action = "Attached available metadata and moved to Escrow 2"
            print(image["image"]["tag"] + "," + current_image_metadata.get_metadata_update_string_plain() + "," + "ACTION: " + action + ",")
            count = count + 1
        print(str(count) + " files processed.")
        return image_metadata


