import numpy as np


class BitstreamCorrelator:
    """
    Preamble detection and payload extraction utilities.

    The correlator searches a demodulated bitstream for a known
    synchronization word and extracts the payload following it.
    """

    # ---------------------------------------------------------
    # PREDEFINED PREAMBLES
    # ---------------------------------------------------------

    PREAMBLES = {
        "Sync-Word Alpha": np.array([
            1, 0, 1, 0, 1, 1, 0, 0,
            1, 1, 0, 1, 0, 0, 1, 0,
            1, 0, 0, 1, 1, 0, 1, 1,
            0, 1, 0, 0, 1, 1, 1, 0
        ], dtype=np.uint8),

        "Sync-Word Beta": np.array([
            1, 1, 0, 0, 1, 0, 1, 1,
            0, 1, 1, 0, 0, 1, 0, 1,
            1, 0, 1, 1, 0, 0, 1, 0,
            0, 1, 0, 1, 1, 0, 1, 1
        ], dtype=np.uint8),
    }

    # ---------------------------------------------------------
    # BIT NORMALIZATION
    # ---------------------------------------------------------

    @staticmethod
    def _normalize_bits(bit_array):
        """
        Convert input into a clean binary NumPy array.
        """

        bits = np.asarray(
            bit_array,
            dtype=np.uint8
        )

        return bits & 1

    # ---------------------------------------------------------
    # HAMMING DISTANCE
    # ---------------------------------------------------------

    @staticmethod
    def hamming_distance(bits_a, bits_b):
        """
        Calculate the number of different bits between two
        equally-sized bit arrays.
        """

        a = BitstreamCorrelator._normalize_bits(bits_a)
        b = BitstreamCorrelator._normalize_bits(bits_b)

        if len(a) != len(b):
            raise ValueError(
                "Bit arrays must have the same length."
            )

        if len(a) == 0:
            return 0

        return int(np.sum(a != b))

    # ---------------------------------------------------------
    # PREAMBLE CORRELATION
    # ---------------------------------------------------------

    @staticmethod
    def correlate_preamble(bitstream, preamble):
        """
        Search for a preamble inside a bitstream.

        Returns:
            index      -> starting index of best match
            confidence -> similarity score from 0.0 to 1.0

        A confidence of 1.0 means an exact match.
        """

        bits = BitstreamCorrelator._normalize_bits(
            bitstream
        )

        pattern = BitstreamCorrelator._normalize_bits(
            preamble
        )

        if len(bits) == 0:
            return -1, 0.0

        if len(pattern) == 0:
            return -1, 0.0

        if len(bits) < len(pattern):
            return -1, 0.0

        best_index = -1
        best_confidence = 0.0

        pattern_length = len(pattern)

        # Sliding-window correlation
        for index in range(
            len(bits) - pattern_length + 1
        ):

            window = bits[
                index:index + pattern_length
            ]

            matches = np.sum(
                window == pattern
            )

            confidence = (
                matches / pattern_length
            )

            if confidence > best_confidence:
                best_confidence = float(
                    confidence
                )
                best_index = index

        return best_index, best_confidence

    # ---------------------------------------------------------
    # CORRELATE AGAINST ALL KNOWN PREAMBLES
    # ---------------------------------------------------------

    @staticmethod
    def detect_preamble(bitstream):
        """
        Test the bitstream against all predefined preambles.

        Returns:
            name
            index
            confidence
        """

        best_name = None
        best_index = -1
        best_confidence = 0.0

        for name, preamble in BitstreamCorrelator.PREAMBLES.items():

            index, confidence = (
                BitstreamCorrelator.correlate_preamble(
                    bitstream,
                    preamble
                )
            )

            if confidence > best_confidence:

                best_name = name
                best_index = index
                best_confidence = confidence

        return (
            best_name,
            best_index,
            best_confidence
        )

    # ---------------------------------------------------------
    # PAYLOAD EXTRACTION
    # ---------------------------------------------------------

    @staticmethod
    def extract_payload(
        bitstream,
        preamble_index,
        preamble_length,
        payload_len=64
    ):
        """
        Extract payload bits immediately after the preamble.
        """

        bits = BitstreamCorrelator._normalize_bits(
            bitstream
        )

        if preamble_index < 0:
            return np.array([], dtype=np.uint8)

        if preamble_length <= 0:
            raise ValueError(
                "Preamble length must be positive."
            )

        if payload_len <= 0:
            raise ValueError(
                "Payload length must be positive."
            )

        payload_start = (
            preamble_index
            + preamble_length
        )

        payload_end = (
            payload_start
            + payload_len
        )

        if payload_start >= len(bits):
            return np.array([], dtype=np.uint8)

        payload = bits[
            payload_start:payload_end
        ]

        return payload.astype(np.uint8)

    # ---------------------------------------------------------
    # BITS TO BYTE
    # ---------------------------------------------------------

    @staticmethod
    def bits_to_bytes(bit_array):
        """
        Convert binary bits into bytes.

        Incomplete final byte is padded with zeros.
        """

        bits = BitstreamCorrelator._normalize_bits(
            bit_array
        )

        if len(bits) == 0:
            return b""

        padding = (-len(bits)) % 8

        if padding:
            bits = np.pad(
                bits,
                (0, padding)
            )

        byte_array = np.packbits(bits)

        return byte_array.tobytes()

    # ---------------------------------------------------------
    # BITS TO ASCII
    # ---------------------------------------------------------

    @staticmethod
    def bits_to_ascii(bit_array):
        """
        Convert bitstream into readable ASCII text.

        Non-printable characters are replaced with '.'.
        """

        raw_bytes = (
            BitstreamCorrelator.bits_to_bytes(
                bit_array
            )
        )

        if not raw_bytes:
            return ""

        text = ""

        for value in raw_bytes:

            if 32 <= value <= 126:
                text += chr(value)
            else:
                text += "."

        return text

    # ---------------------------------------------------------
    # DEBUG INFORMATION
    # ---------------------------------------------------------

    @staticmethod
    def analyze_match(
        bitstream,
        preamble,
        index
    ):
        """
        Return detailed matching information for debugging.
        """

        bits = BitstreamCorrelator._normalize_bits(
            bitstream
        )

        pattern = BitstreamCorrelator._normalize_bits(
            preamble
        )

        if index < 0:
            return {
                "index": -1,
                "matches": 0,
                "errors": len(pattern),
                "confidence": 0.0,
            }

        window = bits[
            index:index + len(pattern)
        ]

        if len(window) != len(pattern):
            return {
                "index": index,
                "matches": int(
                    len(window)
                ),
                "errors": int(
                    len(pattern) - len(window)
                ),
                "confidence": (
                    len(window)
                    / len(pattern)
                ),
            }

        matches = int(
            np.sum(window == pattern)
        )

        errors = (
            len(pattern) - matches
        )

        confidence = (
            matches / len(pattern)
        )

        return {
            "index": index,
            "matches": matches,
            "errors": errors,
            "confidence": float(confidence),
        }