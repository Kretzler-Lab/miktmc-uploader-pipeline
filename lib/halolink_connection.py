import ssl
import os
import aiohttp
from gql import Client
from gql import gql
from gql.transport.websockets import WebsocketsTransport
from enum import Enum

HALOLINK_HOST = "dpr.niddk.nih.gov"


class HLField(Enum):
    STUDY_ID = {"id": "U3lzdGVtRmllbGQ6Mw==", "name": "StudyID"}
    ORGAN = {"id": "U3lzdGVtRmllbGQ6MjE=", "name": "Organ"}
    IMAGE_TYPE = {"id": "U3lzdGVtRmllbGQ6MTU=", "name": "Image_Type"}
    BIOPSY_DATE = {"id": "U3lzdGVtRmllbGQ6Ng==", "name": "Biopsy_Date"}
    NPT_PATIENT_STUDY_ID = {"id": "U3lzdGVtRmllbGQ6OQ==", "name": "NPT_PatientStudyID"}
    CGN_PATIENT_STUDY_ID = {"id": "U3lzdGVtRmllbGQ6MTA=", "name": "CGN_PatientStudyID"}
    DISEASE = {"id": "U3lzdGVtRmllbGQ6MTE=", "name": "Disease"}
    BIOPSY_ID = {"id": "U3lzdGVtRmllbGQ6MTI=", "name": "BiopsyID"}
    TISSUE_COMMENT = {"id": "U3lzdGVtRmllbGQ6MjI=", "name": "Tissue_Comment"}
    EVENT_TYPE = {"id": "U3lzdGVtRmllbGQ6MTY=", "name": "Event_Type"}
    LEVEL = {"id": "U3lzdGVtRmllbGQ6MTQ=", "name": "Level"}


class HalolinkConnection:

    def __init__(self):
        self.access_token = ""
        self.client_id = os.environ.get("halolink_client_id")
        self.client_secret = os.environ.get("halolink_client_secret")
        self.client_session = None

    async def request_access_token(self):
        async with aiohttp.ClientSession() as session:
            async with session.request(
                    method="post",
                    url=f"https://{HALOLINK_HOST}/idsrv/connect/token",
                    data={
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "scope": "serviceuser graphql",
                        "grant_type": "client_credentials"
                    },
                    ssl=ssl.SSLContext(ssl.PROTOCOL_TLS),
                    raise_for_status=True
            ) as response:
                data = await response.json()
                self.access_token = data['access_token']

    async def create_client_session(self, add_local_bearer=False):
        transport = WebsocketsTransport(
            url=f"wss://{HALOLINK_HOST}/graphql",
            headers={"authorization": f"bearer {self.access_token}"},
            subprotocols=[WebsocketsTransport.APOLLO_SUBPROTOCOL],
            ssl=ssl.SSLContext(ssl.PROTOCOL_TLS),
            connect_timeout=40
        )
        if add_local_bearer:
            transport.headers["x-authentication-scheme"] = "LocalBearer"

        client = Client(transport=transport, execute_timeout=40)
        self.client_session = await client.connect_async()

    async def get_image_by_pk(self, primary_key: int) -> dict:
        image = await self.client_session.execute(
            gql("""
            query imageByPk($pk: Int!) {
              imageByPk(pk:$pk) {
                id
                location
                tag
                barcode
                stain
                fieldValues {
                    pk
                    id
                    value
                    type
                    string
                    text
                    systemField {
                       pk
                       id
                       name
                       type
                    }
                }
              }
            }
        """),
            variable_values={"pk": primary_key}
        )
        return image

    async def get_images_in_study(self, study_pk: int):
        study = await self.client_session.execute(
            gql("""
            query studyByPk($pk: Int!) {
              studyByPk(pk:$pk) {
                pk
                id
                name
                studyImages {
                  image {
                    pk
                    id
                    location
                    tag
                    stain
                    barcode
                                    fieldValues {
                                      value
                                      systemField {
                                        name
                                      }
                }
                  }
                }
              }
            }
        """),
            variable_values={"pk": study_pk}
        )
        return study['studyByPk']['studyImages']

    async def get_study_info(self, study_pk: int):
        study = await self.client_session.execute(
            gql("""
        query studyByPk($pk: Int!) {
          studyByPk(pk:$pk) {
            pk
            id
            name
            isSystem
            isPublic
            description
            createdTime
            permission
            resolvedRole
          }
        }
    """),
            variable_values={"pk": study_pk}
        )
        return study['studyByPk']

    async def update_stain(self, image_id: str, stain: str):
        response = await self.client_session.execute(
            gql("""
            mutation($image_id: ID!, $stain: String) {
                changeImageProperties(input: {
                    imageId: $image_id,
                    stain: $stain
                })
                {
                mutated {
                  node {
                    pk
                    id
                    location
                    tag
                    stain
                    barcode
                    permission
                    resolvedRole
                    modifiedTime
                    createdTime
                  }
                } 
                }
                }
            """), variable_values={"image_id": image_id, "stain": stain}
        )
        return response


    #NOTE: This mutation uses the internal IDs NOT the integer primary keys.
    async def move_image(self, image_id: str, src_study_id: str, dest_study_id: str):
        response = await self.client_session.execute(
            gql("""
             mutation($study_id: ID!, $image_id: ID!, $src_study_id: ID!){
                  moveImageToStudy(input: {
                    imageId: $image_id
                    studyId: $study_id
                    sourceStudyId: $src_study_id 
                  })
            {
                mutated {
                  node {
                study {
                studyImages {
                  image {
                    pk
                    id
                    location
                    tag
                    stain
                    barcode
                    permission
                    resolvedRole
                    modifiedTime
                    createdTime
                  }
                }
                }
                  }
                }
              }
              }
              """),
            variable_values={"image_id": image_id, "study_id": dest_study_id, "src_study_id": src_study_id}
        )
        return response

    async def set_image_fields(self, image_id: str, field_updates: list):
        update_string = ""
        for field_update in field_updates:
            update_string = update_string + f",{{ operation: SET, systemFieldId: \"{field_update['field_enum'].value['id']}\", newValue: \"{field_update['value']}\"}}"
        update_string = update_string[1:]
        response = await self.client_session.execute(
            gql("""
             mutation($image_id: ID!){
                  updateImageFieldValues (input: {
                    imageId: $image_id
                    updates: [
                        """
                        + update_string +
                        """
                    ]
                  })
            {
                mutated {
                  node {
                    pk
                    id
                    value
                    type
                    string
                    text
                    systemField {
                       pk
                       id
                       name
                       type
                    }
                  }
                }
                }
                }
                """),
            variable_values={"image_id": image_id}
        )
        return response


