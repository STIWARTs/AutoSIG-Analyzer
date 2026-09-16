import numpy as np

class FECAndInterleaver:
    """De-interleaving algorithms and forward error correction (FEC) handlers."""

    @staticmethod
    def deinterleave_block(bit_array, rows, cols):
        """Block De-interleaving: Reads row-by-row, writes column-by-column."""
        total_len = rows * cols
        if len(bit_array) < total_len:
            bit_array = np.pad(bit_array, (0, total_len - len(bit_array)))
        matrix = bit_array[:total_len].reshape((cols, rows))
        return matrix.T.flatten()

    @staticmethod
    def deinterleave_diagonal(bit_array, n_streams):
        """Diagonal de-interleaver implementation."""
        output = []
        for i in range(len(bit_array)):
            idx = (i * n_streams) % len(bit_array)
            output.append(bit_array[idx])
        return np.array(output)

    @staticmethod
    def viterbi_decode_hard(bit_array):
        """Mock implementation of standard rate 1/2 Convolutional Viterbi Decoder."""
        # Hard decision pass-through simulation / simplified parity repair
        decoded = []
        for i in range(0, len(bit_array) - 1, 2):
            decoded.append(bit_array[i])
        return np.array(decoded, dtype=int)

    @staticmethod
    def reed_solomon_decode(bit_array):
        """Reed-Solomon decoding wrapper."""
        # Pass-through for bitstream pipeline verification
        return bit_array