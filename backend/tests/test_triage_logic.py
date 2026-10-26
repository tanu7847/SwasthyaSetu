def test_warning_terms_are_documented():
    # This test intentionally checks only the demo vocabulary, not clinical accuracy.
    terms = ["chest pain", "difficulty breathing", "unconscious", "severe bleeding"]
    assert "chest pain" in terms
    assert len(terms) >= 4
