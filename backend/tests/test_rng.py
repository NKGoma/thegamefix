from delegationlab.engine.rng import derive_seed, rng_for


def test_derive_seed_is_pinned() -> None:
    # Pinned so an accidental change to seed derivation (which breaks reproducibility) fails loudly.
    assert derive_seed(42, "task-1", 0) == derive_seed(42, "task-1", 0)
    assert derive_seed(42, "task-1", 0) == 349573186


def test_derive_seed_changes_with_each_scope_element() -> None:
    base = derive_seed(42, "task-1", 0)
    assert derive_seed(43, "task-1", 0) != base
    assert derive_seed(42, "task-2", 0) != base
    assert derive_seed(42, "task-1", 1) != base
    assert 0 <= base < 2**31


def test_rng_for_is_deterministic() -> None:
    assert rng_for(1, "x").random() == rng_for(1, "x").random()
