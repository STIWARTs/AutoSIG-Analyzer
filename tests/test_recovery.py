import numpy as np

from backend.recovery.coding import block_deinterleave, block_interleave, convolutional_encode, make_frame, viterbi_decode
from backend.validation.correlation import validate_bitstream


def test_block_and_viterbi_recover_frame():
    payload = np.tile(np.array([0, 1, 1, 0], dtype=np.uint8), 32)
    frame = make_frame(payload)
    encoded = convolutional_encode(frame)
    restored = viterbi_decode(block_deinterleave(block_interleave(encoded)))
    assert np.array_equal(restored, frame)
    assert validate_bitstream(restored).passed
