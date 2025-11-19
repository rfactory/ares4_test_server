import pytest
import sys
import os
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy_utils import database_exists, create_database
from datetime import datetime, timedelta, timezone

# Add the project root to the Python path to allow imports from 'app'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from app.database import Base
from app.main import app
from app.dependencies import get_db
from app.domains.accounts.crud import user_crud
from app.domains.accounts.schemas import UserCreate
from app.core.security import create_access_token
from app.models.objects.user import User as DBUser
from app.models.objects.hardware_blueprint import HardwareBlueprint
from app.models.objects.organization import Organization
from app.models.objects.product_line import ProductLine
from app.models.objects.organization_type import OrganizationType
from app.settings import settings


# Use a separate test database URL
TEST_DATABASE_URL = "postgresql://ares_user:ares_password@ares4-postgres-v2:5432/test_ares_db_v2"

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def anyio_backend():
    return 'asyncio'

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """
    Fixture to create and drop the test database for the entire test session.
    """
    if not database_exists(engine.url):
        create_database(engine.url, template="template0")
        
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(name="db_session")
def db_session_fixture():
    """
    Fixture that provides a test database session for a single test.
    Each test runs within its own transaction, which is rolled back afterwards.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(name="client")
async def client_fixture(db_session: Session):
    """
    Fixture that provides an asynchronous test client for FastAPI.
    It overrides the get_db dependency to use the test database session.
    """
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()

@pytest.fixture(name="test_user_data")
def test_user_data_fixture():
    return {
        "username": "testuser_auth",
        "email": "test_auth@example.com",
        "password": "testpassword"
    }

@pytest.fixture(name="test_user")
def test_user_fixture(db_session: Session, test_user_data: dict) -> DBUser:
    """
    Creates a test user for each test function.
    Changes are rolled back by the db_session fixture.
    """
    user_in = UserCreate(**test_user_data)
    user = user_crud.create_user(db_session, user=user_in)
    return user

@pytest.fixture(name="test_user_token")
def test_user_token_fixture(test_user: DBUser) -> str:
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return create_access_token(
        data={"sub": test_user.username}, expires_delta=access_token_expires
    )

@pytest.fixture(name="test_product_line")
def test_product_line_fixture(db_session: Session) -> ProductLine:
    product_line = ProductLine(name="Test Product Line", description="Description for test product line")
    db_session.add(product_line)
    db_session.commit()
    db_session.refresh(product_line)
    return product_line

@pytest.fixture(name="test_hardware_blueprint")
def test_hardware_blueprint_fixture(db_session: Session, test_product_line: ProductLine) -> HardwareBlueprint:
    hardware_blueprint = HardwareBlueprint(
        blueprint_version="1.0.0",
        blueprint_name="Test Blueprint",
        description="A test hardware blueprint",
        product_line_id=test_product_line.id
    )
    db_session.add(hardware_blueprint)
    db_session.commit()
    db_session.refresh(hardware_blueprint)
    return hardware_blueprint

@pytest.fixture(name="test_organization_type")
def test_organization_type_fixture(db_session: Session) -> OrganizationType:
    org_type = OrganizationType(type_name="Test Type", description="A test organization type")
    db_session.add(org_type)
    db_session.commit()
    db_session.refresh(org_type)
    return org_type

@pytest.fixture(name="test_organization")
def test_organization_fixture(db_session: Session, test_organization_type: OrganizationType) -> Organization:
    organization = Organization(
        company_name="Test Org",
        address="123 Test St",
        contact_email="org@test.com",
        business_registration_number="1234567890",
        contact_phone="123-456-7890",
        legal_name="Test Organization Inc.",
        country="Testland",
        main_contact_person="Test Contact",  # Required NOT NULL field
        organization_type_id=test_organization_type.id
    )
    db_session.add(organization)
    db_session.commit()
    db_session.refresh(organization)
    return organization