# Copyright Amazon.com Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You may
# not use this file except in compliance with the License. A copy of the
# License is located at
#
#        http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is distributed
# on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# express or implied. See the License for the specific language governing
# permissions and limitations under the License.

"""Integration tests for the Athena DataCatalog resource"""

import time
import boto3
import pytest

from acktest.k8s import condition
from acktest.k8s import resource as k8s
from acktest import tags as tagutil
from acktest.resources import random_suffix_name
from acktest.aws import identity
from e2e import service_marker, CRD_GROUP, CRD_VERSION, load_athena_resource
from e2e.replacement_values import REPLACEMENT_VALUES
from e2e import data_catalog

DATA_CATALOG_RESOURCE_PLURAL = "datacatalogs"

CREATE_WAIT_SECONDS = 10
MODIFY_WAIT_SECONDS = 10
DELETE_WAIT_SECONDS = 10

@pytest.fixture(scope="module")
def athena_client():
    return boto3.client("athena")


@pytest.fixture(scope="module")
def glue_data_catalog():
    catalog_name = random_suffix_name("my-glue-catalog", 24)

    replacements = REPLACEMENT_VALUES.copy()
    replacements["DATA_CATALOG_NAME"] = catalog_name
    replacements["AWS_ACCOUNT_ID"] = identity.get_account_id()

    resource_data = load_athena_resource(
        "data_catalog_glue",
        additional_replacements=replacements,
    )

    ref = k8s.CustomResourceReference(
        CRD_GROUP,
        CRD_VERSION,
        DATA_CATALOG_RESOURCE_PLURAL,
        catalog_name,
        namespace="default",
    )
    k8s.create_custom_resource(ref, resource_data)
    cr = k8s.wait_resource_consumed_by_controller(ref)

    assert cr is not None
    assert k8s.get_resource_exists(ref)

    yield (ref, cr)

    try:
        _, deleted = k8s.delete_custom_resource(ref, DELETE_WAIT_SECONDS)
        assert deleted
    except:
        pass


@pytest.fixture(scope="module")
def lambda_data_catalog():
    catalog_name = random_suffix_name("my-lambda-catalog", 24)

    replacements = REPLACEMENT_VALUES.copy()
    replacements["DATA_CATALOG_NAME"] = catalog_name

    resource_data = load_athena_resource(
        "data_catalog_lambda",
        additional_replacements=replacements,
    )

    ref = k8s.CustomResourceReference(
        CRD_GROUP,
        CRD_VERSION,
        DATA_CATALOG_RESOURCE_PLURAL,
        catalog_name,
        namespace="default",
    )
    k8s.create_custom_resource(ref, resource_data)
    cr = k8s.wait_resource_consumed_by_controller(ref)

    assert cr is not None
    assert k8s.get_resource_exists(ref)

    yield (ref, cr)

    try:
        _, deleted = k8s.delete_custom_resource(ref, DELETE_WAIT_SECONDS)
        assert deleted
    except:
        pass


@pytest.fixture(scope="module")
def hive_data_catalog():
    catalog_name = random_suffix_name("my-hive-catalog", 24)

    replacements = REPLACEMENT_VALUES.copy()
    replacements["DATA_CATALOG_NAME"] = catalog_name

    resource_data = load_athena_resource(
        "data_catalog_hive",
        additional_replacements=replacements,
    )

    ref = k8s.CustomResourceReference(
        CRD_GROUP,
        CRD_VERSION,
        DATA_CATALOG_RESOURCE_PLURAL,
        catalog_name,
        namespace="default",
    )
    k8s.create_custom_resource(ref, resource_data)
    cr = k8s.wait_resource_consumed_by_controller(ref)

    assert cr is not None
    assert k8s.get_resource_exists(ref)

    yield (ref, cr)

    try:
        _, deleted = k8s.delete_custom_resource(ref, DELETE_WAIT_SECONDS)
        assert deleted
    except:
        pass


@service_marker
@pytest.mark.canary
class TestDataCatalogGlue:
    def test_crud_glue(self, glue_data_catalog, athena_client):
        ref, _ = glue_data_catalog

        time.sleep(CREATE_WAIT_SECONDS)
        condition.assert_synced(ref)

        cr = k8s.get_resource(ref)
        assert "spec" in cr
        assert "name" in cr["spec"]
        catalog_name = cr["spec"]["name"]

        latest = data_catalog.get(catalog_name)
        assert latest is not None
        assert latest["Type"] == "GLUE"
        assert latest["Description"] == "glue data catalog for e2e test"
        assert latest.get("Parameters", {}).get("catalog-id") == identity.get_account_id()

        catalog_tags = athena_client.list_tags_for_resource(
            ResourceARN=cr["status"]["ackResourceMetadata"]["arn"],
        )["Tags"]
        tags = tagutil.clean(catalog_tags)
        assert {"Key": "env", "Value": "test"} in tags

        # update tags
        new_tags = [
            {
                "key": "env",
                "value": "changed"
            },
            {
                "key": "k1",
                "value": "v1"
            }
        ]
        updates = {
            "spec": {
                "tags": new_tags
            }
        }
        k8s.patch_custom_resource(ref, updates)
        time.sleep(MODIFY_WAIT_SECONDS)

        catalog_tags = athena_client.list_tags_for_resource(
            ResourceARN=cr["status"]["ackResourceMetadata"]["arn"],
        )["Tags"]
        tags = tagutil.clean(catalog_tags)
        assert len(tags) == 2
        assert {"Key": "env", "Value": "changed"} in tags
        assert {"Key": "k1", "Value": "v1"} in tags

        # update type
        updates = {
            "spec": {
                "type": "HIVE",
                "parameters": {
                    "catalog-id": None,
                    "metadata-function": REPLACEMENT_VALUES["LAMBDA_FUNCTION_ARN"]
                }
            }
        }

        k8s.patch_custom_resource(ref, updates)
        time.sleep(MODIFY_WAIT_SECONDS)

        latest = data_catalog.get(catalog_name)
        assert latest is not None
        assert "catalog-id" not in latest.get("Parameters", {})
        assert latest["Type"] == "HIVE"
        assert "metadata-function" in latest.get("Parameters", {})

        # Delete
        _, deleted = k8s.delete_custom_resource(ref, DELETE_WAIT_SECONDS)
        assert deleted
        data_catalog.wait_until_deleted(catalog_name)


@service_marker
@pytest.mark.canary
class TestDataCatalogLambda:
    def test_crud_lambda(self, lambda_data_catalog, athena_client):
        ref, _ = lambda_data_catalog

        time.sleep(CREATE_WAIT_SECONDS)
        condition.assert_synced(ref)

        cr = k8s.get_resource(ref)
        catalog_name = cr["spec"]["name"]

        latest = data_catalog.get(catalog_name)
        assert latest is not None
        assert latest["Type"] == "LAMBDA"
        assert latest["Description"] == "lambda data catalog for e2e test"
        parameters = latest.get("Parameters", {})
        assert "metadata-function" in parameters
        assert "record-function" in parameters

        catalog_tags = athena_client.list_tags_for_resource(
            ResourceARN=cr["status"]["ackResourceMetadata"]["arn"],
        )["Tags"]
        tags = tagutil.clean(catalog_tags)
        assert {"Key": "env", "Value": "test"} in tags

        # Update description
        updates = {"spec": {"description": "updated lambda catalog"}}
        k8s.patch_custom_resource(ref, updates)
        time.sleep(MODIFY_WAIT_SECONDS)
        condition.assert_synced(ref)

        latest = data_catalog.get(catalog_name)
        assert latest["Description"] == "updated lambda catalog"

        # Delete
        _, deleted = k8s.delete_custom_resource(ref, DELETE_WAIT_SECONDS)
        assert deleted
        data_catalog.wait_until_deleted(catalog_name)


@service_marker
@pytest.mark.canary
class TestDataCatalogHive:
    def test_crud_hive(self, hive_data_catalog, athena_client):
        ref, _ = hive_data_catalog

        time.sleep(CREATE_WAIT_SECONDS)
        condition.assert_synced(ref)

        cr = k8s.get_resource(ref)
        catalog_name = cr["spec"]["name"]

        latest = data_catalog.get(catalog_name)
        assert latest is not None
        assert latest["Type"] == "HIVE"
        assert latest["Description"] == "hive data catalog for e2e test"
        assert "metadata-function" in latest.get("Parameters", {})
        assert "sdk-version" in latest.get("Parameters", {})

        catalog_tags = athena_client.list_tags_for_resource(
            ResourceARN=cr["status"]["ackResourceMetadata"]["arn"],
        )["Tags"]
        tags = tagutil.clean(catalog_tags)
        assert {"Key": "env", "Value": "test"} in tags

        # update description
        updates = {"spec": {"description": "updated hive catalog"}}
        k8s.patch_custom_resource(ref, updates)
        time.sleep(MODIFY_WAIT_SECONDS)
        condition.assert_synced(ref)

        latest = data_catalog.get(catalog_name)
        assert latest["Description"] == "updated hive catalog"

        # Delete
        _, deleted = k8s.delete_custom_resource(ref, DELETE_WAIT_SECONDS)
        assert deleted
        data_catalog.wait_until_deleted(catalog_name)
