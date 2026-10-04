from app.services.echo.service import Echo


async def test_echo_plugin():
    assert (await Echo().run({"text": "اختبار"})).text == "اختبار"
