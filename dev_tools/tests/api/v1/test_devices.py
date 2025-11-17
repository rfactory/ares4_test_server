import pytest
from httpx import AsyncClient
from uuid import uuid4

@pytest.mark.anyio
async def test_create_device(
    client: AsyncClient,
    test_user_token: str,
    test_hardware_blueprint,
    test_organization
):
    """
    Test device creation.
    """
    device_data = {
        "cpu_serial": "test_cpu_serial_123",
        "current_uuid": str(uuid4()),
        "hardware_blueprint_id": test_hardware_blueprint.id,
        "organization_id": test_organization.id,
        "visibility_status": "PRIVATE"
    }
    response = await client.post(
        "/api/v1/devices/",
        json=device_data,
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["cpu_serial"] == device_data["cpu_serial"]
    assert data["hardware_blueprint_id"] == device_data["hardware_blueprint_id"]
    assert data["organization_id"] == device_data["organization_id"]
    assert "id" in data

@pytest.mark.anyio
async def test_create_duplicate_device_cpu_serial(
    client: AsyncClient,
    test_user_token: str,
    test_hardware_blueprint,
    test_organization
):
    """
    Test creating a device with a duplicate CPU serial.
    """
    cpu_serial = "duplicate_cpu_serial"
    # Create a device first
    device_data_1 = {
        "cpu_serial": cpu_serial,
        "current_uuid": str(uuid4()),
        "hardware_blueprint_id": test_hardware_blueprint.id,
        "organization_id": test_organization.id,
        "visibility_status": "PRIVATE"
    }
    await client.post(
        "/api/v1/devices/",
        json=device_data_1,
        headers={"Authorization": f"Bearer {test_user_token}"}
    )

    # Try to create another device with the same CPU serial
    device_data_2 = {
        "cpu_serial": cpu_serial,
        "current_uuid": str(uuid4()),
        "hardware_blueprint_id": test_hardware_blueprint.id,
        "organization_id": test_organization.id,
        "visibility_status": "PRIVATE"
    }
    response = await client.post(
        "/api/v1/devices/",
        json=device_data_2,
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Device with this CPU serial already exists"

@pytest.mark.anyio
async def test_create_duplicate_device_uuid(
    client: AsyncClient,
    test_user_token: str,
    test_hardware_blueprint,
    test_organization
):
    """
    Test creating a device with a duplicate UUID.
    """
    current_uuid = str(uuid4())
    # Create a device first
    device_data_1 = {
        "cpu_serial": "unique_cpu_serial_1",
        "current_uuid": current_uuid,
        "hardware_blueprint_id": test_hardware_blueprint.id,
        "organization_id": test_organization.id,
        "visibility_status": "PRIVATE"
    }
    await client.post(
        "/api/v1/devices/",
        json=device_data_1,
        headers={"Authorization": f"Bearer {test_user_token}"}
    )

    # Try to create another device with the same UUID
    device_data_2 = {
        "cpu_serial": "unique_cpu_serial_2",
        "current_uuid": current_uuid,
        "hardware_blueprint_id": test_hardware_blueprint.id,
        "organization_id": test_organization.id,
        "visibility_status": "PRIVATE"
    }
    response = await client.post(
        "/api/v1/devices/",
        json=device_data_2,
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Device with this UUID already exists"

@pytest.mark.anyio
async def test_read_device(
    client: AsyncClient,
    test_user_token: str,
    test_hardware_blueprint,
    test_organization
):
    """
    Test reading a single device's details.
    """
    # Create a device first
    device_data = {
        "cpu_serial": "read_cpu_serial",
        "current_uuid": str(uuid4()),
        "hardware_blueprint_id": test_hardware_blueprint.id,
        "organization_id": test_organization.id,
        "visibility_status": "PRIVATE"
    }
    create_response = await client.post(
        "/api/v1/devices/",
        json=device_data,
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert create_response.status_code == 201
    created_device_id = create_response.json()["id"]

    # Read the device
    read_response = await client.get(
        f"/api/v1/devices/{created_device_id}",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert read_response.status_code == 200
    data = read_response.json()
    assert data["cpu_serial"] == device_data["cpu_serial"]
    assert data["id"] == created_device_id

@pytest.mark.anyio
async def test_update_device(
    client: AsyncClient,
    test_user_token: str,
    test_hardware_blueprint,
    test_organization
):
    """
    Test updating an existing device.
    """
    # Create a device first
    device_data = {
        "cpu_serial": "update_cpu_serial",
        "current_uuid": str(uuid4()),
        "hardware_blueprint_id": test_hardware_blueprint.id,
        "organization_id": test_organization.id,
        "visibility_status": "PRIVATE"
    }
    create_response = await client.post(
        "/api/v1/devices/",
        json=device_data,
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert create_response.status_code == 201
    created_device_id = create_response.json()["id"]

    # Update the device
    update_data = {
        "cpu_serial": "updated_cpu_serial",
        "visibility_status": "PUBLIC"
    }
    update_response = await client.put(
        f"/api/v1/devices/{created_device_id}",
        json=update_data,
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert update_response.status_code == 200
    data = update_response.json()
    assert data["cpu_serial"] == update_data["cpu_serial"]
    assert data["visibility_status"] == update_data["visibility_status"]
    assert data["id"] == created_device_id

@pytest.mark.anyio
async def test_delete_device(
    client: AsyncClient,
    test_user_token: str,
    test_hardware_blueprint,
    test_organization
):
    """
    Test deleting a device.
    """
    # Create a device first
    device_data = {
        "cpu_serial": "delete_cpu_serial",
        "current_uuid": str(uuid4()),
        "hardware_blueprint_id": test_hardware_blueprint.id,
        "organization_id": test_organization.id,
        "visibility_status": "PRIVATE"
    }
    create_response = await client.post(
        "/api/v1/devices/",
        json=device_data,
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert create_response.status_code == 201
    created_device_id = create_response.json()["id"]

    # Delete the device
    delete_response = await client.delete(
        f"/api/v1/devices/{created_device_id}",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert delete_response.status_code == 200
    data = delete_response.json()
    assert data["id"] == created_device_id

    # Try to read the deleted device
    read_response = await client.get(
        f"/api/v1/devices/{created_device_id}",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert read_response.status_code == 404
