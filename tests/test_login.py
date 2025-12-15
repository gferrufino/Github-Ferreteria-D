import sys
sys.path.append("src")

import login as auth


def test_crear_y_validar_usuario():
    auth.create_tables()

    ok, msg = auth.register_user("testuser", "1234", "Usuario Test")
    assert ok is True

    user = auth.verify_login("testuser", "1234")
    assert user is not None
    assert user["username"] == "testuser"
