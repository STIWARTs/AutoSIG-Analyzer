# GNU Radio synthetic flowgraph

`synthetic_flowgraph.py` is the offline GNU Radio flowgraph used by
`training/generate_dataset.py`. It writes oversampled BPSK/QPSK complex captures
after applying real carrier offset and AWGN. Framing, block interleaving and
convolutional coding are performed before the samples reach the flowgraph.

Install GNU Radio into the project Conda environment before regenerating the
dataset: `conda install -p .conda -c conda-forge gnuradio`.
