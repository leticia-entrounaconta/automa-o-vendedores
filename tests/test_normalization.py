from app.data_processing.normalization import normalize_code, normalize_cpf_cnpj, normalize_name


def test_normalize_cpf_cnpj_preserves_leading_zeroes() -> None:
    assert normalize_cpf_cnpj("001.234.567-89") == "00123456789"
    assert normalize_cpf_cnpj("00.123.456/0001-09") == "00123456000109"


def test_normalize_code_and_name() -> None:
    assert normalize_code(" 000-abc.0 ") == "000ABC0"
    assert normalize_code("000123.0") == "000123"
    assert normalize_name("  João  D'Ávila ") == "JOAO D AVILA"
