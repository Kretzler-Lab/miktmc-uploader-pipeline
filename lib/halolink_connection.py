import ssl
import os
import aiohttp
from gql import Client
from gql import gql
from gql.transport.websockets import WebsocketsTransport

HALOLINK_HOST = "dpr.niddk.nih.gov"


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
            ssl=ssl.SSLContext(ssl.PROTOCOL_TLS)
        )
        if add_local_bearer:
            transport.headers["x-authentication-scheme"] = "LocalBearer"

        client = Client(transport=transport)
        self.client_session = await client.connect_async()

    async def get_image_by_pk(self, primary_key: int) -> dict:
        image = await self.client_session.execute(
            gql("""
            query imageByPk($pk: Int!) {
              imageByPk(pk:$pk) {
                id
                location
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
                isSystem
                isPublic
                description
                createdTime
                permission
                resolvedRole
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
        """),
        variable_values={"pk": study_pk}
        )
        return study['studyByPk']['studyImages']

    async def get_schema(self) -> dict:
        introspection_query = gql.gql(
            """
            query IntrospectionQuery {
                __schema {
                    queryType { name }
                    mutationType { name }
                    subscriptionType { name }
                    types {
                        ...FullType
                    }
                }
            }
        
            fragment FullType on __Type {
                kind
                name
                description
                fields(includeDeprecated: true) {
                    name
                    description
                    args {
                        name
                        description
                        type {
                            ...TypeRef
                        }
                    }
                    type {
                        ...TypeRef
                    }
                }
            }
        
            fragment TypeRef on __Type {
                kind
                name
                ofType {
                    kind
                    name
                    ofType {
                        kind
                        name
                        ofType {
                            kind
                            name
                        }
                    }
                }
            }
            """
        )

        result = await self.client_session.execute(introspection_query)
        schema = result['__schema']
        return schema
