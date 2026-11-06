from trustai.ingestion.cleaning import clean_text


def test_ligatures_and_nbsp_normalised():
    assert clean_text("ofﬁce policy") == "office policy"


def test_hyphenated_linebreak_rejoined():
    assert clean_text("infor-\nmation security") == "information security"


def test_hyphen_before_uppercase_or_digit_kept():
    assert clean_text("COVID-\n19 rules") == "COVID-\n19 rules"


def test_whitespace_and_blank_lines_collapsed():
    assert clean_text("a   b\n\n\n\n\nc") == "a b\n\nc"


def test_control_characters_removed():
    assert clean_text("he\x00llo\x07 world") == "hello world"


def test_windows_line_endings_normalised():
    assert clean_text("one\r\ntwo\rthree") == "one\ntwo\nthree"
