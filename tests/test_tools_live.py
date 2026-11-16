from ereplan.tools_live import parse_final_number, gsm8k_truth, same_number, load_gsm8k, load_freshqa


def test_parse_final_number_takes_last_answer_line():
    assert parse_final_number("r = 5\nAnswer: 12\nwait\nAnswer: 1,250.5") == 1250.5
    assert parse_final_number("Answer: $18") == 18
    assert parse_final_number("the answer is eighteen") is None


def test_gsm8k_truth_and_compare():
    assert gsm8k_truth("blah\n#### 1,000") == 1000
    assert same_number(18.0, 18) and not same_number(None, 18)


def test_task_loaders_are_deterministic():
    assert [t["id"] for t in load_gsm8k(5, seed=1)] == [t["id"] for t in load_gsm8k(5, seed=1)]
    assert load_gsm8k(5, seed=1)[0]["question"] != load_gsm8k(5, seed=2)[0]["question"]
    fq = load_freshqa()
    assert len(fq) == 574 and sum(t["changed"] for t in fq) == 89
