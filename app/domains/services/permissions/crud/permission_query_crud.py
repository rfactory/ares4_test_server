from app.core.crud_base import CRUDBase
from app.models.objects.permission import Permission

class CRUDPermissionQuery(CRUDBase[Permission, None, None]):
    # 'get_multi' (전체 조회)는 CRUDBase에 이미 구현되어 있으므로, 추가 로직이 필요 없습니다.
    pass

permission_query_crud = CRUDPermissionQuery(Permission)
