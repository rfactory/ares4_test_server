import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from typing import List

from app.models.objects.device import Device as DBDevice
from app.models.objects.product_line import ProductLine as DBProductLine
from app.models.objects.organization import Organization as DBOrganization
from app.models.objects.organization_type import OrganizationType as DBOrganizationType
from app.models.objects.hardware_blueprint import HardwareBlueprint as DBHardwareBlueprint # Import HardwareBlueprint
from app.domains.data.schemas import TelemetryDataCreate, TelemetryMetadataCreate, MetaValueType, TelemetryDataResponse

@pytest.fixture
def test_device(db_session: Session, test_hardware_blueprint: DBHardwareBlueprint, test_organization: DBOrganization) -> DBDevice:
    device = DBDevice(
        cpu_serial="TestDevice1CPU",
        current_uuid="00000000-0000-0000-0000-000000000001",
        hardware_blueprint_id=test_hardware_blueprint.id, # Use hardware_blueprint_id
        organization_id=test_organization.id
    )
    db_session.add(device)
    db_session.commit()
    db_session.refresh(device)
    return device

@pytest.mark.anyio
async def test_create_telemetry_data(client: AsyncClient, db_session: Session, test_device: DBDevice, test_user_token: str):
    """
    Test creating a new telemetry data record with associated metadata.
    """
    telemetry_data_in = TelemetryDataCreate(
        device_id=test_device.id,
        timestamp=datetime.now(timezone.utc),
        metric_name="temperature",
        metric_value=25.5,
        unit="°C",
        metadata_items=[
            TelemetryMetadataCreate(meta_key="sensor_location", meta_value="engine", meta_value_type=MetaValueType.STRING),
            TelemetryMetadataCreate(meta_key="threshold_exceeded", meta_value="false", meta_value_type=MetaValueType.BOOLEAN)
        ]
    )
    response = await client.post(
        "/api/v1/data/telemetry",
        json=telemetry_data_in.model_dump(mode='json'),
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["device_id"] == test_device.id
    assert data["metric_name"] == "temperature"
    assert data["metric_value"] == 25.5
    assert len(data["metadata_items"]) == 2
    assert data["metadata_items"][0]["meta_key"] == "sensor_location"
    assert data["metadata_items"][1]["meta_value_type"] == "BOOLEAN"

@pytest.mark.anyio
async def test_get_telemetry_data_by_id(client: AsyncClient, db_session: Session, test_device: DBDevice, test_user_token: str):
    """
    Test retrieving a single telemetry data record by its ID.
    """
    telemetry_data_in = TelemetryDataCreate(
        device_id=test_device.id,
        timestamp=datetime.now(timezone.utc),
        metric_name="pressure",
        metric_value=101.2,
        unit="kPa"
    )
    create_response = await client.post(
        "/api/v1/data/telemetry",
        json=telemetry_data_in.model_dump(mode='json'),
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert create_response.status_code == 201
    created_id = create_response.json()["id"]

    get_response = await client.get(
        f"/api/v1/data/telemetry/{created_id}",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["id"] == created_id
    assert data["metric_name"] == "pressure"
    assert data["device"]["id"] == test_device.id # Check nested device info

@pytest.mark.anyio
async def test_get_multiple_telemetry_data(client: AsyncClient, db_session: Session, test_device: DBDevice, test_user_token: str):
    """
    Test retrieving multiple telemetry data records with filtering.
    """
    # Create multiple telemetry records
    now = datetime.now(timezone.utc)
    telemetry_data_1 = TelemetryDataCreate(device_id=test_device.id, timestamp=now - timedelta(hours=1), metric_name="temp", metric_value=20.0)
    telemetry_data_2 = TelemetryDataCreate(device_id=test_device.id, timestamp=now, metric_name="temp", metric_value=22.0)
    telemetry_data_3 = TelemetryDataCreate(device_id=test_device.id, timestamp=now + timedelta(hours=1), metric_name="humidity", metric_value=60.0)

    await client.post("/api/v1/data/telemetry", json=telemetry_data_1.model_dump(mode='json'), headers={"Authorization": f"Bearer {test_user_token}"})
    await client.post("/api/v1/data/telemetry", json=telemetry_data_2.model_dump(mode='json'), headers={"Authorization": f"Bearer {test_user_token}"})
    await client.post("/api/v1/data/telemetry", json=telemetry_data_3.model_dump(mode='json'), headers={"Authorization": f"Bearer {test_user_token}"})

    # Test filter by device_id and metric_name
    response = await client.get(
        f"/api/v1/data/telemetry?device_id={test_device.id}&metric_name=temp",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(item["metric_name"] == "temp" for item in data)

    # Test filter by time range
    start_time_str = (now - timedelta(minutes=30)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    end_time_str = (now + timedelta(minutes=30)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    response = await client.get(
        f"/api/v1/data/telemetry?start_time={start_time_str}&end_time={end_time_str}",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1 # Only telemetry_data_2 should be in this range
    assert data[0]["metric_value"] == 22.0

@pytest.mark.anyio
async def test_update_telemetry_data(client: AsyncClient, db_session: Session, test_device: DBDevice, test_user_token: str):
    """
    Test updating an existing telemetry data record.
    """
    telemetry_data_in = TelemetryDataCreate(
        device_id=test_device.id,
        timestamp=datetime.now(timezone.utc),
        metric_name="voltage",
        metric_value=12.0,
        unit="V"
    )
    create_response = await client.post(
        "/api/v1/data/telemetry",
        json=telemetry_data_in.model_dump(mode='json'),
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert create_response.status_code == 201
    created_id = create_response.json()["id"]

    update_payload = {"metric_value": 12.5, "unit": "mV"}
    update_response = await client.patch(
        f"/api/v1/data/telemetry/{created_id}",
        json=update_payload,
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert update_response.status_code == 200
    data = update_response.json()
    assert data["id"] == created_id
    assert data["metric_value"] == 12.5
    assert data["unit"] == "mV"

@pytest.mark.anyio
async def test_delete_telemetry_data(client: AsyncClient, db_session: Session, test_device: DBDevice, test_user_token: str):
    """
    Test deleting a telemetry data record.
    """
    telemetry_data_in = TelemetryDataCreate(
        device_id=test_device.id,
        timestamp=datetime.now(timezone.utc),
        metric_name="current",
        metric_value=0.5,
        unit="A"
    )
    create_response = await client.post(
        "/api/v1/data/telemetry",
        json=telemetry_data_in.model_dump(mode='json'),
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert create_response.status_code == 201
    created_id = create_response.json()["id"]

    delete_response = await client.delete(
        f"/api/v1/data/telemetry/{created_id}",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert delete_response.status_code == 204

    get_response = await client.get(
        f"/api/v1/data/telemetry/{created_id}",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert get_response.status_code == 404

