from section11_alias_policy import map_section11_endpoint, move_source_value_to_standard_endpoint


def test_mucous_membrane_irritation_maps_to_existing_eye_endpoint():
    assert map_section11_endpoint("主要粘膜刺激性：") == "11.3 主要眼睛刺激性"


def test_alias_mapping_does_not_change_source_value():
    assert move_source_value_to_standard_endpoint("主要粘膜刺激性", "轻微刺激") == (
        "11.3 主要眼睛刺激性",
        "轻微刺激",
    )


def test_unknown_endpoint_is_not_invented():
    assert map_section11_endpoint("未定义毒理项目") is None
